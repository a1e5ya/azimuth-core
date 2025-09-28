import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const isAuthenticated = computed(() => !!user.value && !!token.value)
  const loading = ref(false)
  
  // Get API base URL from environment or default to local
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  
  // Load authentication state from localStorage on store initialization
  const initAuth = () => {
    try {
      const storedToken = localStorage.getItem('azimuth_token')
      const storedUser = localStorage.getItem('azimuth_user')
      
      if (storedToken && storedUser) {
        token.value = storedToken
        user.value = JSON.parse(storedUser)
        
        // Set axios default header
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
  
  // Save authentication state to localStorage
  const saveAuthState = (authToken, userData) => {
    try {
      localStorage.setItem('azimuth_token', authToken)
      localStorage.setItem('azimuth_user', JSON.stringify(userData))
      
      token.value = authToken
      user.value = userData
      
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
      
      console.log('✅ Auth state saved')
    } catch (error) {
      console.error('❌ Error saving auth state:', error)
    }
  }
  
  // Clear authentication state
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
  
  // Register new user
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
  
  // Login user
  const login = async (email, password) => {
    loading.value = true
    
    try {
      console.log('🔑 Attempting login for:', email)
      
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
  
  // Request password reset
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
  
  // Reset password with token
  const resetPassword = async (resetToken, newPassword) => {
    loading.value = true
    
    try {
      console.log('🔒 Resetting password with token')
      
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
  
  // Verify current token
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
  
  // Get current user profile
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
  
  // Logout user
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
  
  // Change password
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
  
  // Check authentication status
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
  
  // Initialize auth store
  initAuth()
  
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