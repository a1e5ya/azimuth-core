<!--
  TimelineTab Component - Main Timeline View Container
  
  Provides complete timeline visualization interface:
  - Filter bar for breakdown mode selection
  - Category legend sidebar with toggles
  - Timeline chart with ApexCharts
  - Zoom controls and mode selection
  - Year selector scrollbar
  - Hover info detail panel
  
  Features:
  - Multiple breakdown modes (All, Owner, Account)
  - Category visibility toggles (Type, Category, Subcategory)
  - Zoom levels (Year, Quarter, Month)
  - View/Add mode toggle
  - Custom date range scrolling
  - Pinnable hover info
  - Dynamic cursor based on mode
  
  Composables:
  - useTimelineData: Transaction loading and zoom management
  - useTimelineVisibility: Category visibility state
  - useTimelineChart: Chart configuration and data processing
  
  Layout Structure:
  - TimelineFilterBar: Top filter controls
  - TimelineCategoryLegend: Left sidebar
  - TimelineControls: Zoom and mode controls
  - TimelineChart: Main chart area
  - TimelineYearSelector: Bottom scrollbar
  - TimelineHoverInfo: Bottom detail panel
  
  State Management:
  - Loading state from backend
  - Category visibility tracking
  - Date range management
  - Breakdown mode and filters
-->

<template>
  <div class="timeline-container">
    <!-- Filter Bar -->
    <TimelineFilterBar
      :breakdownMode="breakdownMode"
      :selectedOwners="selectedOwners"
      :selectedAccounts="selectedAccounts"
      :transactions="transactions"
      @update:breakdownMode="breakdownMode = $event"
      @update:selectedOwners="selectedOwners = $event"
      @update:selectedAccounts="selectedAccounts = $event"
    />

    <!-- Main Content: Legend + Chart Area -->
    <div class="timeline-main-content">
      <!-- Compact Legend - Left Side -->
      <TimelineCategoryLegend
        :expense-categories="expenseCategories"
        :income-categories="incomeCategories"
        :transfer-categories="transferCategories"
        :target-categories="targetCategories"
        :visible-types="visibleTypes"
        :visible-categories="visibleCategories"
        :visible-subcategories="visibleSubcategories"
        :expanded-categories="expandedCategories"
        @toggle-type="toggleType"
        @toggle-category="toggleCategory"
        @toggle-subcategory="toggleSubcategory"
        @toggle-category-expanded="toggleCategoryExpanded"
      />

      <!-- Right Side: Controls + Chart + Scrollbar + Info -->
      <div class="timeline-chart-container container">
        <!-- 1. Controls at the TOP -->
        <TimelineControls
          :current-zoom-level="currentZoomLevel"
          :current-mode="currentMode"
          :full-range-start="fullRangeStart"
          :full-range-end="fullRangeEnd"
          :visible-range-start="visibleRangeStart"
          :visible-range-end="visibleRangeEnd"
          @set-zoom-level="handleSetZoomLevel"
          @set-mode="setMode"
        />
        
        <!-- 2. Chart in the MIDDLE -->
        <div class="chart-wrapper" :class="cursorClass">
          <TimelineChart
            ref="chartComponentRef"
            :loading="loading"
            :has-data="hasData"
            :chart-options="chartOptions"
            :chart-series="chartSeries"
          />
        </div>
        
        <!-- 3. Scrollbar BELOW the chart -->
        <TimelineYearSelector
          :full-range-start="fullRangeStart"
          :full-range-end="fullRangeEnd"
          :visible-range-start="visibleRangeStart"
          :visible-range-end="visibleRangeEnd"
          :current-zoom-level="currentZoomLevel"
          @scroll-to="handleScrollTo"
        />
        
        <!-- 4. Hover Info at the BOTTOM -->
        <TimelineHoverInfo
          :hovered-data="hoveredData"
          @unpin="unpinHoverData"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import { useTimelineData } from '@/composables/useTimelineData'
import { useTimelineVisibility } from '@/composables/useTimelineVisibility'
import { useTimelineChart } from '@/composables/useTimelineChart'
import TimelineFilterBar from './TimelineFilterBar.vue'
import TimelineCategoryLegend from './TimelineCategoryLegend.vue'
import TimelineChart from './TimelineChart.vue'
import TimelineControls from './TimelineControls.vue'
import TimelineYearSelector from './TimelineYearSelector.vue'
import TimelineHoverInfo from './TimelineHoverInfo.vue'

