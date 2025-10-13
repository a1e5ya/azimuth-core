<template>
  <div class="tab-content">


    <!-- Transactions Header with Stats and Pagination -->
    <div class="container">
      <div class="transactions-header">

        <!-- Left: Stats -->
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-label">Total:</span>
            <span class="stat-value">{{ summary?.total_transactions?.toLocaleString() || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Categorized:</span>
            <span class="stat-value">{{ summary?.categorized_count?.toLocaleString() || 0 }}</span>
          </div>
          
          <!-- Upload Progress Inline -->
          <div v-if="localUploads.length > 0" class="upload-inline">
            <div v-for="upload in localUploads.slice(0, 1)" :key="upload.id" class="upload-mini">
              <span v-if="upload.status === 'success'">✓</span>
              <span v-else-if="upload.status === 'error'">✗</span>
              <span v-else class="loading-spinner-mini">⟳</span>
              <span class="upload-mini-text">{{ upload.filename }}</span>
              <span v-if="upload.status === 'success'" class="upload-mini-count">
                {{ upload.rows }} rows
              </span>
            </div>
          </div>
        </div>

                    <!-- Action Buttons - Compact Top Left -->
    <div class="action-buttons-compact">
      <button 
        class="btn btn-icon" 
        @click="triggerFileUpload"
        title="Import Transactions"
      >
        <AppIcon name="file-add" size="medium" />
      </button>
      
      <button 
        class="btn btn-icon" 
        @click="$emit('update:showFilters', !showFilters)"
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
      
      <input 
        ref="fileInput" 
        type="file" 
        accept=".csv,.xlsx" 
        multiple 
        @change="handleFileSelect" 
        style="display: none;"
      >
    </div>
        
        <!-- Right: Pagination -->
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
      
      <!-- Compact Filters Panel -->
      <div class="filters-panel-compact" v-if="showFilters">
        <!-- First Row: Date Range & Amounts -->
        <div class="filters-row">
          <div class="filter-group-compact">
            <label>From Date</label>
            <input 
              type="date" 
              v-model="filters.startDate"
              class="filter-input-compact"
            >
          </div>
          
          <div class="filter-group-compact">
            <label>To Date</label>
            <input 
              type="date" 
              v-model="filters.endDate"
              class="filter-input-compact"
            >
          </div>
          
          <div class="filter-group-compact">
            <label>Min Amount</label>
            <input 
              type="number" 
              v-model.number="filters.minAmount"
              class="filter-input-compact"
              placeholder="0.00"
              step="0.01"
            >
          </div>
          
          <div class="filter-group-compact">
            <label>Max Amount</label>
            <input 
              type="number" 
              v-model.number="filters.maxAmount"
              class="filter-input-compact"
              placeholder="1000.00"
              step="0.01"
            >
          </div>
        </div>
        
        <!-- Second Row: Type & Categories -->
        <div class="filters-row filters-row-3col">
          <div class="filter-group-compact">
            <label>Type</label>
            <select v-model="filters.typeFilter" class="filter-input-compact">
              <option value="">All Types</option>
              <option v-for="type in availableTypes" :key="type.id" :value="type.id">
                {{ type.name }}
              </option>
            </select>
          </div>
          
          <div class="filter-group-compact">
            <label>Category</label>
            <select v-model="filters.categoryFilter" class="filter-input-compact" :disabled="!filters.typeFilter">
              <option value="">All Categories</option>
              <option v-for="category in availableCategories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
          
          <div class="filter-group-compact">
            <label>Subcategory</label>
            <select v-model="filters.subcategoryFilter" class="filter-input-compact" :disabled="!filters.categoryFilter">
              <option value="">All Subcategories</option>
              <option v-for="subcategory in availableSubcategories" :key="subcategory.id" :value="subcategory.id">
                {{ subcategory.name }}
              </option>
            </select>
          </div>
        </div>
        
        <!-- Third Row: Search & Actions -->
        <div class="filters-row filters-row-actions">
          <div class="filter-group-compact filter-search-compact">
            <label>Search</label>
            <input 
              type="text" 
              v-model="filters.merchant"
              class="filter-input-compact"
              placeholder="Search merchant, message..."
            >
          </div>
          
          <div class="filter-actions-compact">
            <button class="btn btn-small" @click="clearFilters">Clear</button>
            <button class="btn btn-small" @click="$emit('update:showFilters', false)">Hide</button>
          </div>
        </div>
      </div>

      <!-- Bulk Selection -->
      <div class="bulk-actions" v-if="selectedTransactions.length > 0">
        <span class="bulk-selection">{{ selectedTransactions.length }} selected</span>
        <select v-model="bulkCategoryId" class="bulk-category-select">
          <option value="">Select category for bulk assignment...</option>
          <optgroup 
            v-for="group in groupedCategories" 
            :key="group.name" 
            :label="group.name"
          >
            <option 
              v-for="category in group.categories" 
              :key="category.id" 
              :value="category.id"
            >
              {{ category.name }}
            </option>
          </optgroup>
        </select>
        <button class="btn btn-small" @click="bulkCategorize" :disabled="!bulkCategoryId">
          Apply Category
        </button>
        <button class="btn btn-link" @click="clearSelection">
          Clear Selection
        </button>
      </div>

      <!-- Loading and Empty States -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading transactions...</div>
      </div>
      
      <div v-else-if="transactions.length === 0" class="empty-state">
        <div class="empty-title">No transactions found</div>
        <div class="empty-subtitle">
          {{ hasActiveFilters ? 'Try adjusting your filters' : 'Upload CSV files to get started' }}
        </div>
      </div>
      
      <!-- Transactions Table -->
      <div v-else class="transactions-table-container">
        <table class="transactions-table">
          <thead>
            <tr>
              <th class="col-select">
                <input 
                  type="checkbox" 
                  :checked="allVisibleTransactionsSelected"
                  @change="toggleAllTransactions"
                >
              </th>
              <th class="col-date clickable" @click="toggleSort('posted_at')">
                Date
                <span v-if="sortBy === 'posted_at'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-amount clickable" @click="toggleSort('amount')">
                Amount
                <span v-if="sortBy === 'amount'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-merchant clickable" @click="toggleSort('merchant')">
                Merchant
                <span v-if="sortBy === 'merchant'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-type">Type</th>
              <th class="col-category">Category</th>
              <th class="col-subcategory">Subcategory</th>
              <th class="col-actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="transaction in transactions" 
              :key="transaction.id"
              class="transaction-row"
              :class="{ 
                'selected': selectedTransactions.includes(transaction.id)
              }"
              :style="getTransactionRowStyle(transaction)"
            >
              <td class="col-select">
                <input 
                  type="checkbox" 
                  :checked="selectedTransactions.includes(transaction.id)"
                  @change="toggleTransactionSelection(transaction.id)"
                >
              </td>
              
              <td class="col-date">
                <div class="date-primary">{{ formatDate(transaction.posted_at) }}</div>
                <div class="date-secondary">{{ transaction.weekday }}</div>
              </td>
              
              <td class="col-amount" :class="getAmountClass(transaction)">
                <div class="amount-primary">{{ formatAmount(transaction.amount) }}</div>
              </td>
              
              <td class="col-merchant">
                <div class="merchant-primary">{{ transaction.merchant || 'Unknown Merchant' }}</div>
                <div class="merchant-secondary" v-if="transaction.memo">
                  {{ truncateText(transaction.memo, 50) }}
                </div>
              </td>
              
              <td class="col-type">
                <div class="category-text" v-if="getCategoryType(transaction)">
                  {{ getCategoryType(transaction) }}
                </div>
                <div v-else class="text-muted">-</div>
              </td>
              
              <td class="col-category">
                <div class="category-text" v-if="getCategoryName(transaction)">
                  {{ getCategoryName(transaction) }}
                </div>
                <div v-else class="text-muted">-</div>
              </td>
              
              <td class="col-subcategory">
                <div class="category-text" v-if="getSubcategoryName(transaction)">
                  {{ getSubcategoryName(transaction) }}
                </div>
                <div v-else class="text-muted">-</div>
              </td>
              
              <td class="col-actions">
                <ActionsMenu
                  :show-edit="true"
                  :show-add="false"
                  :show-check="false"
                  :show-delete="true"
                  @edit="editTransaction(transaction)"
                  @delete="deleteTransaction(transaction)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit Transaction Modal -->
    <div v-if="editingTransaction" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content transaction-edit-modal" @click.stop>
        <div class="modal-header">
          <h3>Edit Transaction</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="edit-form">
            <div class="form-group">
              <label>Merchant</label>
              <input 
                type="text" 
                v-model="editForm.merchant"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label>Amount</label>
              <input 
                type="number" 
                v-model.number="editForm.amount"
                class="form-input"
                step="0.01"
              >
            </div>
            
            <div class="form-group">
              <label>Memo</label>
              <textarea 
                v-model="editForm.memo"
                class="form-input"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label>Category</label>
              <select v-model="editForm.category_id" class="form-input">
                <option value="">Select category...</option>
                <optgroup 
                  v-for="group in groupedCategories" 
                  :key="group.name" 
                  :label="group.name"
                >
                  <option 
                    v-for="category in group.categories" 
                    :key="category.id" 
                    :value="category.id"
                  >
                    {{ category.name }}
                  </option>
                </optgroup>
              </select>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn" 
            @click="saveTransactionEdit"
            :disabled="saving"
          >
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
          <button class="btn btn-link" @click="closeEditModal" :disabled="saving">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deletingTransaction" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h3>Delete Transaction</h3>
          <button class="close-btn" @click="closeDeleteModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="delete-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>Are you sure you want to delete this transaction?</strong></p>
              <p class="transaction-details">
                <strong>{{ deletingTransaction.merchant || 'Unknown Merchant' }}</strong><br>
                {{ formatAmount(deletingTransaction.amount) }}<br>
                {{ formatDate(deletingTransaction.posted_at) }}
              </p>
              <p>This action cannot be undone.</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmDelete"
            :disabled="deleting"
          >
            {{ deleting ? 'Deleting...' : 'Yes, Delete' }}
          </button>
          <button class="btn btn-link" @click="closeDeleteModal" :disabled="deleting">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import ActionsMenu from './ActionsMenu.vue'
import AppIcon from './AppIcon.vue'

export default {
  name: 'TransactionsTab',
  components: {
    ActionsMenu,
    AppIcon
  },
  props: {
    user: {
      type: Object,
      required: true
    },
    allCategories: {
      type: Array,
      default: () => []
    },
    showFilters: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'add-chat-message',
    'update:showFilters'
  ],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
    const fileInput = ref(null)
    const isDragging = ref(false)
    const localUploads = ref([])
    
    const loading = ref(false)
    const summary = ref(null)
    const transactions = ref([])
    
    const currentPage = ref(1)
    const pageSize = ref(50)
    const sortBy = ref('posted_at')
    const sortOrder = ref('desc')
    
    const filters = ref({
      startDate: '',
      endDate: '',
      minAmount: null,
      maxAmount: null,
      merchant: '',
      typeFilter: '',
      categoryFilter: '',
      subcategoryFilter: ''
    })
    
    const csvMainCategories = ref([])
    const csvCategories = ref([])
    const csvSubcategories = ref([])
    
    const selectedTransactions = ref([])
    const bulkCategoryId = ref('')
    
    const editingTransaction = ref(null)
    const deletingTransaction = ref(null)
    const saving = ref(false)
    const deleting = ref(false)
    
    const editForm = ref({
      merchant: '',
      amount: 0,
      memo: '',
      category_id: ''
    })

    const categoryTree = computed(() => categoryStore.categories || [])
    
    const availableTypes = computed(() => {
      return csvMainCategories.value.map(name => ({ id: name, name }))
    })

    const availableCategories = computed(() => {
      if (!filters.value.typeFilter) return []
      
      return csvCategories.value
        .filter(cat => cat.main === filters.value.typeFilter)
        .map(cat => ({ id: cat.name, name: cat.name }))
    })

    const availableSubcategories = computed(() => {
      if (!filters.value.categoryFilter) return []
      
      return csvSubcategories.value
        .filter(sub => 
          sub.main === filters.value.typeFilter && 
          sub.category === filters.value.categoryFilter
        )
        .map(sub => ({ id: sub.name, name: sub.name }))
    })

    const hasActiveFilters = computed(() => {
      return Object.values(filters.value).some(value => value !== '' && value !== null)
    })
    
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
    
    const allVisibleTransactionsSelected = computed(() => {
      return transactions.value.length > 0 && 
             transactions.value.every(t => selectedTransactions.value.includes(t.id))
    })

    watch(filters, () => {
      currentPage.value = 1
      loadTransactions()
    }, { deep: true })
    
    watch(() => filters.value.typeFilter, (newVal, oldVal) => {
      if (newVal !== oldVal) {
        filters.value.categoryFilter = ''
        filters.value.subcategoryFilter = ''
      }
    })
    
    watch(() => filters.value.categoryFilter, (newVal, oldVal) => {
      if (newVal !== oldVal) {
        filters.value.subcategoryFilter = ''
      }
    })
    
    watch(() => [currentPage.value, pageSize.value, sortBy.value, sortOrder.value], () => {
      loadTransactions()
    })

    const hexToRgba = (hex, alpha) => {
      if (!hex) return 'transparent'
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    const getTransactionRowStyle = (transaction) => {
      if (!transaction.category_id) {
        return {}
      }
      
      const category = findCategoryById(transaction.category_id)
      if (!category || !category.color) {
        return {}
      }
      
      return {
        backgroundColor: hexToRgba(category.color, 0.1)
      }
    }

    const triggerFileUpload = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const files = event.target.files
      processFiles(files)
      event.target.value = ''
    }

    const processFiles = async (files) => {
      if (!files || files.length === 0) return
      
      if (!props.user) {
        emit('add-chat-message', {
          response: 'Please sign in to upload files.'
        })
        return
      }

      for (const file of Array.from(files)) {
        console.log('Processing file:', file.name)
        
        if (!file.name.toLowerCase().endsWith('.csv') && !file.name.toLowerCase().endsWith('.xlsx')) {
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: 'Please upload only CSV or XLSX files.'
          })
          continue
        }

        if (file.size > 10 * 1024 * 1024) {
          emit('add-chat-message', {
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
          timestamp: new Date().toLocaleTimeString(),
          summary: null,
          batch_id: null
        }
        
        localUploads.value.unshift(upload)
        
        emit('add-chat-message', {
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
          upload.summary = response.data.summary
          upload.batch_id = response.data.batch_id
          
          emit('add-chat-message', {
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
          
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: errorMessage
          })
        }
      }
    }

    const loadFilterOptions = async () => {
      if (!props.user) return
      
      try {
        const token = authStore.token
        
        const mainCats = new Set()
        const cats = new Map()
        const subCats = new Map()
        
        let page = 1
        let hasMore = true
        const batchSize = 1000
        
        while (hasMore && page <= 10) {
          const response = await axios.get(`${API_BASE}/transactions/list`, {
            params: {
              page: page,
              limit: batchSize
            },
            headers: { 'Authorization': `Bearer ${token}` }
          })
          
          const pageTransactions = response.data
          
          if (pageTransactions.length === 0) {
            hasMore = false
            break
          }
          
          pageTransactions.forEach(t => {
            if (t.main_category) {
              mainCats.add(t.main_category)
              
              if (t.category) {
                const key = `${t.main_category}|${t.category}`
                cats.set(key, {
                  main: t.main_category,
                  name: t.category
                })
                
                if (t.subcategory) {
                  const subKey = `${t.main_category}|${t.category}|${t.subcategory}`
                  subCats.set(subKey, {
                    main: t.main_category,
                    category: t.category,
                    name: t.subcategory
                  })
                }
              }
            }
          })
          
          if (pageTransactions.length < batchSize) {
            hasMore = false
          }
          
          page++
        }
        
        csvMainCategories.value = Array.from(mainCats).sort()
        csvCategories.value = Array.from(cats.values())
        csvSubcategories.value = Array.from(subCats.values())
        
      } catch (error) {
        console.error('Failed to load filter options:', error)
      }
    }

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

    const loadTransactions = async () => {
      if (!props.user) return
      
      loading.value = true
      try {
        const token = authStore.token
        
        const hasCSVFilter = filters.value.typeFilter || filters.value.categoryFilter || filters.value.subcategoryFilter
        
        if (hasCSVFilter) {
          let allTransactions = []
          let page = 1
          const batchSize = 1000
          
          while (page <= 10) {
            const params = {
              page: page,
              limit: batchSize,
              sort_by: sortBy.value,
              sort_order: sortOrder.value
            }
            
            if (filters.value.startDate) params.start_date = filters.value.startDate
            if (filters.value.endDate) params.end_date = filters.value.endDate
            if (filters.value.merchant) params.merchant = filters.value.merchant
            if (filters.value.minAmount) params.min_amount = filters.value.minAmount
            if (filters.value.maxAmount) params.max_amount = filters.value.maxAmount
            
            const response = await axios.get(`${API_BASE}/transactions/list`, {
              params,
              headers: { 'Authorization': `Bearer ${token}` }
            })
            
            const batch = response.data
            
            if (batch.length === 0) break
            
            allTransactions = allTransactions.concat(batch)
            
            if (batch.length < batchSize) break
            
            page++
          }
          
          let filtered = allTransactions.filter(t => {
            if (filters.value.typeFilter && t.main_category !== filters.value.typeFilter) {
              return false
            }
            
            if (filters.value.categoryFilter && t.category !== filters.value.categoryFilter) {
              return false
            }
            
            if (filters.value.subcategoryFilter && t.subcategory !== filters.value.subcategoryFilter) {
              return false
            }
            
            return true
          })
          
          const start = (currentPage.value - 1) * pageSize.value
          const end = start + pageSize.value
          transactions.value = filtered.slice(start, end)
          
        } else {
          const params = {
            page: currentPage.value,
            limit: pageSize.value,
            sort_by: sortBy.value,
            sort_order: sortOrder.value
          }
          
          if (filters.value.startDate) params.start_date = filters.value.startDate
          if (filters.value.endDate) params.end_date = filters.value.endDate
          if (filters.value.merchant) params.merchant = filters.value.merchant
          if (filters.value.minAmount) params.min_amount = filters.value.minAmount
          if (filters.value.maxAmount) params.max_amount = filters.value.maxAmount
          
          const response = await axios.get(`${API_BASE}/transactions/list`, {
            params,
            headers: { 'Authorization': `Bearer ${token}` }
          })
          
          transactions.value = response.data
        }
      } catch (error) {
        console.error('Failed to load transactions:', error)
      } finally {
        loading.value = false
      }
    }

    const refreshTransactions = async () => {
      await loadSummary()
      await loadTransactions()
    }

    const editTransaction = (transaction) => {
      editingTransaction.value = transaction
      editForm.value = {
        merchant: transaction.merchant || '',
        amount: parseFloat(transaction.amount),
        memo: transaction.memo || '',
        category_id: transaction.category_id || ''
      }
    }

    const closeEditModal = () => {
      editingTransaction.value = null
      editForm.value = {
        merchant: '',
        amount: 0,
        memo: '',
        category_id: ''
      }
    }

    const saveTransactionEdit = async () => {
      if (!editingTransaction.value || saving.value) return
      
      saving.value = true
      
      try {
        const token = authStore.token
        
        await axios.put(
          `${API_BASE}/transactions/${editingTransaction.value.id}`,
          editForm.value,
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        )
        
        emit('add-chat-message', {
          message: 'Transaction updated',
          response: 'Transaction has been successfully updated!'
        })
        
        await loadTransactions()
        await loadSummary()
        closeEditModal()
        
      } catch (error) {
        console.error('Failed to update transaction:', error)
        emit('add-chat-message', {
          response: 'Failed to update transaction. Please try again.'
        })
      } finally {
        saving.value = false
      }
    }

    const deleteTransaction = (transaction) => {
      deletingTransaction.value = transaction
    }

    const closeDeleteModal = () => {
      deletingTransaction.value = null
    }

    const confirmDelete = async () => {
      if (!deletingTransaction.value || deleting.value) return
      
      deleting.value = true
      
      try {
        const token = authStore.token
        
        await axios.delete(
          `${API_BASE}/transactions/${deletingTransaction.value.id}`,
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        )
        
        emit('add-chat-message', {
          message: 'Transaction deleted',
          response: 'Transaction has been permanently deleted.'
        })
        
        await loadTransactions()
        await loadSummary()
        closeDeleteModal()
        
      } catch (error) {
        console.error('Failed to delete transaction:', error)
        emit('add-chat-message', {
          response: 'Failed to delete transaction. Please try again.'
        })
      } finally {
        deleting.value = false
      }
    }

    const bulkCategorize = async () => {
      if (!bulkCategoryId.value || selectedTransactions.value.length === 0) return
      
      try {
        const token = authStore.token
        
        await axios.post(`${API_BASE}/transactions/bulk-categorize`, {
          transaction_ids: selectedTransactions.value,
          category_id: bulkCategoryId.value,
          confidence: 1.0
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        const category = props.allCategories.find(c => c.id === bulkCategoryId.value)
        emit('add-chat-message', {
          message: `Bulk categorization: ${selectedTransactions.value.length} transactions`,
          response: `Successfully applied category ${category?.name || 'selected category'} to ${selectedTransactions.value.length} transactions!`
        })
        
        selectedTransactions.value = []
        bulkCategoryId.value = ''
        await loadTransactions()
        await loadSummary()
        
      } catch (error) {
        console.error('Bulk categorization failed:', error)
        emit('add-chat-message', {
          response: 'Bulk categorization failed. Please try again.'
        })
      }
    }

    const clearFilters = () => {
      filters.value = {
        startDate: '',
        endDate: '',
        minAmount: null,
        maxAmount: null,
        merchant: '',
        typeFilter: '',
        categoryFilter: '',
        subcategoryFilter: ''
      }
    }

    const toggleSort = (column) => {
      if (sortBy.value === column) {
        sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
      } else {
        sortBy.value = column
        sortOrder.value = 'desc'
      }
    }

    const toggleTransactionSelection = (transactionId) => {
      const index = selectedTransactions.value.indexOf(transactionId)
      if (index > -1) {
        selectedTransactions.value.splice(index, 1)
      } else {
        selectedTransactions.value.push(transactionId)
      }
    }

    const toggleAllTransactions = () => {
      if (allVisibleTransactionsSelected.value) {
        selectedTransactions.value = []
      } else {
        selectedTransactions.value = transactions.value.map(t => t.id)
      }
    }

    const clearSelection = () => {
      selectedTransactions.value = []
      bulkCategoryId.value = ''
    }

    const changePage = (newPage) => {
      if (newPage >= 1) {
        currentPage.value = newPage
      }
    }

    const changePageSize = () => {
      currentPage.value = 1
      loadTransactions()
    }

    const findCategoryById = (categoryId) => {
      const searchInTree = (categories) => {
        for (const cat of categories) {
          if (cat.id === categoryId) return cat
          if (cat.children) {
            const found = searchInTree(cat.children)
            if (found) return found
          }
        }
        return null
      }
      
      return searchInTree(categoryTree.value)
    }

    const getCategoryType = (transaction) => {
      if (!transaction.main_category) return null
      return transaction.main_category
    }

    const getCategoryName = (transaction) => {
      if (!transaction.assigned_category) return null
      return transaction.assigned_category
    }

    const getSubcategoryName = (transaction) => {
      if (!transaction.subcategory) return null
      return transaction.subcategory
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-EU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    }

const formatAmount = (amount) => {
  const num = parseFloat(amount)
  const formattedValue = new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR'
  }).format(Math.abs(num))
  
  if (num > 0) {
    return `+ ${formattedValue}`
  } else if (num < 0) {
    return `- ${formattedValue}`
  }
  return formattedValue
}

    const getAmountClass = (transaction) => {
      const amount = parseFloat(transaction.amount)
      if (transaction.transaction_type === 'income' || amount > 0) {
        return 'amount-positive'
      } else if (transaction.transaction_type === 'expense' || amount < 0) {
        return 'amount-negative'
      }
      return 'amount-neutral'
    }

    const truncateText = (text, maxLength) => {
      if (!text || text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

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
      isDragging,
      localUploads,
      loading,
      summary,
      transactions,
      currentPage,
      pageSize,
      sortBy,
      sortOrder,
      filters,
      hasActiveFilters,
      availableTypes,
      availableCategories,
      availableSubcategories,
      selectedTransactions,
      bulkCategoryId,
      allVisibleTransactionsSelected,
      editingTransaction,
      deletingTransaction,
      saving,
      deleting,
      editForm,
      groupedCategories,
      hexToRgba,
      getTransactionRowStyle,
      triggerFileUpload,
      handleFileSelect,
      loadFilterOptions,
      loadSummary,
      loadTransactions,
      refreshTransactions,
      editTransaction,
      closeEditModal,
      saveTransactionEdit,
      deleteTransaction,
      closeDeleteModal,
      confirmDelete,
      bulkCategorize,
      clearFilters,
      toggleSort,
      toggleTransactionSelection,
      toggleAllTransactions,
      clearSelection,
      changePage,
      changePageSize,
      findCategoryById,
      getCategoryType,
      getCategoryName,
      getSubcategoryName,
      formatDate,
      formatAmount,
      getAmountClass,
      truncateText
    }
  }
}
</script>

<style scoped>
/* ==============================================
   ACTION BUTTONS COMPACT - TOP LEFT
   ============================================== */

.action-buttons-compact {

  display: flex;
  gap: var(--gap-large);

}

.action-buttons-compact .btn-icon {
  width: 2.5rem;
  height: 2.5rem;
  padding: 0.5rem;
  backdrop-filter: blur(1.25rem);
  background: var(--color-background);
  box-shadow: var(--shadow);
  margin: 0;
}

.action-buttons-compact .btn-icon:hover {
  box-shadow: var(--shadow-hover);
}

/* ==============================================
   TRANSACTIONS HEADER - REDESIGNED
   ============================================== */

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

/* Header Stats - Left Side */
.header-stats {
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.stat-value {
  font-size: var(--text-medium);
  font-weight: 600;
  color: var(--color-text);
}

/* Upload Progress Inline */
.upload-inline {
  display: flex;
  gap: var(--gap-small);
}

.upload-mini {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.5rem;
  background: var(--color-background);
  border-radius: var(--radius);
  font-size: var(--text-small);
}

.loading-spinner-mini {
  animation: spin 1s linear infinite;
  display: inline-block;
}

.upload-mini-text {
  max-width: 10rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-mini-count {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

/* Pagination Controls - Right Side */
.pagination-controls {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.page-size-select {
  padding: 0.375rem 0.5rem;
  margin: 0 1rem;
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

/* ==============================================
   COMPACT FILTERS PANEL
   ============================================== */

.filters-panel-compact {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
  }
  to {
    opacity: 1;
    max-height: 20rem;
    padding-top: var(--gap-standard);
    padding-bottom: var(--gap-standard);
  }
}

.filters-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--gap-small);
  margin-bottom: var(--gap-small);
}

.filters-row:last-child {
  margin-bottom: 0;
}

.filters-row-3col {
  grid-template-columns: repeat(3, 1fr);
}

.filters-row-actions {
  grid-template-columns: 1fr 1fr;
}

.filter-group-compact {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group-compact label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-light);
}

.filter-input-compact {
  padding: 0.375rem 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-button);
  font-size: var(--text-small);
  transition: border-color 0.2s ease;
}

.filter-input-compact:focus {
  outline: none;
  border-color: var(--color-button-active);
}

.filter-search-compact {
  flex: 1;
}

.filter-actions-compact {
  display: flex;
  gap: var(--gap-small);
  align-items: flex-end;
  justify-content: flex-end;
}

/* ==============================================
   BULK ACTIONS
   ============================================== */

.bulk-actions {
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
  padding: var(--gap-standard);
  background: var(--color-background-light);
  border-radius: var(--radius);
  margin-bottom: var(--gap-standard);
  flex-wrap: wrap;
}

.bulk-selection {
  font-weight: 600;
  color: var(--color-text);
}

.bulk-category-select {
  padding: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-button);
  min-width: 12rem;
}

/* ==============================================
   LOADING AND EMPTY STATES
   ============================================== */

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

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--gap-standard);
}

