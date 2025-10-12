<template>
  <div class="tab-content">
<div class="stats-overview">

    <!-- KPI Cards - Updated styling with background colors -->
    <div class="grid grid-4">
      <div 
        class="container stat-card"
        :style="{ backgroundColor: hexToRgba(getTypeColor('expenses'), 0.1) }"
      >
        <div class="stat-label">{{ viewMode === 'monthly' ? 'This Month' : 'This Year' }} Spending</div>
        <div class="stat-value">{{ formatCurrency(kpis.currentPeriodSpending) }}</div>
        <div class="stat-detail" :class="spendingTrendClass">
          {{ spendingTrendText }}
        </div>
      </div>

      <div 
        class="container stat-card"
        :style="{ backgroundColor: hexToRgba(getTypeColor('income'), 0.1) }"
      >
        <div class="stat-label">{{ viewMode === 'monthly' ? 'This Month' : 'This Year' }} Income</div>
        <div class="stat-value">{{ formatCurrency(kpis.currentPeriodIncome) }}</div>
        <div class="stat-detail">
          {{ kpis.incomeTransactionCount }} transactions
        </div>
      </div>

      <div 
        class="container stat-card"
        :style="{ backgroundColor: hexToRgba(getTypeColor('transfers'), 0.1) }"
      >
        <div class="stat-label">{{ viewMode === 'monthly' ? 'This Month' : 'This Year' }} Transfers</div>
        <div class="stat-value">{{ formatCurrency(kpis.currentPeriodTransfers) }}</div>
        <div class="stat-detail">
          {{ kpis.transferTransactionCount }} transfers
        </div>
      </div>

      <div 
        class="container stat-card"
        :style="{ backgroundColor: kpis.netSavings >= 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)' }"
      >
        <div class="stat-label">Net Savings</div>
        <div class="stat-value">
          {{ formatCurrency(kpis.netSavings) }}
        </div>
        <div class="stat-detail">
          {{ kpis.savingsRate }}% savings rate
        </div>
      </div>
    </div>

        <!-- View Mode Toggle -->
<div class="dashboard-header">
      <div class="view-toggle">
        <button 
          class="btn btn-small"
          :class="{ 'btn-active': viewMode === 'monthly' }"
          @click="viewMode = 'monthly'"
        >
          Monthly 
        </button>
        <button 
          class="btn btn-small"
          :class="{ 'btn-active': viewMode === 'yearly' }"
          @click="viewMode = 'yearly'"
        >
          Yearly 
        </button>
      </div>
      </div>
  </div>

    <!-- Income vs Expenses Trend Chart - Timeline Style -->
    <div class="container">
      <div class="chart-header">
        <h3>Income vs Expenses Trend</h3>
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
          :options="timelineChartOptions"
          :series="timelineChartSeries"
        />
      </div>

    </div>

    <!-- Two Column Layout: Top Spending Categories + Accounts Overview -->
    <div class="grid grid-2">
      <!-- Top Spending Categories - No Transfers -->
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

      <!-- Accounts Overview by Owner and Type -->
      <div class="container">
        <h3 style="margin-bottom: var(--gap-standard);">Accounts Overview ({{ viewMode === 'monthly' ? 'This Month' : 'This Year' }})</h3>
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <div>Loading data...</div>
        </div>
        <div v-else-if="accountStats.length === 0" class="empty-state-small">
          No account data
        </div>
        <div v-else class="accounts-list">
          <div 
            v-for="account in accountStats" 
            :key="account.key" 
            class="account-card-compact"
          >
            <div class="account-header-compact">
              <div class="account-title-compact">
                <AppIcon name="credit-card" size="small" />
                <div>
                  <div class="account-owner-compact">{{ account.owner || 'Unknown' }}</div>
                  <div class="account-type-compact">{{ account.accountType || 'Unknown Type' }}</div>
                </div>
              </div>
            </div>
            <div class="account-stats-compact">
              <div class="account-stat-compact">
                <span class="account-stat-label-compact">Income:</span>
                <span class="account-stat-value-compact positive">{{ formatCurrency(account.income) }}</span>
              </div>
              <div class="account-stat-compact">
                <span class="account-stat-label-compact">Expenses:</span>
                <span class="account-stat-value-compact negative">{{ formatCurrency(account.expenses) }}</span>
              </div>
              <div class="account-stat-compact">
                <span class="account-stat-label-compact">Transfers:</span>
                <span class="account-stat-value-compact neutral">{{ formatCurrency(account.transfers) }}</span>
              </div>
              <div class="account-stat-compact account-stat-total-compact">
                <span class="account-stat-label-compact">Net:</span>
                <span 
                  class="account-stat-value-compact" 
                  :class="account.net >= 0 ? 'positive' : 'negative'"
                >
                  {{ formatCurrency(account.net) }}
                </span>
              </div>
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
import AppIcon from './AppIcon.vue'

