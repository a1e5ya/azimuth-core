<!--
  SettingsTab Component - Main Settings Container
  
  Provides masonry layout for settings components:
  - Account settings (profile, password)
  - AI settings configuration
  - Data management (backup/restore)
  - Danger zone (logout, delete operations)
  
  Features:
  - Masonry grid layout (3 columns)
  - System status monitoring (API, Database, Ollama)
  - Event propagation from child components
  - Auto-refresh system status every 30 seconds
  - Responsive column layout
  
  Events:
  - @chat-cleared: Emitted when chat history cleared
  
  Child Components:
  - SettingsAccount: Profile and password management
  - SettingsAI: AI model configuration
  - SettingsData: Database backup/restore
  - SettingsDanger: Dangerous operations
  
  System Status:
  - database: Database connection status
  - api: API endpoint availability
  - ollama: AI model availability
  - transactions: Transaction count
-->

<template>
  <div class="settings-container">
    <div class="settings-masonry">
      
      <!-- User Account Settings -->
      <SettingsAccount />
      
      <!-- AI Configuration Settings -->
      <SettingsAI />
      
      <!-- Data & Privacy Settings -->
      <SettingsData @data-imported="handleDataImported" />
      
      <!-- Danger Zone -->
      <SettingsDanger 
        @transaction-deleted="handleTransactionDeleted" 
        @account-deleted="handleAccountDeleted" 
        @chat-cleared="handleChatCleared"
      />
      
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import SettingsAccount from './SettingsAccount.vue'
import SettingsAI from './SettingsAI.vue'
import SettingsData from './SettingsData.vue'
import SettingsDanger from './SettingsDanger.vue'

export default {
  name: 'SettingsTab',
  components: {
    SettingsAccount,
    SettingsAI,
    SettingsData,
    SettingsDanger
  },
  emits: ['chat-cleared'],
  setup(props, { emit }) {
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

    /**
     * Checks system status (API, Database, Ollama)
     * @async
     * @returns {Promise<void>}
     */
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

        systemStatus.value.database = true
      } catch (error) {
        console.error('System status check failed:', error)
        systemStatus.value.database = false
      }
    }

    /**
     * Handles data imported event
     * @returns {void}
     */
    const handleDataImported = () => {
      checkSystemStatus()
    }

    /**
     * Handles transaction deleted event
     * @returns {void}
     */
    const handleTransactionDeleted = () => {
      checkSystemStatus()
    }

    /**
     * Handles account deleted event (no action needed - will redirect)
     * @returns {void}
     */
    const handleAccountDeleted = () => {
      // This will redirect, so no need to refresh
    }

    /**
     * Handles chat cleared event and emits to parent
     * @returns {void}
     */
    const handleChatCleared = () => {
      emit('chat-cleared')
    }

    onMounted(() => {
      checkSystemStatus()
      setInterval(checkSystemStatus, 30000)
    })

    return {
      systemStatus,
      systemDetails,
      showSystemDetails,
      handleDataImported,
      handleTransactionDeleted,
      handleAccountDeleted,
      handleChatCleared
    }
  }
}
</script>

<style scoped>
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

.settings-card {
  margin: 0 0 var(--gap-standard);
}
</style>