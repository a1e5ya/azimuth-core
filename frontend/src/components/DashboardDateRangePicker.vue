<template>
  <div class="date-range-picker">
    <!-- Preset Buttons -->
    <div class="preset-buttons">
      <button
        v-for="preset in presets"
        :key="preset.id"
        class="btn btn-small"
        :class="{ 'btn-active': isPresetActive(preset.id) }"
        @click="applyPreset(preset.id)"
      >
        {{ preset.label }}
      </button>
    </div>

    <!-- Custom Month Inputs -->
    <div class="custom-date-inputs">
      <div class="date-input-group">
        <label for="start-month">From</label>
        <input
          id="start-month"
          type="month"
          :value="localStartMonth"
          :max="localEndMonth"
          @input="updateStartMonth"
          class="filter-input"
        />
      </div>

      <div class="date-separator">→</div>

      <div class="date-input-group">
        <label for="end-month">To</label>
        <input
          id="end-month"
          type="month"
          :value="localEndMonth"
          :min="localStartMonth"
          @input="updateEndMonth"
          class="filter-input"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'DashboardDateRangePicker',
  props: {
    dateRange: {
      type: Object,
      required: true,
      validator: (value) => {
        return value.startDate instanceof Date && value.endDate instanceof Date
      }
    }
  },
  emits: ['update:dateRange'],
  setup(props, { emit }) {
    const localStartMonth = ref(formatMonthForInput(props.dateRange.startDate))
    const localEndMonth = ref(formatMonthForInput(props.dateRange.endDate))
    const activePreset = ref('all-time')

    // Only 3 presets
    const presets = [
      { id: 'all-time', label: 'All Time' },
      { id: 'this-year', label: 'This Year' },
      { id: 'this-month', label: 'This Month' }
    ]

    // Watch for external changes to dateRange prop
    watch(() => props.dateRange, (newRange) => {
      localStartMonth.value = formatMonthForInput(newRange.startDate)
      localEndMonth.value = formatMonthForInput(newRange.endDate)
    }, { deep: true })

    function formatMonthForInput(date) {
      if (!date) return ''
      const d = new Date(date)
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      return `${year}-${month}`
    }

    function updateStartMonth(event) {
      localStartMonth.value = event.target.value
      activePreset.value = 'custom'
      emitDateRange()
    }

    function updateEndMonth(event) {
      localEndMonth.value = event.target.value
      activePreset.value = 'custom'
      emitDateRange()
    }

    function emitDateRange() {
      const [startYear, startMonth] = localStartMonth.value.split('-').map(Number)
      const [endYear, endMonth] = localEndMonth.value.split('-').map(Number)
      
      const startDate = new Date(startYear, startMonth - 1, 1)
      const endDate = new Date(endYear, endMonth, 0) // Last day of month
      
      // Validate dates
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) return
      if (startDate > endDate) return
      
      emit('update:dateRange', {
        startDate,
        endDate
      })
    }

    function applyPreset(presetId) {
      activePreset.value = presetId
      const today = new Date()
      let startDate, endDate

      switch (presetId) {
        case 'all-time':
          emit('update:dateRange', { preset: 'all-time' })
          return

        case 'this-year':
          startDate = new Date(today.getFullYear(), 0, 1)
          endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0) // Last day of current month
          break

        case 'this-month':
          startDate = new Date(today.getFullYear(), today.getMonth(), 1)
          endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0) // Last day of current month
          break

        default:
          return
      }

      localStartMonth.value = formatMonthForInput(startDate)
      localEndMonth.value = formatMonthForInput(endDate)
      
      emit('update:dateRange', {
        startDate,
        endDate
      })
    }

    function isPresetActive(presetId) {
      return activePreset.value === presetId
    }

    return {
      localStartMonth,
      localEndMonth,
      presets,
      updateStartMonth,
      updateEndMonth,
      applyPreset,
      isPresetActive
    }
  }
}
</script>

<style scoped>
.date-range-picker {
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
  flex-wrap: wrap;
}

.preset-buttons {
  display: flex;
  gap: 0.5rem;
}

.preset-buttons .btn {
  margin: 0;
}

.custom-date-inputs {
  display: flex;
  gap: var(--gap-small);
  align-items: end;
}

.date-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.date-input-group label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text-light);
}

.date-separator {
  font-size: var(--text-large);
  color: var(--color-text-muted);
  padding-bottom: 0.25rem;
}

.filter-input {
  padding: 0.5rem;
  border: 0.0625rem solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-button);
  font-size: var(--text-small);
  transition: border-color 0.2s ease;
  font-family: "Livvic", sans-serif;
}

.filter-input:focus {
  outline: none;
  border-color: var(--color-button-active);
}

@media (max-width: 48rem) {
  .date-range-picker {
    flex-direction: column;
    align-items: stretch;
  }

  .custom-date-inputs {
    flex-direction: column;
  }

  .date-separator {
    display: none;
  }
}
</style>