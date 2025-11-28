/**
 * Timeline Helpers - Transaction Timeline Utility Functions
 * 
 * Provides utility functions for the Timeline component visualization:
 * - Date and currency formatting
 * - Transaction grouping (year, quarter, month)
 * - Category lookups and color resolution
 * - Date range calculations based on zoom level
 * - Grouping type determination
 * 
 * Used by: TimelineView component
 * Data Source: Transaction store (filtered transactions)
 * 
 * Grouping Strategy:
 * - Year: Annual totals for long-term overview
 * - Quarter: Quarterly totals for mid-range analysis
 * - Month: Monthly totals for detailed analysis
 * 
 * Each group tracks:
 * - Total income, expenses, transfers
 * - Per-category breakdowns
 * - Date timestamp for sorting
 */

// ============================================================================
// FORMATTING UTILITIES
// ============================================================================

/**
 * Format a date value for display
 * 
 * Converts various date formats to human-readable format.
 * Handles Date objects, timestamps, and ISO strings.
 * 
 * @param {Date|number|string} dateValue - The date to format
 * @returns {string} Formatted date string (e.g., "Jan 15, 2024")
 * 
 * @example
 * formatDate(new Date(2024, 0, 15)) // Returns: "Jan 15, 2024"
 * formatDate(1705276800000) // Returns: "Jan 15, 2024"
 * formatDate("2024-01-15") // Returns: "Jan 15, 2024"
 */
export function formatDate(dateValue) {
  const date = typeof dateValue === 'number' ? new Date(dateValue) : 
               typeof dateValue === 'string' ? new Date(dateValue) : dateValue
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Format a currency amount
 * 
 * Formats amounts as currency with proper locale and symbol.
 * Always uses absolute value (negatives handled by context).
 * No decimal places for cleaner timeline display.
 * 
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code (default: EUR)
 * @returns {string} Formatted currency string (e.g., "€1,234")
 * 
 * @example
 * formatCurrency(1234.56) // Returns: "€1,235"
 * formatCurrency(-1234.56) // Returns: "€1,235" (absolute value)
 * formatCurrency(1234.56, 'USD') // Returns: "$1,235"
 */
export function formatCurrency(amount, currency = 'EUR') {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(Math.abs(amount))
}

// ============================================================================
// TRANSACTION GROUPING FUNCTIONS
// ============================================================================

/**
 * Group transactions by year
 * 
 * Aggregates transactions into annual periods.
 * Each period contains:
 * - Total income, expenses, transfers
 * - Per-category breakdowns for each type
 * - Date timestamp (Jan 1 of year)
 * 
 * Process:
 * 1. Create Map with year start as key (Jan 1)
 * 2. For each transaction, determine year
 * 3. Add to period totals
 * 4. Track category breakdowns
 * 5. Return sorted array (oldest to newest)
 * 
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by year
 * 
 * @example
 * const grouped = groupTransactionsByYear(transactions)
 * // Returns: [
 * //   {
 * //     date: 1672531200000, // Jan 1, 2023 timestamp
 * //     income: 50000,
 * //     expenses: 35000,
 * //     transfers: 5000,
 * //     incomeByCategory: { "Salary": 50000 },
 * //     expensesByCategory: { "Food": 12000, "Transport": 8000 },
 * //     transfersByCategory: { "Savings": 5000 }
 * //   }
 * // ]
 */
export function groupTransactionsByYear(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const yearStart = new Date(date.getFullYear(), 0, 1)
    const keyStr = yearStart.toISOString()
    
    // Initialize period if not exists
    if (!grouped.has(keyStr)) {
      grouped.set(keyStr, {
        date: yearStart.getTime(),
        income: 0,
        expenses: 0,
        transfers: 0,
        incomeByCategory: {},
        expensesByCategory: {},
        transfersByCategory: {}
      })
    }
    
    const period = grouped.get(keyStr)
    const amount = Math.abs(parseFloat(t.amount))
    const category = t.subcategory || t.category || 'Uncategorized'
    const mainCat = (t.main_category || '').toUpperCase()
    
    // Add to appropriate totals
    if (mainCat === 'INCOME') {
      period.income += amount
      period.incomeByCategory[category] = (period.incomeByCategory[category] || 0) + amount
    } else if (mainCat === 'EXPENSES') {
      period.expenses += amount
      period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
    } else if (mainCat === 'TRANSFERS') {
      period.transfers += amount
      period.transfersByCategory[category] = (period.transfersByCategory[category] || 0) + amount
    }
  })
  
  // Convert to sorted array
  return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
}

/**
 * Group transactions by quarter
 * 
 * Aggregates transactions into quarterly periods (Q1, Q2, Q3, Q4).
 * Same structure as groupTransactionsByYear but quarterly.
 * 
 * Quarter calculation:
 * - Q1: Jan-Mar (months 0-2)
 * - Q2: Apr-Jun (months 3-5)
 * - Q3: Jul-Sep (months 6-8)
 * - Q4: Oct-Dec (months 9-11)
 * 
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by quarter
 * 
 * @example
 * const grouped = groupTransactionsByQuarter(transactions)
 * // Returns quarterly periods with same structure as yearly
 */
