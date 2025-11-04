<!-- Settings Security - NO custom styles, uses global -->
<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Security & Sessions</div>
    </div>
    
    <div class="form-row">
      <label>Auto-logout Timeout</label>
      <select v-model="securitySettings.autoLogoutTimeout" @change="saveSecuritySettings" class="form-select">
        <option value="15">15 minutes</option>
        <option value="30">30 minutes</option>
        <option value="60">1 hour</option>
        <option value="120">2 hours</option>
        <option value="240">4 hours</option>
        <option value="0">Never</option>
      </select>
    </div>
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Current Session</div>
        <div class="setting-desc">Started {{ sessionStartTime }}</div>
      </div>
      <button @click="logout" class="btn btn-danger">Logout</button>
    </div>
    
    <button @click="viewLoginHistory" class="btn btn-secondary" style="width: 100%; margin-bottom: 0.75rem;">
      View Login History
    </button>
    
    <hr class="divider">
    
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">Activity Log Entries</div>
      </div>
      <span class="setting-value">{{ formatNumber(activityLogCount) }}</span>
    </div>
    
    <button @click="viewActivityLog" class="btn btn-secondary" style="width: 100%;">
      View Activity Log
    </button>

    <!-- Login History Modal -->
    <div v-if="showLoginHistory" class="modal-overlay" @click="showLoginHistory = false">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <h3>Login History</h3>
          <button class="close-btn" @click="showLoginHistory = false">×</button>
        </div>
        <div class="modal-body">
          <div class="activity-list">
            <div v-for="login in loginHistory" :key="login.id" class="activity-item">
              <div class="activity-icon">🔐</div>
              <div class="activity-details">
                <div class="activity-action">{{ login.action }}</div>
                <div class="activity-meta">{{ login.created_at }} • {{ login.ip_address }}</div>
              </div>
            </div>
            <div v-if="loginHistory.length === 0" class="empty-state">
              No login history found
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showLoginHistory = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>

    <!-- Activity Log Modal -->
    <div v-if="showActivityLog" class="modal-overlay" @click="showActivityLog = false">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <h3>Activity Log</h3>
          <button class="close-btn" @click="showActivityLog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="activity-list">
            <div v-for="log in activityLogs" :key="log.id" class="activity-item">
              <div class="activity-icon">{{ getActivityIcon(log.entity) }}</div>
              <div class="activity-details">
                <div class="activity-action">{{ log.action }} • {{ log.entity }}</div>
                <div class="activity-meta">{{ log.created_at }}</div>
              </div>
            </div>
            <div v-if="activityLogs.length === 0" class="empty-state">
              No activity logs found
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showActivityLog = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
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