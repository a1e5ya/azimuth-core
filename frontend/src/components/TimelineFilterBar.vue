<!--
  TimelineFilterBar Component - Data Breakdown Filters
  
  Provides filtering options for timeline data:
  - Breakdown mode selection (All, Owner, Account)
  - Multi-select owner filtering
  - Multi-select account filtering
  - Automatic data extraction from transactions
  
  Features:
  - Three view modes: All, Owner, Account
  - Dynamic owner list from transaction data
  - Dynamic account list (Owner_AccountType format)
  - Multi-select with active state indicators
  - Prevents deselecting last item (at least one must be selected)
  - Auto-sorted lists
  
  Props:
  - breakdownMode: String - Current mode ('all', 'owner', 'account')
  - selectedOwners: Array - Currently selected owners
  - selectedAccounts: Array - Currently selected accounts
  - transactions: Array - All transaction data for extraction
  
  Events:
  - @update:breakdownMode: Emitted when mode changes
  - @update:selectedOwners: Emitted when owner selection changes
  - @update:selectedAccounts: Emitted when account selection changes
  
  Breakdown Modes:
  - All: Show all transactions combined
  - Owner: Filter by transaction owners
  - Account: Filter by owner + account type combinations
-->

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
          Owner
        </button>
        <button
          class="toggle-option"
          :class="{ active: breakdownMode === 'account' }"
          @click="$emit('update:breakdownMode', 'account')"
        >
          Account
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
    /**
     * Extracts unique owners from transactions
     * @type {import('vue').ComputedRef<string[]>}
     */
    const availableOwners = computed(() => {
      const owners = new Set()
      props.transactions.forEach(t => {
        if (t.owner) owners.add(t.owner)
      })
      return Array.from(owners).sort()
    })

    /**
     * Extracts unique account combinations (Owner_AccountType)
     * @type {import('vue').ComputedRef<string[]>}
     */
    const availableAccounts = computed(() => {
      const accounts = new Set()
      props.transactions.forEach(t => {
        if (t.owner && t.bank_account_type) {
          accounts.add(`${t.owner}_${t.bank_account_type}`)
        }
      })
      return Array.from(accounts).sort()
    })

    /**
     * Toggles owner selection (prevents deselecting last item)
     * @param {string} owner - Owner name to toggle
     * @returns {void}
     */
    function toggleOwner(owner) {
      const current = [...props.selectedOwners]
      const index = current.indexOf(owner)
      
      if (index > -1) {
        if (current.length > 1) {
          current.splice(index, 1)
        }
      } else {
        current.push(owner)
      }
      
      emit('update:selectedOwners', current)
    }

    /**
     * Toggles account selection (prevents deselecting last item)
     * @param {string} account - Account identifier (Owner_AccountType)
     * @returns {void}
     */
    function toggleAccount(account) {
      const current = [...props.selectedAccounts]
      const index = current.indexOf(account)
      
      if (index > -1) {
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
  align-items: flex-start;
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
  position: relative;
  display: flex;

  background: var(--color-background-dark);
  border-radius: var(--radius);
  gap: var(--gap-standard);
}

.toggle-option {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 4rem;
  height: 1.75rem;
  background: transparent;
  border: none;
  padding: 1.125rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-light);
  box-shadow: var(--shadow);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  opacity: 0.8;
  z-index: 1;
}

.toggle-option.active {
background-color: var(--color-background-light);
  opacity: 1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
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