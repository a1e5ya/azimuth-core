<template>
  <div class="transactions-info">
    <!-- Column 1 -->
    <div class="info-column">
      <div class="info-item">
        <span class="info-label">Total Transactions</span>
        <span class="info-value">{{ summary?.total_transactions?.toLocaleString() || 0 }}</span>
      </div>
      

      
      <div class="info-item">
        <span class="info-label">Filtered Results</span>
        <span class="info-value">{{ displayFilteredCount?.toLocaleString() || 0 }}</span>
      </div>
      
    </div>

    <!-- Column 2 -->
    <div class="info-column">

      <div class="info-item">
        <span class="info-label">Categorized</span>
        <span class="info-value">{{ summary?.categorized_count?.toLocaleString() || 0 }}</span>
      </div>

            <div class="info-item">
        <span class="info-label">Uncategorized</span>
        <span class="info-value">{{ uncategorizedCount?.toLocaleString() || 0 }}</span>
      </div>


    </div>

    <!-- Upload Progress -->
    <div class="upload-progress" v-if="uploads.length > 0">
      <div v-for="upload in uploads.slice(0, 1)" :key="upload.id" class="upload-item">
        <span v-if="upload.status === 'success'">✓</span>
        <span v-else-if="upload.status === 'error'">✗</span>
        <span v-else class="loading-spinner">⟳</span>
        <span class="upload-filename">{{ upload.filename }}</span>
        <span v-if="upload.status === 'success'" class="upload-count">
          {{ upload.rows }} rows
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'TransactionsInfo',
  props: {
    summary: {
      type: Object,
      default: null
    },
    filteredCount: {
      type: Number,
      default: 0
    },
    hasActiveFilters: {
      type: Boolean,
      default: false
    },
    uploads: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const displayFilteredCount = computed(() => {
      return props.filteredCount || props.summary?.total_transactions || 0
    })

    const uncategorizedCount = computed(() => {
      if (!props.summary?.total_transactions || !props.summary?.categorized_count) return 0
      return props.summary.total_transactions - props.summary.categorized_count
    })

    const filteredPercentageLabel = computed(() => {
      return props.hasActiveFilters ? '% coverage' : ''
    })

    const filteredPercentage = computed(() => {
      const total = props.summary?.total_transactions
      const categorized = props.summary?.categorized_count
      if (!total || !categorized) return ''
      const percentage = (categorized / total) * 100
      return `${Math.round(percentage)}%`
    })

    const percentOfTotalLabel = computed(() => {
      return props.hasActiveFilters ? '% of total' : ''
    })

    const percentOfTotal = computed(() => {
      const total = props.summary?.total_transactions
      const filtered = displayFilteredCount.value
      if (!total || !filtered || !props.hasActiveFilters) return ''
      const percentage = (filtered / total) * 100
      return `${Math.round(percentage)}%`
    })

    const uncategorizedPercentageLabel = computed(() => {
      return props.hasActiveFilters ? '% of total' : ''
    })

    const uncategorizedPercentage = computed(() => {
      const total = props.summary?.total_transactions
      const uncat = uncategorizedCount.value
      if (!total || !uncat || !props.hasActiveFilters) return ''
      const percentage = (uncat / total) * 100
      return `${Math.round(percentage)}%`
    })

    const formatCurrency = (amount) => {
      if (amount === null || amount === undefined) return '€0.00'
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
      }).format(amount)
    }

    return {
      displayFilteredCount,
      uncategorizedCount,
      filteredPercentageLabel,
      filteredPercentage,
      percentOfTotalLabel,
      percentOfTotal,
      uncategorizedPercentageLabel,
      uncategorizedPercentage,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.transactions-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6rem;
  padding: 0;
}

.info-column {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
  background-color: var(--color-background-light);
  padding: var(--gap-large);
  border-radius: var(--radius);
}

.info-item {
display: flex
;
    flex-direction: row;
    gap: 1rem;
    justify-content: space-between;
}

.info-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  font-weight: 400;
  min-height: 1rem;
}

.info-value {
  font-size: var(--text-medium);
  font-weight: 600;
  color: var(--color-text);
}

.upload-progress {
  grid-column: 1 / -1;
  display: flex;
  gap: var(--gap-small);
  padding-top: var(--gap-small);
}

.upload-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: var(--text-small);
  background-color: transparent;
  padding: 0;
}

.loading-spinner {
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-filename {
  max-width: 10rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-count {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}
</style>