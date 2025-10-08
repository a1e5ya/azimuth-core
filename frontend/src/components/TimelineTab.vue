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
        <!-- Refresh Button -->
        <button 
          class="btn btn-small" 
          @click="refreshData"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Main Timeline Chart -->
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
        <div class="stat-detail">
          Income minus Expenses
        </div>
      </div>
    </div>

    <!-- Top Categories Breakdown -->
    <div v-if="hasData && topCategories.length > 0" class="container">
      <h3 style="margin-bottom: var(--gap-standard);">Top Spending Categories</h3>
      <div class="category-breakdown-grid">
        <div v-for="(cat, index) in topCategories" :key="index" class="category-breakdown-item">
          <div class="category-breakdown-header">
            <div class="category-breakdown-rank">{{ index + 1 }}</div>
            <div class="category-breakdown-info">
              <div class="category-breakdown-name">{{ cat.name }}</div>
              <div class="category-breakdown-amount">{{ formatCurrency(cat.amount) }}</div>
            </div>
          </div>
          <div class="category-breakdown-bar-container">
            <div class="category-breakdown-bar" :style="{ width: cat.percentage + '%' }"></div>
          </div>
          <div class="category-breakdown-details">
            <span>{{ cat.count }} transactions</span>
            <span>{{ cat.percentage.toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Monthly Comparison -->
    <div v-if="hasData && monthlyComparison.length > 0" class="container">
      <h3 style="margin-bottom: var(--gap-standard);">Monthly Comparison</h3>
      <div class="comparison-grid">
        <div v-for="item in monthlyComparison" :key="item.period" class="comparison-item">
          <div class="comparison-period-name">{{ item.periodName }}</div>
          <div class="comparison-stats">
            <div class="comparison-stat">
              <span class="comparison-label">Income:</span>
              <span class="comparison-value positive">{{ formatCurrency(item.income) }}</span>
            </div>
            <div class="comparison-stat">
              <span class="comparison-label">Expenses:</span>
              <span class="comparison-value negative">{{ formatCurrency(item.expenses) }}</span>
            </div>
            <div class="comparison-stat">
              <span class="comparison-label">Transfers:</span>
              <span class="comparison-value neutral">{{ formatCurrency(item.transfers) }}</span>
            </div>
            <div class="comparison-stat">
              <span class="comparison-label">Net:</span>
              <span class="comparison-value" :class="item.net >= 0 ? 'positive' : 'negative'">
                {{ formatCurrency(item.net) }}
              </span>
            </div>
          </div>
        </div>
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
    
    // Chart ref
    const mainChart = ref(null)
    
    const dateRange = ref({
      start: null,
      end: null
    })
    
    // Computed
    const hasData = computed(() => transactions.value.length > 0)
    
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
      
      return groupTransactionsByDay(transactions.value)
    })
    
    const topCategories = computed(() => {
      if (!transactions.value.length) return []
      
      const categoryTotals = {}
      let maxAmount = 0
      
      transactions.value
        .filter(t => t.transaction_type === 'expense')
        .forEach(t => {
          const category = t.csv_category || t.main_category || 'Uncategorized'
          const amount = Math.abs(parseFloat(t.amount))
          
          if (!categoryTotals[category]) {
            categoryTotals[category] = { amount: 0, count: 0 }
          }
          
          categoryTotals[category].amount += amount
          categoryTotals[category].count += 1
          maxAmount = Math.max(maxAmount, categoryTotals[category].amount)
        })
      
      return Object.entries(categoryTotals)
        .map(([name, data]) => ({
          name,
          amount: data.amount,
          count: data.count,
          percentage: maxAmount > 0 ? (data.amount / maxAmount) * 100 : 0
        }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 10)
    })
    
    const monthlyComparison = computed(() => {
      if (!transactions.value.length) return []
      
      const monthlyData = {}
      
      transactions.value.forEach(t => {
        const date = new Date(t.posted_at)
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        
        if (!monthlyData[monthKey]) {
          monthlyData[monthKey] = {
            period: monthKey,
            income: 0,
            expenses: 0,
            transfers: 0,
            net: 0
          }
        }
        
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          monthlyData[monthKey].income += amount
        } else if (t.transaction_type === 'expense') {
          monthlyData[monthKey].expenses += amount
        } else if (t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS') {
          monthlyData[monthKey].transfers += amount
        }
      })
      
      return Object.values(monthlyData)
        .map(month => ({
          ...month,
          net: month.income - month.expenses,
          periodName: new Date(month.period + '-01').toLocaleDateString('en-US', {
            month: 'short',
            year: 'numeric'
          })
        }))
        .sort((a, b) => b.period.localeCompare(a.period))
        .slice(0, 12)
    })
    
    const categoryColors = {
      // Food & Dining
      'Groceries': '#10b981',
      'Restaurants': '#ef4444',
      'Cafes & Coffee': '#f59e0b',
      'Sweets': '#ec4899',
      
      // Shopping
      'Clothing & Shoes': '#8b5cf6',
      'Electronics': '#3b82f6',
      'Household': '#06b6d4',
      'Accessories': '#d946ef',
      'Subscriptions': '#f97316',
      'Guilty Pleasure': '#db2777',
      
      // Housing & Utilities
      'Monthly Rent': '#0891b2',
      'Internet & Phone': '#6366f1',
      'Energy & Water': '#14b8a6',
      
      // Transport
      'Fuel': '#f59e0b',
      'Public Transport': '#84cc16',
      'Vehicle Registration & Tax': '#eab308',
      'Maintenance & Repairs': '#f97316',
      'Parking Fees': '#facc15',
      
      // Health
      'Pharmacy': '#22c55e',
      'Medical Services': '#10b981',
      'Dental Care': '#059669',
      'Gym & Fitness': '#84cc16',
      
      // Leisure & Culture
      'Music': '#a855f7',
      'Social Activities': '#ec4899',
      'Education': '#3b82f6',
      'Books & Media': '#6366f1',
      'Hobbies & Crafts': '#8b5cf6',
      
      // Family
      'Sports Activities': '#0ea5e9',
      "Child's Activities": '#06b6d4',
      'Toys & Games': '#14b8a6',
      
      // Insurance
      'Health Insurance': '#f43f5e',
      'Home Insurance': '#e11d48',
      'Vehicle Insurance': '#be123c',
      
      // Financial
      'Bureaucracy': '#64748b',
      'Investment Accounts': '#475569',
      'Withdrawal': '#334155',
      'Payment Provider': '#1e293b',
      'Bank Services': '#0f172a',
      
      // Transfers
      'Between Own Accounts': '#06b6d4',
      'Family Support': '#14b8a6',
      'Reserve Transfer': '#0891b2',
      'Savings Transfer': '#0e7490',
      'House Savings': '#155e75',
      
      // Default
      'Uncategorized': '#94a3b8'
    }
    
    const chartSeries = computed(() => {
      if (!timelineData.value.length) return []
      
      const series = []
      
      // Group expenses by category
      const expensesByCategory = {}
      transactions.value
        .filter(t => t.transaction_type === 'expense')
        .forEach(t => {
          const category = t.csv_subcategory || t.csv_category || 'Uncategorized'
          if (!expensesByCategory[category]) {
            expensesByCategory[category] = new Map()
          }
          
          const date = new Date(t.posted_at)
          const key = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
          const amount = Math.abs(parseFloat(t.amount))
          
          expensesByCategory[category].set(key, (expensesByCategory[category].get(key) || 0) + amount)
        })
      
      // Create expense series (positive values above zero line)
      Object.entries(expensesByCategory)
        .sort((a, b) => {
          const sumA = Array.from(a[1].values()).reduce((s, v) => s + v, 0)
          const sumB = Array.from(b[1].values()).reduce((s, v) => s + v, 0)
          return sumB - sumA
        })
        .slice(0, 15) // Top 15 categories
        .forEach(([category, dateMap]) => {
          series.push({
            name: category,
            type: 'line',
            data: timelineData.value.map(d => ({
              x: d.date,
              y: dateMap.get(d.date) || 0
            }))
          })
        })
      
      // Income series (negative values below zero line)
      series.push({
        name: 'Income',
        type: 'line',
        data: timelineData.value.map(d => ({
          x: d.date,
          y: -d.income // Negative to show below zero
        }))
      })
      
      // Running balance line (thicker, more prominent)
      let runningBalance = 0
      const balanceData = timelineData.value.map(d => {
        runningBalance += (d.income - d.expenses)
        return {
          x: d.date,
          y: runningBalance
        }
      })
      
      series.push({
        name: 'Balance',
        type: 'line',
        data: balanceData
      })
      
      return series
    })
    
    const chartOptions = computed(() => {
      const colors = []
      
      // Generate colors for expense categories
      chartSeries.value.forEach((serie, index) => {
        if (serie.name === 'Income') {
          colors.push('#22c55e')
        } else if (serie.name === 'Balance') {
          colors.push('#8b5cf6')
        } else {
          colors.push(categoryColors[serie.name] || `hsl(${index * 25}, 70%, 60%)`)
        }
      })
      
      return {
        chart: {
          id: 'timeline-main',
          type: 'line',
          height: 500,
          stacked: false,
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
          }
        },
        dataLabels: {
          enabled: false
        },
        stroke: {
          curve: 'smooth',
          width: chartSeries.value.map((serie, index) => {
            if (serie.name === 'Balance') return 3
            if (serie.name === 'Income') return 2
            return 1.5
          })
        },
        fill: {
          type: 'solid',
          opacity: chartSeries.value.map((serie) => {
            if (serie.name === 'Balance') return 1
            if (serie.name === 'Income') return 0.8
            return 0.6
          })
        },
        legend: {
          position: 'top',
          horizontalAlign: 'left',
          floating: false,
          offsetY: 0,
          markers: {
            width: 12,
            height: 12,
            radius: 2
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
          shared: true,
          intersect: false,
          x: {
            format: 'dd MMM yyyy'
          },
          y: {
            formatter: (val) => '€' + Math.abs(val).toFixed(2)
          }
        },
        colors: colors,
        annotations: {
          yaxis: [{
            y: 0,
            borderColor: '#374151',
            borderWidth: 2,
            opacity: 0.8,
            label: {
              text: 'Zero Line',
              style: {
                color: '#fff',
                background: '#374151'
              }
            }
          }]
        }
      }
    })
    
    // Methods
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
            transfers: 0
          })
        }
        
        const period = grouped.get(keyStr)
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          period.income += amount
        } else if (t.transaction_type === 'expense') {
          period.expenses += amount
        } else if (t.transaction_type === 'transfer' || t.main_category === 'TRANSFERS') {
          period.transfers += amount
        }
      })
      
      return Array.from(grouped.values())
        .sort((a, b) => a.date - b.date)
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
    
    // Initialize
    onMounted(async () => {
      if (authStore.user) {
        await categoryStore.loadCategories()
        await loadTransactions()
      }
    })
    
    // Watch for auth changes
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
      topCategories,
      monthlyComparison,
      chartSeries,
      chartOptions,
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
  margin-bottom: var(--gap-large);
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

