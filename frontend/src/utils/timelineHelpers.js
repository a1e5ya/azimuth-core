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
 * Group transactions by day
 * @param {Array} transactions - Array of transaction objects
 * @returns {Array} Grouped data by day
 */
export function groupTransactionsByDay(transactions) {
  const grouped = new Map()
  
  transactions.forEach(t => {
    const date = new Date(t.posted_at)
    const key = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    const keyStr = key.toISOString()
    
    if (!grouped.has(keyStr)) {
      grouped.set(keyStr, {
        date: key.getTime(),
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
 * Group transactions by period type
 * @param {Array} transactions - Array of transaction objects
 * @param {string} grouping - 'day', 'month', or 'quarter'
 * @returns {Array} Grouped data
 */
export function groupTransactionsByPeriod(transactions, grouping) {
  if (grouping === 'quarter') {
    return groupTransactionsByQuarter(transactions)
  } else if (grouping === 'month') {
    return groupTransactionsByMonth(transactions)
  } else {
    return groupTransactionsByDay(transactions)
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
 * @param {number} zoomLevel - Current zoom level (0, 1, or 2)
 * @returns {Object} Object with start and end dates
 */
export function calculateVisibleDateRange(startDate, endDate, zoomLevel) {
  if (!startDate || !endDate) return null
  
  const totalDays = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24))
  
  if (zoomLevel === 0) {
    return { start: startDate, end: endDate }
  } else if (zoomLevel === 1) {
    const daysToShow = Math.min(365, totalDays)
    const end = endDate
    const start = new Date(end.getTime() - (daysToShow * 24 * 60 * 60 * 1000))
    return { start, end }
  } else {
    const daysToShow = Math.min(90, totalDays)
    const end = endDate
    const start = new Date(end.getTime() - (daysToShow * 24 * 60 * 60 * 1000))
    return { start, end }
  }
}

/**
 * Get grouping type based on zoom level
 * @param {number} zoomLevel - Current zoom level (0, 1, or 2)
 * @returns {string} 'quarter', 'month', or 'day'
 */
export function getGroupingByZoomLevel(zoomLevel) {
  if (zoomLevel === 0) return 'quarter'
  if (zoomLevel === 1) return 'month'
  return 'day'
}