export default {
  name: 'DashboardTab',
  components: {
    apexchart: VueApexCharts,
    AppIcon
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
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
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        
        if (txMonth === currentMonth && txYear === currentYear) {
          currentPeriodTransactions++
          
          if (mainCategory === 'TRANSFERS') {
            currentPeriodTransfers += amount
            transferTransactionCount++
          } else if (mainCategory === 'EXPENSES') {
            currentPeriodSpending += amount
          } else if (mainCategory === 'INCOME') {
            currentPeriodIncome += amount
            incomeTransactionCount++
          }
        }
        
        if (txMonth === lastMonth && txYear === lastMonthYear) {
          if (mainCategory === 'EXPENSES') {
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
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        
        if (txYear === currentYear) {
          currentPeriodTransactions++
          
          if (mainCategory === 'TRANSFERS') {
            currentPeriodTransfers += amount
            transferTransactionCount++
          } else if (mainCategory === 'EXPENSES') {
            currentPeriodSpending += amount
          } else if (mainCategory === 'INCOME') {
            currentPeriodIncome += amount
            incomeTransactionCount++
          }
        }
        
        if (txYear === lastYear) {
          if (mainCategory === 'EXPENSES') {
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
    
    const accountStats = computed(() => {
      if (transactions.value.length === 0) return []
      
      const accountMap = new Map()
      const now = new Date()
      const currentPeriod = viewMode.value === 'monthly' 
        ? { month: now.getMonth(), year: now.getFullYear() }
        : { year: now.getFullYear() }
      
      transactions.value.forEach(tx => {
        const txDate = new Date(tx.posted_at)
        const isCurrentPeriod = viewMode.value === 'monthly'
          ? txDate.getMonth() === currentPeriod.month && txDate.getFullYear() === currentPeriod.year
          : txDate.getFullYear() === currentPeriod.year
        
        if (!isCurrentPeriod) return
        
        // Try multiple field names for account type
        const owner = tx.owner || 'Unknown'
        const accountType = tx.csv_account_type || tx.account_type || tx.Account_Type || 'Unknown Type'
        const key = `${owner}|${accountType}`
        
        if (!accountMap.has(key)) {
          accountMap.set(key, {
            key,
            owner,
            accountType,
            income: 0,
            expenses: 0,
            transfers: 0,
            net: 0
          })
        }
        
        const account = accountMap.get(key)
        const amount = Math.abs(parseFloat(tx.amount))
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        
        if (mainCategory === 'INCOME') {
          account.income += amount
        } else if (mainCategory === 'EXPENSES') {
          account.expenses += amount
        } else if (mainCategory === 'TRANSFERS') {
          account.transfers += amount
        }
      })
      
      const accounts = Array.from(accountMap.values())
      accounts.forEach(account => {
        account.net = account.income - account.expenses
      })
      
      return accounts.sort((a, b) => b.net - a.net)
    })
    
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
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        // Only count EXPENSES, exclude TRANSFERS
        if (mainCategory !== 'EXPENSES') return
        
        const txDate = new Date(tx.posted_at)
        const isCurrentPeriod = viewMode.value === 'monthly'
          ? txDate.getMonth() === currentPeriod.month && txDate.getFullYear() === currentPeriod.year
          : txDate.getFullYear() === currentPeriod.year
        
        if (!isCurrentPeriod) return
        
        const category = tx.csv_category || 'Uncategorized'
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
    
    const timelineChartSeries = computed(() => {
      if (chartData.value.length === 0) return []
      
      const data = viewMode.value === 'monthly' ? chartData.value : yearlyChartData.value
      
      return [
        {
          name: 'Income',
          data: data.map(d => ({
            x: new Date(d.period + '-01').getTime(),
            y: d.income
          }))
        },
        {
          name: 'Expenses',
          data: data.map(d => ({
            x: new Date(d.period + '-01').getTime(),
            y: d.spending
          }))
        }
      ]
    })
    
    const timelineChartOptions = computed(() => ({
      chart: {
        type: 'area',
        height: 300,
        stacked: false,
        toolbar: {
          show: false
        },
        zoom: {
          enabled: false
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
        width: 2
      },
      fill: {
        type: 'gradient',
        gradient: {
          opacityFrom: 0.4,
          opacityTo: 0.1,
          stops: [0, 90, 100]
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'left',
        fontSize: '14px',
        fontWeight: 500
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
          format: 'MMM yyyy',
          style: {
            colors: '#6b7280',
            fontSize: '12px'
          }
        },
        axisBorder: {
          show: true,
          color: '#e5e7eb'
        },
        axisTicks: {
          show: true,
          color: '#e5e7eb'
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
          formatter: (val) => '€' + Math.round(val).toLocaleString(),
          style: {
            colors: '#6b7280',
            fontSize: '12px'
          }
        }
      },
      tooltip: {
        shared: true,
        intersect: false,
        x: {
          format: 'MMM yyyy'
        },
        y: {
          formatter: (val) => '€' + val.toFixed(2)
        },
        theme: 'light'
      },
      colors: ['#22c55e', '#ef4444'],
      markers: {
        size: 0,
        hover: {
          size: 5
        }
      }
    }))
    
    const yearlyChartData = computed(() => {
      if (transactions.value.length === 0) return []
      
      const yearlyData = {}
      
      transactions.value.forEach(tx => {
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        // Exclude TRANSFERS from chart
        if (mainCategory === 'TRANSFERS') return
        
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
        
        if (mainCategory === 'EXPENSES') {
          yearlyData[yearKey].spending += amount
        } else if (mainCategory === 'INCOME') {
          yearlyData[yearKey].income += amount
        }
      })
      
      return Object.values(yearlyData)
        .sort((a, b) => a.period.localeCompare(b.period))
    })
    
    async function loadTransactions() {
      if (!authStore.token) return
      
      loading.value = true
      
      try {
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
        
        // Debug: Check first few transactions
        if (allTransactions.length > 0) {
          console.log('Sample transaction fields:', allTransactions[0])
        }
        
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
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        // Exclude TRANSFERS from chart
        if (mainCategory === 'TRANSFERS') return
        
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
        
        if (mainCategory === 'EXPENSES') {
          monthlyData[monthKey].spending += amount
        } else if (mainCategory === 'INCOME') {
          monthlyData[monthKey].income += amount
        }
      })
      
      chartData.value = Object.values(monthlyData)
        .sort((a, b) => a.period.localeCompare(b.period))
        .slice(-12) // Show last 12 months
    }
    
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
    
    function hexToRgba(hex, alpha) {
      if (!hex) return 'transparent'
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
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
      const mainCategory = (transaction.main_category || '').toUpperCase().trim()
      if (mainCategory === 'INCOME') {
        return 'positive'
      } else if (mainCategory === 'EXPENSES') {
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
    
    onMounted(async () => {
      if (authStore.user) {
        await categoryStore.loadCategories()
        await loadSummary()
        await loadTransactions()
      }
    })
    
    return {
      loading,
      kpis,
      spendingTrendClass,
      spendingTrendText,
      topCategories,
      accountStats,
      chartData,
      timelineChartSeries,
      timelineChartOptions,
      viewMode,
      formatCurrency,
      formatDate,
      getAmountClass,
      getTypeColor,
      hexToRgba,
      loadTransactions
    }
  }
}
</script>
<style scoped>

.stats-overview {
  display: flex;
  justify-content: space-between;
    align-items: flex-start;
}

.stat-card {
  text-align: center;
  padding: var(--gap-large);
  border-radius: var(--radius);
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
  color: var(--color-text);
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

/* Accounts List - Compact for Grid */
.accounts-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.account-card-compact {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-small);
}

.account-header-compact {
  margin-bottom: var(--gap-small);
  padding-bottom: var(--gap-small);
  border-bottom: 1px solid var(--color-background-dark);
}

.account-title-compact {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.account-owner-compact {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.account-type-compact {
  font-size: 0.6875rem;
  color: var(--color-text-muted);
}

.account-stats-compact {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.account-stat-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.75rem;
}

.account-stat-total-compact {
  padding-top: 0.375rem;
  border-top: 1px solid var(--color-background-dark);
  font-weight: 600;
  margin-top: 0.25rem;
}

.account-stat-label-compact {
  color: var(--color-text-light);
}

.account-stat-value-compact {
  font-weight: 600;
  font-size: 0.75rem;
}

.account-stat-value-compact.positive {
  color: #22c55e;
}

.account-stat-value-compact.negative {
  color: #ef4444;
}

.account-stat-value-compact.neutral {
  color: #3b82f6;
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

.dashboard-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--gap-standard);
}

/* ApexCharts customization */
:deep(.apexcharts-tooltip) {
  background: var(--color-background-light) !important;
  border: 1px solid var(--color-background-dark) !important;
  box-shadow: var(--shadow) !important;
}

:deep(.apexcharts-tooltip-title) {
  background: var(--color-background-dark) !important;
  border-bottom: 1px solid var(--color-background-dark) !important;
  color: var(--color-text) !important;
  font-weight: 600 !important;
}

:deep(.apexcharts-tooltip-text-y-label) {
  color: var(--color-text-light) !important;
}

:deep(.apexcharts-tooltip-text-y-value) {
  color: var(--color-text) !important;
  font-weight: 600 !important;
}

:deep(.apexcharts-legend-text) {
  color: var(--color-text) !important;
}

:deep(.apexcharts-xaxis-label) {
  fill: #6b7280 !important;
}

:deep(.apexcharts-yaxis-label) {
  fill: #6b7280 !important;
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
  
  .stat-card {
    padding: var(--gap-standard);
  }
  
  .account-card-compact {
    padding: var(--gap-small);
  }
}

@media (max-width: 30rem) {
  .stat-card {
    padding: var(--gap-small);
  }
  
  .stat-label {
    font-size: 0.6875rem;
  }
  
  .stat-value {
    font-size: var(--text-medium);
  }
  
  .account-owner-compact {
    font-size: 0.6875rem;
  }
  
  .account-type-compact {
    font-size: 0.625rem;
  }
  
  .account-stat-compact {
    font-size: 0.6875rem;
  }
}
</style>