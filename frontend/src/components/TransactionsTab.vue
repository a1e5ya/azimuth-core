<template>
  <div class="tab-content">
    <!-- Top Cards Section -->
    <div class="grid grid-3">
      <!-- Import Card -->
      <div class="container">
        <div class="import-section">
          <div 
            class="drop-zone" 
            @click="triggerFileUpload"
            @drop.prevent="handleFileDrop"
            @dragover.prevent
            @dragenter.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            :class="{ 'drag-active': isDragging }"
          >
            <div class="drop-zone-content">
              <div class="upload-text">
                <div class="import-header">
                  <h3>Import Transactions</h3>
                </div>
              </div>
            </div>
            <input 
              ref="fileInput" 
              type="file" 
              accept=".csv,.xlsx" 
              multiple 
              @change="handleFileSelect" 
              style="display: none;"
            >
          </div>
        </div>
      </div>

      <!-- Transaction Count Card -->
      <div class="container stat-card">
        <div class="stat-label">Total Transactions</div>
        <div class="stat-value">{{ summary?.total_transactions?.toLocaleString() || 0 }}</div>
        <div class="stat-detail">
          <span v-if="summary?.categorized_count">
            {{ summary.categorized_count }} categorized
          </span>
        </div>
      </div>

      <!-- Reset Card -->
      <div class="container stat-card">
        <div class="stat-detail">
          <button class="btn btn-danger" @click="showResetModal = true" v-if="summary && summary.total_transactions > 0">
            Reset All Data
          </button>
          <span v-else class="text-muted">No data to reset</span>
        </div>
      </div>
    </div>

    <!-- Upload Progress -->
    <div class="container" v-if="localUploads.length > 0">
      <div class="upload-progress">
        <h4>Upload Progress</h4>
        <div class="upload-items">
          <div v-for="upload in localUploads" :key="upload.id" class="upload-item" :class="upload.status">
            <div class="upload-status-icon">
              <span v-if="upload.status === 'success'">✅</span>
              <span v-else-if="upload.status === 'error'">❌</span>
              <span v-else class="loading-spinner">⟳</span>
            </div>
            <div class="upload-details">
              <div class="upload-filename">{{ upload.filename }}</div>
              <div class="upload-info">
                <span class="upload-time">{{ upload.timestamp }}</span>
                <span v-if="upload.status === 'processing'" class="upload-status"> • Processing...</span>
                <span v-else-if="upload.status === 'success'" class="upload-status"> • {{ upload.rows }} rows imported</span>
                <span v-else-if="upload.status === 'error'" class="upload-status"> • Upload failed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transactions Table with Filters -->
    <div class="container">
      <!-- Table Header with Controls -->
      <div class="transactions-header">
        <div class="header-info">
          <h3>Transaction History</h3>
          <span class="transaction-count">({{ summary?.total_transactions || 0 }} total)</span>
        </div>
              <!-- Pagination -->

        
        <div class="pagination-controls">
          <select v-model.number="pageSize" @change="changePageSize" class="page-size-select">
            <option :value="25">25 per page</option>
            <option :value="50">50 per page</option>
            <option :value="100">100 per page</option>
            <option :value="200">200 per page</option>
          </select>
          
          <button 
            class="btn btn-small" 
            @click="changePage(currentPage - 1)"
            :disabled="currentPage <= 1"
          >
            Previous
          </button>
          
          <span class="page-indicator">Page {{ currentPage }}</span>
          
          <button 
            class="btn btn-small" 
            @click="changePage(currentPage + 1)"
            :disabled="transactions.length < pageSize"
          >
            Next
          </button>
        </div>
        <div class="header-actions">
          <button 
            class="btn btn-small" 
            @click="$emit('update:showFilters', !showFilters)" 
            :class="{ 'btn-active': showFilters }"
          >
            Filters {{ hasActiveFilters ? '(Active)' : '' }}
          </button>
          <button class="btn btn-small" @click="refreshTransactions" :disabled="loading">
            Refresh
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
                'selected': selectedTransactions.includes(transaction.id),
                'auto-categorizing': categorizingTransactions.includes(transaction.id)
              }"
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

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="modal-overlay" @click="showResetModal = false">
      <div class="modal-content reset-modal" @click.stop>
        <div class="modal-header">
          <h3>Reset All Transaction Data</h3>
        </div>
        
        <div class="modal-body">
          <div class="reset-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>This action cannot be undone!</strong></p>
              <p>This will permanently delete all {{ summary?.total_transactions || 0 }} transactions.</p>
              <p>Are you sure you want to continue?</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmReset"
            :disabled="resetting"
          >
            {{ resetting ? 'Resetting...' : 'Yes, Reset All Data' }}
          </button>
          <button class="btn btn-link" @click="showResetModal = false" :disabled="resetting">
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

