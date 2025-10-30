<template>
  <div class="settings-container">
    <div class="settings-masonry">
      
      <!-- User Account Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">User Account</div>
        </div>
        
        <div class="form-row">
          <label>Display Name</label>
          <input v-model="userProfile.displayName" type="text" placeholder="Your name">
        </div>
        
        <div class="form-row">
          <label>Email</label>
          <input v-model="userProfile.email" type="email" placeholder="your.email@example.com" disabled>
        </div>
        
        <button @click="saveProfile" class="btn btn-primary">Save Profile</button>
        
        <hr class="divider">
        
        <div class="form-row">
          <label>Current Password</label>
          <input v-model="passwordForm.currentPassword" type="password" placeholder="Enter current password">
        </div>
        
        <div class="form-row">
          <label>New Password</label>
          <input v-model="passwordForm.newPassword" type="password" placeholder="Enter new password">
        </div>
        
        <div class="form-row">
          <label>Confirm New Password</label>
          <input v-model="passwordForm.confirmPassword" type="password" placeholder="Confirm new password">
        </div>
        
        <button @click="changePassword" class="btn btn-primary">Change Password</button>
      </div>
      

      
      <!-- AI Settings Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">AI Assistant</div>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Ollama Status</div>
          </div>
          <span :class="['badge', ollamaStatus.connected ? 'badge-success' : 'badge-warning']">
            {{ ollamaStatus.connected ? 'Online' : 'Offline' }}
          </span>
        </div>
        
        <div class="form-row">
          <label>Model</label>
          <select v-model="aiSettings.model">
            <option value="llama3.2:3b">llama3.2:3b (Current)</option>
            <option value="llama3.2:1b">llama3.2:1b</option>
            <option value="mistral:7b">mistral:7b</option>
            <option value="phi3:mini">phi3:mini</option>
          </select>
        </div>
        
        <div class="form-column">
          <label>Custom Instructions (Optional)</label>
          <textarea 
            v-model="aiSettings.customInstructions"
            placeholder="Tell the AI how you want it to behave..."
            class="custom-textarea"
          ></textarea>
        </div>
        
        <button @click="testConnection" class="btn btn-secondary">Test AI Connection</button>
      </div>

            <!-- Data & Privacy Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Data & Privacy</div>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Automatic Backups</div>
          </div>
          <div :class="['toggle', autoBackup ? 'active' : '']" @click="autoBackup = !autoBackup"></div>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Database Location</div>
            <div class="setting-desc">/data/finance.db</div>
          </div>
          <button class="btn btn-secondary">Open</button>
        </div>
        
        <div class="btn-row">
          <button @click="backupData" class="btn btn-primary">Backup Now</button>
          <button @click="restoreData" class="btn btn-secondary">Restore</button>
          <button @click="importTransactions" class="btn btn-primary">Import Transactions</button>
          <button @click="exportData" class="btn btn-secondary">Export All Data</button>
        </div>
        
        <div class="btn-row">
          <button @click="viewHistory" class="btn btn-secondary" style="flex: 1;">View History</button>
        </div>
        
        <hr class="divider">
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Data Stored</div>
          </div>
          <span class="setting-value">{{ dataStats.databaseSize }}</span>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Last Backup</div>
          </div>
          <span class="setting-value">{{ dataStats.lastBackup }}</span>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Total Transactions</div>
          </div>
          <span class="setting-value">{{ formatNumber(dataStats.totalTransactions) }}</span>
        </div>
      </div>
      
      <!-- Security & Sessions Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Security & Sessions</div>
        </div>
        
        <div class="form-row">
          <label>Auto-logout Timeout</label>
          <select v-model="securitySettings.autoLogoutTimeout">
            <option value="15">15 minutes</option>
            <option value="30">30 minutes</option>
            <option value="60">1 hour</option>
            <option value="120">2 hours</option>
            <option value="240">4 hours</option>
            <option value="0">Never</option>
          </select>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Current Session</div>
            <div class="setting-desc">Started {{ sessionStartTime }}</div>
          </div>
          <button @click="logout" class="btn btn-danger">Logout</button>
        </div>
        
        <button @click="viewLoginHistory" class="btn btn-secondary" style="width: 100%; margin-bottom: 0.75rem;">View Login History</button>
        
        <hr class="divider">
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Activity Log Entries</div>
          </div>
          <span class="setting-value">{{ formatNumber(dataStats.activityLogs) }}</span>
        </div>
        
        <button @click="viewActivityLog" class="btn btn-secondary" style="width: 100%;">View Activity Log</button>
      </div>
      
      <!-- System Status Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">System Status</div>
        </div>
        
        <div class="stats-grid">
          <div class="stat-box">
            <div :class="['stat-value', systemStatus.database ? 'status-ok' : 'status-error']">
              {{ systemStatus.database ? 'OK' : 'ERR' }}
            </div>
            <div class="stat-label">Database</div>
          </div>
          <div class="stat-box">
            <div :class="['stat-value', systemStatus.api ? 'status-ok' : 'status-error']">
              {{ systemStatus.api ? 'OK' : 'ERR' }}
            </div>
            <div class="stat-label">API</div>
          </div>
          <div class="stat-box">
            <div :class="['stat-value', systemStatus.ollama ? 'status-ok' : 'status-error']">
              {{ systemStatus.ollama ? 'OK' : 'ERR' }}
            </div>
            <div class="stat-label">Ollama</div>
          </div>
          <div class="stat-box">
            <div class="stat-value status-info">{{ formatShortNumber(dataStats.totalTransactions) }}</div>
            <div class="stat-label">Transactions</div>
          </div>
        </div>
        
        <button @click="viewSystemDetails" class="btn btn-secondary" style="width: 100%; margin-top: 0.625rem;">View Details</button>
      </div>
      
      <!-- Danger Zone Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Danger Zone</div>
        </div>
        

        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Reset Categories to Default</div>
          </div>
          <button @click="confirmAction('reset-categories')" class="btn btn-danger">Reset</button>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Clear All Chat History</div>
          </div>
          <button @click="confirmAction('clear-chat')" class="btn btn-danger">Clear</button>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Delete All Transactions</div>
          </div>
          <button @click="confirmAction('delete-transactions')" class="btn btn-danger">Delete</button>
        </div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">Delete Account</div>
          </div>
          <button @click="confirmAction('delete-account')" class="btn btn-danger">Delete Account</button>
        </div>
      </div>
      
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmation" class="modal-overlay" @click="showConfirmation = false">
      <div class="modal-content" @click.stop>
        <h3>{{ confirmationTitle }}</h3>
        <p>{{ confirmationMessage }}</p>
        <div class="modal-actions">
          <button @click="showConfirmation = false" class="btn btn-secondary">Cancel</button>
          <button @click="executeAction" class="btn btn-danger">Confirm</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'

