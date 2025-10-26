<template>
  <div class="timeline-chart-wrapper">
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
        ref="chartRef"
        type="area"
        height="500"
        :options="chartOptions"
        :series="chartSeries"
      />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'TimelineChart',
  components: {
    apexchart: VueApexCharts
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
    }
  },
  setup() {
    const chartRef = ref(null)
    
    return {
      chartRef
    }
  }
}
</script>

<style scoped>
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
  .timeline-chart-wrapper {
    padding: var(--gap-small);
    min-height: 400px;
  }
  
  .loading-state,
  .empty-state {
    min-height: 400px;
  }
}
</style>