<template>
  <div class="timeline-container">
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
      <div class="timeline-chart-container">
        <!-- 1. Controls at the TOP -->
        <TimelineControls
          :current-zoom-level="currentZoomLevel"
          :current-mode="currentMode"
          :full-range-start="fullRangeStart"
          :full-range-end="fullRangeEnd"
          :visible-range-start="visibleRangeStart"
          :visible-range-end="visibleRangeEnd"
          @zoom-in="zoomIn"
          @zoom-out="zoomOut"
          @reset-zoom="handleResetZoom"
          @set-mode="setMode"
        />
        
        <!-- 2. Chart in the MIDDLE -->
        <div class="chart-wrapper" :class="cursorClass">
          <TimelineChart
            :loading="loading"
            :has-data="hasData"
            :chart-options="chartOptions"
            :chart-series="chartSeries"
          />
        </div>
        
        <!-- 3. Scrollbar BELOW the chart -->
        <TimelineScrollbar
          :full-range-start="fullRangeStart"
          :full-range-end="fullRangeEnd"
          :visible-range-start="visibleRangeStart"
          :visible-range-end="visibleRangeEnd"
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
import TimelineCategoryLegend from './TimelineCategoryLegend.vue'
import TimelineChart from './TimelineChart.vue'
import TimelineControls from './TimelineControls.vue'
import TimelineScrollbar from './TimelineScrollbar.vue'
import TimelineHoverInfo from './TimelineHoverInfo.vue'

export default {
  name: 'TimelineTab',
  components: {
    TimelineCategoryLegend,
    TimelineChart,
    TimelineControls,
    TimelineScrollbar,
    TimelineHoverInfo
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
    // Current mode state
    const currentMode = ref('view') // 'view' or 'add'
    
    // Visible range for scrolling
    const customVisibleRange = ref(null)
    
    // Data management
    const {
      loading,
      transactions,
      dateRange,
      currentZoomLevel,
      hasData,
      timelineData,
      loadTransactions,
      zoomIn,
      zoomOut,
      resetZoom
    } = useTimelineData()
    
    // Calculate full range (including some future for targets)
    const fullRangeStart = computed(() => {
      if (!dateRange.value.start) return new Date()
      return dateRange.value.start
    })
    
    const fullRangeEnd = computed(() => {
      if (!dateRange.value.end) return new Date()
      // Extend to 1 year in the future for target planning
      const futureDate = new Date(dateRange.value.end)
      futureDate.setFullYear(futureDate.getFullYear() + 1)
      return futureDate
    })
    
    // Calculate visible range based on custom range or full range
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
    
    // Cursor class based on mode
    const cursorClass = computed(() => {
      return currentMode.value === 'add' ? 'cursor-plus' : 'cursor-default'
    })
    
    // Visibility management
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
    
    // Chart configuration - PASS customVisibleRange
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
      customVisibleRange // Pass this so chart knows about scroll position
    )
    
    // Set mode
    function setMode(mode) {
      currentMode.value = mode
      console.log('📍 Mode changed to:', mode)
      
      // Unpin when switching modes
      if (isPinned.value) {
        unpinHoverData()
      }
    }
    
    // Handle scroll to new range
    function handleScrollTo({ start, end }) {
      // Clamp to full range
      const clampedStart = new Date(Math.max(start.getTime(), fullRangeStart.value.getTime()))
      const clampedEnd = new Date(Math.min(end.getTime(), fullRangeEnd.value.getTime()))
      
      customVisibleRange.value = {
        start: clampedStart,
        end: clampedEnd
      }
      
      console.log('📜 Scrolled to:', clampedStart.toLocaleDateString(), '-', clampedEnd.toLocaleDateString())
    }
    
    // Handle reset zoom with unpin
    function handleResetZoom() {
      resetZoom()
      unpinHoverData()
      customVisibleRange.value = null // Reset to full range
    }
    
    // Watch for visibility changes
    watch(
      [visibleTypes, visibleCategories, visibleSubcategories, expandedCategories],
      () => {
        console.log('Visibility changed, chart will rebuild')
      },
      { deep: true }
    )
    
    // Watch for zoom level changes
    watch(() => currentZoomLevel.value, () => {
      console.log('Zoom level:', currentZoomLevel.value)
      unpinHoverData()
      customVisibleRange.value = null // Reset scroll when zooming
    })
    
    // Watch for mode changes
    watch(() => currentMode.value, (newMode) => {
      console.log('Mode changed to:', newMode)
    })
    
    // Watch for user authentication
    watch(() => authStore.user, (newUser) => {
      if (newUser) {
        loadTransactions(authStore.token)
      }
    })
    
    // Initialize on mount
    onMounted(async () => {
      if (authStore.user) {
        await categoryStore.loadCategories()
        await loadTransactions(authStore.token)
        initializeVisibility()
      }
    })
    
    return {
      // Data
      loading,
      hasData,
      currentZoomLevel,
      currentMode,
      cursorClass,
      
      // Date ranges for scrollbar
      fullRangeStart,
      fullRangeEnd,
      visibleRangeStart,
      visibleRangeEnd,
      
      // Categories
      expenseCategories,
      incomeCategories,
      transferCategories,
      targetCategories,
      
      // Visibility
      visibleTypes,
      visibleCategories,
      visibleSubcategories,
      expandedCategories,
      
      // Chart
      chartSeries,
      chartOptions,
      hoveredData,
      
      // Actions
      toggleType,
      toggleCategory,
      toggleSubcategory,
      toggleCategoryExpanded,
      zoomIn,
      zoomOut,
      handleResetZoom,
      unpinHoverData,
      setMode,
      handleScrollTo
    }
  }
}
</script>

<style scoped>
.timeline-container {
  padding: var(--gap-standard);
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

/* Cursor styles for different modes */
.cursor-default :deep(.apexcharts-svg) {
  cursor: default !important;
}

.cursor-plus :deep(.apexcharts-svg) {
  cursor: crosshair !important;
}

@media (max-width: 64rem) {
  .timeline-main-content {
    flex-direction: column;
  }
}

@media (max-width: 48rem) {
  .timeline-container {
    padding: var(--gap-small);
  }
}
</style>