/**
 * Timeline Chart Composable - Chart configuration and series generation with breakdown support
 * 
 * This composable manages the ApexCharts timeline visualization for financial transactions.
 * It handles chart series generation, visibility filtering, breakdown modes (All/Owner/Account),
 * hover interactions, and dynamic Y-axis scaling.
 * 
 * Features:
 * - Multi-breakdown support (All transactions, By Owner, By Account)
 * - Category visibility filtering with expand/collapse
 * - Stacked bar charts with separate positive/negative stacks per breakdown
 * - Dynamic Y-axis scaling based on visible data
 * - Hover info panel with period breakdowns
 * - Pin/unpin functionality for detailed inspection
 * - Automatic category hierarchy resolution
 * - Transfer direction tracking (In/Out)
 * - Memoization for performance optimization
 * 
 * Breakdown Modes:
 * - 'all': Single view of all transactions combined
 * - 'owner': Separate stacks for each owner (e.g., Alexa, John)
 * - 'account': Separate stacks for each owner_accountType combination
 * 
 * Chart Structure:
 * - Each breakdown gets its own stack group
 * - Within each stack: Expenses (bottom) → Transfers Out → Income → Transfers In (top)
 * - Negative values (expenses, transfers out) shown below zero line
 * - Positive values (income, transfers in) shown above zero line
 * 
 * @module composables/useTimelineChart
 */

import { ref, computed, watch } from 'vue'
import { 
  calculateVisibleDateRange, 
  getCategoryColor, 
  findCategoryId,
  findParentCategory 
} from '@/utils/timelineHelpers'

// ========================================
// HELPER FUNCTIONS
// ========================================