export function groupTransactionsByQuarter(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const quarter = Math.floor(date.getMonth() / 3) // 0-3
    const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
    const keyStr = quarterStart.toISOString()
    
    // Initialize period if not exists
    if (!grouped.has(keyStr)) {
      grouped.set(keyStr, {
        date: quarterStart.getTime(),
        income: 0,
        expenses: 0,
        transfers: 0,
        incomeByCategory: {},
        expensesByCategory: {},
        transfersByCategory: {}
      })
    }
    
    const period = grouped.get(keyStr)
    const amount = Math.abs(parseFloat(t.amount))
    const category = t.subcategory || t.category || 'Uncategorized'
    const mainCat = (t.main_category || '').toUpperCase()
    
    // Add to appropriate totals
    if (mainCat === 'INCOME') {
      period.income += amount
      period.incomeByCategory[category] = (period.incomeByCategory[category] || 0) + amount
    } else if (mainCat === 'EXPENSES') {
      period.expenses += amount
      period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
    } else if (mainCat === 'TRANSFERS') {
      period.transfers += amount
      period.transfersByCategory[category] = (period.transfersByCategory[category] || 0) + amount
    }
  })
  
  // Convert to sorted array
  return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
}

/**
 * Group transactions by month
 * 
 * Aggregates transactions into monthly periods.
 * Most granular grouping level for detailed analysis.
 * Same structure as yearly/quarterly grouping.
 * 
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by month
 * 
 * @example
 * const grouped = groupTransactionsByMonth(transactions)
 * // Returns monthly periods with same structure as yearly/quarterly
 */
export function groupTransactionsByMonth(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
    const keyStr = monthStart.toISOString()
    
    // Initialize period if not exists
    if (!grouped.has(keyStr)) {
      grouped.set(keyStr, {
        date: monthStart.getTime(),
        income: 0,
        expenses: 0,
        transfers: 0,
        incomeByCategory: {},
        expensesByCategory: {},
        transfersByCategory: {}
      })
    }
    
    const period = grouped.get(keyStr)
    const amount = Math.abs(parseFloat(t.amount))
    const category = t.subcategory || t.category || 'Uncategorized'
    const mainCat = (t.main_category || '').toUpperCase()
    
    // Add to appropriate totals
    if (mainCat === 'INCOME') {
      period.income += amount
      period.incomeByCategory[category] = (period.incomeByCategory[category] || 0) + amount
    } else if (mainCat === 'EXPENSES') {
      period.expenses += amount
      period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
    } else if (mainCat === 'TRANSFERS') {
      period.transfers += amount
      period.transfersByCategory[category] = (period.transfersByCategory[category] || 0) + amount
    }
  })
  
  // Convert to sorted array
  return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
}

/**
 * Group transactions by period type
 * 
 * Convenience wrapper that calls appropriate grouping function
 * based on specified period type.
 * 
 * @param {Array} transactions - Array of transaction objects
 * @param {string} grouping - 'year', 'quarter', or 'month'
 * @returns {Array} Grouped data
 * 
 * @example
 * // Group by month
 * const monthly = groupTransactionsByPeriod(transactions, 'month')
 * 
 * @example
 * // Group by year
 * const yearly = groupTransactionsByPeriod(transactions, 'year')
 */
export function groupTransactionsByPeriod(transactions, grouping) {
  if (grouping === 'year') {
    return groupTransactionsByYear(transactions)
  } else if (grouping === 'quarter') {
    return groupTransactionsByQuarter(transactions)
  } else {
    return groupTransactionsByMonth(transactions)
  }
}

// ============================================================================
// CATEGORY LOOKUP UTILITIES
// ============================================================================

/**
 * Find category ID by name
 * 
 * Searches through category tree (3 levels) to find category by name.
 * Searches recursively through:
 * - Level 1: Type (Income, Expenses, etc.)
 * - Level 2: Category (Food, Transport, etc.)
 * - Level 3: Subcategory (Groceries, Fuel, etc.)
 * 
 * @param {Array} categories - Category tree from store
 * @param {string} categoryName - Name to search for
 * @returns {string|null} Category ID or null if not found
 * 
 * @example
 * const categoryId = findCategoryId(categories, 'Groceries')
 * // Returns: "uuid-of-groceries-category"
 */
export function findCategoryId(categories, categoryName) {
  if (!categories) return null
  
  // Search through category tree
  for (const type of categories) {
    if (type.children) {
      for (const cat of type.children) {
        if (cat.name === categoryName) return cat.id
        
        if (cat.children) {
          for (const subcat of cat.children) {
            if (subcat.name === categoryName) return subcat.id
          }
        }
      }
    }
  }
  
  return null
}

/**
 * Get category color by name
 * 
 * Searches through category tree to find color for category name.
 * Falls back to parent color or default gray if not found.
 * 
 * Color Priority:
 * 1. Subcategory color (if exists)
 * 2. Parent category color (if subcategory has no color)
 * 3. Default gray (#94a3b8)
 * 
 * @param {Array} categories - Category tree from store
 * @param {string} categoryName - Name to search for
 * @returns {string} Hex color code
 * 
 * @example
 * const color = getCategoryColor(categories, 'Groceries')
 * // Returns: "#9B7EDE" (Food category color)
 */
