<template>
  <div class="container">
    <div class="chart-header">
      <h3>Income vs Expenses Trend</h3>
    </div>

    <div v-if="chartData.length === 0" class="empty-state">
      <div>No data for selected period</div>
    </div>

    <div v-else class="chart-container">
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
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'DashboardIncomeExpensesChart',
  components: {
    apexchart: VueApexCharts
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
  setup(props) {
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
      chartData,
      chartSeries,
      chartOptions
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