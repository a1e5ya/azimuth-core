<template>
  <div class="timeline-filter-bar container">
    <!-- Breakdown Mode Toggle -->
    <div class="filter-section">
      <label class="filter-label">View by:</label>
      <div class="breakdown-toggle">
        <button
          class="toggle-option"
          :class="{ active: breakdownMode === 'all' }"
          @click="$emit('update:breakdownMode', 'all')"
        >
          All
        </button>
        <button
          class="toggle-option"
          :class="{ active: breakdownMode === 'owner' }"
          @click="$emit('update:breakdownMode', 'owner')"
        >
          By Owner
        </button>
        <button
          class="toggle-option"
          :class="{ active: breakdownMode === 'account' }"
          @click="$emit('update:breakdownMode', 'account')"
        >
          By Account
        </button>
      </div>
    </div>

    <!-- Owner Selection (shown when breakdownMode === 'owner') -->
    <div v-if="breakdownMode === 'owner'" class="filter-section">
      <label class="filter-label">Owners:</label>
      <div class="multiselect-group">
        <button
          v-for="owner in availableOwners"
          :key="owner"
          class="multiselect-item"
          :class="{ active: selectedOwners.includes(owner) }"
          @click="toggleOwner(owner)"
        >
          {{ owner }}
        </button>
      </div>
    </div>

    <!-- Account Selection (shown when breakdownMode === 'account') -->
    <div v-if="breakdownMode === 'account'" class="filter-section">
      <label class="filter-label">Accounts:</label>
      <div class="multiselect-group">
        <button
          v-for="account in availableAccounts"
          :key="account"
          class="multiselect-item"
          :class="{ active: selectedAccounts.includes(account) }"
          @click="toggleAccount(account)"
        >
          {{ account }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'TimelineFilterBar',
  props: {
    breakdownMode: {
      type: String,
      required: true
    },
    selectedOwners: {
      type: Array,
      required: true
    },
    selectedAccounts: {
      type: Array,
      required: true
    },
    transactions: {
      type: Array,
      required: true
    }
  },
  emits: ['update:breakdownMode', 'update:selectedOwners', 'update:selectedAccounts'],
  setup(props, { emit }) {
    // Extract unique owners from transactions
    const availableOwners = computed(() => {
      const owners = new Set()
      props.transactions.forEach(t => {
        if (t.owner) owners.add(t.owner)
      })
      return Array.from(owners).sort()
    })

    // Extract unique account combinations (Owner_AccountType)
    const availableAccounts = computed(() => {
      const accounts = new Set()
      props.transactions.forEach(t => {
        if (t.owner && t.bank_account_type) {
          accounts.add(`${t.owner}_${t.bank_account_type}`)
        }
      })
      return Array.from(accounts).sort()
    })

    function toggleOwner(owner) {
      const current = [...props.selectedOwners]
      const index = current.indexOf(owner)
      
      if (index > -1) {
        // Don't allow deselecting if it's the last one
        if (current.length > 1) {
          current.splice(index, 1)
        }
      } else {
        current.push(owner)
      }
      
      emit('update:selectedOwners', current)
    }

    function toggleAccount(account) {
      const current = [...props.selectedAccounts]
      const index = current.indexOf(account)
      
      if (index > -1) {
        // Don't allow deselecting if it's the last one
        if (current.length > 1) {
          current.splice(index, 1)
        }
      } else {
        current.push(account)
      }
      
      emit('update:selectedAccounts', current)
    }

    return {
      availableOwners,
      availableAccounts,
      toggleOwner,
      toggleAccount
    }
  }
}
</script>

<style scoped>
.timeline-filter-bar {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
  padding: var(--gap-standard);
  background: var(--color-background);
  border-radius: var(--radius);
  margin-bottom: var(--gap-standard);
}

.filter-section {
  display: flex;
  align-items: center;
  gap: var(--gap-standard);
}

.filter-label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text-light);
  min-width: 5rem;
}

.breakdown-toggle {
  display: flex;
  gap: 0.25rem;
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: 0.25rem;
}

.toggle-option {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: calc(var(--radius) - 0.125rem);
  cursor: pointer;
  font-size: var(--text-small);
  color: var(--color-text-light);
  transition: all 0.2s;
}

.toggle-option:hover {
  background: var(--color-background-dark);
  color: var(--color-text);
}

.toggle-option.active {
  background: var(--color-background);
  color: var(--color-text);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.multiselect-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.multiselect-item {
  padding: 0.5rem 1rem;
  background: var(--color-background-light);
  border: 2px solid var(--color-background-dark);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: var(--text-small);
  color: var(--color-text-light);
  transition: all 0.2s;
}

.multiselect-item:hover {
  background: var(--color-background-dark);
  color: var(--color-text);
  border-color: var(--color-text-light);
}

.multiselect-item.active {
  background: var(--color-button-active);
  color: white;
  border-color: var(--color-button-active);
  font-weight: 600;
}
</style>