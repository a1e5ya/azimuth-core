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
        <div class="modal-header">
          <h3>System Details</h3>
          <button class="close-btn" @click="showSystemDetails = false">×</button>
        </div>
        
        <div class="modal-body">
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

        try {
          const apiResponse = await fetch('http://localhost:8001/health')
          systemStatus.value.api = apiResponse.ok
        } catch {
          systemStatus.value.api = false
        }

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
      checkSystemStatus()
    }

    const handleTransactionDeleted = () => {
      checkSystemStatus()
    }

    const handleAccountDeleted = () => {
      // This will redirect, so no need to refresh
    }

    onMounted(() => {
      checkSystemStatus()
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
/* Only SettingsTab-specific layout */
.settings-container {
  padding: 0;
  width: 100%;
  max-width: 100%;
  margin: 0;
}

.settings-masonry {
  column-count: 3;
  column-gap: var(--gap-standard);
  padding: var(--gap-standard);
}
</style>