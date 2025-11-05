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
</style>