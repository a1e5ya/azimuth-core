<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">User Account</div>
    </div>
    
    <div class="form-row">
      <label>Display Name</label>
      <input v-model="userProfile.displayName" type="text" placeholder="Your name">
    </div>
    
    <div class="form-row">
      <label>Email</label>
      <input v-model="userProfile.email" type="email" placeholder="your.email@example.com" disabled>
    </div>
    
    <button @click="saveProfile" class="btn btn-primary" :disabled="saving">
      {{ saving ? 'Saving...' : 'Save Profile' }}
    </button>
    
    <hr class="divider">
    
    <div class="form-row">
      <label>Current Password</label>
      <input v-model="passwordForm.currentPassword" type="password" placeholder="Enter current password">
    </div>
    
    <div class="form-row">
      <label>New Password</label>
      <input v-model="passwordForm.newPassword" type="password" placeholder="Enter new password">
    </div>
    
    <div class="form-row">
      <label>Confirm New Password</label>
      <input v-model="passwordForm.confirmPassword" type="password" placeholder="Confirm new password">
    </div>
    
    <button @click="changePassword" class="btn btn-primary" :disabled="changingPassword">
      {{ changingPassword ? 'Changing...' : 'Change Password' }}
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

<style scoped>
/* Using global design system - minimal overrides only */
.card {
  break-inside: avoid;
}

.form-row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: var(--gap-small);
  align-items: center;
  margin-bottom: var(--gap-small);
}

.form-row label {
  font-size: var(--text-small);
  font-weight: 500;
  color: var(--color-text);
  text-align: left;
}

.form-row input {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 0.0625rem solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  font-size: var(--text-small);
  color: var(--color-text);
  background: var(--color-button);
  transition: all 0.2s ease;
}

.form-row input:focus {
  outline: none;
  border-color: var(--color-button-active);
  box-shadow: 0 0 0 0.125rem rgba(0, 0, 0, 0.1);
}

.form-row input:disabled {
  background: var(--color-background-dark);
  color: var(--color-text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.divider {
  margin: var(--gap-small) 0;
  border: none;
  border-top: 0.0625rem solid rgba(0, 0, 0, 0.1);
}

@media (max-width: 48rem) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 0.125rem;
  }
}
</style>