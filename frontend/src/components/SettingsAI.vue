<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">AI Assistant</div>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Ollama Status</div>
        <div class="setting-desc">{{ ollamaStatus.message }}</div>
      </div>
      <span :class="['badge', ollamaStatus.connected ? 'badge-success' : 'badge-warning']">
        {{ ollamaStatus.connected ? 'Online' : 'Offline' }}
      </span>
    </div>
    
    <div class="form-row">
      <label>Model</label>
      <select v-model="aiSettings.model" @change="saveAISettings" class="form-select">
        <option value="llama3.2:3b">llama3.2:3b</option>
        <option value="llama3.2:1b">llama3.2:1b</option>
        <option value="llama3.1:8b">llama3.1:8b</option>
        <option value="mistral:7b">mistral:7b</option>
        <option value="phi3:mini">phi3:mini</option>
        <option value="qwen2.5:3b">qwen2.5:3b</option>
      </select>
    </div>
    
    <div class="form-column">
      <label>Custom Instructions (Optional)</label>
      <textarea 
        v-model="aiSettings.customInstructions"
        placeholder="Tell the AI how you want it to behave..."
        class="custom-textarea"
        @blur="saveAISettings"
      ></textarea>
    </div>
    
    <div class="btn-row">
      <button @click="testConnection" class="btn btn-primary" :disabled="testing">
        {{ testing ? 'Testing...' : 'Test Connection' }}
      </button>
      <button @click="refreshStatus" class="btn btn-secondary" :disabled="refreshing">
        {{ refreshing ? 'Refreshing...' : 'Refresh Status' }}
      </button>
    </div>

    <!-- Test Result Modal -->
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
          console.log('AI settings saved')
        }
      } catch (error) {
        console.error('Failed to save AI settings:', error)
      }
    }

    const testConnection = async () => {
      testing.value = true
      testResult.value = {
        success: false,
        message: '',
        response: ''
      }

      try {
        const token = localStorage.getItem('token')
        if (!token) {
          testResult.value.message = 'Not authenticated'
          showTestResult.value = true
          return
        }

        const response = await fetch('http://localhost:8001/chat/test', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: aiSettings.value.model
          })
        })

        if (response.ok) {
          const data = await response.json()
          testResult.value = {
            success: true,
            message: 'AI is responding correctly',
            response: data.response || ''
          }
        } else {
          const data = await response.json()
          testResult.value = {
            success: false,
            message: data.detail || 'Test failed',
            response: ''
          }
        }
      } catch (error) {
        console.error('Test connection failed:', error)
        testResult.value = {
          success: false,
          message: 'Connection error. Make sure Ollama is running.',
          response: ''
        }
      } finally {
        testing.value = false
        showTestResult.value = true
      }
    }

    const refreshStatus = async () => {
      refreshing.value = true
      await checkOllamaStatus()
      refreshing.value = false
    }

    const loadAISettings = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/chat/settings', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          if (data.model) aiSettings.value.model = data.model
          if (data.custom_instructions) aiSettings.value.customInstructions = data.custom_instructions
        }
      } catch (error) {
        console.error('Failed to load AI settings:', error)
      }
    }

    onMounted(() => {
      checkOllamaStatus()
      loadAISettings()
    })

    return {
      aiSettings,
      ollamaStatus,
      testing,
      refreshing,
      showTestResult,
      testResult,
      checkOllamaStatus,
      saveAISettings,
      testConnection,
      refreshStatus
    }
  }
}
</script>

<style scoped>
.test-response {
  margin-top: 1rem;
  padding: 0.75rem;
  background: var(--color-background-dark);
  border-radius: var(--radius);
}

.response-text {
  margin-top: 0.5rem;
  font-style: italic;
  color: var(--color-text-light);
  white-space: pre-wrap;
}
</style>