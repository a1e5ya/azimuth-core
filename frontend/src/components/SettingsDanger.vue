<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Danger Zone</div>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Reset Categories to Default</div>
        <div class="setting-desc">Restore default category structure</div>
      </div>
      <button @click="confirmAction('reset-categories')" class="btn btn-danger">Reset</button>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Clear All Chat History</div>
        <div class="setting-desc">Delete all AI chat messages</div>
      </div>
      <button @click="confirmAction('clear-chat')" class="btn btn-danger">Clear</button>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Delete All Transactions</div>
        <div class="setting-desc">Permanently delete all transaction data</div>
      </div>
      <button @click="confirmAction('delete-transactions')" class="btn btn-danger">Delete</button>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Delete Account</div>
        <div class="setting-desc">Permanently delete your account and all data</div>
      </div>
      <button @click="confirmAction('delete-account')" class="btn btn-danger">Delete Account</button>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmation" class="modal-overlay" @click="showConfirmation = false">
      <div class="modal-content" @click.stop>
        <h3>{{ confirmationTitle }}</h3>
        <p>{{ confirmationMessage }}</p>
        
        <div v-if="requiresPasswordConfirmation" class="form-row" style="margin-bottom: 1rem;">
          <label>Password</label>
          <input 
            v-model="confirmationPassword" 
            type="password" 
            placeholder="Enter your password to confirm"
            @keyup.enter="executeAction"
          >
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

    const cancelAction = () => {
      showConfirmation.value = false
      confirmationPassword.value = ''
      pendingAction.value = null
    }

    const executeAction = async () => {
      if (requiresPasswordConfirmation.value && !confirmationPassword.value) {
        return
      }

      executing.value = true

      try {
        const token = localStorage.getItem('token')
        if (!token) {
          return
        }

        switch (pendingAction.value) {
          case 'reset-categories':
            await resetCategories(token)
            break
          case 'clear-chat':
            await clearChatHistory(token)
            break
          case 'delete-transactions':
            await deleteAllTransactions(token)
            break
          case 'delete-account':
            await deleteAccount(token)
            break
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
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        window.location.reload()
      } else {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to reset categories')
      }
    }

    const clearChatHistory = async (token) => {
      const response = await fetch('http://localhost:8001/chat/history', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        window.location.reload()
      } else {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to clear chat history')
      }
    }

    const deleteAllTransactions = async (token) => {
      const response = await fetch('http://localhost:8001/dangerous/transactions/delete-all', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          password: confirmationPassword.value
        })
      })

      if (response.ok) {
        emit('transaction-deleted')
        window.location.reload()
      } else {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to delete transactions')
      }
    }

    const deleteAccount = async (token) => {
      const response = await fetch('http://localhost:8001/dangerous/account', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          password: confirmationPassword.value
        })
      })

      if (response.ok) {
        localStorage.removeItem('token')
        emit('account-deleted')
        window.location.href = '/'
      } else {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to delete account')
      }
    }

    return {
      showConfirmation,
      confirmationTitle,
      confirmationMessage,
      confirmationPassword,
      requiresPasswordConfirmation,
      executing,
      confirmAction,
      cancelAction,
      executeAction
    }
  }
}
</script>

<style scoped>
/* Settings component styles - matches global design system */
.card { break-inside: avoid; }
.setting-row { display: flex; justify-content: space-between; align-items: center; padding: var(--gap-small) 0; border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.05); }
.setting-row:last-child { border-bottom: none; padding-bottom: 0; }
.setting-info { flex: 1; }
.setting-label { font-size: var(--text-small); font-weight: 500; color: var(--color-text); margin-bottom: 0.125rem; }
.setting-desc { font-size: var(--text-small); color: var(--color-text-muted); }
.setting-value { font-size: var(--text-small); color: var(--color-text-light); background: var(--color-background-dark); padding: 0.1875rem 0.5rem; border-radius: var(--radius); }
.form-row { display: grid; grid-template-columns: 7rem 1fr; gap: var(--gap-small); align-items: center; margin-bottom: var(--gap-small); }
.form-row label { font-size: var(--text-small); font-weight: 500; color: var(--color-text); text-align: left; }
.form-row input, .form-row select { width: 100%; padding: 0.25rem 0.5rem; border: 0.0625rem solid rgba(0, 0, 0, 0.2); border-radius: var(--radius); font-size: var(--text-small); color: var(--color-text); background: var(--color-button); transition: all 0.2s ease; }
.form-row input:focus, .form-row select:focus { outline: none; border-color: var(--color-button-active); box-shadow: 0 0 0 0.125rem rgba(0, 0, 0, 0.1); }
.form-column { display: flex; flex-direction: column; gap: 0.125rem; margin-bottom: var(--gap-small); }
.custom-textarea { width: 100%; padding: 0.25rem 0.5rem; border: 0.0625rem solid rgba(0, 0, 0, 0.2); border-radius: var(--radius); font-size: var(--text-small); color: var(--color-text); background: var(--color-button); font-family: "Livvic", sans-serif; font-style: italic; min-height: 2.5rem; resize: vertical; }
.badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: var(--radius); font-size: var(--text-small); font-weight: 600; }
.badge-success { background: rgba(34, 197, 94, 0.15); color: #15803d; }
.badge-warning { background: rgba(251, 146, 60, 0.15); color: #c2410c; }
.toggle { position: relative; width: 2.25rem; height: 1.125rem; background: var(--color-background-dark); border-radius: 0.5625rem; cursor: pointer; transition: background 0.3s ease; }
.toggle.active { background: var(--color-button-active); }
.toggle::after { content: ""; position: absolute; width: 0.875rem; height: 0.875rem; background: var(--color-button); border-radius: 50%; top: 0.125rem; left: 0.125rem; transition: left 0.3s ease; box-shadow: var(--shadow); }
.toggle.active::after { left: 1.25rem; }
.btn-row { display: flex; gap: var(--gap-small); margin-top: var(--gap-small); }
.divider { margin: var(--gap-small) 0; border: none; border-top: 0.0625rem solid rgba(0, 0, 0, 0.1); }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-content { backdrop-filter: blur(1.5rem); background: var(--color-background-light); border-radius: var(--radius-large); padding: var(--gap-large); max-width: 25rem; width: 90%; box-shadow: var(--shadow); animation: slideUp 0.3s ease; }
.modal-large { max-width: 40rem; }
@keyframes slideUp { from { opacity: 0; transform: translateY(2rem); } to { opacity: 1; transform: translateY(0); } }
.modal-content h3 { margin-bottom: var(--gap-standard); color: var(--color-text); font-size: var(--text-large); font-weight: 600; }
.modal-content p { color: var(--color-text-light); margin-bottom: var(--gap-standard); font-size: var(--text-small); line-height: 1.5; }
.modal-actions { display: flex; gap: var(--gap-small); justify-content: flex-end; }
@media (max-width: 48rem) { .btn-row { flex-direction: column; } .form-row { grid-template-columns: 1fr; gap: 0.125rem; } }
</style>