/* Chart Wrapper */
.timeline-chart-wrapper {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  min-height: 500px;
}

.timeline-chart {
  width: 100%;
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

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--gap-standard);
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
  margin-bottom: var(--gap-standard);
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

/* Category Breakdown */
.category-breakdown-grid {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.category-breakdown-item {
  background: var(--color-background-light);
  padding: var(--gap-standard);
  border-radius: var(--radius);
}

.category-breakdown-header {
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
  margin-bottom: 0.5rem;
}

.category-breakdown-rank {
  width: 2rem;
  height: 2rem;
  background: var(--color-background-dark);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--text-small);
  flex-shrink: 0;
}

.category-breakdown-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-breakdown-name {
  font-weight: 500;
  font-size: var(--text-medium);
}

.category-breakdown-amount {
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--text-medium);
}

.category-breakdown-bar-container {
  height: 0.5rem;
  background: var(--color-background-dark);
  border-radius: 0.25rem;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.category-breakdown-bar {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #dc2626);
  border-radius: 0.25rem;
  transition: width 0.3s ease;
}

.category-breakdown-details {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

/* Period Comparison */
.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap-standard);
}

.comparison-item {
  background: var(--color-background-light);
  padding: var(--gap-standard);
  border-radius: var(--radius);
}

.comparison-period-name {
  font-weight: 600;
  margin-bottom: var(--gap-small);
  text-align: center;
  font-size: var(--text-medium);
}

.comparison-stats {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.comparison-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-small);
}

.comparison-label {
  color: var(--color-text-muted);
}

.comparison-value {
  font-weight: 600;
}

.comparison-value.positive {
  color: #22c55e;
}

.comparison-value.negative {
  color: #ef4444;
}

.comparison-value.neutral {
  color: #3b82f6;
}

/* Responsive Design */
@media (max-width: 64rem) {
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
}

@media (max-width: 48rem) {
  .timeline-container {
    padding: var(--gap-small);
  }
  
  .timeline-stats {
    grid-template-columns: 1fr;
  }
  
  .comparison-grid {
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
  
  .category-breakdown-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .category-breakdown-info {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>