// frontend/src/composables/useTimelineChart.js

import { ref, computed, watch } from 'vue'
import { 
  calculateVisibleDateRange, 
  getCategoryColor, 
  findCategoryId,
  findParentCategory 
} from '@/utils/timelineHelpers'

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
  customVisibleRange = null
) {
  const hoveredData = ref(null)
  const isPinned = ref(false)
  
  const {
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded
  } = visibilityState
  
  // Get category arrays - NOW INCLUDES targetCategories
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
  
  // Calculate visible date range - use custom if provided, otherwise calculate from zoom
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
  
  /**
   * Build expenses by category for chart series
   */
  function buildExpensesByCategory() {
    const expensesByCategory = {}
    const currentGroupingValue = timelineData.value[0] ? 
      (timelineData.value[1]?.date - timelineData.value[0]?.date > 86400000 * 60 ? 'quarter' : 
       timelineData.value[1]?.date - timelineData.value[0]?.date > 86400000 * 25 ? 'month' : 'day') : 'day'
    
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
    const currentGroupingValue = timelineData.value[0] ? 
      (timelineData.value[1]?.date - timelineData.value[0]?.date > 86400000 * 60 ? 'quarter' : 
       timelineData.value[1]?.date - timelineData.value[0]?.date > 86400000 * 25 ? 'month' : 'day') : 'day'
    
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
            (incomeByCategory[displayName].get(key) || 0) + Math.abs(amount)  // Force positive
          )
      })
    
    return incomeByCategory
  }
  
  /**
   * Build transfers by category for chart series
   */
  function buildTransfersByCategory() {
    const transfersByCategory = {}
    const currentGroupingValue = timelineData.value[0] ? 
      (timelineData.value[1]?.date - timelineData.value[0]?.date > 86400000 * 60 ? 'quarter' : 
       timelineData.value[1]?.date - timelineData.value[0]?.date > 86400000 * 25 ? 'month' : 'day') : 'day'
    
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
   * Build chart series from visible data
   * FIXED: Transfers now stack correctly based on their sign
   * FIXED: Alphabetical order for predictable stacking
   * FIXED: Gradient fill for fade-out effect from zero line
   */
const chartSeries = computed(() => {
  if (!timelineData.value.length) return []
  
  const series = []
  
  // ========== BUILD NEGATIVE STACK ==========
  const expenseSeries = []
  const negativeTransferSeries = []
  
  // 1. Build expenses
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
        type: 'area',
        data: data,
        color: color,
        fillColor: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.9,
            opacityTo: 0.3,
            stops: [0, 100]
          }
        }
      })
    })
  }
  
  // 2. Build NEGATIVE transfers BEFORE sorting
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
          type: 'area',
          data: negativeData,
          color: color,
          fillColor: {
            type: 'gradient',
            gradient: {
              shadeIntensity: 1,
              opacityFrom: 0.9,
              opacityTo: 0.3,
              stops: [0, 100]
            }
          }
        })
      }
    })
  }
  
  // 3. NOW sort and add to series
  expenseSeries.sort((a, b) => a.name.localeCompare(b.name))
  negativeTransferSeries.sort((a, b) => a.name.localeCompare(b.name))
  
  series.push(...expenseSeries)
  series.push(...negativeTransferSeries)
  
  // ========== BUILD POSITIVE STACK ==========
  const incomeSeries = []
  const positiveTransferSeries = []
  
  // 4. Build income
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
        type: 'area',
        data: data,
        color: color,
        fillColor: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.9,
            opacityTo: 0.3,
            stops: [0, 100]
          }
        }
      })
    })
  }
  
  // 5. Build POSITIVE transfers BEFORE sorting
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
          type: 'area',
          data: positiveData,
          color: color,
          fillColor: {
            type: 'gradient',
            gradient: {
              shadeIntensity: 1,
              opacityFrom: 0.9,
              opacityTo: 0.3,
              stops: [0, 100]
            }
          }
        })
      }
    })
  }
  
  // 6. NOW sort and add to series
  incomeSeries.sort((a, b) => a.name.localeCompare(b.name))
  positiveTransferSeries.sort((a, b) => a.name.localeCompare(b.name))
  
  series.push(...incomeSeries)
  series.push(...positiveTransferSeries)
  
  return series
})
  
  /**
   * Calculate max Y-axis value with dynamic zero-line positioning
   * Power BI style: zero line moves based on data
   * CRITICAL FIX: Calculate CUMULATIVE stacked values, not individual series max
   */
  const yAxisMax = computed(() => {
    if (!chartSeries.value.length || !timelineData.value.length) {
      return { maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false }
    }
    
    let maxPositive = 0
    let maxNegative = 0
    let hasPositive = false
    let hasNegative = false
    
    // For each date point, calculate STACKED TOTALS
    timelineData.value.forEach((dataPoint, index) => {
      let cumulativePositive = 0
      let cumulativeNegative = 0
      
      // Sum up all series values at this date point
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
      
      // Track the maximum cumulative values
      if (cumulativePositive > maxPositive) {
        maxPositive = cumulativePositive
      }
      if (cumulativeNegative < maxNegative) {
        maxNegative = cumulativeNegative
      }
    })
    
    // Add 15% padding for better visibility
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
      income: dataPoint.income,
      expenses: dataPoint.expenses,
      transfers: dataPoint.transfers,
      balance: dataPoint.income - dataPoint.expenses,
      incomeByCategory: dataPoint.incomeByCategory,
      expensesByCategory: dataPoint.expensesByCategory,
      transfersByCategory: dataPoint.transfersByCategory
    }
  }
  
  /**
   * Unpin hover data
   */
  function unpinHoverData() {
    isPinned.value = false
    hoveredData.value = null
  }
  
  /**
   * Build chart options - NOW WITH DYNAMIC ZERO-LINE POSITIONING (Power BI style)
   */
  const chartOptions = computed(() => {
    const range = visibleDateRange.value
    const yAxis = yAxisMax.value
    
    // POWER BI LOGIC: Dynamic zero-line positioning
    let yMin, yMax
    
    if (yAxis.hasPositive && yAxis.hasNegative) {
      // Both income and expenses: zero in middle
      const maxRange = Math.max(yAxis.maxPositive, yAxis.maxNegative)
      yMin = -maxRange
      yMax = maxRange
    } else if (yAxis.hasPositive && !yAxis.hasNegative) {
      // Only income/positive: zero at bottom
      yMin = 0
      yMax = yAxis.maxPositive
    } else if (!yAxis.hasPositive && yAxis.hasNegative) {
      // Only expenses/negative: zero at top
      yMin = -yAxis.maxNegative
      yMax = 0
    } else {
      // No data
      yMin = -1000
      yMax = 1000
    }
    
    return {
      chart: {
        id: 'timeline-main',
        type: 'area',
        height: 500,
        stacked: true,  // Enable stacking
        stackType: 'normal',  // CRITICAL: This makes it cumulative stacking
        toolbar: {
          show: false
        },
        zoom: {
          enabled: false
        },
        animations: {
          enabled: true,  // Enable animations
          easing: 'easeinout',
          speed: 500,
          animateGradually: {
            enabled: false  // CRITICAL: Disable gradual animation - all series animate together
          },
          dynamicAnimation: {
            enabled: true,  // Enable for adding/removing series
            speed: 350  // Fast animation when toggling categories
          }
        },
        events: {
          mouseMove: (event, chartContext, config) => {
            if (config.dataPointIndex >= 0) {
              handleChartHover(config)
            }
          },
          mouseLeave: () => {
            if (!isPinned.value) {
              hoveredData.value = null
            }
          },
          click: (event, chartContext, config) => {
            if (config.dataPointIndex >= 0) {
              isPinned.value = !isPinned.value
              if (isPinned.value) {
                handleChartHover(config)
              } else {
                hoveredData.value = null
              }
            }
          }
        }
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth',
        width: 1,  // Reduced from 2 to make cleaner boundaries
        colors: undefined  // Use series colors for strokes
      },
      fill: {
        type: 'gradient'  // Use gradient fill (defined per series)
      },
      legend: {
        show: false
      },
      markers: {
        size: 0,
        hover: {
          size: 5
        }
      },
      grid: {
        borderColor: '#e5e7eb',
        strokeDashArray: 4,
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
        },
        crosshairs: {
          show: true,
          position: 'back',
          stroke: {
            color: '#374151',
            width: 2,
            dashArray: 4
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
        min: yMin,  // DYNAMIC: Changes based on visible data
        max: yMax   // DYNAMIC: Changes based on visible data
      },
      tooltip: {
        enabled: false
      },
      annotations: {
        yaxis: [{
          y: 0,
          borderColor: '#374151',
          borderWidth: 2,
          opacity: 0.8,
          label: {
            text: yAxis.hasPositive && yAxis.hasNegative ? 'Zero Line' : ''
          }
        }]
      }
    }
  })
  
  // Watch for visible range changes
  watch(() => visibleDateRange.value, (newRange) => {
    console.log('📊 Chart visible range updated:', newRange)
  }, { deep: true })
  
  return {
    // State
    hoveredData,
    isPinned,
    
    // Computed - NOW INCLUDES targetCategories
    chartSeries,
    chartOptions,
    expenseCategories,
    incomeCategories,
    transferCategories,
    targetCategories,
    visibleDateRange,
    
    // Actions
    handleChartHover,
    unpinHoverData
  }
}