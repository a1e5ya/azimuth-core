<!--
  SettingsAccount Component - User Profile & Password Management
  
  Provides user account settings interface:
  - Display name and email editing
  - Profile data management (currency, locale)
  - Password change with validation
  - Loading states for async operations
  
  Features:
  - Profile update (display name, email, currency, locale)
  - Password change with validation (min 8 chars, match confirmation)
  - Current password verification required
  - Error handling with console.error
  - Automatic profile loading on mount
  
  Authentication:
  - Uses authStore for token management
  - All requests require Bearer token
  - Auto-loads user data from /auth/me endpoint
  
  API Endpoints:
  - GET /auth/me - Load user profile
  - PUT /auth/profile - Update profile data
  - POST /auth/change-password - Change password
  
  Data Structure:
  - userProfile: { displayName, email, currency, locale }
  - passwordForm: { currentPassword, newPassword, confirmPassword }
-->

<template>
  <div class="card settings-card">
    
    <!-- Profile Information Section -->
    <div class="form-row">
      <label>Display Name</label>
      <input v-model="userProfile.displayName" type="text" placeholder="Your name" class="form-input">
    </div>
    
    <div class="form-row">
      <label>Email</label>
      <input v-model="userProfile.email" type="email" placeholder="your.email@example.com" class="form-input">
    </div>

    <!-- Save Profile Button -->
    <button @click="saveProfile" class="btn btn-primary" :disabled="saving">
      {{ saving ? 'Saving...' : 'Save Profile' }}
    </button>
    
    <hr class="divider">
    
    <!-- Password Change Section -->
    <form @submit.prevent="changePassword">
      <!-- Hidden username field for accessibility -->
      <input type="text" v-model="userProfile.email" autocomplete="username" style="display: none;" aria-hidden="true">
      
      <div class="form-row">
        <label>Current Password</label>
        <input v-model="passwordForm.currentPassword" type="password" placeholder="Enter current password" class="form-input" autocomplete="current-password">
      </div>
      
      <div class="form-row">
        <label>New Password</label>
        <input v-model="passwordForm.newPassword" type="password" placeholder="Enter new password" class="form-input" autocomplete="new-password">
      </div>
      
      <div class="form-row">
        <label>Confirm New Password</label>
        <input v-model="passwordForm.confirmPassword" type="password" placeholder="Confirm new password" class="form-input" autocomplete="new-password">
      </div>
      
      <!-- Change Password Button -->
      <button type="submit" class="btn btn-primary" :disabled="changingPassword" style="margin-top: 12px;">
        {{ changingPassword ? 'Changing...' : 'Change Password' }}
      </button>
    </form>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'SettingsAccount',
  setup() {
    const authStore = useAuthStore()
    const userProfile = ref({
      displayName: '',
      email: '',
      currency: 'EUR',
      locale: 'en-US'
    })

    const passwordForm = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    const saving = ref(false)
    const changingPassword = ref(false)

    /**
     * Loads user profile data from the backend
     * @async
     * @returns {Promise<void>}
     */
    const loadUserProfile = async () => {
      try {
        const token = authStore.token
        if (!token) return

        const response = await fetch('http://localhost:8001/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const userData = await response.json()
          userProfile.value.email = userData.email
          userProfile.value.displayName = userData.display_name || ''
          userProfile.value.currency = userData.currency || 'EUR'
          userProfile.value.locale = userData.locale || 'en-US'
        }
      } catch (error) {
        console.error('Failed to load user profile:', error)
      }
    }

    /**
     * Saves user profile data to the backend
     * @async
     * @returns {Promise<void>}
     */
    const saveProfile = async () => {
      try {
        saving.value = true
        const token = authStore.token
        if (!token) return

        const response = await fetch('http://localhost:8001/auth/profile', {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            display_name: userProfile.value.displayName,
            email: userProfile.value.email,
            currency: userProfile.value.currency,
            locale: userProfile.value.locale
          })
        })

        if (!response.ok) {
          const data = await response.json()
          console.error('Failed to save profile:', data)
        }
      } catch (error) {
        console.error('Failed to save profile:', error)
      } finally {
        saving.value = false
      }
    }

    /**
     * Changes user password with validation
     * @async
     * @returns {Promise<void>}
     */
    const changePassword = async () => {
      if (!passwordForm.value.currentPassword) {
        return
      }

      if (!passwordForm.value.newPassword) {
        return
      }

      if (passwordForm.value.newPassword.length < 8) {
        return
      }

      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        return
      }

      try {
        changingPassword.value = true
        const token = authStore.token
        if (!token) return

        const params = new URLSearchParams({
          current_password: passwordForm.value.currentPassword,
          new_password: passwordForm.value.newPassword
        })
        const response = await fetch(`http://localhost:8001/auth/change-password?${params}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          passwordForm.value = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }
        } else {
          const data = await response.json()
          console.error('Failed to change password:', data)
          console.error('Error detail:', JSON.stringify(data.detail, null, 2))
        }
      } catch (error) {
        console.error('Failed to change password:', error)
      } finally {
        changingPassword.value = false
      }
    }

    onMounted(() => {
      loadUserProfile()
    })

    return {
      userProfile,
      passwordForm,
      saving,
      changingPassword,
      saveProfile,
      changePassword
    }
  }
}
</script>