export default {
  name: 'SettingsTab',
  setup() {
    const userProfile = ref({
      displayName: '',
      email: '',
      currency: 'EUR',
      locale: 'en-US'
    })

    const passwordForm = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    const aiSettings = ref({
      model: 'llama3.2:3b',
      customInstructions: ''
    })

    const securitySettings = ref({
      autoLogoutTimeout: '60'
    })

    const autoBackup = ref(false)

    const ollamaStatus = ref({
      connected: false,
      message: ''
    })

    const dataStats = ref({
      totalTransactions: 0,
      databaseSize: '0 MB',
      lastBackup: 'Never',
      activityLogs: 0
    })

    const systemStatus = ref({
      database: true,
      api: true,
      ollama: false
    })

    const sessionStartTime = ref('2 hours ago')

    const showConfirmation = ref(false)
    const confirmationTitle = ref('')
    const confirmationMessage = ref('')
    const pendingAction = ref(null)

    const formatNumber = (num) => {
      return num.toLocaleString()
    }

    const formatShortNumber = (num) => {
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      return num.toString()
    }

    const loadUserProfile = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const userData = await response.json()
          userProfile.value.email = userData.email
          userProfile.value.displayName = userData.display_name || ''
        }
      } catch (error) {
        console.error('Failed to load user profile:', error)
      }
    }

    const checkOllamaStatus = async () => {
      try {
        const response = await fetch('http://localhost:8001/chat/ollama-status')
        if (response.ok) {
          const data = await response.json()
          ollamaStatus.value.connected = data.ollama_running && data.model_available
          systemStatus.value.ollama = ollamaStatus.value.connected
          ollamaStatus.value.message = data.message || ''
        }
      } catch (error) {
        console.error('Failed to check Ollama status:', error)
        ollamaStatus.value.connected = false
        systemStatus.value.ollama = false
      }
    }

    const loadDataStats = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/transactions/stats', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          dataStats.value.totalTransactions = data.total_count || 0
          // Mock data for now - implement these endpoints later
          dataStats.value.databaseSize = '12.4 MB'
          dataStats.value.lastBackup = '2 hours ago'
          dataStats.value.activityLogs = 3847
        }
      } catch (error) {
        console.error('Failed to load data stats:', error)
      }
    }

    const saveProfile = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        // Mock implementation - add actual endpoint later
        alert('Profile updated successfully!')
      } catch (error) {
        console.error('Failed to save profile:', error)
        alert('Failed to save profile')
      }
    }

    const changePassword = async () => {
      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        alert('New passwords do not match')
        return
      }

      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/auth/change-password', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            current_password: passwordForm.value.currentPassword,
            new_password: passwordForm.value.newPassword
          })
        })

        if (response.ok) {
          alert('Password changed successfully!')
          passwordForm.value = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }
        } else {
          const data = await response.json()
          alert(data.detail || 'Failed to change password')
        }
      } catch (error) {
        console.error('Failed to change password:', error)
        alert('Failed to change password')
      }
    }

    const testConnection = async () => {
      await checkOllamaStatus()
      if (ollamaStatus.value.connected) {
        alert('✅ AI connection successful!')
      } else {
        alert('❌ AI connection failed. Please check if Ollama is running.')
      }
    }

    const backupData = () => {
      alert('Backup feature coming soon!')
    }

    const restoreData = () => {
      alert('Restore feature coming soon!')
    }

    const exportData = () => {
      alert('Export feature coming soon!')
    }

    const importTransactions = () => {
      alert('Please use the Transactions tab to import CSV files')
    }

    const viewHistory = () => {
      alert('History view coming soon!')
    }

    const viewLoginHistory = () => {
      alert('Login history view coming soon!')
    }

    const viewActivityLog = () => {
      alert('Activity log view coming soon!')
    }

    const viewSystemDetails = () => {
      alert('System details view coming soon!')
    }

    const logout = () => {
      localStorage.removeItem('token')
      window.location.reload()
    }

    const confirmAction = (action) => {
      pendingAction.value = action

      const actions = {
        'reset-categories': {
          title: 'Reset Categories?',
          message: 'This will reset all categories to their default state. Custom categories will be removed.'
        },
        'clear-chat': {
          title: 'Clear Chat History?',
          message: 'This will delete all chat messages permanently.'
        },
        'delete-transactions': {
          title: 'Delete All Transactions?',
          message: 'This will delete all your transaction data permanently. This cannot be undone!'
        },
        'delete-account': {
          title: 'Delete Account?',
          message: 'This will permanently delete your account and all associated data. This cannot be undone!'
        }
      }

      const actionConfig = actions[action]
      confirmationTitle.value = actionConfig.title
      confirmationMessage.value = actionConfig.message
      showConfirmation.value = true
    }

    const executeAction = async () => {
      showConfirmation.value = false
      alert(`Action "${pendingAction.value}" would be executed here`)
      // Implement actual dangerous actions with backend endpoints
    }

    onMounted(() => {
      loadUserProfile()
      checkOllamaStatus()
      loadDataStats()
    })

    return {
      userProfile,
      passwordForm,
      aiSettings,
      securitySettings,
      autoBackup,
      ollamaStatus,
      dataStats,
      systemStatus,
      sessionStartTime,
      showConfirmation,
      confirmationTitle,
      confirmationMessage,
      formatNumber,
      formatShortNumber,
      saveProfile,
      changePassword,
      testConnection,
      backupData,
      restoreData,
      exportData,
      importTransactions,
      viewHistory,
      viewLoginHistory,
      viewActivityLog,
      viewSystemDetails,
      logout,
      confirmAction,
      executeAction
    }
  }
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.settings-container {
  padding: 0;
  color: var(--color-text);
  font-size: var(--text-small);
  width: 100%;
  max-width: 100%;
  margin: 0;
}

