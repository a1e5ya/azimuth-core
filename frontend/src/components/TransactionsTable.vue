<template>
  <div>
    <!-- Bulk Actions -->
    <div class="bulk-actions" v-if="selectedIds.length > 0">
      <span class="bulk-selection">{{ selectedIds.length }} selected</span>
      <select v-model="bulkCategoryId" class="bulk-category-select form-select">
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
            <th class="col-indicator"></th>
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
            <td class="col-indicator"><div 
                  v-if="getCategoryColor(transaction)"
                  class="type-indicator"
                  v-html="getTypeShape(transaction)"
                ></div></td>
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

    const getTypeShape = (transaction) => {
      const color = getCategoryColor(transaction)
      if (!color) return ''
      
      const amount = parseFloat(transaction.amount)
      
      // Income - up arrow
      if (amount > 0) {
        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 858 1000" fill="${color}"><path d="M0,995.3C142.08,666.06,284.15,336.82,429.5,0c144.66,336.09,286.58,665.83,428.5,995.57-.95,1.48-1.9,2.95-2.85,4.43-136.09-78.77-269.66-161.99-404.48-243.08-15.79-9.62-28.28-9.41-44.01.15-134.05,80.88-267.52,162.59-402.48,241.8-1.4-1.19-2.79-2.38-4.19-3.57Z"/></svg>`
      }
      // Expense - down arrow  
      else if (amount < 0) {
        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 858.01 1000" fill="${color}"><path d="M858,4.7c-142.08,329.24-284.15,658.48-429.5,995.3C283.84,663.91,141.92,334.17,0,4.43.95,2.95,1.9,1.48,2.85,0c136.09,78.77,269.66,161.99,404.48,243.08,15.79,9.62,28.28,9.41,44.01-.15C585.39,162.05,718.86,80.34,853.82,1.13c1.4,1.19,2.79,2.38,4.19,3.57h-.01Z"/></svg>`
      }
      // Transfer - right arrow
      else {
        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 858.01" fill="${color}"><path d="M4.7.01c329.24,142.08,658.48,284.15,995.3,429.5C663.91,574.17,334.17,716.09,4.43,858.01c-1.48-.95-2.95-1.9-4.43-2.85,78.77-136.09,161.99-269.66,243.08-404.48,9.62-15.79,9.41-28.28-.15-44.01C162.05,272.62,80.34,139.15,1.13,4.19,2.32,2.79,3.51,1.4,4.7,0h0Z"/></svg>`
      }
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

    const getAccountInfo = (transaction) => {
      if (transaction.bank_account && transaction.bank_account_type) {
        return `${transaction.bank_account} (${transaction.bank_account_type})`
      }
      return transaction.bank_account || transaction.bank_account_type || '-'
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
      getTypeShape,
      formatDate,
      formatAmount,
      getAmountClass,
      truncateText,
      getAccountInfo
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
  min-width: 12rem;
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
  vertical-align: center;
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
  width: 6rem;
}

.col-category {
  width: 10rem;
}

.col-type {
  width: 6rem;
}
.col-indicator {
  width: 2rem;
  text-align: center;

}


.col-actions {
  width: 2rem;
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

.type-indicator {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 1;
  filter: drop-shadow(0 1px 2px rgba(179, 179, 179, 0.2));
}

.type-indicator svg {
  width: 100%;
  height: 100%;
  opacity: 1;
}
</style>