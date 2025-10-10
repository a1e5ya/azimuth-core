<template>
  <div class="tab-content">
    <!-- System Status -->
    <div class="container">
      <div class="text-medium section-header">System Status</div>
      <div class="grid grid-auto">
        <div class="card text-center">
          <div class="text-small text-muted">Authentication</div>
          <div class="text-medium">{{ user ? 'Signed In' : 'Anonymous' }}</div>
          <div class="text-small text-light">{{ user ? user.email : 'Not authenticated' }}</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Backend Status</div>
          <div class="text-medium">{{ backendStatus }}</div>
          <div class="text-small text-light">API Connection</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Phase Progress</div>
          <div class="text-medium">{{ phase }}</div>
          <div class="text-small text-light">Current Development Phase</div>
        </div>
      </div>
    </div>

    <!-- User Profile -->
    <div class="container">
      <div class="text-medium section-header">User Profile</div>
      <div v-if="user">
        <div class="text-small"><strong>Email:</strong> {{ user.email }}</div>
        <div class="text-small"><strong>User ID:</strong> {{ getUserId() }}</div>
        <div class="text-small"><strong>Display Name:</strong> {{ user.display_name || 'Not set' }}</div>
        <div class="text-small"><strong>Account Created:</strong> {{ formatDate(user.created_at) }}</div>
        <button class="btn" @click="$emit('logout')">Sign Out</button>
      </div>
      <div v-else>
        <div class="text-small text-light">Sign in to access personalized features and secure data storage.</div>
        <button class="btn" @click="$emit('logout')">Sign In</button>
      </div>
    </div>

    <!-- Data Management -->
    <div class="container">
      <div class="text-medium section-header">Data Management</div>
      <div class="flex flex-gap flex-wrap">
        <button class="btn" @click="$emit('show-tab', 'transactions')">Import Data</button>
        <button class="btn">Export Data</button>
        <button class="btn" @click="showResetModal = true" :disabled="!transactionCount || transactionCount === 0">
          Reset All Transactions
        </button>
        <button class="btn">Reset Categories</button>
      </div>
      
      <div v-if="transactionCount > 0" class="text-small text-muted" style="margin-top: var(--gap-small)">
        Current database: {{ transactionCount.toLocaleString() }} transactions
      </div>
    </div>

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="modal-overlay" @click="showResetModal = false">
      <div class="modal-content reset-modal" @click.stop>
        <div class="modal-header">
          <h3>Reset All Transaction Data</h3>
          <button class="close-btn" @click="showResetModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <div class="reset-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>This action cannot be undone!</strong></p>
              <p>This will permanently delete all {{ transactionCount?.toLocaleString() || 0 }} transactions and import history.</p>
              <ul>
                <li>All transaction records will be removed</li>
                <li>All import batches will be cleared</li>
                <li>Categories will remain intact</li>
                <li>This cannot be reversed</li>
              </ul>
              <p>Are you absolutely sure you want to continue?</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmReset"
            :disabled="resetting"
          >
            {{ resetting ? 'Resetting...' : 'Yes, Reset All Data' }}
          </button>
          <button class="btn btn-link" @click="showResetModal = false" :disabled="resetting">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'SettingsTab',
  props: {
    user: Object,
    backendStatus: {
      type: String,
      default: 'Checking...'
    },
    phase: {
      type: String,
      default: 'Phase 1'
    }
  },
  emits: ['logout', 'show-tab', 'add-chat-message', 'transactions-reset'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    
    const showResetModal = ref(false)
    const resetting = ref(false)
    const transactionCount = ref(0)

    const getUserId = () => {
      if (!props.user) return 'N/A'
      
      const id = props.user.id || props.user.uid || ''
      
      return id.length > 16 ? id.substring(0, 16) + '...' : id
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      
      try {
        return new Date(dateString).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      } catch (error) {
        return dateString
      }
    }

    const loadTransactionCount = async () => {
      if (!props.user) return
      
      try {
        const token = authStore.token
        const response = await axios.get(`${API_BASE}/transactions/summary`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        transactionCount.value = response.data.total_transactions || 0
      } catch (error) {
        console.error('Failed to load transaction count:', error)
        transactionCount.value = 0
      }
    }

    const confirmReset = async () => {
      if (resetting.value) return
      
      resetting.value = true
      
      try {
        const token = authStore.token
        
        const response = await axios.post(`${API_BASE}/transactions/reset`, {}, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        console.log('✅ Reset successful:', response.data)
        
        transactionCount.value = 0
        
        emit('add-chat-message', {
          message: 'Reset all transaction data',
          response: `Successfully deleted ${response.data.deleted_count} transactions. All transaction data has been cleared.`
        })
        
        emit('transactions-reset')
        
        showResetModal.value = false
        
      } catch (error) {
        console.error('❌ Reset failed:', error)
        
        const errorMessage = error.response?.data?.detail || 
                           error.response?.data?.message || 
                           'Failed to reset transactions'
        
        emit('add-chat-message', {
          response: `Reset failed: ${errorMessage}`
        })
      } finally {
        resetting.value = false
      }
    }

    onMounted(async () => {
      if (props.user) {
        await loadTransactionCount()
      }
    })

    return {
      showResetModal,
      resetting,
      transactionCount,
      getUserId,
      formatDate,
      loadTransactionCount,
      confirmReset
    }
  }
}
</script>

<style scoped>
.reset-warning {
  display: flex;
  gap: var(--gap-standard);
  padding: var(--gap-standard);
  background: rgba(239, 68, 68, 0.05);
  border-radius: var(--radius);
}

.warning-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.warning-text p {
  margin-bottom: var(--gap-small);
}

.warning-text ul {
  margin: var(--gap-small) 0;
  padding-left: 1.5rem;
}

.warning-text ul li {
  margin-bottom: 0.25rem;
}

.reset-modal {
  max-width: 30rem;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>