.settings-masonry {
  column-count: 3;
  column-gap: var(--gap-standard);
  padding: var(--gap-standard);
}

.card {
  backdrop-filter: blur(1.25rem);
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  box-shadow: var(--shadow);
  transition: all 0.3s ease;
  break-inside: avoid;
  margin-bottom: var(--gap-standard);
  display: inline-block;
  width: 100%;
}

.card.full-width {
  grid-column: auto;
}

.card-header {
  margin-bottom: var(--gap-small);
  padding-bottom: var(--gap-small);
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: var(--text-medium);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.125rem;
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-small) 0;
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.05);
}

.setting-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-size: var(--text-small);
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 0.125rem;
}

.setting-desc {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.setting-value {
  font-size: var(--text-small);
  color: var(--color-text-light);
  background: var(--color-background-dark);
  padding: 0.1875rem 0.5rem;
  border-radius: var(--radius);
  margin-right: 0.5rem;
}

.btn {
  padding: 0.25rem var(--gap-small);
  border-radius: var(--radius);
  border: none;
  font-size: var(--text-small);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--shadow);
  margin: 0;
}

.btn-primary {
  background: var(--color-button);
  color: var(--color-button-text);
}

.btn-primary:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-0.125rem);
}

.btn-secondary {
  background: var(--color-background-dark);
  color: var(--color-text);
}

