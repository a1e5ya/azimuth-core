<template>
  <div class="timeline-chart-area">
    <div class="timeline-chart-wrapper">
      <!-- Zoom Controls - Top Right Corner -->
      <div class="zoom-controls">
        <button 
          class="btn btn-icon btn-small"
          :disabled="currentZoomLevel <= 0"
          @click="$emit('zoom-out')"
          title="Zoom Out"
        >
          <AppIcon name="zoom-out" size="small" />
        </button>
        
        <button 
          class="btn btn-icon btn-small"
          :disabled="currentZoomLevel >= 2"
          @click="$emit('zoom-in')"
          title="Zoom In"
        >
          <AppIcon name="zoom-in" size="small" />
        </button>
        
        <button 
          class="btn btn-icon btn-small"
          @click="$emit('reset-zoom')"
          title="Reset Zoom"
        >
          <AppIcon name="refresh" size="small" />
        </button>
      </div>
      
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <p>Loading timeline data...</p>
      </div>
      
      <div v-else-if="!hasData" class="empty-state">
        <p class="empty-title">No transaction data available</p>
        <p class="empty-subtitle">Import transactions to see your financial timeline</p>
      </div>
      
      <div v-else class="timeline-chart">
        <apexchart
          ref="mainChart"
          type="area"
          height="500"
          :options="chartOptions"
          :series="chartSeries"
        />
      </div>
    </div>

    <!-- Hover Info Field - Below Chart - ALWAYS VISIBLE -->
    <div class="hover-info-field" :class="{ 'hover-info-empty': !hoveredData }">
      <div v-if="!hoveredData" class="hover-info-placeholder">
        
      </div>
      
      <template v-else>
        <div class="hover-info-header">
          <h4>{{ formatDate(hoveredData.date) }}</h4>
          <button class="btn-icon btn-small" @click="$emit('unpin-hover-data')">
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
  </div>
</template>

<script>
import VueApexCharts from 'vue3-apexcharts'
import AppIcon from './AppIcon.vue'

export default {
  name: 'TimelineComponent',
  components: {
    apexchart: VueApexCharts,
    AppIcon
  },
  props: {
    loading: {
      type: Boolean,
      required: true
    },
    hasData: {
      type: Boolean,
      required: true
    },
    chartOptions: {
      type: Object,
      required: true
    },
    chartSeries: {
      type: Array,
      required: true
    },
    hoveredData: {
      type: Object,
      default: null
    },
    currentZoomLevel: {
      type: Number,
      required: true
    }
  },
  emits: ['zoom-in', 'zoom-out', 'reset-zoom', 'unpin-hover-data'],
  setup() {
    function formatDate(dateValue) {
      const date = typeof dateValue === 'number' ? new Date(dateValue) : 
                   typeof dateValue === 'string' ? new Date(dateValue) : dateValue
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    }
    
    function formatCurrency(amount) {
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }
    
    return {
      formatDate,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.timeline-chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.zoom-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--gap-small);
  border-radius: var(--radius);
}

.zoom-controls .btn-icon {
  background: transparent;
  border: none;
  padding: 0;
  margin: 0;
  width: 1.5rem;
  height: 1.5rem;
  box-shadow: none;
}

.timeline-chart-wrapper {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  min-height: 500px;
}

.timeline-chart {
  width: 100%;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--gap-large);
  color: var(--color-text-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}

.loading-spinner {
  font-size: 2rem;
  animation: spin 1s linear infinite;
  margin-bottom: var(--gap-standard);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-title {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.empty-subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-small);
}

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
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--color-background-dark);
}

.hover-info-header h4 {
  margin: 0;
  font-size: var(--text-medium);
  font-weight: 600;
}

.hover-info-header .btn-icon {
  width: 1.5rem;
  height: 1.5rem;
  padding: 0.25rem;
  background: transparent;
  box-shadow: none;
}

.hover-info-header .btn-icon:hover {
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
  margin-bottom: 0.5rem;
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
  margin-top: 0.5rem;
  padding-top: 0.5rem;
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

:deep(.apexcharts-toolbar) {
  z-index: 11;
}

:deep(.custom-icon-refresh) {
  cursor: pointer;
}

:deep(.custom-icon-refresh):hover {
  fill: var(--color-text);
}

:deep(.apexcharts-pan-icon) {
  display: none !important;
}

@media (max-width: 48rem) {
  .zoom-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .timeline-chart-wrapper {
    padding: var(--gap-small);
    min-height: 400px;
  }
  
  .loading-state,
  .empty-state {
    min-height: 400px;
  }
  
  .hover-info-field {
    padding: var(--gap-small);
  }
  
  .hover-info-row-split {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 30rem) {
  .hover-info-categories {
    font-size: 0.6875rem;
  }
}
</style>