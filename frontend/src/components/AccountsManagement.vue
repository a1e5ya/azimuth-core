<template>
  <div class="accounts-management">
    <!-- Header with Add Owner Button -->
    <div class="header-with-action">
      <h3>Account Owners & Accounts</h3>
      <button class="btn btn-primary" @click="showAddOwnerModal = true">
        <AppIcon name="plus" size="small" />
        Add Owner
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">⟳</div>
      <div>Loading accounts...</div>
    </div>

    <!-- Empty State -->
    <div v-else-if="owners.length === 0" class="empty-state">
      <AppIcon name="credit-card" size="large" />
      <div>No account owners yet</div>
      <div class="text-small">Create an owner to start managing accounts</div>
    </div>

    <!-- Owners List -->
    <div v-else class="owners-list">
      <div 
        v-for="owner in owners" 
        :key="owner.id" 
        class="owner-card"
      >
        <!-- Owner Header -->
        <div class="owner-header">
          <div class="owner-info">
            <div 
              class="owner-color-badge" 
              :style="{ backgroundColor: owner.color || '#94a3b8' }"
            ></div>
            <div>
              <div class="owner-name">{{ owner.name }}</div>
              <div class="owner-meta">
                {{ owner.accounts.length }} account{{ owner.accounts.length !== 1 ? 's' : '' }}
              </div>
            </div>
          </div>
          
          <ActionsMenu
            :show-add="true"
            :show-edit="true"
            :show-delete="true"
            :show-check="false"
            menu-title="Owner Actions"
            @add="showAddAccountModal(owner)"
            @edit="editOwner(owner)"
            @delete="confirmDeleteOwner(owner)"
            class="always-visible"
          />
        </div>

        <!-- Accounts List -->
        <div v-if="owner.accounts.length > 0" class="accounts-list">
          <div 
            v-for="account in owner.accounts" 
            :key="account.id"
            class="account-item"
          >
            <div class="account-info-row">
              <div class="account-details">
                <AppIcon name="credit-card" size="small" />
                <div>
                  <div class="account-name">{{ account.name }}</div>
                  <div class="account-type">{{ account.account_type }}</div>
                </div>
              </div>
              
              <div class="account-balance">
                {{ formatCurrency(account.current_balance) }}
              </div>

              <div class="account-actions">
                <button 
                  class="btn-icon" 
                  @click="importToAccount(account, owner)"
                  title="Import transactions"
                >
                  <AppIcon name="upload" size="small" />
                </button>
                
                <ActionsMenu
                  :show-add="false"
                  :show-edit="true"
                  :show-delete="true"
                  :show-check="false"
                  menu-title="Account Actions"
                  @edit="editAccount(account, owner)"
                  @delete="confirmDeleteAccount(account, owner)"
                />
              </div>
            </div>

            <div v-if="account.institution" class="account-institution">
              {{ account.institution }}
            </div>
          </div>
        </div>

        <!-- Empty Accounts State -->
        <div v-else class="empty-accounts">
          <div class="text-small">No accounts yet</div>
          <button 
            class="btn btn-small" 
            @click="showAddAccountModal(owner)"
          >
            Add Account
          </button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Owner Modal -->
    <div v-if="showAddOwnerModal || editingOwner" class="modal-overlay" @click="closeOwnerModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingOwner ? 'Edit Owner' : 'Add Owner' }}</h3>
          <button class="close-btn" @click="closeOwnerModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Owner Name *</label>
            <input 
              type="text" 
              v-model="ownerForm.name"
              class="form-input"
              placeholder="e.g., Egor, Alex, Lila"
              maxlength="50"
            >
          </div>
          
          <div class="form-group">
            <label>Color (Optional)</label>
            <div class="color-picker">
              <input 
                type="color" 
                v-model="ownerForm.color"
                class="color-input"
              >
              <input 
                type="text" 
                v-model="ownerForm.color"
                class="form-input"
                placeholder="#3b82f6"
                maxlength="7"
              >
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-primary" 
            @click="saveOwner"
            :disabled="!ownerForm.name || saving"
          >
            {{ saving ? 'Saving...' : (editingOwner ? 'Update' : 'Create') }}
          </button>
          <button class="btn btn-link" @click="closeOwnerModal" :disabled="saving">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Account Modal -->
    <div v-if="showAccountModal || editingAccount" class="modal-overlay" @click="closeAccountModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingAccount ? 'Edit Account' : 'Add Account' }}</h3>
          <button class="close-btn" @click="closeAccountModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Account Name *</label>
            <input 
              type="text" 
              v-model="accountForm.name"
              class="form-input"
              placeholder="e.g., Main Account, Savings"
            >
          </div>
          
          <div class="form-group">
            <label>Account Type *</label>
            <select v-model="accountForm.account_type" class="form-input">
              <option value="">Select type...</option>
              <option value="Main">Main</option>
              <option value="Kopio">Kopio</option>
              <option value="Reserv">Reserv</option>
              <option value="BSP">BSP</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Institution (Optional)</label>
            <input 
              type="text" 
              v-model="accountForm.institution"
              class="form-input"
              placeholder="e.g., Bank Name"
            >
          </div>
          
          <div class="form-group">
            <label>Current Balance (Optional)</label>
            <input 
              type="number" 
              v-model.number="accountForm.current_balance"
              class="form-input"
              step="0.01"
              placeholder="0.00"
            >
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-primary" 
            @click="saveAccount"
            :disabled="!accountForm.name || !accountForm.account_type || saving"
          >
            {{ saving ? 'Saving...' : (editingAccount ? 'Update' : 'Create') }}
          </button>
          <button class="btn btn-link" @click="closeAccountModal" :disabled="saving">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Owner Confirmation -->
    <div v-if="deletingOwner" class="modal-overlay" @click="closeDeletingOwner">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h3>Delete Owner</h3>
          <button class="close-btn" @click="closeDeletingOwner">×</button>
        </div>
        
        <div class="modal-body">
          <div class="delete-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>Are you sure you want to delete {{ deletingOwner.name }}?</strong></p>
              <p v-if="deletingOwner.accounts.length > 0">
                This will also delete <strong>{{ deletingOwner.accounts.length }} account(s)</strong> 
                and all associated transactions.
              </p>
              <p>This action cannot be undone.</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="deleteOwner"
            :disabled="deleting"
          >
            {{ deleting ? 'Deleting...' : 'Yes, Delete' }}
          </button>
          <button class="btn btn-link" @click="closeDeletingOwner" :disabled="deleting">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Account Confirmation -->
    <div v-if="deletingAccount" class="modal-overlay" @click="closeDeletingAccount">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h3>Delete Account</h3>
          <button class="close-btn" @click="closeDeletingAccount">×</button>
        </div>
        
        <div class="modal-body">
          <div class="delete-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>Delete {{ deletingAccount.account.name }}?</strong></p>
              <p>Owner: {{ deletingAccount.owner.name }}</p>
              <p v-if="deletingAccount.account.transaction_count > 0">
                This account has <strong>{{ deletingAccount.account.transaction_count }} transaction(s)</strong>.
              </p>
              <p>This action cannot be undone.</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="deleteAccount"
            :disabled="deleting"
          >
            {{ deleting ? 'Deleting...' : 'Yes, Delete' }}
          </button>
          <button class="btn btn-link" @click="closeDeletingAccount" :disabled="deleting">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Import File Input (Hidden) -->
    <input 
      ref="fileInput" 
      type="file" 
      accept=".csv,.xlsx"
      @change="handleFileSelect"
      style="display: none"
    >
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import AppIcon from './AppIcon.vue'
import ActionsMenu from './ActionsMenu.vue'

