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

    <input ref="restoreFileInput" type="file" accept=".db,.sqlite,.sqlite3" style="display: none" @change="handleRestoreFile">
    <input ref="importFileInput" type="file" accept=".csv" style="display: none" @change="handleImportFile">
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
    const dataStats = ref({ totalTransactions: 0, databaseSize: '0 MB', lastBackup: 'Never' })

    const formatNumber = (num) => num.toLocaleString()

    const loadDataStats = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/transactions/stats', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          const data = await response.json()
          dataStats.value.totalTransactions = data.total_count || 0
        }
        const statsResponse = await fetch('http://localhost:8001/system/database-stats', {
          headers: { 'Authorization': `Bearer ${token}` }
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
      alert(`Auto-backup ${autoBackup.value ? 'enabled' : 'disabled'}`)
    }

    const openDatabaseFolder = () => alert('Database location: ' + databasePath.value)

    const backupData = async () => {
      try {
        backingUp.value = true
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/system/backup', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
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
          headers: { 'Authorization': `Bearer ${token}` },
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
      event.target.value = ''
    }

    const triggerImport = () => importFileInput.value?.click()

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
          headers: { 'Authorization': `Bearer ${token}` },
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
      event.target.value = ''
    }

    const exportData = async () => {
      try {
        exporting.value = true
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/transactions/export', {
          headers: { 'Authorization': `Bearer ${token}` }
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

    const viewHistory = () => alert('Import history view coming soon!')

    onMounted(() => loadDataStats())

    return {
      autoBackup, databasePath, dataStats, backingUp, exporting, restoreFileInput, importFileInput,
      formatNumber, toggleAutoBackup, openDatabaseFolder, backupData, restoreData, handleRestoreFile,
      triggerImport, handleImportFile, exportData, viewHistory
    }
  }
}
</script>