// frontend/src/composables/useTimelineChart.js

import { ref, computed } from 'vue'
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
  visibilityState
) {
  const hoveredData = ref(null)
  const isPinned = ref(false)
  
  const {
    visibleTypes,
    visibleCategories,
    visibleSubcategories,
    expandedCategories,
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
  
  // Calculate visible date range
  const visibleDateRange = computed(() => {
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
          ...transferCategories.value
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
          ...transferCategories.value
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
          (incomeByCategory[displayName].get(key) || 0) + amount
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
          ...transferCategories.value
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
   */
  const chartSeries = computed(() => {
    if (!timelineData.value.length) return []
    
    const series = []
    
    // Build series based on visible types
    if (isTypeVisible('expenses')) {
      const expensesByCategory = buildExpensesByCategory()
      
      Object.entries(expensesByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const data = timelineData.value.map(d => ({
          x: d.date,
          y: -(dateMap.get(d.date) || 0) // Negative for expenses
        }))
        
        series.push({
          name: categoryName,
          type: 'line',
          data: data,
          color: color
        })
      })
    }
    
    if (isTypeVisible('income')) {
      const incomeByCategory = buildIncomeByCategory()
      
      Object.entries(incomeByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const data = timelineData.value.map(d => ({
          x: d.date,
          y: dateMap.get(d.date) || 0 // Positive for income
        }))
        
        series.push({
          name: categoryName,
          type: 'line',
          data: data,
          color: color
        })
      })
    }
    
    if (isTypeVisible('transfers')) {
      const transfersByCategory = buildTransfersByCategory()
      
      Object.entries(transfersByCategory).forEach(([categoryName, dateMap]) => {
        const color = getCategoryColor(categoryStore.categories, categoryName)
        
        const data = timelineData.value.map(d => ({
          x: d.date,
          y: dateMap.get(d.date) || 0
        }))
        
        series.push({
          name: categoryName,
          type: 'line',
          data: data,
          color: color
        })
      })
    }
    
    return series
  })
  
  /**
   * Calculate max Y-axis value
   */
  const yAxisMax = computed(() => {
    if (!chartSeries.value.length) return 1000
    
    let maxPositive = 0
    let maxNegative = 0
    
    chartSeries.value.forEach(series => {
      series.data.forEach(point => {
        const val = point.y
        if (val > maxPositive) maxPositive = val
        if (val < maxNegative) maxNegative = val
      })
    })
    
    const maxValue = Math.max(maxPositive, Math.abs(maxNegative))
    return maxValue * 1.1 // 10% padding
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
   * Build chart options
   */
  const chartOptions = computed(() => {
    const range = visibleDateRange.value
    
    return {
      chart: {
        id: 'timeline-main',
        type: 'line',
        height: 500,
        stacked: false,
        toolbar: {
          show: false
        },
        zoom: {
          enabled: false
        },
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800
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
        width: 2
      },
      fill: {
        type: 'solid',
        opacity: 1
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
        min: -yAxisMax.value,
        max: yAxisMax.value
      },
      tooltip: {
        enabled: false
      },
      annotations: {
        yaxis: [{
          y: 0,
          borderColor: '#374151',
          borderWidth: 2,
          opacity: 0.8
        }]
      }
    }
  })
  
  return {
    // State
    hoveredData,
    isPinned,
    
    // Computed
    chartSeries,
    chartOptions,
    expenseCategories,
    incomeCategories,
    transferCategories,
    
    // Actions
    handleChartHover,
    unpinHoverData
  }
}