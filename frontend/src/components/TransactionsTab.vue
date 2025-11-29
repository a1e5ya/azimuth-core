<!--
  Transactions Tab - Main transaction list with filtering and CRUD operations
  
  Core features:
  - Paginated transaction list (25/50/100/200 per page)
  - Multi-criteria filtering (date, amount, merchant, owner, account, category)
  - Sort by any column (ascending/descending)
  - Bulk operations (categorize, delete)
  - Transaction CRUD (create, edit, delete)
  - CSV/XLSX import with auto-categorization
  - Real-time stats (total, filtered, categorized counts)
  
  Data flow:
  - Summary stats from /transactions/summary (total counts)
  - Filtered stats from /transactions/filtered-summary (current filter results)
  - Filter metadata from /transactions/filter-metadata (dropdown options)
  - Transaction list from /transactions/list (paginated results)
  
  Child components:
  - TransactionsInfo: Summary statistics display
  - TransactionsFilters: Multi-criteria filter panel
  - TransactionsTable: Data grid with inline editing
  - TransactionsCRUD: Add/edit/delete modals
  - TransactionImportModal: File upload interface
-->
<template>
  <div class="tab-content">
    <div class="container">
      <!-- Transactions Header -->
      <div class="transactions-header">
        <TransactionsInfo
          :summary="summary"
          :filtered-stats="filteredStats"
          :uploads="localUploads"
        />

        <!-- Action Buttons -->
        <div class="action-buttons-compact">
          <button 
            class="btn btn-icon" 
            @click="handleAdd"
            title="Add Transaction"
          >
            <AppIcon name="plus" size="medium" />
          </button>
          
          <button 
            class="btn btn-icon" 
            @click="showImportModal = true"
            title="Import Transactions"
          >
            <AppIcon name="file-add" size="medium" />
          </button>
          
          <button 
            class="btn btn-icon" 
            @click="showFilters = !showFilters"
            :class="{ 'btn-active': showFilters }"
            title="Filter Transactions"
          >
            <AppIcon name="filter" size="medium" />
          </button>
          
          <button 
            class="btn btn-icon" 
            @click="refreshTransactions" 
            :disabled="loading"
            title="Refresh"
          >
            <AppIcon name="refresh" size="medium" />
          </button>
        </div>
        
        <!-- Pagination controls -->
        <div class="pagination-controls">
          <select v-model.number="pageSize" @change="changePageSize" class="page-size-select">
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
          </select>
          
          <button 
            class="btn btn-icon" 
            @click="changePage(currentPage - 1)"
            :disabled="currentPage <= 1"
            title="Previous Page"
          >
            <AppIcon name="angle-double-left" size="medium" />
          </button>
          
          <span class="page-indicator">{{ currentPage }}</span>
          
          <button 
            class="btn btn-icon" 
            @click="changePage(currentPage + 1)"
            :disabled="transactions.length < pageSize"
            title="Next Page"
          >
            <AppIcon name="angle-double-right" size="medium" />
          </button>
        </div>
      </div>
      
      <!-- Collapsible filter panel -->
      <TransactionsFilters
        v-model:show="showFilters"
        v-model="filters"
        :filter-options="filterOptions"
        @apply="loadTransactions"
      />

      <!-- Transaction data grid -->
      <TransactionsTable
        :transactions="transactions"
        :loading="loading"
        :has-active-filters="hasActiveFilters"
        :sort-by="sortBy"
        :sort-order="sortOrder"
        :grouped-categories="groupedCategories"
        :category-tree="categoryTree"
        @edit="handleEdit"
        @delete="handleDelete"
        @sort="toggleSort"
        @bulk-categorize="handleBulkCategorize"
        @bulk-delete="handleBulkDelete"
        @category-updated="handleCategoryUpdated"
      />
    </div>

    <!-- CRUD Modals -->
    <TransactionsCRUD
      ref="crudComponent"
      @transaction-updated="handleTransactionUpdated"
      @transaction-deleted="handleTransactionDeleted"
      @add-chat-message="addChatMessage"
    />

    <!-- Import modal -->
    <TransactionImportModal
      :show="showImportModal"
      @close="showImportModal = false"
      @import-started="handleImportStarted"
      @import-complete="handleImportComplete"
    />
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import AppIcon from './AppIcon.vue'
import TransactionsInfo from './TransactionsInfo.vue'
import TransactionsFilters from './TransactionsFilters.vue'
import TransactionsTable from './TransactionsTable.vue'
import TransactionsCRUD from './TransactionsCRUD.vue'
import TransactionImportModal from './TransactionImportModal.vue'

