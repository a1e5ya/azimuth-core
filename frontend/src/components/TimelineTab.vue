<template>
  <div class="timeline-container">
    <!-- Main Content: Legend + Chart -->
    <div class="timeline-main-content">
      <!-- Compact Legend - Left Side -->
      <CategoryLegend
        :expense-categories="expenseCategories"
        :income-categories="incomeCategories"
        :transfer-categories="transferCategories"
        :visible-types="visibleTypes"
        :visible-categories="visibleCategories"
        :visible-subcategories="visibleSubcategories"
        :expanded-categories="expandedCategories"
        @toggle-type="toggleType"
        @toggle-category="toggleCategory"
        @toggle-subcategory="toggleSubcategory"
        @toggle-category-expanded="toggleCategoryExpanded"
      />

      <!-- Chart Area -->
      <TimelineComponent
        :loading="loading"
        :has-data="hasData"
        :chart-options="chartOptions"
        :chart-series="chartSeries"
        :hovered-data="hoveredData"
        :current-zoom-level="currentZoomLevel"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @reset-zoom="resetZoom"
        @unpin-hover-data="unpinHoverData"
      />
    </div>

    <!-- Statistics Summary -->
    <div v-if="hasData" class="timeline-stats">
      <div class="stat-card">
        <div class="stat-label">Total Income</div>
        <div class="stat-value positive">{{ formatCurrency(stats.totalIncome) }}</div>
        <div class="stat-detail">{{ stats.incomeCount }} transactions</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Expenses</div>
        <div class="stat-value negative">{{ formatCurrency(stats.totalExpenses) }}</div>
        <div class="stat-detail">{{ stats.expenseCount }} transactions</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Transfers</div>
        <div class="stat-value neutral">{{ formatCurrency(stats.totalTransfers) }}</div>
        <div class="stat-detail">{{ stats.transferCount }} transactions</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Net Savings</div>
        <div class="stat-value" :class="stats.netSavings >= 0 ? 'positive' : 'negative'">
          {{ formatCurrency(stats.netSavings) }}
        </div>
        <div class="stat-detail">Income minus Expenses</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import CategoryLegend from './CategoryLegend.vue'
import TimelineComponent from './TimelineComponent.vue'

