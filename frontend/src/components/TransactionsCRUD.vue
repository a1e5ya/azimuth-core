<template>
  <div>
    <!-- Edit/Add Transaction Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content transaction-edit-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ isAddMode ? 'Add Transaction' : 'Edit Transaction' }}</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="edit-form">
            <div class="form-row">
              <div class="form-group">
                <label>Date *</label>
                <input 
                  type="date" 
                  v-model="editForm.posted_at"
                  class="form-input"
                  required
                >
              </div>
              
              <div class="form-group">
                <label>Amount *</label>
                <input 
                  type="number" 
                  v-model.number="editForm.amount"
                  class="form-input"
                  step="0.01"
                  required
                >
              </div>
            </div>
            
            <div class="form-group">
              <label>Merchant</label>
              <input 
                type="text" 
                v-model="editForm.merchant"
                class="form-input"
                placeholder="Merchant name..."
              >
            </div>
            
            <div class="form-group">
              <label>Memo</label>
              <textarea 
                v-model="editForm.memo"
                class="form-input"
                rows="2"
                placeholder="Transaction notes..."
              ></textarea>
            </div>
            
            <div class="form-group">
              <label>Owner & Account Type</label>
              <div v-if="loadingAccounts" class="loading-text">Loading accounts...</div>
              <select 
                v-else 
                v-model="selectedOwnerAccount" 
                class="form-input" 
                @change="onOwnerAccountChange"
              >
                <option value="">Select owner & account...</option>
                <optgroup 
                  v-for="group in groupedAccounts" 
                  :key="group.owner" 
                  :label="group.owner"
                >
                  <option 
                    v-for="account in group.accounts" 
                    :key="account.id" 
                    :value="`${group.owner}|${account.account_type}`"
                  >
                    {{ account.name }} ({{ account.account_type }})
                  </option>
                </optgroup>
              </select>
              <div v-if="!loadingAccounts && accounts.length === 0" class="help-text error">
                No owners/accounts found. Create accounts first in Settings.
              </div>
            </div>
            
            <div class="form-group">
              <label>Category (Type → Category → Subcategory)</label>
              <select v-model="editForm.category_id" class="form-input">
                <option value="">Select category...</option>
                <template v-for="type in categoryTree" :key="type.id">
                  <template v-for="cat in type.children" :key="cat.id">
                    <option 
                      v-for="subcat in cat.children"
                      :key="subcat.id"
                      :value="subcat.id"
                    >
                      {{ type.name }} → {{ cat.name }} → {{ subcat.name }}
                    </option>
                  </template>
                </template>
              </select>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn" 
            @click="saveEdit"
            :disabled="saving || !isFormValid"
          >
            {{ saving ? 'Saving...' : (isAddMode ? 'Add Transaction' : 'Save Changes') }}
          </button>
          <button class="btn btn-link" @click="closeEditModal" :disabled="saving">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal (Single) -->
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

    <!-- Bulk Delete Confirmation Modal -->
    <div v-if="showBulkDeleteModal" class="modal-overlay" @click="closeBulkDeleteModal">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h3>Delete Multiple Transactions</h3>
          <button class="close-btn" @click="closeBulkDeleteModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="delete-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>Are you sure you want to delete {{ bulkDeleteIds.length }} transactions?</strong></p>
              <p>This action cannot be undone.</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmBulkDelete"
            :disabled="deleting"
          >
            {{ deleting ? 'Deleting...' : `Yes, Delete ${bulkDeleteIds.length}` }}
          </button>
          <button class="btn btn-link" @click="closeBulkDeleteModal" :disabled="deleting">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
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
    
    const showEditModal = ref(false)
    const isAddMode = ref(false)
    const editingTransaction = ref(null)
    const deletingTransaction = ref(null)
    const showBulkDeleteModal = ref(false)
    const bulkDeleteIds = ref([])
    const saving = ref(false)
    const deleting = ref(false)
    const loadingAccounts = ref(false)
    const accounts = ref([])
    
    const editForm = ref({
      posted_at: '',
      amount: 0,
      merchant: '',
      memo: '',
      owner: '',
      bank_account_type: '',
      category_id: ''
    })

    const selectedOwnerAccount = ref('')

    const categoryTree = computed(() => categoryStore.categories || [])

    const groupedAccounts = computed(() => {
      const groups = {}
      for (const account of accounts.value) {
        const ownerName = account.owner.name
        if (!groups[ownerName]) {
          groups[ownerName] = {
            owner: ownerName,
            accounts: []
          }
        }
        groups[ownerName].accounts.push(account)
      }
      return Object.values(groups)
    })

    const isFormValid = computed(() => {
      return editForm.value.posted_at && editForm.value.amount !== 0
    })

    const loadAccounts = async () => {
      loadingAccounts.value = true
      try {
        const response = await axios.get(`${API_BASE}/accounts/list-simple`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        accounts.value = response.data.accounts || []
        console.log('✅ Loaded accounts:', accounts.value.length)
      } catch (error) {
        console.error('❌ Failed to load accounts:', error)
      } finally {
        loadingAccounts.value = false
      }
    }

    watch(showEditModal, (newVal) => {
      if (newVal) {
        loadAccounts()
      }
    })

    const onOwnerAccountChange = () => {
      if (!selectedOwnerAccount.value) {
        editForm.value.owner = ''
        editForm.value.bank_account_type = ''
        return
      }
      
      const [owner, accountType] = selectedOwnerAccount.value.split('|')
      editForm.value.owner = owner
      editForm.value.bank_account_type = accountType
      console.log('✅ Selected:', { owner, accountType })
    }

    const addTransaction = () => {
      isAddMode.value = true
      showEditModal.value = true
      selectedOwnerAccount.value = ''
      editForm.value = {
        posted_at: new Date().toISOString().split('T')[0],
        amount: 0,
        merchant: '',
        memo: '',
        owner: '',
        bank_account_type: '',
        category_id: ''
      }
    }

    const editTransaction = (transaction) => {
      isAddMode.value = false
      editingTransaction.value = transaction
      showEditModal.value = true
      
      // Set combined owner|account value
      if (transaction.owner && transaction.bank_account_type) {
        selectedOwnerAccount.value = `${transaction.owner}|${transaction.bank_account_type}`
      } else {
        selectedOwnerAccount.value = ''
      }
      
      editForm.value = {
        posted_at: transaction.posted_at.split('T')[0],
        amount: parseFloat(transaction.amount),
        merchant: transaction.merchant || '',
        memo: transaction.memo || '',
        owner: transaction.owner || '',
        bank_account_type: transaction.bank_account_type || '',
        category_id: transaction.category_id || ''
      }
    }

    const closeEditModal = () => {
      showEditModal.value = false
      isAddMode.value = false
      editingTransaction.value = null
      selectedOwnerAccount.value = ''
      editForm.value = {
        posted_at: '',
        amount: 0,
        merchant: '',
        memo: '',
        owner: '',
        bank_account_type: '',
        category_id: ''
      }
    }

    const saveEdit = async () => {
      if (!isFormValid.value || saving.value) return
      
      saving.value = true
      
      try {
        const token = authStore.token
        
        const data = {
          posted_at: editForm.value.posted_at,
          amount: editForm.value.amount,
          merchant: editForm.value.merchant || null,
          memo: editForm.value.memo || null,
          owner: editForm.value.owner || null,
          bank_account_type: editForm.value.bank_account_type || null,
          category_id: editForm.value.category_id || null
        }
        
        console.log('💾 Saving transaction:', data)
        
        if (isAddMode.value) {
          const response = await axios.post(
            `${API_BASE}/transactions/create`,
            data,
            {
              headers: { 'Authorization': `Bearer ${token}` }
            }
          )
          
          emit('add-chat-message', {
            message: 'Transaction added',
            response: response.data.message || 'Transaction successfully added!'
          })
        } else {
          const response = await axios.put(
            `${API_BASE}/transactions/${editingTransaction.value.id}`,
            data,
            {
              headers: { 
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache'
              }
            }
          )
          
          console.log('✅ Update response:', response.data)
          
          emit('add-chat-message', {
            message: 'Transaction updated',
            response: response.data.message || 'Transaction successfully updated!'
          })
        }
        
        closeEditModal()
        emit('transaction-updated')
        
      } catch (error) {
        console.error('❌ Failed to save transaction:', error)
        console.error('Error response:', error.response?.data)
        emit('add-chat-message', {
          response: error.response?.data?.detail || 'Failed to save transaction. Please try again.'
        })
      } finally {
        saving.value = false
      }
    }

    const deleteTransaction = (transaction) => {
      deletingTransaction.value = transaction
      console.log('🗑️ Deleting transaction:', transaction.id)
    }

    const closeDeleteModal = () => {
      deletingTransaction.value = null
    }

    const confirmDelete = async () => {
      if (!deletingTransaction.value || deleting.value) return
      
      deleting.value = true
      
      try {
        const token = authStore.token
        const transactionId = deletingTransaction.value.id
        
        console.log('🗑️ DELETE request for:', transactionId)
        
        const response = await axios.delete(
          `${API_BASE}/transactions/${transactionId}`,
          {
            headers: { 
              'Authorization': `Bearer ${token}`,
              'Cache-Control': 'no-cache'
            }
          }
        )
        
        console.log('✅ Delete response:', response.data)
        
        emit('add-chat-message', {
          message: 'Transaction deleted',
          response: 'Transaction has been permanently deleted.'
        })
        
        closeDeleteModal()
        emit('transaction-deleted')
        
      } catch (error) {
        console.error('❌ Delete failed:', error)
        emit('add-chat-message', {
          response: error.response?.data?.detail || 'Failed to delete transaction. Please try again.'
        })
      } finally {
        deleting.value = false
      }
    }

    const bulkDelete = (transactionIds) => {
      bulkDeleteIds.value = transactionIds
      showBulkDeleteModal.value = true
    }

    const closeBulkDeleteModal = () => {
      showBulkDeleteModal.value = false
      bulkDeleteIds.value = []
    }

    const confirmBulkDelete = async () => {
      if (bulkDeleteIds.value.length === 0 || deleting.value) return
      
      deleting.value = true
      
      try {
        const token = authStore.token
        
        console.log('🗑️ Bulk DELETE request for:', bulkDeleteIds.value)
        
        const response = await axios.post(
          `${API_BASE}/transactions/bulk-delete`,
          { transaction_ids: bulkDeleteIds.value },
          {
            headers: { 
              'Authorization': `Bearer ${token}`,
              'Cache-Control': 'no-cache'
            }
          }
        )
        
        console.log('✅ Bulk delete response:', response.data)
        
        emit('add-chat-message', {
          message: `Bulk delete: ${bulkDeleteIds.value.length} transactions`,
          response: `Successfully deleted ${response.data.deleted_count} transactions.`
        })
        
        closeBulkDeleteModal()
        emit('transaction-deleted')
        
      } catch (error) {
        console.error('❌ Bulk delete failed:', error)
        emit('add-chat-message', {
          response: error.response?.data?.detail || 'Failed to delete transactions. Please try again.'
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
      showEditModal,
      isAddMode,
      editingTransaction,
      deletingTransaction,
      showBulkDeleteModal,
      bulkDeleteIds,
      saving,
      deleting,
      loadingAccounts,
      accounts,
      editForm,
      selectedOwnerAccount,
      categoryTree,
      groupedAccounts,
      isFormValid,
      onOwnerAccountChange,
      addTransaction,
      editTransaction,
      closeEditModal,
      saveEdit,
      deleteTransaction,
      closeDeleteModal,
      confirmDelete,
      bulkDelete,
      closeBulkDeleteModal,
      confirmBulkDelete,
      formatDate,
      formatAmount
    }
  }
}
</script>

<style scoped>
.transaction-edit-modal {
  max-width: 40rem;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

.help-text {
  font-size: var(--text-small);
  color: var(--color-text-light);
  margin-top: 0.25rem;
}

.help-text.error {
  color: #ef4444;
}

.loading-text {
  padding: var(--gap-small);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-small);
}
</style>