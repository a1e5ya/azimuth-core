<!--
  SettingsSecurity Component - Session & Activity Monitoring
  
  Provides security information display:
  - Current session duration
  - Activity log with entity icons
  - Real-time session time updates
  
  Features:
  - Session start time calculation
  - Activity log display (transactions, categories, chat, auth, system)
  - Icon mapping for different activity types
  - Auto-refresh session time every minute
  - Date/time formatting
  
  Activity Types:
  - transaction: Credit card icon
  - category: Apps add icon
  - chat: Comment icon
  - auth: Lock icon
  - system: Settings icon
  
  API Endpoints:
  - GET /system/activity-log - Load session info and activity logs
  
  Authentication:
  - Uses localStorage token
  - Requires Bearer authentication
-->

<!-- Settings Security -->
<template>
  <div class="card settings-card">
    
    <!-- Session Information -->
    <div class="stat-row">
      <span>Session Started:</span>
      <span>{{ sessionStartTime }}</span>
    </div>
    
    <!-- Activity Log List -->
    <div class="log-list">
      <div v-for="log in activityLogs" :key="log.id" class="log-item">
        <AppIcon :name="getActivityIcon(log.entity)" size="small" />
        <span class="log-entity">{{ log.entity }}</span>
        <span class="log-action">{{ log.action }}</span>
        <span class="log-time">{{ formatDate(log.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import AppIcon from './AppIcon.vue'

export default {
  name: 'SettingsSecurity',
  components: { AppIcon },
  setup() {
    const sessionStartTime = ref('Loading...')
    const activityLogs = ref([])

    /**
     * Formats date string to locale string
     * @param {string} dateStr - Date string from backend
     * @returns {string} Formatted date and time
     */
    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleString()
    }

    /**
     * Gets icon name for activity entity type
     * @param {string} entity - Entity type (transaction, category, chat, auth, system)
     * @returns {string} Icon name
     */
    const getActivityIcon = (entity) => {
      const icons = { 
        'transaction': 'credit-card', 
        'category': 'apps-add', 
        'chat': 'comment-alt', 
        'auth': 'lock', 
        'system': 'settings' 
      }
      return icons[entity] || 'circle'
    }

    /**
     * Loads session info and calculates session duration
     * @async
     * @returns {Promise<void>}
     */
    const loadSessionInfo = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          sessionStartTime.value = 'Unknown'
          return
        }
        
        const response = await fetch('http://localhost:8001/system/activity-log', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (response.ok) {
          const logs = await response.json()
          const lastLogin = logs.find(log => log.entity === 'auth' && log.action === 'login')
          
          if (lastLogin && lastLogin.created_at) {
            const loginDate = new Date(lastLogin.created_at.replace(' ', 'T'))
            const elapsed = Date.now() - loginDate.getTime()
            const hours = Math.floor(elapsed / (1000 * 60 * 60))
            const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60))
            sessionStartTime.value = hours > 0 ? `${hours} hour${hours > 1 ? 's' : ''} ago` : `${minutes} minute${minutes > 1 ? 's' : ''} ago`
            return
          }
        }
      } catch (error) {
        console.error('Failed to load session info:', error)
      }
      sessionStartTime.value = 'Unknown'
    }

    /**
     * Loads activity log from backend
     * @async
     * @returns {Promise<void>}
     */
    const loadActivityLog = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await fetch('http://localhost:8001/system/activity-log', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          activityLogs.value = await response.json()
        }
      } catch (error) {
        console.error('Failed to load activity log:', error)
      }
    }

    onMounted(() => {
      loadSessionInfo()
      loadActivityLog()
      setInterval(loadSessionInfo, 60000)
    })

    return {
      sessionStartTime, activityLogs, formatDate, getActivityIcon
    }
  }
}
</script>

<style scoped>
.log-list {
  margin-top: var(--gap-standard);
}

.log-item {
  display: grid;
  grid-template-columns: 40px 100px 100px 1fr;
  gap: var(--gap-small);
  padding: var(--gap-small);
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9em;
  align-items: center;
}

.log-entity {
  font-weight: 500;
  text-transform: capitalize;
}

.log-action {
  color: var(--text-muted);
}

.log-time {
  color: var(--text-muted);
  font-size: 0.85em;
}
</style>