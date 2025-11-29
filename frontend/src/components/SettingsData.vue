<!--
  SettingsData Component - Database Backup & Restore
  
  Provides database management operations:
  - Backup database to downloadable .db file
  - Restore database from uploaded .db file
  - Confirmation modals for all operations
  
  Features:
  - One-click database backup download
  - Database restore with confirmation
  - Automatic filename with current date
  - Success/error notifications
  - Auto-reload after restore
  - Loading states during operations
  
  Events:
  - @data-imported: Emitted after successful restore
  
  Authentication:
  - Uses localStorage token (azimuth_token)
  - All requests require Bearer authentication
  
  API Endpoints:
  - GET /backup/export - Download database backup
  - POST /backup/import - Upload and restore database
  
  Safety:
  - Confirmation required for restore operation
  - Warning about data replacement
  - Cannot be undone notice
-->

<template>
  <div class="card settings-card">
    
    <!-- Backup and Restore Buttons -->
    <div class="btn-row">
      <button @click="backupData" class="btn btn-primary" :disabled="backingUp">
        {{ backingUp ? 'Backing up...' : 'Backup Database' }}
      </button>
      <button @click="restoreData" class="btn btn-primary">
        Restore Database
      </button>
    </div>
    
    <!-- Hidden File Input for Restore -->
    <input 
      ref="restoreFileInput" 
      type="file" 
      accept=".db" 
      style="display: none" 
      @change="handleRestoreFile"
    />

    <!-- Confirmation/Notification Modal -->
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <!-- Modal Header -->
        <div class="modal-header">
          <h3>{{ modalTitle }}</h3>
          <button class="close-btn" @click="showModal = false">×</button>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          <p>{{ modalMessage }}</p>
        </div>
        
        <!-- Modal Actions -->
        <div class="modal-actions">
          <button @click="cancelModal" class="btn btn-secondary">{{ modalCancelText }}</button>
          <button v-if="modalConfirmAction" @click="modalConfirmAction" class="btn btn-primary">
            {{ modalConfirmText }}
          </button>
        </div>
      </div>
    </div>
    
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'SettingsData',
  emits: ['data-imported'],
  setup() {
    const backingUp = ref(false)
    const restoreFileInput = ref(null)
    const showModal = ref(false)
    const modalTitle = ref('')
    const modalMessage = ref('')
    const modalConfirmText = ref('OK')
    const modalCancelText = ref('Cancel')
    const modalConfirmAction = ref(null)

    /**
     * Shows notification modal
     * @param {string} title - Modal title
     * @param {string} message - Modal message
     * @param {string} confirmText - Confirm button text
     * @returns {void}
     */
    const showNotification = (title, message, confirmText = 'OK') => {
      modalTitle.value = title
      modalMessage.value = message
      modalConfirmText.value = confirmText
      modalCancelText.value = 'Close'
      modalConfirmAction.value = null
      showModal.value = true
    }

    /**
     * Shows confirmation modal with callback
     * @param {string} title - Modal title
     * @param {string} message - Modal message
     * @param {Function} onConfirm - Callback function on confirmation
     * @returns {void}
     */
    const showConfirmation = (title, message, onConfirm) => {
      modalTitle.value = title
      modalMessage.value = message
      modalConfirmText.value = 'Continue'
      modalCancelText.value = 'Cancel'
      modalConfirmAction.value = () => {
        showModal.value = false
        onConfirm()
      }
      showModal.value = true
    }

    /**
     * Cancels modal and resets action
     * @returns {void}
     */
    const cancelModal = () => {
      showModal.value = false
      modalConfirmAction.value = null
    }

    /**
     * Downloads database backup as .db file
     * @async
     * @returns {Promise<void>}
     */
    const backupData = async () => {
      try {
        backingUp.value = true
        const token = localStorage.getItem('azimuth_token')
        if (!token) {
          showNotification('Not Authenticated', 'Please login to backup your database.')
          return
        }
        
        const response = await fetch('http://localhost:8001/backup/export', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (response.ok) {
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `azimuth_backup_${new Date().toISOString().split('T')[0]}.db`
          a.click()
          window.URL.revokeObjectURL(url)
          showNotification('Success', 'Backup downloaded successfully!')
        } else {
          const data = await response.json()
          showNotification('Backup Failed', data.detail || 'Failed to create backup.')
        }
      } catch (error) {
        console.error('Backup failed:', error)
        showNotification('Error', 'Backup failed: ' + error.message)
      } finally {
        backingUp.value = false
      }
    }

    /**
     * Opens file picker for database restore
     * @returns {void}
     */
    const restoreData = () => {
      showConfirmation(
        'Restore Database?',
        'This will replace ALL current data with the backup. This cannot be undone!',
        () => {
          restoreFileInput.value?.click()
        }
      )
    }

    /**
     * Handles database restore file upload
     * @async
     * @param {Event} event - File input change event
     * @returns {Promise<void>}
     */
    const handleRestoreFile = async (event) => {
      const file = event.target.files?.[0]
      if (!file) return
      
      try {
        const token = localStorage.getItem('azimuth_token')
        if (!token) {
          showNotification('Not Authenticated', 'Please login to restore your database.')
          return
        }
        
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await fetch('http://localhost:8001/backup/import', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        })
        
        const data = await response.json()
        
        if (response.ok) {
          showNotification('Success', 'Database restored! Page will reload in 2 seconds.')
          setTimeout(() => window.location.reload(), 2000)
        } else {
          showNotification('Restore Failed', data.detail || 'Failed to restore backup.')
        }
      } catch (error) {
        console.error('Restore failed:', error)
        showNotification('Error', 'Restore failed: ' + error.message)
      } finally {
        event.target.value = ''
      }
    }

    return {
      backingUp,
      restoreFileInput,
      showModal,
      modalTitle,
      modalMessage,
      modalConfirmText,
      modalCancelText,
      modalConfirmAction,
      backupData,
      restoreData,
      handleRestoreFile,
      cancelModal
    }
  }
}
</script>

<style scoped>

.btn-row {
  display: flex;
  gap: var(--gap-large);
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
  z-index: 9999;
}

.modal-content {
  background: #dddddd;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: var(--gap-large);
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 10000;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-large);
  padding-bottom: var(--gap-large);
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: var(--text-large);
  font-weight: 600;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-btn:hover {
  color: #111827;
}

.modal-body {
  margin-bottom: var(--gap-large);
  line-height: 1.6;
}

.modal-body p {
  margin: 0;
  color: #374151;
}

.modal-actions {
  display: flex;
  gap: var(--gap-large);
  justify-content: flex-end;
}
</style>