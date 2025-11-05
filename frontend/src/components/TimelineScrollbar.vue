<template>
  <div class="timeline-scrollbar-wrapper">
    <div 
      class="scrollbar-track" 
      ref="trackRef"
      @mousedown="handleTrackClick"
    >
      <div 
        class="scrollbar-thumb"
        ref="thumbRef"
        :style="thumbStyle"
        @mousedown.stop="startDragging"
      ></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onUnmounted, watch } from 'vue'

export default {
  name: 'TimelineScrollbar',
  props: {
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
  emits: ['scroll-to'],
  setup(props, { emit }) {
    const trackRef = ref(null)
    const thumbRef = ref(null)
    const isDragging = ref(false)
    const dragStartX = ref(0)
    const dragStartLeft = ref(0)

    const thumbStyle = computed(() => {
      const fullRange = props.fullRangeEnd.getTime() - props.fullRangeStart.getTime()
      if (fullRange <= 0) return { width: '100%', left: '0%' }
      
      const visibleRange = props.visibleRangeEnd.getTime() - props.visibleRangeStart.getTime()
      const visibleStart = props.visibleRangeStart.getTime() - props.fullRangeStart.getTime()
      
      const widthPercent = Math.min(100, Math.max(8, (visibleRange / fullRange) * 100))
      const leftPercent = Math.max(0, Math.min(100 - widthPercent, (visibleStart / fullRange) * 100))
      
      return {
        width: `${widthPercent}%`,
        left: `${leftPercent}%`
      }
    })

    function handleTrackClick(event) {
      if (event.target.classList.contains('scrollbar-thumb')) return
      
      const rect = event.currentTarget.getBoundingClientRect()
      const clickX = event.clientX - rect.left
      const clickPercent = clickX / rect.width
      
      const fullRange = props.fullRangeEnd.getTime() - props.fullRangeStart.getTime()
      const visibleRange = props.visibleRangeEnd.getTime() - props.visibleRangeStart.getTime()
      
      const targetCenter = props.fullRangeStart.getTime() + (fullRange * clickPercent)
      const newStart = new Date(targetCenter - (visibleRange / 2))
      const newEnd = new Date(targetCenter + (visibleRange / 2))
      
      emit('scroll-to', { start: newStart, end: newEnd })
    }

    function startDragging(event) {
      event.preventDefault()
      
      isDragging.value = true
      dragStartX.value = event.clientX
      
      const thumbElement = thumbRef.value
      const thumbLeft = parseFloat(thumbElement.style.left) || 0
      dragStartLeft.value = thumbLeft
      
      document.addEventListener('mousemove', handleDrag)
      document.addEventListener('mouseup', stopDragging)
      document.body.style.userSelect = 'none'
      document.body.style.cursor = 'grabbing'
    }

    function handleDrag(event) {
      if (!isDragging.value) return
      
      const track = trackRef.value
      const rect = track.getBoundingClientRect()
      const deltaX = event.clientX - dragStartX.value
      const deltaPercent = (deltaX / rect.width) * 100
      
      const thumbWidth = parseFloat(thumbStyle.value.width)
      const newLeft = Math.max(0, Math.min(100 - thumbWidth, dragStartLeft.value + deltaPercent))
      const leftDecimal = newLeft / 100
      
      const fullRange = props.fullRangeEnd.getTime() - props.fullRangeStart.getTime()
      const visibleRange = props.visibleRangeEnd.getTime() - props.visibleRangeStart.getTime()
      
      const newStart = new Date(props.fullRangeStart.getTime() + (fullRange * leftDecimal))
      const newEnd = new Date(newStart.getTime() + visibleRange)
      
      emit('scroll-to', { start: newStart, end: newEnd })
    }

    function stopDragging() {
      isDragging.value = false
      document.removeEventListener('mousemove', handleDrag)
      document.removeEventListener('mouseup', stopDragging)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }

    watch(() => [props.visibleRangeStart, props.visibleRangeEnd], () => {
      console.log('📏 Scrollbar thumb updated')
    })

    onUnmounted(() => {
      document.removeEventListener('mousemove', handleDrag)
      document.removeEventListener('mouseup', stopDragging)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    })

    return {
      trackRef,
      thumbRef,
      thumbStyle,
      handleTrackClick,
      startDragging
    }
  }
}
</script>

<style scoped>
.timeline-scrollbar-wrapper {
  width: 100%;
  padding: var(--gap-small);
  background: var(--color-background);
  border-radius: var(--radius);
}

.scrollbar-track {
  position: relative;
  width: 100%;
  height: var(--gap-small);
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  border: 1px solid var(--color-background-dark);
}

.scrollbar-thumb {
  position: absolute;
  top: 0;
  height: 100%;
  background: var(--color-button-active);
  border-radius: 0.25rem;
  cursor: grab;
  transition: background 0.15s;
  min-width: 8%;
  opacity: 1;
}

.scrollbar-thumb:hover {
  background: var(--color-button-active);
  opacity: 0.85;
}

.scrollbar-thumb:active {
  cursor: grabbing;
  background: var(--color-button-active);
  opacity: 1;
}
</style>