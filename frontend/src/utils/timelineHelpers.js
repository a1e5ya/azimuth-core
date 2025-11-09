// frontend/src/utils/timelineHelpers.js

/**
 * Format a date value for display
 * @param {Date|number|string} dateValue - The date to format
 * @returns {string} Formatted date string
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
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code (default: EUR)
 * @returns {string} Formatted currency string
 */
export function formatCurrency(amount, currency = 'EUR') {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(Math.abs(amount))
}

/**
 * Group transactions by year
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by year
 */
export function groupTransactionsByYear(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const yearStart = new Date(date.getFullYear(), 0, 1)
    const keyStr = yearStart.toISOString()
    
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
  
  return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
}

/**
 * Group transactions by quarter
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by quarter
 */
export function groupTransactionsByQuarter(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const quarter = Math.floor(date.getMonth() / 3)
    const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
    const keyStr = quarterStart.toISOString()
    
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
  
  return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
}

/**
 * Group transactions by month
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by month
 */
export function groupTransactionsByMonth(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
    const keyStr = monthStart.toISOString()
    
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
  
  return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
}

/**
 * Group transactions by period type
 * @param {Array} transactions - Array of transaction objects
 * @param {string} grouping - 'year', 'quarter', or 'month'
 * @returns {Array} Grouped data
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

/**
 * Find category ID by name
 * @param {Array} categories - Category tree from store
 * @param {string} categoryName - Name to search for
 * @returns {string|null} Category ID or null
 */
export function findCategoryId(categories, categoryName) {
  if (!categories) return null
  
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
 * @param {Array} categories - Category tree from store
 * @param {string} categoryName - Name to search for
 * @returns {string} Hex color code
 */
export function getCategoryColor(categories, categoryName) {
  if (!categories) return '#94a3b8'
  
  for (const type of categories) {
    if (type.children) {
      for (const cat of type.children) {
        if (cat.name === categoryName) {
          return cat.color || '#94a3b8'
        }
        
        if (cat.children) {
          for (const subcat of cat.children) {
            if (subcat.name === categoryName) {
              return subcat.color || cat.color || '#94a3b8'
            }
          }
        }
      }
    }
  }
  
  return '#94a3b8'
}

/**
 * Find parent category for a subcategory
 * @param {Array} allCategories - Flat array of all categories
 * @param {string} subcategoryName - Subcategory name
 * @returns {Object|null} Parent category or null
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

/**
 * Calculate visible date range based on zoom level
 * @param {Date} startDate - Minimum date
 * @param {Date} endDate - Maximum date
 * @param {number} zoomLevel - Current zoom level (-1, 0, or 1)
 * @returns {Object} Object with start and end dates
 */
export function calculateVisibleDateRange(startDate, endDate, zoomLevel) {
  if (!startDate || !endDate) return null
  
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
  const rangeStartYear = targetYear % 2 === 0 ? targetYear : targetYear - 1
  const start = new Date(rangeStartYear, 0, 1)
  const end = new Date(rangeStartYear + 1, 11, 31)
  
  return { start, end }
}

/**
 * Get grouping type based on zoom level
 * @param {number} zoomLevel - Current zoom level (-1, 0, or 1)
 * @returns {string} 'year', 'quarter', or 'month'
 */
export function getGroupingByZoomLevel(zoomLevel) {
  if (zoomLevel === -1) return 'year'
  if (zoomLevel === 0) return 'quarter'
  return 'month'
}