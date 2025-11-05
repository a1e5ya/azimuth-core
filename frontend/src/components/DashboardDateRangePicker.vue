<template>
  <div class="time-range-picker">
    <!-- Mode Toggle Buttons -->
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

    <!-- Navigation Controls -->
    <div class="navigation-container two-column">
      <!-- Single Column (Monthly/Yearly) or Left Column (Range/All Time) -->
      <div class="date-column">
        <!-- Year Navigation -->
        <div class="nav-row">
          <button class="btn btn-icon nav-btn" @click="adjustYear('start', -1)" :disabled="isStartYearMin">
            <span>←</span>
          </button>
          <div class="date-display">{{ startYear }}</div>
          <button class="btn btn-icon nav-btn" @click="adjustYear('start', 1)" :disabled="isStartYearMax">
            <span>→</span>
          </button>
        </div>

        <!-- Month Navigation (only for Monthly, Range, and All Time) -->
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

      <!-- Right Column (Range and All Time modes only, invisible otherwise) -->
      <div class="date-column" :class="{ invisible: currentMode !== 'range' && currentMode !== 'all-time' }">
        <!-- Year Navigation -->
        <div class="nav-row">
          <button class="btn btn-icon nav-btn" @click="adjustYear('end', -1)" :disabled="isEndYearMin">
            <span>←</span>
          </button>
          <div class="date-display">{{ endYear }}</div>
          <button class="btn btn-icon nav-btn" @click="adjustYear('end', 1)" :disabled="isEndYearMax">
            <span>→</span>
          </button>
        </div>

        <!-- Month Navigation -->
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

    <!-- Labels Row (always present for consistent sizing) -->
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
    dateRange: {
      type: Object,
      required: true,
      validator: (value) => {
        return value.startDate instanceof Date && value.endDate instanceof Date
      }
    },
    minAvailableDate: {
      type: [Date, String],
      default: null
    },
    maxAvailableDate: {
      type: [Date, String],
      default: null
    }
  },
  emits: ['update:dateRange'],
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

    watch(() => props.dateRange, (newRange) => {
      startYear.value = newRange.startDate.getFullYear()
      startMonth.value = newRange.startDate.getMonth()
      endYear.value = newRange.endDate.getFullYear()
      endMonth.value = newRange.endDate.getMonth()
    }, { deep: true })

    const minYear = computed(() => {
      if (!props.minAvailableDate) return 2000
      const date = props.minAvailableDate instanceof Date 
        ? props.minAvailableDate 
        : new Date(props.minAvailableDate)
      return date.getFullYear()
    })
    
    const maxYear = computed(() => {
      if (!props.maxAvailableDate) return new Date().getFullYear()
      const date = props.maxAvailableDate instanceof Date 
        ? props.maxAvailableDate 
        : new Date(props.maxAvailableDate)
      return date.getFullYear()
    })
    
    const minMonth = computed(() => {
      if (!props.minAvailableDate) return 0
      const date = props.minAvailableDate instanceof Date 
        ? props.minAvailableDate 
        : new Date(props.minAvailableDate)
      return date.getMonth()
    })
    
    const maxMonth = computed(() => {
      if (!props.maxAvailableDate) return 11
      const date = props.maxAvailableDate instanceof Date 
        ? props.maxAvailableDate 
        : new Date(props.maxAvailableDate)
      return date.getMonth()
    })

    const isStartYearMin = computed(() => {
      return startYear.value <= minYear.value
    })

    const isStartYearMax = computed(() => {
      if (currentMode.value === 'monthly' || currentMode.value === 'yearly') {
        return startYear.value >= maxYear.value
      }
      return startYear.value >= endYear.value
    })

    const isEndYearMin = computed(() => {
      return endYear.value <= startYear.value
    })

    const isEndYearMax = computed(() => {
      return endYear.value >= maxYear.value
    })

    const isStartMonthMin = computed(() => {
      if (startYear.value === minYear.value) {
        return startMonth.value <= minMonth.value
      }
      return startMonth.value <= 0
    })

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

    const isEndMonthMin = computed(() => {
      if (startYear.value === endYear.value) {
        return endMonth.value <= startMonth.value
      }
      return endMonth.value <= 0
    })

    const isEndMonthMax = computed(() => {
      if (endYear.value === maxYear.value) {
        return endMonth.value >= maxMonth.value
      }
      return endMonth.value >= 11
    })

    function getMonthName(monthIndex) {
      return monthNames[monthIndex]
    }

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

    function adjustMonth(target, delta) {
      if (target === 'start') {
        let newMonth = startMonth.value + delta
        let newYear = startYear.value

        if (newMonth < 0) {
          newMonth = 11
          newYear -= 1
        } else if (newMonth > 11) {
          newMonth = 0
          newYear += 1
        }

        if (newYear >= minYear.value && newYear <= maxYear.value) {
          startYear.value = newYear
          startMonth.value = newMonth

          if (currentMode.value === 'monthly') {
            endYear.value = newYear
            endMonth.value = newMonth
          }

          emitDateRange()
        }
      } else {
        let newMonth = endMonth.value + delta
        let newYear = endYear.value

        if (newMonth < 0) {
          newMonth = 11
          newYear -= 1
        } else if (newMonth > 11) {
          newMonth = 0
          newYear += 1
        }

        if (newYear >= startYear.value && newYear <= maxYear.value) {
          endYear.value = newYear
          endMonth.value = newMonth
          emitDateRange()
        }
      }
    }

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
  gap: var(--gap-standard);
  padding: 1.25rem;
}

.mode-buttons {
  display: flex;
  gap: var(--gap-small);
  flex-wrap: wrap;
  justify-content: space-between;
}

.mode-btn {
  margin: 0;
}

.labels-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-standard);
  margin-top: var(--gap-small);
}

.label-column {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: center;
}

.label-column.invisible {
  visibility: hidden;
}

.navigation-container {
  display: flex;
  gap: var(--gap-standard);
}

.navigation-container.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.date-column {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.date-column.invisible {
  visibility: hidden;
}

.nav-row {
  display: grid;
  grid-template-columns: 2.5rem 1fr 2.5rem;
  gap: var(--gap-small);
  align-items: center;
}

.nav-row.invisible {
  visibility: hidden;
}

.nav-btn {
  width: 2.5rem;
  height: 2.5rem;
  margin: 0;
  font-size: 1rem;
}

.date-display {
  text-align: center;
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
  padding: var(--gap-small);
  background: var(--color-background);
  border: 0.0625rem solid rgba(0, 0, 0, 0.1);
  border-radius: var(--radius);
}
</style>