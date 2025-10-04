<template>
  <div class="subcategory-details">
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

    <div class="card">
      <div class="transactions-header">
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading transactions...</div>
      </div>

      <div v-else-if="transactions.length === 0" class="empty-state">
        <div class="empty-title">No transactions</div>
      </div>

      <div v-else class="transactions-table-container">
        <table class="transactions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Merchant</th>
              <th>Amount</th>
              <th>Memo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in transactions" :key="transaction.id" class="transaction-row">
              <td>{{ formatDate(transaction.posted_at) }}</td>
              <td>{{ transaction.merchant || 'Unknown' }}</td>
              <td :class="getAmountClass(transaction)">
                {{ formatAmount(transaction.amount) }}
              </td>
              <td class="memo-cell">{{ truncate(transaction.memo, 50) }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="total > limit" class="pagination-section">
          <div class="pagination-info">
            Showing {{ ((page - 1) * limit) + 1 }} to {{ Math.min(page * limit, total) }} of {{ total }}
          </div>
          <div class="pagination-controls">
            <button class="btn btn-small" @click="changePage(page - 1)" :disabled="page <= 1">
              Previous
            </button>
            <span class="page-indicator">Page {{ page }}</span>
            <button class="btn btn-small" @click="changePage(page + 1)" :disabled="page * limit >= total">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'SubcategoryDetails',
  props: {
    summary: {
      type: Object,
      required: true
    },
    subcategoryId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const authStore = useAuthStore()
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    const transactions = ref([])
    const loading = ref(false)
    const page = ref(1)
    const limit = ref(50)
    const total = ref(0)

    async function loadTransactions() {
      loading.value = true

      try {
        const response = await axios.get(
          `${API_BASE}/categories/${props.subcategoryId}/transactions`,
          {
            params: { page: page.value, limit: limit.value },
            headers: { Authorization: `Bearer ${authStore.token}` }
          }
        )

        transactions.value = response.data.transactions || []
        total.value = response.data.total || 0

        console.log('✅ Loaded transactions:', transactions.value.length)
      } catch (error) {
        console.error('❌ Failed to load transactions:', error)
      } finally {
        loading.value = false
      }
    }

    function changePage(newPage) {
      if (newPage >= 1 && newPage * limit.value <= total.value + limit.value) {
        page.value = newPage
        loadTransactions()
      }
    }

    function formatAmount(amount) {
      if (!amount) return '€0.00'
      const num = parseFloat(amount)
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
      }).format(Math.abs(num))
    }

    function formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString('en-EU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    }

    function formatMonth(monthStr) {
      if (!monthStr) return ''
      const [year, month] = monthStr.split('-')
      const date = new Date(year, parseInt(month) - 1)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
    }

    function getAmountClass(transaction) {
      const amount = parseFloat(transaction.amount)
      if (transaction.transaction_type === 'income' || amount > 0) {
        return 'amount-positive'
      } else if (transaction.transaction_type === 'expense' || amount < 0) {
        return 'amount-negative'
      }
      return 'amount-neutral'
    }

    function truncate(text, maxLength) {
      if (!text || text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    watch(() => props.subcategoryId, () => {
      page.value = 1
      loadTransactions()
    })

    onMounted(() => {
      loadTransactions()
    })

    return {
      transactions,
      loading,
      page,
      limit,
      total,
      loadTransactions,
      changePage,
      formatAmount,
      formatDate,
      formatMonth,
      getAmountClass,
      truncate
    }
  }
}
</script>

<style scoped>
.subcategory-details {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
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

.transactions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
}

.transactions-header h3 {
  margin: 0;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--gap-large);
  color: var(--color-text-light);
}

.loading-spinner {
  font-size: var(--text-large);
  animation: spin 1s linear infinite;
  margin-bottom: var(--gap-small);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-title {
  font-size: var(--text-medium);
  font-weight: 600;
}

.transactions-table-container {
  overflow-x: auto;
  border-radius: var(--radius);
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-background);
  font-size: var(--text-small);
}

.transactions-table thead {
  background: var(--color-background-dark);
}

.transactions-table th {
  padding: var(--gap-small);
  text-align: left;
  font-weight: 600;
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.1);
}

.transactions-table td {
  padding: var(--gap-small);
  border-bottom: 0.0625rem solid rgba(0, 0, 0, 0.05);
}

.transaction-row:hover {
  background: var(--color-background-light);
}

.memo-cell {
  max-width: 20rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.amount-positive {
  color: green;
  font-weight: 600;
}

.amount-negative {
  color: red;
  font-weight: 600;
}

.amount-neutral {
  color: var(--color-text-light);
}

.pagination-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-standard);
  background: var(--color-background-light);
  border-radius: 0 0 var(--radius) var(--radius);
  margin-top: var(--gap-small);
}

.pagination-info {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.page-indicator {
  font-size: var(--text-small);
  color: var(--color-text-light);
}
</style>