.empty-title {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.empty-subtitle {
  color: var(--color-text-muted);
}

/* ==============================================
   TRANSACTIONS TABLE
   ============================================== */

.transactions-table-container {
  overflow-x: auto;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-background);
  font-size: var(--text-small);
}

.transactions-table thead {
  background: var(--color-background-dark);
  position: sticky;
  top: 0;
  z-index: 10;
}

.transactions-table th {
  padding: var(--gap-standard);
  text-align: left;
  font-weight: 600;
  color: var(--color-text);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  user-select: none;
}

.transactions-table th.clickable {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.transactions-table th.clickable:hover {
  background: var(--color-background);
}

.transactions-table td {
  padding: var(--gap-standard);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  vertical-align: top;
}

.transaction-row {
  transition: background-color 0.2s ease;
}

.transaction-row:hover {
  filter: brightness(0.95);
}

.transaction-row.selected {
  outline: 2px solid var(--color-button-active);
  outline-offset: -2px;
}




/* ==============================================
   TABLE COLUMN WIDTHS
   ============================================== */

.col-select {
  width: 3rem;
  text-align: center;
}

.col-date {
  width: 7rem;
}

.col-merchant {
  min-width: 12rem;
  max-width: 20rem;
}

.col-amount {
  width: 8rem;
  text-align: right;
}

.col-type {
  width: 6rem;
}

.col-category {
  width: 10rem;
}

.col-subcategory {
  width: 10rem;
}

.col-actions {
  width: 3rem;
  text-align: center;
}


/* ==============================================
   TABLE CELL CONTENT
   ============================================== */

.date-primary {
  font-weight: 600;
  margin-bottom: 0.125rem;
}

.date-secondary {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.merchant-primary {
  font-weight: 600;
  margin-bottom: 0.125rem;
  word-break: break-word;
}

.merchant-secondary {
  color: var(--color-text-light);
  margin-bottom: 0.125rem;
  line-height: 1.3;
}

.amount-primary {
  font-weight: 600;
  margin-bottom: 0.125rem;
}

.amount-positive {
  color: none;
}

.amount-negative {
  color: none;
}

.amount-neutral {
  color: var(--color-text-light);
}

.category-text {
  font-size: var(--text-small);
  color: var(--color-text);
}

/* ==============================================
   MODALS
   ============================================== */

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: var(--color-background-light);
  backdrop-filter: blur(1.25rem);
  border-radius: var(--radius-large);
  padding: 0;
  width: 90%;
  max-width: 40rem;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(2rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-standard);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 0.25rem;
}

.close-btn:hover {
  color: var(--color-text);
}

.modal-body {
  padding: var(--gap-standard);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--gap-small);
  padding: var(--gap-standard);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* ==============================================
   TRANSACTION EDIT MODAL
   ============================================== */

.transaction-edit-modal {
  max-width: 35rem;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: var(--color-text-light);
  font-size: var(--text-small);
}

.form-input {
  padding: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-button);
  font-size: var(--text-medium);
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-button-active);
}