export default {
  name: 'TimelineTab',
  components: {
    CategoryLegend,
    TimelineComponent
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    
    const loading = ref(false)
    const transactions = ref([])
    const mainChart = ref(null)
    const hoveredData = ref(null)
    const isPinned = ref(false)
    
    const visibleTypes = ref(['income', 'expenses', 'transfers'])
    const visibleCategories = ref([])
    const visibleSubcategories = ref([])
    const expandedCategories = ref([])
    
    const currentZoomLevel = ref(0)
    
    const dateRange = ref({
      start: null,
      end: null
    })
    
    const hasData = computed(() => transactions.value.length > 0)
    
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
    
    const stats = computed(() => {
      const income = transactions.value
        .filter(t => t.transaction_type === 'income' && t.main_category !== 'TRANSFERS')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const expenses = transactions.value
        .filter(t => t.transaction_type === 'expense' && t.main_category !== 'TRANSFERS')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const transfers = transactions.value
        .filter(t => t.main_category === 'TRANSFERS')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const incomeCount = transactions.value
        .filter(t => t.transaction_type === 'income' && t.main_category !== 'TRANSFERS').length
      
      const expenseCount = transactions.value
        .filter(t => t.transaction_type === 'expense' && t.main_category !== 'TRANSFERS').length
      
      const transferCount = transactions.value
        .filter(t => t.main_category === 'TRANSFERS').length
      
      const netSavings = income - expenses
      
      return {
        totalIncome: income,
        totalExpenses: expenses,
        totalTransfers: transfers,
        netSavings,
        incomeCount,
        expenseCount,
        transferCount
      }
    })
    
    const zoomLevelName = computed(() => {
      const levels = ['All Time (Quarters)', 'Year View (Months)', 'Detail View (Days)']
      return levels[currentZoomLevel.value] || 'All Time'
    })
    
    const currentGrouping = computed(() => {
      if (currentZoomLevel.value === 0) return 'quarter'
      if (currentZoomLevel.value === 1) return 'month'
      return 'day'
    })
    
    const visibleDateRange = computed(() => {
      if (!dateRange.value.start || !dateRange.value.end) return null
      
      const totalDays = Math.floor((dateRange.value.end - dateRange.value.start) / (1000 * 60 * 60 * 24))
      
      if (currentZoomLevel.value === 0) {
        return {
          start: dateRange.value.start,
          end: dateRange.value.end
        }
      } else if (currentZoomLevel.value === 1) {
        const daysToShow = Math.min(365, totalDays)
        const end = dateRange.value.end
        const start = new Date(end.getTime() - (daysToShow * 24 * 60 * 60 * 1000))
        return { start, end }
      } else {
        const daysToShow = Math.min(90, totalDays)
        const end = dateRange.value.end
        const start = new Date(end.getTime() - (daysToShow * 24 * 60 * 60 * 1000))
        return { start, end }
      }
    })
    
    const timelineData = computed(() => {
      if (!transactions.value.length) return []
      return groupTransactionsByPeriod(transactions.value, currentGrouping.value)
    })
    
const chartSeries = computed(() => {
      if (!timelineData.value.length) return []
      
      const series = []
      
      // EXPENSES - Build as cumulative ranges
      if (isTypeVisible('expenses')) {
        const expensesByCategory = buildExpensesByCategory()
        
        const sortedExpenses = Object.entries(expensesByCategory)
          .sort((a, b) => {
            const sumA = Array.from(a[1].values()).reduce((s, v) => s + v, 0)
            const sumB = Array.from(b[1].values()).reduce((s, v) => s + v, 0)
            return sumB - sumA
          })
        
        let cumulativeExpenses = new Map()
        
        sortedExpenses.forEach(([category, dateMap]) => {
          const color = getCategoryColor(category)
          
          // Create line data for the TOP of this band
          const lineData = timelineData.value.map(d => {
            const amount = dateMap.get(d.date) || 0
            const cumulative = cumulativeExpenses.get(d.date) || 0
            const newCumulative = cumulative - amount
            
            cumulativeExpenses.set(d.date, newCumulative)
            
            return {
              x: d.date,
              y: newCumulative
            }
          })
          
          series.push({
            name: category,
            type: 'area',  // Changed from 'line' to 'area'
            data: lineData,
            color: color
          })
        })
        
      }
      
      // INCOME - Build as cumulative ranges
      if (isTypeVisible('income')) {
        const incomeByCategory = buildIncomeByCategory()
        
        let cumulativeIncome = new Map()
        
        Object.entries(incomeByCategory).forEach(([category, dateMap]) => {
          const color = getCategoryColor(category)
          
          const lineData = timelineData.value.map(d => {
            const amount = dateMap.get(d.date) || 0
            const cumulative = cumulativeIncome.get(d.date) || 0
            const newCumulative = cumulative + amount
            
            cumulativeIncome.set(d.date, newCumulative)
            
            return {
              x: d.date,
              y: newCumulative
            }
          })
          
          series.push({
            name: category,
            type: 'area',  // Changed from 'line' to 'area'
            data: lineData,
            color: color
          })
        })
        
      }
      
      // TRANSFERS
      if (isTypeVisible('transfers')) {
        const transfersByCategory = buildTransfersByCategory()
        
        const positiveTransfers = {}
        const negativeTransfers = {}
        
        Object.entries(transfersByCategory).forEach(([category, dateMap]) => {
          positiveTransfers[category] = new Map()
          negativeTransfers[category] = new Map()
          
          dateMap.forEach((amount, date) => {
            if (amount >= 0) {
              positiveTransfers[category].set(date, amount)
            } else {
              negativeTransfers[category].set(date, amount)
            }
          })
        })
        
        // Positive transfers
        let cumulativeTransfersPos = new Map()
        Object.entries(positiveTransfers).forEach(([category, dateMap]) => {
          if (Array.from(dateMap.values()).some(v => v > 0)) {
            const color = getCategoryColor(category)
            
            const lineData = timelineData.value.map(d => {
              const amount = dateMap.get(d.date) || 0
              const cumulative = cumulativeTransfersPos.get(d.date) || 0
              const newCumulative = cumulative + amount
              
              cumulativeTransfersPos.set(d.date, newCumulative)
              
              return {
                x: d.date,
                y: newCumulative
              }
            })
            
            series.push({
              name: `${category} (In)`,
              type: 'area',  // Changed from 'line' to 'area'
              data: lineData,
              color: color
            })
          }
        })
        
        // Negative transfers
        let cumulativeTransfersNeg = new Map()
        Object.entries(negativeTransfers).forEach(([category, dateMap]) => {
          if (Array.from(dateMap.values()).some(v => v < 0)) {
            const color = getCategoryColor(category)
            
            const lineData = timelineData.value.map(d => {
              const amount = dateMap.get(d.date) || 0
              const cumulative = cumulativeTransfersNeg.get(d.date) || 0
              const newCumulative = cumulative + amount
              
              cumulativeTransfersNeg.set(d.date, newCumulative)
              
              return {
                x: d.date,
                y: newCumulative
              }
            })
            
            series.push({
              name: `${category} (Out)`,
              type: 'area',  // Changed from 'line' to 'area'
              data: lineData,
              color: color
            })
          }
        })
      }
      
      return series
    })
    
    const yAxisMax = computed(() => {
      if (!chartSeries.value.length) return 1000
      
      let maxPositive = 0
      let maxNegative = 0
      
      chartSeries.value.forEach(series => {
        series.data.forEach(point => {
          const values = Array.isArray(point.y) ? point.y : [point.y]
          values.forEach(val => {
            if (val > maxPositive) maxPositive = val
            if (val < maxNegative) maxNegative = val
          })
        })
      })
      
      const maxValue = Math.max(maxPositive, Math.abs(maxNegative))
      return maxValue * 1.05
    })
    
const chartOptions = computed(() => {
      const range = visibleDateRange.value
      
      return {
        chart: {
          id: 'timeline-main',
          type: 'area',  // Changed from 'line' to 'area'
          height: 500,
          stacked: false,
          toolbar: {
            show: false
          },
          zoom: {
            enabled: false
          },
          animations: {
            enabled: false
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
          width: 1  // Thin border for areas
        },
        fill: {
          type: 'solid',
          opacity: 0.15  // Good visibility with slight transparency
        },
        legend: {
          show: false
        },
        markers: {
          size: 0
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
              colors: '#6b7280'
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
              color: '#6b7280'
            }
          },
          labels: {
            formatter: (val) => '€' + Math.round(val).toLocaleString(),
            style: {
              colors: '#6b7280'
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
    
    function getTypeColor(typeId) {
      const typeMap = {
        'income': '#00C9A0',
        'expenses': '#F17D99',
        'transfers': '#F0C46C'
      }
      
      const type = categoryStore.categories?.find(t => t.code === typeId || t.id === typeId)
      if (type?.color) return type.color
      
      return typeMap[typeId] || '#94a3b8'
    }
    
    function isTypeVisible(typeId) {
      return visibleTypes.value.includes(typeId)
    }
    
    function isCategoryVisible(categoryId) {
      return visibleCategories.value.includes(categoryId)
    }
    
    function isSubcategoryVisible(subcategoryId) {
      return visibleSubcategories.value.includes(subcategoryId)
    }
    
    function isCategoryExpanded(categoryId) {
      return expandedCategories.value.includes(categoryId)
    }
    
    function toggleCategoryExpanded(categoryId) {
      const index = expandedCategories.value.indexOf(categoryId)
      if (index > -1) {
        expandedCategories.value.splice(index, 1)
      } else {
        expandedCategories.value.push(categoryId)
      }
    }
    
    function toggleType(typeId) {
      const index = visibleTypes.value.indexOf(typeId)
      
      if (index > -1) {
        visibleTypes.value.splice(index, 1)
        
        let categories = []
        if (typeId === 'expenses') {
          categories = expenseCategories.value
        } else if (typeId === 'income') {
          categories = incomeCategories.value
        } else if (typeId === 'transfers') {
          categories = transferCategories.value
        }
        
        categories.forEach(cat => {
          const catIndex = visibleCategories.value.indexOf(cat.id)
          if (catIndex > -1) {
            visibleCategories.value.splice(catIndex, 1)
          }
          
          if (cat.children) {
            cat.children.forEach(subcat => {
              const subcatIndex = visibleSubcategories.value.indexOf(subcat.id)
              if (subcatIndex > -1) {
                visibleSubcategories.value.splice(subcatIndex, 1)
              }
            })
          }
        })
      } else {
        visibleTypes.value.push(typeId)
        
        let categories = []
        if (typeId === 'expenses') {
          categories = expenseCategories.value
        } else if (typeId === 'income') {
          categories = incomeCategories.value
        } else if (typeId === 'transfers') {
          categories = transferCategories.value
        }
        
        categories.forEach(cat => {
          if (!visibleCategories.value.includes(cat.id)) {
            visibleCategories.value.push(cat.id)
          }
          
          if (cat.children) {
            cat.children.forEach(subcat => {
              if (!visibleSubcategories.value.includes(subcat.id)) {
                visibleSubcategories.value.push(subcat.id)
              }
            })
          }
        })
      }
    }
    
    function toggleCategory(categoryId) {
      const index = visibleCategories.value.indexOf(categoryId)
      
      let category = null
      for (const categories of [expenseCategories.value, incomeCategories.value, transferCategories.value]) {
        category = categories.find(c => c.id === categoryId)
        if (category) break
      }
      
      if (!category) return
      
      if (index > -1) {
        visibleCategories.value.splice(index, 1)
        
        if (category.children) {
          category.children.forEach(subcat => {
            const subcatIndex = visibleSubcategories.value.indexOf(subcat.id)
            if (subcatIndex > -1) {
              visibleSubcategories.value.splice(subcatIndex, 1)
            }
          })
        }
      } else {
        visibleCategories.value.push(categoryId)
        
        if (category.children) {
          category.children.forEach(subcat => {
            if (!visibleSubcategories.value.includes(subcat.id)) {
              visibleSubcategories.value.push(subcat.id)
            }
          })
        }
      }
    }
    
    function toggleSubcategory(subcategoryId) {
      const index = visibleSubcategories.value.indexOf(subcategoryId)
      
      if (index > -1) {
        visibleSubcategories.value.splice(index, 1)
      } else {
        visibleSubcategories.value.push(subcategoryId)
      }
    }
    
    function zoomIn() {
      if (currentZoomLevel.value < 2) {
        currentZoomLevel.value++
      }
    }
    
    function zoomOut() {
      if (currentZoomLevel.value > 0) {
        currentZoomLevel.value--
      }
    }
    
    function resetZoom() {
      currentZoomLevel.value = 0
      isPinned.value = false
      hoveredData.value = null
    }
    
    function groupTransactionsByPeriod(txs, grouping) {
      if (grouping === 'quarter') {
        return groupTransactionsByQuarter(txs)
      } else if (grouping === 'month') {
        return groupTransactionsByMonth(txs)
      } else {
        return groupTransactionsByDay(txs)
      }
    }
    
    function groupTransactionsByDay(txs) {
      const grouped = new Map()
      
      txs.forEach(t => {
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
        
        if (t.transaction_type === 'income' && t.main_category !== 'TRANSFERS') {
          period.income += amount
          period.incomeByCategory[category] = (period.incomeByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'expense' && t.main_category !== 'TRANSFERS') {
          period.expenses += amount
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.main_category === 'TRANSFERS') {
          period.transfers += amount
          period.transfersByCategory[category] = (period.transfersByCategory[category] || 0) + amount
        }
      })
      
      return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
    }
    
    function groupTransactionsByMonth(txs) {
      const grouped = new Map()
      
      txs.forEach(t => {
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
        
        if (t.transaction_type === 'income' && t.main_category !== 'TRANSFERS') {
          period.income += amount
          period.incomeByCategory[category] = (period.incomeByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'expense' && t.main_category !== 'TRANSFERS') {
          period.expenses += amount
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.main_category === 'TRANSFERS') {
          period.transfers += amount
          period.transfersByCategory[category] = (period.transfersByCategory[category] || 0) + amount
        }
      })
      
      return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
    }
    
    function groupTransactionsByQuarter(txs) {
      const grouped = new Map()
      
      txs.forEach(t => {
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
        
        if (t.transaction_type === 'income' && t.main_category !== 'TRANSFERS') {
          period.income += amount
          period.incomeByCategory[category] = (period.incomeByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'expense' && t.main_category !== 'TRANSFERS') {
          period.expenses += amount
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.main_category === 'TRANSFERS') {
          period.transfers += amount
          period.transfersByCategory[category] = (period.transfersByCategory[category] || 0) + amount
        }
      })
      
      return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
    }
    
    function findParentCategory(subcategoryName) {
      const allCategories = [
        ...expenseCategories.value,
        ...incomeCategories.value,
        ...transferCategories.value
      ]
      
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
    
function buildExpensesByCategory() {
      const expensesByCategory = {}
      const processedTransactions = new Set()
      
      transactions.value
        .filter(t => t.transaction_type === 'expense' && t.main_category !== 'TRANSFERS')
        .forEach(t => {
          if (processedTransactions.has(t.id)) return
          
          const subcategoryName = t.subcategory
          const categoryName = t.category || 'Uncategorized'
          const amount = Math.abs(parseFloat(t.amount))
          
          const parentCategory = subcategoryName ? findParentCategory(subcategoryName) : null
          
          let displayName = categoryName
          let shouldInclude = true
          
          if (parentCategory) {
            // Has parent category - check visibility
            if (!isCategoryVisible(parentCategory.id)) {
              shouldInclude = false
            } else {
              if (isCategoryExpanded(parentCategory.id)) {
                // Parent is expanded - show subcategory if visible
                if (subcategoryName) {
                  const subcategoryId = findCategoryId(subcategoryName)
                  if (subcategoryId && isSubcategoryVisible(subcategoryId)) {
                    displayName = subcategoryName
                  } else {
                    shouldInclude = false
                  }
                } else {
                  displayName = categoryName
                }
              } else {
                // Parent is collapsed - show parent name
                displayName = parentCategory.name
              }
            }
          } else {
            // No parent found - check if this category itself is visible
            const categoryId = findCategoryId(categoryName)
            if (categoryId && isCategoryVisible(categoryId)) {
              displayName = categoryName
            } else {
              shouldInclude = false
            }
          }
          
          if (!shouldInclude) return
          
          processedTransactions.add(t.id)
          
          if (!expensesByCategory[displayName]) {
            expensesByCategory[displayName] = new Map()
          }
          
          const date = new Date(t.posted_at)
          let key
          
          if (currentGrouping.value === 'quarter') {
            const quarter = Math.floor(date.getMonth() / 3)
            const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
            key = quarterStart.getTime()
          } else if (currentGrouping.value === 'month') {
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
    
    function buildIncomeByCategory() {
      const incomeByCategory = {}
      const processedTransactions = new Set()
      
      transactions.value
        .filter(t => t.transaction_type === 'income' && t.main_category !== 'TRANSFERS')
        .forEach(t => {
          if (processedTransactions.has(t.id)) return
          
          const subcategoryName = t.subcategory
          const categoryName = t.category || 'Income'
          const amount = Math.abs(parseFloat(t.amount))
          
          const parentCategory = subcategoryName ? findParentCategory(subcategoryName) : null
          
          let displayName = categoryName
          let shouldInclude = true
          
          if (parentCategory) {
            // Has parent category - check visibility
            if (!isCategoryVisible(parentCategory.id)) {
              shouldInclude = false
            } else {
              if (isCategoryExpanded(parentCategory.id)) {
                // Parent is expanded - show subcategory if visible
                if (subcategoryName) {
                  const subcategoryId = findCategoryId(subcategoryName)
                  if (subcategoryId && isSubcategoryVisible(subcategoryId)) {
                    displayName = subcategoryName
                  } else {
                    shouldInclude = false
                  }
                } else {
                  displayName = categoryName
                }
              } else {
                // Parent is collapsed - show parent name
                displayName = parentCategory.name
              }
            }
          } else {
            // No parent found - check if this category itself is visible
            const categoryId = findCategoryId(categoryName)
            if (categoryId && isCategoryVisible(categoryId)) {
              displayName = categoryName
            } else {
              shouldInclude = false
            }
          }
          
          if (!shouldInclude) return
          
          processedTransactions.add(t.id)
          
          if (!incomeByCategory[displayName]) {
            incomeByCategory[displayName] = new Map()
          }
          
          const date = new Date(t.posted_at)
          let key
          
          if (currentGrouping.value === 'quarter') {
            const quarter = Math.floor(date.getMonth() / 3)
            const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
            key = quarterStart.getTime()
          } else if (currentGrouping.value === 'month') {
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
    
    function buildTransfersByCategory() {
      const transfersByCategory = {}
      const processedTransactions = new Set()
      
      transactions.value
        .filter(t => t.main_category === 'TRANSFERS')
        .forEach(t => {
          if (processedTransactions.has(t.id)) return
          
          const subcategoryName = t.subcategory
          const categoryName = t.category || 'Transfer'
          const amount = parseFloat(t.amount)
          
          const parentCategory = subcategoryName ? findParentCategory(subcategoryName) : null
          
          let displayName = categoryName
          let shouldInclude = true
          
          if (parentCategory) {
            // Has parent category - check visibility
            if (!isCategoryVisible(parentCategory.id)) {
              shouldInclude = false
            } else {
              if (isCategoryExpanded(parentCategory.id)) {
                // Parent is expanded - show subcategory if visible
                if (subcategoryName) {
                  const subcategoryId = findCategoryId(subcategoryName)
                  if (subcategoryId && isSubcategoryVisible(subcategoryId)) {
                    displayName = subcategoryName
                  } else {
                    shouldInclude = false
                  }
                } else {
                  displayName = categoryName
                }
              } else {
                // Parent is collapsed - show parent name
                displayName = parentCategory.name
              }
            }
          } else {
            // No parent found - check if this category itself is visible
            const categoryId = findCategoryId(categoryName)
            if (categoryId && isCategoryVisible(categoryId)) {
              displayName = categoryName
            } else {
              shouldInclude = false
            }
          }
          
          if (!shouldInclude) return
          
          processedTransactions.add(t.id)
          
          if (!transfersByCategory[displayName]) {
            transfersByCategory[displayName] = new Map()
          }
          
          const date = new Date(t.posted_at)
          let key
          
          if (currentGrouping.value === 'quarter') {
            const quarter = Math.floor(date.getMonth() / 3)
            const quarterStart = new Date(date.getFullYear(), quarter * 3, 1)
            key = quarterStart.getTime()
          } else if (currentGrouping.value === 'month') {
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
    
    function findCategoryId(categoryName) {
      if (!categoryStore.categories) return null
      
      for (const type of categoryStore.categories) {
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
    
    function getCategoryColor(categoryName) {
      if (!categoryStore.categories) return '#94a3b8'
      
      // Check all categories and subcategories
      for (const type of categoryStore.categories) {
        if (type.children) {
          for (const cat of type.children) {
            // Check if this is the category we're looking for
            if (cat.name === categoryName) {
              return cat.color || '#94a3b8'
            }
            
            // Check subcategories
            if (cat.children) {
              for (const subcat of cat.children) {
                if (subcat.name === categoryName) {
                  // Subcategory found - return its color or parent color
                  return subcat.color || cat.color || '#94a3b8'
                }
              }
            }
          }
        }
      }
      
      // If not found in store, return default color
      return '#94a3b8'
    }
    
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
    
    function unpinHoverData() {
      isPinned.value = false
      hoveredData.value = null
    }
    
    async function loadTransactions() {
      if (!authStore.token) return
      
      loading.value = true
      
      try {
        let allTransactions = []
        let page = 1
        const batchSize = 1000
        
        while (page <= 10) {
          const response = await fetch(
            `${API_BASE}/transactions/list?page=${page}&limit=${batchSize}`,
            {
              headers: { Authorization: `Bearer ${authStore.token}` }
            }
          )
          
          if (!response.ok) throw new Error('Failed to load transactions')
          
          const data = await response.json()
          
          if (data.length === 0) break
          
          allTransactions = allTransactions.concat(data)
          
          if (data.length < batchSize) break
          
          page++
        }
        
        transactions.value = allTransactions
        
        if (allTransactions.length > 0) {
          const dates = allTransactions.map(t => new Date(t.posted_at))
          dateRange.value.start = new Date(Math.min(...dates))
          dateRange.value.end = new Date(Math.max(...dates))
        }
        
        initializeVisibility()
        
        console.log('Timeline loaded:', allTransactions.length, 'transactions')
        
      } catch (error) {
        console.error('Failed to load transactions:', error)
      } finally {
        loading.value = false
      }
    }
    
    function initializeVisibility() {
      visibleCategories.value = []
      visibleSubcategories.value = []
      
      const allCategories = [
        ...expenseCategories.value,
        ...incomeCategories.value,
        ...transferCategories.value
      ]
      
      allCategories.forEach(cat => {
        visibleCategories.value.push(cat.id)
        
        if (cat.children) {
          cat.children.forEach(subcat => {
            visibleSubcategories.value.push(subcat.id)
          })
        }
      })
    }
    
    async function refreshData() {
      await loadTransactions()
    }
    
    function formatDate(dateValue) {
      const date = typeof dateValue === 'number' ? new Date(dateValue) : 
                   typeof dateValue === 'string' ? new Date(dateValue) : dateValue
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    }
    
    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }
    
    watch([visibleTypes, visibleCategories, visibleSubcategories, expandedCategories], () => {
      console.log('Visibility changed, chart will rebuild')
    }, { deep: true })
    
    watch(() => currentZoomLevel.value, (newLevel) => {
      console.log('Zoom level changed to:', zoomLevelName.value)
      isPinned.value = false
      hoveredData.value = null
    })
    
    onMounted(async () => {
      if (authStore.user) {
        await categoryStore.loadCategories()
        await loadTransactions()
      }
    })
    
    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadTransactions()
      }
    })
    
    return {
      loading,
      mainChart,
      dateRange,
      hasData,
      stats,
      timelineData,
      chartSeries,
      chartOptions,
      expenseCategories,
      incomeCategories,
      transferCategories,
      visibleTypes,
      visibleCategories,
      visibleSubcategories,
      expandedCategories,
      hoveredData,
      isPinned,
      currentZoomLevel,
      zoomLevelName,
      getTypeColor,
      isTypeVisible,
      isCategoryVisible,
      isSubcategoryVisible,
      isCategoryExpanded,
      toggleCategoryExpanded,
      toggleType,
      toggleCategory,
      toggleSubcategory,
      zoomIn,
      zoomOut,
      resetZoom,
      unpinHoverData,
      refreshData,
      formatDate,
      formatCurrency
    }
  }
}
</script>




<style>
.timeline-container {
  padding: var(--gap-standard);
}

.timeline-main-content {
  display: flex;
  gap: var(--gap-standard);
  margin-bottom: var(--gap-standard);
}

.timeline-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap-standard);
}

.stat-card {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  text-align: center;
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.stat-value.positive {
  color: #22c55e;
}

.stat-value.negative {
  color: #ef4444;
}

.stat-value.neutral {
  color: #3b82f6;
}

.stat-detail {
  font-size: var(--text-small);
  color: var(--color-text-light);
}

@media (max-width: 64rem) {
  .timeline-main-content {
    flex-direction: column;
  }
  
  .timeline-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 48rem) {
  .timeline-container {
    padding: var(--gap-small);
  }
  
  .timeline-stats {
    grid-template-columns: 1fr;
  }
}
</style>