<template>
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
</template>

<script>
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
    }
  },
  emits: ['zoom-in', 'zoom-out', 'reset-zoom']
}
</script>

<style scoped>
.zoom-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--gap-small);
  border-radius: var(--radius);
}

.zoom-controls .btn-icon {
  background: transparent;
  border: none;
  padding: 0;
  margin: 0;
  width: 1.5rem;
  height: 1.5rem;
  box-shadow: none;
}

@media (max-width: 48rem) {
  .zoom-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>