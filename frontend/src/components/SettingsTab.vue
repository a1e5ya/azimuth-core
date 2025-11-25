<template>
  <div class="settings-container">
    <div class="settings-masonry">
      
      <!-- User Account -->
      <SettingsAccount />
      
      <!-- AI Settings -->
      <SettingsAI />
      
      <!-- Data & Privacy -->
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

    const handleDataImported = () => {
      checkSystemStatus()
    }

    const handleTransactionDeleted = () => {
      checkSystemStatus()
    }

    const handleAccountDeleted = () => {
      // This will redirect, so no need to refresh
    }

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