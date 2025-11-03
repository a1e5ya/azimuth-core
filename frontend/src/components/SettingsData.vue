<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Data & Privacy</div>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Automatic Backups</div>
        <div class="setting-desc">Backup database daily</div>
      </div>
      <div :class="['toggle', autoBackup ? 'active' : '']" @click="toggleAutoBackup"></div>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Database Location</div>
        <div class="setting-desc">{{ databasePath }}</div>
      </div>
      <button class="btn btn-secondary" @click="openDatabaseFolder">Open</button>
    </div>
    
    <div class="btn-row">
      <button @click="backupData" class="btn btn-primary" :disabled="backingUp">
        {{ backingUp ? 'Backing up...' : 'Backup Now' }}
      </button>
      <button @click="restoreData" class="btn btn-secondary">Restore</button>
      <button @click="triggerImport" class="btn btn-primary">Import CSV</button>
      <button @click="exportData" class="btn btn-secondary" :disabled="exporting">
        {{ exporting ? 'Exporting...' : 'Export All' }}
      </button>
    </div>
    
    <div class="btn-row">
      <button @click="viewHistory" class="btn btn-secondary" style="flex: 1;">View Import History</button>
    </div>
    
    <hr class="divider">
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Data Stored</div>
      </div>
      <span class="setting-value">{{ dataStats.databaseSize }}</span>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Last Backup</div>
      </div>
      <span class="setting-value">{{ dataStats.lastBackup }}</span>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Total Transactions</div>
      </div>
      <span class="setting-value">{{ formatNumber(dataStats.totalTransactions) }}</span>
    </div>

    <!-- Hidden file input for restore -->
    <input 
      ref="restoreFileInput" 
      type="file" 
      accept=".db,.sqlite,.sqlite3" 
      style="display: none"
      @change="handleRestoreFile"
    >

    <!-- Hidden file input for CSV import -->
    <input 
      ref="importFileInput" 
      type="file" 
      accept=".csv" 
      style="display: none"
      @change="handleImportFile"
    >
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'SettingsData',
  emits: ['data-imported'],
  setup(props, { emit }) {
    const autoBackup = ref(false)
    const databasePath = ref('/data/finance.db')
    const backingUp = ref(false)
    const exporting = ref(false)
    const restoreFileInput = ref(null)
    const importFileInput = ref(null)

    const dataStats = ref({
      totalTransactions: 0,
      databaseSize: '0 MB',
      lastBackup: 'Never'
    })

    const formatNumber = (num) => {
      return num.toLocaleString()
    }

    const loadDataStats = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/transactions/stats', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          dataStats.value.totalTransactions = data.total_count || 0
        }

        // Load database stats
        const statsResponse = await fetch('http://localhost:8001/system/database-stats', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (statsResponse.ok) {
          const stats = await statsResponse.json()
          dataStats.value.databaseSize = stats.size || '0 MB'
          dataStats.value.lastBackup = stats.last_backup || 'Never'
        }
      } catch (error) {
        console.error('Failed to load data stats:', error)
      }
    }

    const toggleAutoBackup = () => {
      autoBackup.value = !autoBackup.value
      // TODO: Save preference to backend
      alert(`Auto-backup ${autoBackup.value ? 'enabled' : 'disabled'}`)
    }

    const openDatabaseFolder = () => {
      alert('Database location: ' + databasePath.value)
      // In a desktop app, this would open the file explorer
    }

    const backupData = async () => {
      try {
        backingUp.value = true
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/system/backup', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `finance-backup-${new Date().toISOString().split('T')[0]}.db`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
          
          alert('✅ Backup created successfully!')
          await loadDataStats()
        } else {
          const data = await response.json()
          alert('❌ ' + (data.detail || 'Backup failed'))
        }
      } catch (error) {
        console.error('Backup failed:', error)
        alert('❌ Backup failed')
      } finally {
        backingUp.value = false
      }
    }

    const restoreData = () => {
      if (confirm('⚠️ Restoring a backup will replace ALL current data. Continue?')) {
        restoreFileInput.value?.click()
      }
    }

    const handleRestoreFile = async (event) => {
      const file = event.target.files?.[0]
      if (!file) return

      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('http://localhost:8001/system/restore', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        })

        if (response.ok) {
          alert('✅ Database restored successfully! Reloading...')
          window.location.reload()
        } else {
          const data = await response.json()
          alert('❌ ' + (data.detail || 'Restore failed'))
        }
      } catch (error) {
        console.error('Restore failed:', error)
        alert('❌ Restore failed')
      }

      // Reset input
      event.target.value = ''
    }

    const triggerImport = () => {
      importFileInput.value?.click()
    }

    const handleImportFile = async (event) => {
      const file = event.target.files?.[0]
      if (!file) return

      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('http://localhost:8001/transactions/import', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        })

        if (response.ok) {
          const result = await response.json()
          alert(`✅ Import completed!\nImported: ${result.rows_imported}\nDuplicates: ${result.rows_duplicated}\nErrors: ${result.rows_errors}`)
          emit('data-imported')
          await loadDataStats()
        } else {
          const data = await response.json()
          alert('❌ ' + (data.detail || 'Import failed'))
        }
      } catch (error) {
        console.error('Import failed:', error)
        alert('❌ Import failed')
      }

      // Reset input
      event.target.value = ''
    }

    const exportData = async () => {
      try {
        exporting.value = true
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/transactions/export', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `finance-export-${new Date().toISOString().split('T')[0]}.csv`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
          
          alert('✅ Data exported successfully!')
        } else {
          const data = await response.json()
          alert('❌ ' + (data.detail || 'Export failed'))
        }
      } catch (error) {
        console.error('Export failed:', error)
        alert('❌ Export failed')
      } finally {
        exporting.value = false
      }
    }

    const viewHistory = () => {
      alert('Import history view coming soon!')
      // TODO: Show modal with import batch history
    }

    onMounted(() => {
      loadDataStats()
    })

    return {
      autoBackup,
      databasePath,
      dataStats,
      backingUp,
      exporting,
      restoreFileInput,
      importFileInput,
      formatNumber,
      toggleAutoBackup,
      openDatabaseFolder,
      backupData,
      restoreData,
      handleRestoreFile,
      triggerImport,
      handleImportFile,
      exportData,
      viewHistory
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
</style>