export function getCategoryColor(categories, categoryName) {
  if (!categories) return '#94a3b8'
  
  // Search through category tree
  for (const type of categories) {
    if (type.children) {
      for (const cat of type.children) {
        if (cat.name === categoryName) {
          return cat.color || '#94a3b8'
        }
        
        if (cat.children) {
          for (const subcat of cat.children) {
            if (subcat.name === categoryName) {
              // Prefer subcat color, fall back to parent color
              return subcat.color || cat.color || '#94a3b8'
            }
          }
        }
      }
    }
  }
  
  return '#94a3b8' // Default gray
}

/**
 * Find parent category for a subcategory
 * 
 * Given a subcategory name, finds its parent category object.
 * Useful for showing category hierarchy in UI.
 * 
 * @param {Array} allCategories - Flat array of all categories
 * @param {string} subcategoryName - Subcategory name
 * @returns {Object|null} Parent category or null if not found
 * 
 * @example
 * const parent = findParentCategory(categories, 'Groceries')
 * // Returns: { id: "...", name: "Food", color: "#9B7EDE", ... }
 */
export function findParentCategory(allCategories, subcategoryName) {
  for (const cat of allCategories) {
    if (cat.children) {
      for (const subcat of cat.children) {
        if (subcat.name === subcategoryName) {
          return cat
        }
      }
    }
  }
  
  return null
}

// ============================================================================
// ZOOM AND DATE RANGE UTILITIES
// ============================================================================

/**
 * Calculate visible date range based on zoom level
 * 
 * Determines which date range to display on timeline based on zoom:
 * 
 * Zoom Levels:
 * - Level -1 (Zoomed Out): Full data range + 2 years future
 * - Level 0 (Medium): Full data range + 2 years future
 * - Level 1 (Zoomed In): 2-year window containing current/most recent year
 * 
 * Level 1 Logic:
 * - Prefers showing current year if it has data
 * - Falls back to most recent data year if current year has no data
 * - Always shows 2-year ranges (e.g., 2023-2024, 2024-2025)
 * - Range starts on even years (2022, 2024, 2026)
 * 
 * @param {Date} startDate - Minimum date in dataset
 * @param {Date} endDate - Maximum date in dataset
 * @param {number} zoomLevel - Current zoom level (-1, 0, or 1)
 * @returns {Object|null} Object with start and end dates, or null if invalid input
 * 
 * @example
 * // Zoom level -1 or 0: Full range
 * calculateVisibleDateRange(new Date(2020, 0, 1), new Date(2024, 11, 31), 0)
 * // Returns: { start: Date(2020-01-01), end: Date(2026-12-31) }
 * 
 * @example
 * // Zoom level 1: 2-year window
 * calculateVisibleDateRange(new Date(2020, 0, 1), new Date(2024, 11, 31), 1)
 * // Returns: { start: Date(2024-01-01), end: Date(2025-12-31) }
 */
export function calculateVisibleDateRange(startDate, endDate, zoomLevel) {
  if (!startDate || !endDate) return null
  
  // Always add 2 years to end for future planning
  const futureEnd = new Date(endDate.getFullYear() + 2, 11, 31)
  
  // Level -1 & 0: Always show full range + 2 years future
  if (zoomLevel <= 0) {
    return { start: startDate, end: futureEnd }
  }
  
  // Level 1: Default to range containing current year
  const currentYear = new Date().getFullYear()
  const dataEndYear = endDate.getFullYear()
  
  // Use current year if it's in data range, otherwise use most recent data year
  const targetYear = currentYear <= dataEndYear ? currentYear : dataEndYear
  
  // Find which 2-year range contains the target year
  // Ranges start on even years: 2022-2023, 2024-2025, etc.
  const rangeStartYear = targetYear % 2 === 0 ? targetYear : targetYear - 1
  const start = new Date(rangeStartYear, 0, 1)
  const end = new Date(rangeStartYear + 1, 11, 31)
  
  return { start, end }
}

/**
 * Get grouping type based on zoom level
 * 
 * Determines appropriate time grouping for current zoom level:
 * - Zoomed out: Yearly grouping (annual overview)
 * - Medium: Quarterly grouping (mid-range analysis)
 * - Zoomed in: Monthly grouping (detailed analysis)
 * 
 * @param {number} zoomLevel - Current zoom level (-1, 0, or 1)
 * @returns {string} 'year', 'quarter', or 'month'
 * 
 * @example
 * getGroupingByZoomLevel(-1) // Returns: 'year'
 * getGroupingByZoomLevel(0) // Returns: 'quarter'
 * getGroupingByZoomLevel(1) // Returns: 'month'
 */
export function getGroupingByZoomLevel(zoomLevel) {
  if (zoomLevel === -1) return 'year'
  if (zoomLevel === 0) return 'quarter'
  return 'month'
}