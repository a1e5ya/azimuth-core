export function formatDate(dateValue) {
  const date = typeof dateValue === 'number' ? new Date(dateValue) : 
               typeof dateValue === 'string' ? new Date(dateValue) : dateValue
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

export function formatCurrency(amount, currency = 'EUR') {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(Math.abs(amount))
}

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

export function groupTransactionsByPeriod(transactions, grouping) {
  if (grouping === 'year') {
    return groupTransactionsByYear(transactions)
  } else if (grouping === 'quarter') {
    return groupTransactionsByQuarter(transactions)
  } else {
    return groupTransactionsByMonth(transactions)
  }
}

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

export function calculateVisibleDateRange(startDate, endDate, zoomLevel) {
  if (!startDate || !endDate) return null
  
  const futureEnd = new Date(endDate.getFullYear() + 2, 11, 31)
  
  if (zoomLevel <= 0) {
    return { start: startDate, end: futureEnd }
  }
  
  const currentYear = new Date().getFullYear()
  const dataEndYear = endDate.getFullYear()
  
  const targetYear = currentYear <= dataEndYear ? currentYear : dataEndYear
  
  const rangeStartYear = targetYear % 2 === 0 ? targetYear : targetYear - 1
  const start = new Date(rangeStartYear, 0, 1)
  const end = new Date(rangeStartYear + 1, 11, 31)
  
  return { start, end }
}

export function getGroupingByZoomLevel(zoomLevel) {
  if (zoomLevel === -1) return 'year'
  if (zoomLevel === 0) return 'quarter'
  return 'month'
}