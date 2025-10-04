<template>
  <div class="category-detail-summary">
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

    <div v-if="summary.subcategories && summary.subcategories.length > 0" class="card">
      <div class="subcategory-grid">
        <button
          v-for="subcategory in summary.subcategories"
          :key="subcategory.id"
          class="subcategory-card"
          @click="$emit('select-subcategory', subcategory)"
        >
          <div class="subcategory-card-icon">
            <AppIcon :name="subcategory.icon || 'circle'" size="large" />
          </div>
          <div class="subcategory-card-content">
            <div class="subcategory-card-name">{{ subcategory.name }}</div>
            <div class="subcategory-card-amount">{{ formatAmount(subcategory.amount) }}</div>
            <div class="subcategory-card-count">{{ subcategory.count }} transactions</div>
          </div>
        </button>
      </div>
    </div>

    <div v-if="summary.top_merchants && summary.top_merchants.length > 0" class="card">
      <h3>Top Merchants</h3>
      <div class="merchant-list">
        <div
          v-for="merchant in summary.top_merchants"
          :key="merchant.name"
          class="merchant-item"
        >
          <span class="merchant-name">{{ merchant.name }}</span>
          <div class="merchant-amount">
            {{ formatAmount(merchant.amount) }}
            <span class="transaction-count">({{ merchant.count }})</span>
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
  name: 'CategoryDetailSummary',
  components: { AppIcon },
  props: {
    summary: {
      type: Object,
      required: true
    }
  },
  emits: ['select-subcategory'],
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
.category-detail-summary {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-title {
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
}

.category-title h2 {
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

.subcategory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr));
  gap: var(--gap-standard);
}

.subcategory-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--gap-standard);
  background: var(--color-background-light);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.subcategory-card:hover {
  background: var(--color-background);
  transform: translateY(-0.125rem);
  box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
}

.subcategory-card-icon {
  margin-bottom: var(--gap-small);
}

.subcategory-card-content {
  width: 100%;
}

.subcategory-card-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
  font-size: var(--text-small);
}

.subcategory-card-amount {
  font-weight: 700;
  color: var(--color-text);
  font-size: var(--text-medium);
  margin-bottom: 0.25rem;
}

.subcategory-card-count {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.merchant-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.merchant-item {
  display: flex;
  justify-content: space-between;
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.merchant-name {
  font-weight: 500;
}

.merchant-amount {
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