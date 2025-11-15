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
        <button class="btn btn-icon" @click="showCreateMenu = !showCreateMenu">
          <AppIcon name="plus" size="medium" />
        </button>
        
        <!-- Create Menu Dropdown -->
        <div v-if="showCreateMenu" class="create-dropdown">
          <button class="create-option" @click="handleCreateType">
            <AppIcon name="apps-add" size="small" />
            <span>Add Type</span>
          </button>
          <button class="create-option" @click="handleEditTypes">
            <AppIcon name="pencil" size="small" />
            <span>Edit Types</span>
          </button>
          <button class="create-option" @click="handleAddMainCategory">
            <AppIcon name="folder-add" size="small" />
            <span>Add Category</span>
          </button>
        </div>
        
        <!-- Backdrop to close menu -->
        <div v-if="showCreateMenu" class="menu-backdrop" @click="showCreateMenu = false"></div>
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
                  @edit="handleEdit(mainCat)"
                  @add="handleAdd(mainCat)"
                  @delete="handleDelete(mainCat)"
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
                      @edit="handleEdit(subcat)"
                      @delete="handleDelete(subcat)"
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
                <button class="btn btn-small" @click="handleAdd(mainCat)">
                  Add Subcategory
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
    
    <!-- Edit Types Modal -->
    <div v-if="showEditTypesModal" class="modal-overlay" @click="showEditTypesModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Edit Types</h3>
          <button class="close-btn" @click="showEditTypesModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <div class="types-list">
            <div 
              v-for="type in sortedCategories" 
              :key="type.id"
              class="type-row"
            >
              <div class="type-info">
                <AppIcon :name="type.icon" size="medium" :style="{ color: type.color }" />
                <span>{{ type.name }}</span>
              </div>
              <button class="btn btn-small" @click="handleEdit(type); showEditTypesModal = false">
                Edit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- CRUD Component -->
    <CategoriesCRUD
      ref="crudComponent"
      @category-updated="handleCategoryUpdated"
      @category-deleted="handleCategoryDeleted"
      @add-chat-message="addChatMessage"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import AppIcon from './AppIcon.vue'
import ActionsMenu from './ActionsMenu.vue'
import CategoriesCRUD from './CategoriesCRUD.vue'

export default {
  name: 'CategoriesTab',
  components: { 
    AppIcon,
    ActionsMenu,
    CategoriesCRUD
  },
  emits: ['add-chat-message'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    
    const categories = ref([])
    const loading = ref(false)
    const activeTypeId = ref(null)
    const scrollContainer = ref(null)
    const crudComponent = ref(null)
    const showCreateMenu = ref(false)
    const showEditTypesModal = ref(false)
    let scrollTimeout = null

    const sortedCategories = computed(() => {
      const cats = categories.value || []
      const order = ['income', 'expenses', 'transfers', 'targets']
      
      return [...cats].sort((a, b) => {
        const aIndex = order.indexOf(a.code)
        const bIndex = order.indexOf(b.code)
        return aIndex - bIndex
      })
    })

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
      
      setTimeout(() => {
        activeTypeId.value = null
      }, 1000)
    }

    function handleScroll() {
      if (scrollTimeout) clearTimeout(scrollTimeout)
      
      scrollTimeout = setTimeout(() => {
        const sections = document.querySelectorAll('.type-section')
        let currentSection = null
        
        sections.forEach(section => {
          const rect = section.getBoundingClientRect()
          if (rect.top <= window.innerHeight / 2 && rect.bottom > 100) {
            currentSection = section.id.replace('type-', '')
          }
        })

        if (currentSection && currentSection !== activeTypeId.value) {
          activeTypeId.value = currentSection
        }
      }, 100)
    }

    async function loadCategories() {
      loading.value = true
      
      try {
        const response = await axios.get(`${API_BASE}/categories/tree`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        
        categories.value = response.data.tree || []
        console.log('✅ Categories loaded:', categories.value.length)
        
        if (categories.value.length > 0 && !activeTypeId.value) {
          activeTypeId.value = categories.value[0].id
        }
        
      } catch (error) {
        console.error('❌ Failed to load categories:', error)
        
        if (error.response?.status === 401) {
          await authStore.verifyToken()
        }
      } finally {
        loading.value = false
      }
    }

    function handleEdit(category) {
      crudComponent.value.editCategory(category)
    }

    function handleDelete(category) {
      crudComponent.value.deleteCategory(category)
    }

    function handleAdd(parent) {
      crudComponent.value.createCategory(parent)
    }

    function handleAddMainCategory() {
      crudComponent.value.createCategory(null, true)
      showCreateMenu.value = false
    }

    function handleCreateType() {
      crudComponent.value.createCategory(null)
      showCreateMenu.value = false
    }

    function handleEditTypes() {
      // Show modal with list of all types to edit
      showEditTypesModal.value = true
      showCreateMenu.value = false
    }

    async function handleCategoryUpdated() {
      await loadCategories()
    }

    async function handleCategoryDeleted() {
      await loadCategories()
    }

    function addChatMessage(messageData) {
      emit('add-chat-message', messageData)
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
      await loadCategories()
      scrollContainer.value?.addEventListener('scroll', handleScroll)
    })

    onUnmounted(() => {
      if (scrollTimeout) clearTimeout(scrollTimeout)
      scrollContainer.value?.removeEventListener('scroll', handleScroll)
    })

    return {
      categories: sortedCategories,
      loading,
      activeTypeId,
      scrollContainer,
      crudComponent,
      showCreateMenu,
      showEditTypesModal,
      hexToRgba,
      scrollToType,
      handleScroll,
      loadCategories,
      handleEdit,
      handleDelete,
      handleAdd,
      handleAddMainCategory,
      handleCreateType,
      handleEditTypes,
      handleCategoryUpdated,
      handleCategoryDeleted,
      addChatMessage,
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
  position: relative;
}

.create-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  background: var(--color-background-light);
  backdrop-filter: blur(1rem);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  z-index: 100;
  min-width: 10rem;
}

.create-option {
  background: none;
  border: none;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
  font-size: var(--text-small);
  color: var(--color-text);
  text-align: left;
  white-space: nowrap;
}

.create-option:hover {
  background: var(--color-background-dark);
}

.menu-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
  background: transparent;
}

.types-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.type-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-small);
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
}

.type-info {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  font-weight: 500;
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