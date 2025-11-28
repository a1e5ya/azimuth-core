<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content import-modal" @click.stop>
      <div class="modal-header">
        <h3>Import Transactions</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      
      <div class="modal-body">
        <!-- File Selection -->
        <div class="form-section">
          <h4>Select Files</h4>
          <div class="file-drop-zone" 
               @drop.prevent="handleDrop" 
               @dragover.prevent
               @click="triggerFileInput">
            <div v-if="selectedFiles.length === 0" class="drop-placeholder">
              <AppIcon name="file-add" size="large" />
              <p>Drop CSV files here or click to browse</p>
              <p class="help-text">Multiple files supported</p>
            </div>
            <div v-else class="file-list">
              <div v-for="(file, idx) in selectedFiles" :key="idx" class="file-item">
                <AppIcon name="file" size="small" />
                <span>{{ file.name }}</span>
                <button class="btn-remove" @click.stop="removeFile(idx)">×</button>
              </div>
            </div>
          </div>
          <input 
            ref="fileInput" 
            type="file" 
            accept=".csv,.xlsx" 
            multiple 
            @change="handleFileSelect" 
            style="display: none;"
          >
        </div>

        <!-- Import Mode Selection -->
        <div class="form-section">
          <h4>Import Mode</h4>
          <div class="radio-group">
            <label class="radio-option">
              <input 
                type="radio" 
                v-model="importMode" 
                value="training"
              >
              <div class="radio-content">
                <strong>Training Data</strong>
                <p>Pre-categorized data with auto-creation</p>
              </div>
            </label>
            
            <label class="radio-option" :class="{ 'disabled': !hasAccounts }">
              <input 
                type="radio" 
                v-model="importMode" 
                value="account"
                :disabled="!hasAccounts"
              >
              <div class="radio-content">
                <strong>Direct to Account</strong>
                <p v-if="hasAccounts">Import to a specific account</p>
                <p v-else class="warning-text">No accounts available - create accounts first</p>
              </div>
            </label>
          </div>
        </div>

        <!-- Account Selection (only for account mode) -->
        <div v-if="importMode === 'account'" class="form-section">
          <h4>Select Account</h4>
          <div v-if="loadingAccounts" class="loading-text">
            Loading accounts...
          </div>
          <select v-else v-model="selectedAccountId" class="form-select">
            <option value="">Select an account...</option>
            <optgroup 
              v-for="group in groupedAccounts" 
              :key="group.owner" 
              :label="group.owner"
            >
              <option 
                v-for="account in group.accounts" 
                :key="account.id" 
                :value="account.id"
              >
                {{ account.name }} ({{ account.account_type }})
              </option>
            </optgroup>
          </select>
          
          <div v-if="selectedAccount" class="account-preview">
            <div class="preview-label">Selected:</div>
            <div class="preview-content">
              <strong>{{ selectedAccount.name }}</strong>
              <span>{{ selectedAccount.account_type }}</span>
              <span class="owner-badge" :style="{ background: selectedAccount.owner.color }">
                {{ selectedAccount.owner.name }}
              </span>
            </div>
          </div>
        </div>

        <!-- Options (only for account mode) -->
        <div v-if="importMode === 'account'" class="form-section">
          <h4>Options</h4>
          <label class="checkbox-option">
            <input type="checkbox" v-model="autoCategorize">
            <span>Automatically categorize transactions</span>
          </label>
        </div>
      </div>
      
      <div class="modal-actions">
        <button 
          class="btn btn-primary" 
          @click="startImport"
          :disabled="!canImport || importing"
        >
          {{ importing ? 'Importing...' : `Import ${selectedFiles.length} file(s)` }}
        </button>
        <button class="btn btn-link" @click="$emit('close')" :disabled="importing">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import AppIcon from './AppIcon.vue'
import { onUnmounted } from 'vue'

