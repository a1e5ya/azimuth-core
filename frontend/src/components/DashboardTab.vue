<template>
  <div class="tab-content">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">⟳</div>
      <div>Loading data...</div>
    </div>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Stats Overview with Date Picker -->
      <div class="stats-with-controls">
        <DashboardStatCards
          :filtered-transactions="filteredTransactions"
          :get-type-color="getTypeColor"
        />
        
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
        @import-complete="handleImportComplete"
      />

      <DashboardAccountsManagement
        :filtered-transactions="filteredTransactions"
        @open-import="showImportModal = true"
      />
    </template>

    <!-- Import Modal -->
    <TransactionImportModal
      :show="showImportModal"
      @close="showImportModal = false"
      @import-complete="handleImportComplete"
    />
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import DashboardDateRangePicker from './DashboardDateRangePicker.vue'
import DashboardStatCards from './DashboardStatCards.vue'
import DashboardIncomeExpensesChart from './DashboardIncomeExpensesChart.vue'
import DashboardAccountsManagement from './DashboardAccountsManagement.vue'
import TransactionImportModal from './TransactionImportModal.vue'

export default {
  name: 'DashboardTab',
  components: {
    DashboardDateRangePicker,
    DashboardStatCards,
    DashboardIncomeExpensesChart,
    DashboardAccountsManagement,
    TransactionImportModal
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    
    const loading = ref(false)
    const transactions = ref([])
    const showImportModal = ref(false)
    const dateRange = ref({
      startDate: new Date(),
      endDate: new Date()
    })

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

    const filteredTransactions = computed(() => {
      if (transactions.value.length === 0) return []

      const start = new Date(dateRange.value.startDate)
      const end = new Date(dateRange.value.endDate)
      
      start.setHours(0, 0, 0, 0)
      end.setHours(23, 59, 59, 999)

      return transactions.value.filter(tx => {
        const txDate = new Date(tx.posted_at)
        return txDate >= start && txDate <= end
      })
    })

    const filteredTransactionsWithContext = computed(() => {
      if (transactions.value.length === 0) return []

      const start = new Date(dateRange.value.startDate)
      const end = new Date(dateRange.value.endDate)
      
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

    async function handleImportComplete(result) {
      if (result.success) {
        await loadTransactions()
      }
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
      showImportModal,
      handleDateRangeChange,
      handleImportComplete,
      getTypeColor
    }
  }
}
</script>

<style scoped>
.stats-with-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--gap-large);
  margin-bottom: var(--gap-standard);
}
</style>