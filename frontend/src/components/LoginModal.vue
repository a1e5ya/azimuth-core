<template>
  <div v-if="showModal" :class="modalClasses" @click="handleOverlayClick">
    <div :class="contentClasses" @click.stop>
      <h2 v-if="!isFullScreen">{{ isLogin ? 'Sign In' : 'Sign Up' }}</h2>
      
      <form @submit.prevent="handleEmailAuth">
        <input v-model="email" type="email" placeholder="Email" required :class="inputClasses" />
        <input v-if="!isLogin" v-model="displayName" type="text" placeholder="Display Name (optional)" :class="inputClasses" />
        <input v-model="password" type="password" placeholder="Password" required :class="inputClasses" />
        <button type="submit" :class="authBtnClasses" :disabled="loading">
          {{ loading ? 'Loading...' : (isLogin ? 'Log In' : 'Sign Up') }}
        </button>
      </form>
      
      <p :class="toggleTextClasses">
        {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
        <button @click="isLogin = !isLogin" class="toggle-btn">
          {{ isLogin ? 'Sign Up' : 'Log In' }}
        </button>
      </p>
      
      <div v-if="error" class="error-message">{{ error }}</div>
      
      <button v-if="!isFullScreen" @click="closeModal" class="close-btn">×</button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'LoginModal',
  props: {
    showModal: { type: Boolean, default: false },
    isFullScreen: { type: Boolean, default: false }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const isLogin = ref(true)
    const email = ref('')
    const password = ref('')
    const displayName = ref('')
    const error = ref('')
    const loading = ref(false)
    
    const closeModal = () => {
      if (!props.isFullScreen) {
        emit('close')
        resetForm()
      }
    }
    
    const handleOverlayClick = () => {
      if (!props.isFullScreen) closeModal()
    }
    
    const resetForm = () => {
      email.value = ''
      password.value = ''
      displayName.value = ''
      error.value = ''
      loading.value = false
    }
    
    const handleEmailAuth = async () => {
      loading.value = true
      error.value = ''
      try {
        let result
        if (isLogin.value) {
          result = await authStore.login(email.value, password.value)
        } else {
          result = await authStore.register(email.value, password.value, displayName.value)
        }
        if (result.success) {
          if (!props.isFullScreen) closeModal()
        } else {
          error.value = result.error
        }
      } catch (err) {
        error.value = err.message
      }
      loading.value = false
    }
    
    const modalClasses = computed(() => [props.isFullScreen ? 'fullscreen-modal' : 'modal-overlay'])
    const contentClasses = computed(() => [props.isFullScreen ? 'fullscreen-content' : 'modal-content'])
    const inputClasses = computed(() => ['form-input', props.isFullScreen ? 'fullscreen-input' : ''])
    const authBtnClasses = computed(() => ['btn', 'btn-primary', props.isFullScreen ? 'fullscreen-auth-btn' : ''])
    const toggleTextClasses = computed(() => ['toggle-text', props.isFullScreen ? 'fullscreen-toggle-text' : ''])
    
    return {
      isLogin, email, password, displayName, error, loading,
      closeModal, handleOverlayClick, handleEmailAuth,
      modalClasses, contentClasses, inputClasses, authBtnClasses, toggleTextClasses
    }
  }
}
</script>

<style scoped>
.fullscreen-modal {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-content {
  backdrop-filter: blur(20px);
  border-radius: 30px;
  padding: var(--gap-large);
  width: 100%;
  max-width: 400px;
  position: relative;
}

.modal-content h2,
.fullscreen-content h2 {
  text-align: center;
  margin-bottom: var(--gap-standard);
  color: var(--color-text);
  font-weight: 600;
}

.fullscreen-input {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.3);
  margin-bottom: 1.5rem;
  color: #333;
}

.fullscreen-auth-btn {
  background: rgba(255, 255, 255, 0.2) !important;
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: var(--color-button-text);
}

.toggle-text {
  text-align: center;
  font-size: var(--text-small);
  margin: 0;
}

.toggle-btn {
  background: none;
  border: none;
  color: var(--color-text);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #dc2626;
  padding: var(--gap-small);
  border-radius: var(--radius);
  font-size: var(--text-small);
  margin-top: var(--gap-standard);
}
</style>