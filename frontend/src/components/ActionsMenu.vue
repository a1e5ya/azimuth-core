<!--
  ActionsMenu Component - Contextual Actions Dropdown
  
  Provides a three-dot menu with configurable actions (edit, add, check, delete).
  Appears on hover and shows popup menu on click.
  
  Features:
  - Show/hide on hover (parent element must have hover class)
  - Configurable action buttons (show/hide via props)
  - Popup menu with smooth transitions
  - Click-outside to close
  - Escape key to close
  - Backdrop overlay for mobile
  - Color-coded actions (delete: red, check: green)
  
  Events:
  - @edit: Edit button clicked
  - @add: Add button clicked
  - @check: Check/confirm button clicked
  - @delete: Delete button clicked
  
  Usage:
  <ActionsMenu 
    :show-edit="true"
    :show-add="false"
    :show-delete="true"
    @edit="handleEdit"
    @delete="handleDelete"
  />
  
  Typical Use Cases:
  - Category management (edit, add child, delete)
  - Transaction rows (edit, delete)
  - List items with actions
  
  Integration:
  Parent element should have hover class for visibility:
  .category-header-compact:hover .btn-menu-dots { opacity: 0.6; }
-->

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
        <!-- Edit Action -->
        <button 
          v-if="showEdit"
          class="action-btn"
          @click.stop="handleEdit"
          title="Edit"
        >
          <AppIcon name="pencil" size="small" />
          <span>Edit</span>
        </button>

        <!-- Add Action -->
        <button 
          v-if="showAdd"
          class="action-btn"
          @click.stop="handleAdd"
          title="Add"
        >
          <AppIcon name="plus" size="small" />
          <span>Add</span>
        </button>

        <!-- Check/Confirm Action -->
        <button 
          v-if="showCheck"
          class="action-btn action-check"
          @click.stop="handleCheck"
          title="Confirm"
        >
          <AppIcon name="check" size="small" />
          <span>Confirm</span>
        </button>

        <!-- Delete Action -->
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

    <!-- Click Outside Detector - Transparent Backdrop -->
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
    /**
     * Show edit action button
     * Default: true
     */
    showEdit: {
      type: Boolean,
      default: true
    },
    
    /**
     * Show add action button
     * Typically used for adding child items
     * Default: false
     */
    showAdd: {
      type: Boolean,
      default: false
    },
    
    /**
     * Show check/confirm action button
     * Styled in green for positive actions
     * Default: false
     */
    showCheck: {
      type: Boolean,
      default: false
    },
    
    /**
     * Show delete action button
     * Styled in red for destructive actions
     * Default: true
     */
    showDelete: {
      type: Boolean,
      default: true
    },
    
    /**
     * Menu button tooltip text
     * Default: 'Actions'
     */
    menuTitle: {
      type: String,
      default: 'Actions'
    }
  },
  
  emits: ['edit', 'add', 'check', 'delete'],
  
  setup(props, { emit }) {
    /** @type {Ref<boolean>} Menu open/closed state */
    const isMenuOpen = ref(false)

    /**
     * Toggle menu open/closed
     * Called when three-dot button is clicked
     */
    function toggleMenu() {
      isMenuOpen.value = !isMenuOpen.value
    }

    /**
     * Close menu
     * Called when:
     * - Action button is clicked
     * - Backdrop is clicked
     * - Escape key is pressed
     */
    function closeMenu() {
      isMenuOpen.value = false
    }

    /**
     * Handle edit action
     * Emits 'edit' event and closes menu
     */
    function handleEdit() {
      emit('edit')
      closeMenu()
    }

    /**
     * Handle add action
     * Emits 'add' event and closes menu
     */
    function handleAdd() {
      emit('add')
      closeMenu()
    }

    /**
     * Handle check/confirm action
     * Emits 'check' event and closes menu
     */
    function handleCheck() {
      emit('check')
      closeMenu()
    }

    /**
     * Handle delete action
     * Emits 'delete' event and closes menu
     */
    function handleDelete() {
      emit('delete')
      closeMenu()
    }

    /**
     * Handle Escape key press
     * Closes menu if open
     * 
     * @param {KeyboardEvent} e - Keyboard event
     */
    function handleEscape(e) {
      if (e.key === 'Escape' && isMenuOpen.value) {
        closeMenu()
      }
    }

    // Register Escape key listener on mount
    onMounted(() => {
      document.addEventListener('keydown', handleEscape)
    })

    // Clean up listener on unmount
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
/* ============================================================================
   COMPONENT POSITIONING
   ============================================================================ */

.actions-menu-wrapper {
  position: relative;
  display: inline-flex;
}

/* ============================================================================
   THREE-DOT BUTTON
   ============================================================================ */

.btn-menu-dots {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  opacity: 0; /* Hidden by default, shown on parent hover */
  transition: all 0.2s;
  color: var(--color-text-light);
}

/* Show button on parent hover - requires parent to have these classes */
.category-header-compact:hover .btn-menu-dots,
.subcat-top:hover .btn-menu-dots,
.transaction-row:hover .btn-menu-dots {
  opacity: 0.6;
}

/* Always visible variant - for explicit visibility */
.actions-menu-wrapper.always-visible .btn-menu-dots {
  opacity: 1 !important;
  color: var(--color-text);
}

/* Button hover and active states */
.btn-menu-dots:hover,
.btn-menu-dots.menu-open {
  opacity: 1 !important;
  background: var(--color-background-dark);
  color: var(--color-text);
}

/* ============================================================================
   ACTIONS POPUP
   ============================================================================ */

.actions-popup {
  position: absolute;
  top: calc(100% + 0.25rem); /* Position below button */
  right: 0; /* Align to right edge */
  background: var(--color-background-light);
  backdrop-filter: blur(1rem); /* Blur background for glassmorphism */
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  z-index: 100; /* Above most content, below backdrop */
  min-width: 8rem;
}

/* ============================================================================
   ACTION BUTTONS
   ============================================================================ */

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

/* Delete action - red on hover */
.action-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Check action - green on hover */
.action-check:hover {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

/* ============================================================================
   BACKDROP
   ============================================================================ */

.menu-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99; /* Below popup, above content */
  background: transparent; /* Invisible but clickable */
}

/* ============================================================================
   TRANSITIONS
   ============================================================================ */

.actions-fade-enter-active,
.actions-fade-leave-active {
  transition: all 0.15s ease;
}

.actions-fade-enter-from,
.actions-fade-leave-to {
  opacity: 0;
  transform: translateY(-0.5rem); /* Slide up effect */
}
</style>