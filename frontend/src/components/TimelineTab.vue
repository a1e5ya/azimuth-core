<template>
  <div class="timeline-container">
    <!-- Header Controls -->
    <div class="timeline-header">
      <div class="timeline-title">
        <span class="timeline-subtitle">
          {{ formatDateRange(dateRange.start, dateRange.end) }}
        </span>
      </div>
      
      <div class="timeline-controls">
        <!-- Zoom Controls -->
        <div class="zoom-controls">
          <button 
            v-for="zoom in zoomLevels" 
            :key="zoom.value"
            class="btn btn-small"
            :class="{ 'btn-active': currentZoom === zoom.value }"
            @click="setZoom(zoom.value)"
          >
            {{ zoom.label }}
          </button>
        </div>
        
        <!-- Category Toggle -->
        <button 
          class="btn btn-small"
          @click="showCategoryPanel = !showCategoryPanel"
        >
          Categories {{ visibleCategories.length }}/{{ allCategories.length }}
        </button>
        
        <!-- View Mode Toggle -->
        <div class="view-toggle">
          <button 
            class="btn btn-small"
            :class="{ 'btn-active': viewMode === 'stacked' }"
            @click="viewMode = 'stacked'"
          >
            Stacked
          </button>
          <button 
            class="btn btn-small"
            :class="{ 'btn-active': viewMode === 'separate' }"
            @click="viewMode = 'separate'"
          >
            Separate
          </button>
        </div>
      </div>
    </div>

    <!-- Category Selection Panel -->
    <transition name="slide-down">
      <div v-if="showCategoryPanel" class="category-panel">
        <div class="category-filters">
          <div class="filter-section">
            <h4>Transaction Types</h4>
            <label v-for="type in transactionTypes" :key="type.id" class="checkbox-label">
              <input 
                type="checkbox" 
                :checked="visibleTypes.includes(type.id)"
                @change="toggleType(type.id)"
              >
              <span>{{ type.name }}</span>
            </label>
          </div>
          
          <div class="filter-section">
            <h4>Categories</h4>
            <div class="category-grid">
              <label v-for="cat in allCategories" :key="cat.id" class="checkbox-label">
                <input 
                  type="checkbox" 
                  :checked="visibleCategories.includes(cat.id)"
                  @change="toggleCategory(cat.id)"
                >
                <span :style="{ color: cat.color }">{{ cat.name }}</span>
              </label>
            </div>
          </div>
          
          <div class="filter-actions">
            <button class="btn btn-small" @click="selectAllCategories">Select All</button>
            <button class="btn btn-small" @click="deselectAllCategories">Deselect All</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Main Timeline Chart -->
    <div class="timeline-chart-wrapper">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <p>Loading timeline data...</p>
      </div>
      
      <div v-else-if="!hasData" class="empty-state">
        <p>No transaction data available</p>
        <p class="text-small">Import transactions to see your financial timeline</p>
      </div>
      
      <div v-else ref="chartContainer" class="timeline-chart">
        <apexchart
          ref="mainChart"
          type="area"
          height="400"
          :options="chartOptions"
          :series="chartSeries"
          @dataPointSelection="handleDataPointClick"
        />
      </div>
    </div>

    <!-- Navigator/Brush Chart -->
    <div v-if="hasData && !loading" class="timeline-navigator">
      <apexchart
        ref="navigatorChart"
        type="area"
        height="100"
        :options="navigatorOptions"
        :series="navigatorSeries"
      />
    </div>

    <!-- Goal Creation Inline Form -->
    <transition name="fade">
      <div v-if="showGoalForm" class="goal-form-overlay" @click.self="closeGoalForm">
        <div class="goal-form">
          <div class="goal-form-header">
            <h3>Create Financial Goal</h3>
            <button class="btn-close" @click="closeGoalForm">×</button>
          </div>
          
          <div class="goal-form-body">
            <div class="form-group">
              <label>Goal Name</label>
              <input 
                v-model="newGoal.name" 
                type="text" 
                class="form-input"
                placeholder="e.g., Summer Vacation"
              >
            </div>
            
            <div class="form-group">
              <label>Target Amount (€)</label>
              <input 
                v-model.number="newGoal.amount" 
                type="number" 
                class="form-input"
                placeholder="3000"
              >
            </div>
            
            <div class="form-group">
              <label>Target Date</label>
              <input 
                v-model="newGoal.date" 
                type="date" 
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label>Goal Type</label>
              <select v-model="newGoal.type" class="form-input">
                <option value="savings">Savings Target</option>
                <option value="spending-limit">Spending Limit</option>
                <option value="debt-payoff">Debt Payoff</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Category (optional)</label>
              <select v-model="newGoal.categoryId" class="form-input">
                <option value="">All Categories</option>
                <option v-for="cat in allCategories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
            </div>
            
            <!-- Forecast Preview -->
            <div v-if="goalForecast" class="goal-forecast">
              <h4>Forecast</h4>
              <div class="forecast-details">
                <p>Monthly savings needed: <strong>€{{ goalForecast.monthlySavings }}</strong></p>
                <p>Probability of success: <strong>{{ goalForecast.probability }}%</strong></p>
                <p class="text-small">Based on your spending patterns</p>
              </div>
            </div>
          </div>
          
          <div class="goal-form-actions">
            <button class="btn" @click="saveGoal">Create Goal</button>
            <button class="btn btn-link" @click="closeGoalForm">Cancel</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Goals & Annotations List -->
    <div v-if="goals.length > 0" class="goals-list">
      <h3>Active Goals</h3>
      <div class="goals-grid">
        <div v-for="goal in goals" :key="goal.id" class="goal-card">
          <div class="goal-header">
            <h4>{{ goal.name }}</h4>
            <button class="btn-small btn-link" @click="removeGoal(goal.id)">×</button>
          </div>
          <div class="goal-details">
            <p>Target: €{{ goal.amount }}</p>
            <p>Due: {{ formatDate(goal.date) }}</p>
            <div class="goal-progress">
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: goal.progress + '%' }"
                ></div>
              </div>
              <span>{{ goal.progress }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Statistics Summary -->
    <div class="timeline-stats">
      <div class="stat-card">
        <div class="stat-label">Total Income</div>
        <div class="stat-value positive">€{{ formatNumber(stats.totalIncome) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Expenses</div>
        <div class="stat-value negative">€{{ formatNumber(stats.totalExpenses) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Net Savings</div>
        <div class="stat-value" :class="stats.netSavings >= 0 ? 'positive' : 'negative'">
          €{{ formatNumber(stats.netSavings) }}
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Average Monthly</div>
        <div class="stat-value">€{{ formatNumber(stats.avgMonthly) }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'TimelineTab',
  components: {
    apexchart: VueApexCharts
  },
  props: {
    transactions: {
      type: Array,
      default: () => []
    },
    categories: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    // State
    const loading = ref(false)
    const currentZoom = ref('month')
    const viewMode = ref('stacked')
    const showCategoryPanel = ref(false)
    const showGoalForm = ref(false)
    const selectedDataPoint = ref(null)
    
    // Chart refs
    const mainChart = ref(null)
    const navigatorChart = ref(null)
    const chartContainer = ref(null)
    
    // Data
    const visibleCategories = ref([])
    const visibleTypes = ref(['income', 'expenses'])
    const goals = ref([])
    const newGoal = ref({
      name: '',
      amount: 0,
      date: '',
      type: 'savings',
      categoryId: ''
    })
    
    const dateRange = ref({
      start: null,
      end: null
    })
    
    // Constants
    const zoomLevels = [
      { value: 'month', label: 'Month', days: 30 },
      { value: 'year', label: 'Year', days: 365 }
    ]
    
    const transactionTypes = [
      { id: 'income', name: 'Income', color: '#22c55e' },
      { id: 'expenses', name: 'Expenses', color: '#ef4444' },
      { id: 'transfers', name: 'Transfers', color: '#3b82f6' }
    ]
    
    // Computed
    const allCategories = computed(() => {
      // Extract all unique categories from transactions
      const catMap = new Map()
      props.transactions.forEach(t => {
        if (t.main_category) {
          const key = t.main_category
          if (!catMap.has(key)) {
            catMap.set(key, {
              id: key,
              name: t.main_category,
              color: generateCategoryColor(key)
            })
          }
        }
      })
      return Array.from(catMap.values())
    })
    
    const hasData = computed(() => props.transactions.length > 0)
    
    const stats = computed(() => {
      const income = props.transactions
        .filter(t => t.transaction_type === 'income')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const expenses = props.transactions
        .filter(t => t.transaction_type === 'expense')
        .reduce((sum, t) => sum + Math.abs(parseFloat(t.amount)), 0)
      
      const netSavings = income - expenses
      const months = getMonthCount()
      const avgMonthly = months > 0 ? expenses / months : 0
      
      return {
        totalIncome: income,
        totalExpenses: expenses,
        netSavings,
        avgMonthly
      }
    })
    
    // Process timeline data based on zoom level
    const timelineData = computed(() => {
      if (!props.transactions.length) return []
      
      const grouped = groupTransactionsByPeriod(
        props.transactions,
        currentZoom.value
      )
      
      return grouped
    })
    
    // Chart series
    const chartSeries = computed(() => {
      if (!timelineData.value.length) return []
      
      const series = []
      
      // Income/Expense totals
      if (visibleTypes.value.includes('income')) {
        series.push({
          name: 'Income',
          type: 'area',
          data: timelineData.value.map(d => ({
            x: d.date,
            y: d.income
          }))
        })
      }
      
      if (visibleTypes.value.includes('expenses')) {
        if (viewMode.value === 'stacked') {
          // Stacked by category
          visibleCategories.value.forEach(catId => {
            const category = allCategories.value.find(c => c.id === catId)
            if (category) {
              series.push({
                name: category.name,
                type: 'area',
                data: timelineData.value.map(d => ({
                  x: d.date,
                  y: d.categories[catId] || 0
                }))
              })
            }
          })
        } else {
          // Total expenses line
          series.push({
            name: 'Expenses',
            type: 'area',
            data: timelineData.value.map(d => ({
              x: d.date,
              y: d.expenses
            }))
          })
        }
      }
      
      // Balance line
      series.push({
        name: 'Balance',
        type: 'line',
        data: timelineData.value.map(d => ({
          x: d.date,
          y: d.balance
        }))
      })
      
      return series
    })
    
    const chartOptions = computed(() => ({
      chart: {
        id: 'timeline-main',
        type: 'area',
        height: 400,
        stacked: viewMode.value === 'stacked',
        toolbar: {
          show: true,
          tools: {
            download: true,
            selection: true,
            zoom: true,
            zoomin: true,
            zoomout: true,
            pan: true,
            reset: true
          }
        },
        zoom: {
          enabled: true,
          type: 'x',
          autoScaleYaxis: true
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
        width: [0, 0, 0, 3] // Thicker line for balance
      },
      fill: {
        type: 'gradient',
        gradient: {
          opacityFrom: 0.6,
          opacityTo: 0.1
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'left'
      },
      xaxis: {
        type: 'datetime',
        labels: {
          datetimeUTC: false
        }
      },
      yaxis: {
        title: {
          text: 'Amount (€)'
        },
        labels: {
          formatter: (val) => '€' + val.toFixed(0)
        }
      },
      tooltip: {
        shared: true,
        intersect: false,
        x: {
          format: 'dd MMM yyyy'
        },
        y: {
          formatter: (val) => '€' + val.toFixed(2)
        }
      },
      annotations: {
        points: goals.value.map(goal => ({
          x: new Date(goal.date).getTime(),
          y: goal.amount,
          marker: {
            size: 8,
            fillColor: goal.progress >= 100 ? '#22c55e' : '#ef4444',
            strokeColor: '#fff',
            strokeWidth: 2
          },
          label: {
            borderColor: goal.progress >= 100 ? '#22c55e' : '#ef4444',
            style: {
              color: '#fff',
              background: goal.progress >= 100 ? '#22c55e' : '#ef4444'
            },
            text: goal.name
          }
        }))
      },
      colors: generateChartColors()
    }))
    
    const navigatorSeries = computed(() => [{
      name: 'Balance',
      data: timelineData.value.map(d => ({
        x: d.date,
        y: d.balance
      }))
    }])
    
    const navigatorOptions = computed(() => ({
      chart: {
        id: 'timeline-navigator',
        type: 'area',
        height: 100,
        brush: {
          enabled: true,
          target: 'timeline-main'
        },
        selection: {
          enabled: true,
          xaxis: {
            min: dateRange.value.start?.getTime(),
            max: dateRange.value.end?.getTime()
          }
        },
        toolbar: {
          show: false
        }
      },
      colors: ['#3b82f6'],
      fill: {
        type: 'gradient',
        gradient: {
          opacityFrom: 0.4,
          opacityTo: 0.1
        }
      },
      xaxis: {
        type: 'datetime',
        labels: {
          show: false
        }
      },
      yaxis: {
        show: false
      },
      tooltip: {
        enabled: false
      }
    }))
    
    const goalForecast = computed(() => {
      if (!newGoal.value.amount || !newGoal.value.date) return null
      
      const targetDate = new Date(newGoal.value.date)
      const today = new Date()
      const monthsRemaining = Math.max(1, 
        (targetDate.getFullYear() - today.getFullYear()) * 12 +
        (targetDate.getMonth() - today.getMonth())
      )
      
      const monthlySavings = (newGoal.value.amount / monthsRemaining).toFixed(2)
      
      // Simple probability based on historical savings rate
      const avgMonthlySavings = stats.value.netSavings / getMonthCount()
      const probability = Math.min(100, Math.round(
        (avgMonthlySavings / monthlySavings) * 100
      ))
      
      return {
        monthlySavings,
        probability: Math.max(0, probability)
      }
    })
    
    // Methods
    function groupTransactionsByPeriod(transactions, zoom) {
      const grouped = new Map()
      
      transactions.forEach(t => {
        const date = new Date(t.posted_at)
        let key
        
        if (zoom === 'month') {
          key = new Date(date.getFullYear(), date.getMonth(), 1)
        }  else {
          key = new Date(date.getFullYear(), 0, 1)
        }
        
        const keyStr = key.toISOString()
        
        if (!grouped.has(keyStr)) {
          grouped.set(keyStr, {
            date: key.getTime(),
            income: 0,
            expenses: 0,
            balance: 0,
            categories: {}
          })
        }
        
        const period = grouped.get(keyStr)
        const amount = Math.abs(parseFloat(t.amount))
        
        if (t.transaction_type === 'income') {
          period.income += amount
          period.balance += amount
        } else if (t.transaction_type === 'expense') {
          period.expenses += amount
          period.balance -= amount
          
          // Track by category
          const cat = t.main_category || 'Uncategorized'
          period.categories[cat] = (period.categories[cat] || 0) + amount
        }
      })
      
      // Calculate running balance
      let runningBalance = 0
      return Array.from(grouped.values())
        .sort((a, b) => a.date - b.date)
        .map(period => {
          runningBalance += period.balance
          return {
            ...period,
            balance: runningBalance
          }
        })
    }
    
    function generateCategoryColor(categoryName) {
      // Simple hash-based color generation
      let hash = 0
      for (let i = 0; i < categoryName.length; i++) {
        hash = categoryName.charCodeAt(i) + ((hash << 5) - hash)
      }
      const hue = hash % 360
      return `hsl(${hue}, 70%, 60%)`
    }
    
    function generateChartColors() {
      return [
        '#22c55e', // Income - green
        ...visibleCategories.value.map(catId => {
          const cat = allCategories.value.find(c => c.id === catId)
          return cat?.color || '#94a3b8'
        }),
        '#3b82f6' // Balance - blue
      ]
    }
    
    function setZoom(level) {
      currentZoom.value = level
    }
    
    function toggleCategory(catId) {
      const index = visibleCategories.value.indexOf(catId)
      if (index > -1) {
        visibleCategories.value.splice(index, 1)
      } else {
        visibleCategories.value.push(catId)
      }
    }
    
    function toggleType(typeId) {
      const index = visibleTypes.value.indexOf(typeId)
      if (index > -1) {
        visibleTypes.value.splice(index, 1)
      } else {
        visibleTypes.value.push(typeId)
      }
    }
    
    function selectAllCategories() {
      visibleCategories.value = allCategories.value.map(c => c.id)
    }
    
    function deselectAllCategories() {
      visibleCategories.value = []
    }
    
    function handleDataPointClick(event, chartContext, config) {
      const dataPointIndex = config.dataPointIndex
      const seriesIndex = config.seriesIndex
      
      if (dataPointIndex < 0) return
      
      const clickedDate = timelineData.value[dataPointIndex]?.date
      if (!clickedDate) return
      
      const clickedDateObj = new Date(clickedDate)
      const today = new Date()
      
      // Only allow goal creation for future dates
      if (clickedDateObj > today) {
        selectedDataPoint.value = clickedDateObj
        newGoal.value.date = clickedDateObj.toISOString().split('T')[0]
        showGoalForm.value = true
      }
    }
    
    function saveGoal() {
      if (!newGoal.value.name || !newGoal.value.amount || !newGoal.value.date) {
        alert('Please fill in all required fields')
        return
      }
      
      goals.value.push({
        id: Date.now(),
        ...newGoal.value,
        progress: 0 // TODO: Calculate based on current savings
      })
      
      closeGoalForm()
    }
    
    function closeGoalForm() {
      showGoalForm.value = false
      newGoal.value = {
        name: '',
        amount: 0,
        date: '',
        type: 'savings',
        categoryId: ''
      }
      selectedDataPoint.value = null
    }
    
    function removeGoal(goalId) {
      goals.value = goals.value.filter(g => g.id !== goalId)
    }
    
    function getMonthCount() {
      if (!props.transactions.length) return 1
      
      const dates = props.transactions.map(t => new Date(t.posted_at))
      const minDate = new Date(Math.min(...dates))
      const maxDate = new Date(Math.max(...dates))
      
      return Math.max(1,
        (maxDate.getFullYear() - minDate.getFullYear()) * 12 +
        (maxDate.getMonth() - minDate.getMonth()) + 1
      )
    }
    
    function formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        year: 'numeric'
      })
    }
    
    function formatDateRange(start, end) {
      if (!start || !end) return 'All Time'
      return `${formatDate(start)} - ${formatDate(end)}`
    }
    
    function formatNumber(num) {
      return Math.abs(num).toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      })
    }
    
    // Initialize
    onMounted(() => {
      if (props.transactions.length > 0) {
        const dates = props.transactions.map(t => new Date(t.posted_at))
        dateRange.value.start = new Date(Math.min(...dates))
        dateRange.value.end = new Date(Math.max(...dates))
        
        // Select top 5 expense categories by default
        const categoryTotals = new Map()
        props.transactions
          .filter(t => t.transaction_type === 'expense')
          .forEach(t => {
            const cat = t.main_category || 'Uncategorized'
            categoryTotals.set(cat, (categoryTotals.get(cat) || 0) + Math.abs(parseFloat(t.amount)))
          })
        
        visibleCategories.value = Array.from(categoryTotals.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([cat]) => cat)
      }
    })
    
    // Watch for transaction changes
    watch(() => props.transactions, () => {
      if (props.transactions.length > 0 && visibleCategories.value.length === 0) {
        selectAllCategories()
      }
    })
    
    return {
      loading,
      currentZoom,
      viewMode,
      showCategoryPanel,
      showGoalForm,
      mainChart,
      navigatorChart,
      chartContainer,
      visibleCategories,
      visibleTypes,
      goals,
      newGoal,
      dateRange,
      zoomLevels,
      transactionTypes,
      allCategories,
      hasData,
      stats,
      chartSeries,
      chartOptions,
      navigatorSeries,
      navigatorOptions,
      goalForecast,
      setZoom,
      toggleCategory,
      toggleType,
      selectAllCategories,
      deselectAllCategories,
      handleDataPointClick,
      saveGoal,
      closeGoalForm,
      removeGoal,
      formatDate,
      formatDateRange,
      formatNumber
    }
  }
}
</script>

<style scoped>
.timeline-container {
  padding: var(--gap-standard);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-large);
  flex-wrap: wrap;
  gap: var(--gap-standard);
}

.timeline-title h2 {
  margin: 0 0 0.25rem 0;
}

.timeline-subtitle {
  color: var(--color-text-light);
  font-size: var(--text-small);
}

.timeline-controls {
  display: flex;
  gap: var(--gap-standard);
  align-items: center;
  flex-wrap: wrap;
}

.zoom-controls,
.view-toggle {
  display: flex;
  gap: 0.25rem;
}

/* Category Panel */
.category-panel {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
}

.category-filters {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.filter-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: var(--text-medium);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
}

.checkbox-label:hover {
  background: var(--color-background-dark);
}

.checkbox-label input {
  cursor: pointer;
}

.filter-actions {
  display: flex;
  gap: var(--gap-small);
}

/* Chart Wrapper */
.timeline-chart-wrapper {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  min-height: 400px;
}

.timeline-navigator {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
}

/* Goal Form */
.goal-form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.goal-form {
  background: var(--color-background-light);
  border-radius: var(--radius-large);
  padding: 0;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow);
}

