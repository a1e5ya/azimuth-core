<template>
  <div class="tab-content">
    <div class="container">
      <div class="categories-header">
        <h2>Categories Management</h2>
        <div class="header-actions">
          <button class="btn btn-small" @click="showAddModal = true">Add Category</button>
          <button class="btn btn-small btn-link" @click="refreshCategories">Refresh</button>
        </div>
      </div>

      <!-- Type Tabs -->
      <div class="type-tabs">
        <button
          v-for="type in categories"
          :key="type.id"
          class="type-tab"
          :class="{ active: selectedTypeId === type.id }"
          @click="selectedTypeId = type.id"
        >
          <AppIcon :name="type.icon" size="medium" />
          {{ type.name }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading categories...</div>
      </div>

      <!-- Categories Grid -->
      <div v-else-if="currentType" class="categories-grid">
        <div
          v-for="mainCat in currentType.children"
          :key="mainCat.id"
          class="main-category-section"
        >
          <!-- Main Category Header -->
          <div class="main-category-header">
            <div class="category-title">
              <AppIcon :name="mainCat.icon" size="large" />
              <h3>{{ mainCat.name }}</h3>
            </div>
            <div class="category-actions">
              <button class="btn btn-small btn-link" @click="editCategory(mainCat)">Edit</button>
              <button class="btn btn-small btn-link" @click="addSubcategory(mainCat)">Add Sub</button>
              <button class="btn btn-small btn-link" @click="deleteCategory(mainCat)">Delete</button>
            </div>
          </div>

          <!-- Subcategories -->
          <div v-if="mainCat.children && mainCat.children.length > 0" class="subcategories-grid">
            <div
              v-for="subcat in mainCat.children"
              :key="subcat.id"
              class="subcategory-card"
            >
              <div class="subcat-header">
                <AppIcon :name="subcat.icon" size="medium" />
                <span class="subcat-name">{{ subcat.name }}</span>
              </div>
              
              <div class="subcat-keywords">
                <label>Keywords:</label>
                <input
                  type="text"
                  class="keyword-input"
                  placeholder="coffee, starbucks..."
                  :value="getKeywords(subcat.id)"
                  @change="updateKeywords(subcat.id, $event.target.value)"
                >
              </div>

              <div class="subcat-merchants">
                <label>Merchants:</label>
                <div class="merchant-list">
                  <span v-for="merchant in getMerchants(subcat.id)" :key="merchant" class="merchant-tag">
                    {{ merchant }}
                  </span>
                  <span v-if="!getMerchants(subcat.id).length" class="text-muted">
                    None yet
                  </span>
                </div>
              </div>

              <div class="subcat-actions">
                <button class="btn btn-small btn-link" @click="editCategory(subcat)">Edit</button>
                <button class="btn btn-small btn-link" @click="deleteCategory(subcat)">Delete</button>
              </div>
            </div>
          </div>

          <div v-else class="no-subcategories">
            <button class="btn btn-small" @click="addSubcategory(mainCat)">
              Add First Subcategory
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

export default {
  name: 'CategoriesTab',
  components: { AppIcon },
  setup() {
    const categoryStore = useCategoryStore()
    const selectedTypeId = ref(null)
    const showAddModal = ref(false)

    const categories = computed(() => categoryStore.categories)
    const loading = computed(() => categoryStore.loading)

    const currentType = computed(() => {
      if (!selectedTypeId.value || !categories.value) return null
      return categories.value.find(t => t.id === selectedTypeId.value)
    })

    async function refreshCategories() {
      await categoryStore.loadCategories()
      if (categories.value && categories.value.length > 0 && !selectedTypeId.value) {
        selectedTypeId.value = categories.value[0].id
      }
    }

    function editCategory(category) {
      console.log('Edit:', category.name)
    }

    function deleteCategory(category) {
      console.log('Delete:', category.name)
    }

    function addSubcategory(parent) {
      console.log('Add subcategory to:', parent.name)
    }

    function getKeywords(categoryId) {
      return ''
    }

    function updateKeywords(categoryId, keywords) {
      console.log('Update keywords:', categoryId, keywords)
    }

    function getMerchants(categoryId) {
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
      showAddModal,
      refreshCategories,
      editCategory,
      deleteCategory,
      addSubcategory,
      getKeywords,
      updateKeywords,
      getMerchants
    }
  }
}
</script>

<style scoped>
.categories-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-large);
}

.categories-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--gap-small);
}

.type-tabs {
  display: flex;
  gap: var(--gap-small);
  margin-bottom: var(--gap-large);
  border-bottom: 2px solid var(--color-background-dark);
}

.type-tab {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: var(--gap-small) var(--gap-standard);
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
  background: var(--color-background-light);
}

.type-tab.active {
  color: var(--color-text);
  border-bottom-color: var(--color-text);
  font-weight: 600;
}

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

.categories-grid {
  display: flex;
  flex-direction: column;
  gap: var(--gap-large);
}

.main-category-section {
  background: var(--color-background-light);
  padding: var(--gap-standard);
  border-radius: var(--radius);
}

.main-category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  padding-bottom: var(--gap-small);
  border-bottom: 1px solid var(--color-background-dark);
}

.category-title {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.category-title h3 {
  margin: 0;
  font-size: var(--text-medium);
}

.category-actions {
  display: flex;
  gap: var(--gap-small);
}

.subcategories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  gap: var(--gap-standard);
}

.subcategory-card {
  background: var(--color-background);
  padding: var(--gap-standard);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.subcat-header {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  margin-bottom: var(--gap-small);
}

.subcat-name {
  font-weight: 600;
  font-size: var(--text-small);
}

.subcat-keywords,
.subcat-merchants {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.subcat-keywords label,
.subcat-merchants label {
  font-size: var(--text-small);
  color: var(--color-text-muted);
  font-weight: 500;
}

.keyword-input {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  font-size: var(--text-small);
  font-family: inherit;
}

.keyword-input:focus {
  outline: none;
  border-color: var(--color-text-light);
}

.merchant-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  min-height: 1.5rem;
}

.merchant-tag {
  background: var(--color-background-light);
  padding: 0.125rem 0.375rem;
  border-radius: var(--radius);
  font-size: var(--text-small);
  color: var(--color-text);
}

.text-muted {
  color: var(--color-text-muted);
  font-size: var(--text-small);
  font-style: italic;
}

.subcat-actions {
  display: flex;
  gap: var(--gap-small);
  justify-content: flex-end;
  margin-top: var(--gap-small);
  padding-top: var(--gap-small);
  border-top: 1px solid var(--color-background-light);
}

.no-subcategories {
  text-align: center;
  padding: var(--gap-standard);
  color: var(--color-text-muted);
}
</style>