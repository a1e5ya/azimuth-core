<template>
  <div class="timeline-controls-wrapper">
    <!-- Main Controls Row -->
    <div class="controls-row">
      <!-- Zoom Controls - Left Side -->
      <div class="zoom-controls">
        <button 
          class="btn btn-icon btn-small"
          :disabled="currentZoomLevel <= 0"
          @click="$emit('zoom-out')"
          title="Zoom Out"
        >
          <AppIcon name="zoom-out" size="small" />
        </button>
        
        <button 
          class="btn btn-icon btn-small"
          :disabled="currentZoomLevel >= 2"
          @click="$emit('zoom-in')"
          title="Zoom In"
        >
          <AppIcon name="zoom-in" size="small" />
        </button>
        
        <button 
          class="btn btn-icon btn-small"
          @click="$emit('reset-zoom')"
          title="Reset Zoom"
        >
          <AppIcon name="refresh" size="small" />
        </button>
      </div>

      <!-- Mode Toggle Switch - Right Side -->
      <div class="mode-toggle-switch">
        <label class="toggle-label">
          <input 
            type="checkbox" 
            :checked="currentMode === 'add'"
            @change="toggleMode"
          />
          <span class="toggle-slider">
            <span class="toggle-option toggle-view" :class="{ active: currentMode === 'view' }">
              <AppIcon name="eye" size="small" />
            </span>
            <span class="toggle-option toggle-add" :class="{ active: currentMode === 'add' }">
              <AppIcon name="plus" size="small" />
            </span>
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onUnmounted } from 'vue'
import AppIcon from './AppIcon.vue'

export default {
  name: 'TimelineControls',
  components: {
    AppIcon
  },
  props: {
    currentZoomLevel: {
      type: Number,
      required: true
    },
    currentMode: {
      type: String,
      default: 'view'
    },
    fullRangeStart: {
      type: Date,
      required: true
    },
    fullRangeEnd: {
      type: Date,
      required: true
    },
    visibleRangeStart: {
      type: Date,
      required: true
    },
    visibleRangeEnd: {
      type: Date,
      required: true
    }
  },
  emits: ['zoom-in', 'zoom-out', 'reset-zoom', 'set-mode', 'scroll-to'],
  setup(props, { emit }) {
    // Toggle between view and add modes
    function toggleMode() {
      const newMode = props.currentMode === 'view' ? 'add' : 'view'
      emit('set-mode', newMode)
    }

    return {
      toggleMode
    }
  }
}
</script>

<style scoped>
.timeline-controls-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

/* Controls Row */
.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--gap-standard);
}

/* Zoom Controls */
.zoom-controls {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.zoom-controls .btn-icon {
  background: var(--color-background);
  border: 1px solid var(--color-background-dark);
  padding: 0;
  margin: 0;
  width: 2rem;
  height: 2rem;
  box-shadow: none;
  transition: all 0.2s;
}

.zoom-controls .btn-icon:hover:not(:disabled) {
  background: var(--color-background-light);
}

.zoom-controls .btn-icon:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Mode Toggle Switch */
.mode-toggle-switch {
  display: flex;
  align-items: center;
}

.toggle-label {
  position: relative;
  display: inline-block;
  width: 5rem;
  height: 2rem;
  cursor: pointer;
}

.toggle-label input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-background-dark);
  border-radius: var(--radius);
  transition: all 0.3s;
  display: flex;
  align-items: center;
  padding: 0.125rem;
}

.toggle-option {
  position: absolute;
width: 2rem;
    height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
      border-radius: var(--radius);
        background: var(--color-background-light);
        opacity: 0.8;
  transition: all 0.3s;
  z-index: 1;
  color: var(--color-text-light);
}

.toggle-view {
  left: 0.125rem;
}

.toggle-add {
  right: 0.125rem;
}

.toggle-option.active {
  background: var(--color-background-light);
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Responsive */
@media (max-width: 48rem) {
  .controls-row {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .zoom-controls {
    flex: 1;
    justify-content: flex-start;
  }

  .mode-toggle-switch {
    flex: 0 0 auto;
  }
}

@media (max-width: 30rem) {
  .toggle-label {
    width: 4.5rem;
    height: 1.75rem;
  }

  .toggle-option {
    width: 2rem;
    height: 1.25rem;
  }
}
</style>