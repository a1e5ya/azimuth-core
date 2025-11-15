<template>
  <div class="container">


    <!-- Empty State with Drop Zone -->
    <div v-if="chartData.length === 0" class="empty-state-import">
      <div class="file-drop-zone" 
           @drop.prevent="handleDrop" 
           @dragover.prevent
           @click="triggerFileInput">
        <AppIcon name="file-add" size="large" />
        <p>Drop training data here or click to browse</p>
        <p class="help-text">CSV/XLSX files supported</p>
      </div>
      <input 
        ref="fileInput" 
        type="file" 
        accept=".csv,.xlsx"
        multiple
        @change="handleFileSelect"
        style="display: none"
      >
    </div>

    <div v-else class="chart-container">
          <div class="chart-header">
      <h3>Income vs Expenses Trend</h3>
    </div>
      <apexchart
        type="area"
        height="300"
        :options="chartOptions"
        :series="chartSeries"
      />
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import AppIcon from './AppIcon.vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'DashboardIncomeExpensesChart',
  components: {
    apexchart: VueApexCharts,
    AppIcon
  },
  props: {
    filteredTransactions: {
      type: Array,
      required: true
    },
    getTypeColor: {
      type: Function,
      required: true
    }
  },
  emits: ['import-complete'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    const fileInput = ref(null)

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      processFiles(files)
      event.target.value = ''
    }

    const handleDrop = (event) => {
      const files = Array.from(event.dataTransfer.files)
      const validFiles = files.filter(f => 
        f.name.toLowerCase().endsWith('.csv') || 
        f.name.toLowerCase().endsWith('.xlsx')
      )
      processFiles(validFiles)
    }

    const processFiles = async (files) => {
      if (!files || files.length === 0) return

      for (const file of files) {
        try {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('import_mode', 'training')
          formData.append('auto_categorize', 'true')

          await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000
          })

          console.log(`✅ Imported: ${file.name}`)
        } catch (error) {
          console.error(`❌ Import failed: ${file.name}`, error)
        }
      }

      emit('import-complete', { success: true, fileCount: files.length })
    }

    const chartData = computed(() => {
      if (props.filteredTransactions.length === 0) return []

      const monthlyData = {}

      props.filteredTransactions.forEach(tx => {
        const mainCategory = (tx.main_category || '').toUpperCase().trim()
        if (mainCategory === 'TRANSFERS') return

        const date = new Date(tx.posted_at)
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

        if (!monthlyData[monthKey]) {
          monthlyData[monthKey] = {
            period: monthKey,
            spending: 0,
            income: 0
          }
        }

        const amount = Math.abs(parseFloat(tx.amount))

        if (mainCategory === 'EXPENSES') {
          monthlyData[monthKey].spending += amount
        } else if (mainCategory === 'INCOME') {
          monthlyData[monthKey].income += amount
        }
      })

      return Object.values(monthlyData)
        .sort((a, b) => a.period.localeCompare(b.period))
    })

    const chartSeries = computed(() => {
      if (chartData.value.length === 0) return []

      return [
        {
          name: 'Income',
          data: chartData.value.map(d => ({
            x: new Date(d.period + '-01').getTime(),
            y: d.income
          }))
        },
        {
          name: 'Expenses',
          data: chartData.value.map(d => ({
            x: new Date(d.period + '-01').getTime(),
            y: d.spending
          }))
        }
      ]
    })

    const chartOptions = computed(() => ({
      chart: {
        type: 'area',
        height: 300,
        stacked: false,
        toolbar: {
          show: false
        },
        zoom: {
          enabled: false
        },
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800
        }
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth',
        width: 2
      },
      fill: {
        type: 'gradient',
        gradient: {
          opacityFrom: 0.4,
          opacityTo: 0.1,
          stops: [0, 90, 100]
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'left',
        fontSize: '14px',
        fontWeight: 500
      },
      grid: {
        borderColor: '#e5e7eb',
        strokeDashArray: 4,
        xaxis: {
          lines: {
            show: true
          }
        },
        yaxis: {
          lines: {
            show: true
          }
        }
      },
      xaxis: {
        type: 'datetime',
        labels: {
          format: 'MMM yyyy',
          style: {
            colors: '#6b7280',
            fontSize: '12px'
          }
        },
        axisBorder: {
          show: true,
          color: '#e5e7eb'
        },
        axisTicks: {
          show: true,
          color: '#e5e7eb'
        }
      },
      yaxis: {
        title: {
          text: 'Amount (€)',
          style: {
            color: '#6b7280',
            fontSize: '12px',
            fontWeight: 500
          }
        },
        labels: {
          formatter: (val) => '€' + Math.round(val).toLocaleString(),
          style: {
            colors: '#6b7280',
            fontSize: '12px'
          }
        }
      },
      tooltip: {
        shared: true,
        intersect: false,
        x: {
          format: 'MMM yyyy'
        },
        y: {
          formatter: (val) => '€' + val.toFixed(2)
        },
        theme: 'light'
      },
      colors: [props.getTypeColor('income'), props.getTypeColor('expenses')],
      markers: {
        size: 0,
        hover: {
          size: 5
        }
      }
    }))

    return {
      fileInput,
      chartData,
      chartSeries,
      chartOptions,
      triggerFileInput,
      handleFileSelect,
      handleDrop
    }
  }
}
</script>

<style scoped>
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  flex-wrap: wrap;
  gap: var(--gap-small);
}

.chart-header h3 {
  margin: 0;
}

.chart-container {
  padding: var(--gap-small);
}

.empty-state-import {
  padding: var(--gap-large);
}

.file-drop-zone {
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  padding: var(--gap-xxl);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-background-light);
}

.file-drop-zone:hover {
  border-color: var(--color-button-active);
  background: rgba(0, 0, 0, 0.02);
}

.file-drop-zone p {
  margin: var(--gap-small) 0;
}

.help-text {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

:deep(.apexcharts-tooltip) {
  background: var(--color-background-light) !important;
  border: 1px solid var(--color-background-dark) !important;
  box-shadow: var(--shadow) !important;
}

:deep(.apexcharts-tooltip-title) {
  background: var(--color-background-dark) !important;
  border-bottom: 1px solid var(--color-background-dark) !important;
  color: var(--color-text) !important;
  font-weight: 600 !important;
}

:deep(.apexcharts-tooltip-text-y-label) {
  color: var(--color-text-light) !important;
}

:deep(.apexcharts-tooltip-text-y-value) {
  color: var(--color-text) !important;
  font-weight: 600 !important;
}

:deep(.apexcharts-legend-text) {
  color: var(--color-text) !important;
}

:deep(.apexcharts-xaxis-label) {
  fill: #6b7280 !important;
}

:deep(.apexcharts-yaxis-label) {
  fill: #6b7280 !important;
}
</style>