<!--
  Dashboard Stat Cards - KPI summary with real-time calculations
  
  Four financial KPI cards: Spending, Income, Transfers, Net Savings.
  Aggregates from filtered transactions by main_category.
  
  Key Features:
  - Real-time calculation (computed from props)
  - Savings rate: (Net/Income) * 100
  - Dynamic net savings color (green profit, red loss)
  - Transaction counts per category
-->
<template>
  <div class="stats-overview">
    <div class="grid grid-4">
      <!-- Total Spending Card -->
      <div class="container stat-card card-expenses">
        <div class="stat-label">Total Spending</div>
        <div class="stat-value">{{ formatCurrency(kpis.totalSpending) }}</div>
        <div class="stat-detail">
          {{ kpis.expenseTransactionCount }} transactions
        </div>
      </div>

      <!-- Total Income Card -->
      <div class="container stat-card card-income">
        <div class="stat-label">Total Income</div>
        <div class="stat-value">{{ formatCurrency(kpis.totalIncome) }}</div>
        <div class="stat-detail">
          {{ kpis.incomeTransactionCount }} transactions
        </div>
      </div>

      <!-- Total Transfers Card -->
      <div class="container stat-card card-transfers">
        <div class="stat-label">Total Transfers</div>
        <div class="stat-value">{{ formatCurrency(kpis.totalTransfers) }}</div>
        <div class="stat-detail">
          {{ kpis.transferTransactionCount }} transfers
        </div>
      </div>

      <!-- Net Savings Card (dynamic color) -->
      <div 
        class="container stat-card"
        :style="{ backgroundColor: kpis.netSavings >= 0 ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)' }"
      >
        <div class="stat-label">Net Savings</div>
        <div class="stat-value">
          {{ formatCurrency(kpis.netSavings) }}
        </div>
        <div class="stat-detail">
          {{ kpis.savingsRate }}% savings rate
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'DashboardStatCards',
  props: {
    /**
     * Filtered transactions array
     * @type {Array}
     */
    filteredTransactions: {
      type: Array,
      required: true
    },
    /**
     * Function to get color for transaction type
     * @type {Function}
     * @param {string} type - Type identifier
     * @returns {string} Hex color
     */
    getTypeColor: {
      type: Function,
      required: true
    }
  },
  setup(props) {
    /**
     * Calculate KPIs from filtered transactions
     * Groups by main_category, sums amounts, counts transactions.
     * Net savings = income - expenses. Rate = (net/income) * 100.
     * 
     * @returns {Object} KPI metrics
     * @returns {number} totalSpending - Sum of EXPENSES
     * @returns {number} totalIncome - Sum of INCOME
     * @returns {number} totalTransfers - Sum of TRANSFERS
     * @returns {number} netSavings - Income minus expenses
     * @returns {number} savingsRate - Percentage saved (0-100)
     * @returns {number} expenseTransactionCount
     * @returns {number} incomeTransactionCount
     * @returns {number} transferTransactionCount
     */
    const kpis = computed(() => {
      if (props.filteredTransactions.length === 0) {
        return {
          totalSpending: 0,
          totalIncome: 0,
          totalTransfers: 0,
          netSavings: 0,
          savingsRate: 0,
          expenseTransactionCount: 0,
          incomeTransactionCount: 0,
          transferTransactionCount: 0
        }
      }

      let totalSpending = 0
      let totalIncome = 0
      let totalTransfers = 0
      let expenseTransactionCount = 0
      let incomeTransactionCount = 0
      let transferTransactionCount = 0

      props.filteredTransactions.forEach(tx => {
        const amount = Math.abs(parseFloat(tx.amount))
        const mainCategory = (tx.main_category || '').toUpperCase().trim()

        if (mainCategory === 'EXPENSES') {
          totalSpending += amount
          expenseTransactionCount++
        } else if (mainCategory === 'INCOME') {
          totalIncome += amount
          incomeTransactionCount++
        } else if (mainCategory === 'TRANSFERS') {
          totalTransfers += amount
          transferTransactionCount++
        }
      })

      const netSavings = totalIncome - totalSpending
      const savingsRate = totalIncome > 0 
        ? Math.round((netSavings / totalIncome) * 100) 
        : 0

      return {
        totalSpending,
        totalIncome,
        totalTransfers,
        netSavings,
        savingsRate,
        expenseTransactionCount,
        incomeTransactionCount,
        transferTransactionCount
      }
    })

    /**
     * Convert hex to rgba (unused, available for future use)
     * 
     * @param {string} hex - Hex color (#RRGGBB)
     * @param {number} alpha - Opacity 0-1
     * @returns {string} RGBA color string
     */
    function hexToRgba(hex, alpha) {
      if (!hex) return 'transparent'
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    /**
     * Format as EUR currency, no decimals, absolute value
     * 
     * @param {number} amount - Amount to format
     * @returns {string} Formatted currency (e.g. "€1,234")
     */
    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }

    return {
      kpis,
      hexToRgba,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.stats-overview {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stat-card {
  text-align: center;
  padding: var(--gap-large);
  border-radius: var(--radius);
  height: 145px;
  width: 12rem;
  box-shadow: none;
}

.card-expenses {
  background-color: rgba(197, 145, 232, 0.5);
}

.card-income {
  background-color: rgba(24, 234, 184, 0.5);
} 

.card-transfers {
  background-color: rgba(240, 196, 108, 0.5);
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  margin-bottom: var(--gap-small);
}

.stat-value {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: var(--gap-small);
  color: var(--color-text);
}

.stat-detail {
  font-size: var(--text-small);
  color: var(--color-text-light);
}
</style>