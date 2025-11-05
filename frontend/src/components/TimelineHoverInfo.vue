<template>
  <div class="hover-info-field" :class="{ 'hover-info-empty': !hoveredData }">
    <div v-if="!hoveredData" class="hover-info-placeholder">
      
    </div>
    
    <template v-else>
      <div class="hover-info-header">
        <h4>{{ formatDate(hoveredData.date) }}</h4>
        <button class="btn btn-icon hover-close-btn" @click="$emit('unpin')">
          <AppIcon name="times" size="small" />
        </button>
      </div>
      
      <div class="hover-info-content">
        <!-- Row 1: Income and Transfers (side by side) -->
        <div class="hover-info-row-split">
          <!-- Income Section -->
          <div class="hover-info-section" v-if="hoveredData.income > 0">
            <div class="hover-info-label positive">Income</div>
            <div class="hover-info-value">{{ formatCurrency(hoveredData.income) }}</div>
            
            <div class="hover-info-categories" v-if="hoveredData.incomeByCategory">
              <div 
                class="hover-info-category" 
                v-for="(amount, category) in hoveredData.incomeByCategory" 
                :key="category"
                v-show="amount > 0"
              >
                <span class="hover-category-name">{{ category }}</span>
                <span class="hover-category-amount">{{ formatCurrency(amount) }}</span>
              </div>
            </div>
          </div>

          <!-- Transfers Section -->
          <div class="hover-info-section" v-if="hoveredData.transfers > 0">
            <div class="hover-info-label neutral">Transfers</div>
            <div class="hover-info-value">{{ formatCurrency(hoveredData.transfers) }}</div>
            
            <div class="hover-info-categories" v-if="hoveredData.transfersByCategory">
              <div 
                class="hover-info-category" 
                v-for="(amount, category) in hoveredData.transfersByCategory" 
                :key="category"
                v-show="amount > 0"
              >
                <span class="hover-category-name">{{ category }}</span>
                <span class="hover-category-amount">{{ formatCurrency(amount) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Row 2: Expenses (full width) -->
        <div class="hover-info-section hover-info-expenses" v-if="hoveredData.expenses > 0">
          <div class="hover-info-label negative">Expenses</div>
          <div class="hover-info-value">{{ formatCurrency(hoveredData.expenses) }}</div>
          
          <div class="hover-info-categories" v-if="hoveredData.expensesByCategory">
            <div 
              class="hover-info-category" 
              v-for="(amount, category) in hoveredData.expensesByCategory" 
              :key="category"
              v-show="amount > 0"
            >
              <span class="hover-category-name">{{ category }}</span>
              <span class="hover-category-amount">{{ formatCurrency(amount) }}</span>
            </div>
          </div>
        </div>

        <!-- Row 3: Balance Change (full width) -->
        <div class="hover-info-section hover-info-total" v-if="hoveredData.balance !== undefined">
          <div class="hover-info-label">Balance Change</div>
          <div class="hover-info-value" :class="hoveredData.balance >= 0 ? 'positive' : 'negative'">
            {{ formatCurrency(hoveredData.balance) }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import AppIcon from './AppIcon.vue'
import { formatDate, formatCurrency } from '@/utils/timelineHelpers'

export default {
  name: 'TimelineHoverInfo',
  components: {
    AppIcon
  },
  props: {
    hoveredData: {
      type: Object,
      default: null
    }
  },
  emits: ['unpin'],
  setup() {
    return {
      formatDate,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.hover-info-field {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  border: 2px solid var(--color-background-dark);
  min-height: 8rem;
}

.hover-info-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.hover-info-placeholder {
  text-align: center;
  color: var(--color-text-muted);
  font-style: italic;
}

.hover-info-placeholder p {
  margin: 0;
}

.hover-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  padding-bottom: var(--gap-small);
  border-bottom: 2px solid var(--color-background-dark);
}

.hover-info-header h4 {
  margin: 0;
  font-size: var(--text-medium);
  font-weight: 600;
}

.hover-close-btn {
  width: 1.5rem;
  height: 1.5rem;
  padding: 0.25rem;
  background: transparent;
  box-shadow: none;
  margin: 0;
}

.hover-close-btn:hover {
  background: var(--color-background-dark);
}

.hover-info-content {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.hover-info-row-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-standard);
}

.hover-info-section {
  padding: 0.75rem;
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.hover-info-expenses,
.hover-info-total {
  grid-column: 1 / -1;
}

.hover-info-total {
  background: var(--color-background-dark);
}

.hover-info-label {
  font-size: var(--text-small);
  font-weight: 600;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.hover-info-label.positive {
  color: #22c55e;
}

.hover-info-label.negative {
  color: #ef4444;
}

.hover-info-label.neutral {
  color: #3b82f6;
}

.hover-info-value {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: var(--gap-small);
}

.hover-info-value.positive {
  color: #22c55e;
}

.hover-info-value.negative {
  color: #ef4444;
}

.hover-info-categories {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: var(--gap-small);
  padding-top: var(--gap-small);
  border-top: 1px solid var(--color-background-dark);
}

.hover-info-category {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-small);
  padding: 0.25rem 0;
}

.hover-category-name {
  color: var(--color-text-light);
}

.hover-category-amount {
  font-weight: 500;
  color: var(--color-text);
}
</style>