.btn-secondary:hover {
  background: var(--color-background);
  box-shadow: var(--shadow-hover);
  transform: translateY(-0.125rem);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.2);
  box-shadow: var(--shadow-hover);
  transform: translateY(-0.125rem);
}

.toggle {
  position: relative;
  width: 2.25rem;
  height: 1.125rem;
  background: var(--color-background-dark);
  border-radius: 0.5625rem;
  cursor: pointer;
  transition: background 0.3s ease;
  flex-shrink: 0;
  box-shadow: inset 0 0.125rem 0.25rem rgba(0, 0, 0, 0.1);
}

.toggle.active {
  background: var(--color-button-active);
}

.toggle::after {
  content: '';
  position: absolute;
  width: 0.875rem;
  height: 0.875rem;
  background: var(--color-button);
  border-radius: 50%;
  top: 0.125rem;
  left: 0.125rem;
  transition: left 0.3s ease;
  box-shadow: var(--shadow);
}

.toggle.active::after {
  left: 1.25rem;
}

.input-group {
  margin-bottom: var(--gap-small);
}

.input-group:last-child {
  margin-bottom: 0;
}

.input-group label {
  display: block;
  font-size: var(--text-small);
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 0.125rem;
}

.input-group input,
.input-group select {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 0.0625rem solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  font-size: var(--text-small);
  color: var(--color-text);
  background: var(--color-button);
  transition: all 0.2s ease;
}

