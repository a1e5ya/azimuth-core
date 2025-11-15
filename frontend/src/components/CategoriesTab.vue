<template>
  <div class="categories-layout">
    
    <!-- Vertical Type Tabs - Left Side -->
    <div class="vertical-tabs">
      <button
        v-for="type in categories"
        :key="type.id"
        class="vertical-tab"
        :class="{ active: activeTypeId === type.id }"
        :style="{ '--tab-color': type.color }"
        @click="scrollToType(type.id)"
      >
        <span class="vertical-text">{{ type.name }}</span>
        <AppIcon :name="type.icon" size="medium" />
      </button>
    </div>
    

    <!-- Scrollable Content - All Categories -->
    <div class="categories-scroll-container" ref="scrollContainer">
      <div class="add-category-button" style="margin-bottom: 1rem;">
      <button class=" btn-plus" @click="showAddOwnerModal = true">
        <AppIcon name="plus" size="medium" />
      </button>
      </div>
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading categories...</div>
      </div>

      <!-- All Type Sections -->
      <div v-else class="all-categories">
        <section
          v-for="type in categories"
          :key="type.id"
          :id="`type-${type.id}`"
          class="type-section"
        >
          <div class="categories-grid">
            <div
              v-for="mainCat in type.children"
              :key="mainCat.id"
              class="category-card"
              :style="{ backgroundColor: hexToRgba(mainCat.color, 0.1) }"
            >
              <div class="category-header">
                <div class="category-title">
                  <AppIcon 
                    :name="mainCat.icon" 
                    size="medium"
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

              <div v-if="mainCat.children && mainCat.children.length > 0" class="subcategories">
                <div
                  v-for="subcat in mainCat.children"
                  :key="subcat.id"
                  class="subcategory"
                  :style="{ backgroundColor: hexToRgba(subcat.color, 0.1) }"
                >
                  <div class="subcat-header">
                    <div class="subcat-title">
                      <AppIcon 
                        :name="subcat.icon" 
                        size="small"
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
                    class="keyword-input"
                    placeholder="keywords..."
                    :value="getKeywords(subcat.id)"
                    @change="updateKeywords(subcat.id, $event.target.value)"
                  >

                  <div class="merchant-tags">
                    <span v-for="merchant in getMerchants(subcat.id)" :key="merchant" class="tag">
                      {{ merchant }}
                    </span>
                    <span v-if="!getMerchants(subcat.id).length" class="text-muted">
                      No merchants
                    </span>
                  </div>
                </div>
              </div>

              <div v-else class="no-subcategories">
                <button class="btn btn-small" @click="addSubcategory(mainCat)">
                  Add Subcategory
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
    const activeTypeId = ref(null)
    const scrollContainer = ref(null)
    let scrollTimeout = null

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

    function hexToRgba(hex, alpha) {
      if (!hex) return 'transparent'
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    function scrollToType(typeId) {
  const section = document.getElementById(`type-${typeId}`)
  if (section) {
    section.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }
  activeTypeId.value = typeId
  
  // Clear active state after scroll animation
  setTimeout(() => {
    activeTypeId.value = null
  }, 1000)
}

    function handleScroll() {
      console.log('🔄 Scroll detected!')
      if (scrollTimeout) clearTimeout(scrollTimeout)
      
      scrollTimeout = setTimeout(() => {
        const sections = document.querySelectorAll('.type-section')
        console.log('📍 Sections found:', sections.length)
        
        let currentSection = null
        
        sections.forEach(section => {
          const rect = section.getBoundingClientRect()
          console.log(section.id, 'rect.top:', rect.top, 'rect.bottom:', rect.bottom)
          // If section top is above middle of screen and bottom is below top bar
          if (rect.top <= window.innerHeight / 2 && rect.bottom > 100) {
            currentSection = section.id.replace('type-', '')
            console.log('✅ Active section:', currentSection)
          }
        })

        if (currentSection && currentSection !== activeTypeId.value) {
          console.log('🎯 Setting active:', currentSection)
          activeTypeId.value = currentSection
        }
      }, 100)
    }

    async function refreshCategories() {
      await categoryStore.loadCategories()
      if (categories.value && categories.value.length > 0 && !activeTypeId.value) {
        activeTypeId.value = categories.value[0].id
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

    function addNewCategory(type) {
      console.log('Add new main category to:', type.name)
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
  scrollContainer.value?.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  if (scrollTimeout) clearTimeout(scrollTimeout)
  scrollContainer.value?.removeEventListener('scroll', handleScroll)
})

    return {
      categories,
      loading,
      activeTypeId,
      scrollContainer,
      hexToRgba,
      scrollToType,
      handleScroll,
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

.add-category-button {
  display: flex;
  justify-content: flex-end;
  margin-bottom: -30px !important;
}

.btn-plus{
    margin: 0;
    background-color: transparent;
    border: none;
    cursor: pointer;
}

.categories-layout {
  display: flex;
  min-height: 100%;
}

/* Vertical Tabs - Left Sidebar */
.vertical-tabs {
  position: fixed;
  left: 0;
  top: 80px;
  height: 100vh;
  width: 4rem;
  background: var(--color-background);
  border-right: 2px solid var(--color-background-dark);
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  padding: 0 0 150px;
  gap: var(--gap-large);
  z-index: 10;
}

.vertical-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--gap-small);
  padding: var(--gap-standard);
  background: none;
  border: none;
  border-left: 3px solid transparent;
  cursor: pointer;
  color: var(--color-text-light);
  transition: all 0.3s;
  position: relative;
}

.vertical-tab:hover {
  color: var(--color-text);
  background: var(--color-background-light);
}

.vertical-tab:hover :deep(.icon-wrapper) {
  color: var(--tab-color);
}

.vertical-tab.active {
  color: var(--color-text);
  border-left-color: var(--tab-color);
  background: var(--color-background-light);
}

.vertical-tab.active :deep(.icon-wrapper) {
  color: var(--tab-color);
}

.vertical-text {
  writing-mode: vertical-lr;
  text-orientation: mixed;
  font-size: var(--text-small);
  font-weight: 500;
  letter-spacing: 0.05em;
  transform: rotate(180deg);
}

/* Scrollable Container */
.categories-scroll-container {
  flex: 1;
  padding: var(--gap-large);
  margin-left: 4rem;
}

.all-categories {
  margin: 0 auto;
}

/* Type Section */
.type-section {
  margin-bottom: 3rem;
  scroll-margin-top: 20px;
}

/* Categories Grid */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--gap-standard);
  grid-auto-flow: dense;
}

