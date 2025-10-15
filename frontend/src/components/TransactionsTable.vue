<template>
  <div>
    <!-- Bulk Actions -->
    <div class="bulk-actions" v-if="selectedIds.length > 0">
      <span class="bulk-selection">{{ selectedIds.length }} selected</span>
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
      <button class="btn btn-small" @click="handleBulkCategorize" :disabled="!bulkCategoryId">
        Apply Category
      </button>
      <button class="btn btn-link" @click="clearSelection">
        Clear Selection
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">⟳</div>
      <div>Loading transactions...</div>
    </div>
    
    <!-- Empty State -->
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
                :checked="allSelected"
                @change="toggleAll"
              >
            </th>
            <th class="col-date clickable" @click="$emit('sort', 'posted_at')">
              Date
              <span v-if="sortBy === 'posted_at'">
                {{ sortOrder === 'desc' ? '↓' : '↑' }}
              </span>
            </th>
            <th class="col-amount clickable" @click="$emit('sort', 'amount')">
              Amount
              <span v-if="sortBy === 'amount'">
                {{ sortOrder === 'desc' ? '↓' : '↑' }}
              </span>
            </th>
            <th class="col-merchant clickable" @click="$emit('sort', 'merchant')">
              Merchant
              <span v-if="sortBy === 'merchant'">
                {{ sortOrder === 'desc' ? '↓' : '↑' }}
              </span>
            </th>
            <th class="col-owner">Owner</th>
            <th class="col-category">Category</th>
            <th class="col-type">Type</th>
            <th class="col-actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="transaction in transactions" 
            :key="transaction.id"
            class="transaction-row"
            :class="{ 'selected': selectedIds.includes(transaction.id) }"
          >
            <td class="col-select">
              <input 
                type="checkbox" 
                :checked="selectedIds.includes(transaction.id)"
                @change="toggleSelection(transaction.id)"
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
            
            <td class="col-owner">
              <div class="owner-primary">{{ transaction.owner || '-' }}</div>
              <div class="owner-secondary">{{ transaction.bank_account_type || '-' }}</div>
            </td>
            
            <td class="col-category">
              <div class="category-primary" v-if="transaction.category">
                {{ transaction.category }}
              </div>
              <div class="category-secondary" v-if="transaction.subcategory">
                {{ transaction.subcategory }}
              </div>
              <div v-if="!transaction.category && !transaction.subcategory" class="text-muted">-</div>
            </td>
            
            <td class="col-type">
              <div class="type-text" v-if="transaction.main_category">
                {{ transaction.main_category }}
              </div>
              <div v-else class="text-muted">-</div>
            </td>
            
            <td class="col-actions">
              <div class="actions-cell">
                <ActionsMenu
                  :show-edit="true"
                  :show-add="false"
                  :show-check="false"
                  :show-delete="true"
                  @edit="$emit('edit', transaction)"
                  @delete="$emit('delete', transaction)"
                />
                <div 
                  v-if="getCategoryColor(transaction)"
                  class="color-indicator"
                  :style="{ backgroundColor: getCategoryColor(transaction) }"
                ></div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import ActionsMenu from './ActionsMenu.vue'

export default {
  name: 'TransactionsTable',
  components: {
    ActionsMenu
  },
  props: {
    transactions: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    hasActiveFilters: {
      type: Boolean,
      default: false
    },
    sortBy: {
      type: String,
      default: 'posted_at'
    },
    sortOrder: {
      type: String,
      default: 'desc'
    },
    groupedCategories: {
      type: Array,
      default: () => []
    },
    categoryTree: {
      type: Array,
      default: () => []
    }
  },
  emits: ['edit', 'delete', 'sort', 'bulk-categorize'],
  setup(props, { emit }) {
    const selectedIds = ref([])
    const bulkCategoryId = ref('')

    const allSelected = computed(() => {
      return props.transactions.length > 0 && 
             props.transactions.every(t => selectedIds.value.includes(t.id))
    })

    const toggleSelection = (id) => {
      const index = selectedIds.value.indexOf(id)
      if (index > -1) {
        selectedIds.value.splice(index, 1)
      } else {
        selectedIds.value.push(id)
      }
    }

    const toggleAll = () => {
      if (allSelected.value) {
        selectedIds.value = []
      } else {
        selectedIds.value = props.transactions.map(t => t.id)
      }
    }

    const clearSelection = () => {
      selectedIds.value = []
      bulkCategoryId.value = ''
    }

    const handleBulkCategorize = () => {
      if (!bulkCategoryId.value || selectedIds.value.length === 0) return
      
      emit('bulk-categorize', {
        transactionIds: selectedIds.value,
        categoryId: bulkCategoryId.value
      })
      
      clearSelection()
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
      
      return searchInTree(props.categoryTree)
    }

    const getCategoryColor = (transaction) => {
      if (!transaction.category_id) return null
      
      const category = findCategoryById(transaction.category_id)
      return category?.color || null
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
      if (amount > 0) {
        return 'amount-positive'
      } else if (amount < 0) {
        return 'amount-negative'
      }
      return 'amount-neutral'
    }

    const truncateText = (text, maxLength) => {
      if (!text || text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    return {
      selectedIds,
      bulkCategoryId,
      allSelected,
      toggleSelection,
      toggleAll,
      clearSelection,
      handleBulkCategorize,
      getCategoryColor,
      formatDate,
      formatAmount,
      getAmountClass,
      truncateText
    }
  }
}
</script>

<style scoped>
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

.empty-title {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.empty-subtitle {
  color: var(--color-text-muted);
}

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
  background: var(--color-background-light);
}

.transaction-row.selected {
  outline-offset: -2px;
}

.col-select {
  width: 3rem;
  text-align: center;
}

.col-date {
  width: 7rem;
}

.col-amount {
  width: 8rem;
  text-align: right;
}

.col-merchant {
  min-width: 12rem;
  max-width: 20rem;
}

.col-owner {
  width: 8rem;
}

.col-category {
  width: 12rem;
}

.col-type {
  width: 8rem;
}

.col-actions {
  width: 4rem;
  text-align: center;
}

.date-primary {
  font-weight: 600;
  margin-bottom: 0.125rem;
}

.date-secondary {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.amount-primary {
  font-weight: 600;
}

.amount-positive {
  color: var(--color-text);
}

.amount-negative {
  color: var(--color-text);
}

.amount-neutral {
  color: var(--color-text-light);
}

.merchant-primary {
  font-weight: 600;
  margin-bottom: 0.125rem;
  word-break: break-word;
}

.merchant-secondary {
  color: var(--color-text-light);
  line-height: 1.3;
}

.owner-primary {
  font-weight: 600;
  margin-bottom: 0.125rem;
}

.owner-secondary {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.category-primary {
  font-weight: 500;
  margin-bottom: 0.125rem;
}

.category-secondary {
  font-size: var(--text-small);
  color: var(--color-text-light);
}

.type-text {
  font-size: var(--text-small);
  color: var(--color-text);
}

.text-muted {
  color: var(--color-text-muted);
  font-style: italic;
}

.actions-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}
</style>