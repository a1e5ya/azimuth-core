<!--
  Dashboard Accounts Management - Owner and account CRUD with stats display
  
  Hierarchical structure: Owners → Accounts → Transactions
  
  Features:
  - Owner management: Create/edit/delete owners with color coding
  - Account management: Create/edit/delete accounts under owners
  - Financial stats: Real-time income/expenses/transfers/balance per account
  - CSV/XLSX import: Direct file upload to specific accounts
  - Delete safety: Confirmation dialogs with cascade warnings
  - Stats computation: Automatic aggregation from filteredTransactions
  
  Import workflow:
  - User clicks import icon on account card
  - Hidden file input triggered programmatically
  - Multi-format support (CSV/XLSX, Finnish/Swedish/English)
  - Auto-categorization with LLM during import
  - Progress/results sent to chat via emit
  
  Layout: 3-column grid of owner sections, each containing account cards
-->
<template>
  <div class="container">
    <!-- Header with add owner button -->
    <div class="header-with-action">
      <h3>Account Owners & Accounts</h3>
      <button class=" btn-plus" @click="showAddOwnerModal = true">
        <AppIcon name="plus" size="medium" />
      </button>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">⟳</div>
      <div>Loading...</div>
    </div>
    
    <!-- Empty State -->
<div v-else-if="owners.length === 0" class="empty-state">
  <div>No account owners yet</div>
