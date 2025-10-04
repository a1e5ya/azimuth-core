<template>
  <div class="type-summary">
    <div class="summary-header">
      <h2>{{ typeData.name }} Summary</h2>
    </div>

    <div class="summary-cards">
      <div class="card stat-card">
        <div class="stat-label">Total Transactions</div>
        <div class="stat-value">{{ summary.stats?.total_count || 0 }}</div>
      </div>

      <div class="card stat-card">
        <div class="stat-label">Total Amount</div>
        <div class="stat-value">{{ formatAmount(summary.stats?.total_amount) }}</div>
      </div>

      <div class="card stat-card">
        <div class="stat-label">Average per Transaction</div>
        <div class="stat-value">{{ formatAmount(summary.stats?.avg_amount) }}</div>
      </div>
    </div>

    <div class="card">
      <h3>Top Categories</h3>
      <div class="category-list">
        <div
          v-for="category in summary.categories || []"
          :key="category.id"
          class="category-item"
        >
          <div class="category-info">
            <AppIcon :name="category.icon" size="medium" />
            <span class="category-name">{{ category.name }}</span>
          </div>
          <div class="category-amount">
            {{ formatAmount(category.amount) }}
            <span class="transaction-count">({{ category.count }})</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="summary.monthly && summary.monthly.length > 0" class="card">
      <h3>Monthly Breakdown</h3>
      <div class="monthly-list">
        <div
          v-for="month in summary.monthly"
          :key="month.month"
          class="monthly-item"
        >
          <span class="month-label">{{ formatMonth(month.month) }}</span>
          <span class="month-amount">{{ formatAmount(month.amount) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AppIcon from './AppIcon.vue'

export default {
  name: 'CategoryTypeSummary',
  components: { AppIcon },
  props: {
    typeData: {
      type: Object,
      required: true
    },
    summary: {
      type: Object,
      required: true
    }
  },
  setup() {
    function formatAmount(amount) {
      if (!amount) return '€0.00'
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
      }).format(Math.abs(amount))
    }

    function formatMonth(monthStr) {
      if (!monthStr) return ''
      const [year, month] = monthStr.split('-')
      const date = new Date(year, parseInt(month) - 1)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
    }

    return {
      formatAmount,
      formatMonth
    }
  }
}
</script>

<style scoped>
.type-summary {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.summary-header h2 {
  margin: 0;
  font-size: var(--text-large);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: var(--gap-standard);
}

.stat-card {
  text-align: center;
  padding: var(--gap-standard);
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: var(--text-large);
  font-weight: 600;
  color: var(--color-text);
}

.card h3 {
  margin: 0 0 var(--gap-standard) 0;
  font-size: var(--text-medium);
  font-weight: 600;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.category-info {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.category-name {
  font-weight: 500;
}

.category-amount {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.transaction-count {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  font-weight: 400;
}

.monthly-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.monthly-item {
  display: flex;
  justify-content: space-between;
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.month-label {
  font-weight: 500;
}

.month-amount {
  font-weight: 600;
}
</style>