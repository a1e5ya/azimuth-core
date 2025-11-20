// frontend/src/composables/useTimelineData.js

import { ref, computed } from 'vue'
import { groupTransactionsByPeriod, getGroupingByZoomLevel } from '@/utils/timelineHelpers'

/**
 * Composable for managing timeline data
 * Handles transaction loading, grouping, breakdown filtering, and date range management
 */
export function useTimelineData() {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  
  const loading = ref(false)
  const transactions = ref([])
  const currentZoomLevel = ref(0) // Start at quarter view
  
  // Breakdown state
  const breakdownMode = ref('all') // 'all' | 'owner' | 'account'
  const selectedOwners = ref([])
  const selectedAccounts = ref([])
  
  const dateRange = ref({
    start: null,
    end: null
  })
  
  // Computed properties
  const hasData = computed(() => transactions.value.length > 0)
  
  const currentGrouping = computed(() => {
    return getGroupingByZoomLevel(currentZoomLevel.value)
  })
  
  // Filtered transactions based on breakdown mode
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
  
  const timelineData = computed(() => {
    if (!filteredTransactions.value.length) return []
    return groupTransactionsByPeriod(filteredTransactions.value, currentGrouping.value)
  })
  
  /**
   * Load all transactions from the API
   * @param {string} token - Auth token
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
        
        if (data.length === 0) break
        
        allTransactions = allTransactions.concat(data)
        
        if (data.length < batchSize) break
        
        page++
      }
      
      transactions.value = allTransactions
      
      // Calculate date range
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
  
  /**
   * Initialize breakdown selections with first available owner/account
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
  
  /**
   * Zoom in (increase detail level)
   * -1: Year → 0: Quarter → 1: Month
   */
  function zoomIn() {
    if (currentZoomLevel.value < 1) {
      currentZoomLevel.value++
    }
  }
  
  /**
   * Zoom out (decrease detail level)
   * 1: Month → 0: Quarter → -1: Year
   */
  function zoomOut() {
    if (currentZoomLevel.value > -1) {
      currentZoomLevel.value--
    }
  }
  
  /**
   * Reset zoom to default level (quarter view)
   */
  function resetZoom() {
    currentZoomLevel.value = 0
  }
  
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