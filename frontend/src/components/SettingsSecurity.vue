<!-- Settings Security - NO custom styles, uses global -->
<template>
  <div class="card settings-card">

    

    
    
      Activity Log

  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'SettingsSecurity',
  setup() {
    const securitySettings = ref({ autoLogoutTimeout: '60' })
    const sessionStartTime = ref('Loading...')
    const activityLogCount = ref(0)
    const showLoginHistory = ref(false)
    const showActivityLog = ref(false)
    const loginHistory = ref([])
    const activityLogs = ref([])

    const formatNumber = (num) => num.toLocaleString()

    const getActivityIcon = (entity) => {
      const icons = { 'transaction': '💰', 'category': '📁', 'chat': '💬', 'auth': '🔐', 'system': '⚙️' }
      return icons[entity] || '📋'
    }

    const loadSessionInfo = () => {
      const loginTime = localStorage.getItem('loginTime')
      if (loginTime) {
        const elapsed = Date.now() - parseInt(loginTime)
        const hours = Math.floor(elapsed / (1000 * 60 * 60))
        const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60))
        sessionStartTime.value = hours > 0 ? `${hours} hour${hours > 1 ? 's' : ''} ago` : `${minutes} minute${minutes > 1 ? 's' : ''} ago`
      } else {
        sessionStartTime.value = 'Unknown'
      }
    }

    const loadActivityLogCount = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/system/activity-log/count', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          const data = await response.json()
          activityLogCount.value = data.count || 0
        }
      } catch (error) {
        console.error('Failed to load activity log count:', error)
      }
    }

    const saveSecuritySettings = () => {}

    const logout = () => {
      if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('token')
        localStorage.removeItem('loginTime')
        window.location.href = '/'
      }
    }

    const viewLoginHistory = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/system/login-history', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          loginHistory.value = await response.json()
          showLoginHistory.value = true
        }
      } catch (error) {
        console.error('Failed to load login history:', error)
      }
    }

    const viewActivityLog = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/system/activity-log', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          activityLogs.value = await response.json()
          showActivityLog.value = true
        }
      } catch (error) {
        console.error('Failed to load activity log:', error)
      }
    }

    onMounted(() => {
      loadSessionInfo()
      loadActivityLogCount()
      setInterval(loadSessionInfo, 60000)
    })

    return {
      securitySettings, sessionStartTime, activityLogCount, showLoginHistory, showActivityLog,
      loginHistory, activityLogs, formatNumber, getActivityIcon, saveSecuritySettings,
      logout, viewLoginHistory, viewActivityLog
    }
  }
}
</script>