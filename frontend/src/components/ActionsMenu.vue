<template>
  <div class="actions-menu-wrapper" @click.stop>
    <!-- Three Dots Button - Visible on Hover -->
    <button 
      class="btn-menu-dots"
      :class="{ 'menu-open': isMenuOpen }"
      @click.stop="toggleMenu"
      :title="menuTitle"
    >
      <AppIcon name="menu-dots" size="small" />
    </button>

    <!-- Actions Popup - Visible When Menu Open -->
    <transition name="actions-fade">
      <div v-if="isMenuOpen" class="actions-popup" @click.stop>
        <button 
          v-if="showEdit"
          class="action-btn"
          @click.stop="handleEdit"
          title="Edit"
        >
          <AppIcon name="pencil" size="small" />
          <span>Edit</span>
        </button>

        <button 
          v-if="showAdd"
          class="action-btn"
          @click.stop="handleAdd"
          title="Add"
        >
          <AppIcon name="plus" size="small" />
          <span>Add</span>
        </button>

        <button 
          v-if="showCheck"
          class="action-btn action-check"
          @click.stop="handleCheck"
          title="Confirm"
        >
          <AppIcon name="check" size="small" />
          <span>Confirm</span>
        </button>

        <button 
          v-if="showDelete"
          class="action-btn action-delete"
          @click.stop="handleDelete"
          title="Delete"
        >
          <AppIcon name="cross" size="small" />
          <span>Delete</span>
        </button>
      </div>
    </transition>

    <!-- Click Outside Detector -->
    <div 
      v-if="isMenuOpen" 
      class="menu-backdrop"
      @click.stop="closeMenu"
    ></div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import AppIcon from './AppIcon.vue'

export default {
  name: 'ActionsMenu',
  components: { AppIcon },
  props: {
    showEdit: {
      type: Boolean,
      default: true
    },
    showAdd: {
      type: Boolean,
      default: false
    },
    showCheck: {
      type: Boolean,
      default: false
    },
    showDelete: {
      type: Boolean,
      default: true
    },
    menuTitle: {
      type: String,
      default: 'Actions'
    }
  },
  emits: ['edit', 'add', 'check', 'delete'],
  setup(props, { emit }) {
    const isMenuOpen = ref(false)

    function toggleMenu() {
      isMenuOpen.value = !isMenuOpen.value
    }

    function closeMenu() {
      isMenuOpen.value = false
    }

    function handleEdit() {
      emit('edit')
      closeMenu()
    }

    function handleAdd() {
      emit('add')
      closeMenu()
    }

    function handleCheck() {
      emit('check')
      closeMenu()
    }

    function handleDelete() {
      emit('delete')
      closeMenu()
    }

    // Close menu on Escape key
    function handleEscape(e) {
      if (e.key === 'Escape' && isMenuOpen.value) {
        closeMenu()
      }
    }

    onMounted(() => {
      document.addEventListener('keydown', handleEscape)
    })

    onUnmounted(() => {
      document.removeEventListener('keydown', handleEscape)
    })

    return {
      isMenuOpen,
      toggleMenu,
      closeMenu,
      handleEdit,
      handleAdd,
      handleCheck,
      handleDelete
    }
  }
}
</script>

<style scoped>
.actions-menu-wrapper {
  position: relative;
  display: inline-flex;
}

/* Three Dots Button */
.btn-menu-dots {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  opacity: 0;
  transition: all 0.2s;
  color: var(--color-text-light);
}

/* Show on parent hover */
.category-header-compact:hover .btn-menu-dots,
.subcat-top:hover .btn-menu-dots {
  opacity: 0.6;
}

/* Always visible when has class */
.actions-menu-wrapper.always-visible .btn-menu-dots {
  opacity: 1 !important;
  color: var(--color-text);
}

.btn-menu-dots:hover,
.btn-menu-dots.menu-open {
  opacity: 1 !important;
  background: var(--color-background-dark);
  color: var(--color-text);
}

/* Actions Popup */
.actions-popup {
  position: absolute;
  top: calc(100% + 0.25rem);
  right: 0;
  background: var(--color-background-light);
  backdrop-filter: blur(1rem);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  z-index: 100;
  min-width: 8rem;
}

.action-btn {
  background: none;
  border: none;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
  font-size: var(--text-small);
  color: var(--color-text);
  text-align: left;
  white-space: nowrap;
}

.action-btn:hover {
  background: var(--color-background-dark);
}

.action-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.action-check:hover {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

/* Backdrop */
.menu-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
  background: transparent;
}

/* Fade Transition */
.actions-fade-enter-active,
.actions-fade-leave-active {
  transition: all 0.15s ease;
}

.actions-fade-enter-from,
.actions-fade-leave-to {
  opacity: 0;
  transform: translateY(-0.5rem);
}
</style>