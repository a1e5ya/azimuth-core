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
  
  if (grouping === 'day') {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
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
    if (!timelineData.value[0] || !timelineData.value[1]) return 'day'
    const diff = timelineData.value[1]?.date - timelineData.value[0]?.date
    if (diff > 86400000 * 60) return 'quarter'
    if (diff > 86400000 * 25) return 'month'
    return 'day'
  })
  
  /**
   * Build expenses by category for chart series
   */
  function buildExpensesByCategory() {
    const expensesByCategory = {}
    const currentGroupingValue = currentGrouping.value
    
    transactions.value
      .filter(t => {
        const mainCat = (t.main_category || '').toUpperCase()
        return mainCat === 'EXPENSES'
      })
      .forEach(t => {
        const subcategoryName = t.subcategory
        const categoryName = t.category || 'Uncategorized'
        const amount = Math.abs(parseFloat(t.amount))
        
        const allCategories = [
          ...expenseCategories.value,
          ...incomeCategories.value,
          ...transferCategories.value,
          ...targetCategories.value
        ]
        
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
        
        if (!expensesByCategory[displayName]) {
          expensesByCategory[displayName] = new Map()
        }
        
        const date = new Date(t.posted_at)
        let key
        
        if (currentGroupingValue === 'quarter') {
          const quarter = Math.floor(date.getMonth() / 3)
          const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
          key = quarterStart.getTime()
        } else if (currentGroupingValue === 'month') {
          const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
          key = monthStart.getTime()
        } else {
          key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
        }
        
        expensesByCategory[displayName].set(
          key, 
          (expensesByCategory[displayName].get(key) || 0) + amount
        )
      })
    
    return expensesByCategory
  }
  
  /**
   * Build income by category for chart series
   */
  function buildIncomeByCategory() {
    const incomeByCategory = {}
    const currentGroupingValue = currentGrouping.value
    
    transactions.value
      .filter(t => {
        const mainCat = (t.main_category || '').toUpperCase()
        return mainCat === 'INCOME'
      })
      .forEach(t => {
        const subcategoryName = t.subcategory
        const categoryName = t.category || 'Income'
        const amount = Math.abs(parseFloat(t.amount))
        
        const allCategories = [
          ...expenseCategories.value,
          ...incomeCategories.value,
          ...transferCategories.value,
          ...targetCategories.value
        ]
        
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
        
        if (!incomeByCategory[displayName]) {
          incomeByCategory[displayName] = new Map()
        }
        
        const date = new Date(t.posted_at)
        let key
        
        if (currentGroupingValue === 'quarter') {
          const quarter = Math.floor(date.getMonth() / 3)
          const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
          key = quarterStart.getTime()
        } else if (currentGroupingValue === 'month') {
          const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
          key = monthStart.getTime()
        } else {
          key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
        }
        
        incomeByCategory[displayName].set(
          key,
          (incomeByCategory[displayName].get(key) || 0) + Math.abs(amount)
        )
      })
    
    return incomeByCategory
  }
  
  /**
   * Build transfers by category for chart series
   */
  function buildTransfersByCategory() {
    const transfersByCategory = {}
    const currentGroupingValue = currentGrouping.value
    
    transactions.value
      .filter(t => {
        const mainCat = (t.main_category || '').toUpperCase()
        return mainCat === 'TRANSFERS'
      })
      .forEach(t => {
        const subcategoryName = t.subcategory
        const categoryName = t.category || 'Transfer'
        const amount = parseFloat(t.amount)
        
        const allCategories = [
          ...expenseCategories.value,
          ...incomeCategories.value,
          ...transferCategories.value,
          ...targetCategories.value
        ]
        
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
        
        if (!transfersByCategory[displayName]) {
          transfersByCategory[displayName] = new Map()
        }
        
        const date = new Date(t.posted_at)
        let key
        
        if (currentGroupingValue === 'quarter') {
          const quarter = Math.floor(date.getMonth() / 3)
          const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
          key = quarterStart.getTime()
        } else if (currentGroupingValue === 'month') {
          const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
          key = monthStart.getTime()
        } else {
          key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
        }
        
        transfersByCategory[displayName].set(
          key,
          (transfersByCategory[displayName].get(key) || 0) + amount
        )
      })
    
    return transfersByCategory
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
   * Calculate max Y-axis values
   */
  const yAxisMax = computed(() => {
    if (!chartSeries.value.length || !timelineData.value.length) {
      return { maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false }
    }
    
    let maxPositive = 0
    let maxNegative = 0
    let hasPositive = false
    let hasNegative = false
    
    timelineData.value.forEach((dataPoint, index) => {
      let cumulativePositive = 0
      let cumulativeNegative = 0
      
      chartSeries.value.forEach(series => {
        const point = series.data[index]
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
  })
  
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
  
  /**
   * Build chart options - TWO Y-AXES VERSION
   */
const chartOptions = computed(() => {
  const range = visibleDateRange.value
  const yAxis = yAxisMax.value
  
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
        enabled: true,
        easing: 'easeinout',
        speed: 200,
        animateGradually: {
          enabled: false
        },
        dynamicAnimation: {
          enabled: false
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
  
  watch(() => visibleDateRange.value, (newRange) => {
    console.log('📊 Chart visible range updated:', newRange)
  }, { deep: true })
  
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