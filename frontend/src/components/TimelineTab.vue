<template>
  <div class="timeline-container">
    <!-- Main Content: Legend + Chart -->
    <div class="timeline-main-content">
      <!-- Compact Legend - Left Side -->
      <TimelineCategoryLegend
        :expense-categories="expenseCategories"
        :income-categories="incomeCategories"
        :transfer-categories="transferCategories"
        :visible-types="visibleTypes"
        :visible-categories="visibleCategories"
        :visible-subcategories="visibleSubcategories"
        :expanded-categories="expandedCategories"
        @toggle-type="toggleType"
        @toggle-category="toggleCategory"
        @toggle-subcategory="toggleSubcategory"
        @toggle-category-expanded="toggleCategoryExpanded"
      />

      <!-- Chart Area -->
      <div class="timeline-chart-area">
        <!-- Zoom Controls -->
        <TimelineControls
          :current-zoom-level="currentZoomLevel"
          @zoom-in="zoomIn"
          @zoom-out="zoomOut"
          @reset-zoom="handleResetZoom"
        />
        
        <!-- Chart -->
        <TimelineChart
          :loading="loading"
          :has-data="hasData"
          :chart-options="chartOptions"
          :chart-series="chartSeries"
        />
        
        <!-- Hover Info -->
        <TimelineHoverInfo
          :hovered-data="hoveredData"
          @unpin="unpinHoverData"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import { useTimelineData } from '@/composables/useTimelineData'
import { useTimelineVisibility } from '@/composables/useTimelineVisibility'
import { useTimelineChart } from '@/composables/useTimelineChart'
import TimelineCategoryLegend from './TimelineCategoryLegend.vue'
import TimelineChart from './TimelineChart.vue'
import TimelineControls from './TimelineControls.vue'
import TimelineHoverInfo from './TimelineHoverInfo.vue'

export default {
  name: 'TimelineTab',
  components: {
    TimelineCategoryLegend,
    TimelineChart,
    TimelineControls,
    TimelineHoverInfo
  },
  setup() {
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
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
      }
    )
    
    // Chart configuration
    const {
      hoveredData,
      isPinned,
      chartSeries,
      chartOptions,
      expenseCategories,
      incomeCategories,
      transferCategories,
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
      }
    )
    
    // Handle reset zoom with unpin
    function handleResetZoom() {
      resetZoom()
      unpinHoverData()
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
      
      // Categories
      expenseCategories,
      incomeCategories,
      transferCategories,
      
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
      unpinHoverData
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

.timeline-chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
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