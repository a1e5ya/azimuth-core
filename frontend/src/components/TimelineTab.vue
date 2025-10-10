<template>
  <div class="timeline-container">
    <!-- Header Controls -->
    <div class="timeline-header">
      <div class="timeline-title">
        <span class="timeline-subtitle">
          {{ formatDateRange(dateRange.start, dateRange.end) }}
        </span>
      </div>
      
      <div class="timeline-controls">
        <button 
          class="btn btn-small" 
          @click="refreshData"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Main Content: Legend + Chart -->
    <div class="timeline-main-content">
      <!-- Compact Legend - Left Side -->
      <div class="timeline-legend-sidebar">
        <!-- EXPENSES Section -->
        <div class="legend-section">
          <div 
            class="legend-type-header" 
            @click="toggleType('expenses')"
          >
            <span 
              class="legend-indicator" 
              :style="{ backgroundColor: isTypeVisible('expenses') ? getTypeColor('expenses') : '#fff' }"
            ></span>
            <span class="legend-type-name">EXPENSES</span>
          </div>
          
          <div class="legend-categories-list">
            <div 
              class="legend-category-item" 
              v-for="category in expenseCategories" 
              :key="category.id"
            >
              <div class="legend-category-row">
                <div 
                  class="legend-category-header"
                  @click="toggleCategory(category.id)"
                >
                  <span 
                    class="legend-indicator legend-indicator-small" 
                    :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                  ></span>
                  <span class="legend-item-name">{{ category.name }}</span>
                </div>
                
                <button 
                  v-if="category.children && category.children.length > 0"
                  class="legend-expand-btn"
                  @click.stop="toggleCategoryExpanded(category.id)"
                >
                  {{ isCategoryExpanded(category.id) ? '−' : '+' }}
                </button>
              </div>
              
              <div 
                v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
                class="legend-subcategories-list"
              >
                <div 
                  class="legend-subcat-item" 
                  v-for="subcat in category.children" 
                  :key="subcat.id"
                  @click="toggleSubcategory(subcat.id)"
                >
                  <span 
                    class="legend-indicator legend-indicator-tiny" 
                    :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                  ></span>
                  <span class="legend-item-name">{{ subcat.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- INCOME Section -->
        <div class="legend-section">
          <div 
            class="legend-type-header" 
            @click="toggleType('income')"
          >
            <span 
              class="legend-indicator" 
              :style="{ backgroundColor: isTypeVisible('income') ? getTypeColor('income') : '#fff' }"
            ></span>
            <span class="legend-type-name">INCOME</span>
          </div>
          
          <div class="legend-categories-list">
            <div 
              class="legend-category-item" 
              v-for="category in incomeCategories" 
              :key="category.id"
            >
              <div class="legend-category-row">
                <div 
                  class="legend-category-header"
                  @click="toggleCategory(category.id)"
                >
                  <span 
                    class="legend-indicator legend-indicator-small" 
                    :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                  ></span>
                  <span class="legend-item-name">{{ category.name }}</span>
                </div>
                
                <button 
                  v-if="category.children && category.children.length > 0"
                  class="legend-expand-btn"
                  @click.stop="toggleCategoryExpanded(category.id)"
                >
                  {{ isCategoryExpanded(category.id) ? '−' : '+' }}
                </button>
              </div>
              
              <div 
                v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
                class="legend-subcategories-list"
              >
                <div 
                  class="legend-subcat-item" 
                  v-for="subcat in category.children" 
                  :key="subcat.id"
                  @click="toggleSubcategory(subcat.id)"
                >
                  <span 
                    class="legend-indicator legend-indicator-tiny" 
                    :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                  ></span>
                  <span class="legend-item-name">{{ subcat.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TRANSFERS Section -->
        <div class="legend-section">
          <div 
            class="legend-type-header" 
            @click="toggleType('transfers')"
          >
            <span 
              class="legend-indicator" 
              :style="{ backgroundColor: isTypeVisible('transfers') ? getTypeColor('transfers') : '#fff' }"
            ></span>
            <span class="legend-type-name">TRANSFERS</span>
          </div>
          
          <div class="legend-categories-list">
            <div 
              class="legend-category-item" 
              v-for="category in transferCategories" 
              :key="category.id"
            >
              <div class="legend-category-row">
                <div 
                  class="legend-category-header"
                  @click="toggleCategory(category.id)"
                >
                  <span 
                    class="legend-indicator legend-indicator-small" 
                    :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                  ></span>
                  <span class="legend-item-name">{{ category.name }}</span>
                </div>
                
                <button 
                  v-if="category.children && category.children.length > 0"
                  class="legend-expand-btn"
                  @click.stop="toggleCategoryExpanded(category.id)"
                >
                  {{ isCategoryExpanded(category.id) ? '−' : '+' }}
                </button>
              </div>
              
              <div 
                v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
                class="legend-subcategories-list"
              >
                <div 
                  class="legend-subcat-item" 
                  v-for="subcat in category.children" 
                  :key="subcat.id"
                  @click="toggleSubcategory(subcat.id)"
                >
                  <span 
                    class="legend-indicator legend-indicator-tiny" 
                    :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                  ></span>
                  <span class="legend-item-name">{{ subcat.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Area -->
      <div class="timeline-chart-area">
        <div class="timeline-chart-wrapper">
          <div v-if="loading" class="loading-state">
            <div class="loading-spinner">⟳</div>
            <p>Loading timeline data...</p>
          </div>
          
          <div v-else-if="!hasData" class="empty-state">
            <p class="empty-title">No transaction data available</p>
            <p class="empty-subtitle">Import transactions to see your financial timeline</p>
          </div>
          
          <div v-else class="timeline-chart">
            <apexchart
              ref="mainChart"
              type="area"
              height="500"
              :options="chartOptions"
              :series="chartSeries"
            />
          </div>
        </div>

        <!-- Hover Info Field - Below Chart -->
        <div v-if="hoveredData" class="hover-info-field">
          <div class="hover-info-header">
            <h4>{{ formatDate(hoveredData.date) }}</h4>
            <button class="btn-icon btn-small" @click="hoveredData = null">×</button>
          </div>
          
          <div class="hover-info-content">
            <div class="hover-info-section" v-if="hoveredData.income > 0">
              <div class="hover-info-label positive">Income</div>
              <div class="hover-info-value">{{ formatCurrency(hoveredData.income) }}</div>
            </div>

            <div class="hover-info-section" v-if="hoveredData.expenses > 0">
              <div class="hover-info-label negative">Expenses</div>
              <div class="hover-info-value">{{ formatCurrency(hoveredData.expenses) }}</div>
              
              <div class="hover-info-categories" v-if="hoveredData.expensesByCategory">
                <div 
                  class="hover-info-category" 
                  v-for="(amount, category) in hoveredData.expensesByCategory" 
                  :key="category"
                  v-show="amount > 0"
                >
                  <span class="hover-category-name">{{ category }}</span>
                  <span class="hover-category-amount">{{ formatCurrency(amount) }}</span>
                </div>
              </div>
            </div>

            <div class="hover-info-section" v-if="hoveredData.transfers > 0">
              <div class="hover-info-label neutral">Transfers</div>
              <div class="hover-info-value">{{ formatCurrency(hoveredData.transfers) }}</div>
            </div>

            <div class="hover-info-section hover-info-total" v-if="hoveredData.balance !== undefined">
              <div class="hover-info-label">Balance Change</div>
              <div class="hover-info-value" :class="hoveredData.balance >= 0 ? 'positive' : 'negative'">
                {{ formatCurrency(hoveredData.balance) }}
              </div>
            </div>
          </div>
        </div>
      </div>
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
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'TimelineTab',
  components: {
    apexchart: VueApexCharts
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    
    // State
    const loading = ref(false)
    const transactions = ref([])
    const mainChart = ref(null)
    const hoveredData = ref(null)
    
    // Visibility toggles
    const visibleTypes = ref(['income', 'expenses', 'transfers'])
    const visibleCategories = ref([])
    const visibleSubcategories = ref([])
    const expandedCategories = ref([])
    
    const dateRange = ref({
      start: null,
      end: null
    })
    
    // Computed
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
        .filter(t => t.transaction_type === 'income')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const expenses = transactions.value
        .filter(t => t.transaction_type === 'expense')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const transfers = transactions.value
        .filter(t => t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const incomeCount = transactions.value
        .filter(t => t.transaction_type === 'income').length
      
      const expenseCount = transactions.value
        .filter(t => t.transaction_type === 'expense').length
      
      const transferCount = transactions.value
        .filter(t => t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS').length
      
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
    
    const timelineData = computed(() => {
      if (!transactions.value.length) return []
      return groupTransactionsByPeriod(transactions.value)
    })
    
    const chartSeries = computed(() => {
      if (!timelineData.value.length) return []
      
      const series = []
      
      // Build expense series by category/subcategory (negative values - below zero)
      if (isTypeVisible('expenses')) {
        const expensesByCategory = buildExpensesByCategory()
        
        Object.entries(expensesByCategory)
          .sort((a, b) => {
            const sumA = Array.from(a[1].values()).reduce((s, v) => s + v, 0)
            const sumB = Array.from(b[1].values()).reduce((s, v) => s + v, 0)
            return sumB - sumA
          })
          .forEach(([category, dateMap]) => {
            const color = getCategoryColor(category)
            
            series.push({
              name: category,
              type: 'area',
              data: timelineData.value.map(d => ({
                x: d.date,
                y: -(dateMap.get(d.date) || 0)
              })),
              color: color
            })
          })
      }
      
      // Income series (positive values - above zero)
      if (isTypeVisible('income')) {
        const incomeByCategory = buildIncomeByCategory()
        
        Object.entries(incomeByCategory).forEach(([category, dateMap]) => {
          const color = getCategoryColor(category)
          
          series.push({
            name: category,
            type: 'area',
            data: timelineData.value.map(d => ({
              x: d.date,
              y: dateMap.get(d.date) || 0
            })),
            color: color
          })
        })
      }
      
      // Transfers series (line)
      if (isTypeVisible('transfers')) {
        const transfersByCategory = buildTransfersByCategory()
        
        Object.entries(transfersByCategory).forEach(([category, dateMap]) => {
          const color = getCategoryColor(category)
          
          series.push({
            name: category,
            type: 'line',
            data: timelineData.value.map(d => ({
              x: d.date,
              y: dateMap.get(d.date) || 0
            })),
            color: color
          })
        })
      }
      
      return series
    })
    
    const chartOptions = computed(() => {
      return {
        chart: {
          id: 'timeline-main',
          type: 'area',
          height: 500,
          stacked: true,
          toolbar: {
            show: true,
            tools: {
              download: true,
              selection: true,
              zoom: true,
              zoomin: true,
              zoomout: true,
              pan: true,
              reset: true
            }
          },
          zoom: {
            enabled: true,
            type: 'x',
            autoScaleYaxis: true
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
              // Keep hover info visible
            }
          }
        },
        dataLabels: {
          enabled: false
        },
        stroke: {
          curve: 'smooth',
          width: chartSeries.value.map((serie) => {
            if (serie.type === 'line') return 2
            return 0
          })
        },
        fill: {
          type: 'solid',
          opacity: chartSeries.value.map((serie) => {
            if (serie.type === 'line') return 0.3
            return 0.8
          })
        },
        legend: {
          show: false
        },
        markers: {
          size: 0,
          strokeWidth: 0,
          hover: {
            size: 5,
            sizeOffset: 3
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
          labels: {
            datetimeUTC: false,
            style: {
              colors: '#6b7280'
            }
          },
          crosshairs: {
            show: true,
            position: 'front',
            stroke: {
              color: '#374151',
              width: 1,
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
          }
        },
        tooltip: {
          enabled: true,
          shared: true,
          intersect: false,
          x: {
            format: 'dd MMM yyyy'
          },
          y: {
            formatter: (val) => '€' + Math.abs(val).toFixed(2)
          }
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
    
    // Methods
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
    
    function groupTransactionsByPeriod(txs) {
      if (!dateRange.value.start || !dateRange.value.end) {
        return groupTransactionsByDay(txs)
      }
      
      const daysDiff = Math.floor((dateRange.value.end - dateRange.value.start) / (1000 * 60 * 60 * 24))
      
      if (daysDiff > 730) {
        return groupTransactionsByQuarter(txs)
      } else if (daysDiff > 180) {
        return groupTransactionsByMonth(txs)
      } else if (daysDiff > 60) {
        return groupTransactionsByWeek(txs)
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
            expensesByCategory: {}
          })
        }
        
        const period = grouped.get(keyStr)
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          period.income += amount
        } else if (t.transaction_type === 'expense') {
          period.expenses += amount
          const category = t.csv_subcategory || t.csv_category || 'Uncategorized'
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS') {
          period.transfers += amount
        }
      })
      
      return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
    }
    
    function groupTransactionsByWeek(txs) {
      const grouped = new Map()
      
      txs.forEach(t => {
        const date = new Date(t.posted_at)
        const weekStart = new Date(date)
        weekStart.setDate(date.getDate() - date.getDay())
        weekStart.setHours(0, 0, 0, 0)
        const keyStr = weekStart.toISOString()
        
        if (!grouped.has(keyStr)) {
          grouped.set(keyStr, {
            date: weekStart.getTime(),
            income: 0,
            expenses: 0,
            transfers: 0,
            expensesByCategory: {}
          })
        }
        
        const period = grouped.get(keyStr)
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          period.income += amount
        } else if (t.transaction_type === 'expense') {
          period.expenses += amount
          const category = t.csv_subcategory || t.csv_category || 'Uncategorized'
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS') {
          period.transfers += amount
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
            expensesByCategory: {}
          })
        }
        
        const period = grouped.get(keyStr)
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          period.income += amount
        } else if (t.transaction_type === 'expense') {
          period.expenses += amount
          const category = t.csv_subcategory || t.csv_category || 'Uncategorized'
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS') {
          period.transfers += amount
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
            expensesByCategory: {}
          })
        }
        
        const period = grouped.get(keyStr)
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          period.income += amount
        } else if (t.transaction_type === 'expense') {
          period.expenses += amount
          const category = t.csv_subcategory || t.csv_category || 'Uncategorized'
          period.expensesByCategory[category] = (period.expensesByCategory[category] || 0) + amount
        } else if (t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS') {
          period.transfers += amount
        }
      })
      
      return Array.from(grouped.values()).sort((a, b) => a.date - b.date)
    }
    
    function buildExpensesByCategory() {
      const expensesByCategory = {}
      
      transactions.value
        .filter(t => t.transaction_type === 'expense')
        .forEach(t => {
          const category = t.csv_subcategory || t.csv_category || 'Uncategorized'
          
          const categoryId = findCategoryId(category)
          if (categoryId && !isSubcategoryVisible(categoryId) && !isCategoryVisible(categoryId)) {
            return
          }
          
          if (!expensesByCategory[category]) {
            expensesByCategory[category] = new Map()
          }
          
          const date = new Date(t.posted_at)
          const key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
          const amount = Math.abs(parseFloat(t.amount))
          
          expensesByCategory[category].set(key, (expensesByCategory[category].get(key) || 0) + amount)
        })
      
      return expensesByCategory
    }
    
    function buildIncomeByCategory() {
      const incomeByCategory = {}
      
      transactions.value
        .filter(t => t.transaction_type === 'income')
        .forEach(t => {
          const category = t.csv_subcategory || t.csv_category || 'Income'
          
          const categoryId = findCategoryId(category)
          if (categoryId && !isSubcategoryVisible(categoryId) && !isCategoryVisible(categoryId)) {
            return
          }
          
          if (!incomeByCategory[category]) {
            incomeByCategory[category] = new Map()
          }
          
          const date = new Date(t.posted_at)
          const key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
          const amount = Math.abs(parseFloat(t.amount))
          
          incomeByCategory[category].set(key, (incomeByCategory[category].get(key) || 0) + amount)
        })
      
      return incomeByCategory
    }
    
    function buildTransfersByCategory() {
      const transfersByCategory = {}
      
      transactions.value
        .filter(t => t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS')
        .forEach(t => {
          const category = t.csv_subcategory || t.csv_category || 'Transfer'
          
          const categoryId = findCategoryId(category)
          if (categoryId && !isSubcategoryVisible(categoryId) && !isCategoryVisible(categoryId)) {
            return
          }
          
          if (!transfersByCategory[category]) {
            transfersByCategory[category] = new Map()
          }
          
          const date = new Date(t.posted_at)
          const key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
          const amount = Math.abs(parseFloat(t.amount))
          
          transfersByCategory[category].set(key, (transfersByCategory[category].get(key) || 0) + amount)
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
      
      for (const type of categoryStore.categories) {
        if (type.children) {
          for (const cat of type.children) {
            if (cat.name === categoryName) return cat.color || '#94a3b8'
            
            if (cat.children) {
              for (const subcat of cat.children) {
                if (subcat.name === categoryName) return subcat.color || cat.color || '#94a3b8'
              }
            }
          }
        }
      }
      
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
        expensesByCategory: dataPoint.expensesByCategory
      }
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
        if (error.response?.status === 401) {
          await authStore.verifyToken()
        }
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
    
    function formatDateRange(start, end) {
      if (!start || !end) return 'All Time'
      return `${formatDate(start)} - ${formatDate(end)}`
    }
    
    function formatDate(dateStr) {
      const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
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
      getTypeColor,
      isTypeVisible,
      isCategoryVisible,
      isSubcategoryVisible,
      isCategoryExpanded,
      toggleCategoryExpanded,
      toggleType,
      toggleCategory,
      toggleSubcategory,
      refreshData,
      formatDateRange,
      formatDate,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.timeline-container {
  padding: var(--gap-standard);
}

/* Header */
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  flex-wrap: wrap;
  gap: var(--gap-standard);
}

.timeline-title h2 {
  margin: 0 0 0.25rem 0;
}

.timeline-subtitle {
  color: var(--color-text-light);
  font-size: var(--text-small);
}

.timeline-controls {
  display: flex;
  gap: var(--gap-small);
  align-items: center;
}

/* Main Content Layout */
.timeline-main-content {
  display: flex;
  gap: var(--gap-standard);
  margin-bottom: var(--gap-standard);
}

/* Legend Sidebar */
.timeline-legend-sidebar {
  width: 250px;
  flex-shrink: 0;
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-small);
  max-height: 80vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.legend-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.legend-type-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  font-weight: 600;
  font-size: var(--text-small);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.legend-type-header:hover {
  background: var(--color-background-dark);
}

.legend-type-name {
  user-select: none;
}

.legend-indicator {
  width: 1rem;
  height: 1rem;
  border-radius: 0.25rem;
  border: 2px solid var(--color-background-dark);
  flex-shrink: 0;
  transition: all 0.2s;
}

.legend-indicator-small {
  width: 0.875rem;
  height: 0.875rem;
}

.legend-indicator-tiny {
  width: 0.625rem;
  height: 0.625rem;
}

.legend-categories-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.legend-category-item {
  display: flex;
  flex-direction: column;
}

.legend-category-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.25rem;
}

.legend-category-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.8125rem;
  flex: 1;
}

.legend-category-header:hover {
  background: var(--color-background-dark);
}

.legend-item-name {
  user-select: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.legend-expand-btn {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-light);
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: background 0.2s;
  flex-shrink: 0;
}

.legend-expand-btn:hover {
  background: var(--color-background-dark);
}

.legend-subcategories-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-left: 1rem;
  margin-top: 0.25rem;
}

.legend-subcat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.375rem;
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.75rem;
}

.legend-subcat-item:hover {
  background: var(--color-background-dark);
}

/* Chart Area */
.timeline-chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.timeline-chart-wrapper {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  min-height: 500px;
}

.timeline-chart {
  width: 100%;
}

/* Hover Info Field */
.hover-info-field {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  border: 2px solid var(--color-background-dark);
}

.hover-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--color-background-dark);
}

