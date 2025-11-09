// frontend/src/composables/useTimelineChart.js

import { ref, computed, watch } from 'vue'
import { 
  calculateVisibleDateRange, 
  getCategoryColor, 
  findCategoryId,
  findParentCategory 
} from '@/utils/timelineHelpers'

/**
 * Get period name from date and grouping
 */
function getPeriodName(date, grouping) {
  const d = new Date(date)
  
  if (grouping === 'year') {
    return d.getFullYear().toString()
  } else if (grouping === 'month') {
    return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  } else if (grouping === 'quarter') {
    // Show month range instead of Q1
    const quarter = Math.floor(d.getMonth() / 3)
    const startMonth = quarter * 3
    const endMonth = startMonth + 2
    const startDate = new Date(d.getFullYear(), startMonth, 1)
    const endDate = new Date(d.getFullYear(), endMonth + 1, 0)
    
    const start = startDate.toLocaleDateString('en-US', { month: 'short' })
    const end = endDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    return `${start} - ${end}`
  }
  
  return d.toLocaleDateString()
}

/**
 * Composable for managing timeline chart configuration and series
 */
export function useTimelineChart(
  timelineData,
  transactions,
  dateRange,
  currentZoomLevel,
  categoryStore,
  visibilityState,
  customVisibleRange = null,
  chartRef = null
) {
  const hoveredData = ref(null)
  const isPinned = ref(false)
  const yAxisValues = ref({ maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false })
  
  // Memoization for expensive category builds
  const memoizedCategoryData = ref(null)
  const lastVisibilityHash = ref('')
  
  const {
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded
  } = visibilityState
  
  // Get category arrays
  const expenseCategories = computed(() => {
    const expenseType = categoryStore.categories?.find(t => t.code === 'expenses')
    return expenseType?.children || []
  })
  
  const incomeCategories = computed(() => {
    const incomeType = categoryStore.categories?.find(t => t.code === 'income')
    return incomeType?.children || []
  })
  
  const transferCategories = computed(() => {
    const transferType = categoryStore.categories?.find(t => t.code === 'transfers')
    return transferType?.children || []
  })
  
  const targetCategories = computed(() => {
    const targetType = categoryStore.categories?.find(t => t.code === 'targets')
    return targetType?.children || []
  })
  
  // Calculate visible date range
  const visibleDateRange = computed(() => {
    if (customVisibleRange && customVisibleRange.value) {
      return {
        start: customVisibleRange.value.start,
        end: customVisibleRange.value.end
      }
    }
    
    return calculateVisibleDateRange(
      dateRange.value.start,
      dateRange.value.end,
      currentZoomLevel.value
    )
  })
  
  // Get current grouping
  const currentGrouping = computed(() => {
    if (!timelineData.value[0] || !timelineData.value[1]) return 'quarter'
    const diff = timelineData.value[1]?.date - timelineData.value[0]?.date
    if (diff > 86400000 * 300) return 'year' // More than ~300 days = year
    if (diff > 86400000 * 60) return 'quarter'
    return 'month'
  })
  
  /**
   * Create hash of current visibility state for memoization
   */
  function getVisibilityHash() {
    return JSON.stringify({
      types: visibilityState.visibleTypes.value.slice().sort(),
      cats: visibilityState.visibleCategories.value.slice().sort(),
      subcats: visibilityState.visibleSubcategories.value.slice().sort(),
      expanded: visibilityState.expandedCategories.value.slice().sort()
    })
  }
  
  /**
   * OPTIMIZED: Single-pass category builder
   * Processes all transactions once instead of 3 separate loops
   */
  function buildAllCategoriesSinglePass() {
    const currentVisibilityHash = getVisibilityHash()
    
    // Return memoized data if visibility hasn't changed
    if (memoizedCategoryData.value && lastVisibilityHash.value === currentVisibilityHash) {
      return memoizedCategoryData.value
    }
    
    const expensesByCategory = {}
    const incomeByCategory = {}
    const transfersByCategory = {}
    const currentGroupingValue = currentGrouping.value
    
    const allCategories = [
      ...expenseCategories.value,
      ...incomeCategories.value,
      ...transferCategories.value,
      ...targetCategories.value
    ]
    
    // SINGLE PASS through all transactions
    transactions.value.forEach(t => {
      const mainCat = (t.main_category || '').toUpperCase()
      const subcategoryName = t.subcategory
      const categoryName = t.category || 'Uncategorized'
      const amount = Math.abs(parseFloat(t.amount))
      const rawAmount = parseFloat(t.amount)
      
      // Determine display name and visibility
      const parentCategory = subcategoryName ? findParentCategory(allCategories, subcategoryName) : null
      let displayName = categoryName
      let shouldInclude = true
      
      if (parentCategory) {
        if (!isCategoryVisible(parentCategory.id)) {
          shouldInclude = false
        } else {
          if (isCategoryExpanded(parentCategory.id)) {
            if (subcategoryName) {
              const subcategoryId = findCategoryId(categoryStore.categories, subcategoryName)
              if (subcategoryId && isSubcategoryVisible(subcategoryId)) {
                displayName = subcategoryName
              } else {
                shouldInclude = false
              }
            } else {
              displayName = categoryName
            }
          } else {
            displayName = parentCategory.name
          }
        }
      } else {
        const categoryId = findCategoryId(categoryStore.categories, categoryName)
        if (categoryId && isCategoryVisible(categoryId)) {
          displayName = categoryName
        } else {
          shouldInclude = false
        }
      }
      
      if (!shouldInclude) return
      
      // Calculate date key once
      const date = new Date(t.posted_at)
      let key
      
      if (currentGroupingValue === 'year') {
        const yearStart = new Date(date.getFullYear(), 0, 1)
        key = yearStart.getTime()
      } else if (currentGroupingValue === 'quarter') {
        const quarter = Math.floor(date.getMonth() / 3)
        const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
        key = quarterStart.getTime()
      } else if (currentGroupingValue === 'month') {
        const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
        key = monthStart.getTime()
      } else {
        key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
      }
      
      // Add to appropriate category map
      if (mainCat === 'EXPENSES') {
        if (!expensesByCategory[displayName]) {
          expensesByCategory[displayName] = new Map()
        }
        expensesByCategory[displayName].set(
          key,
          (expensesByCategory[displayName].get(key) || 0) + amount
        )
      } else if (mainCat === 'INCOME') {
        if (!incomeByCategory[displayName]) {
          incomeByCategory[displayName] = new Map()
        }
        incomeByCategory[displayName].set(
          key,
          (incomeByCategory[displayName].get(key) || 0) + amount
        )
      } else if (mainCat === 'TRANSFERS') {
        if (!transfersByCategory[displayName]) {
          transfersByCategory[displayName] = new Map()
        }
        transfersByCategory[displayName].set(
          key,
          (transfersByCategory[displayName].get(key) || 0) + rawAmount
        )
      }
    })
    
    // Memoize result
    const result = { expensesByCategory, incomeByCategory, transfersByCategory }
    memoizedCategoryData.value = result
    lastVisibilityHash.value = currentVisibilityHash
    
    return result
  }
  
  /**
   * Build expenses by category for chart series (DEPRECATED - now uses single pass)
   */
  function buildExpensesByCategory() {
    return buildAllCategoriesSinglePass().expensesByCategory
  }
  
  /**
   * Build income by category for chart series (DEPRECATED - now uses single pass)
   */
  function buildIncomeByCategory() {
    return buildAllCategoriesSinglePass().incomeByCategory
  }
  
  /**
   * Build transfers by category for chart series (DEPRECATED - now uses single pass)
   */
  function buildTransfersByCategory() {
    return buildAllCategoriesSinglePass().transfersByCategory
  }
  
  /**
   * Build chart series - TWO Y-AXES VERSION
   */
  const chartSeries = computed(() => {
    if (!timelineData.value.length) return []
    
    const series = []
    
    // ========== NEGATIVE AXIS (expenses + negative transfers) ==========
    const expenseSeries = []
    const negativeTransferSeries = []
    
    if (isTypeVisible('expenses')) {
      const expensesByCategory = buildExpensesByCategory()
      
      Object.entries(expensesByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const data = timelineData.value.map(d => ({
          x: d.date,
          y: -(dateMap.get(d.date) || 0)
        }))
        
        expenseSeries.push({
          name: categoryName,
          type: 'bar',
          data: data,
          color: color
        })
      })
    }
    
    if (isTypeVisible('transfers')) {
      const transfersByCategory = buildTransfersByCategory()
      
      Object.entries(transfersByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const negativeData = timelineData.value.map(d => {
          const value = dateMap.get(d.date) || 0
          return { x: d.date, y: value < 0 ? value : 0 }
        })
        
        if (negativeData.some(p => p.y < 0)) {
          negativeTransferSeries.push({
            name: `${categoryName} (Out)`,
            type: 'bar',
            data: negativeData,
            color: color
          })
        }
      })
    }
    
    expenseSeries.sort((a, b) => a.name.localeCompare(b.name))
    negativeTransferSeries.sort((a, b) => a.name.localeCompare(b.name))
    
    series.push(...expenseSeries)
    series.push(...negativeTransferSeries)
    
    // ========== POSITIVE AXIS (income + positive transfers) ==========
    const incomeSeries = []
    const positiveTransferSeries = []
    
    if (isTypeVisible('income')) {
      const incomeByCategory = buildIncomeByCategory()
      
      Object.entries(incomeByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const data = timelineData.value.map(d => ({
          x: d.date,
          y: Math.abs(dateMap.get(d.date) || 0)
        }))
        
        incomeSeries.push({
          name: categoryName,
          type: 'bar',
          data: data,
          color: color
        })
      })
    }
    
    if (isTypeVisible('transfers')) {
      const transfersByCategory = buildTransfersByCategory()
      
      Object.entries(transfersByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const positiveData = timelineData.value.map(d => {
          const value = dateMap.get(d.date) || 0
          return { x: d.date, y: value > 0 ? value : 0 }
        })
        
        if (positiveData.some(p => p.y > 0)) {
          positiveTransferSeries.push({
            name: `${categoryName} (In)`,
            type: 'bar',
            data: positiveData,
            color: color
          })
        }
      })
    }
    
    incomeSeries.sort((a, b) => a.name.localeCompare(b.name))
    positiveTransferSeries.sort((a, b) => a.name.localeCompare(b.name))
    
    series.push(...incomeSeries)
    series.push(...positiveTransferSeries)
    
    return series
  })
  
  /**
   * Calculate max Y-axis values from chart series
   * For level 1, only calculate from visible date range
   */
  function calculateYAxisMax() {
    if (!chartSeries.value.length || !timelineData.value.length) {
      return { maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false }
    }
    
    let maxPositive = 0
    let maxNegative = 0
    let hasPositive = false
    let hasNegative = false
    
    // Filter to visible range if on level 1
    const visibleRange = visibleDateRange.value
    const dataToAnalyze = (currentZoomLevel.value === 1 && visibleRange)
      ? timelineData.value.filter(d => {
          const date = d.date
          return date >= visibleRange.start.getTime() && date <= visibleRange.end.getTime()
        })
      : timelineData.value
    
    dataToAnalyze.forEach((dataPoint, index) => {
      // Find actual index in full timeline for series lookup
      const actualIndex = timelineData.value.findIndex(d => d.date === dataPoint.date)
      if (actualIndex === -1) return
      
      let cumulativePositive = 0
      let cumulativeNegative = 0
      
      chartSeries.value.forEach(series => {
        const point = series.data[actualIndex]
        if (point && point.y) {
          if (point.y > 0) {
            cumulativePositive += point.y
            hasPositive = true
          } else if (point.y < 0) {
            cumulativeNegative += point.y
            hasNegative = true
          }
        }
      })
      
      if (cumulativePositive > maxPositive) {
        maxPositive = cumulativePositive
      }
      if (cumulativeNegative < maxNegative) {
        maxNegative = cumulativeNegative
      }
    })
    
    maxPositive = maxPositive * 1.15
    maxNegative = maxNegative * 1.15
    
    return {
      maxPositive,
      maxNegative: Math.abs(maxNegative),
      hasPositive,
      hasNegative
    }
  }
  
  /**
   * Handle chart hover event
   */
  function handleChartHover(config) {
    if (!config || config.dataPointIndex === -1) return
    
    const dataPoint = timelineData.value[config.dataPointIndex]
    if (!dataPoint) return
    
    hoveredData.value = {
      date: dataPoint.date,
      periodName: getPeriodName(dataPoint.date, currentGrouping.value),
      income: dataPoint.income,
      expenses: dataPoint.expenses,
      transfers: dataPoint.transfers,
      balance: dataPoint.income - dataPoint.expenses,
      incomeByCategory: dataPoint.incomeByCategory,
      expensesByCategory: dataPoint.expensesByCategory,
      transfersByCategory: dataPoint.transfersByCategory
    }
    
    // Update line annotation without rebuilding entire chart
    updateLineAnnotation()
  }
  
  /**
   * Update vertical line annotation
   */
  function updateLineAnnotation() {
    // Direct annotation update is faster than recomputing entire chartOptions
    const chart = chartRef?.value?.chart
    if (!chart || !hoveredData.value) return
    
    chart.clearAnnotations()
    
    // Add horizontal line at zero
    chart.addYaxisAnnotation({
      y: 0,
      borderColor: '#374151',
      borderWidth: 0.5,
      opacity: 0.2
    })
    
    // Add vertical line at hovered position
    chart.addXaxisAnnotation({
      x: hoveredData.value.date,
      borderColor: isPinned.value ? '#3a3a3aff' : '#5b636eff',
      strokeDashArray: isPinned.value ? 0 : 5,
      borderWidth: isPinned.value ? 2 : 1,
      opacity: isPinned.value ? 1 : 0.6
    })
  }
  
  /**
   * Unpin hover data
   */
  function unpinHoverData() {
    isPinned.value = false
    hoveredData.value = null
    
    const chart = chartRef?.value?.chart
    if (chart) {
      chart.clearAnnotations()
      chart.addYaxisAnnotation({
        y: 0,
        borderColor: '#374151',
        borderWidth: 2,
        opacity: 0.8
      })
    }
  }
  
  // Watch for pin state changes
  watch(() => isPinned.value, () => {
    if (hoveredData.value) {
      updateLineAnnotation()
    }
  })
  
  // Debounced visibility watcher - only recalculate after 50ms of no changes
  let visibilityDebounceTimer = null
  watch([
    () => visibilityState.visibleCategories.value,
    () => visibilityState.visibleSubcategories.value,
    () => visibilityState.expandedCategories.value
  ], () => {
    if (visibilityDebounceTimer) {
      clearTimeout(visibilityDebounceTimer)
    }
    visibilityDebounceTimer = setTimeout(() => {
      // Invalidate memoization cache
      memoizedCategoryData.value = null
      yAxisValues.value = calculateYAxisMax()
      console.log('📏 Y-axis recalculated after visibility change')
    }, 50)
  }, { deep: true })
  
  // Recalculate Y-axis ONLY on zoom (immediate, no debounce)
  watch(currentZoomLevel, () => {
    memoizedCategoryData.value = null // Invalidate cache
    yAxisValues.value = calculateYAxisMax()
    console.log('📏 Y-axis recalculated on zoom')
  })
  
  // Update X-axis range via updateOptions when scrollbar changes (no rebuild)
  watch(() => visibleDateRange.value, (newRange, oldRange) => {
    const chart = chartRef?.value?.chart
    if (!chart || !newRange) return
    
    // On level 1, recalculate Y-axis for the visible range whenever it changes
    if (currentZoomLevel.value === 1) {
      // Force recalculation by invalidating cache
      memoizedCategoryData.value = null
      yAxisValues.value = calculateYAxisMax()
      console.log('📏 Y-axis recalculated for year range:', yAxisValues.value)
    }
    
    // Update x-axis without animation
    chart.updateOptions({
      xaxis: {
        min: newRange.start.getTime(),
        max: newRange.end.getTime()
      },
      yaxis: {
        min: yAxisValues.value.hasPositive && yAxisValues.value.hasNegative 
          ? -Math.max(yAxisValues.value.maxPositive, yAxisValues.value.maxNegative)
          : yAxisValues.value.hasPositive ? 0 : -yAxisValues.value.maxNegative,
        max: yAxisValues.value.hasPositive && yAxisValues.value.hasNegative
          ? Math.max(yAxisValues.value.maxPositive, yAxisValues.value.maxNegative)
          : yAxisValues.value.hasPositive ? yAxisValues.value.maxPositive : 0
      }
    }, false, false) // false = no redraw, false = no animation
    
    console.log('📊 X-axis and Y-axis updated')
  }, { deep: true })
  
  /**
   * Build chart options - TWO Y-AXES VERSION
   */