export default {
  name: 'TransactionImportModal',
  components: { AppIcon },
  props: {
    show: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'import-started', 'import-complete'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    
    const fileInput = ref(null)
    const selectedFiles = ref([])
    const importMode = ref('training')
    const selectedAccountId = ref('')
    const autoCategorize = ref(true)
    const importing = ref(false)
    const loadingAccounts = ref(false)
    const accounts = ref([])

    const pollInterval = ref(null)
    const importStatus = ref(null)

    const hasAccounts = computed(() => accounts.value.length > 0)

    const selectedAccount = computed(() => {
      return accounts.value.find(a => a.id === selectedAccountId.value)
    })

    const groupedAccounts = computed(() => {
      const groups = {}
      for (const account of accounts.value) {
        const ownerName = account.owner.name
        if (!groups[ownerName]) {
          groups[ownerName] = {
            owner: ownerName,
            accounts: []
          }
        }
        groups[ownerName].accounts.push(account)
      }
      return Object.values(groups)
    })

    const canImport = computed(() => {
      if (selectedFiles.value.length === 0) return false
      if (importMode.value === 'account' && !selectedAccountId.value) return false
      return true
    })

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      selectedFiles.value.push(...files)
      event.target.value = ''
    }

    const handleDrop = (event) => {
      const files = Array.from(event.dataTransfer.files)
      const validFiles = files.filter(f => 
        f.name.toLowerCase().endsWith('.csv') || 
        f.name.toLowerCase().endsWith('.xlsx')
      )
      selectedFiles.value.push(...validFiles)
    }

    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }

    const loadAccounts = async () => {
      loadingAccounts.value = true
      try {
        const response = await axios.get(`${API_BASE}/accounts/list-simple`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        accounts.value = response.data.accounts || []
        
        // Switch to training mode if no accounts
        if (accounts.value.length === 0) {
          importMode.value = 'training'
        }
      } catch (error) {
        console.error('Failed to load accounts:', error)
      } finally {
        loadingAccounts.value = false
      }
    }

    const startImport = async () => {
      if (!canImport.value || importing.value) return
      
      importing.value = true
      emit('import-started')
      
      try {
        for (const file of selectedFiles.value) {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('import_mode', importMode.value)
          formData.append('auto_categorize', importMode.value === 'account' ? autoCategorize.value : 'true')
          
          if (importMode.value === 'account') {
            formData.append('account_id', selectedAccountId.value)
          }
          
          // ✅ START IMPORT - GET JOB_ID
          const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'multipart/form-data'
            }
          })
          
          const jobId = response.data.job_id
          
          // ✅ START POLLING
          await pollJobStatus(jobId, file.name)
        }
        
        emit('close')
        
      } catch (error) {
        console.error('Import failed:', error)
        console.error('Import failed:', error.response?.data)
      } finally {
        importing.value = false
        selectedFiles.value = []
      }
    }

    const pollJobStatus = async (jobId, filename) => {
      return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
          try {
            const response = await axios.get(
              `${API_BASE}/transactions/import/status/${jobId}`,
              { headers: { 'Authorization': `Bearer ${authStore.token}` } }
            )
            
            const status = response.data
            importStatus.value = status
            
            // ✅ EMIT PROGRESS TO PARENT
            if (status.message) {
              emit('import-progress', {
                filename,
                message: status.message,
                progress: status.progress,
                total: status.total,
                step: status.current_step
              })
            }
            
            // ✅ CHECK IF DONE
            if (status.status === 'complete') {
              clearInterval(interval)
              
              const result = status.result || {}
              const stats = result.summary || {}
              
              // Build detailed message
              let message = `Imported ${stats.rows_inserted || 0} transactions!\n\n`
              
              if (stats.categories_trained) {
                message += `🎓 Trained ${stats.categories_trained} categories\n`
                if (stats.training_log && stats.training_log.length > 0) {
                  const lastItems = stats.training_log.slice(-5)
                  message += lastItems.map(item => `   • ${item}`).join('\n')
                }
              }
              
              emit('import-complete', {
                success: true,
                message: message
              })
              
              resolve()
            } else if (status.status === 'failed') {
              clearInterval(interval)
              reject(new Error(status.error || 'Import failed'))
            }
            
          } catch (error) {
            clearInterval(interval)
            reject(error)
          }
        }, 2000) // Poll every 2 seconds
      })
    }

    // Cleanup on unmount
    
    onUnmounted(() => {
      if (pollInterval.value) {
        clearInterval(pollInterval.value)
      }
    })

    watch(() => props.show, (newVal) => {
      if (newVal) {
        loadAccounts()
      }
    })

    return {
      fileInput,
      selectedFiles,
      importMode,
      selectedAccountId,
      selectedAccount,
      autoCategorize,
      importing,
      loadingAccounts,
      groupedAccounts,
      hasAccounts,
      canImport,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      removeFile,
      startImport
    }
  }
}
</script>

<style scoped>
.import-modal {
  max-width: 45rem;
}

.form-section {
  margin-bottom: var(--gap-large);
}

.form-section h4 {
  margin-bottom: var(--gap-standard);
  font-size: var(--text-medium);
  font-weight: 600;
}

.file-drop-zone {
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  padding: var(--gap-large);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 10rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-drop-zone:hover {
  border-color: var(--color-button-active);
  background: rgba(0, 0, 0, 0.02);
}

.drop-placeholder p {
  margin: var(--gap-small) 0;
}

.help-text {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.file-list {
  width: 100%;
}

.file-item {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
  margin-bottom: var(--gap-small);
}

.file-item span {
  flex: 1;
  text-align: left;
}

.btn-remove {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 0 var(--gap-small);
}

.btn-remove:hover {
  color: var(--color-danger);
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: var(--gap-small);
  padding: var(--gap-standard);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.radio-option:hover {
  background: rgba(0, 0, 0, 0.02);
}

.radio-option.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.radio-content {
  flex: 1;
}

.radio-content p {
  margin: 0.25rem 0 0 0;
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.warning-text {
  color: var(--color-warning);
  font-size: var(--text-small);
}

.form-select {
  width: 100%;
  padding: var(--gap-small);
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-background-light);
  font-size: var(--text-small);
}

.account-preview {
  margin-top: var(--gap-standard);
  padding: var(--gap-standard);
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.preview-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  margin-bottom: var(--gap-small);
}

.preview-content {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  flex-wrap: wrap;
}

.owner-badge {
  padding: 0.25rem var(--gap-small);
  border-radius: var(--radius);
  color: white;
  font-size: var(--text-small);
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  cursor: pointer;
}

.loading-text {
  padding: var(--gap-standard);
  text-align: center;
  color: var(--color-text-muted);
}
</style>