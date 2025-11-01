<template>
  <div class="tab-content">
        <!-- Type Tabs -->
      <div class="type-tabs">
        <div class="tabs-left">
          <button
            v-for="type in categories"
            :key="type.id"
            class="type-tab"
            :class="{ active: selectedTypeId === type.id }"
            :style="{ '--tab-hover-color': type.color }"
            @click="selectedTypeId = type.id"
          >
            <AppIcon :name="type.icon" size="medium" />
            {{ type.name }}
          </button>
        </div>
        
        <div class="tabs-right">
          <ActionsMenu
            class="always-visible"
            :show-add="true"
            :show-edit="false"
            :show-delete="false"
            :show-check="false"
            menu-title="Category Actions"
            @add="addNewCategory"
          />
        </div>
      </div>
    <div       class="container"    >


      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading categories...</div>
      </div>

      <!-- Categories Compact Grid -->
      <div 
        v-else-if="currentType" 
        class="categories-compact-grid"
      >
        <div
          v-for="mainCat in currentType.children"
          :key="mainCat.id"
          class="category-container"
          :style="{ backgroundColor: hexToRgba(mainCat.color, 0.1) }"
        >
          <!-- Main Category Header - Compact -->
          <div class="category-header-compact">
            <div class="category-title-compact">
              <AppIcon 
                :name="mainCat.icon" 
                size="medium"
                class="category-icon"
                :style="{ '--icon-hover-color': mainCat.color }"
              />
              <h4>{{ mainCat.name }}</h4>
            </div>
            <ActionsMenu
              :show-add="true"
              :show-edit="true"
              :show-delete="true"
              @edit="editCategory(mainCat)"
              @add="addSubcategory(mainCat)"
              @delete="deleteCategory(mainCat)"
            />
          </div>

          <!-- Subcategories Compact -->
          <div v-if="mainCat.children && mainCat.children.length > 0" class="subcats-compact">
            <div
              v-for="subcat in mainCat.children"
              :key="subcat.id"
              class="subcat-compact"
              :style="{ backgroundColor: hexToRgba(subcat.color, 0.1) }"
            >
              <div class="subcat-top">
                <div class="subcat-name-icon">
                  <AppIcon 
                    :name="subcat.icon" 
                    size="small"
                    class="subcat-icon"
                    :style="{ '--icon-hover-color': subcat.color }"
                  />
                  <span>{{ subcat.name }}</span>
                </div>
                <ActionsMenu
                  :show-add="false"
                  :show-edit="true"
                  :show-delete="true"
                  @edit="editCategory(subcat)"
                  @delete="deleteCategory(subcat)"
                />
              </div>

              <input
                type="text"
                class="keyword-input-compact"
                placeholder="keywords..."
                :value="getKeywords(subcat.id)"
                @change="updateKeywords(subcat.id, $event.target.value)"
              >

              <div class="merchant-tags-compact">
                <span v-for="merchant in getMerchants(subcat.id)" :key="merchant" class="tag-micro">
                  {{ merchant }}
                </span>
                <span v-if="!getMerchants(subcat.id).length" class="text-micro-muted">
                  No merchants
                </span>
              </div>
            </div>
          </div>

          <div v-else class="no-subcats-compact">
            <button class="btn btn-small" @click="addSubcategory(mainCat)">
              Add Subcategory
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useCategoryStore } from '@/stores/categories'
import AppIcon from './AppIcon.vue'
import ActionsMenu from './ActionsMenu.vue'