/**
 * Get human-readable period name from date and grouping level
 * 
 * Formats dates according to the current zoom level:
 * - Year grouping: "2024"
 * - Quarter grouping: "Jan - Mar 2024"
 * - Month grouping: "January 2024"
 * 
 * @param {number} date - Timestamp in milliseconds
 * @param {string} grouping - Grouping level ('year', 'quarter', 'month')
 * @returns {string} Formatted period name
 * 
 * @example
 * getPeriodName(1704067200000, 'year') // "2024"
 * getPeriodName(1704067200000, 'quarter') // "Jan - Mar 2024"
 * getPeriodName(1704067200000, 'month') // "January 2024"
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

// ========================================
// MAIN COMPOSABLE
// ========================================

/**
 * Timeline Chart Composable
 * 
 * Creates and manages the timeline chart configuration with breakdown support.
 * Handles data aggregation, visibility filtering, and chart interactions.
 * 
 * @param {Ref<Array>} timelineData - Array of date points with timestamps
 * @param {Ref<Array>} transactions - All transactions for the user
 * @param {Ref<Object>} dateRange - Date range with start/end dates
 * @param {Ref<number>} currentZoomLevel - Current zoom level (-1: year, 0: quarter, 1: month)
 * @param {Object} categoryStore - Pinia category store
 * @param {Object} visibilityState - Visibility state (types, categories, subcategories, expanded)
 * @param {Ref<Object>} customVisibleRange - Optional custom visible date range
 * @param {Ref<Object>} chartRef - Reference to ApexCharts instance
 * @param {Ref<string>} breakdownMode - Breakdown mode ('all', 'owner', 'account')
 * @param {Ref<Array<string>>} selectedOwners - Selected owners for breakdown filtering
 * @param {Ref<Array<string>>} selectedAccounts - Selected accounts for breakdown filtering
 * 
 * @returns {Object} Chart composable object
 * @returns {Ref<Object>} hoveredData - Currently hovered period data with breakdowns
 * @returns {Ref<boolean>} isPinned - Whether hover data is pinned
 * @returns {Ref<Array>} chartSeries - ApexCharts series data
 * @returns {Ref<Object>} chartOptions - ApexCharts configuration
 * @returns {Ref<Array>} expenseCategories - Expense category tree
 * @returns {Ref<Array>} incomeCategories - Income category tree
 * @returns {Ref<Array>} transferCategories - Transfer category tree
 * @returns {Ref<Array>} targetCategories - Target category tree
 * @returns {Ref<Object>} visibleDateRange - Currently visible date range
 * @returns {Function} handleChartHover - Handle chart hover events
 * @returns {Function} unpinHoverData - Unpin hover data
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
  // ========================================
  // STATE
  // ========================================
  
  /** Currently hovered data with period breakdown information */
  const hoveredData = ref(null)
  
  /** Whether hover data is pinned for detailed inspection */
  const isPinned = ref(false)
  
  /** Y-axis scale values (max positive/negative, has positive/negative flags) */
  const yAxisValues = ref({ maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false })
  
  /** Memoized category aggregation data to avoid recalculation */
  const memoizedCategoryData = ref(null)
  
  /** Hash of last visibility state to detect changes */
  const lastVisibilityHash = ref('')
  
  // Extract visibility functions from state
  const {
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded
  } = visibilityState
  
  // ========================================
  // CATEGORY TREES
  // ========================================
  
  /**
   * Expense categories from category store
   * Filtered to only show EXPENSES type children
   */
  const expenseCategories = computed(() => {
    const expenseType = categoryStore.categories?.find(t => t.code === 'expenses')
    return expenseType?.children || []
  })
  
  /**
   * Income categories from category store
   * Filtered to only show INCOME type children
   */
  const incomeCategories = computed(() => {
    const incomeType = categoryStore.categories?.find(t => t.code === 'income')
    return incomeType?.children || []
  })
  
  /**
   * Transfer categories from category store
   * Filtered to only show TRANSFERS type children
   */
  const transferCategories = computed(() => {
    const transferType = categoryStore.categories?.find(t => t.code === 'transfers')
    return transferType?.children || []
  })
  
  /**
   * Target categories from category store
   * Filtered to only show TARGETS type children
   */
  const targetCategories = computed(() => {
    const targetType = categoryStore.categories?.find(t => t.code === 'targets')
    return targetType?.children || []
  })
  
  // ========================================
  // DATE RANGE MANAGEMENT
  // ========================================
  
  /**
   * Currently visible date range
   * Uses custom range if set, otherwise calculates from zoom level
   */
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
   * Current grouping level based on timeline data spacing
   * Determines how data points are aggregated (year/quarter/month)
   */
  const currentGrouping = computed(() => {
    if (!timelineData.value[0] || !timelineData.value[1]) return 'quarter'
    const diff = timelineData.value[1]?.date - timelineData.value[0]?.date
    if (diff > 86400000 * 300) return 'year'
    if (diff > 86400000 * 60) return 'quarter'
    return 'month'
  })
  
  // ========================================
  // BREAKDOWN MANAGEMENT
  // ========================================
  
  /**
   * Breakdown keys based on current mode
   * - 'all': ['all']
   * - 'owner': ['Alexa', 'John', ...]
   * - 'account': ['Alexa_Main', 'Alexa_Kopio', ...]
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
  
  // ========================================
  // VISIBILITY HASH FOR MEMOIZATION
  // ========================================
  
  /**
   * Generate hash of current visibility state
   * Used to detect changes and invalidate memoized data
   * 
   * @returns {string} JSON string representing current visibility state
   */
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
  
  // ========================================
  // CATEGORY DATA AGGREGATION
  // ========================================
  
  /**
   * Build aggregated category data with breakdown support
   * 
   * This is the core data aggregation function that:
   * 1. Groups transactions by breakdown key (all/owner/account)
   * 2. Filters by visibility settings (type/category/subcategory)
   * 3. Aggregates amounts by category and date period
   * 4. Tracks positive and negative transfers separately
   * 
   * Process:
   * 1. Check memoized data (return if visibility unchanged)
   * 2. Initialize breakdown buckets for each key
   * 3. Process each transaction:
   *    - Determine breakdown key (owner/account)
   *    - Skip if not in selected breakdowns
   *    - Extract category names with hierarchy
   *    - Check visibility (type → category → subcategory)
   *    - Calculate period key (year/quarter/month)
   *    - Add amount to appropriate category map
   * 4. Return structured data by breakdown and category type
   * 
   * @returns {Object} Aggregated data structure
   * @returns {Object} expensesByBreakdown - { breakdownKey: { categoryName: Map<date, amount> } }
   * @returns {Object} incomeByBreakdown - { breakdownKey: { categoryName: Map<date, amount> } }
   * @returns {Object} transfersNegativeByBreakdown - { breakdownKey: { categoryName: Map<date, amount> } }
   * @returns {Object} transfersPositiveByBreakdown - { breakdownKey: { categoryName: Map<date, amount> } }
   * 
   * @example
   * // Returns structure like:
   * {
   *   expensesByBreakdown: {
   *     'Alexa': {
   *       'Groceries': Map { 1704067200000 => 150.50, ... },
   *       'Transport': Map { 1704067200000 => 45.20, ... }
   *     }
   *   },
   *   incomeByBreakdown: { ... },
   *   transfersNegativeByBreakdown: { ... },
   *   transfersPositiveByBreakdown: { ... }
   * }
   */
  function buildAllCategoriesSinglePass() {
    // Check memoized cache
    const currentVisibilityHash = getVisibilityHash()
    
    if (memoizedCategoryData.value && lastVisibilityHash.value === currentVisibilityHash) {
      return memoizedCategoryData.value
    }

    // Validate category store loaded
    if (!categoryStore.categories || categoryStore.categories.length === 0) {
      console.error('⚠️ Categories not loaded yet')
      return { 
        expensesByBreakdown: {}, 
        incomeByBreakdown: {}, 
        transfersNegativeByBreakdown: {},
        transfersPositiveByBreakdown: {}
      }
    }
    
    // Initialize data structure: { breakdownKey: { categoryName: Map<date, amount> } }
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
    
    // Counters for debugging
    let processedCount = 0
    let skippedByMode = 0
    let skippedByVisibility = 0
    
    // Process each transaction
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
      
      // Extract transaction details
      const mainCat = (t.main_category || '').toUpperCase()
      const subcategoryName = t.subcategory
      const categoryName = t.category || 'Uncategorized'
      const amount = Math.abs(parseFloat(t.amount))
      const rawAmount = parseFloat(t.amount)
      
      // Find parent category if subcategory exists
      const parentCategory = subcategoryName ? findParentCategory(allCategories, subcategoryName) : null
      let displayName = categoryName
      let shouldInclude = true
      
      // Check visibility filters
      // First check if the TYPE is visible
      if (mainCat === 'INCOME' && !isTypeVisible('income')) {
        shouldInclude = false
      } else if (mainCat === 'EXPENSES' && !isTypeVisible('expenses')) {
        shouldInclude = false
      } else if (mainCat === 'TRANSFERS' && !isTypeVisible('transfers')) {
        shouldInclude = false
      } else if (parentCategory) {
        // Has a parent category - check parent visibility
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
          // Parent not expanded - group under parent name
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
      
      // Skip if not visible
      if (!shouldInclude) {
        skippedByVisibility++
        return
      }
      
      processedCount++
      
      // Calculate period key based on grouping level
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
      
      // Add to appropriate breakdown bucket based on transaction type
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
        // Track positive and negative transfers separately for directional visualization
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
    
    // Cache results
    const result = { expensesByBreakdown, incomeByBreakdown, transfersNegativeByBreakdown, transfersPositiveByBreakdown }
    memoizedCategoryData.value = result
    lastVisibilityHash.value = currentVisibilityHash
    
    return result
  }
  
  // ========================================
  // CHART SERIES GENERATION
  // ========================================
  
  /**
   * Generate ApexCharts series data with breakdown support
   * 
   * Creates stacked bar chart series where each breakdown gets its own stack group.
   * Within each stack, series are ordered: Expenses → Transfers Out → Income → Transfers In
   * 
   * Series Structure:
   * - Each series represents one category (e.g., "Groceries", "Salary")
   * - Each series belongs to one breakdown (e.g., "Alexa", "John")
   * - Each series belongs to one stack group (e.g., "breakdown-0", "breakdown-1")
   * - Data points are { x: timestamp, y: amount } pairs
   * 
   * Stacking Rules:
   * - 'all' mode: All series in one stack ("all")
   * - 'owner' mode: Each owner gets separate stack ("breakdown-0", "breakdown-1", ...)
   * - 'account' mode: Each account gets separate stack
   * 
   * @returns {Array<Object>} ApexCharts series array
   * 
   * @example
   * // Returns series like:
   * [
   *   {
   *     name: "Groceries - Alexa",
   *     type: "bar",
   *     data: [{ x: 1704067200000, y: -150.50 }, ...],
   *     color: "#F17D99",
   *     breakdownKey: "Alexa",
   *     group: "breakdown-0"
   *   },
   *   ...
   * ]
   */
  const chartSeries = computed(() => {
    if (!timelineData.value.length) return []
    
    const { expensesByBreakdown, incomeByBreakdown, transfersNegativeByBreakdown, transfersPositiveByBreakdown } = buildAllCategoriesSinglePass()
    const series = []
    
    // For each breakdown key, create separate series with ONE stack group per breakdown
    breakdownKeys.value.forEach((breakdownKey, breakdownIndex) => {
      const suffix = breakdownMode.value === 'all' ? '' : ` - ${breakdownKey}`
      const stackGroup = breakdownMode.value === 'all' ? 'all' : `breakdown-${breakdownIndex}`
      
      // EXPENSES - all go into same stack group (negative values)
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
      
      // NEGATIVE TRANSFERS - same stack group (negative values)
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
      
      // INCOME - same stack group (positive values)
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
      
      // POSITIVE TRANSFERS - same stack group (positive values)
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
    
    return series
  })
  
  // ========================================
  // Y-AXIS SCALING
  // ========================================
  
  /**
   * Calculate Y-axis maximum values based on visible data
   * 
   * Analyzes stacked totals per breakdown group to find maximum positive/negative values.
   * Ensures symmetrical scaling when both positive and negative values exist.
   * 
   * Process:
   * 1. Filter data points to visible range (if zoomed to year view)
   * 2. For each data point:
   *    - Group series by stack group (breakdown)
   *    - Sum positive and negative values within each group
   * 3. Find maximum positive and negative across all groups
   * 4. Add 15% padding for visual spacing
   * 
   * @returns {Object} Y-axis scale configuration
   * @returns {number} maxPositive - Maximum positive value with padding
   * @returns {number} maxNegative - Maximum negative value (absolute) with padding
   * @returns {boolean} hasPositive - Whether any positive values exist
   * @returns {boolean} hasNegative - Whether any negative values exist
   * 
   * @example
   * // Returns something like:
   * {
   *   maxPositive: 3450.75,
   *   maxNegative: 2890.50,
   *   hasPositive: true,
   *   hasNegative: true
   * }
   */
  function calculateYAxisMax() {
    if (!chartSeries.value.length || !timelineData.value.length) {
      return { maxPositive: 1000, maxNegative: 1000, hasPositive: false, hasNegative: false }
    }
    
    let maxPositive = 0
    let maxNegative = 0
    let hasPositive = false
    let hasNegative = false
    
    // Filter to visible range if zoomed to month level
    const visibleRange = visibleDateRange.value
    const dataToAnalyze = (currentZoomLevel.value === 1 && visibleRange)
      ? timelineData.value.filter(d => {
          const date = d.date
          return date >= visibleRange.start.getTime() && date <= visibleRange.end.getTime()
        })
      : timelineData.value
    
    // Analyze each data point
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
    
    // Add 15% padding
    maxPositive = maxPositive * 1.15
    maxNegative = maxNegative * 1.15
    
    return {
      maxPositive,
      maxNegative: Math.abs(maxNegative),
      hasPositive,
      hasNegative
    }
  }
  
  // ========================================
  // CHART INTERACTIONS
  // ========================================
  
  /**
   * Handle chart hover/click interactions
   * 
   * When user hovers or clicks a bar, this function:
   * 1. Finds the corresponding data point in timelineData
   * 2. Filters transactions for that period
   * 3. Aggregates by breakdown (all/owner/account)
   * 4. Calculates totals and breakdowns by category
   * 5. Updates hoveredData with formatted information
   * 6. Updates chart annotation line
   * 
   * Breakdown Data Structure:
   * {
   *   date: timestamp,
   *   periodName: "January 2024",
   *   breakdownMode: "owner",
   *   breakdownData: {
   *     "Alexa": {
   *       income: 3500,
   *       expenses: 2100,
   *       transfersOut: 500,
   *       transfersIn: 200,
   *       balance: 1100,
   *       incomeByCategory: { "Salary": 3500 },
   *       expensesByCategory: { "Groceries": 450, "Transport": 120, ... },
   *       transfersOutByCategory: { ... },
   *       transfersInByCategory: { ... }
   *     },
   *     "John": { ... }
   *   }
   * }
   * 
   * @param {Object} config - ApexCharts event config
   * @param {number} config.dataPointIndex - Index of clicked data point
   */
  function handleChartHover(config) {
    if (!config || config.dataPointIndex === -1) return
    
    const dataPoint = timelineData.value[config.dataPointIndex]
    if (!dataPoint) return
    
    const breakdownData = {}
    
    if (breakdownMode.value === 'all') {
      // Single breakdown - all transactions together
      const incomeByCategory = {}
      const expensesByCategory = {}
      const transfersOutByCategory = {}
      const transfersInByCategory = {}
      
      // Filter transactions for this period
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
      
      // Aggregate by category
      periodTransactions.forEach(t => {
        const amount = Math.abs(parseFloat(t.amount))
        const rawAmount = parseFloat(t.amount)
        const subcategoryName = t.subcategory
        const categoryName = t.category || 'Uncategorized'
        const mainCat = (t.main_category || '').toUpperCase()
        
        // Skip if type not visible
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
      // Multiple breakdowns - separate data for each owner/account
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
    
    // Update hover data
    hoveredData.value = {
      date: dataPoint.date,
      periodName: getPeriodName(dataPoint.date, currentGrouping.value),
      breakdownMode: breakdownMode.value,
      breakdownData: breakdownData
    }
    
    updateLineAnnotation()
  }
  
  /**
   * Update vertical line annotation on chart
   * 
   * Draws a vertical line at hovered date and horizontal line at zero.
   * Line style changes when pinned (solid vs dashed).
   */
  function updateLineAnnotation() {
    const chart = chartRef?.value?.chart
    if (!chart || !hoveredData.value) return
    
    chart.clearAnnotations()
    
    // Add zero line
    chart.addYaxisAnnotation({
      y: 0,
      borderColor: '#374151',
      borderWidth: 0.5,
      opacity: 0.2
    })
    
    // Add vertical line at hovered date
    chart.addXaxisAnnotation({
      x: hoveredData.value.date,
      borderColor: isPinned.value ? '#3a3a3aff' : '#5b636eff',
      strokeDashArray: isPinned.value ? 0 : 5,
      borderWidth: isPinned.value ? 2 : 1,
      opacity: isPinned.value ? 1 : 0.6
    })
  }
  
  /**
   * Unpin hover data and clear annotations
   * 
   * Resets chart to default state with only zero line visible.
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
  
  // ========================================
  // WATCHERS
  // ========================================
  
  /**
   * Watch pinned state and update annotation style
   */
  watch(() => isPinned.value, () => {
    if (hoveredData.value) {
      updateLineAnnotation()
    }
  })
  
  /**
   * Watch visibility changes and recalculate Y-axis
   * Debounced to avoid excessive recalculations
   */
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
      }
    }, 100)
  }, { deep: true })
  
  /**
   * Watch zoom level changes and recalculate Y-axis
   */
  watch(currentZoomLevel, () => {
    memoizedCategoryData.value = null
    yAxisValues.value = calculateYAxisMax()
  })
  
  /**
   * Watch visible date range changes and update chart
   * Updates both X-axis and Y-axis for zoomed views
   */
  watch(() => visibleDateRange.value, (newRange, oldRange) => {
    const chart = chartRef?.value?.chart
    if (!chart || !newRange) return
    
    // Recalculate Y-axis for year-level zoom
    if (currentZoomLevel.value === 1) {
      memoizedCategoryData.value = null
      yAxisValues.value = calculateYAxisMax()
    }
    
    // Update chart axes
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
  }, { deep: true })
  
  // ========================================
  // CHART OPTIONS
  // ========================================
  
  /**
   * ApexCharts configuration object
   * 
   * Configures all chart behavior including:
   * - Stacking behavior
   * - Animations (disabled for performance)
   * - Event handlers (hover, click)
   * - Axes configuration
   * - Grid styling
   * - Tooltip (disabled, using custom hover info)
   * 
   * @returns {Object} ApexCharts options configuration
   */
  const chartOptions = computed(() => {
    const range = visibleDateRange.value
    const yAxis = yAxisValues.value
    
    // Calculate Y-axis min/max with symmetry for dual-sided charts
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
    
    // Adjust bar width based on breakdown mode
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
  
  // ========================================
  // RETURN API
  // ========================================
  
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