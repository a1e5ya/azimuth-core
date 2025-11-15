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
              <p>Drop CSV/XLSX files here or click to browse</p>
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
                <p>Import as uncategorized training data (current behavior)</p>
              </div>
            </label>
            
            <label class="radio-option">
              <input 
                type="radio" 
                v-model="importMode" 
                value="account"
              >
              <div class="radio-content">
                <strong>Direct to Account</strong>
                <p>Import to a specific account with categorization</p>
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

        <!-- Options -->
        <div class="form-section">
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
          formData.append('auto_categorize', autoCategorize.value)
          
          if (importMode.value === 'account') {
            formData.append('account_id', selectedAccountId.value)
          }
          
          await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000
          })
        }
        
        emit('import-complete', { 
          success: true, 
          fileCount: selectedFiles.value.length 
        })
        emit('close')
        
      } catch (error) {
        console.error('Import failed:', error)
        emit('import-complete', { 
          success: false, 
          error: error.response?.data?.detail || 'Import failed' 
        })
      } finally {
        importing.value = false
        selectedFiles.value = []
      }
    }

    watch(() => props.show, (newVal) => {
      if (newVal && importMode.value === 'account' && accounts.value.length === 0) {
        loadAccounts()
      }
    })

    watch(importMode, (newVal) => {
      if (newVal === 'account' && accounts.value.length === 0) {
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
</style>