.hover-info-header h4 {
  margin: 0;
  font-size: var(--text-medium);
  font-weight: 600;
}

.hover-info-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap-standard);
}

.hover-info-section {
  padding: 0.75rem;
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.hover-info-total {
  grid-column: 1 / -1;
  background: var(--color-background-dark);
}

.hover-info-label {
  font-size: var(--text-small);
  font-weight: 600;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.hover-info-label.positive {
  color: #22c55e;
}

.hover-info-label.negative {
  color: #ef4444;
}

.hover-info-label.neutral {
  color: #3b82f6;
}

.hover-info-value {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.hover-info-value.positive {
  color: #22c55e;
}

.hover-info-value.negative {
  color: #ef4444;
}

.hover-info-categories {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-background-dark);
}

.hover-info-category {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-small);
  padding: 0.25rem 0;
}

.hover-category-name {
  color: var(--color-text-light);
}

.hover-category-amount {
  font-weight: 500;
  color: var(--color-text);
}

/* Loading and Empty States */
.loading-state,
.empty-state {
  text-align: center;
  padding: var(--gap-large);
  color: var(--color-text-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}

.loading-spinner {
  font-size: 2rem;
  animation: spin 1s linear infinite;
  margin-bottom: var(--gap-standard);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-title {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.empty-subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-small);
}

/* Statistics */
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

/* Responsive Design */
@media (max-width: 64rem) {
  .timeline-main-content {
    flex-direction: column;
  }
  
  .timeline-legend-sidebar {
    width: 100%;
    max-height: 300px;
  }
  
  .timeline-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .timeline-title {
    text-align: center;
  }
  
  .timeline-controls {
    justify-content: center;
  }
  
  .timeline-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .hover-info-content {
    grid-template-columns: 1fr;
  }
  
  .hover-info-total {
    grid-column: 1;
  }
}

@media (max-width: 48rem) {
  .timeline-container {
    padding: var(--gap-small);
  }
  
  .timeline-legend-sidebar {
    padding: var(--gap-small);
  }
  
  .timeline-stats {
    grid-template-columns: 1fr;
  }
  
  .timeline-chart-wrapper {
    padding: var(--gap-small);
    min-height: 400px;
  }
  
  .loading-state,
  .empty-state {
    min-height: 400px;
  }
  
  .hover-info-field {
    padding: var(--gap-small);
  }
}

@media (max-width: 30rem) {
  .timeline-header {
    gap: var(--gap-small);
  }
  
  .timeline-controls {
    width: 100%;
  }
  
  .timeline-controls button {
    flex: 1;
  }
  
  .legend-type-header {
    font-size: 0.75rem;
    padding: 0.375rem 0.5rem;
  }
  
  .legend-category-header {
    font-size: 0.75rem;
  }
  
  .legend-subcat-item {
    font-size: 0.6875rem;
  }
}
</style>