export default {
  name: 'AccountsManagement',
  components: {
    AppIcon,
    ActionsMenu
  },
  emits: ['import-success'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    
    const loading = ref(false)
    const saving = ref(false)
    const deleting = ref(false)
    const owners = ref([])
    
    // Modals
    const showAddOwnerModal = ref(false)
    const showAccountModal = ref(false)
    const editingOwner = ref(null)
    const editingAccount = ref(null)
    const selectedOwner = ref(null)
    const deletingOwner = ref(null)
    const deletingAccount = ref(null)
    
    // Forms
    const ownerForm = ref({
      name: '',
      color: '#3b82f6'
    })
    
    const accountForm = ref({
      owner_id: '',
      name: '',
      account_type: '',
      institution: '',
      current_balance: 0
    })
    
    // File import
    const fileInput = ref(null)
    const importingAccount = ref(null)
    const importingOwner = ref(null)

    async function loadOwners() {
      if (!authStore.token) return
      
      loading.value = true
      
      try {
        const response = await axios.get(`${API_BASE}/owners/`, {
          headers: { 'Authorization': `Bearer ${authStore.token}` }
        })
        
        owners.value = response.data
        console.log('Loaded owners:', owners.value.length)
        
      } catch (error) {
        console.error('Failed to load owners:', error)
      } finally {
        loading.value = false
      }
    }

    // Owner CRUD
    function showAddAccountModal(owner) {
      selectedOwner.value = owner
      accountForm.value = {
        owner_id: owner.id,
        name: '',
        account_type: '',
        institution: '',
        current_balance: 0
      }
      showAccountModal.value = true
    }

    function editOwner(owner) {
      editingOwner.value = owner
      ownerForm.value = {
        name: owner.name,
        color: owner.color || '#3b82f6'
      }
    }

    function closeOwnerModal() {
      showAddOwnerModal.value = false
      editingOwner.value = null
      ownerForm.value = {
        name: '',
        color: '#3b82f6'
      }
    }

    async function saveOwner() {
      if (!ownerForm.value.name || saving.value) return
      
      saving.value = true
      
      try {
        if (editingOwner.value) {
          // Update
          await axios.put(
            `${API_BASE}/owners/${editingOwner.value.id}`,
            ownerForm.value,
            { headers: { 'Authorization': `Bearer ${authStore.token}` } }
          )
        } else {
          // Create
          await axios.post(
            `${API_BASE}/owners/`,
            ownerForm.value,
            { headers: { 'Authorization': `Bearer ${authStore.token}` } }
          )
        }
        
        await loadOwners()
        closeOwnerModal()
        
      } catch (error) {
        console.error('Failed to save owner:', error)
        alert(error.response?.data?.detail || 'Failed to save owner')
      } finally {
        saving.value = false
      }
    }

    function confirmDeleteOwner(owner) {
      deletingOwner.value = owner
    }

    function closeDeletingOwner() {
      deletingOwner.value = null
    }

    async function deleteOwner() {
      if (!deletingOwner.value || deleting.value) return
      
      deleting.value = true
      
      try {
        const force = deletingOwner.value.accounts.length > 0
        
        await axios.delete(
          `${API_BASE}/owners/${deletingOwner.value.id}?force=${force}`,
          { headers: { 'Authorization': `Bearer ${authStore.token}` } }
        )
        
        await loadOwners()
        closeDeletingOwner()
        
      } catch (error) {
        console.error('Failed to delete owner:', error)
        alert(error.response?.data?.detail || 'Failed to delete owner')
      } finally {
        deleting.value = false
      }
    }

    // Account CRUD
    function editAccount(account, owner) {
      editingAccount.value = account
      selectedOwner.value = owner
      accountForm.value = {
        owner_id: owner.id,
        name: account.name,
        account_type: account.account_type,
        institution: account.institution || '',
        current_balance: account.current_balance || 0
      }
    }

    function closeAccountModal() {
      showAccountModal.value = false
      editingAccount.value = null
      selectedOwner.value = null
      accountForm.value = {
        owner_id: '',
        name: '',
        account_type: '',
        institution: '',
        current_balance: 0
      }
    }

    async function saveAccount() {
      if (!accountForm.value.name || !accountForm.value.account_type || saving.value) return
      
      saving.value = true
      
      try {
        if (editingAccount.value) {
          // Update
          await axios.put(
            `${API_BASE}/accounts/${editingAccount.value.id}`,
            accountForm.value,
            { headers: { 'Authorization': `Bearer ${authStore.token}` } }
          )
        } else {
          // Create
          await axios.post(
            `${API_BASE}/accounts/`,
            accountForm.value,
            { headers: { 'Authorization': `Bearer ${authStore.token}` } }
          )
        }
        
        await loadOwners()
        closeAccountModal()
        
      } catch (error) {
        console.error('Failed to save account:', error)
        alert(error.response?.data?.detail || 'Failed to save account')
      } finally {
        saving.value = false
      }
    }

    function confirmDeleteAccount(account, owner) {
      deletingAccount.value = {
        account,
        owner
      }
    }

    function closeDeletingAccount() {
      deletingAccount.value = null
    }

    async function deleteAccount() {
      if (!deletingAccount.value || deleting.value) return
      
      deleting.value = true
      
      try {
        const force = deletingAccount.value.account.transaction_count > 0
        
        await axios.delete(
          `${API_BASE}/accounts/${deletingAccount.value.account.id}?force=${force}`,
          { headers: { 'Authorization': `Bearer ${authStore.token}` } }
        )
        
        await loadOwners()
        closeDeletingAccount()
        
      } catch (error) {
        console.error('Failed to delete account:', error)
        alert(error.response?.data?.detail || 'Failed to delete account')
      } finally {
        deleting.value = false
      }
    }

    // Import to account
    function importToAccount(account, owner) {
      importingAccount.value = account
      importingOwner.value = owner
      fileInput.value.click()
    }

    async function handleFileSelect(event) {
      const file = event.target.files[0]
      if (!file) return
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('auto_categorize', 'true')
      
      loading.value = true
      
      try {
        await axios.post(
          `${API_BASE}/accounts/${importingAccount.value.id}/import`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        )
        
        alert(`Successfully imported to ${importingOwner.value.name} - ${importingAccount.value.name}`)
        emit('import-success')
        await loadOwners()
        
      } catch (error) {
        console.error('Import failed:', error)
        alert(error.response?.data?.detail || 'Import failed')
      } finally {
        loading.value = false
        event.target.value = ''
        importingAccount.value = null
        importingOwner.value = null
      }
    }

    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(amount)
    }

    onMounted(() => {
      loadOwners()
    })

    return {
      loading,
      saving,
      deleting,
      owners,
      showAddOwnerModal,
      showAccountModal,
      editingOwner,
      editingAccount,
      deletingOwner,
      deletingAccount,
      ownerForm,
      accountForm,
      fileInput,
      showAddAccountModal,
      editOwner,
      closeOwnerModal,
      saveOwner,
      confirmDeleteOwner,
      closeDeletingOwner,
      deleteOwner,
      editAccount,
      closeAccountModal,
      saveAccount,
      confirmDeleteAccount,
      closeDeletingAccount,
      deleteAccount,
      importToAccount,
      handleFileSelect,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.accounts-management {
  width: 100%;
}

.header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
}

.header-with-action h3 {
  margin: 0;
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
  margin-bottom: var(--gap-small);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.owners-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.owner-card {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
}

.owner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  padding-bottom: var(--gap-standard);
  border-bottom: 1px solid var(--color-background-dark);
}

.owner-info {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.owner-color-badge {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  flex-shrink: 0;
}

.owner-name {
  font-size: var(--text-medium);
  font-weight: 600;
  color: var(--color-text);
}

.owner-meta {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.accounts-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.account-item {
  background: var(--color-background-dark);
  border-radius: var(--radius);
  padding: var(--gap-small);
}

.account-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--gap-small);
}

.account-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.account-name {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.account-type {
  font-size: 0.6875rem;
  color: var(--color-text-muted);
}

.account-balance {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.account-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.btn-icon {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  transition: background 0.2s;
  color: var(--color-text-light);
}

.btn-icon:hover {
  background: var(--color-background-light);
  color: var(--color-text);
}

.account-institution {
  margin-top: 0.25rem;
  padding-top: 0.25rem;
  border-top: 1px solid var(--color-background-light);
  font-size: 0.6875rem;
  color: var(--color-text-muted);
}

.empty-accounts {
  text-align: center;
  padding: var(--gap-small);
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
  align-items: center;
}

/* Modal Styles */
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
  max-width: 35rem;
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: var(--gap-standard);
}

.form-group:last-child {
  margin-bottom: 0;
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

.color-picker {
  display: flex;
  gap: var(--gap-small);
  align-items: center;
}

.color-input {
  width: 3rem;
  height: 2.5rem;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  cursor: pointer;
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

.warning-text p:last-child {
  margin-bottom: 0;
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