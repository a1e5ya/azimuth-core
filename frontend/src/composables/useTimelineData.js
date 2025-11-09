// frontend/src/composables/useTimelineData.js

import { ref, computed } from 'vue'
import { groupTransactionsByPeriod, getGroupingByZoomLevel } from '@/utils/timelineHelpers'

/**
 * Composable for managing timeline data
 * Handles transaction loading, grouping, and date range management
 */
export function useTimelineData() {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  
  const loading = ref(false)
  const transactions = ref([])
  const currentZoomLevel = ref(0) // Start at quarter view
  
  const dateRange = ref({
    start: null,
    end: null
  })
  
  // Computed properties
  const hasData = computed(() => transactions.value.length > 0)
  
  const currentGrouping = computed(() => {
    return getGroupingByZoomLevel(currentZoomLevel.value)
  })
  
  const timelineData = computed(() => {
    if (!transactions.value.length) return []
    return groupTransactionsByPeriod(transactions.value, currentGrouping.value)
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
      }
      
      console.log('Timeline loaded:', allTransactions.length, 'transactions')
      
    } catch (error) {
      console.error('Failed to load transactions:', error)
    } finally {
      loading.value = false
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
    
    // Computed
    hasData,
    currentGrouping,
    timelineData,
    
    // Actions
    loadTransactions,
    zoomIn,
    zoomOut,
    resetZoom
  }
}