export default {
  name: 'CategoriesTab',
  components: { 
    AppIcon,
    ActionsMenu
  },
  setup() {
    const categoryStore = useCategoryStore()
    const selectedTypeId = ref(null)

    // Sort categories in the correct order: INCOME, EXPENSES, TRANSFERS, TARGETS
    const categories = computed(() => {
      const cats = categoryStore.categories || []
      const order = ['income', 'expenses', 'transfers', 'targets']
      
      return [...cats].sort((a, b) => {
        const aIndex = order.indexOf(a.code)
        const bIndex = order.indexOf(b.code)
        return aIndex - bIndex
      })
    })
    
    const loading = computed(() => categoryStore.loading)

    const currentType = computed(() => {
      if (!selectedTypeId.value || !categories.value) return null
      return categories.value.find(t => t.id === selectedTypeId.value)
    })

    function hexToRgba(hex, alpha) {
      if (!hex) return 'transparent'
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    async function refreshCategories() {
      await categoryStore.loadCategories()
      if (categories.value && categories.value.length > 0 && !selectedTypeId.value) {
        // Default to first tab (INCOME)
        selectedTypeId.value = categories.value[0].id
      }
    }

    function editCategory(category) {
      console.log('Edit:', category.name)
      // TODO: Open edit modal/form
    }

    function deleteCategory(category) {
      console.log('Delete:', category.name)
      // TODO: Confirm and delete category
    }

    function addSubcategory(parent) {
      console.log('Add subcategory to:', parent.name)
      // TODO: Open add subcategory modal/form
    }

    function addNewCategory() {
      console.log('Add new main category to:', currentType.value?.name)
      // TODO: Open add category modal/form
    }

    function getKeywords(categoryId) {
      // TODO: Fetch keywords for category from backend
      return ''
    }

    function updateKeywords(categoryId, keywords) {
      console.log('Update keywords:', categoryId, keywords)
      // TODO: Save keywords to backend
    }

    function getMerchants(categoryId) {
      // TODO: Fetch merchants for category from backend
      return []
    }

    onMounted(async () => {
      await refreshCategories()
    })

    return {
      categories,
      loading,
      selectedTypeId,
      currentType,
      hexToRgba,
      refreshCategories,
      editCategory,
      deleteCategory,
      addSubcategory,
      addNewCategory,
      getKeywords,
      updateKeywords,
      getMerchants
    }
  }
}
</script>

<style scoped>
/* Type Tabs */
.type-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  border-bottom: 2px solid var(--color-background-dark);
}

.tabs-left {
  display: flex;
  gap: var(--gap-small);
}

.tabs-right {
  display: flex;
  align-items: center;
  margin-bottom: -2px;
}

.type-tab {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: 0.5rem var(--gap-standard);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  color: var(--color-text-light);
  font-weight: 500;
  transition: all 0.2s;
}

.type-tab:hover {
  color: var(--color-text);
}

.type-tab:hover :deep(.icon-wrapper) {
  color: var(--tab-hover-color);
}

.type-tab.active {
  color: var(--color-text);
  border-bottom-color: var(--color-text);
  font-weight: 600;
}

/* Loading */
.loading-state {
  text-align: center;
  padding: var(--gap-large);
}

.loading-spinner {
  font-size: var(--text-large);
  animation: spin 1s linear infinite;
  margin-bottom: var(--gap-small);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Compact Grid Layout */
.categories-compact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  gap: var(--gap-standard);
  align-items: start;
}

.category-container {
  padding: 0.75rem;
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Category Header - Compact */
.category-header-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-background-dark);
}

.category-title-compact {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.category-title-compact h4 {
  margin: 0;
  font-size: var(--text-small);
  font-weight: 600;
}

.category-title-compact .category-icon:hover :deep(.icon-wrapper) {
  color: var(--icon-hover-color);
  transition: color 0.2s;
}

/* Subcategories Compact */
.subcats-compact {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.subcat-compact {
  padding: 0.5rem;
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.subcat-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subcat-name-icon {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: var(--text-small);
  font-weight: 500;
}

.subcat-name-icon .subcat-icon:hover :deep(.icon-wrapper) {
  color: var(--icon-hover-color);
  transition: color 0.2s;
}

/* Compact Input */
.keyword-input-compact {
  width: 100%;
  padding: 0.25rem 0.375rem;
  border: 1px solid var(--color-background-dark);
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-family: inherit;
}

.keyword-input-compact:focus {
  outline: none;
  border-color: var(--color-text-light);
}

.keyword-input-compact::placeholder {
  color: var(--color-text-muted);
  font-style: italic;
}

/* Merchant Tags */
.merchant-tags-compact {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  min-height: 1.25rem;
}

.tag-micro {
  background: var(--color-background-light);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: var(--color-text);
}

.text-micro-muted {
  color: var(--color-text-muted);
  font-size: 0.6875rem;
  font-style: italic;
}

/* No Subcategories */
.no-subcats-compact {
  text-align: center;
  padding: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-small {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.btn:hover {
  background: var(--color-background-dark);
}

/* Responsive */
@media (max-width: 48rem) {
  .categories-compact-grid {
    grid-template-columns: 1fr;
  }
}
</style>