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
</style>