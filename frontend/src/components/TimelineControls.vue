<template>
  <div class="timeline-controls-wrapper">
    <!-- Main Controls Row -->
    <div class="controls-row">
      <!-- Zoom Level Toggle - Left Side -->
      <div class="zoom-level-toggle">
        <button 
          v-for="level in zoomLevels" 
          :key="level.value"
          class="btn btn-zoom-level"
          :class="{ active: currentZoomLevel === level.value }"
          @click="$emit('set-zoom-level', level.value)"
          :title="`View by ${level.label}`"
        >
          {{ level.label }}
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
  emits: ['zoom-in', 'zoom-out', 'reset-zoom', 'set-mode', 'scroll-to', 'set-zoom-level'],
  setup(props, { emit }) {
    const zoomLevels = [
      { value: -1, label: 'Year' },
      { value: 0, label: 'Quarter' },
      { value: 1, label: 'Month' }
    ]

    function toggleMode() {
      const newMode = props.currentMode === 'view' ? 'add' : 'view'
      emit('set-mode', newMode)
    }

    return {
      zoomLevels,
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

.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--gap-standard);
}

.zoom-level-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
  background: var(--color-background-dark);
  border-radius: var(--radius);
  padding: 0.125rem;
  height: 2rem;
}

.btn-zoom-level {
  background: transparent;
  border: none;
  padding: 0 0.75rem;
  height: 1.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-light);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  opacity: 0.8;
  z-index: 1;
  position: relative;
}

.btn-zoom-level:hover:not(.active) {
  opacity: 1;
}

.btn-zoom-level.active {
  background: var(--color-background-light);

  opacity: 1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

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

  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>