</div>
    
    <!-- Owners & Accounts List -->
    <div v-else class="accounts-grid">
      <div 
        v-for="owner in ownersWithStats" 
        :key="owner.id" 
        class="owner-section"
      >
        <!-- Owner Header with Actions -->
        <div class="owner-header">
          <div class="owner-info">
            <div class="owner-name">{{ owner.name }}</div>
            <div class="owner-meta">
              {{ owner.accounts.length }} account{{ owner.accounts.length !== 1 ? 's' : '' }}
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

        <!-- Accounts Grid -->
        <div v-if="owner.accounts.length > 0" class="accounts-grid-row">
          <div 
            v-for="account in owner.accounts" 
            :key="account.id"
            class="account-card"
          >
            <!-- Account Header -->
            <div class="account-card-header">
              <div class="account-info">
                <button 
                  class="btn-icon" 
                  @click="importToAccount(account, owner)"
                  title="Import transactions"
                >
                  <AppIcon name="file-add" size="medium" />
                </button>
                <div>
                  <div class="account-name">{{ account.name || account.account_type }}</div>
                </div>
              </div>

              <div class="account-actions">
                
                <ActionsMenu
                  :show-add="false"
                  :show-edit="true"
                  :show-delete="true"
                  :show-check="false"
                  @edit="editAccount(account, owner)"
                  @delete="confirmDeleteAccount(account, owner)"
                />
              </div>
            </div>

            <!-- Financial Stats -->
            <div class="account-stats">
              <div class="stat-item">
                <span class="stat-label">Income:</span>
                <span class="stat-value">{{ formatCurrency(account.stats.income) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Expenses:</span>
                <span class="stat-value">{{ formatCurrency(account.stats.expenses) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Transfers:</span>
                <span class="stat-value">{{ formatCurrency(account.stats.transfers) }}</span>
              </div>
              <div class="stat-item stat-total">
                <span class="stat-label">Balance:</span>
                <span class="stat-value">{{ formatCurrency(account.stats.balance) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty Accounts for Owner -->
        <div v-else class="empty-accounts">
          <div class="text-small">No accounts for {{ owner.name }}</div>
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
    <teleport to="body">
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
                placeholder=""
                maxlength="50"
              >
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
    </teleport>

    <!-- Add/Edit Account Modal -->
    <teleport to="body">
      <div v-if="showAccountModal || editingAccount" class="modal-overlay" @click="closeAccountModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>{{ editingAccount ? 'Edit Account' : 'Add Account' }}</h3>
            <button class="close-btn" @click="closeAccountModal">×</button>
          </div>
          
          <div class="modal-body">
            <div class="form-group">
              <label>Account Name (Optional)</label>
              <input 
                type="text" 
                v-model="accountForm.name"
                class="form-input"
                placeholder="Leave empty to use account type as name"
              >
            </div>
            
            <div class="form-group">
              <label>Account Type *</label>
              <select v-model="accountForm.account_type" class="form-input">
                <option value="">Select type...</option>
                <option value="Main">Main</option>
                <option value="Kopio">Kopilka</option>
                <option value="Reserv">Reserv</option>
                <option value="BSP">BSP</option>
              </select>
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
              :disabled="!accountForm.account_type || saving"
            >
              {{ saving ? 'Saving...' : (editingAccount ? 'Update' : 'Create') }}
            </button>
            <button class="btn btn-link" @click="closeAccountModal" :disabled="saving">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Delete Owner Confirmation -->
    <teleport to="body">
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
                <p><strong>Delete {{ deletingOwner.name }}?</strong></p>
                <p v-if="deletingOwner.accounts.length > 0">
                  This will delete <strong>{{ deletingOwner.accounts.length }} account(s)</strong> 
                  and all transactions.
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
    </teleport>

    <!-- Delete Account Confirmation -->
    <teleport to="body">
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
                <p><strong>Delete {{ deletingAccount.account.name || deletingAccount.account.account_type }}?</strong></p>
                <p>Owner: {{ deletingAccount.owner.name }}</p>
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
    </teleport>

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
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import AppIcon from './AppIcon.vue'
import ActionsMenu from './ActionsMenu.vue'

export default {
  name: 'DashboardAccountsManagement',
  components: {
    AppIcon,
    ActionsMenu
  },
  props: {
    /**
     * Filtered transactions from parent (for stats computation)
     * @type {Array}
     */
    filteredTransactions: {
      type: Array,
      required: true
    }
  },
  emits: [
    /**
     * Import success notification
     */
    'import-success',
    /**
     * Open import modal request
     */
    'open-import',
    /**
     * Add message to chat
     * @param {Object} payload - {message: string, response: string}
     */
    'add-chat-message'
  ],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    
    /** Loading state for data fetching */
    const loading = ref(false)
    /** Saving state for create/update operations */
    const saving = ref(false)
    /** Deleting state for delete operations */
    const deleting = ref(false)
    /** List of owners with nested accounts */
    const owners = ref([])
    
    /** Show add owner modal */
    const showAddOwnerModal = ref(false)
    /** Show add/edit account modal */
    const showAccountModal = ref(false)
    /** Currently editing owner */
    const editingOwner = ref(null)
    /** Currently editing account */
    const editingAccount = ref(null)
    /** Selected owner for account operations */
    const selectedOwner = ref(null)
    /** Owner pending deletion */
    const deletingOwner = ref(null)
    /** Account pending deletion with owner reference */
    const deletingAccount = ref(null)
    
    /** Owner form data */
    const ownerForm = ref({
      name: '',
      color: '#3b82f6'
    })
    
    /** Account form data */
    const accountForm = ref({
      owner_id: '',
      name: '',
      account_type: '',
      institution: '',
      current_balance: 0
    })
    
    /** Hidden file input reference for import */
    const fileInput = ref(null)
    /** Account receiving imported transactions */
    const importingAccount = ref(null)
    /** Owner of importing account (for display) */
    const importingOwner = ref(null)

    /**
     * Compute owners with account stats from filteredTransactions
     * Aggregates income/expenses/transfers per account
     * @returns {Array} Owners with enriched account stats
     */
    const ownersWithStats = computed(() => {
      return owners.value.map(owner => {
        const accountsWithStats = owner.accounts.map(account => {
          const accountTransactions = props.filteredTransactions.filter(
            tx => tx.account_id === account.id
          )

          let income = 0
          let expenses = 0
          let transfers = 0

          accountTransactions.forEach(tx => {
            const amount = Math.abs(parseFloat(tx.amount))
            const mainCategory = (tx.main_category || '').toUpperCase().trim()

            if (mainCategory === 'INCOME') {
              income += amount
            } else if (mainCategory === 'EXPENSES') {
              expenses += amount
            } else if (mainCategory === 'TRANSFERS') {
              transfers += amount
            }
          })

          return {
            ...account,
            stats: {
              income,
              expenses,
              transfers,
              balance: account.current_balance || (income - expenses),
              transactionCount: accountTransactions.length
            }
          }
        })

        return {
          ...owner,
          accounts: accountsWithStats
        }
      })
    })

    /**
     * Load all owners with nested accounts from API
     */
    async function loadOwners() {
      if (!authStore.token) return
      
      loading.value = true
      
      try {
        const response = await axios.get(`${API_BASE}/owners/`, {
          headers: { 'Authorization': `Bearer ${authStore.token}` }
        })
        
        owners.value = response.data
        
      } catch (error) {
        console.error('❌ Failed to load owners:', error)
      } finally {
        loading.value = false
      }
    }

    /**
     * Show add account modal for specific owner
     * @param {Object} owner - Owner object
     */
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

    /**
     * Open edit owner modal with pre-filled data
     * @param {Object} owner - Owner to edit
     */
    function editOwner(owner) {
      editingOwner.value = owner
      ownerForm.value = {
        name: owner.name,
        color: owner.color || '#3b82f6'
      }
    }

    /**
     * Close owner modal and reset form
     */
    function closeOwnerModal() {
      showAddOwnerModal.value = false
      editingOwner.value = null
      ownerForm.value = {
        name: '',
        color: '#3b82f6'
      }
    }

    /**
     * Save owner (create or update)
     * Sends POST for new, PUT for existing
     */
    async function saveOwner() {
      if (!ownerForm.value.name || saving.value) return
      
      saving.value = true
      
      try {
        if (editingOwner.value) {
          await axios.put(
            `${API_BASE}/owners/${editingOwner.value.id}`,
            ownerForm.value,
            { headers: { 'Authorization': `Bearer ${authStore.token}` } }
          )
        } else {
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

    /**
     * Show delete owner confirmation dialog
     * @param {Object} owner - Owner to delete
     */
    function confirmDeleteOwner(owner) {
      deletingOwner.value = owner
    }

    /**
     * Close delete owner dialog
     */
    function closeDeletingOwner() {
      deletingOwner.value = null
    }

    /**
     * Delete owner (cascade deletes accounts if force=true)
     */
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

    /**
     * Open edit account modal with pre-filled data
     * @param {Object} account - Account to edit
     * @param {Object} owner - Account's owner
     */
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

    /**
     * Close account modal and reset form
     */
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

    /**
     * Save account (create or update)
     * Sends POST for new, PUT for existing
     */
    async function saveAccount() {
      if (!accountForm.value.account_type || saving.value) return
      
      saving.value = true
      
      try {
        if (editingAccount.value) {
          await axios.put(
            `${API_BASE}/accounts/${editingAccount.value.id}`,
            accountForm.value,
            { headers: { 'Authorization': `Bearer ${authStore.token}` } }
          )
        } else {
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

    /**
     * Show delete account confirmation dialog
     * @param {Object} account - Account to delete
     * @param {Object} owner - Account's owner
     */
    function confirmDeleteAccount(account, owner) {
      deletingAccount.value = {
        account,
        owner
      }
    }

    /**
     * Close delete account dialog
     */
    function closeDeletingAccount() {
      deletingAccount.value = null
    }

    /**
     * Delete account (force=true to cascade delete transactions)
     */
    async function deleteAccount() {
      if (!deletingAccount.value || deleting.value) return
      
      deleting.value = true
      
      try {
        const force = true
        
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

    /**
     * Trigger file input for account import
     * @param {Object} account - Target account for import
     * @param {Object} owner - Account's owner
     */
    function importToAccount(account, owner) {
      importingAccount.value = account
      importingOwner.value = owner
      fileInput.value.click()
    }

    /**
     * Handle file selection and import
     * Uploads CSV/XLSX to backend with auto-categorization
     * Sends import results to chat via emit
     * @param {Event} event - File input change event
     */
    async function handleFileSelect(event) {
      const file = event.target.files[0]
      if (!file) return
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('import_mode', 'account')
      formData.append('account_id', importingAccount.value.id)
      formData.append('auto_categorize', 'true')
      
      loading.value = true
      
      try {
        const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
          headers: {
            'Authorization': `Bearer ${authStore.token}`,
            'Content-Type': 'multipart/form-data'
          },
          timeout: 300000
        })
        
        const stats = response.data.summary
        
        // Build detailed message with training log
        let message = `Successfully imported ${stats.rows_inserted || 0} transactions!\n\n`
        message += `📊 Results:\n`
        message += `• Transfer pairs: ${stats.transfer_pairs_found || 0}\n`
        message += `• AI categorized: ${stats.llm_categorized || 0}\n`
        message += `• Need review: ${stats.needs_review || 0}\n`
        
        if (stats.categories_trained) {
          message += `\n🎓 Trained ${stats.categories_trained} categories\n`
          
          // Show last 5 training items
          if (stats.training_log && stats.training_log.length > 0) {
            const lastItems = stats.training_log.slice(-5)
            message += lastItems.map(item => `   • ${item}`).join('\n')
          }
        }
        
        emit('add-chat-message', {
          message: `Imported ${file.name}`,
          response: message
        })
        
        emit('import-success')
        await loadOwners()
        
      
      } finally {
        loading.value = false
        event.target.value = ''
        importingAccount.value = null
        importingOwner.value = null
      }
    }

    /**
     * Format number as EUR currency
     * @param {number} amount - Amount to format
     * @returns {string} Formatted currency string
     */
    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }

    /** Reload owners when user logs in */
    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadOwners()
      }
    })

    /** Stats auto-recompute when filteredTransactions change */
    watch(() => props.filteredTransactions, () => {
      // Stats will auto-recompute via computed property
    }, { deep: true })

    /** Load owners on component mount */
    onMounted(() => {
      if (authStore.user) {
        loadOwners()
      }
    })

    return {
      loading,
      saving,
      deleting,
      owners,
      ownersWithStats,
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
.header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
}

.header-with-action h3 {
  margin: 0;
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--gap-standard);
}

.owner-section {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-large);
}

.owner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--gap-small);
  border-bottom: 1px solid var(--color-background-dark);
}

.owner-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
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

.accounts-grid-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: var(--gap-small);
}

.account-card {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-large);
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.account-card:hover :deep(.btn-menu-dots) {
  opacity: 1 !important;
}

.owner-header:hover :deep(.btn-menu-dots) {
  opacity: 1 !important;
}

.account-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: var(--gap-small);
  border-bottom: 1px solid var(--color-background-dark);
}

.account-info {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  flex: 1;
}

.account-name {
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

.btn-plus {
  margin: 0;
  background-color: transparent;
  border: none;
  cursor: pointer;
}

.btn-icon:hover {
  background: var(--color-background-dark);
  color: var(--color-text);
}

.account-stats {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
}

.stat-total {
  padding-top: 0.375rem;
  margin-top: 0.25rem;
  border-top: 1px solid var(--color-background-dark);
  font-weight: 600;
}

.stat-label {
  color: var(--color-text-light);
}

.stat-value {
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--text-medium);
}

.empty-accounts {
  text-align: center;
  padding: var(--gap-standard);
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
  align-items: center;
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.delete-modal {
  max-width: 30rem;
}

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
}

.modal-content {
  background: var(--color-background-light);
  border-radius: var(--radius);
  max-width: 32rem;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow);
}
</style>