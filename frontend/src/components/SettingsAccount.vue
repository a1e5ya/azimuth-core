<template>
  <div class="card settings-card">
    
    <div class="form-row">
      <label>Display Name</label>
      <input v-model="userProfile.displayName" type="text" placeholder="Your name" class="form-input">
    </div>
    
    <div class="form-row">
      <label>Email</label>
      <input v-model="userProfile.email" type="email" placeholder="your.email@example.com" class="form-input">
    </div>
    
    <hr class="divider">
    
    <div class="form-row">
      <label>Current Password</label>
      <input v-model="passwordForm.currentPassword" type="password" placeholder="Enter current password" class="form-input">
    </div>
    
    <div class="form-row">
      <label>New Password</label>
      <input v-model="passwordForm.newPassword" type="password" placeholder="Enter new password" class="form-input">
    </div>
    
    <div class="form-row">
      <label>Confirm New Password</label>
      <input v-model="passwordForm.confirmPassword" type="password" placeholder="Confirm new password" class="form-input">
    </div>
    
    <button @click="saveProfile" class="btn btn-primary" :disabled="saving">
      {{ saving ? 'Saving...' : 'Save Profile' }}
    </button>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'SettingsAccount',
  setup() {
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

    const loadUserProfile = async () => {
      try {
        const token = localStorage.getItem('token')
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

    const saveProfile = async () => {
      try {
        saving.value = true
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/auth/profile', {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            display_name: userProfile.value.displayName,
            currency: userProfile.value.currency,
            locale: userProfile.value.locale
          })
        })

        if (!response.ok) {
          await response.json()
          console.error('Failed to save profile:', data)
        }
      } catch (error) {
        console.error('Failed to save profile:', error)
      } finally {
        saving.value = false
      }
    }

    const changePassword = async () => {
      if (!passwordForm.value.currentPassword) {
        return
      }

      if (!passwordForm.value.newPassword) {
        return
      }

      if (passwordForm.value.newPassword.length < 6) {
        return
      }

      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        return
      }

      try {
        changingPassword.value = true
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:8001/auth/change-password', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            current_password: passwordForm.value.currentPassword,
            new_password: passwordForm.value.newPassword
          })
        })

        if (response.ok) {
          passwordForm.value = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }
        } else {
          const data = await response.json()
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