textarea.form-input {
  resize: vertical;
  min-height: 4rem;
}

/* ==============================================
   DELETE MODAL
   ============================================== */

.delete-modal {
  max-width: 30rem;
}

.delete-warning {
  display: flex;
  gap: var(--gap-standard);
  padding: var(--gap-standard);
  background: rgba(239, 68, 68, 0.05);
  border-radius: var(--radius);
}

.warning-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.warning-text p {
  margin-bottom: var(--gap-small);
}

.transaction-details {
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
  margin: var(--gap-small) 0;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ==============================================
   RESPONSIVE DESIGN
   ============================================== */

@media (max-width: 64rem) {
  .action-buttons-compact {
    position: static;
    margin-bottom: var(--gap-standard);
  }

  .transactions-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-stats {
    justify-content: center;
  }

  .pagination-controls {
    justify-content: center;
  }
  
  .bulk-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filters-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filters-row-3col {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filters-row-actions {
    grid-template-columns: 1fr;
  }
  
  .filter-actions-compact {
    justify-content: stretch;
  }
  
  .filter-actions-compact button {
    flex: 1;
  }
}

@media (max-width: 48rem) {
  .filters-row {
    grid-template-columns: 1fr;
  }
  
  .transactions-table {
    font-size: 0.75rem;
  }
  
  .transactions-table th,
  .transactions-table td {
    padding: 0.5rem;
  }
  
  .col-type,
  .col-category,
  .col-subcategory {
    display: none;
  }

  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 30rem) {
  .transactions-table-container {
    font-size: 0.6875rem;
  }
  
  .col-merchant {
    min-width: 8rem;
  }
  
  .action-buttons-compact {
    flex-wrap: wrap;
  }
}
</style>