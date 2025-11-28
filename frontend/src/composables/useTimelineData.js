/**
 * Timeline Data Composable - Transaction Data Management
 * 
 * Manages timeline visualization data:
 * - Transaction loading from API (paginated batches)
 * - Grouping by period (year/quarter/month)
 * - Breakdown filtering (all/owner/account)
 * - Zoom level management (-1: year, 0: quarter, 1: month)
 * - Date range calculation
 * 
 * Breakdown Modes:
 * - 'all': Show all transactions (default)
 * - 'owner': Filter by selected owner(s)
 * - 'account': Filter by selected account(s)
 * 
 * Zoom Levels:
 * - Level -1: Year grouping (least detail)
 * - Level 0: Quarter grouping (medium detail)
 * - Level 1: Month grouping (most detail)
 * 
 * Data Loading:
 * - Fetches transactions in 1000-record batches
 * - Continues until all data loaded or 10 pages reached
 * - Automatically calculates date range from data
 * - Initializes breakdown selections with first available options
 * 
 * Integration:
 * - Uses groupTransactionsByPeriod from timelineHelpers
 * - Uses getGroupingByZoomLevel from timelineHelpers
 * - Requires auth token for API calls
 */

import { ref, computed } from 'vue'
import { groupTransactionsByPeriod, getGroupingByZoomLevel } from '@/utils/timelineHelpers'

