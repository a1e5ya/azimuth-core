<template>
  <div class="type-summary">
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

    <div v-if="summary.categories && summary.categories.length > 0" class="card">
      <div class="category-grid">
        <button
          v-for="category in summary.categories"
          :key="category.id"
          class="category-card"
          @click="selectCategory(category)"
        >
          <div class="category-card-icon">
            <AppIcon :name="category.icon || 'circle'" size="large" />
          </div>
          <div class="category-card-content">
            <div class="category-card-name">{{ category.name }}</div>
            <div class="category-card-amount">{{ formatAmount(category.amount) }}</div>
            <div class="category-card-count">{{ category.count }} transactions</div>
          </div>
        </button>
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
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import { useCategoryStore } from '@/stores/categories'

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
    const categoryStore = useCategoryStore()
    
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
    
    function selectCategory(category) {
      const fullCategory = categoryStore.categories
        .flatMap(type => type.children)
        .find(cat => cat.id === category.id)
      
      if (fullCategory) {
        categoryStore.selectCategory(fullCategory)
      }
    }

    return {
      formatAmount,
      formatMonth,
      selectCategory
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

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr));
  gap: var(--gap-standard);
}

.category-card {
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

.category-card:hover {
  background: var(--color-background);
  transform: translateY(-0.125rem);
  box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
}

.category-card-icon {
  margin-bottom: var(--gap-small);
}

.category-card-content {
  width: 100%;
}

.category-card-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
  font-size: var(--text-small);
}

.category-card-amount {
  font-weight: 700;
  color: var(--color-text);
  font-size: var(--text-medium);
  margin-bottom: 0.25rem;
}

.category-card-count {
  font-size: var(--text-small);
  color: var(--color-text-muted);
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