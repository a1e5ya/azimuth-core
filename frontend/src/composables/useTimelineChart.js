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
 * Composable for managing timeline chart configuration and series WITH BREAKDOWN
 */
export function useTimelineChart(
  timelineData,
  transactions,
  dateRange,
  currentZoomLevel,
  categoryStore,
  visibilityState,
  customVisibleRange = null,
  chartRef = null,
  breakdownMode = ref('all'),
  selectedOwners = ref([]),
  selectedAccounts = ref([])
) {
  const hoveredData = ref(null)
  const isPinned = ref(false)
  const yAxisValues = ref({ maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false })
  
  const memoizedCategoryData = ref(null)
  const lastVisibilityHash = ref('')
  
  const {
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded
  } = visibilityState
  
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
  
  const currentGrouping = computed(() => {
    if (!timelineData.value[0] || !timelineData.value[1]) return 'quarter'
    const diff = timelineData.value[1]?.date - timelineData.value[0]?.date
    if (diff > 86400000 * 300) return 'year'
    if (diff > 86400000 * 60) return 'quarter'
    return 'month'
  })
  
  /**
   * Get breakdown keys based on mode
   */
  const breakdownKeys = computed(() => {
    if (breakdownMode.value === 'all') {
      return ['all']
    } else if (breakdownMode.value === 'owner') {
      return selectedOwners.value
    } else if (breakdownMode.value === 'account') {
      return selectedAccounts.value
    }
    return ['all']
  })
  
  function getVisibilityHash() {
    return JSON.stringify({
      types: visibilityState.visibleTypes.value.slice().sort(),
      cats: visibilityState.visibleCategories.value.slice().sort(),
      subcats: visibilityState.visibleSubcategories.value.slice().sort(),
      expanded: visibilityState.expandedCategories.value.slice().sort(),
      breakdown: breakdownMode.value,
      owners: selectedOwners.value.slice().sort(),
      accounts: selectedAccounts.value.slice().sort()
    })
  }
  
  /**
   * Build categories WITH BREAKDOWN - separate by owner/account
   * FIX: Only filter by owner/account when NOT in 'all' mode
   */
  function buildAllCategoriesSinglePass() {
    const currentVisibilityHash = getVisibilityHash()
    
    if (memoizedCategoryData.value && lastVisibilityHash.value === currentVisibilityHash) {
      return memoizedCategoryData.value
    }

    if (!categoryStore.categories || categoryStore.categories.length === 0) {
      console.warn('⚠️ Categories not loaded yet')
      return { 
        expensesByBreakdown: {}, 
        incomeByBreakdown: {}, 
        transfersNegativeByBreakdown: {},
        transfersPositiveByBreakdown: {}
      }
    }
    
    console.log('🔄 Building categories - Mode:', breakdownMode.value, 'Keys:', breakdownKeys.value)
    
    // Structure: { breakdownKey: { categoryName: Map<date, amount> } }
    const expensesByBreakdown = {}
    const incomeByBreakdown = {}
    const transfersNegativeByBreakdown = {}
    const transfersPositiveByBreakdown = {}
    
    const currentGroupingValue = currentGrouping.value
    const allCategories = [
      ...expenseCategories.value,
      ...incomeCategories.value,
      ...transferCategories.value,
      ...targetCategories.value
    ]
    
    // Initialize breakdown keys
    breakdownKeys.value.forEach(key => {
      expensesByBreakdown[key] = {}
      incomeByBreakdown[key] = {}
      transfersNegativeByBreakdown[key] = {}
      transfersPositiveByBreakdown[key] = {}
    })
    
    let processedCount = 0
    let skippedByMode = 0
    let skippedByVisibility = 0
    
    transactions.value.forEach(t => {
      // Determine breakdown key for this transaction
      let breakdownKey = 'all'
      
      if (breakdownMode.value === 'owner') {
        if (!t.owner) return
        breakdownKey = t.owner
        if (!selectedOwners.value.includes(breakdownKey)) {
          skippedByMode++
          return
        }
      } else if (breakdownMode.value === 'account') {
        if (!t.owner || !t.bank_account_type) return
        breakdownKey = `${t.owner}_${t.bank_account_type}`
        if (!selectedAccounts.value.includes(breakdownKey)) {
          skippedByMode++
          return
        }
      }
      // For 'all' mode: breakdownKey='all' and we process ALL transactions
      
      const mainCat = (t.main_category || '').toUpperCase()
      const subcategoryName = t.subcategory
      const categoryName = t.category || 'Uncategorized'
      const amount = Math.abs(parseFloat(t.amount))
      const rawAmount = parseFloat(t.amount)
      
      // Debug: log Savings Transfer transactions
      if (mainCat === 'TRANSFERS' && (subcategoryName === 'Savings Transfer' || categoryName === 'Savings Transfer')) {
        console.log('🔍 Processing Savings Transfer transaction:', {
          category: categoryName,
          subcategory: subcategoryName,
          amount: rawAmount
        })
      }
      
      const parentCategory = subcategoryName ? findParentCategory(allCategories, subcategoryName) : null
      let displayName = categoryName
      let shouldInclude = true
      
      // Check category visibility
      // First check if the TYPE is visible
      if (mainCat === 'INCOME' && !isTypeVisible('income')) {
        shouldInclude = false
      } else if (mainCat === 'EXPENSES' && !isTypeVisible('expenses')) {
        shouldInclude = false
      } else if (mainCat === 'TRANSFERS' && !isTypeVisible('transfers')) {
        shouldInclude = false
      } else if (parentCategory) {
        // Has a parent category
        if (!isCategoryVisible(parentCategory.id)) {
          shouldInclude = false
        } else if (isCategoryExpanded(parentCategory.id)) {
          // Parent is expanded - show subcategory if visible
          if (subcategoryName) {
            const subcategoryId = findCategoryId(categoryStore.categories, subcategoryName)
            if (subcategoryId && !isSubcategoryVisible(subcategoryId)) {
              shouldInclude = false
            } else {
              displayName = subcategoryName
            }
          } else {
            displayName = categoryName
          }
        } else {
          // Parent not expanded - group under parent
          displayName = parentCategory.name
        }
      } else {
        // No parent category - check if category itself is visible
        const categoryId = findCategoryId(categoryStore.categories, categoryName)
        if (categoryId && !isCategoryVisible(categoryId)) {
          shouldInclude = false
        } else {
          displayName = subcategoryName || categoryName
        }
      }
      
      if (!shouldInclude) {
        if (mainCat === 'TRANSFERS' && (subcategoryName === 'Savings Transfer' || categoryName === 'Savings Transfer')) {
          console.log('❌ HIDING Savings Transfer:', {
            subcategoryName,
            categoryName,
            displayName,
            parentCategory: parentCategory?.name,
            parentId: parentCategory?.id,
            parentVisible: parentCategory ? isCategoryVisible(parentCategory.id) : 'no parent',
            parentExpanded: parentCategory ? isCategoryExpanded(parentCategory.id) : 'no parent'
          })
        }
        skippedByVisibility++
        return
      }
      
      if (mainCat === 'TRANSFERS' && (subcategoryName === 'Savings Transfer' || categoryName === 'Savings Transfer')) {
        console.log('✅ SHOWING Savings Transfer:', {
          subcategoryName,
          categoryName,
          displayName,
          parentCategory: parentCategory?.name,
          parentExpanded: parentCategory ? isCategoryExpanded(parentCategory.id) : 'no parent'
        })
      }
      
      processedCount++
      
      // Calculate period key
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
      
      // Add to appropriate breakdown bucket
      if (mainCat === 'EXPENSES') {
        if (!expensesByBreakdown[breakdownKey][displayName]) {
          expensesByBreakdown[breakdownKey][displayName] = new Map()
        }
        expensesByBreakdown[breakdownKey][displayName].set(
          key,
          (expensesByBreakdown[breakdownKey][displayName].get(key) || 0) + amount
        )
      } else if (mainCat === 'INCOME') {
        if (!incomeByBreakdown[breakdownKey][displayName]) {
          incomeByBreakdown[breakdownKey][displayName] = new Map()
        }
        incomeByBreakdown[breakdownKey][displayName].set(
          key,
          (incomeByBreakdown[breakdownKey][displayName].get(key) || 0) + amount
        )
      } else if (mainCat === 'TRANSFERS') {
        // Track positive and negative transfers separately 
        if (rawAmount < 0) {
          if (!transfersNegativeByBreakdown[breakdownKey][displayName]) {
            transfersNegativeByBreakdown[breakdownKey][displayName] = new Map()
          }
          transfersNegativeByBreakdown[breakdownKey][displayName].set(
            key,
            (transfersNegativeByBreakdown[breakdownKey][displayName].get(key) || 0) + amount
          )
        } else if (rawAmount > 0) {
          if (!transfersPositiveByBreakdown[breakdownKey][displayName]) {
            transfersPositiveByBreakdown[breakdownKey][displayName] = new Map()
          }
          transfersPositiveByBreakdown[breakdownKey][displayName].set(
            key,
            (transfersPositiveByBreakdown[breakdownKey][displayName].get(key) || 0) + amount
          )
        }
      }
    })
    
    console.log('📊 Processed:', processedCount, '| Skipped by mode:', skippedByMode, '| Skipped by visibility:', skippedByVisibility)
    
    const result = { expensesByBreakdown, incomeByBreakdown, transfersNegativeByBreakdown, transfersPositiveByBreakdown }
    memoizedCategoryData.value = result
    lastVisibilityHash.value = currentVisibilityHash
    
    return result
  }
  
  /**
   * Build chart series WITH BREAKDOWN - single stack per breakdown
   */
  const chartSeries = computed(() => {
    if (!timelineData.value.length) return []
    
    const { expensesByBreakdown, incomeByBreakdown, transfersNegativeByBreakdown, transfersPositiveByBreakdown } = buildAllCategoriesSinglePass()
    const series = []
    
    // For each breakdown key, create separate series with ONE stack group per breakdown
    breakdownKeys.value.forEach((breakdownKey, breakdownIndex) => {
      const suffix = breakdownMode.value === 'all' ? '' : ` - ${breakdownKey}`
      const stackGroup = breakdownMode.value === 'all' ? 'all' : `breakdown-${breakdownIndex}`
      
      // EXPENSES - all go into same stack group
      if (isTypeVisible('expenses') && expensesByBreakdown[breakdownKey]) {
        Object.entries(expensesByBreakdown[breakdownKey]).forEach(([categoryName, dateMap]) => {
          const color = getCategoryColor(categoryStore.categories, categoryName)
          
          const data = timelineData.value.map(d => ({
            x: d.date,
            y: -(dateMap.get(d.date) || 0)
          }))
          
          series.push({
            name: `${categoryName}${suffix}`,
            type: 'bar',
            data: data,
            color: color,
            breakdownKey: breakdownKey,
            group: stackGroup
          })
        })
      }
      
      // NEGATIVE TRANSFERS - same stack group
      if (isTypeVisible('transfers') && transfersNegativeByBreakdown[breakdownKey]) {
        Object.entries(transfersNegativeByBreakdown[breakdownKey]).forEach(([categoryName, dateMap]) => {
          const color = getCategoryColor(categoryStore.categories, categoryName)
          
          const negativeData = timelineData.value.map(d => ({
            x: d.date,
            y: -(dateMap.get(d.date) || 0)
          }))
          
          const hasNegative = negativeData.some(p => p.y < 0)
          
          if (hasNegative) {
            series.push({
              name: `${categoryName} (Out)${suffix}`,
              type: 'bar',
              data: negativeData,
              color: color,
              breakdownKey: breakdownKey,
              group: stackGroup
            })
          }
        })
      }
      
      // INCOME - same stack group
      if (isTypeVisible('income') && incomeByBreakdown[breakdownKey]) {
        Object.entries(incomeByBreakdown[breakdownKey]).forEach(([categoryName, dateMap]) => {
          const color = getCategoryColor(categoryStore.categories, categoryName)
          
          const data = timelineData.value.map(d => ({
            x: d.date,
            y: Math.abs(dateMap.get(d.date) || 0)
          }))
          
          series.push({
            name: `${categoryName}${suffix}`,
            type: 'bar',
            data: data,
            color: color,
            breakdownKey: breakdownKey,
            group: stackGroup
          })
        })
      }
      
      // POSITIVE TRANSFERS - same stack group
      if (isTypeVisible('transfers') && transfersPositiveByBreakdown[breakdownKey]) {
        Object.entries(transfersPositiveByBreakdown[breakdownKey]).forEach(([categoryName, dateMap]) => {
          const color = getCategoryColor(categoryStore.categories, categoryName)
          
          const positiveData = timelineData.value.map(d => ({
            x: d.date,
            y: dateMap.get(d.date) || 0
          }))
          
          const hasPositive = positiveData.some(p => p.y > 0)
          
          if (hasPositive) {
            series.push({
              name: `${categoryName} (In)${suffix}`,
              type: 'bar',
              data: positiveData,
              color: color,
              breakdownKey: breakdownKey,
              group: stackGroup
            })
          }
        })
      }
    })
    
    console.log('📊 Final series count:', series.length)
    
    return series
  })
  
  function calculateYAxisMax() {
    if (!chartSeries.value.length || !timelineData.value.length) {
      return { maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false }
    }
    
    let maxPositive = 0
    let maxNegative = 0
    let hasPositive = false
    let hasNegative = false
    
    const visibleRange = visibleDateRange.value
    const dataToAnalyze = (currentZoomLevel.value === 1 && visibleRange)
      ? timelineData.value.filter(d => {
          const date = d.date
          return date >= visibleRange.start.getTime() && date <= visibleRange.end.getTime()
        })
      : timelineData.value
    
    dataToAnalyze.forEach((dataPoint, index) => {
      const actualIndex = timelineData.value.findIndex(d => d.date === dataPoint.date)
      if (actualIndex === -1) return
      
      // Group series by breakdown to calculate stacked totals per group
      const groupTotals = {}
      
      chartSeries.value.forEach(series => {
        const point = series.data[actualIndex]
        if (point && point.y) {
          const group = series.group || 'all'
          
          if (!groupTotals[group]) {
            groupTotals[group] = { positive: 0, negative: 0 }
          }
          
          if (point.y > 0) {
            groupTotals[group].positive += point.y
            hasPositive = true
          } else if (point.y < 0) {
            groupTotals[group].negative += point.y
            hasNegative = true
          }
        }
      })
      
      // Find max across all groups
      Object.values(groupTotals).forEach(totals => {
        if (totals.positive > maxPositive) {
          maxPositive = totals.positive
        }
        if (totals.negative < maxNegative) {
          maxNegative = totals.negative
        }
      })
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
   * Handle chart hover - track transfer directions separately (In/Out)
   */
  function handleChartHover(config) {
    if (!config || config.dataPointIndex === -1) return
    
    const dataPoint = timelineData.value[config.dataPointIndex]
    if (!dataPoint) return
    
    const breakdownData = {}
    
    if (breakdownMode.value === 'all') {
      const incomeByCategory = {}
      const expensesByCategory = {}
      const transfersOutByCategory = {}
      const transfersInByCategory = {}
      
      const grouping = currentGrouping.value
      const periodTransactions = transactions.value.filter(t => {
        const tDate = new Date(t.posted_at)
        let periodMatches = false
        
        if (grouping === 'year') {
          periodMatches = tDate.getFullYear() === new Date(dataPoint.date).getFullYear()
        } else if (grouping === 'quarter') {
          const tQuarter = Math.floor(tDate.getMonth() / 3)
          const pQuarter = Math.floor(new Date(dataPoint.date).getMonth() / 3)
          periodMatches = tQuarter === pQuarter && tDate.getFullYear() === new Date(dataPoint.date).getFullYear()
        } else {
          periodMatches = tDate.getMonth() === new Date(dataPoint.date).getMonth() && tDate.getFullYear() === new Date(dataPoint.date).getFullYear()
        }
        
        return periodMatches
      })
      
      let income = 0
      let expenses = 0
      let transfersOut = 0
      let transfersIn = 0
      
      periodTransactions.forEach(t => {
        const amount = Math.abs(parseFloat(t.amount))
        const rawAmount = parseFloat(t.amount)
        const subcategoryName = t.subcategory
        const categoryName = t.category || 'Uncategorized'
        const mainCat = (t.main_category || '').toUpperCase()
        
        if (mainCat === 'INCOME' && !isTypeVisible('income')) return
        if (mainCat === 'EXPENSES' && !isTypeVisible('expenses')) return
        if (mainCat === 'TRANSFERS' && !isTypeVisible('transfers')) return
        
        // Use subcategory if available, otherwise use category
        const displayName = subcategoryName || categoryName
        
        if (mainCat === 'INCOME') {
          income += amount
          incomeByCategory[displayName] = (incomeByCategory[displayName] || 0) + amount
        } else if (mainCat === 'EXPENSES') {
          expenses += amount
          expensesByCategory[displayName] = (expensesByCategory[displayName] || 0) + amount
        } else if (mainCat === 'TRANSFERS') {
          if (rawAmount < 0) {
            transfersOut += amount
            transfersOutByCategory[displayName] = (transfersOutByCategory[displayName] || 0) + amount
          } else if (rawAmount > 0) {
            transfersIn += amount
            transfersInByCategory[displayName] = (transfersInByCategory[displayName] || 0) + amount
          }
        }
      })
      
      breakdownData.all = {
        income,
        expenses,
        transfersOut,
        transfersIn,
        balance: income - expenses,
        incomeByCategory,
        expensesByCategory,
        transfersOutByCategory,
        transfersInByCategory
      }
    } else {
      breakdownKeys.value.forEach(key => {
        const keyTransactions = transactions.value.filter(t => {
          const tDate = new Date(t.posted_at)
          const tKey = breakdownMode.value === 'owner' 
            ? t.owner 
            : `${t.owner}_${t.bank_account_type}`
          
          const grouping = currentGrouping.value
          let periodMatches = false
          
          if (grouping === 'year') {
            periodMatches = tDate.getFullYear() === new Date(dataPoint.date).getFullYear()
          } else if (grouping === 'quarter') {
            const tQuarter = Math.floor(tDate.getMonth() / 3)
            const pQuarter = Math.floor(new Date(dataPoint.date).getMonth() / 3)
            periodMatches = tQuarter === pQuarter && tDate.getFullYear() === new Date(dataPoint.date).getFullYear()
          } else {
            periodMatches = tDate.getMonth() === new Date(dataPoint.date).getMonth() && tDate.getFullYear() === new Date(dataPoint.date).getFullYear()
          }
          
          return tKey === key && periodMatches
        })
        
        let income = 0
        let expenses = 0
        let transfersOut = 0
        let transfersIn = 0
        const incomeByCategory = {}
        const expensesByCategory = {}
        const transfersOutByCategory = {}
        const transfersInByCategory = {}
        
        keyTransactions.forEach(t => {
          const amount = Math.abs(parseFloat(t.amount))
          const rawAmount = parseFloat(t.amount)
          const subcategoryName = t.subcategory
          const categoryName = t.category || 'Uncategorized'
          const mainCat = (t.main_category || '').toUpperCase()
          
          if (mainCat === 'INCOME' && !isTypeVisible('income')) return
          if (mainCat === 'EXPENSES' && !isTypeVisible('expenses')) return
          if (mainCat === 'TRANSFERS' && !isTypeVisible('transfers')) return
          
          // Use subcategory if available, otherwise use category
          const displayName = subcategoryName || categoryName
          
          if (mainCat === 'INCOME') {
            income += amount
            incomeByCategory[displayName] = (incomeByCategory[displayName] || 0) + amount
          } else if (mainCat === 'EXPENSES') {
            expenses += amount
            expensesByCategory[displayName] = (expensesByCategory[displayName] || 0) + amount
          } else if (mainCat === 'TRANSFERS') {
            if (rawAmount < 0) {
              transfersOut += amount
              transfersOutByCategory[displayName] = (transfersOutByCategory[displayName] || 0) + amount
            } else if (rawAmount > 0) {
              transfersIn += amount
              transfersInByCategory[displayName] = (transfersInByCategory[displayName] || 0) + amount
            }
          }
        })
        
        breakdownData[key] = {
          income,
          expenses,
          transfersOut,
          transfersIn,
          balance: income - expenses,
          incomeByCategory,
          expensesByCategory,
          transfersOutByCategory,
          transfersInByCategory
        }
      })
    }
    
    hoveredData.value = {
      date: dataPoint.date,
      periodName: getPeriodName(dataPoint.date, currentGrouping.value),
      breakdownMode: breakdownMode.value,
      breakdownData: breakdownData
    }
    
    updateLineAnnotation()
  }
  
  function updateLineAnnotation() {
    const chart = chartRef?.value?.chart
    if (!chart || !hoveredData.value) return
    
    chart.clearAnnotations()
    
    chart.addYaxisAnnotation({
      y: 0,
      borderColor: '#374151',
      borderWidth: 0.5,
      opacity: 0.2
    })
    
    chart.addXaxisAnnotation({
      x: hoveredData.value.date,
      borderColor: isPinned.value ? '#3a3a3aff' : '#5b636eff',
      strokeDashArray: isPinned.value ? 0 : 5,
      borderWidth: isPinned.value ? 2 : 1,
      opacity: isPinned.value ? 1 : 0.6
    })
  }
  
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
  
  watch(() => isPinned.value, () => {
    if (hoveredData.value) {
      updateLineAnnotation()
    }
  })
  
  let visibilityDebounceTimer = null
  watch([
    () => visibilityState.visibleCategories.value,
    () => visibilityState.visibleSubcategories.value,
    () => visibilityState.expandedCategories.value,
    breakdownMode,
    selectedOwners,
    selectedAccounts
  ], async () => {
    if (visibilityDebounceTimer) {
      clearTimeout(visibilityDebounceTimer)
    }
    
    // Clear memoized data immediately
    memoizedCategoryData.value = null
    
    // Wait for DOM updates before recalculating Y-axis
    visibilityDebounceTimer = setTimeout(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
      const chart = chartRef?.value?.chart
      if (chart) {
        yAxisValues.value = calculateYAxisMax()
        console.log('📏 Y-axis recalculated after visibility/breakdown change')
      }
    }, 100)
  }, { deep: true })
  
  watch(currentZoomLevel, () => {
    memoizedCategoryData.value = null
    yAxisValues.value = calculateYAxisMax()
    console.log('📏 Y-axis recalculated on zoom')
  })
  
  watch(() => visibleDateRange.value, (newRange, oldRange) => {
    const chart = chartRef?.value?.chart
    if (!chart || !newRange) return
    
    if (currentZoomLevel.value === 1) {
      memoizedCategoryData.value = null
      yAxisValues.value = calculateYAxisMax()
      console.log('📏 Y-axis recalculated for year range:', yAxisValues.value)
    }
    
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
    }, false, false)
    
    console.log('📊 X-axis and Y-axis updated')
  }, { deep: true })
  
  const chartOptions = computed(() => {
    const range = visibleDateRange.value
    const yAxis = yAxisValues.value
    
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
    
    const columnWidth = breakdownMode.value === 'all' ? '90%' : '90%'
    
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
              isPinned.value = true
              handleChartHover(config)
            }
          },
          mouseMove: (event, chartContext, config) => {
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
          columnWidth: columnWidth,
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