export function useTimelineData() {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  
  // ========================================
  // STATE
  // ========================================
  
  /** @type {Ref<boolean>} Loading state for async operations */
  const loading = ref(false)
  
  /** @type {Ref<Array>} All loaded transactions */
  const transactions = ref([])
  
  /** @type {Ref<number>} Current zoom level (-1: year, 0: quarter, 1: month) */
  const currentZoomLevel = ref(0) // Start at quarter view
  
  // Breakdown state
  /** @type {Ref<string>} Breakdown mode: 'all', 'owner', or 'account' */
  const breakdownMode = ref('all')
  
  /** @type {Ref<Array<string>>} Selected owner names for filtering */
  const selectedOwners = ref([])
  
  /** @type {Ref<Array<string>>} Selected account keys (owner_accountType) for filtering */
  const selectedAccounts = ref([])
  
  /** @type {Ref<Object>} Date range of all transactions */
  const dateRange = ref({
    start: null,
    end: null
  })
  
  // ========================================
  // COMPUTED PROPERTIES
  // ========================================
  
  /**
   * Check if timeline has any data
   * @type {ComputedRef<boolean>}
   */
  const hasData = computed(() => transactions.value.length > 0)
  
  /**
   * Get current grouping type based on zoom level
   * @type {ComputedRef<string>} 'year', 'quarter', or 'month'
   */
  const currentGrouping = computed(() => {
    return getGroupingByZoomLevel(currentZoomLevel.value)
  })
  
  /**
   * Filter transactions based on breakdown mode
   * 
   * Filtering logic:
   * - 'all': No filtering, return all transactions
   * - 'owner': Filter by selected owners (if any selected)
   * - 'account': Filter by selected account keys (if any selected)
   * 
   * Account key format: "owner_accountType" (e.g., "John_checking")
   * 
   * @type {ComputedRef<Array>} Filtered transaction array
   */
  const filteredTransactions = computed(() => {
    if (breakdownMode.value === 'all') {
      return transactions.value
    }
    
    if (breakdownMode.value === 'owner') {
      if (selectedOwners.value.length === 0) return transactions.value
      return transactions.value.filter(t => selectedOwners.value.includes(t.owner))
    }
    
    if (breakdownMode.value === 'account') {
      if (selectedAccounts.value.length === 0) return transactions.value
      return transactions.value.filter(t => {
        const accountKey = `${t.owner}_${t.bank_account_type}`
        return selectedAccounts.value.includes(accountKey)
      })
    }
    
    return transactions.value
  })
  
  /**
   * Group filtered transactions by current period
   * 
   * Returns array of period objects with:
   * - date: Period start timestamp
   * - income: Total income for period
   * - expenses: Total expenses for period
   * - transfers: Total transfers for period
   * - incomeByCategory: Income breakdown by category
   * - expensesByCategory: Expenses breakdown by category
   * - transfersByCategory: Transfers breakdown by category
   * 
   * @type {ComputedRef<Array>} Grouped timeline data
   */
  const timelineData = computed(() => {
    if (!filteredTransactions.value.length) return []
    return groupTransactionsByPeriod(filteredTransactions.value, currentGrouping.value)
  })
  
  // ========================================
  // TRANSACTION LOADING
  // ========================================
  
  /**
   * Load all transactions from the API
   * 
   * Process:
   * 1. Fetch transactions in batches (1000 per page)
   * 2. Continue until all data loaded or 10 pages reached
   * 3. Calculate date range from loaded data
   * 4. Initialize breakdown selections
   * 
   * Pagination:
   * - Batch size: 1000 transactions per request
   * - Max pages: 10 (up to 10,000 transactions)
   * - Stops early if response has fewer than batch size
   * 
   * @param {string} token - JWT auth token
   * @returns {Promise<void>}
   * 
   * @example
   * await loadTransactions(authStore.token)
   */
  async function loadTransactions(token) {
    if (!token) return
    
    loading.value = true
    
    try {
      let allTransactions = []
      let page = 1
      const batchSize = 1000
      
      // Load transactions in batches
      while (page <= 10) {
        const response = await fetch(
          `${API_BASE}/transactions/list?page=${page}&limit=${batchSize}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        
        if (!response.ok) throw new Error('Failed to load transactions')
        
        const data = await response.json()
        
        // No more data, stop pagination
        if (data.length === 0) break
        
        allTransactions = allTransactions.concat(data)
        
        // Last page (incomplete batch), stop pagination
        if (data.length < batchSize) break
        
        page++
      }
      
      transactions.value = allTransactions
      
      // Calculate date range from loaded data
      if (allTransactions.length > 0) {
        const dates = allTransactions.map(t => new Date(t.posted_at))
        dateRange.value.start = new Date(Math.min(...dates))
        dateRange.value.end = new Date(Math.max(...dates))
        
        // Initialize breakdown selections with first available options
        initializeBreakdownSelections()
      }
      
      console.log('Timeline loaded:', allTransactions.length, 'transactions')
      
    } catch (error) {
      console.error('Failed to load transactions:', error)
    } finally {
      loading.value = false
    }
  }
  
  // ========================================
  // BREAKDOWN INITIALIZATION
  // ========================================
  
  /**
   * Initialize breakdown selections with first available owner/account
   * 
   * Process:
   * 1. Extract unique owners from transactions
   * 2. Extract unique account keys (owner_accountType)
   * 3. Select first owner (alphabetically) by default
   * 4. Select first account (alphabetically) by default
   * 
   * Called automatically after transactions are loaded.
   * Provides sensible defaults for breakdown filtering.
   */
  function initializeBreakdownSelections() {
    // Get unique owners
    const owners = new Set()
    transactions.value.forEach(t => {
      if (t.owner) owners.add(t.owner)
    })
    
    // Get unique accounts
    const accounts = new Set()
    transactions.value.forEach(t => {
      if (t.owner && t.bank_account_type) {
        accounts.add(`${t.owner}_${t.bank_account_type}`)
      }
    })
    
    // Select first owner and account by default
    if (owners.size > 0) {
      selectedOwners.value = [Array.from(owners).sort()[0]]
    }
    if (accounts.size > 0) {
      selectedAccounts.value = [Array.from(accounts).sort()[0]]
    }
  }
  
  // ========================================
  // ZOOM CONTROLS
  // ========================================
  
  /**
   * Zoom in (increase detail level)
   * 
   * Zoom progression:
   * -1 (Year) → 0 (Quarter) → 1 (Month)
   * 
   * Stops at level 1 (most detailed view).
   */
  function zoomIn() {
    if (currentZoomLevel.value < 1) {
      currentZoomLevel.value++
    }
  }
  
  /**
   * Zoom out (decrease detail level)
   * 
   * Zoom progression:
   * 1 (Month) → 0 (Quarter) → -1 (Year)
   * 
   * Stops at level -1 (least detailed view).
   */
  function zoomOut() {
    if (currentZoomLevel.value > -1) {
      currentZoomLevel.value--
    }
  }
  
  /**
   * Reset zoom to default level (quarter view)
   * 
   * Returns to level 0 (quarter grouping).
   */
  function resetZoom() {
    currentZoomLevel.value = 0
  }
  
  // ========================================
  // EXPOSED API
  // ========================================
  
  return {
    // State
    loading,
    transactions,
    dateRange,
    currentZoomLevel,
    breakdownMode,
    selectedOwners,
    selectedAccounts,
    
    // Computed
    hasData,
    currentGrouping,
    timelineData,
    filteredTransactions,
    
    // Actions
    loadTransactions,
    zoomIn,
    zoomOut,
    resetZoom
  }
}