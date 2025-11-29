<!--
  Settings AI - Ollama LLM configuration and status
  
  AI/LLM settings interface for Ollama integration status.
  
  Features:
  - Ollama connection status check (GET /chat/ollama-status)
  - Model availability verification
  - Status refresh button
  - Connection test with response display
  - Visual status badges (Online/Offline)
  
  Status Display:
  - Green "Online": Ollama running and model available
  - Yellow "Offline": Service unavailable or model missing
  - Status message with details
-->
<template>
  <div class="card settings-card">
    
    <!-- Ollama status display -->
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Ollama Status</div>
        <div class="setting-desc">{{ ollamaStatus.message }}</div>
      </div>
      <span :class="['badge', ollamaStatus.connected ? 'badge-success' : 'badge-warning']">
        {{ ollamaStatus.connected ? 'Online' : 'Offline' }}
      </span>
    </div>
    
    <!-- Refresh button -->
    <div class="btn-row">
      <button @click="refreshStatus" class="btn btn-primary" :disabled="refreshing">
        {{ refreshing ? 'Refreshing...' : 'Refresh Status' }}
      </button>
    </div>

    <!-- Test result modal -->
    <div v-if="showTestResult" class="modal-overlay" @click="showTestResult = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ testResult.success ? '✅ Connection Successful' : '❌ Connection Failed' }}</h3>
          <button class="close-btn" @click="showTestResult = false">×</button>
        </div>
        <div class="modal-body">
          <p>{{ testResult.message }}</p>
          <div v-if="testResult.response" class="test-response">
            <strong>AI Response:</strong>
            <div class="response-text">{{ testResult.response }}</div>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showTestResult = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'SettingsAI',
  setup() {
    const aiSettings = ref({
      model: 'llama3.2:3b',
      customInstructions: ''
    })

    const ollamaStatus = ref({
      connected: false,
      message: 'Checking...'
    })

    const testing = ref(false)
    const refreshing = ref(false)
    const showTestResult = ref(false)
    const testResult = ref({
      success: false,
      message: '',
      response: ''
    })

    /**
     * Check Ollama status
     * Fetches from GET /chat/ollama-status
     * Updates connection status and current model
     */
    const checkOllamaStatus = async () => {
      try {
        const response = await fetch('http://localhost:8001/chat/ollama-status')
        if (response.ok) {
          const data = await response.json()
          ollamaStatus.value.connected = data.ollama_running && data.model_available
          ollamaStatus.value.message = data.message || (ollamaStatus.value.connected ? 'Ready' : 'Not available')
          
          if (data.current_model) {
            aiSettings.value.model = data.current_model
          }
        } else {
          ollamaStatus.value.connected = false
          ollamaStatus.value.message = 'Service unavailable'
        }
      } catch (error) {
        console.error('Failed to check Ollama status:', error)
        ollamaStatus.value.connected = false
        ollamaStatus.value.message = 'Connection error'
      }
    }

    /**
     * Save AI settings
     * Updates via PUT /chat/settings
     */
    const saveAISettings = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/chat/settings', {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: aiSettings.value.model,
            custom_instructions: aiSettings.value.customInstructions
          })
        })

        if (response.ok) {
          alert('AI settings saved successfully!')
        } else {
          alert('Failed to save settings')
        }
      } catch (error) {
        console.error('Failed to save AI settings:', error)
        alert('Failed to save settings')
      }
    }

    /**
     * Test Ollama connection
     * Sends test message, displays response in modal
     */
    const testConnection = async () => {
      testing.value = true
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('http://localhost:8001/chat/test', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: 'Test connection'
          })
        })

        if (response.ok) {
          const data = await response.json()
          testResult.value = {
            success: true,
            message: 'Connection successful! Ollama is responding.',
            response: data.response || 'OK'
          }
        } else {
          testResult.value = {
            success: false,
            message: 'Failed to connect to Ollama',
            response: ''
          }
        }
      } catch (error) {
        console.error('Connection test failed:', error)
        testResult.value = {
          success: false,
          message: 'Connection error: ' + error.message,
          response: ''
        }
      } finally {
        testing.value = false
        showTestResult.value = true
      }
    }

    /**
     * Refresh status
     * Re-checks Ollama connection
     */
    const refreshStatus = async () => {
      refreshing.value = true
      await checkOllamaStatus()
      refreshing.value = false
    }

    /** Check status on mount */
    onMounted(() => {
      checkOllamaStatus()
    })

    return {
      aiSettings,
      ollamaStatus,
      testing,
      refreshing,
      showTestResult,
      testResult,
      saveAISettings,
      testConnection,
      refreshStatus
    }
  }
}
</script>

<style scoped>

.setting-info {
  flex: 1;
}

.setting-label {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.setting-desc {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: var(--text-small);
  font-weight: 500;
}

.badge-success {
  background: rgba(34, 197, 94, 0.2);
  color: rgb(34, 197, 94);
}

.badge-warning {
  background: rgba(245, 158, 11, 0.2);
  color: rgb(245, 158, 11);
}


.test-response {
  margin-top: var(--gap-standard);
  padding: var(--gap-standard);
  background: var(--color-background-dark);
  border-radius: var(--radius);
}

.response-text {
  margin-top: var(--gap-small);
  font-family: monospace;
  font-size: var(--text-small);
  white-space: pre-wrap;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--gap-small);
  margin-top: var(--gap-standard);
}
</style>