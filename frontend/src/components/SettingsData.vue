<template>
  <div class="card settings-card">
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Auto Backup</div>
      </div>
      <label class="switch">
        <input type="checkbox" v-model="autoBackup" @change="toggleAutoBackup">
        <span class="slider round"></span>
      </label>

    </div>
    
    <div class="btn-row">
      <button @click="backupData" class="btn btn-primary" :disabled="backingUp">
        {{ backingUp ? 'Backing up...' : 'Backup Now' }}
      </button>
      <button @click="restoreData" class="btn btn-primary">Restore</button>
    </div>
        <div class="btn-row">
      <button @click="exportData" class="btn btn-primary" :disabled="exporting">
        {{ exporting ? 'Exporting...' : 'Export All' }}
      </button>
    </div>
    

    
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