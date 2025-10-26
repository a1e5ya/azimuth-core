<template>
  <div class="tab-content">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">⟳</div>
      <div>Loading data...</div>
    </div>

    <!-- Empty State -->
    <div v-else-if="transactions.length === 0" class="empty-state">
      <div>No transaction data available</div>
      <div class="text-small">Import transactions to see your dashboard</div>
    </div>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Stats Overview with Date Picker -->
      <div class="stats-with-controls">
        <!-- Stat Cards -->
        <DashboardStatCards
          :filtered-transactions="filteredTransactions"
          :get-type-color="getTypeColor"
        />
        
        <!-- Date Range Picker -->
        <DashboardDateRangePicker
          :date-range="dateRange"
          :min-available-date="minAvailableDate"
          :max-available-date="maxAvailableDate"
          @update:date-range="handleDateRangeChange"
        />
      </div>

      <!-- Income vs Expenses Chart -->
      <DashboardIncomeExpensesChart
        :filtered-transactions="filteredTransactionsWithContext"
        :get-type-color="getTypeColor"
      />

      <!-- Two Column Layout -->
      <div class="grid grid-2">
        <!-- Top Categories -->
        <DashboardTopCategories
          :filtered-transactions="filteredTransactions"
        />

        <!-- Accounts Overview -->
        <DashboardAccountsOverview
          :filtered-transactions="filteredTransactions"
        />
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import DashboardDateRangePicker from './DashboardDateRangePicker.vue'
import DashboardStatCards from './DashboardStatCards.vue'
import DashboardIncomeExpensesChart from './DashboardIncomeExpensesChart.vue'
import DashboardTopCategories from './DashboardTopCategories.vue'
import DashboardAccountsOverview from './DashboardAccountsOverview.vue'

export default {
  name: 'DashboardTab',
  components: {
    DashboardDateRangePicker,
    DashboardStatCards,
    DashboardIncomeExpensesChart,
    DashboardTopCategories,
    DashboardAccountsOverview
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    
    const loading = ref(false)
    const transactions = ref([])
    const dateRange = ref({
      startDate: new Date(),
      endDate: new Date()
    })

    // Calculate available date range from transactions
    const minAvailableDate = computed(() => {
      if (transactions.value.length === 0) return null
      const dates = transactions.value.map(t => new Date(t.posted_at))
      return new Date(Math.min(...dates))
    })

    const maxAvailableDate = computed(() => {
      if (transactions.value.length === 0) return null
      const dates = transactions.value.map(t => new Date(t.posted_at))
      return new Date(Math.max(...dates))
    })

    // Filter transactions by date range
    const filteredTransactions = computed(() => {
      if (transactions.value.length === 0) return []

      const start = new Date(dateRange.value.startDate)
      const end = new Date(dateRange.value.endDate)
      
      // Set time to start/end of day for accurate filtering
      start.setHours(0, 0, 0, 0)
      end.setHours(23, 59, 59, 999)

      return transactions.value.filter(tx => {
        const txDate = new Date(tx.posted_at)
        return txDate >= start && txDate <= end
      })
    })

    // Filtered transactions with adjacent months for chart continuity
    const filteredTransactionsWithContext = computed(() => {
      if (transactions.value.length === 0) return []

      const start = new Date(dateRange.value.startDate)
      const end = new Date(dateRange.value.endDate)
      
      // Include previous and next month for chart line continuity
      const expandedStart = new Date(start)
      expandedStart.setMonth(expandedStart.getMonth() - 1)
      expandedStart.setHours(0, 0, 0, 0)
      
      const expandedEnd = new Date(end)
      expandedEnd.setMonth(expandedEnd.getMonth() + 1)
      expandedEnd.setHours(23, 59, 59, 999)

      return transactions.value.filter(tx => {
        const txDate = new Date(tx.posted_at)
        return txDate >= expandedStart && txDate <= expandedEnd
      })
    })

    function handleDateRangeChange(newRange) {
      dateRange.value = newRange
    }

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

        // Set initial date range to all time
        if (allTransactions.length > 0) {
          const dates = allTransactions.map(t => new Date(t.posted_at))
          dateRange.value = {
            startDate: new Date(Math.min(...dates)),
            endDate: new Date(Math.max(...dates))
          }
        }
        
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

    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadTransactions()
      }
    })
    
    onMounted(async () => {
      if (authStore.user) {
        await categoryStore.loadCategories()
        await loadTransactions()
      }
    })
    
    return {
      loading,
      transactions,
      dateRange,
      minAvailableDate,
      maxAvailableDate,
      filteredTransactions,
      filteredTransactionsWithContext,
      handleDateRangeChange,
      getTypeColor
    }
  }
}
</script>

<style scoped>
.loading-state,
.empty-state {
  text-align: center;
  padding: var(--gap-large);
  color: var(--color-text-light);
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

.stats-with-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--gap-large);
  margin-bottom: var(--gap-standard);
}

@media (max-width: 64rem) {
  .stats-with-controls {
    flex-direction: column;
  }
}
</style>