const chartOptions = computed(() => {
  const range = visibleDateRange.value
  const yAxis = yAxisValues.value
  
  // Dynamic zero-line positioning
  let yMin, yMax
  
  if (yAxis.hasPositive && yAxis.hasNegative) {
    const maxRange = Math.max(yAxis.maxPositive, yAxis.maxNegative)
    yMin = -maxRange
    yMax = maxRange
  } else if (yAxis.hasPositive && !yAxis.hasNegative) {
    yMin = 0
    yMax = yAxis.maxPositive
  } else if (!yAxis.hasPositive && yAxis.hasNegative) {
    yMin = -yAxis.maxNegative
    yMax = 0
  } else {
    yMin = -1000
    yMax = 1000
  }
  
  return {
    chart: {
      id: 'timeline-main',
      type: 'bar',
      height: 500,
      stacked: true,
      stackType: 'normal',
      toolbar: {
        show: false
      },
      zoom: {
        enabled: false
      },
      animations: {
        enabled: false,
        easing: 'linear',
        speed: 0,
        animateGradually: {
          enabled: false,
          delay: 0
        },
        dynamicAnimation: {
          enabled: false,
          speed: 0
        }
      },
      events: {
        dataPointSelection: (event, chartContext, config) => {
          if (config.dataPointIndex >= 0) {
            // Pin to new position
            isPinned.value = true
            handleChartHover(config)
          }
        },
        mouseMove: (event, chartContext, config) => {
          // Only update hover if not pinned
          if (!isPinned.value && config.dataPointIndex >= 0) {
            handleChartHover(config)
          }
        },
        mouseLeave: () => {
          if (!isPinned.value) {
            hoveredData.value = null
          }
        }
      },
      selection: {
        enabled: false
      }
    },
    states: {
      normal: {
        filter: {
          type: 'none'
        }
      },
      hover: {
        filter: {
          type: 'none'
        }
      },
      active: {
        filter: {
          type: 'none'
        }
      }
    },
    fill: {
      opacity: 1,
      type: 'solid'
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: '98%',
        borderRadius: 0,
        borderRadiusApplication: 'end',
        borderRadiusWhenStacked: 'last',
        dataLabels: {
          position: 'center'
        }
      }
    },
    stroke: {
      show: true,
      width: 0,
      colors: ['transparent']
    },
    dataLabels: {
      enabled: false
    },
    legend: {
      show: false
    },
    grid: {
      borderColor: '#e5e7eb',
      strokeDashArray: 5,
      xaxis: {
        lines: {
          show: true
        }
      },
      yaxis: {
        lines: {
          show: true
        }
      }
    },
    xaxis: {
      type: 'datetime',
      min: range?.start?.getTime(),
      max: range?.end?.getTime(),
      labels: {
        datetimeUTC: false,
        style: {
          colors: '#6b7280',
          fontSize: '12px'
        }
      }
    },
    yaxis: {
      title: {
        text: 'Amount (€)',
        style: {
          color: '#6b7280',
          fontSize: '12px',
          fontWeight: 500
        }
      },
      labels: {
        formatter: (val) => {
          if (val === 0) return '€0'
          const absVal = Math.abs(val)
          return (val < 0 ? '-' : '') + '€' + Math.round(absVal).toLocaleString()
        },
        style: {
          colors: '#6b7280',
          fontSize: '12px'
        }
      },
      min: yMin,
      max: yMax
    },
    tooltip: {
      enabled: false
    }
  }
})
  
  return {
    hoveredData,
    isPinned,
    chartSeries,
    chartOptions,
    expenseCategories,
    incomeCategories,
    transferCategories,
    targetCategories,
    visibleDateRange,
    handleChartHover,
    unpinHoverData
  }
}