.goal-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-standard);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.goal-form-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: var(--color-text);
}

.goal-form-body {
  padding: var(--gap-standard);
}

.form-group {
  margin-bottom: var(--gap-standard);
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text-light);
}

.form-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-button);
  font-size: var(--text-medium);
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-button-active);
}

.goal-forecast {
  background: var(--color-background-dark);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-top: var(--gap-standard);
}

.goal-forecast h4 {
  margin: 0 0 0.5rem 0;
  font-size: var(--text-medium);
}

.forecast-details p {
  margin: 0.25rem 0;
  font-size: var(--text-small);
}

.goal-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--gap-small);
  padding: var(--gap-standard);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* Goals List */
.goals-list {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
}

.goals-list h3 {
  margin: 0 0 var(--gap-standard) 0;
}

.goals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: var(--gap-standard);
}

.goal-card {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.goal-header h4 {
  margin: 0;
  font-size: var(--text-medium);
}

.goal-details p {
  margin: 0.25rem 0;
  font-size: var(--text-small);
  color: var(--color-text-light);
}

.goal-progress {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar {
  flex: 1;
  height: 0.5rem;
  background: var(--color-background-dark);
  border-radius: 0.25rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #16a34a);
  transition: width 0.3s ease;
}

/* Statistics */
.timeline-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap-standard);
}

.stat-card {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  text-align: center;
}

.stat-label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: var(--text-large);
  font-weight: 600;
}

.stat-value.positive {
  color: #22c55e;
}

.stat-value.negative {
  color: #ef4444;
}

/* Loading and Empty States */
.loading-state,
.empty-state {
  text-align: center;
  padding: var(--gap-large);
  color: var(--color-text-light);
}

.loading-spinner {
  font-size: var(--text-large);
  animation: spin 1s linear infinite;
  margin-bottom: var(--gap-standard);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}

.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 500px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}


</style>