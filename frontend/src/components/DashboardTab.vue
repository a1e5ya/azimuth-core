<template>
  <div class="tab-content">
    <!-- View Mode Toggle -->
    <div class="dashboard-header">
      <div class="view-toggle">
        <button 
          class="btn btn-small"
          :class="{ 'btn-active': viewMode === 'monthly' }"
          @click="viewMode = 'monthly'"
        >
          Monthly View
        </button>
        <button 
          class="btn btn-small"
          :class="{ 'btn-active': viewMode === 'yearly' }"
          @click="viewMode = 'yearly'"
        >
          Yearly View
        </button>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-4">
      <div class="container stat-card">
        <div class="stat-label">{{ viewMode === 'monthly' ? 'This Month' : 'This Year' }} Spending</div>
        <div class="stat-value negative">{{ formatCurrency(kpis.currentPeriodSpending) }}</div>
        <div class="stat-detail" :class="spendingTrendClass">
          {{ spendingTrendText }}
        </div>
      </div>

      <div class="container stat-card">
        <div class="stat-label">{{ viewMode === 'monthly' ? 'This Month' : 'This Year' }} Income</div>
        <div class="stat-value positive">{{ formatCurrency(kpis.currentPeriodIncome) }}</div>
        <div class="stat-detail">
          {{ kpis.incomeTransactionCount }} transactions
        </div>
      </div>

      <div class="container stat-card">
        <div class="stat-label">{{ viewMode === 'monthly' ? 'This Month' : 'This Year' }} Transfers</div>
        <div class="stat-value neutral">{{ formatCurrency(kpis.currentPeriodTransfers) }}</div>
        <div class="stat-detail">
          {{ kpis.transferTransactionCount }} transfers
        </div>
      </div>

      <div class="container stat-card">
        <div class="stat-label">Net Savings</div>
        <div class="stat-value" :class="kpis.netSavings >= 0 ? 'positive' : 'negative'">
          {{ formatCurrency(kpis.netSavings) }}
        </div>
        <div class="stat-detail">
          {{ kpis.savingsRate }}% savings rate
        </div>
      </div>
    </div>

    <!-- Spending Trend Chart -->
    <div class="container">
      <div class="chart-header">
        <h3>Spending Trend</h3>
      </div>
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading data...</div>
      </div>
      <div v-else-if="chartData.length === 0" class="empty-state">
        <div>No transaction data available</div>
        <div class="text-small">Import transactions to see your dashboard</div>
      </div>
      <div v-else class="chart-container">
        <apexchart
          type="area"
          height="300"
          :options="chartOptions"
          :series="chartSeries"
        />
      </div>
    </div>

    <!-- Two Column Layout -->
    <div class="grid grid-2">
      <!-- Top Spending Categories -->
      <div class="container">
        <h3 style="margin-bottom: var(--gap-standard);">Top Spending Categories ({{ viewMode === 'monthly' ? 'This Month' : 'This Year' }})</h3>
        <div v-if="topCategories.length === 0" class="empty-state-small">
          No category data
        </div>
        <div v-else class="category-list">
          <div v-for="(cat, index) in topCategories" :key="index" class="category-item">
            <div class="category-rank">{{ index + 1 }}</div>
            <div class="category-info">
              <div class="category-name">{{ cat.name }}</div>
              <div class="category-amount">{{ formatCurrency(cat.amount) }}</div>
            </div>
            <div class="category-bar-container">
              <div class="category-bar" :style="{ width: cat.percentage + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="container">
        <h3 style="margin-bottom: var(--gap-standard);">Recent Activity</h3>
        <div v-if="recentTransactions.length === 0" class="empty-state-small">
          No recent transactions
        </div>
        <div v-else class="transaction-list">
          <div v-for="tx in recentTransactions" :key="tx.id" class="transaction-item">
            <div class="transaction-date">{{ formatDate(tx.posted_at) }}</div>
            <div class="transaction-details">
              <div class="transaction-merchant">{{ tx.merchant || 'Unknown' }}</div>
              <div class="transaction-category">{{ tx.csv_category || tx.main_category || 'Uncategorized' }}</div>
            </div>
            <div class="transaction-amount" :class="getAmountClass(tx)">
              {{ formatCurrency(tx.amount) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Monthly Comparison -->
    <div class="container">
      <div class="chart-header">
        <h3>{{ viewMode === 'monthly' ? 'Monthly' : 'Yearly' }} Comparison</h3>
      </div>
      <div v-if="monthlyComparison.length === 0" class="empty-state-small">
        Not enough data for comparison
      </div>
      <div v-else class="comparison-grid">
        <div v-for="item in monthlyComparison" :key="item.period" class="comparison-item">
          <div class="comparison-month">{{ item.periodName }}</div>
          <div class="comparison-stats">
            <div class="comparison-stat">
              <span class="comparison-label">Spending:</span>
              <span class="comparison-value negative">{{ formatCurrency(item.spending) }}</span>
            </div>
            <div class="comparison-stat">
              <span class="comparison-label">Income:</span>
              <span class="comparison-value positive">{{ formatCurrency(item.income) }}</span>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'DashboardTab',
  components: {
    apexchart: VueApexCharts
  },
  setup() {
    const authStore = useAuthStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    
    const loading = ref(false)
    const transactions = ref([])
    const chartData = ref([])
    const viewMode = ref('monthly')
    const summary = ref(null)
    
    const kpis = computed(() => {
      if (transactions.value.length === 0) {
        return {
          currentPeriodSpending: 0,
          lastPeriodSpending: 0,
          currentPeriodIncome: 0,
          currentPeriodTransfers: 0,
          netSavings: 0,
          savingsRate: 0,
          totalTransactions: 0,
          currentPeriodTransactions: 0,
          incomeTransactionCount: 0,
          transferTransactionCount: 0
        }
      }
      
      const now = new Date()
      
      if (viewMode.value === 'monthly') {
        return calculateMonthlyKPIs(now)
      } else {
        return calculateYearlyKPIs(now)
      }
    })
    
    function calculateMonthlyKPIs(now) {
      const currentMonth = now.getMonth()
      const currentYear = now.getFullYear()
      
      const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1
      const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear
      
      let currentPeriodSpending = 0
      let lastPeriodSpending = 0
      let currentPeriodIncome = 0
      let currentPeriodTransfers = 0
      let currentPeriodTransactions = 0
      let incomeTransactionCount = 0
      let transferTransactionCount = 0
      
      transactions.value.forEach(tx => {
        const txDate = new Date(tx.posted_at)
        const txMonth = txDate.getMonth()
        const txYear = txDate.getFullYear()
        const amount = Math.abs(parseFloat(tx.amount))
        const txType = (tx.transaction_type || '').toLowerCase()
        const mainCategory = (tx.main_category || '').toLowerCase()
        
        if (txMonth === currentMonth && txYear === currentYear) {
          currentPeriodTransactions++
          
          // Check if it's a transfer by type or main_category
          if (txType === 'transfer' || txType === 'transfers' || mainCategory === 'transfers') {
            currentPeriodTransfers += amount
            transferTransactionCount++
          } else if (txType === 'expense') {
            currentPeriodSpending += amount
          } else if (txType === 'income') {
            currentPeriodIncome += amount
            incomeTransactionCount++
          }
        }
        
        if (txMonth === lastMonth && txYear === lastMonthYear) {
          if (txType === 'expense') {
            lastPeriodSpending += amount
          }
        }
      })
      
      const netSavings = currentPeriodIncome - currentPeriodSpending
      const savingsRate = currentPeriodIncome > 0 
        ? Math.round((netSavings / currentPeriodIncome) * 100) 
        : 0
      
      return {
        currentPeriodSpending,
        lastPeriodSpending,
        currentPeriodIncome,
        currentPeriodTransfers,
        netSavings,
        savingsRate,
        totalTransactions: transactions.value.length,
        currentPeriodTransactions,
        incomeTransactionCount,
        transferTransactionCount
      }
    }
    
    function calculateYearlyKPIs(now) {
      const currentYear = now.getFullYear()
      const lastYear = currentYear - 1
      
      let currentPeriodSpending = 0
      let lastPeriodSpending = 0
      let currentPeriodIncome = 0
      let currentPeriodTransfers = 0
      let currentPeriodTransactions = 0
      let incomeTransactionCount = 0
      let transferTransactionCount = 0
      
      transactions.value.forEach(tx => {
        const txDate = new Date(tx.posted_at)
        const txYear = txDate.getFullYear()
        const amount = Math.abs(parseFloat(tx.amount))
        const txType = (tx.transaction_type || '').toLowerCase()
        const mainCategory = (tx.main_category || '').toLowerCase()
        
        if (txYear === currentYear) {
          currentPeriodTransactions++
          
          // Check if it's a transfer by type or main_category
          if (txType === 'transfer' || txType === 'transfers' || mainCategory === 'transfers') {
            currentPeriodTransfers += amount
            transferTransactionCount++
          } else if (txType === 'expense') {
            currentPeriodSpending += amount
          } else if (txType === 'income') {
            currentPeriodIncome += amount
            incomeTransactionCount++
          }
        }
        
        if (txYear === lastYear) {
          if (txType === 'expense') {
            lastPeriodSpending += amount
          }
        }
      })
      
      const netSavings = currentPeriodIncome - currentPeriodSpending
      const savingsRate = currentPeriodIncome > 0 
        ? Math.round((netSavings / currentPeriodIncome) * 100) 
        : 0
      
      return {
        currentPeriodSpending,
        lastPeriodSpending,
        currentPeriodIncome,
        currentPeriodTransfers,
        netSavings,
        savingsRate,
        totalTransactions: transactions.value.length,
        currentPeriodTransactions,
        incomeTransactionCount,
        transferTransactionCount
      }
    }
    
    const spendingTrendClass = computed(() => {
      const diff = kpis.value.currentPeriodSpending - kpis.value.lastPeriodSpending
      if (diff > 0) return 'trend-up'
      if (diff < 0) return 'trend-down'
      return ''
    })
    
    const spendingTrendText = computed(() => {
      const diff = kpis.value.currentPeriodSpending - kpis.value.lastPeriodSpending
      const period = viewMode.value === 'monthly' ? 'last month' : 'last year'
      
      if (diff === 0) return `Same as ${period}`
      
      const percentage = kpis.value.lastPeriodSpending > 0
        ? Math.abs(Math.round((diff / kpis.value.lastPeriodSpending) * 100))
        : 0
      
      if (diff > 0) {
        return `↑ ${percentage}% vs ${period}`
      } else {
        return `↓ ${percentage}% vs ${period}`
      }
    })
    
    const topCategories = computed(() => {
      if (transactions.value.length === 0) return []
      
      const categoryTotals = {}
      let maxAmount = 0
      
      const now = new Date()
      const currentPeriod = viewMode.value === 'monthly' 
        ? { month: now.getMonth(), year: now.getFullYear() }
        : { year: now.getFullYear() }
      
      transactions.value.forEach(tx => {
        if (tx.transaction_type !== 'expense') return
        
        const txDate = new Date(tx.posted_at)
        const isCurrentPeriod = viewMode.value === 'monthly'
          ? txDate.getMonth() === currentPeriod.month && txDate.getFullYear() === currentPeriod.year
          : txDate.getFullYear() === currentPeriod.year
        
        if (!isCurrentPeriod) return
        
        const category = tx.csv_category || tx.main_category || 'Uncategorized'
        const amount = Math.abs(parseFloat(tx.amount))
        
        categoryTotals[category] = (categoryTotals[category] || 0) + amount
        maxAmount = Math.max(maxAmount, categoryTotals[category])
      })
      
      return Object.entries(categoryTotals)
        .map(([name, amount]) => ({
          name,
          amount,
          percentage: maxAmount > 0 ? (amount / maxAmount) * 100 : 0
        }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 5)
    })
    
    const recentTransactions = computed(() => {
      return [...transactions.value]
        .sort((a, b) => new Date(b.posted_at) - new Date(a.posted_at))
        .slice(0, 8)
    })
    
    const monthlyComparison = computed(() => {
      if (transactions.value.length === 0) return []
      
      const data = viewMode.value === 'monthly' ? getMonthlyData() : getYearlyData()
      
      return data
        .sort((a, b) => b.period.localeCompare(a.period))
        .slice(0, 6)
    })
    
    const yearlyChartData = computed(() => {
      if (transactions.value.length === 0) return []
      
      const yearlyData = {}
      
      transactions.value.forEach(tx => {
        const date = new Date(tx.posted_at)
        const yearKey = date.getFullYear().toString()
        
        if (!yearlyData[yearKey]) {
          yearlyData[yearKey] = {
            period: yearKey,
            spending: 0,
            income: 0
          }
        }
        
        const amount = Math.abs(parseFloat(tx.amount))
        
        if (tx.transaction_type === 'expense') {
          yearlyData[yearKey].spending += amount
        } else if (tx.transaction_type === 'income') {
          yearlyData[yearKey].income += amount
        }
      })
      
      return Object.values(yearlyData)
        .sort((a, b) => a.period.localeCompare(b.period))
    })
    
    function getMonthlyData() {
      const monthlyData = {}
      
      transactions.value.forEach(tx => {
        const date = new Date(tx.posted_at)
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        
        if (!monthlyData[monthKey]) {
          monthlyData[monthKey] = {
            period: monthKey,
            spending: 0,
            income: 0,
            net: 0
          }
        }
        
        const amount = Math.abs(parseFloat(tx.amount))
        
        if (tx.transaction_type === 'expense') {
          monthlyData[monthKey].spending += amount
        } else if (tx.transaction_type === 'income') {
          monthlyData[monthKey].income += amount
        }
      })
      
      return Object.values(monthlyData)
        .map(month => ({
          ...month,
          net: month.income - month.spending,
          periodName: new Date(month.period + '-01').toLocaleDateString('en-US', {
            month: 'short',
            year: 'numeric'
          })
        }))
    }
    
    function getYearlyData() {
      const yearlyData = {}
      
      transactions.value.forEach(tx => {
        const date = new Date(tx.posted_at)
        const yearKey = date.getFullYear().toString()
        
        if (!yearlyData[yearKey]) {
          yearlyData[yearKey] = {
            period: yearKey,
            spending: 0,
            income: 0,
            net: 0
          }
        }
        
        const amount = Math.abs(parseFloat(tx.amount))
        
        if (tx.transaction_type === 'expense') {
          yearlyData[yearKey].spending += amount
        } else if (tx.transaction_type === 'income') {
          yearlyData[yearKey].income += amount
        }
      })
      
      return Object.values(yearlyData)
        .map(year => ({
          ...year,
          net: year.income - year.spending,
          periodName: year.period
        }))
    }
    
    const chartSeries = computed(() => {
      if (chartData.value.length === 0) return []
      
      const data = viewMode.value === 'monthly' ? chartData.value : yearlyChartData.value
      
      return [
        {
          name: 'Spending',
          data: data.map(d => ({
            x: new Date(d.period + '-01').getTime(),
            y: d.spending
          }))
        },
        {
          name: 'Income',
          data: data.map(d => ({
            x: new Date(d.period + '-01').getTime(),
            y: d.income
          }))
        }
      ]
    })
    
    const chartOptions = computed(() => ({
      chart: {
        type: 'area',
        height: 300,
        toolbar: {
          show: false
        },
        zoom: {
          enabled: false
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
        type: 'gradient',
        gradient: {
          opacityFrom: 0.6,
          opacityTo: 0.1
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'left'
      },
      xaxis: {
        type: 'datetime',
        labels: {
          format: 'MMM yyyy'
        }
      },
      yaxis: {
        title: {
          text: 'Amount (€)'
        },
        labels: {
          formatter: (val) => '€' + Math.round(val).toLocaleString()
        }
      },
      tooltip: {
        x: {
          format: 'MMM yyyy'
        },
        y: {
          formatter: (val) => '€' + val.toFixed(2)
        }
      },
      colors: ['#ef4444', '#22c55e']
    }))
    
    async function loadTransactions() {
      if (!authStore.token) return
      
      loading.value = true
      
      try {
        // Fetch transactions in batches to avoid limit issues
        let allTransactions = []
        let page = 1
        const batchSize = 1000
        let hasMore = true
        
        while (hasMore && page <= 10) {
          const response = await fetch(`${API_BASE}/transactions/list?page=${page}&limit=${batchSize}`, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`
            }
          })
          
          if (!response.ok) {
            throw new Error('Failed to load transactions')
          }
          
          const data = await response.json()
          
          if (data.length === 0) {
            hasMore = false
            break
          }
          
          allTransactions = allTransactions.concat(data)
          
          if (data.length < batchSize) {
            hasMore = false
          }
          
          page++
        }
        
        transactions.value = allTransactions
        processChartData()
        
        console.log('Dashboard loaded:', allTransactions.length, 'transactions')
        
      } catch (error) {
        console.error('Failed to load transactions:', error)
        if (error.response?.status === 401) {
          await authStore.verifyToken()
        }
      } finally {
        loading.value = false
      }
    }
    
    async function loadSummary() {
      if (!authStore.token) return
      
      try {
        const response = await fetch(`${API_BASE}/transactions/summary`, {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        })
        
        if (!response.ok) throw new Error('Failed to load summary')
        
        const data = await response.json()
        summary.value = data
        
        console.log('Summary loaded:', data)
        
      } catch (error) {
        console.error('Failed to load summary:', error)
      }
    }
    
    function processChartData() {
      const monthlyData = {}
      
      transactions.value.forEach(tx => {
        const date = new Date(tx.posted_at)
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        
        if (!monthlyData[monthKey]) {
          monthlyData[monthKey] = {
            period: monthKey,
            spending: 0,
            income: 0
          }
        }
        
        const amount = Math.abs(parseFloat(tx.amount))
        
        if (tx.transaction_type === 'expense') {
          monthlyData[monthKey].spending += amount
        } else if (tx.transaction_type === 'income') {
          monthlyData[monthKey].income += amount
        }
      })
      
      chartData.value = Object.values(monthlyData)
        .sort((a, b) => a.period.localeCompare(b.period))
        .slice(-6)
    }
    
    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }
    
    function formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-EU', {
        day: '2-digit',
        month: 'short'
      })
    }
    
    function getAmountClass(transaction) {
      if (transaction.transaction_type === 'income') {
        return 'positive'
      } else if (transaction.transaction_type === 'expense') {
        return 'negative'
      }
      return ''
    }
    
    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadSummary()
        loadTransactions()
      }
    })
    
    watch(() => viewMode.value, () => {
      if (transactions.value.length > 0) {
        processChartData()
      }
    })
    
    onMounted(() => {
      if (authStore.user) {
        loadSummary()
        loadTransactions()
      }
    })
    
    return {
      loading,
      kpis,
      spendingTrendClass,
      spendingTrendText,
      topCategories,
      recentTransactions,
      monthlyComparison,
      chartData,
      chartSeries,
      chartOptions,
      viewMode,
      formatCurrency,
      formatDate,
      getAmountClass,
      loadTransactions
    }
  }
}
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: var(--gap-large);
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  margin-bottom: var(--gap-small);
}

.stat-value {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: var(--gap-small);
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

.stat-detail.trend-up {
  color: #ef4444;
}

.stat-detail.trend-down {
  color: #22c55e;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--gap-large);
  color: var(--color-text-light);
}

.empty-state-small {
  text-align: center;
  padding: var(--gap-standard);
  color: var(--color-text-muted);
  font-size: var(--text-small);
}

.loading-spinner {
  font-size: var(--text-large);
  animation: spin 1s linear infinite;
  margin-bottom: var(--gap-standard);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chart-container {
  padding: var(--gap-small);
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.category-item {
  display: grid;
  grid-template-columns: 2rem 1fr;
  gap: var(--gap-small);
  align-items: center;
}

.category-rank {
  width: 2rem;
  height: 2rem;
  background: var(--color-background-dark);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--text-small);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.category-name {
  font-weight: 500;
  font-size: var(--text-small);
}

.category-amount {
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--text-small);
}

.category-bar-container {
  grid-column: 2;
  height: 0.5rem;
  background: var(--color-background-dark);
  border-radius: 0.25rem;
  overflow: hidden;
}

.category-bar {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #dc2626);
  border-radius: 0.25rem;
  transition: width 0.3s ease;
}

.transaction-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.transaction-item {
  display: grid;
  grid-template-columns: 4rem 1fr auto;
  gap: var(--gap-small);
  align-items: center;
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.transaction-date {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  font-weight: 500;
}

.transaction-details {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.transaction-merchant {
  font-size: var(--text-small);
  font-weight: 500;
}

.transaction-category {
  font-size: 0.6875rem;
  color: var(--color-text-muted);
}

.transaction-amount {
  font-weight: 600;
  font-size: var(--text-small);
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: var(--gap-standard);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  flex-wrap: wrap;
  gap: var(--gap-small);
}

.chart-header h3 {
  margin: 0;
}

.view-toggle {
  display: flex;
  gap: 0.25rem;
}

.comparison-item {
  background: var(--color-background-light);
  padding: var(--gap-standard);
  border-radius: var(--radius);
}

.comparison-month {
  font-weight: 600;
  margin-bottom: var(--gap-small);
  text-align: center;
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

.dashboard-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--gap-standard);
}

@media (max-width: 64rem) {
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-header {
    justify-content: center;
  }
}

@media (max-width: 48rem) {
  .grid-4,
  .grid-2 {
    grid-template-columns: 1fr;
  }
  
  .comparison-grid {
    grid-template-columns: 1fr;
  }
}
</style>