.input-group input:focus,
.input-group select:focus {
  outline: none;
  border-color: var(--color-button-active);
  box-shadow: 0 0 0 0.125rem rgba(0, 0, 0, 0.1);
}

.input-group input:disabled {
  background: var(--color-background-dark);
  color: var(--color-text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.form-row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: var(--gap-small);
  align-items: center;
  margin-bottom: var(--gap-small);
}

.form-row label {
  font-size: var(--text-small);
  font-weight: 500;
  color: var(--color-text);
  text-align: left;
}

.form-row input,
.form-row select {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 0.0625rem solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  font-size: var(--text-small);
  color: var(--color-text);
  background: var(--color-button);
  transition: all 0.2s ease;
}

.form-row input:focus,
.form-row select:focus {
  outline: none;
  border-color: var(--color-button-active);
  box-shadow: 0 0 0 0.125rem rgba(0, 0, 0, 0.1);
}

.form-row input:disabled {
  background: var(--color-background-dark);
  color: var(--color-text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  margin-bottom: var(--gap-small);
}

.form-column label {
  font-size: var(--text-small);
  font-weight: 500;
  color: var(--color-text);
}

.custom-textarea {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 0.0625rem solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  font-size: var(--text-small);
  color: var(--color-text);
  background: var(--color-button);
  font-family: "Livvic", sans-serif;
  font-style: italic;
  min-height: 2.5rem;
  resize: vertical;
  transition: all 0.2s ease;
}

.custom-textarea:focus {
  outline: none;
  border-color: var(--color-button-active);
  box-shadow: 0 0 0 0.125rem rgba(0, 0, 0, 0.1);
}

.badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius);
  font-size: var(--text-small);
  font-weight: 600;
}

.badge-success {
  background: rgba(34, 197, 94, 0.15);
  color: #15803d;
}

.badge-warning {
  background: rgba(251, 146, 60, 0.15);
  color: #c2410c;
}

.badge-info {
  background: var(--color-background-dark);
  color: var(--color-text);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--gap-small);
  margin-top: var(--gap-small);
}

.stat-box {
  background: var(--color-background-dark);
  padding: 0.25rem;
  border-radius: var(--radius);
  text-align: center;
}

.stat-value {
  font-size: var(--text-large);
  font-weight: 700;
  margin-bottom: 0.125rem;
}

.stat-value.status-ok {
  color: #15803d;
}

.stat-value.status-error {
  color: #dc2626;
}

.stat-value.status-info {
  color: var(--color-text);
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.alert {
  padding: var(--gap-small);
  border-radius: var(--radius);
  margin-bottom: var(--gap-small);
  font-size: var(--text-small);
}

.alert-info {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.btn-row {
  display: flex;
  gap: var(--gap-small);
  margin-top: var(--gap-small);
}

.divider {
  margin: var(--gap-small) 0;
  border: none;
  border-top: 0.0625rem solid rgba(0, 0, 0, 0.1);
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
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  backdrop-filter: blur(1.5rem);
  background: var(--color-background-light);
  border-radius: var(--radius-large);
  padding: var(--gap-large);
  max-width: 25rem;
  width: 90%;
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

.modal-content h3 {
  margin-bottom: var(--gap-standard);
  color: var(--color-text);
  font-size: var(--text-large);
  font-weight: 600;
}

.modal-content p {
  color: var(--color-text-light);
  margin-bottom: var(--gap-standard);
  font-size: var(--text-small);
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: var(--gap-small);
  justify-content: flex-end;
}

/* Responsive Design */
@media (max-width: 64rem) {
  .settings-masonry {
    column-count: 2;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 48rem) {
  .settings-masonry {
    column-count: 1;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .btn-row {
    flex-direction: column;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 0.125rem;
  }
}

@media (max-width: 30rem) {
  .settings-container {
    padding: 0;
  }
  
  .settings-masonry {
    padding: var(--gap-small);
    column-count: 1;
  }
  
  .card {
    padding: var(--gap-small);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>