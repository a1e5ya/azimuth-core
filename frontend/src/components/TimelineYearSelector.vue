<!--
  TimelineYearSelector Component - Year Range Navigation
  
  Provides year range selector for timeline navigation:
  - 2-year range buttons for quick navigation
  - Active range highlighting
  - Only visible at Month zoom level
  - Automatic range generation from data
  
  Features:
  - Dynamic range calculation from full data range
  - 2-year chunks for easy navigation
  - Active state detection with tolerance
  - Click to scroll to specific range
  - Auto-adjusts to current year
  - Flexible wrapping layout
  
  Props:
  - fullRangeStart: Date - Full data range start
  - fullRangeEnd: Date - Full data range end (inflated +2 years)
  - visibleRangeStart: Date - Currently visible range start
  - visibleRangeEnd: Date - Currently visible range end
  - currentZoomLevel: Number - Current zoom level (only shows at level 1)
  
  Events:
  - @scroll-to: Emitted when range clicked
    Payload: { start: Date, end: Date }
  
  Visibility:
  - Only shown when currentZoomLevel === 1 (Month view)
  - Hidden at Year and Quarter levels
  
  Range Calculation:
  - Generates 2-year ranges (e.g., 2020-2021, 2022-2023)
  - Adjusts end year based on actual data (not inflated range)
  - Ensures ranges cover all historical data
-->

<template>
  <!-- Only show at Month zoom level -->
  <div v-if="currentZoomLevel === 1" class="year-selector-wrapper">
    <div class="year-selector-bar">
      <!-- Year Range Buttons -->
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
import { computed } from 'vue'

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
     * Calculates year ranges (2 years per range) from full data range
     * Adjusts for inflated fullRangeEnd by subtracting 2 years
     * @type {import('vue').ComputedRef<Array<{label: string, start: Date, end: Date}>>}
     */
    const yearRanges = computed(() => {
      if (!props.fullRangeStart || !props.fullRangeEnd) return []
      
      const ranges = []
      const startYear = props.fullRangeStart.getFullYear()
      
      const now = new Date()
      const currentYear = now.getFullYear()
      
      const assumedDataEnd = Math.min(props.fullRangeEnd.getFullYear() - 2, currentYear)
      const lastYearNeeded = assumedDataEnd + 2
      
      for (let year = startYear; year <= lastYearNeeded; year += 2) {
        const rangeStart = new Date(year, 0, 1)
        const rangeEnd = new Date(year + 1, 11, 31)
        
        ranges.push({
          label: `${year}-${year + 1}`,
          start: rangeStart,
          end: rangeEnd
        })
      }
      
      return ranges
    })
    
    /**
     * Checks if a range is currently active
     * Uses tolerance of 31 days for approximate matching
     * @param {Object} range - Range object to check
     * @returns {boolean} True if range is active
     */
    function isActiveRange(range) {
      const visStart = props.visibleRangeStart
      const visEnd = props.visibleRangeEnd
      
      if (!visStart || !visEnd) return false
      
      const tolerance = 31 * 24 * 60 * 60 * 1000
      
      const visStartTime = visStart.getTime()
      const visEndTime = visEnd.getTime()
      const rangeStartTime = range.start.getTime()
      const rangeEndTime = range.end.getTime()
      
      const startMatches = Math.abs(visStartTime - rangeStartTime) < tolerance
      const endMatches = Math.abs(visEndTime - rangeEndTime) < tolerance
      
      return startMatches && endMatches
    }
    
    /**
     * Selects a year range and emits scroll-to event
     * @param {Object} range - Range object with start and end dates
     * @returns {void}
     */
    function selectRange(range) {
      emit('scroll-to', {
        start: range.start,
        end: range.end
      })
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


</style>