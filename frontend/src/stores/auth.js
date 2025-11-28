/**
 * Authentication Store - User Authentication State Management
 * 
 * Manages all authentication-related state and operations:
 * - User session (token, user data)
 * - Login/logout
 * - Registration
 * - Password reset flow
 * - Token verification
 * - LocalStorage persistence
 * 
 * Architecture:
 * - Uses Pinia composition API
 * - Persists auth state to localStorage
 * - Sets axios default Authorization header
 * - Automatic token verification on init
 * 
 * LocalStorage Keys:
 * - azimuth_token: JWT access token
 * - azimuth_user: User profile data (JSON)
 * 
 * API Integration:
 * - Backend: FastAPI JWT authentication
 * - Endpoints: /auth/register, /auth/login, /auth/verify, etc.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  // ========================================
  // STATE
  // ========================================
  
  /** @type {Ref<Object|null>} Current user profile data */
  const user = ref(null)
  
  /** @type {Ref<string|null>} JWT access token */
  const token = ref(null)
  
  /** @type {ComputedRef<boolean>} True if user is authenticated */
  const isAuthenticated = computed(() => !!user.value && !!token.value)
  
  /** @type {Ref<boolean>} Loading state for async operations */
  const loading = ref(false)
  
  // Get API base URL from environment or default to local
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  
  // ========================================
  // INITIALIZATION
  // ========================================
  
  /**
   * Load authentication state from localStorage on store initialization
   * 
   * Process:
   * 1. Check localStorage for saved token and user
   * 2. Restore to reactive state
   * 3. Set axios Authorization header
   * 4. Verify token is still valid with backend
   * 5. Clear state if verification fails
   * 
   * Called automatically when store is created.
   * Enables persistent login across page refreshes.
   */
  const initAuth = () => {
    try {
      const storedToken = localStorage.getItem('azimuth_token')
      const storedUser = localStorage.getItem('azimuth_user')
      
      if (storedToken && storedUser) {
        token.value = storedToken
        user.value = JSON.parse(storedUser)
        
        // Set axios default header for all future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
        
        console.log('✅ Auth state restored from localStorage')
        
        // Verify token is still valid
        verifyToken()
      } else {
        console.log('ℹ️ No stored auth state found')
      }
    } catch (error) {
      console.error('❌ Error loading auth state:', error)
      clearAuthState()
    }
    
    loading.value = false
  }
  
  // ========================================
  // STATE MANAGEMENT UTILITIES
  // ========================================
  
  /**
   * Save authentication state to localStorage
   * 
   * Persists:
   * - JWT token
   * - User profile data
   * - Sets axios Authorization header
   * 
   * @param {string} authToken - JWT access token from backend
   * @param {Object} userData - User profile data
   */
  const saveAuthState = (authToken, userData) => {
    try {
      localStorage.setItem('azimuth_token', authToken)
      localStorage.setItem('azimuth_user', JSON.stringify(userData))
      
      token.value = authToken
      user.value = userData
      
      // Set axios default header for all future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
      
      console.log('✅ Auth state saved')
    } catch (error) {
      console.error('❌ Error saving auth state:', error)
    }
  }
  
  /**
   * Clear authentication state
   * 
   * Removes:
   * - localStorage items
   * - Reactive state
   * - axios Authorization header
   * 
   * Called on:
   * - Logout
   * - Token verification failure
   * - 401 responses
   */
  const clearAuthState = () => {
    try {
      localStorage.removeItem('azimuth_token')
      localStorage.removeItem('azimuth_user')
      
      token.value = null
      user.value = null
      
      // Remove axios default header
      delete axios.defaults.headers.common['Authorization']
      
      console.log('✅ Auth state cleared')
    } catch (error) {
      console.error('❌ Error clearing auth state:', error)
    }
  }
  
  // ========================================
  // AUTHENTICATION ACTIONS
  // ========================================
  
  /**
   * Register new user
   * 
   * Process:
   * 1. Send registration data to backend
   * 2. Receive JWT token and user data
   * 3. Save auth state to localStorage
   * 4. Set axios headers
   * 5. Return success/error result
   * 
   * @param {string} email - User email address
   * @param {string} password - User password
   * @param {string|null} displayName - Optional display name
   * @returns {Promise<{success: boolean, user?: Object, error?: string}>} Registration result
   * 
   * @example
   * const result = await register('user@example.com', 'password123', 'John Doe')
   * if (result.success) {
   *   console.log('Registered:', result.user)
   * }
   */
  const register = async (email, password, displayName = null) => {
    loading.value = true
    
    try {
      console.log('📝 Attempting registration for:', email)
      
      const response = await axios.post(`${API_BASE}/auth/register`, {
        email,
        password,
        display_name: displayName
      })
      
      if (response.data.success) {
        console.log('✅ Registration successful')
        
        // Save auth state
        saveAuthState(response.data.access_token, response.data.user)
        
        return { 
          success: true, 
          user: response.data.user,
          message: 'Registration successful'
        }
      } else {
        return { 
          success: false, 
          error: response.data.message || 'Registration failed'
        }
      }
    } catch (error) {
      console.error('❌ Registration failed:', error)
      
      let errorMessage = 'Registration failed'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.status === 400) {
        errorMessage = 'Email already registered or invalid data'
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please check if Azimuth Core is running.'
      }
      
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Login user
   * 
   * Process:
   * 1. Send credentials to backend
   * 2. Receive JWT token and user data
   * 3. Save auth state
   * 4. Return success/error result
   * 
   * @param {string} email - User email address
   * @param {string} password - User password
   * @returns {Promise<{success: boolean, user?: Object, error?: string}>} Login result
   * 
   * @example
   * const result = await login('user@example.com', 'password123')
   * if (result.success) {
   *   router.push('/dashboard')
   * }
   */
  const login = async (email, password) => {
    loading.value = true
    
    try {
      console.log('🔐 Attempting login for:', email)
      
      const response = await axios.post(`${API_BASE}/auth/login`, {
        email,
        password
      })
      
      if (response.data.success) {
        console.log('✅ Login successful')
        
        // Save auth state
        saveAuthState(response.data.access_token, response.data.user)
        
        return { 
          success: true, 
          user: response.data.user,
          message: 'Login successful'
        }
      } else {
        return { 
          success: false, 
          error: response.data.message || 'Login failed'
        }
      }
    } catch (error) {
      console.error('❌ Login failed:', error)
      
      let errorMessage = 'Login failed'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.status === 401) {
        errorMessage = 'Invalid email or password'
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please check if Azimuth Core is running.'
      }
      
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Request password reset
   * 
   * Sends password reset email to user.
   * Backend generates reset token and emails it.
   * 
   * @param {string} email - User email address
   * @returns {Promise<{success: boolean, message?: string, error?: string}>} Request result
   * 
   * @example
   * const result = await requestPasswordReset('user@example.com')
   * if (result.success) {
   *   console.log('Check your email for reset link')
   * }
   */
  const requestPasswordReset = async (email) => {
    loading.value = true
    
    try {
      console.log('📧 Requesting password reset for:', email)
      
      const response = await axios.post(`${API_BASE}/auth/forgot-password`, {
        email
      })
      
      if (response.data.success) {
        console.log('✅ Password reset email sent')
        return { 
          success: true, 
          message: 'Password reset email sent successfully'
        }
      } else {
        return { 
          success: false, 
          error: response.data.message || 'Failed to send password reset email'
        }
      }
    } catch (error) {
      console.error('❌ Password reset request failed:', error)
      
      let errorMessage = 'Failed to send password reset email'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.status === 404) {
        errorMessage = 'Email address not found'
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many reset requests. Please wait before trying again.'
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please check if Azimuth Core is running.'
      }
      
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Reset password with token
   * 
   * Uses reset token from email link to set new password.
   * Token is validated by backend.
   * 
   * @param {string} resetToken - Password reset token from email
   * @param {string} newPassword - New password to set
   * @returns {Promise<{success: boolean, message?: string, error?: string}>} Reset result
   * 
   * @example
   * const result = await resetPassword('reset-token-123', 'newPassword456')
   * if (result.success) {
   *   router.push('/login')
   * }
   */
  const resetPassword = async (resetToken, newPassword) => {
    loading.value = true
    
    try {
      console.log('🔑 Resetting password with token')
      
      const response = await axios.post(`${API_BASE}/auth/reset-password`, {
        token: resetToken,
        new_password: newPassword
      })
      
      if (response.data.success) {
        console.log('✅ Password reset successful')
        return { 
          success: true, 
          message: 'Password reset successful'
        }
      } else {
        return { 
          success: false, 
          error: response.data.message || 'Password reset failed'
        }
      }
    } catch (error) {
      console.error('❌ Password reset failed:', error)
      
      let errorMessage = 'Password reset failed'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid or expired reset token'
      } else if (error.response?.status === 422) {
        errorMessage = 'Password does not meet requirements'
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please check if Azimuth Core is running.'
      }
      
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Verify current token
   * 
   * Checks if stored JWT token is still valid with backend.
   * Clears auth state if token is expired or invalid.
   * Updates user data if backend provides fresh data.
   * 
   * Called automatically on:
   * - Store initialization
   * - 401 responses
   * 
   * @returns {Promise<{success: boolean, user?: Object, error?: string}>} Verification result
   */
  const verifyToken = async () => {
    if (!token.value) {
      return { success: false, error: 'No token available' }
    }
    
    try {
      console.log('🔍 Verifying token...')
      
      const response = await axios.post(`${API_BASE}/auth/verify`, {}, {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.data.authenticated) {
        console.log('✅ Token verified')
        
        // Update user data if provided
        if (response.data.user) {
          user.value = response.data.user
          localStorage.setItem('azimuth_user', JSON.stringify(response.data.user))
        }
        
        return { success: true, user: response.data.user }
      } else {
        console.log('❌ Token invalid')
        clearAuthState()
        return { success: false, error: 'Token invalid' }
      }
    } catch (error) {
      console.error('❌ Token verification failed:', error)
      
      if (error.response?.status === 401) {
        console.log('🔄 Token expired, clearing auth state')
        clearAuthState()
      }
      
      return { success: false, error: 'Token verification failed' }
    }
  }
  
  /**
   * Get current user profile
   * 
   * Fetches fresh user profile data from backend.
   * Updates stored user data in state and localStorage.
   * 
   * @returns {Promise<{success: boolean, user?: Object, error?: string}>} Profile fetch result
   */
  const getCurrentUser = async () => {
    if (!token.value) {
      return { success: false, error: 'Not authenticated' }
    }
    
    try {
      console.log('👤 Fetching current user profile...')
      
      const response = await axios.get(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      console.log('✅ User profile fetched')
      
      // Update stored user data
      user.value = response.data
      localStorage.setItem('azimuth_user', JSON.stringify(response.data))
      
      return { success: true, user: response.data }
    } catch (error) {
      console.error('❌ Failed to fetch user profile:', error)
      
      if (error.response?.status === 401) {
        clearAuthState()
      }
      
      return { success: false, error: 'Failed to fetch user profile' }
    }
  }
  
  /**
   * Logout user
   * 
   * Process:
   * 1. Call backend logout endpoint (for audit logging)
   * 2. Clear local auth state (even if backend fails)
   * 3. Remove token and user data
   * 4. Clear axios headers
   * 
   * Always succeeds locally even if backend logout fails.
   * 
   * @returns {Promise<{success: boolean, message: string}>} Logout result
   */
  const logout = async () => {
    try {
      console.log('🚪 Logging out...')
      
      // Call backend logout endpoint (for audit logging)
      if (token.value) {
        try {
          await axios.post(`${API_BASE}/auth/logout`, {}, {
            headers: {
              'Authorization': `Bearer ${token.value}`
            }
          })
        } catch (error) {
          console.warn('⚠️ Backend logout failed, proceeding with local logout:', error)
        }
      }
      
      // Clear local auth state
      clearAuthState()
      
      console.log('✅ Logout successful')
      return { success: true, message: 'Logout successful' }
    } catch (error) {
      console.error('❌ Logout error:', error)
      
      // Even if backend logout fails, clear local state
      clearAuthState()
      
      return { success: true, message: 'Logout completed (local)' }
    }
  }
  
  /**
   * Change password
   * 
   * Updates password for authenticated user.
   * Requires current password for verification.
   * 
   * @param {string} currentPassword - Current password for verification
   * @param {string} newPassword - New password to set
   * @returns {Promise<{success: boolean, message?: string, error?: string}>} Change result
   * 
   * @example
   * const result = await changePassword('oldPass123', 'newPass456')
   * if (result.success) {
   *   console.log('Password updated')
   * }
   */
  const changePassword = async (currentPassword, newPassword) => {
    if (!token.value) {
      return { success: false, error: 'Not authenticated' }
    }
    
    loading.value = true
    
    try {
      console.log('🔒 Changing password...')
      
      const response = await axios.post(`${API_BASE}/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      }, {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.data.success) {
        console.log('✅ Password changed successfully')
        return { success: true, message: 'Password changed successfully' }
      } else {
        return { success: false, error: response.data.message || 'Password change failed' }
      }
    } catch (error) {
      console.error('❌ Password change failed:', error)
      
      let errorMessage = 'Password change failed'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.status === 400) {
        errorMessage = 'Current password is incorrect'
      }
      
      return { success: false, error: errorMessage }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Check authentication status
   * 
   * Queries backend for current authentication status.
   * Does not require token (checks if any valid session exists).
   * 
   * @returns {Promise<{authenticated: boolean, user: Object|null, message: string}>} Status result
   */
  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/auth/status`, {
        headers: token.value ? {
          'Authorization': `Bearer ${token.value}`
        } : {}
      })
      
      return {
        authenticated: response.data.authenticated,
        user: response.data.user,
        message: response.data.message
      }
    } catch (error) {
      console.error('❌ Auth status check failed:', error)
      return {
        authenticated: false,
        user: null,
        message: 'Status check failed'
      }
    }
  }
  
  // ========================================
  // STORE INITIALIZATION
  // ========================================
  
  // Initialize auth store on creation
  initAuth()
  
  // ========================================
  // EXPOSED API
  // ========================================
  
  return {
    // State
    user,
    token,
    isAuthenticated,
    loading,
    
    // Actions
    register,
    login,
    logout,
    requestPasswordReset,
    resetPassword,
    verifyToken,
    getCurrentUser,
    changePassword,
    checkAuthStatus,
    
    // Utilities
    initAuth,
    clearAuthState
  }
})