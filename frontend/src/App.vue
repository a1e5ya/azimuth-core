<!--
  App Component - Main Application Shell
  
  Root component managing authentication, navigation, and global state:
  - User authentication and session management
  - Tab navigation (Dashboard, Transactions, Categories, Timeline, Settings)
  - Global chat interface with AI assistant
  - Transaction data loading and filtering
  - File upload coordination
  - Backend health monitoring
  
  Features:
  - Login/logout flow with JWT authentication
  - Persistent chat history (last 20 messages)
  - Tab-based navigation with state preservation
  - Real-time backend status monitoring
  - Chat-driven UI actions (filter transactions, navigate tabs)
  - Welcome message for new users
  - Collapsible chat panel
  
  Layout Structure:
  - Login screen (unauthenticated users)
  - Top navigation bar (authenticated users)
  - Main content area (tab-based)
  - Always-visible chat bar at bottom
  
  Tab Components:
  - DashboardTab: Overview and statistics
  - TransactionsTab: Transaction management
  - CategoriesTab: Category hierarchy management
  - TimelineTab: Time-based visualizations
  - SettingsTab: User preferences and system info
-->

<template>
  <div id="app">
    <!-- Login Screen (unauthenticated users only) -->
    <div v-if="!user" class="login-screen">
      <div class="login-container">
        <div class="logo-section">
          <h1 class="museo-dashboard">azimuth<img src="@/assets/logo.png" alt="Azimuth Logo" width="22" class="logo" /></h1> 
          <p class="tagline">Personal Finance Assistant</p>
        </div>
        
        <LoginModal :showModal="true" @close="() => {}" :isFullScreen="true" />
      </div>
    </div>

    <!-- Main Application (authenticated users only) -->
    <div v-else class="authenticated-app">
      <!-- Top Navigation Bar -->
      <div class="top-bar">
        <!-- Logo/Dashboard Button -->
        <button 
          class="btn btn-active museo-dashboard"
          @click="showTab('dashboard')"
        >
          <span class="text-medium">azimuth</span> <img src="@/assets/logo.png" alt="Azimuth Logo" width="18" class="logo" />
        </button>
        
        <!-- Main Navigation Tabs -->
        <div class="flex flex-gap-lg">
          <button 
            class="btn btn-link"
            :class="{ 'btn-active': currentTab === 'transactions' }"
            @click="showTab('transactions')"
          >
            Transactions
          </button>
          <button 
            class="btn btn-link"
            :class="{ 'btn-active': currentTab === 'categories' }"
            @click="showTab('categories')"
          >
            Categories
          </button>
          <button 
            class="btn btn-link"
            :class="{ 'btn-active': currentTab === 'timeline' }"
            @click="showTab('timeline')"
          >
            Timeline
          </button>
        </div>
        
        <!-- User Actions (Settings, Logout) -->
        <div class="flex flex-center flex-gap">
          <span class="text-medium user-info">
            {{ user.display_name || user.email.split('@')[0] }}
          </span>
          
          <button 
            class="btn btn-icon btn-link"
            :class="{ 'btn-active': currentTab === 'settings' }"
            @click="showTab('settings')" 
            title="Settings"
          >
            <AppIcon name="settings-sliders" size="medium" />
          </button>

          <button 
            class="btn btn-icon btn-link" 
            @click="handleLogout" 
            title="Logout"
          >
            <AppIcon name="sign-out" size="medium" />
          </button>
        </div>
      </div>

      <!-- Main Content Area (tab-based) -->
      <div class="main-content" :class="{ 'chat-open': showHistory && chatHistory.length > 0 }">
        
        <!-- Dashboard Tab -->
        <DashboardTab v-if="currentTab === 'dashboard'" />

        <!-- Transactions Tab -->
        <TransactionsTab 
          v-else-if="currentTab === 'transactions'"
          :user="user"
          :transactionCount="transactionCount"
          :recentUploads="recentUploads"
          :transactions="transactions"
          :loading="loading"
          :currentPage="currentPage"
          :pageSize="pageSize"
          :filters="filters"
          :showFilters="showFilters"
          @file-upload="handleFileUpload"
          @refresh-transactions="refreshTransactions"
          @change-page="changePage"
          @categorize-transaction="categorizeTransaction"
          @edit-transaction="editTransaction"
          @update-transaction-count="updateTransactionCount"
          @update-filters="updateFilters"
          @add-chat-message="addChatMessage"
          @update:showFilters="showFilters = $event"
        />
        
        <!-- Categories Tab -->
        <CategoriesTab 
          v-else-if="currentTab === 'categories'"
          :is-active="currentTab === 'categories'"
          @add-chat-message="addChatMessage"
        />

        <!-- Timeline Tab -->
        <TimelineTab v-else-if="currentTab === 'timeline'" />

        <!-- Settings Tab -->
        <SettingsTab 
          v-else-if="currentTab === 'settings'"
          :user="user"
          :backendStatus="backendStatus"
          :phase="phase"
          @logout="handleLogout"
          @show-tab="showTab"
          @chat-cleared="clearChatHistory"
        />
      </div>

      <!-- Always-Visible Chat Bar -->
      <div class="chat-bar-always">
        <!-- Welcome Message (shown when no chat history) -->
        <div v-if="showWelcomeMessage && !chatHistory.length && showChat" class="welcome-message">
          {{ welcomeText }}
        </div>
        
        <!-- Chat History -->
        <div v-if="chatHistory.length > 0 && showHistory && showChat" class="chat-history-simple">
          <div class="chat-messages-simple">
            <div v-for="(item, index) in chatHistory" :key="index" class="message-pair-simple">
              <div v-if="item.message" class="message user-message-simple">
                <div class="message-content-simple">{{ item.message }}</div>
              </div>
              <div class="message bot-message-simple">
                <div class="message-content-simple">{{ item.response }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Thinking Indicator -->
        <div v-if="currentThinking && showChat" class="current-thinking">
          <div class="message bot-message-simple">
            <div class="message-content-simple">{{ currentThinking }}</div>
          </div>
        </div>

        <!-- Chat Input Row -->
        <div class="chat-input-row">
          <!-- Toggle Chat Panel Button -->
          <button 
            class="history-toggle-btn btn-link"
            @click="toggleChatPanel"
            :title="showChat ? 'Close Chat' : 'Open Chat'"
          >
            <AppIcon :name="showChat ? 'angle-down' : 'angle-up'" size="medium" />
          </button>
          
          <!-- Chat Input Field -->
          <input 
            type="text" 
            class="chat-input-always" 
            v-model="chatInput"
            @keypress.enter="sendMessage()"
            @click="openChatPanel"
            :disabled="loading"
          >
          
          <!-- Send Message Button -->
          <button 
            class="btn btn-link" 
            @click="sendMessage()"
            :disabled="loading || !chatInput.trim()"
          >
            <AppIcon name="arrow-right" size="medium" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// Component imports
import AppIcon from '@/components/AppIcon.vue'
import LoginModal from '@/components/LoginModal.vue'
import DashboardTab from '@/components/DashboardTab.vue'
import TransactionsTab from '@/components/TransactionsTab.vue'
import CategoriesTab from '@/components/CategoriesTab.vue'
import TimelineTab from '@/components/TimelineTab.vue'
import SettingsTab from '@/components/SettingsTab.vue'


export default {
  name: 'App',
  components: {
    AppIcon,
    LoginModal,
    DashboardTab,
    TransactionsTab,
    CategoriesTab,
    TimelineTab,
    SettingsTab
  },
  setup() {
    // Auth store instance
    const authStore = useAuthStore()
    const showFilters = ref(false)
    
    /**
     * Core application state
     */
    const currentTab = ref('dashboard')
    const user = ref(null)
    const backendStatus = ref('Checking...')
    const phase = ref('1 - Transaction Import')
    const loading = ref(false)
    
    /**
     * Chat state management
     */
    const chatInput = ref('')
    const chatHistory = ref([])
    const currentThinking = ref('')
    const showWelcomeMessage = ref(true)
    const showHistory = ref(false)
    const showChat = ref(false)
    
    /**
     * Transaction and file upload state
     */
    const transactionCount = ref(0)
    const recentUploads = ref([])
    const transactions = ref([])
    const currentPage = ref(1)
    const pageSize = ref(50)
    const filters = ref({
      startDate: '',
      endDate: '',
      merchant: '',
      categoryId: '',
      minAmount: null,
      maxAmount: null
    })
    
    /**
     * Category selection state
     */
    const selectedCategory = ref(null)
    
    /**
     * API base URL from environment or default
     */
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    /**
     * Computed welcome text with user's name
     * @returns {string} Personalized welcome message
     */
    const welcomeText = computed(() => {
      const userName = user.value ? 
        (user.value.display_name || user.value.email.split('@')[0]) : 
        'there'
      return `Hello, ${userName}! I'm here to help you with your financial data. You can ask questions about budgeting, upload CSV files, or explore your transaction categories.`
    })
    
    /**
     * Scrolls chat history to bottom
     * @async
     * @returns {Promise<void>}
     */
    const scrollToBottom = async () => {
      await nextTick()
      setTimeout(() => {
        const historyElement = document.querySelector('.chat-messages-simple') || 
                              document.querySelector('.chat-history-simple') ||
                              document.querySelector('.chat-bar-always')
        
        if (historyElement) {
          const lastMessage = historyElement.querySelector('.message-pair-simple:last-child') ||
                             historyElement.querySelector('.current-thinking') ||
                             historyElement.lastElementChild
          
          if (lastMessage) {
            lastMessage.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'end'
            })
          } else {
            historyElement.scrollTo({
              top: historyElement.scrollHeight,
              behavior: 'smooth'
            })
          }
        }
      }, 100)
    }

    /**
     * Adds message to chat history
     * Maintains maximum of 20 messages
     * @param {Object} messageData - Message data object
     * @param {string} messageData.message - User message (optional)
     * @param {string} messageData.response - Bot response
     * @returns {void}
     */
    const addChatMessage = (messageData) => {
      chatHistory.value.push({
        message: messageData.message || '',
        response: messageData.response,
        timestamp: new Date().toLocaleTimeString()
      })
      
      showHistory.value = true
      scrollToBottom()
      
      if (chatHistory.value.length > 20) {
        chatHistory.value = chatHistory.value.slice(-20)
      }
    }

    /**
     * Sends message to chat API and handles response
     * Supports retry on authentication failure
     * @async
     * @param {string|null} message - Message to send (uses chatInput if null)
     * @returns {Promise<void>}
     */
    const sendMessage = async (message = null) => {
      const messageText = message || chatInput.value.trim()
      if (!messageText || loading.value) return

      const originalInput = chatInput.value
      loading.value = true
      chatInput.value = ''
      currentThinking.value = 'Thinking...'
      
      showWelcomeMessage.value = false
      showHistory.value = true

      try {
        const headers = {
          Authorization: `Bearer ${authStore.token}`
        }

        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        }, { headers, timeout: 15000 })
        
        const botResponse = response.data.response
        
        addChatMessage({
          message: messageText,
          response: botResponse
        })
        
        // Handle suggested actions from chat
        if (response.data.suggested_action) {
          switch (response.data.suggested_action) {
            case 'filter_transactions':
              currentTab.value = 'transactions'
              if (response.data.action_params) {
                const params = response.data.action_params
                if (params.main_category) {
                  filters.value.mainCategory = params.main_category
                }
                if (params.category_filter) {
                  filters.value.categoryFilter = params.category_filter
                }
                if (params.merchant) {
                  filters.value.merchant = params.merchant
                }
                if (params.main_category) {
                  filters.value.transactionType = params.main_category
                }
                showFilters.value = true
              }
              break
              
            case 'show_transactions_tab':
              currentTab.value = 'transactions'
              break
              
            case 'show_categories_tab':
              currentTab.value = 'categories'
              break
              
            case 'show_timeline':
              currentTab.value = 'timeline'
              break
              
            case 'show_dashboard':
              currentTab.value = 'dashboard'
              break
              
            case 'show_settings':
              currentTab.value = 'settings'
              break
          }
        }
        
      } catch (error) {
        console.error('❌ Chat error:', error)
        
        let errorMessage = 'Error. Please try again.'
        
        if (error.response?.status === 401) {
          try {
            const verifyResult = await authStore.verifyToken()
            if (verifyResult.success) {
              // Retry the request after token refresh
              const retryResponse = await axios.post(`${API_BASE}/chat/command`, {
                message: messageText
              }, { 
                headers: { Authorization: `Bearer ${authStore.token}` }, 
                timeout: 15000 
              })
              
              addChatMessage({
                message: messageText,
                response: retryResponse.data.response
              })
              
              // Handle actions on retry
              if (retryResponse.data.suggested_action) {
                switch (retryResponse.data.suggested_action) {
                  case 'filter_transactions':
                    currentTab.value = 'transactions'
                    if (retryResponse.data.action_params) {
                      Object.assign(filters.value, retryResponse.data.action_params)
                      showFilters.value = true
                    }
                    break
                  case 'show_transactions_tab':
                    currentTab.value = 'transactions'
                    break
                  case 'show_categories_tab':
                    currentTab.value = 'categories'
                    break
                  case 'show_timeline':
                    currentTab.value = 'timeline'
                    break
                }
              }
              
              loading.value = false
              currentThinking.value = ''
              return
              
            } else {
              errorMessage = 'Auth expired. Sign in again.'
            }
          } catch {
            errorMessage = 'Auth expired. Sign in again.'
          }
        } else if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
          errorMessage = 'Server offline. Check backend.'
        } else if (error.response?.status >= 500) {
          errorMessage = 'Server error. Try again.'
        }
        
        addChatMessage({
          message: messageText,
          response: errorMessage
        })
        
        chatInput.value = originalInput
      } finally {
        loading.value = false
        currentThinking.value = ''
      }
    }

    /**
     * Toggles chat history visibility
     * @returns {void}
     */
    const toggleHistory = () => {
      showHistory.value = !showHistory.value
    }

    /**
     * Opens chat panel and shows history
     * @returns {void}
     */
    const openChatPanel = () => {
      showChat.value = true
      showHistory.value = true
    }

    /**
     * Closes chat panel and hides history
     * @returns {void}
     */
    const closeChatPanel = () => {
      showChat.value = false
      showHistory.value = false
    }

    /**
     * Toggles chat panel open/closed state
     * @returns {void}
     */
    const toggleChatPanel = () => {
      if (showChat.value) {
        closeChatPanel()
      } else {
        openChatPanel()
      }
    }

    /**
     * Clears all chat history
     * @returns {void}
     */
    const clearChatHistory = () => {
      chatHistory.value = []
      showHistory.value = false
    }

    /**
     * Checks backend health and version
     * @async
     * @returns {Promise<void>}
     */
    const checkBackend = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`, { timeout: 10000 })
        backendStatus.value = 'Connected'
        phase.value = response.data.version || 'Local Version'
      } catch (error) {
        backendStatus.value = 'Disconnected'
        console.error('Backend connection failed:', error)
      }
    }

    /**
     * Loads transactions with current filters and pagination
     * @async
     * @returns {Promise<void>}
     */
    const loadTransactions = async () => {
      if (!authStore.token) {
        return
      }
      
      loading.value = true
      try {
        const params = new URLSearchParams({
          page: currentPage.value,
          limit: pageSize.value,
          ...(filters.value.startDate && { start_date: filters.value.startDate }),
          ...(filters.value.endDate && { end_date: filters.value.endDate }),
          ...(filters.value.merchant && { merchant: filters.value.merchant }),
          ...(filters.value.categoryId && { category_id: filters.value.categoryId }),
          ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
          ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount })
        })
        
        const response = await axios.get(`${API_BASE}/transactions/list?${params}`, {
          headers: { 'Authorization': `Bearer ${authStore.token}` }
        })
        
        transactions.value = response.data
      } catch (error) {
        console.error('Failed to load transactions:', error)
        if (error.response?.status === 401) {
          await authStore.verifyToken()
        }
      } finally {
        loading.value = false
      }
    }

    /**
     * Refreshes transactions (resets to page 1)
     * @returns {void}
     */
    const refreshTransactions = () => {
      currentPage.value = 1
      loadTransactions()
    }

    /**
     * Changes current page and reloads transactions
     * @param {number} newPage - Page number to load
     * @returns {void}
     */
    const changePage = (newPage) => {
      currentPage.value = newPage
      loadTransactions()
    }

    /**
     * Updates filter values
     * @param {Object} newFilters - New filter object
     * @returns {void}
     */
    const updateFilters = (newFilters) => {
      filters.value = newFilters
    }

    /**
     * Categorizes a transaction
     * @async
     * @param {number} transactionId - Transaction ID
     * @param {number} categoryId - Category ID
     * @returns {Promise<void>}
     */
    const categorizeTransaction = async (transactionId, categoryId) => {
      if (!authStore.token || !categoryId) return
      
      try {
        await axios.post(`${API_BASE}/transactions/categorize/${transactionId}`, 
          { category_id: categoryId },
          { 
            headers: { 'Authorization': `Bearer ${authStore.token}` },
            params: { category_id: categoryId }
          }
        )
        
        loadTransactions()
        
        const category = null
        if (category) {
          addChatMessage({
            message: 'Transaction categorized',
            response: `Transaction successfully categorized as ${category.name}!`
          })
        }
        
      } catch (error) {
        console.error('Failed to categorize transaction:', error)
        if (error.response?.status === 401) {
          await authStore.verifyToken()
        }
      }
    }

    /**
     * Handles transaction edit request
     * @param {Object} transaction - Transaction object to edit
     * @returns {void}
     */
    const editTransaction = (transaction) => {
      console.log('Edit transaction:', transaction)
    }

    /**
     * Handles file upload event
     * @param {Array} files - Array of file objects
     * @returns {void}
     */
    const handleFileUpload = (files) => {
      console.log('File upload event received:', files.length, 'files')
    }

    /**
     * Updates transaction count
     * @param {number} count - New transaction count
     * @returns {void}
     */
    const updateTransactionCount = (count) => {
      transactionCount.value = count
    }

    /**
     * Selects a category
     * @param {Object} category - Category object
     * @returns {void}
     */
    const selectCategory = (category) => {
      selectedCategory.value = category
    }

    /**
     * Formats date string to localized format
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date
     */
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    /**
     * Formats amount as USD currency
     * @param {number|string} amount - Amount to format
     * @returns {string} Formatted currency string
     */
    const formatAmount = (amount) => {
      const num = parseFloat(amount)
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(Math.abs(num))
    }

    /**
     * Shows specific tab and loads data if needed
     * @param {string} tabName - Tab name to show
     * @returns {void}
     */
    const showTab = (tabName) => {
      currentTab.value = tabName
      if (tabName === 'transactions' && authStore.token) {
        loadTransactions()
      }
    }

    /**
     * Handles user logout
     * @async
     * @returns {Promise<void>}
     */
    const handleLogout = async () => {
      try {
        await authStore.logout()
        addChatMessage({
          message: 'Logout',
          response: "You've been signed out. Sign in again for personalized features!"
        })
        
        showWelcomeMessage.value = false
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    /**
     * Watch filters for changes and reload transactions
     */
    watch(filters, () => {
      if (currentTab.value === 'transactions') {
        loadTransactions()
      }
    }, { deep: true })

    /**
     * Watch auth store for user changes
     * Initialize welcome message for new authenticated users
     */
    watch(() => authStore.user, (newUser) => {
      user.value = newUser
      
      if (newUser && chatHistory.value.length === 0) {
        const userName = newUser.display_name || newUser.email.split('@')[0]
        
        addChatMessage({
          response: `Hello, ${userName}! I'm here to help you with your financial data. You can ask questions about budgeting, upload CSV files, or explore your transaction categories.`
        })
        
        showWelcomeMessage.value = false
      }
    }, { immediate: true })

    /**
     * Initialize application on mount
     */
    onMounted(() => {
      checkBackend()
      authStore.initAuth()
    })

    return {
      // Core state
      currentTab,
      user,
      backendStatus,
      phase,
      loading,
      
      // Chat state
      chatInput,
      chatHistory,
      currentThinking,
      showWelcomeMessage,
      showHistory,
      showChat,
      welcomeText,
      
      // File upload and transaction state
      transactionCount,
      recentUploads,
      transactions,
      currentPage,
      pageSize,
      filters,
      showFilters,
      
      // Category state
      selectedCategory,
      
      // Functions
      toggleHistory,
      openChatPanel,
      closeChatPanel,
      toggleChatPanel,
      sendMessage,
      addChatMessage,
      clearChatHistory,
      scrollToBottom,
      loadTransactions,
      refreshTransactions,
      changePage,
      updateFilters,
      categorizeTransaction,
      editTransaction,
      handleFileUpload,
      updateTransactionCount,
      selectCategory,
      formatDate,
      formatAmount,
      showTab,
      handleLogout
    }
  }
}
</script>

<style scoped>
.login-screen {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-container {
  text-align: center;
  max-width: 400px;
  width: 90%;
}

.logo-section {
  margin-bottom: 2rem;
}

.logo-section h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.tagline {
  color: var(--color-text-light);
  font-size: var(--text-medium);
}

.authenticated-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.user-info {
  color: var(--color-text-light);
}
</style>