export default {
  name: 'TimelineTab',
  components: {
    TimelineFilterBar,
    TimelineCategoryLegend,
    TimelineChart,
    TimelineControls,
    TimelineYearSelector,
    TimelineHoverInfo
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
    const currentMode = ref('view')
    const customVisibleRange = ref(null)
    const chartComponentRef = ref(null)
    
    const {
      loading,
      transactions,
      dateRange,
      currentZoomLevel,
      hasData,
      timelineData,
      breakdownMode,
      selectedOwners,
      selectedAccounts,
      loadTransactions
    } = useTimelineData()
    
    const fullRangeStart = computed(() => {
      if (!dateRange.value.start) return new Date()
      return dateRange.value.start
    })
    
    const fullRangeEnd = computed(() => {
      if (!dateRange.value.end) return new Date()
      const futureDate = new Date(dateRange.value.end)
      futureDate.setFullYear(futureDate.getFullYear() + 2)
      return futureDate
    })
    
    const visibleRangeStart = computed(() => {
      if (customVisibleRange.value) {
        return customVisibleRange.value.start
      }
      return dateRange.value.start || new Date()
    })
    
    const visibleRangeEnd = computed(() => {
      if (customVisibleRange.value) {
        return customVisibleRange.value.end
      }
      return dateRange.value.end || new Date()
    })
    
    const cursorClass = computed(() => {
      return currentMode.value === 'add' ? 'cursor-plus' : 'cursor-default'
    })
    
    const {
      visibleTypes,
      visibleCategories,
      visibleSubcategories,
      expandedCategories,
      toggleType,
      toggleCategory,
      toggleSubcategory,
      toggleCategoryExpanded,
      initializeVisibility
    } = useTimelineVisibility(
      () => {
        const expenseType = categoryStore.categories?.find(t => t.code === 'expenses')
        return expenseType?.children || []
      },
      () => {
        const incomeType = categoryStore.categories?.find(t => t.code === 'income')
        return incomeType?.children || []
      },
      () => {
        const transferType = categoryStore.categories?.find(t => t.code === 'transfers')
        return transferType?.children || []
      },
      () => {
        const targetType = categoryStore.categories?.find(t => t.code === 'targets')
        return targetType?.children || []
      }
    )
    
    const chartRef = computed(() => chartComponentRef.value?.chartRef)
    
    const {
      hoveredData,
      isPinned,
      chartSeries,
      chartOptions,
      expenseCategories,
      incomeCategories,
      transferCategories,
      targetCategories,
      unpinHoverData
    } = useTimelineChart(
      timelineData,
      transactions,
      dateRange,
      currentZoomLevel,
      categoryStore,
      {
        visibleTypes,
        visibleCategories,
        visibleSubcategories,
        expandedCategories,
        isTypeVisible: (typeId) => visibleTypes.value.includes(typeId),
        isCategoryVisible: (categoryId) => visibleCategories.value.includes(categoryId),
        isSubcategoryVisible: (subcategoryId) => visibleSubcategories.value.includes(subcategoryId),
        isCategoryExpanded: (categoryId) => expandedCategories.value.includes(categoryId)
      },
      customVisibleRange,
      chartRef,
      breakdownMode,
      selectedOwners,
      selectedAccounts
    )
    
    /**
     * Sets current mode (view or add) and unpins hover data
     * @param {string} mode - Mode to set ('view' or 'add')
     * @returns {void}
     */
    function setMode(mode) {
      currentMode.value = mode
      
      if (isPinned.value) {
        unpinHoverData()
      }
    }
    
    /**
     * Handles scroll to custom date range
     * @param {Object} params - Range parameters
     * @param {Date} params.start - Range start date
     * @param {Date} params.end - Range end date
     * @returns {void}
     */
    function handleScrollTo({ start, end }) {
      const clampedStart = new Date(Math.max(start.getTime(), fullRangeStart.value.getTime()))
      const clampedEnd = new Date(Math.min(end.getTime(), fullRangeEnd.value.getTime()))
      
      customVisibleRange.value = {
        start: clampedStart,
        end: clampedEnd
      }
    }
    

    
    /**
     * Sets zoom level and resets custom range
     * @param {number} level - Zoom level (-1: Year, 0: Quarter, 1: Month)
     * @returns {void}
     */
    function handleSetZoomLevel(level) {
      currentZoomLevel.value = level
      unpinHoverData()
      customVisibleRange.value = null
    }
    
    watch(
      [visibleTypes, visibleCategories, visibleSubcategories, expandedCategories],
      () => {},
      { deep: true }
    )
    
    watch(() => currentZoomLevel.value, () => {
      unpinHoverData()
      customVisibleRange.value = null
    })
    
    watch(() => currentMode.value, () => {})
    
    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadTransactions(authStore.token)
      }
    })
    
    onMounted(async () => {
      if (authStore.user) {
        await categoryStore.loadCategories()
        await loadTransactions(authStore.token)
        initializeVisibility()
      }
    })
    
    return {
      chartComponentRef,
      loading,
      hasData,
      currentZoomLevel,
      currentMode,
      cursorClass,
      fullRangeStart,
      fullRangeEnd,
      visibleRangeStart,
      visibleRangeEnd,
      expenseCategories,
      incomeCategories,
      transferCategories,
      targetCategories,
      visibleTypes,
      visibleCategories,
      visibleSubcategories,
      expandedCategories,
      chartSeries,
      chartOptions,
      hoveredData,
      toggleType,
      toggleCategory,
      toggleSubcategory,
      toggleCategoryExpanded,
      handleSetZoomLevel,
      unpinHoverData,
      setMode,
      handleScrollTo,
      breakdownMode,
      selectedOwners,
      selectedAccounts,
      transactions
    }
  }
}
</script>

<style scoped>
.timeline-container {
  padding: 0;
}

.timeline-main-content {
  display: flex;
  gap: var(--gap-standard);
  margin-bottom: var(--gap-standard);
}

.timeline-chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.chart-wrapper {
  position: relative;
}

.cursor-default :deep(.apexcharts-svg) {
  cursor: default !important;
}

.cursor-plus :deep(.apexcharts-svg) {
  cursor: crosshair !important;
}
</style>