.category-card {
  padding: 0.75rem;
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  break-inside: avoid;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-background-dark);
}

.category-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.category-title h4 {
  margin: 0;
  font-size: var(--text-small);
  font-weight: 600;
}

.category-title :deep(.icon-wrapper):hover {
  color: var(--icon-hover-color);
  transition: color 0.2s;
}

/* Subcategories */
.subcategories {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.subcategory {
  padding: 0.5rem;
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.subcat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subcat-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: var(--text-small);
  font-weight: 500;
}

.subcat-title :deep(.icon-wrapper):hover {
  color: var(--icon-hover-color);
  transition: color 0.2s;
}

.keyword-input {
  width: 100%;
  padding: 0.25rem 0.375rem;
  border: 1px solid var(--color-background-dark);
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-family: inherit;
}

.keyword-input:focus {
  outline: none;
  border-color: var(--color-text-light);
}

.keyword-input::placeholder {
  color: var(--color-text-muted);
  font-style: italic;
}

.merchant-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  min-height: 1.25rem;
}

.tag {
  background: var(--color-background-light);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: var(--color-text);
}

.text-muted {
  color: var(--color-text-muted);
  font-size: 0.6875rem;
  font-style: italic;
}

.no-subcategories {
  text-align: center;
  padding: 0.5rem;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  gap: var(--gap-standard);
  color: var(--color-text-light);
}

.loading-spinner {
  font-size: 2rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>