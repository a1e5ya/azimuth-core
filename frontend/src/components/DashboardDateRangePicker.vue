<!--
  Dashboard Date Range Picker - Multi-mode date selection interface
  
  Four selection modes with intelligent navigation and boundary constraints.
  
  Modes:
  - Monthly: Single month (start = end, synced navigation)
  - Yearly: Full year (Jan 1 - Dec 31 of selected year)
  - Range: Custom range (independent start/end controls)
  - All Time: Min to max available dates (auto-set from data)
  
  Features:
  - Dual-column layout for range selection (hidden in monthly/yearly)
  - Year/month navigation with arrow buttons
  - Boundary constraints from minAvailableDate/maxAvailableDate
  - Automatic month wrapping (Dec→Jan next year, Jan→Dec previous year)
  - Disabled navigation at min/max boundaries
-->
<template>
  <div class="time-range-picker">
    <!-- Mode toggle buttons -->
    <div class="mode-buttons">
      <button
        v-for="mode in modes"
        :key="mode.id"
        class="btn btn-small mode-btn"
        :class="{ 'btn-active': currentMode === mode.id }"
        @click="switchMode(mode.id)"
      >
        {{ mode.label }}
      </button>
    </div>

    <!-- Navigation controls (two columns, right hidden in monthly/yearly) -->
    <div class="navigation-container two-column">
      <!-- Left column: start date or single date (monthly/yearly) -->
      <div class="date-column">
        <!-- Year navigation -->
        <div class="nav-row">
          <button class="btn btn-icon nav-btn" @click="adjustYear('start', -1)" :disabled="isStartYearMin">
            <span>←</span>
          </button>
          <div class="date-display">{{ startYear }}</div>
          <button class="btn btn-icon nav-btn" @click="adjustYear('start', 1)" :disabled="isStartYearMax">
            <span>→</span>
          </button>
        </div>

        <!-- Month navigation (invisible in yearly mode) -->
        <div class="nav-row" :class="{ invisible: currentMode === 'yearly' }">
          <button class="btn btn-icon nav-btn" @click="adjustMonth('start', -1)" :disabled="isStartMonthMin">
            <span>←</span>
          </button>
          <div class="date-display">{{ getMonthName(startMonth) }}</div>
          <button class="btn btn-icon nav-btn" @click="adjustMonth('start', 1)" :disabled="isStartMonthMax">
            <span>→</span>
          </button>
        </div>
      </div>

      <!-- Right column: end date (invisible in monthly/yearly) -->
      <div class="date-column" :class="{ invisible: currentMode !== 'range' && currentMode !== 'all-time' }">
        <!-- Year navigation -->
        <div class="nav-row">
          <button class="btn btn-icon nav-btn" @click="adjustYear('end', -1)" :disabled="isEndYearMin">
            <span>←</span>
          </button>
          <div class="date-display">{{ endYear }}</div>
          <button class="btn btn-icon nav-btn" @click="adjustYear('end', 1)" :disabled="isEndYearMax">
            <span>→</span>
          </button>
        </div>

        <!-- Month navigation -->
        <div class="nav-row">
          <button class="btn btn-icon nav-btn" @click="adjustMonth('end', -1)" :disabled="isEndMonthMin">
            <span>←</span>
          </button>
          <div class="date-display">{{ getMonthName(endMonth) }}</div>
          <button class="btn btn-icon nav-btn" @click="adjustMonth('end', 1)" :disabled="isEndMonthMax">
            <span>→</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Labels row (always present for layout stability, invisible in monthly/yearly) -->
    <div class="labels-row">
      <div class="label-column" :class="{ invisible: currentMode !== 'range' && currentMode !== 'all-time' }">
        FROM
      </div>
      <div class="label-column" :class="{ invisible: currentMode !== 'range' && currentMode !== 'all-time' }">
        TO
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'DashboardDateRangePicker',
  props: {
    /**
     * Current date range
     * @type {Object}
     */
    dateRange: {
      type: Object,
      required: true,
      validator: (value) => {
        return value.startDate instanceof Date && value.endDate instanceof Date
      }
    },
    /**
     * Minimum available date (from dataset)
     * @type {Date|String}
     */
    minAvailableDate: {
      type: [Date, String],
      default: null
    },
    /**
     * Maximum available date (from dataset)
     * @type {Date|String}
     */
    maxAvailableDate: {
      type: [Date, String],
      default: null
    }
  },
  emits: [
    /**
     * Date range update event
     * @param {Object} range - New date range {startDate, endDate}
     */
    'update:dateRange'
  ],
  setup(props, { emit }) {
    const currentMode = ref('all-time')
    
    const startYear = ref(props.dateRange.startDate.getFullYear())
    const startMonth = ref(props.dateRange.startDate.getMonth())
    const endYear = ref(props.dateRange.endDate.getFullYear())
    const endMonth = ref(props.dateRange.endDate.getMonth())

    const modes = [
      { id: 'monthly', label: 'Monthly' },
      { id: 'yearly', label: 'Yearly' },
      { id: 'range', label: 'Range' },
      { id: 'all-time', label: 'All Time' }
    ]

    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ]

    /** Sync local state when prop changes */
    watch(() => props.dateRange, (newRange) => {
      startYear.value = newRange.startDate.getFullYear()
      startMonth.value = newRange.startDate.getMonth()
      endYear.value = newRange.endDate.getFullYear()
      endMonth.value = newRange.endDate.getMonth()
    }, { deep: true })

    /** Min year from dataset */
    const minYear = computed(() => {
      if (!props.minAvailableDate) return 2000
      const date = props.minAvailableDate instanceof Date 
        ? props.minAvailableDate 
        : new Date(props.minAvailableDate)
      return date.getFullYear()
    })
    
    /** Max year from dataset */
    const maxYear = computed(() => {
      if (!props.maxAvailableDate) return new Date().getFullYear()
      const date = props.maxAvailableDate instanceof Date 
        ? props.maxAvailableDate 
        : new Date(props.maxAvailableDate)
      return date.getFullYear()
    })
    
    /** Min month from dataset */
    const minMonth = computed(() => {
      if (!props.minAvailableDate) return 0
      const date = props.minAvailableDate instanceof Date 
        ? props.minAvailableDate 
        : new Date(props.minAvailableDate)
      return date.getMonth()
    })
    
    /** Max month from dataset */
    const maxMonth = computed(() => {
      if (!props.maxAvailableDate) return 11
      const date = props.maxAvailableDate instanceof Date 
        ? props.maxAvailableDate 
        : new Date(props.maxAvailableDate)
      return date.getMonth()
    })

    /** Start year at minimum boundary */
    const isStartYearMin = computed(() => {
      return startYear.value <= minYear.value
    })

    /** Start year at maximum boundary (varies by mode) */
    const isStartYearMax = computed(() => {
      if (currentMode.value === 'monthly' || currentMode.value === 'yearly') {
        return startYear.value >= maxYear.value
      }
      return startYear.value >= endYear.value
    })

    /** End year cannot be before start year */
    const isEndYearMin = computed(() => {
      return endYear.value <= startYear.value
    })

    /** End year at maximum boundary */
    const isEndYearMax = computed(() => {
      return endYear.value >= maxYear.value
    })

    /** Start month at minimum boundary (considers year) */
    const isStartMonthMin = computed(() => {
      if (startYear.value === minYear.value) {
        return startMonth.value <= minMonth.value
      }
      return startMonth.value <= 0
    })

    /** Start month at maximum boundary (varies by mode) */
    const isStartMonthMax = computed(() => {
      if (currentMode.value === 'monthly') {
        if (startYear.value === maxYear.value) {
          return startMonth.value >= maxMonth.value
        }
        return startMonth.value >= 11
      }
      if (startYear.value === endYear.value) {
        return startMonth.value >= endMonth.value
      }
      return startMonth.value >= 11
    })

    /** End month cannot be before start month (same year) */
    const isEndMonthMin = computed(() => {
      if (startYear.value === endYear.value) {
        return endMonth.value <= startMonth.value
      }
      return endMonth.value <= 0
    })

    /** End month at maximum boundary */
    const isEndMonthMax = computed(() => {
      if (endYear.value === maxYear.value) {
        return endMonth.value >= maxMonth.value
      }
      return endMonth.value >= 11
    })

    /**
     * Get month name from index
     * @param {number} monthIndex - 0-11
     * @returns {string} Month name
     */
    function getMonthName(monthIndex) {
      return monthNames[monthIndex]
    }

    /**
     * Switch mode and update date range
     * - Monthly: Sets to current month, syncs start=end
     * - Yearly: Sets to current year (Jan 1 - Dec 31)
     * - Range: Keeps current selection
     * - All Time: Sets to min/max available dates
     * @param {string} modeId - Mode identifier
     */
    function switchMode(modeId) {
      currentMode.value = modeId

      switch (modeId) {
        case 'monthly':
          { const currentDate = new Date()
          startYear.value = currentDate.getFullYear()
          startMonth.value = currentDate.getMonth()
          endYear.value = currentDate.getFullYear()
          endMonth.value = currentDate.getMonth()
          emitDateRange()
          break }

        case 'yearly':
          { const currentYear = new Date().getFullYear()
          startYear.value = currentYear
          startMonth.value = 0
          endYear.value = currentYear
          endMonth.value = 11
          emitDateRange()
          break }

        case 'range':
          emitDateRange()
          break

        case 'all-time':
          if (props.minAvailableDate && props.maxAvailableDate) {
            const minDate = props.minAvailableDate instanceof Date 
              ? props.minAvailableDate 
              : new Date(props.minAvailableDate)
            const maxDate = props.maxAvailableDate instanceof Date 
              ? props.maxAvailableDate 
              : new Date(props.maxAvailableDate)
            
            startYear.value = minDate.getFullYear()
            startMonth.value = minDate.getMonth()
            endYear.value = maxDate.getFullYear()
            endMonth.value = maxDate.getMonth()
            emitDateRange()
          }
          break
      }
    }

    /**
     * Adjust year
     * In monthly/yearly modes, syncs end year to start year
     * @param {'start'|'end'} target - Which year to adjust
     * @param {number} delta - +1 or -1
     */
    function adjustYear(target, delta) {
      if (target === 'start') {
        const newYear = startYear.value + delta
        if (newYear >= minYear.value && newYear <= maxYear.value) {
          startYear.value = newYear
          
          if (currentMode.value === 'monthly') {
            endYear.value = newYear
          } else if (currentMode.value === 'yearly') {
            endYear.value = newYear
          }
          
          emitDateRange()
        }
      } else {
        const newYear = endYear.value + delta
        if (newYear >= startYear.value && newYear <= maxYear.value) {
          endYear.value = newYear
          emitDateRange()
        }
      }
    }

    /**
     * Adjust month with year wrapping
     * Dec→Jan next year, Jan→Dec previous year
     * In monthly mode, syncs end month to start month
     * @param {'start'|'end'} target - Which month to adjust
     * @param {number} delta - +1 or -1
     */
    function adjustMonth(target, delta) {
      if (target === 'start') {
        let newMonth = startMonth.value + delta
        let newYear = startYear.value

        // Handle month wrapping
        if (newMonth < 0) {
          newMonth = 11
          newYear -= 1
        } else if (newMonth > 11) {
          newMonth = 0
          newYear += 1
        }

        if (newYear >= minYear.value && newYear <= maxYear.value) {
          startMonth.value = newMonth
          startYear.value = newYear
          
          if (currentMode.value === 'monthly') {
            endMonth.value = newMonth
            endYear.value = newYear
          }
          
          emitDateRange()
        }
      } else {
        let newMonth = endMonth.value + delta
        let newYear = endYear.value

        // Handle month wrapping
        if (newMonth < 0) {
          newMonth = 11
          newYear -= 1
        } else if (newMonth > 11) {
          newMonth = 0
          newYear += 1
        }

        if (newYear >= startYear.value && newYear <= maxYear.value) {
          endMonth.value = newMonth
          endYear.value = newYear
          emitDateRange()
        }
      }
    }

    /**
     * Emit date range to parent
     * Constructs Date objects:
     * - Start: First day of month (day 1, 00:00:00)
     * - End: Last day of month (new Date(year, month+1, 0) trick)
     */
    function emitDateRange() {
      const startDate = new Date(startYear.value, startMonth.value, 1)
      const endDate = new Date(endYear.value, endMonth.value + 1, 0)
      
      emit('update:dateRange', {
        startDate,
        endDate
      })
    }

    return {
      currentMode,
      modes,
      startYear,
      startMonth,
      endYear,
      endMonth,
      isStartYearMin,
      isStartYearMax,
      isEndYearMin,
      isEndYearMax,
      isStartMonthMin,
      isStartMonthMax,
      isEndMonthMin,
      isEndMonthMax,
      getMonthName,
      switchMode,
      adjustYear,
      adjustMonth
    }
  }
}
</script>

<style scoped>
.time-range-picker {
  display: flex;
  flex-direction: column;
  width: 450px;
  gap: var(--gap-small);
  padding:  1rem;
}

.mode-buttons {
  display: flex;
  gap: 0.5rem;
}

.mode-btn {
  margin: 0;
  flex: 1;
  padding: 0.5rem 0.75rem;
  font-size: var(--text-small);
}

.navigation-container {
  display: flex;
  gap: var(--gap-small);
}

.navigation-container.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-small);
}

.date-column {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.date-column.invisible {
  visibility: hidden;
}

.nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.25rem;
}

.nav-row.invisible {
  visibility: hidden;
}

.nav-btn {
  padding: 0.25rem 0.5rem;
  min-width: 2rem;
}

.date-display {
  flex: 1;
  text-align: center;
  font-size: var(--text-small);
  font-weight: 500;
  padding: 0.25rem;
}

.labels-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-small);
  margin-top: 0.25rem;
}

.label-column {
  text-align: center;
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-muted);
  letter-spacing: 0.05em;
}

.label-column.invisible {
  visibility: hidden;
}
</style>