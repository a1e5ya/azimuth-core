<template>
  <div class="container">
    <h3 style="margin-bottom: var(--gap-standard);">Accounts Overview</h3>
    
    <div v-if="accountStats.length === 0" class="empty-state-small">
      No account data
    </div>
    
    <div v-else class="accounts-list">
      <div 
        v-for="account in accountStats" 
        :key="account.key" 
        class="account-card-compact"
      >
        <div class="account-header-compact">
          <div class="account-title-compact">
            <AppIcon name="credit-card" size="small" />
            <div>
              <div class="account-owner-compact">{{ account.owner || 'Unknown' }}</div>
              <div class="account-type-compact">{{ account.accountType || 'Unknown Type' }}</div>
            </div>
          </div>
        </div>
        <div class="account-stats-compact">
          <div class="account-stat-compact">
            <span class="account-stat-label-compact">Income:</span>
            <span class="account-stat-value-compact positive">{{ formatCurrency(account.income) }}</span>
          </div>
          <div class="account-stat-compact">
            <span class="account-stat-label-compact">Expenses:</span>
            <span class="account-stat-value-compact negative">{{ formatCurrency(account.expenses) }}</span>
          </div>
          <div class="account-stat-compact">
            <span class="account-stat-label-compact">Transfers:</span>
            <span class="account-stat-value-compact neutral">{{ formatCurrency(account.transfers) }}</span>
          </div>
          <div class="account-stat-compact account-stat-total-compact">
            <span class="account-stat-label-compact">Net:</span>
            <span 
              class="account-stat-value-compact" 
              :class="account.net >= 0 ? 'positive' : 'negative'"
            >
              {{ formatCurrency(account.net) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

export default {
  name: 'DashboardAccountsOverview',
  components: {
    AppIcon
  },
  props: {
    filteredTransactions: {
      type: Array,
      required: true
    }
  },
  setup(props) {
    const accountStats = computed(() => {
      if (props.filteredTransactions.length === 0) return []

      const accountMap = new Map()

      props.filteredTransactions.forEach(tx => {
        const owner = tx.owner || 'Unknown'
        const accountType = tx.bank_account_type || 'Unknown Type'
        const key = `${owner}|${accountType}`

        if (!accountMap.has(key)) {
          accountMap.set(key, {
            key,
            owner,
            accountType,
            income: 0,
            expenses: 0,
            transfers: 0,
            net: 0
          })
        }

        const account = accountMap.get(key)
        const amount = Math.abs(parseFloat(tx.amount))
        const mainCategory = (tx.main_category || '').toUpperCase().trim()

        if (mainCategory === 'INCOME') {
          account.income += amount
        } else if (mainCategory === 'EXPENSES') {
          account.expenses += amount
        } else if (mainCategory === 'TRANSFERS') {
          account.transfers += amount
        }
      })

      const accounts = Array.from(accountMap.values())
      accounts.forEach(account => {
        account.net = account.income - account.expenses
      })

      return accounts.sort((a, b) => b.net - a.net)
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
      accountStats,
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

.accounts-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.account-card-compact {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-small);
}

.account-header-compact {
  margin-bottom: var(--gap-small);
  padding-bottom: var(--gap-small);
  border-bottom: 1px solid var(--color-background-dark);
}

.account-title-compact {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.account-owner-compact {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.account-type-compact {
  font-size: 0.6875rem;
  color: var(--color-text-muted);
}

.account-stats-compact {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.account-stat-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.75rem;
}

.account-stat-total-compact {
  padding-top: 0.375rem;
  border-top: 1px solid var(--color-background-dark);
  font-weight: 600;
  margin-top: 0.25rem;
}

.account-stat-label-compact {
  color: var(--color-text-light);
}

.account-stat-value-compact {
  font-weight: 600;
  font-size: 0.75rem;
}

.account-stat-value-compact.positive {
  color: #22c55e;
}

.account-stat-value-compact.negative {
  color: #ef4444;
}

.account-stat-value-compact.neutral {
  color: #3b82f6;
}

@media (max-width: 48rem) {
  .account-card-compact {
    padding: var(--gap-small);
  }
}

@media (max-width: 30rem) {
  .account-owner-compact {
    font-size: 0.6875rem;
  }
  
  .account-type-compact {
    font-size: 0.625rem;
  }
  
  .account-stat-compact {
    font-size: 0.6875rem;
  }
}
</style>