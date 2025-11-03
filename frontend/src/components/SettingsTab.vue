<template>
  <div class="settings-container">
    <div class="settings-masonry">
      
      <!-- User Account -->
      <SettingsAccount />
      
      <!-- AI Settings -->
      <SettingsAI />
      
      <!-- Data & Privacy -->
      <SettingsData @data-imported="handleDataImported" />
      
      <!-- Security & Sessions -->
      <SettingsSecurity />
      
      <!-- System Status -->
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
            <div class="stat-value status-info">{{ formatShortNumber(systemStatus.transactions) }}</div>
            <div class="stat-label">Transactions</div>
          </div>
        </div>
        
        <button @click="viewSystemDetails" class="btn btn-secondary" style="width: 100%; margin-top: 0.625rem;">
          View Details
        </button>
      </div>
      
      <!-- Danger Zone -->
      <SettingsDanger 
        @transaction-deleted="handleTransactionDeleted" 
        @account-deleted="handleAccountDeleted" 
      />
      
    </div>

    <!-- System Details Modal -->
    <div v-if="showSystemDetails" class="modal-overlay" @click="showSystemDetails = false">
      <div class="modal-content modal-large" @click.stop>
        <h3>System Details</h3>
        
        <div class="detail-section">
          <h4>Database</h4>
          <div class="detail-row">
            <span>Status:</span>
            <span :class="systemStatus.database ? 'status-ok' : 'status-error'">
              {{ systemStatus.database ? 'Connected' : 'Error' }}
            </span>
          </div>
          <div class="detail-row">
            <span>Location:</span>
            <span>/data/finance.db</span>
          </div>
          <div class="detail-row">
            <span>Size:</span>
            <span>{{ systemDetails.databaseSize }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>API Server</h4>
          <div class="detail-row">
            <span>Status:</span>
            <span :class="systemStatus.api ? 'status-ok' : 'status-error'">
              {{ systemStatus.api ? 'Running' : 'Offline' }}
            </span>
          </div>
          <div class="detail-row">
            <span>Endpoint:</span>
            <span>http://localhost:8001</span>
          </div>
          <div class="detail-row">
            <span>Uptime:</span>
            <span>{{ systemDetails.uptime }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>Ollama AI</h4>
          <div class="detail-row">
            <span>Status:</span>
            <span :class="systemStatus.ollama ? 'status-ok' : 'status-error'">
              {{ systemStatus.ollama ? 'Running' : 'Offline' }}
            </span>
          </div>
          <div class="detail-row">
            <span>Model:</span>
            <span>{{ systemDetails.aiModel }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>Data</h4>
          <div class="detail-row">
            <span>Transactions:</span>
            <span>{{ formatNumber(systemStatus.transactions) }}</span>
          </div>
          <div class="detail-row">
            <span>Categories:</span>
            <span>{{ formatNumber(systemDetails.categories) }}</span>
          </div>
          <div class="detail-row">
            <span>Accounts:</span>
            <span>{{ formatNumber(systemDetails.accounts) }}</span>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="showSystemDetails = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import SettingsAccount from './SettingsAccount.vue'
import SettingsAI from './SettingsAI.vue'
import SettingsData from './SettingsData.vue'
import SettingsSecurity from './SettingsSecurity.vue'
import SettingsDanger from './SettingsDanger.vue'

export default {
  name: 'SettingsTab',
  components: {
    SettingsAccount,
    SettingsAI,
    SettingsData,
    SettingsSecurity,
    SettingsDanger
  },
  setup() {
    const systemStatus = ref({
      database: true,
      api: true,
      ollama: false,
      transactions: 0
    })

    const systemDetails = ref({
      databaseSize: '0 MB',
      uptime: 'Unknown',
      aiModel: 'llama3.2:3b',
      categories: 0,
      accounts: 0
    })

    const showSystemDetails = ref(false)

    const formatNumber = (num) => {
      return num.toLocaleString()
    }

    const formatShortNumber = (num) => {
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      return num.toString()
    }

    const checkSystemStatus = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        // Check API
        try {
          const apiResponse = await fetch('http://localhost:8001/health')
          systemStatus.value.api = apiResponse.ok
        } catch {
          systemStatus.value.api = false
        }

        // Check Ollama
        try {
          const ollamaResponse = await fetch('http://localhost:8001/chat/ollama-status')
          if (ollamaResponse.ok) {
            const data = await ollamaResponse.json()
            systemStatus.value.ollama = data.ollama_running && data.model_available
            if (data.current_model) {
              systemDetails.value.aiModel = data.current_model
            }
          }
        } catch {
          systemStatus.value.ollama = false
        }

        // Get transaction count
        try {
          const statsResponse = await fetch('http://localhost:8001/transactions/stats', {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (statsResponse.ok) {
            const stats = await statsResponse.json()
            systemStatus.value.transactions = stats.total_count || 0
          }
        } catch (error) {
          console.error('Failed to load transaction stats:', error)
        }

        // Get system details
        try {
          const detailsResponse = await fetch('http://localhost:8001/system/details', {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (detailsResponse.ok) {
            const details = await detailsResponse.json()
            systemDetails.value = {
              ...systemDetails.value,
              ...details
            }
          }
        } catch (error) {
          console.error('Failed to load system details:', error)
        }

        systemStatus.value.database = true
      } catch (error) {
        console.error('System status check failed:', error)
        systemStatus.value.database = false
      }
    }

    const viewSystemDetails = () => {
      showSystemDetails.value = true
    }

    const handleDataImported = () => {
      // Refresh system status when data is imported
      checkSystemStatus()
    }

    const handleTransactionDeleted = () => {
      // Refresh system status when transactions are deleted
      checkSystemStatus()
    }

    const handleAccountDeleted = () => {
      // This will redirect, so no need to refresh
    }

    onMounted(() => {
      checkSystemStatus()
      
      // Refresh status every 30 seconds
      setInterval(checkSystemStatus, 30000)
    })

    return {
      systemStatus,
      systemDetails,
      showSystemDetails,
      formatNumber,
      formatShortNumber,
      viewSystemDetails,
      handleDataImported,
      handleTransactionDeleted,
      handleAccountDeleted
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

.btn-secondary {
  background: var(--color-background-dark);
  color: var(--color-text);
}

.btn-secondary:hover {
  background: var(--color-background);
  box-shadow: var(--shadow-hover);
  transform: translateY(-0.125rem);
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

.modal-large {
  max-width: 40rem;
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

.detail-section {
  margin-bottom: 1.5rem;
}

.detail-section:last-of-type {
  margin-bottom: 1rem;
}

.detail-section h4 {
  font-size: var(--text-medium);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.75rem;
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.1);
  padding-bottom: 0.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.05);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row span:first-child {
  font-weight: 500;
  color: var(--color-text-muted);
}

.detail-row span:last-child {
  color: var(--color-text);
}

.detail-row .status-ok {
  color: #15803d;
  font-weight: 600;
}

.detail-row .status-error {
  color: #dc2626;
  font-weight: 600;
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