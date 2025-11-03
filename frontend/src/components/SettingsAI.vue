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
      <select v-model="aiSettings.model" @change="saveAISettings">
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
        <h3>{{ testResult.success ? '✅ Connection Successful' : '❌ Connection Failed' }}</h3>
        <p>{{ testResult.message }}</p>
        <div v-if="testResult.response" class="test-response">
          <strong>AI Response:</strong>
          <div class="response-text">{{ testResult.response }}</div>
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
          // Silent save - don't show alert for every change
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