<template>
  <div class="container">
    <h3 style="margin-bottom: var(--gap-standard);">Top Spending Categories</h3>
    
    <div v-if="topCategories.length === 0" class="empty-state-small">
      No category data
    </div>
    
    <div v-else class="category-list">
      <div v-for="(cat, index) in topCategories" :key="index" class="category-item">
        <div class="category-rank">{{ index + 1 }}</div>
        <div class="category-info">
          <div class="category-name">{{ cat.name }}</div>
          <div class="category-amount">{{ formatCurrency(cat.amount) }}</div>
        </div>
        <div class="category-bar-container">
          <div class="category-bar" :style="{ width: cat.percentage + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'DashboardTopCategories',
  props: {
    filteredTransactions: {
      type: Array,
      required: true
    }
  },
  setup(props) {
    const topCategories = computed(() => {
      if (props.filteredTransactions.length === 0) return []

      const categoryTotals = {}
      let maxAmount = 0

      props.filteredTransactions.forEach(tx => {
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        if (mainCategory !== 'EXPENSES') return

        const category = tx.category || 'Uncategorized'
        const amount = Math.abs(parseFloat(tx.amount))

        categoryTotals[category] = (categoryTotals[category] || 0) + amount
        maxAmount = Math.max(maxAmount, categoryTotals[category])
      })

      return Object.entries(categoryTotals)
        .map(([name, amount]) => ({
          name,
          amount,
          percentage: maxAmount > 0 ? (amount / maxAmount) * 100 : 0
        }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 5)
    })

    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }

    return {
      topCategories,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.empty-state-small {
  text-align: center;
  padding: var(--gap-standard);
  color: var(--color-text-muted);
  font-size: var(--text-small);
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.category-item {
  display: grid;
  grid-template-columns: 2rem 1fr;
  gap: var(--gap-small);
  align-items: center;
}

.category-rank {
  width: 2rem;
  height: 2rem;
  background: var(--color-background-dark);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--text-small);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.category-name {
  font-weight: 500;
  font-size: var(--text-small);
}

.category-amount {
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--text-small);
}

.category-bar-container {
  grid-column: 2;
  height: 0.5rem;
  background: var(--color-background-dark);
  border-radius: 0.25rem;
  overflow: hidden;
}

.category-bar {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #dc2626);
  border-radius: 0.25rem;
  transition: width 0.3s ease;
}
</style>