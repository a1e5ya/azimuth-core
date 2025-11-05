<template>
  <div>
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
            @click="saveEdit"
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
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'

export default {
  name: 'TransactionsCRUD',
  emits: ['transaction-updated', 'transaction-deleted', 'add-chat-message'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
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

    const saveEdit = async () => {
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
        
        emit('transaction-updated')
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
        
        emit('transaction-deleted')
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

    return {
      editingTransaction,
      deletingTransaction,
      saving,
      deleting,
      editForm,
      groupedCategories,
      editTransaction,
      closeEditModal,
      saveEdit,
      deleteTransaction,
      closeDeleteModal,
      confirmDelete,
      formatDate,
      formatAmount
    }
  }
}
</script>

<style scoped>
.transaction-edit-modal {
  max-width: 35rem;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.delete-modal {
  max-width: 30rem;
}

.transaction-details {
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
  margin: var(--gap-small) 0;
}
</style>