<template>
  <div class="tab-content">
    <div class="grid grid-sidebar">
      <div class="container">

        <div v-if="loading && !categories.length" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <div>Loading categories...</div>
        </div>

        <div v-else-if="error" class="error-state">
          <div class="error-message">{{ error }}</div>
          <button class="btn btn-small" @click="refreshCategories">
            Try Again
          </button>
        </div>

        <CategoryTree
          v-else
          :categories="categories"
          :selectedId="currentSelectedId"
          :showStats="true"
          @select="handleSelect"
        />
      </div>

      <div class="container">
        <div v-if="!selectedLevel" class="empty-selection">
          <div class="empty-subtitle">
            Choose a transaction type, category, or subcategory from the tree to view details
          </div>
        </div>

        <div v-else-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <div>Loading summary...</div>
        </div>

        <CategoryTypeSummary
          v-else-if="selectedLevel === 'type' && categorySummary"
          :typeData="selectedType"
          :summary="categorySummary"
        />

        <CategoryDetailSummary
          v-else-if="selectedLevel === 'category' && categorySummary"
          :summary="categorySummary"
          @select-subcategory="handleSubcategorySelect"
        />

        <SubcategoryDetails
          v-else-if="selectedLevel === 'subcategory' && categorySummary"
          :summary="categorySummary"
          :subcategoryId="selectedSubcategory.id"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, watch } from 'vue'
import { useCategoryStore } from '@/stores/categories'
import CategoryTree from './CategoryTree.vue'
import CategoryTypeSummary from './CategoryTypeSummary.vue'
import CategoryDetailSummary from './CategoryDetailSummary.vue'
import SubcategoryDetails from './SubcategoryDetails.vue'

export default {
  name: 'CategoriesTab',
  components: {
    CategoryTree,
    CategoryTypeSummary,
    CategoryDetailSummary,
    SubcategoryDetails
  },
  setup() {
    const categoryStore = useCategoryStore()

    const categories = computed(() => categoryStore.categories)
    const selectedType = computed(() => categoryStore.selectedType)
    const selectedCategory = computed(() => categoryStore.selectedCategory)
    const selectedSubcategory = computed(() => categoryStore.selectedSubcategory)
    const categorySummary = computed(() => categoryStore.categorySummary)
    const selectedLevel = computed(() => categoryStore.selectedLevel)
    const loading = computed(() => categoryStore.loading)
    const error = computed(() => categoryStore.error)

    const currentSelectedId = computed(() => {
      if (selectedSubcategory.value) return selectedSubcategory.value.id
      if (selectedCategory.value) return selectedCategory.value.id
      if (selectedType.value) return selectedType.value.id
      return null
    })

    async function refreshCategories() {
      await categoryStore.loadCategories()
    }

    function handleSelect(item, level) {
      console.log('Selected:', level, item.name)

      if (level === 'type') {
        categoryStore.selectType(item)
      } else if (level === 'category') {
        categoryStore.selectCategory(item)
      } else if (level === 'subcategory') {
        categoryStore.selectSubcategory(item)
      }
    }

    function handleSubcategorySelect(subcategory) {
      categoryStore.selectSubcategory(subcategory)
    }

    onMounted(async () => {
      console.log('CategoriesTab mounted')
      await categoryStore.loadCategories()
    })

    return {
      categories,
      selectedType,
      selectedCategory,
      selectedSubcategory,
      categorySummary,
      selectedLevel,
      loading,
      error,
      currentSelectedId,
      refreshCategories,
      handleSelect,
      handleSubcategorySelect
    }
  }
}
</script>

<style scoped>
.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
}

.loading-state,
.error-state,
.empty-selection {
  text-align: center;
  padding: var(--gap-large);
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

.error-message {
  color: #dc2626;
  margin-bottom: var(--gap-standard);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--gap-standard);
}

.empty-title {
  font-size: var(--text-large);
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.empty-subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-small);
}
</style>