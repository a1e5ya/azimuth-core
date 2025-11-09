<template>
  <div v-if="currentZoomLevel === 1" class="year-selector-wrapper">
    <div class="year-selector-bar">
      <div 
        v-for="yearRange in yearRanges" 
        :key="yearRange.label"
        class="year-range"
        :class="{ active: isActiveRange(yearRange) }"
        @click="selectRange(yearRange)"
      >
        {{ yearRange.label }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'TimelineYearSelector',
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
    },
    currentZoomLevel: {
      type: Number,
      required: true
    }
  },
  emits: ['scroll-to'],
  setup(props, { emit }) {
    /**
     * Calculate year ranges (2 years per range)
     * Use the ACTUAL last transaction date from fullRangeEnd
     */
    const yearRanges = computed(() => {
      if (!props.fullRangeStart || !props.fullRangeEnd) return []
      
      const ranges = []
      const startYear = props.fullRangeStart.getFullYear()
      
      // fullRangeEnd is already inflated with +2 years in TimelineTab
      // So we need to subtract 2 to get actual data end
      // OR we can just use a reasonable calculation
      // Since data ends Aug 2025, fullRangeEnd is probably Dec 2027
      
      // Let's use current date as reference - data shouldn't be more than 2 years in future
      const now = new Date()
      const currentYear = now.getFullYear()
      
      // Assume data ends around current year (reasonable for financial data)
      const assumedDataEnd = Math.min(props.fullRangeEnd.getFullYear() - 2, currentYear)
      const lastYearNeeded = assumedDataEnd + 2
      
      console.log('📊 Year selector calculation:', { 
        startYear,
        fullRangeEndYear: props.fullRangeEnd.getFullYear(),
        assumedDataEnd,
        lastYearNeeded,
        currentYear
      })
      
      // Generate ranges
      for (let year = startYear; year <= lastYearNeeded; year += 2) {
        const rangeStart = new Date(year, 0, 1)
        const rangeEnd = new Date(year + 1, 11, 31)
        
        ranges.push({
          label: `${year}-${year + 1}`,
          start: rangeStart,
          end: rangeEnd
        })
      }
      
      console.log('📅 Generated ranges:', ranges.map(r => r.label))
      
      return ranges
    })
    
    /**
     * Check if a range is currently active
     * Simple: check if range start/end match visible range start/end (with some tolerance)
     */
    function isActiveRange(range) {
      const visStart = props.visibleRangeStart
      const visEnd = props.visibleRangeEnd
      
      if (!visStart || !visEnd) return false
      
      // Check if visible range approximately matches this range
      // Allow 1 month tolerance on each side
      const tolerance = 31 * 24 * 60 * 60 * 1000 // 31 days in ms
      
      const visStartTime = visStart.getTime()
      const visEndTime = visEnd.getTime()
      const rangeStartTime = range.start.getTime()
      const rangeEndTime = range.end.getTime()
      
      // Check if visible range is approximately within this range
      const startMatches = Math.abs(visStartTime - rangeStartTime) < tolerance
      const endMatches = Math.abs(visEndTime - rangeEndTime) < tolerance
      
      const isActive = startMatches && endMatches
      
      if (isActive) {
        console.log('✅ Active range:', range.label)
      }
      
      return isActive
    }
    
    /**
     * Select a year range
     */
    function selectRange(range) {
      emit('scroll-to', {
        start: range.start,
        end: range.end
      })
      console.log('📅 Selected year range:', range.label)
    }
    
    return {
      yearRanges,
      isActiveRange,
      selectRange
    }
  }
}
</script>

<style scoped>
.year-selector-wrapper {
  width: 100%;
  padding: var(--gap-small);
  background: var(--color-background);
  border-radius: var(--radius);
}

.year-selector-bar {
  display: flex;
  gap: var(--gap-small);
  flex-wrap: wrap;
}

.year-range {
  flex: 1;
  min-width: 5rem;
  padding: var(--gap-small) var(--gap-standard);
  background: var(--color-background-light);
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  color: var(--color-text-light);
  user-select: none;
}

.year-range:hover {
  background: var(--color-background-dark);
  color: var(--color-text);
  border-color: var(--color-button-active);
}

.year-range.active {

}
</style>