export default {
  name: 'TransactionsTab',
  components: {
    ActionsMenu
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
    const categorizingTransactions = ref([])
    
    const showResetModal = ref(false)
    const resetting = ref(false)
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

    const triggerFileUpload = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const files = event.target.files
      processFiles(files)
      event.target.value = ''
    }

    const handleFileDrop = (event) => {
      isDragging.value = false
      const files = event.dataTransfer.files
      processFiles(files)
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
          response: `Processing ${file.name}... CSV categories will be imported and displayed directly.`
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
          
          const duplicatesMsg = response.data.summary.rows_duplicated ? 
            ` (${response.data.summary.rows_duplicated} duplicates skipped)` : ''
          
          emit('add-chat-message', {
            message: `File uploaded: ${file.name}`,
            response: `Successfully imported ${file.name} with ${upload.rows} transactions!${duplicatesMsg} All CSV category data has been preserved.`
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
          } else if (error.code === 'ECONNABORTED') {
            errorMessage = 'Upload timeout. Please try with a smaller file.'
          }
          
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: `${errorMessage}`
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
        const pageSize = 1000
        
        while (hasMore && page <= 10) {
          const response = await axios.get(`${API_BASE}/transactions/list`, {
            params: {
              page: page,
              limit: pageSize
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
              
              if (t.csv_category) {
                const key = `${t.main_category}|${t.csv_category}`
                cats.set(key, {
                  main: t.main_category,
                  name: t.csv_category
                })
                
                if (t.csv_subcategory) {
                  const subKey = `${t.main_category}|${t.csv_category}|${t.csv_subcategory}`
                  subCats.set(subKey, {
                    main: t.main_category,
                    category: t.csv_category,
                    name: t.csv_subcategory
                  })
                }
              }
            }
          })
          
          if (pageTransactions.length < pageSize) {
            hasMore = false
          }
          
          page++
        }
        
        csvMainCategories.value = Array.from(mainCats).sort()
        csvCategories.value = Array.from(cats.values())
        csvSubcategories.value = Array.from(subCats.values())
        
        console.log('Loaded filter options:', {
          types: csvMainCategories.value.length,
          categories: csvCategories.value.length,
          subcategories: csvSubcategories.value.length,
          pagesLoaded: page - 1
        })
        
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
        console.log('Loaded transaction summary:', response.data)
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
          // Load all transactions in batches when CSV filter is active
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
          
          // Filter by CSV categories
          let filtered = allTransactions.filter(t => {
            if (filters.value.typeFilter && t.main_category !== filters.value.typeFilter) {
              return false
            }
            
            if (filters.value.categoryFilter && t.csv_category !== filters.value.categoryFilter) {
              return false
            }
            
            if (filters.value.subcategoryFilter && t.csv_subcategory !== filters.value.subcategoryFilter) {
              return false
            }
            
            return true
          })
          
          // Apply pagination to filtered results
          const start = (currentPage.value - 1) * pageSize.value
          const end = start + pageSize.value
          transactions.value = filtered.slice(start, end)
          
          console.log('Loaded transactions (filtered):', transactions.value.length, 'of', filtered.length)
        } else {
          // Normal backend pagination when no CSV filter
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
          
          console.log('Loaded transactions:', transactions.value.length)
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

    const confirmReset = async () => {
      if (resetting.value) return
      
      resetting.value = true
      
      try {
        const token = authStore.token
        
        await axios.post(`${API_BASE}/transactions/reset`, {
          action: 'reset_all',
          confirm: true
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        transactions.value = []
        summary.value = null
        selectedTransactions.value = []
        localUploads.value = []
        
        emit('add-chat-message', {
          message: 'Reset all transaction data',
          response: 'All transaction data has been successfully reset.'
        })
        
        showResetModal.value = false
        
      } catch (error) {
        console.error('Reset failed:', error)
        
        emit('add-chat-message', {
          response: 'Reset feature is not yet implemented on the server.'
        })
      } finally {
        resetting.value = false
      }
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

    const getCategoryHierarchy = (category) => {
      const hierarchy = {
        type: null,
        category: null,
        subcategory: null
      }
      
      if (!category) return hierarchy
      
      let current = category
      
      if (current.parent_id) {
        const parent = findCategoryById(current.parent_id)
        
        if (parent && parent.parent_id) {
          hierarchy.subcategory = current
          hierarchy.category = parent
          hierarchy.type = findCategoryById(parent.parent_id)
        } else if (parent) {
          hierarchy.category = current
          hierarchy.type = parent
        }
      } else {
        hierarchy.type = current
      }
      
      return hierarchy
    }

    const getCategoryType = (transaction) => {
      if (!transaction.main_category) return null
      return transaction.main_category
    }

    const getCategoryName = (transaction) => {
      if (!transaction.csv_category) return null
      return transaction.csv_category
    }

    const getSubcategoryName = (transaction) => {
      if (!transaction.csv_subcategory) return null
      return transaction.csv_subcategory
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
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
      }).format(Math.abs(num))
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
      categorizingTransactions,
      allVisibleTransactionsSelected,
      showResetModal,
      resetting,
      editingTransaction,
      deletingTransaction,
      saving,
      deleting,
      editForm,
      groupedCategories,
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
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
      confirmReset,
      findCategoryById,
      getCategoryHierarchy,
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
/* Compact Filters Panel */
.filters-panel-compact {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  animation: slideDown 0.3s ease;
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
  grid-template-columns: 2fr 1fr;
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
}

/* Table improvements */
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

.category-text {
  font-size: var(--text-small);
  color: var(--color-text);
}

.type-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--color-background-light);
  border-radius: var(--radius);
  font-size: var(--text-small);
  font-weight: 500;
  text-transform: capitalize;
}

/* Edit and Delete Modals */
.transaction-edit-modal {
  max-width: 35rem;
}

.delete-modal {
  max-width: 30rem;
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

/* Responsive */
@media (max-width: 64rem) {
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
  
  .col-type,
  .col-category,
  .col-subcategory {
    display: none;
  }
}
</style>