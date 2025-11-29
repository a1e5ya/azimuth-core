<!--
  Dashboard Tab - Main financial overview
  
  Orchestrates KPI cards, trend chart, date picker, and account management.
  Loads transactions with pagination (1000/page, 10K max), filters by date range.
-->
<template>
  <div class="tab-content">
    <!-- Loading state during transaction fetch -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">⟳</div>
      <div>Loading data...</div>
    </div>

    <!-- Main dashboard layout: stats row, chart, accounts -->
    <template v-else>
      <!-- Stats cards + date picker horizontal layout -->
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

      <!-- Trend chart with ±1 month context for smooth edges -->
      <DashboardIncomeExpensesChart
        :filtered-transactions="filteredTransactionsWithContext"
        :get-type-color="getTypeColor"
        @import-complete="handleImportComplete"
      />

      <!-- Account management with real-time stats -->
      <DashboardAccountsManagement
        :filtered-transactions="filteredTransactions"
        @import-success="handleImportComplete"
        @add-chat-message="addChatMessage"
        @open-import="showImportModal = true"
      />
    </template>

    <!-- General import modal (currently unused) -->
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
  emits: ['add-chat-message'],
  setup(props, { emit }) {
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

    /**
     * Earliest transaction date
     * Used by date picker for minimum boundary constraint
     */
    const minAvailableDate = computed(() => {
      if (transactions.value.length === 0) return null
      const dates = transactions.value.map(t => new Date(t.posted_at))
      return new Date(Math.min(...dates))
    })

    /**
     * Latest transaction date  
     * Used by date picker for maximum boundary constraint
     */
    const maxAvailableDate = computed(() => {
      if (transactions.value.length === 0) return null
      const dates = transactions.value.map(t => new Date(t.posted_at))
      return new Date(Math.max(...dates))
    })

    /**
     * Filter transactions to exact date range
     * Used by KPI cards and account statistics for accurate calculations.
     * Sets time to start of day (00:00:00) and end of day (23:59:59.999)
     */
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

    /**
     * Filter transactions with ±1 month context
     * Used by chart to provide smooth edges when viewing specific periods.
     * Prevents abrupt chart start/end, shows trend leading into/out of range.
     */
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

    /**
     * Forward chat message to parent
     * Pass-through for messages from child components (mainly accounts management)
     */
    function addChatMessage(data) {
      emit('add-chat-message', data)
    }

    /**
     * Update date range from picker
     * Triggers re-computation of filtered transaction lists
     */
    function handleDateRangeChange(newRange) {
      dateRange.value = newRange
    }

    /**
     * Reload all transactions after import
     * Called by chart drop zone, account imports, and import modal
     */
    async function handleImportComplete() {
      await loadTransactions()
    }

    /**
     * Load all transactions with pagination
     * 
     * Fetches in batches of 1000, up to 10 pages (10K transactions max).
     * Stops when: empty response OR partial batch (<1000 records).
     * 
     * After loading, sets date range to min/max of dataset for initial view.
     * Handles 401 errors by triggering token verification.
     */
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

        // Set range to full dataset
        if (allTransactions.length > 0) {
          const dates = allTransactions.map(t => new Date(t.posted_at))
          dateRange.value = {
            startDate: new Date(Math.min(...dates)),
            endDate: new Date(Math.max(...dates))
          }
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

    /**
     * Get color for transaction type
     * 
     * Returns color for income, expenses, or transfers.
     * First tries category store (custom colors), then falls back to defaults.
     * 
     * Default colors:
     * - income: #00C9A0 (teal)
     * - expenses: #F17D99 (pink)  
     * - transfers: #F0C46C (orange)
     * - unknown: #94a3b8 (gray)
     */
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

    /** Load transactions on user login */
    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadTransactions()
      }
    })
    
    /** Initial load: categories then transactions */
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
      showImportModal,
      minAvailableDate,
      maxAvailableDate,
      filteredTransactions,
      filteredTransactionsWithContext,
      handleDateRangeChange,
      handleImportComplete,
      addChatMessage,
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