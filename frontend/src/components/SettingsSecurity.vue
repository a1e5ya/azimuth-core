<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Security & Sessions</div>
    </div>
    
    <div class="form-row">
      <label>Auto-logout Timeout</label>
      <select v-model="securitySettings.autoLogoutTimeout" @change="saveSecuritySettings">
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
        <h3>Login History</h3>
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
        <div class="modal-actions">
          <button @click="showLoginHistory = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>

    <!-- Activity Log Modal -->
    <div v-if="showActivityLog" class="modal-overlay" @click="showActivityLog = false">
      <div class="modal-content modal-large" @click.stop>
        <h3>Activity Log</h3>
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
    const securitySettings = ref({
      autoLogoutTimeout: '60'
    })

    const sessionStartTime = ref('Loading...')
    const activityLogCount = ref(0)
    const showLoginHistory = ref(false)
    const showActivityLog = ref(false)
    const loginHistory = ref([])
    const activityLogs = ref([])

    const formatNumber = (num) => {
      return num.toLocaleString()
    }

    const getActivityIcon = (entity) => {
      const icons = {
        'transaction': '💰',
        'category': '📁',
        'chat': '💬',
        'auth': '🔐',
        'system': '⚙️'
      }
      return icons[entity] || '📋'
    }

    const loadSessionInfo = () => {
      const loginTime = localStorage.getItem('loginTime')
      if (loginTime) {
        const elapsed = Date.now() - parseInt(loginTime)
        const hours = Math.floor(elapsed / (1000 * 60 * 60))
        const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60))
        
        if (hours > 0) {
          sessionStartTime.value = `${hours} hour${hours > 1 ? 's' : ''} ago`
        } else {
          sessionStartTime.value = `${minutes} minute${minutes > 1 ? 's' : ''} ago`
        }
      } else {
        sessionStartTime.value = 'Unknown'
      }
    }

    const loadActivityLogCount = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/system/activity-log/count', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          activityLogCount.value = data.count || 0
        }
      } catch (error) {
        console.error('Failed to load activity log count:', error)
      }
    }

    const saveSecuritySettings = () => {
      // TODO: Save to backend
    }

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
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          loginHistory.value = await response.json()
          showLoginHistory.value = true
        } else {
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
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          activityLogs.value = await response.json()
          showActivityLog.value = true
        } else {
        }
      } catch (error) {
        console.error('Failed to load activity log:', error)
      }
    }

    onMounted(() => {
      loadSessionInfo()
      loadActivityLogCount()
      
      // Update session time every minute
      setInterval(loadSessionInfo, 60000)
    })

    return {
      securitySettings,
      sessionStartTime,
      activityLogCount,
      showLoginHistory,
      showActivityLog,
      loginHistory,
      activityLogs,
      formatNumber,
      getActivityIcon,
      saveSecuritySettings,
      logout,
      viewLoginHistory,
      viewActivityLog
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

.modal-large {
  max-width: 40rem;
}

.activity-list {
  max-height: 25rem;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.activity-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.05);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.activity-details {
  flex: 1;
}

.activity-action {
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.activity-meta {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted);
}
</style>