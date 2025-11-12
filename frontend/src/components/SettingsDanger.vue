<template>
  <div class="card settings-card">
    <div class="card-header">
      <div class="card-title">Danger Zone</div>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Current Session</div>
        <div class="setting-desc">Started {{ sessionStartTime }}</div>
      </div>
      <button @click="logout" class="btn btn-danger">Logout</button>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Clear All Chat History</div>
        <div class="setting-desc">Delete all AI chat messages</div>
      </div>
      <button @click="confirmAction('clear-chat')" class="btn btn-danger">Clear Chat</button>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Delete All Transactions</div>
        <div class="setting-desc">Permanently delete all transaction data</div>
      </div>
      <button @click="confirmAction('delete-transactions')" class="btn btn-danger">Delete Transactions</button>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Delete Account</div>
        <div class="setting-desc">Permanently delete account and all data</div>
      </div>
      <button @click="confirmAction('delete-account')" class="btn btn-danger">Delete Account</button>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmation" class="modal-overlay" @click="showConfirmation = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ confirmationTitle }}</h3>
          <button class="close-btn" @click="showConfirmation = false">×</button>
        </div>
        <div class="modal-body">
          <p>{{ confirmationMessage }}</p>
          <div v-if="requiresPasswordConfirmation" class="form-row" style="margin-bottom: 1rem;">
            <label>Password</label>
            <input v-model="confirmationPassword" type="password" placeholder="Enter your password to confirm" class="form-input" @keyup.enter="executeAction">
          </div>
        </div>
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
import { ref, computed } from 'vue'

export default {
  name: 'SettingsDanger',
  emits: ['transaction-deleted', 'account-deleted'],
  setup(props, { emit }) {
    const showConfirmation = ref(false)
    const confirmationTitle = ref('')
    const confirmationMessage = ref('')
    const confirmationPassword = ref('')
    const pendingAction = ref(null)
    const executing = ref(false)

    const requiresPasswordConfirmation = computed(() => {
      return ['delete-transactions', 'delete-account'].includes(pendingAction.value)
    })

    const confirmAction = (action) => {
      pendingAction.value = action
      confirmationPassword.value = ''
      const actions = {
        'reset-categories': { title: 'Reset Categories?', message: 'This will reset all categories to their default state. Custom categories will be removed. This cannot be undone.' },
        'clear-chat': { title: 'Clear Chat History?', message: 'This will delete all chat messages permanently. This cannot be undone.' },
        'delete-transactions': { title: 'Delete All Transactions?', message: 'This will delete ALL your transaction data permanently. This cannot be undone! Please enter your password to confirm.' },
        'delete-account': { title: 'Delete Account?', message: 'This will permanently delete your account and ALL associated data including transactions, categories, budgets, and goals. This cannot be undone! Please enter your password to confirm.' }
      }
      const actionConfig = actions[action]
      confirmationTitle.value = actionConfig.title
      confirmationMessage.value = actionConfig.message
      showConfirmation.value = true
    }

    const cancelAction = () => {
      showConfirmation.value = false
      confirmationPassword.value = ''
      pendingAction.value = null
    }

    const executeAction = async () => {
      if (requiresPasswordConfirmation.value && !confirmationPassword.value) return
      executing.value = true
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        switch (pendingAction.value) {
          case 'reset-categories': await resetCategories(token); break
          case 'clear-chat': await clearChatHistory(token); break
          case 'delete-transactions': await deleteAllTransactions(token); break
          case 'delete-account': await deleteAccount(token); break
        }
      } catch (error) {
        console.error('Action failed:', error)
      } finally {
        executing.value = false
        cancelAction()
      }
    }

    const resetCategories = async (token) => {
      const response = await fetch('http://localhost:8001/categories/reset', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) window.location.reload()
      else throw new Error((await response.json()).detail || 'Failed to reset categories')
    }

    const clearChatHistory = async (token) => {
      const response = await fetch('http://localhost:8001/chat/history', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) window.location.reload()
      else throw new Error((await response.json()).detail || 'Failed to clear chat history')
    }

    const deleteAllTransactions = async (token) => {
      const response = await fetch('http://localhost:8001/dangerous/transactions/delete-all', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: confirmationPassword.value })
      })
      if (response.ok) {
        emit('transaction-deleted')
        window.location.reload()
      } else throw new Error((await response.json()).detail || 'Failed to delete transactions')
    }

    const deleteAccount = async (token) => {
      const response = await fetch('http://localhost:8001/dangerous/account', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: confirmationPassword.value })
      })
      if (response.ok) {
        localStorage.removeItem('token')
        emit('account-deleted')
        window.location.href = '/'
      } else throw new Error((await response.json()).detail || 'Failed to delete account')
    }

    return {
      showConfirmation, confirmationTitle, confirmationMessage, confirmationPassword,
      requiresPasswordConfirmation, executing, confirmAction, cancelAction, executeAction
    }
  }
}
</script>