export default {
  name: 'TransactionsTab',
  components: {
    AppIcon,
    TransactionsInfo,
    TransactionsFilters,
    TransactionsTable,
    TransactionsCRUD,
    TransactionImportModal
  },
  props: {
    /**
     * Current authenticated user
     * @type {Object}
     */
    user: {
      type: Object,
      required: true
    }
  },
  emits: [
    /**
     * Add message to chat
     * @param {Object} payload - {message: string, response: string}
     */
    'add-chat-message'
  ],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
    /** Count of filtered transactions */
    const filteredCount = ref(0)
    /** Hidden file input reference (legacy, unused) */
    const fileInput = ref(null)
    /** CRUD modal component reference */
    const crudComponent = ref(null)
    /** Local upload history display */
    const localUploads = ref([])
    
    /** Loading state for data fetching */
    const loading = ref(false)
    /** Summary stats (total counts) */
    const summary = ref(null)
    /** Current page transactions */
    const transactions = ref([])
    
    /** Current pagination page */
    const currentPage = ref(1)
    /** Transactions per page */
    const pageSize = ref(50)
    /** Sort column */
    const sortBy = ref('posted_at')
    /** Sort direction */
    const sortOrder = ref('desc')
    /** Show/hide filter panel */
    const showFilters = ref(false)
    /** Show/hide import modal */
    const showImportModal = ref(false)
    
    /**
     * Handle import start event
     * Sends notification to chat
     */
    const handleImportStarted = () => {
      addChatMessage({ response: 'Starting import...' })
    }

    /**
     * Open add transaction modal
     */
    const handleAdd = () => {
      crudComponent.value.addTransaction()
    }

    /**
     * Trigger bulk delete operation
     * @param {Array<number>} transactionIds - IDs to delete
     */
    const handleBulkDelete = (transactionIds) => {
      crudComponent.value.bulkDelete(transactionIds)
    }

    /**
     * Handle import completion
     * Reloads all data and shows results in chat
     * @param {Object} result - Import result with success flag and stats
     */
    const handleImportComplete = async (result) => {
      if (result.success) {
        // Show chat message if provided
        if (result.message) {
          addChatMessage({
            message: `Import complete: ${result.fileCount} file(s)`,
            response: result.message
          })
        }
        
        await loadFilterOptions()
        await loadTransactions()
        await loadSummary()
      }
    }

    /** Filter criteria state */
    const filters = ref({
      startDate: '',
      endDate: '',
      minAmount: null,
      maxAmount: null,
      merchant: '',
      owners: [],
      accountTypes: [],
      types: [],
      categories: [],
      subcategories: []
    })
    
    /** Available filter options (dropdowns) */
    const filterOptions = ref({
      ownerAccountMap: {},
      mainCategories: [],
      categoryMap: {},
      subcategoryMap: {}
    })

    /** Filtered transaction statistics */
    const filteredStats = ref({
      filtered_count: 0,
      categorized_count: 0,
      uncategorized_count: 0,
      total_amount: 0
    })

    /**
     * Load filtered statistics from API
     * Uses current filter criteria to get counts
     */
    const loadFilteredStats = async () => {
      if (!props.user) return
      
      try {
        const params = {
          start_date: filters.value.startDate || undefined,
          end_date: filters.value.endDate || undefined,
          min_amount: filters.value.minAmount || undefined,
          max_amount: filters.value.maxAmount || undefined,
          merchant: filters.value.merchant || undefined,
          owners: filters.value.owners.length > 0 ? filters.value.owners : undefined,
          account_types: filters.value.accountTypes.length > 0 ? filters.value.accountTypes : undefined,
          main_categories: filters.value.types.length > 0 ? filters.value.types : undefined,
          categories: filters.value.categories.length > 0 ? filters.value.categories : undefined,
          subcategories: filters.value.subcategories.length > 0 ? filters.value.subcategories : undefined
        }
        
        Object.keys(params).forEach(key => {
          if (params[key] === undefined) delete params[key]
        })
        
        const response = await axios.get(`${API_BASE}/transactions/filtered-summary`, {
          params,
          headers: { Authorization: `Bearer ${authStore.token}` },
          paramsSerializer: {
            indexes: null
          }
        })
        
        filteredStats.value = response.data
      } catch (error) {
        console.error('Failed to load filtered stats:', error)
      }
    }

    /** Category tree from store */
    const categoryTree = computed(() => categoryStore.categories || [])
    
    /**
     * Group categories by parent for dropdown display
     * Flattens tree structure into grouped format
     * @returns {Array} Category groups with nested categories
     */
    const groupedCategories = computed(() => {
      const groups = {}
      
      const flattenCategories = (categories, parentName = '') => {
        const result = []
        for (const cat of categories) {
          result.push({ ...cat, parent_name: parentName })
          if (cat.children) {
            result.push(...flattenCategories(cat.children, cat.name))
          }
        }
        return result
      }
      
      const flatCategories = flattenCategories(categoryTree.value)
      
      for (const category of flatCategories) {
        const groupName = category.parent_name || category.category_type || 'Other'
        
        if (!groups[groupName]) {
          groups[groupName] = {
            name: groupName,
            categories: []
          }
        }
        
        groups[groupName].categories.push(category)
      }
      
      return Object.values(groups)
    })

    /**
     * Check if any filters are active
     * @returns {boolean} True if any filter has a value
     */
    const hasActiveFilters = computed(() => {
      return filters.value.startDate || 
             filters.value.endDate || 
             filters.value.minAmount || 
             filters.value.maxAmount || 
             filters.value.merchant ||
             filters.value.owners.length > 0 ||
             filters.value.accountTypes.length > 0 ||
             filters.value.types.length > 0 ||
             filters.value.categories.length > 0 ||
             filters.value.subcategories.length > 0
    })

    /**
     * Emit chat message to parent
     * @param {Object} messageData - Message object with message/response
     */
    const addChatMessage = (messageData) => {
      emit('add-chat-message', messageData)
    }

    /**
     * Trigger hidden file input (legacy, unused)
     */
    const triggerFileUpload = () => {
      fileInput.value?.click()
    }

    /**
     * Handle file selection (legacy, unused)
     * @param {Event} event - File input change event
     */
    const handleFileSelect = (event) => {
      const files = event.target.files
      processFiles(files)
      event.target.value = ''
    }

    /**
     * Process uploaded files (legacy, unused)
     * Import now handled by TransactionImportModal
     * @param {FileList} files - Files to process
     */
    const processFiles = async (files) => {
      if (!files || files.length === 0) return
      
      if (!props.user) {
        addChatMessage({
          response: 'Please sign in to upload files.'
        })
        return
      }

      for (const file of Array.from(files)) {
        if (!file.name.toLowerCase().endsWith('.csv') && !file.name.toLowerCase().endsWith('.xlsx')) {
          addChatMessage({
            message: `File upload: ${file.name}`,
            response: 'Please upload only CSV or XLSX files.'
          })
          continue
        }

        if (file.size > 10 * 1024 * 1024) {
          addChatMessage({
            message: `File upload: ${file.name}`,
            response: 'File too large. Please upload files smaller than 10MB.'
          })
          continue
        }
        
        const upload = {
          id: Date.now() + Math.random(),
          filename: file.name,
          status: 'processing',
          rows: 0,
          timestamp: new Date().toLocaleTimeString()
        }
        
        localUploads.value.unshift(upload)
        
        addChatMessage({
          message: `Uploading: ${file.name}`,
          response: `Processing ${file.name}...`
        })
        
        try {
          const token = authStore.token
          
          const formData = new FormData()
          formData.append('file', file)
          formData.append('account_name', 'Default Account')
          formData.append('account_type', 'checking')
          formData.append('auto_categorize', 'true')
          
          const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000
          })
          
          upload.status = 'success'
          upload.rows = response.data.summary.rows_inserted || 0
          
          addChatMessage({
            message: `File uploaded: ${file.name}`,
            response: `Successfully imported ${upload.rows} transactions!`
          })
          
          await loadFilterOptions()
          await loadSummary()
          await loadTransactions()
          
        } catch (error) {
          upload.status = 'error'
          console.error('Upload failed:', error)
          
          let errorMessage = 'Upload failed: Unknown error'
          if (error.response?.status === 401) {
            errorMessage = 'Authentication failed. Please try signing out and back in.'
          } else if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail
          }
          
          addChatMessage({
            message: `File upload: ${file.name}`,
            response: errorMessage
          })
        }
      }
    }

    /**
     * Load filter dropdown options from API
     * Tries /filter-metadata endpoint first, falls back to scanning all transactions
     */
    const loadFilterOptions = async () => {
      if (!props.user) return
      
      try {
        const token = authStore.token
        
        const response = await axios.get(`${API_BASE}/transactions/filter-metadata`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        filterOptions.value = response.data
        
      } catch (error) {
        console.error('Filter metadata endpoint failed, using fallback:', error)
        
        const token = authStore.token
        const ownerAccountMap = {}
        const mainCats = new Set()
        const categoryMap = {}
        const subcategoryMap = {}
        
        let page = 1
        let hasMore = true
        const batchSize = 200
        const maxPages = 100
        
        // Scan all transactions to build filter options
        while (hasMore && page <= maxPages) {
          const response = await axios.get(`${API_BASE}/transactions/list`, {
            params: { page: page, limit: batchSize },
            headers: { 'Authorization': `Bearer ${token}` }
          })
          
          const pageTransactions = response.data
          
          if (pageTransactions.length === 0) {
            hasMore = false
            break
          }
          
          pageTransactions.forEach(t => {
            if (t.owner && t.bank_account_type) {
              if (!ownerAccountMap[t.owner]) {
                ownerAccountMap[t.owner] = new Set()
              }
              ownerAccountMap[t.owner].add(t.bank_account_type)
            }
            
            if (t.main_category) {
              mainCats.add(t.main_category)
              
              if (t.category) {
                if (!categoryMap[t.main_category]) {
                  categoryMap[t.main_category] = new Set()
                }
                categoryMap[t.main_category].add(t.category)
                
                if (t.subcategory) {
                  const key = `${t.main_category}|${t.category}`
                  if (!subcategoryMap[key]) {
                    subcategoryMap[key] = new Set()
                  }
                  subcategoryMap[key].add(t.subcategory)
                }
              }
            }
          })
          
          if (pageTransactions.length < batchSize) {
            hasMore = false
          }
          
          page++
        }
        
        // Convert Sets to sorted arrays
        const ownerAccountMapArray = {}
        Object.keys(ownerAccountMap).forEach(owner => {
          ownerAccountMapArray[owner] = Array.from(ownerAccountMap[owner]).sort()
        })
        
        const categoryMapArray = {}
        Object.keys(categoryMap).forEach(main => {
          categoryMapArray[main] = Array.from(categoryMap[main]).sort()
        })
        
        const subcategoryMapArray = {}
        Object.keys(subcategoryMap).forEach(key => {
          subcategoryMapArray[key] = Array.from(subcategoryMap[key]).sort()
        })
        
        filterOptions.value = {
          ownerAccountMap: ownerAccountMapArray,
          mainCategories: Array.from(mainCats).sort(),
          categoryMap: categoryMapArray,
          subcategoryMap: subcategoryMapArray
        }
      }
    }

    /**
     * Load summary statistics from API
     * Gets total transaction count and overall stats
     */
    const loadSummary = async () => {
      if (!props.user) return
      
      try {
        const token = authStore.token
        const response = await axios.get(`${API_BASE}/transactions/summary`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        summary.value = response.data
      } catch (error) {
        console.error('Failed to load summary:', error)
      }
    }

    /**
     * Load paginated transactions with current filters
     * Applies all filter criteria, sorting, and pagination
     */
    async function loadTransactions() {
      loading.value = true
      
      try {
        const params = {
          page: currentPage.value,
          limit: pageSize.value,
          sort_by: sortBy.value,
          sort_order: sortOrder.value,
          start_date: filters.value.startDate || undefined,
          end_date: filters.value.endDate || undefined,
          min_amount: filters.value.minAmount || undefined,
          max_amount: filters.value.maxAmount || undefined,
          merchant: filters.value.merchant || undefined,
          owners: filters.value.owners.length > 0 ? filters.value.owners : undefined,
          account_types: filters.value.accountTypes.length > 0 ? filters.value.accountTypes : undefined,
          main_categories: filters.value.types.length > 0 ? filters.value.types : undefined,
          categories: filters.value.categories.length > 0 ? filters.value.categories : undefined,
          subcategories: filters.value.subcategories.length > 0 ? filters.value.subcategories : undefined,
          _t: Date.now()  // Cache busting timestamp
        }
        
        Object.keys(params).forEach(key => {
          if (params[key] === undefined) delete params[key]
        })
        
        const response = await axios.get(`${API_BASE}/transactions/list`, {
          params,
          headers: { 
            Authorization: `Bearer ${authStore.token}`,
            'Cache-Control': 'no-cache'
          },
          paramsSerializer: {
            indexes: null 
          }
        })
        
        transactions.value = response.data
        await loadFilteredStats()
      } catch (error) {
        console.error('Failed to load transactions:', error)
      } finally {
        loading.value = false
      }
    }

    /**
     * Refresh all transaction data
     * Reloads summary and transaction list
     */
    const refreshTransactions = async () => {
      await loadSummary()
      await loadTransactions()
    }

    /**
     * Change pagination page
     * @param {number} newPage - Target page number (1-indexed)
     */
    const changePage = (newPage) => {
      if (newPage >= 1) {
        currentPage.value = newPage
      }
    }

    /**
     * Change page size and reset to page 1
     */
    const changePageSize = () => {
      currentPage.value = 1
      loadTransactions()
    }

    /**
     * Toggle column sort direction
     * @param {string} column - Column name to sort by
     */
    const toggleSort = (column) => {
      if (sortBy.value === column) {
        sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
      } else {
        sortBy.value = column
        sortOrder.value = 'desc'
      }
    }

    /**
     * Open edit modal for transaction
     * @param {Object} transaction - Transaction to edit
     */
    const handleEdit = (transaction) => {
      crudComponent.value.editTransaction(transaction)
    }

    /**
     * Open delete confirmation for transaction
     * @param {Object} transaction - Transaction to delete
     */
    const handleDelete = (transaction) => {
      crudComponent.value.deleteTransaction(transaction)
    }

    /**
     * Handle transaction update event
     * Reloads all data including filter options and stats
     */
    const handleTransactionUpdated = async () => {
      await loadFilterOptions()
      await loadTransactions()
      await loadSummary()
      await loadFilteredStats()
    }

    /**
     * Handle transaction delete event
     * Clears table and reloads with delay to ensure backend commit
     */
    const handleTransactionDeleted = async () => {
      // Clear transactions array to force re-render
      transactions.value = []
      
      // Wait a moment for backend to commit
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // Reload everything with cache-busting
      await loadFilterOptions()
      await loadTransactions()
      await loadSummary()
      await loadFilteredStats()
    }

    /**
     * Handle category update event
     * Refreshes filter options to reflect new categories
     */
    const handleCategoryUpdated = async () => {
      await loadFilterOptions()
      await loadTransactions()
      await loadSummary()
      await loadFilteredStats()
    }

    /**
     * Handle bulk categorization request
     * Updates multiple transactions with same category
     * @param {Object} data - {transactionIds: Array, categoryId: number}
     */
    const handleBulkCategorize = async (data) => {
      try {
        const token = authStore.token
        
        const response = await axios.post(`${API_BASE}/transactions/bulk-categorize`, {
          transaction_ids: data.transactionIds,
          category_id: data.categoryId,
          confidence: 1.0
        }, {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Cache-Control': 'no-cache'
          }
        })
        
        addChatMessage({
          message: `Bulk categorization: ${data.transactionIds.length} transactions`,
          response: response.data.message || `Successfully categorized ${response.data.updated_count} transactions!`
        })
        
        transactions.value = []
        
        await new Promise(resolve => setTimeout(resolve, 100))
        await loadFilterOptions()
        await loadTransactions()
        await loadSummary()
        await loadFilteredStats()
        
      } catch (error) {
        console.error('❌ Bulk categorization failed:', error)
        addChatMessage({
          response: error.response?.data?.detail || 'Bulk categorization failed. Please try again.'
        })
      }
    }

    /** Watch filters and reload on change */
    watch(filters, () => {
      currentPage.value = 1
      loadTransactions()
      loadFilteredStats()
    }, { deep: true })
    
    /** Watch pagination/sort and reload on change */
    watch(() => [currentPage.value, pageSize.value, sortBy.value, sortOrder.value], () => {
      loadTransactions()
    })

    /** Load initial data on mount */
    onMounted(async () => {
      if (props.user) {
        await categoryStore.loadCategories()
        await loadFilterOptions()
        await loadSummary()
        await loadTransactions()
      }
    })

    return {
      fileInput,
      crudComponent,
      localUploads,
      loading,
      summary,
      filteredCount,
      transactions,
      currentPage,
      pageSize,
      sortBy,
      sortOrder,
      showFilters,
      filters,
      filterOptions,
      filteredStats,
      categoryTree,
      groupedCategories,
      hasActiveFilters,
      addChatMessage,
      triggerFileUpload,
      handleFileSelect,
      loadFilterOptions,
      loadSummary,
      loadTransactions,
      refreshTransactions,
      changePage,
      changePageSize,
      toggleSort,
      handleEdit,
      handleDelete,
      handleTransactionUpdated,
      handleTransactionDeleted,
      handleBulkCategorize,
      handleCategoryUpdated,
      showImportModal,
      handleImportStarted,
      handleImportComplete,
      handleAdd,
      handleBulkDelete
    }
  }
}
</script>

<style scoped>
.action-buttons-compact {
  display: flex;
  gap: var(--gap-large);
}

.action-buttons-compact .btn-icon {
  width: 2.5rem;
  height: 2.5rem;
  padding: var(--gap-small);
  backdrop-filter: blur(1.25rem);
  background: var(--color-background);
  box-shadow: var(--shadow);
  margin: 0;
}

.action-buttons-compact .btn-icon:hover {
  box-shadow: var(--shadow-hover);
}

.transactions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  flex-wrap: wrap;
  gap: var(--gap-standard);
  padding: var(--gap-small);
  border-radius: var(--radius);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.page-size-select {
  padding: 0.375rem var(--gap-small);
  margin: 0 var(--gap-standard);
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: transparent;
  font-size: var(--text-small);
  cursor: pointer;
}

.page-size-select:focus {
  outline: none;
  border-color: var(--color-button-active);
}

.page-indicator {
  font-size: var(--text-small);
  color: var(--color-text);
  padding: 0 var(--gap-small);
  min-width: 2rem;
  text-align: center;
}

.pagination-controls .btn-icon {
  width: 2rem;
  height: 2rem;
  padding: 0.25rem;
  margin: 0;
  background-color: transparent;
  box-shadow: none;
}
</style>