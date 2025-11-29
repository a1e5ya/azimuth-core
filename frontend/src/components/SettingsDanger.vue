<!--
  SettingsDanger Component - Dangerous Operations Management
  
  Provides interface for critical account operations:
  - Logout current session
  - Clear all chat history
  - Delete all transactions (requires password)
  - Delete entire account (requires password)
  
  Features:
  - Confirmation modals for all dangerous actions
  - Password verification for destructive operations
  - Loading states during execution
  - Session time display from activity log
  - Auto-reload or redirect after operations
  
  Events:
  - @transaction-deleted: Emitted after transactions deleted
  - @account-deleted: Emitted after account deleted
  - @chat-cleared: Emitted after chat history cleared
  
  Safety Measures:
  - Password required for: delete transactions, delete account
  - Confirmation dialog for all operations
  - Clear warning messages
  - Cannot be undone warnings
  
  API Endpoints:
  - GET /system/activity-log - Load session info
  - POST /dangerous/categories/reset - Reset categories
  - DELETE /dangerous/transactions/delete-all - Delete transactions
  - DELETE /dangerous/account - Delete account
-->

<template>
  <div class="card settings-card">
    <div class="card-header">
      <div class="card-title">Danger Zone</div>
    </div>
    
    <!-- Logout Current Session -->
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Current Session</div>
      </div>
      <button @click="logout" class="btn btn-danger">Logout</button>
    </div>
    
    <!-- Clear Chat History -->
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Clear All Chat History</div>
      </div>
      <button @click="confirmAction('clear-chat')" class="btn btn-danger">Clear Chat</button>
    </div>
    
    <!-- Delete All Transactions -->
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Delete All Transactions</div>
      </div>
      <button @click="confirmAction('delete-transactions')" class="btn btn-danger">Delete Transactions</button>
    </div>
    
    <!-- Delete Account -->
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Delete Account</div>
      </div>
      <button @click="confirmAction('delete-account')" class="btn btn-danger">Delete Account</button>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmation" class="modal-overlay" @click="showConfirmation = false">
      <div class="modal-content" @click.stop>
        <!-- Modal Header -->
        <div class="modal-header">
          <h3>{{ confirmationTitle }}</h3>
          <button class="close-btn" @click="showConfirmation = false">×</button>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          <p>{{ confirmationMessage }}</p>
          <!-- Password Input (for destructive operations) -->
          <div v-if="requiresPasswordConfirmation" class="form-row" style="margin-bottom: 1rem;">
            <label>Password</label>
            <input v-model="confirmationPassword" type="password" placeholder="Enter your password to confirm" class="form-input" @keyup.enter="executeAction">
          </div>
        </div>
        
        <!-- Modal Actions -->
        <div class="modal-actions">
          <button @click="cancelAction" class="btn btn-secondary">Cancel</button>
          <button @click="executeAction" class="btn btn-danger" :disabled="executing">
            {{ executing ? 'Processing...' : 'Confirm' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

export default {
  name: 'SettingsDanger',
  emits: ['transaction-deleted', 'account-deleted', 'chat-cleared'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    
    const showConfirmation = ref(false)
    const confirmationTitle = ref('')
    const confirmationMessage = ref('')
    const confirmationPassword = ref('')
    const pendingAction = ref(null)
    const executing = ref(false)
    const sessionStartTime = ref('Unknown')

    /**
     * Loads session start time from activity log
     * @async
     * @returns {Promise<void>}
     */
    const loadSessionTime = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          sessionStartTime.value = 'Unknown'
          return
        }
        
        const response = await fetch('http://localhost:8001/system/activity-log', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (response.ok) {
          const logs = await response.json()
          const lastLogin = logs.find(log => log.entity === 'auth' && log.action === 'login')
          
          if (lastLogin && lastLogin.created_at) {
            sessionStartTime.value = lastLogin.created_at
            return
          }
        }
      } catch (error) {
        console.error('Failed to load session time:', error)
      }
      sessionStartTime.value = 'Unknown'
    }

    /** @type {import('vue').ComputedRef<boolean>} */
    const requiresPasswordConfirmation = computed(() => {
      return ['delete-transactions', 'delete-account'].includes(pendingAction.value)
    })

    /**
     * Logs out current user and reloads page
     * @async
     * @returns {Promise<void>}
     */
    const logout = async () => {
      await authStore.logout()
      window.location.reload()
    }

    /**
     * Shows confirmation modal for dangerous action
     * @param {string} action - Action type (reset-categories, clear-chat, delete-transactions, delete-account)
     * @returns {void}
     */
    const confirmAction = (action) => {
      pendingAction.value = action
      confirmationPassword.value = ''
      const actions = {
        'reset-categories': { 
          title: 'Reset Categories?', 
          message: 'This will reset all categories to their default state. Custom categories will be removed. This cannot be undone.' 
        },
        'clear-chat': { 
          title: 'Clear Chat History?', 
          message: 'This will delete all chat messages permanently. This cannot be undone.' 
        },
        'delete-transactions': { 
          title: 'Delete All Transactions?', 
          message: 'This will delete ALL your transaction data permanently. This cannot be undone! Please enter your password to confirm.' 
        },
        'delete-account': { 
          title: 'Delete Account?', 
          message: 'This will permanently delete your account and ALL associated data including transactions, categories, budgets, and goals. This cannot be undone! Please enter your password to confirm.' 
        }
      }
      const actionConfig = actions[action]
      confirmationTitle.value = actionConfig.title
      confirmationMessage.value = actionConfig.message
      showConfirmation.value = true
    }

    /**
     * Cancels current action and closes confirmation modal
     * @returns {void}
     */
    const cancelAction = () => {
      showConfirmation.value = false
      confirmationPassword.value = ''
      pendingAction.value = null
    }

    /**
     * Executes the pending dangerous action
     * @async
     * @returns {Promise<void>}
     */
    const executeAction = async () => {
      if (requiresPasswordConfirmation.value && !confirmationPassword.value) {
        return
      }
      
      executing.value = true
      try {
        switch (pendingAction.value) {
          case 'reset-categories': await resetCategories(); break
          case 'clear-chat': await clearChatHistory(); break
          case 'delete-transactions': await deleteAllTransactions(); break
          case 'delete-account': await deleteAccount(); break
        }
      } catch (error) {
        console.error('Action failed:', error)
      } finally {
        executing.value = false
        cancelAction()
      }
    }

    /**
     * Resets all categories to default state
     * @async
     * @returns {Promise<void>}
     */
    const resetCategories = async () => {
      await axios.post(`${API_BASE}/dangerous/categories/reset`, {}, {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      })
      window.location.reload()
    }

    /**
     * Clears chat history
     * @returns {void}
     */
    const clearChatHistory = async () => {
      emit('chat-cleared')
    }

    /**
     * Deletes all user transactions (requires password)
     * @async
     * @returns {Promise<void>}
     */
    const deleteAllTransactions = async () => {
      await axios.delete(`${API_BASE}/dangerous/transactions/delete-all`, {
        headers: { 
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        },
        data: { password: confirmationPassword.value }
      })
      
      emit('transaction-deleted')
      window.location.reload()
    }

    /**
     * Deletes user account and all data (requires password)
     * @async
     * @returns {Promise<void>}
     */
    const deleteAccount = async () => {
      await axios.delete(`${API_BASE}/dangerous/account`, {
        headers: { 
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        },
        data: { password: confirmationPassword.value }
      })
      
      await authStore.logout()
      emit('account-deleted')
      window.location.href = '/'
    }

    onMounted(() => {
      loadSessionTime()
    })

    return {
      sessionStartTime,
      showConfirmation, 
      confirmationTitle, 
      confirmationMessage, 
      confirmationPassword,
      requiresPasswordConfirmation, 
      executing, 
      logout,
      confirmAction, 
      cancelAction, 
      executeAction
    }
  }
}
</script>