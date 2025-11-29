<!--
  TransactionsInfo Component - Transaction Statistics Display
  
  Displays key transaction metrics and statistics:
  - Total transaction count
  - Filtered results count
  - Total transaction volume (sum of amounts)
  - CSV upload progress indicator
  
  Features:
  - Real-time statistics display
  - Currency formatting (EUR)
  - Upload progress tracking with status indicators
  - Responsive grid layout
  - Loading states for ongoing uploads
  
  Props:
  - summary: Object - Overall transaction statistics
  - filteredStats: Object - Statistics for currently filtered view
  - uncategorizedCount: Number - Count of uncategorized transactions
  - uploads: Array - Active CSV upload progress items
  
  Upload Status Indicators:
  - ✓ Success - Upload completed
  - ✗ Error - Upload failed
  - ⟳ Loading - Upload in progress
-->

<template>
  <div class="transactions-info">
    <!-- Column 1: Transaction Counts -->
    <div class="info-column">
      <!-- Total transactions in database -->
      <div class="info-item">
        <span class="info-label">Total Transactions</span>
        <span class="info-value">{{ summary?.total_transactions?.toLocaleString() || 0 }}</span>
      </div>
      
      <!-- Current filtered result count -->
      <div class="info-item">
        <span class="info-label">Filtered Results</span>
        <span class="info-value">{{ filteredStats?.filtered_count?.toLocaleString() || 0 }}</span>
      </div>
    </div>

    <!-- Column 2: Financial Metrics -->
    <div class="info-column">
      <!-- Total volume of filtered transactions -->
      <div class="info-item">
        <span class="info-label">Total Volume</span>
        <span class="info-value">{{ formatCurrency(filteredStats?.total_amount) }}</span>
      </div>
    </div>

    <!-- CSV Upload Progress (appears when uploads active) -->
    <div class="upload-progress" v-if="uploads.length > 0">
      <div v-for="upload in uploads.slice(0, 1)" :key="upload.id" class="upload-item">
        <!-- Status icon -->
        <span v-if="upload.status === 'success'">✓</span>
        <span v-else-if="upload.status === 'error'">✗</span>
        <span v-else class="loading-spinner">⟳</span>
        
        <!-- File name -->
        <span class="upload-filename">{{ upload.filename }}</span>
        
        <!-- Row count on success -->
        <span v-if="upload.status === 'success'" class="upload-count">
          {{ upload.rows }} rows
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TransactionsInfo',
  props: {
    summary: {
      type: Object,
      default: null
    },
    filteredStats: {
      type: Object,
      default: null
    },
    uncategorizedCount: {
      type: Number,
      default: 0
    },
    uploads: {
      type: Array,
      default: () => []
    }
  },
  setup() {
    /**
     * Formats numeric amount as EUR currency
     * @param {number|null|undefined} amount - Amount to format
     * @returns {string} Formatted currency string
     */
    const formatCurrency = (amount) => {
      if (amount === null || amount === undefined) return '€0.00'
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
      }).format(amount)
    }

    return {
      formatCurrency
    }
  }
}
</script>

<style scoped>
.transactions-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  padding: 0;
}

.info-column {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
  padding: var(--gap-large);
  border-radius: var(--radius);
}

.info-item {
  display: flex;
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