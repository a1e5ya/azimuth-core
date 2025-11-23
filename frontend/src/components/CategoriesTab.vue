<template>
  <div class="categories-layout">
    
    <!-- ALWAYS show sidebar if we have types -->
    <div v-if="typeCategories.length > 0" class="vertical-tabs">
      <button
        v-for="type in typeCategories"
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
    
    <!-- Main Content Area -->
    <div class="categories-scroll-container" :class="{ 'no-sidebar': typeCategories.length === 0 }" ref="scrollContainer">
      
      <!-- Top Action Menu (ALWAYS visible when categories exist) -->
      <div v-if="typeCategories.length > 0" class="add-category-button">
        <button 
          class="btn-menu-dots always-visible"
          @click="showCreateMenu = !showCreateMenu"
        >
          <AppIcon name="menu-dots" size="small" />
        </button>
        
        <!-- Retrain Button (only if trained categories exist) -->
        <button 
          v-if="trainedCategories.length > 0"
          class="btn btn-small" 
          @click="startTraining"
          :disabled="training"
          title="Retrain all categories"
        >
          <AppIcon name="graduation-cap" size="small" />
          {{ training ? 'Training...' : 'Retrain' }}
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

      <!-- STATE 1: No transactions - Show drop zone -->
      <div v-if="!hasTransactions" class="empty-state-wrapper">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <div>Importing training data...</div>
        </div>
        <div v-else 
             class="file-drop-zone" 
             @drop.prevent="handleDrop" 
             @dragover.prevent
             @click="triggerFileInput">
          <AppIcon name="file-add" size="large" />
          <p>Drop training data here or click to browse</p>
          <p class="help-text">CSV files with categories supported</p>
        </div>
        <input 
          ref="fileInput" 
          type="file" 
          accept=".csv,.xlsx"
          multiple
          @change="handleFileSelect"
          style="display: none"
        >
      </div>

      <!-- STATE 2: Has transactions but not trained - Show Start Training button -->
      <div v-else-if="hasTransactions && trainedCategories.length === 0 && typeCategories.length > 0" class="empty-categories">
        <AppIcon name="graduation-cap" size="large" />
        <h3>Ready to Train Categories</h3>
        <p>You have {{ transactionCount }} transactions ready for training.</p>
        <button class="btn btn-primary" @click="startTraining" :disabled="training">
          {{ training ? 'Training...' : 'Start Training' }}
        </button>
        
        <div v-if="training" class="training-status">
          <div class="status-text">{{ trainingMessage }}</div>
        </div>
      </div>

      <!-- STATE 3: Trained categories exist - Show category tree -->
      <div v-else-if="typeCategories.length > 0">
        <!-- Training Status Banner (only when actively training) -->
        <div v-if="training" class="training-banner">
          <div class="training-content">
            <AppIcon name="graduation-cap" size="medium" />
            <div class="training-text">
              <div class="training-message">{{ trainingMessage }}</div>
            </div>
          </div>
        </div>
        
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <div>Loading categories...</div>
        </div>

        <!-- Category Tree -->
        <div v-else class="all-categories">
          <section
            v-for="type in typeCategories"
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
                      @blur="updateKeywords(subcat.id, $event.target.value)"
                      @keyup.enter="$event.target.blur()"
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
              v-for="type in sortedTypes" 
              :key="type.id"
              class="type-row"
            >
              <div class="type-info">
                <AppIcon :name="type.icon" size="medium" :style="{ color: type.color }" />
                <span>{{ type.name }}</span>
              </div>
              <div class="type-actions">
                <button class="btn btn-small" @click="handleEdit(type); showEditTypesModal = false">
                  Edit
                </button>
                <button class="btn btn-small btn-danger" @click="handleDelete(type); showEditTypesModal = false">
                  Delete
                </button>
              </div>
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
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
  props: {
    // Accept active tab prop to detect when this tab is shown
    isActive: {
      type: Boolean,
      default: false
    }
  },
  emits: ['add-chat-message'],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    const categoryStore = useCategoryStore()
    
    const allCategories = ref([])
    const loading = ref(false)
    const activeTypeId = ref(null)
    const scrollContainer = ref(null)
    const crudComponent = ref(null)
    const showCreateMenu = ref(false)
    const showEditTypesModal = ref(false)
    const fileInput = ref(null)
    const hasTransactions = ref(false)
    const transactionCount = ref(0)
    const training = ref(false)
    const trainingMessage = ref('')
    let scrollTimeout = null

    // Type categories (level 0 - INCOME, EXPENSES, etc)
    const typeCategories = computed(() => {
      const types = (allCategories.value || []).filter(cat => !cat.parent_id)
      const order = ['income', 'expenses', 'transfers', 'targets']
      
      return [...types].sort((a, b) => {
        const aIndex = order.indexOf(a.code)
        const bIndex = order.indexOf(b.code)
        return aIndex - bIndex
      })
    })

    const categoryPatterns = ref({})

    // Trained categories (subcategories with training patterns)
    const trainedCategories = computed(() => {
      const trained = []
      
      for (const type of allCategories.value) {
        if (!type.children) continue
        
        for (const mainCat of type.children) {
          if (mainCat.children) {
            for (const subCat of mainCat.children) {
              // Check if has training merchants or keywords
              const patterns = categoryPatterns.value[subCat.id]
              if (patterns && (patterns.merchants?.length > 0 || patterns.keywords?.length > 0)) {
                trained.push(subCat)
              }
            }
          }
        }
      }
      
      console.log('🎯 Trained categories:', trained.length, 'Has transactions:', hasTransactions.value, 'Transaction count:', transactionCount.value)
      
      return trained
    })

    const sortedTypes = computed(() => {
      return typeCategories.value
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

    async function checkTransactions() {
      try {
        const response = await axios.get(`${API_BASE}/transactions/summary`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        hasTransactions.value = response.data.total_transactions > 0
        transactionCount.value = response.data.total_transactions || 0
        console.log('📊 Transaction check:', hasTransactions.value, transactionCount.value)
      } catch (error) {
        console.error('Failed to check transactions:', error)
      }
    }

    async function loadCategories() {
      loading.value = true
      
      try {
        const response = await axios.get(`${API_BASE}/categories/tree`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        
        allCategories.value = response.data.tree || []
        console.log('✅ Categories loaded:', allCategories.value.length)
        
        if (typeCategories.value.length > 0 && !activeTypeId.value) {
          activeTypeId.value = typeCategories.value[0].id
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

    async function startTraining() {
      training.value = true
      trainingMessage.value = 'Starting training...'
      
      try {
        const response = await axios.post(`${API_BASE}/categories/train`, {}, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        
        trainingMessage.value = `Trained ${response.data.trained_count} categories!`
        
        emit('add-chat-message', {
          message: 'Category training complete',
          response: response.data.message
        })
        
        // Auto-refresh
        await loadCategories()
        await loadAllPatterns()
        
        setTimeout(() => {
          training.value = false
        }, 2000)
        
      } catch (error) {
        console.error('Training failed:', error)
        trainingMessage.value = 'Training failed'
        training.value = false
        
        emit('add-chat-message', {
          response: 'Training failed. Please try again.'
        })
      }
    }

    function triggerFileInput() {
      fileInput.value?.click()
    }

    function handleFileSelect(event) {
      const files = Array.from(event.target.files)
      processFiles(files)
      event.target.value = ''
    }

    function handleDrop(event) {
      const files = Array.from(event.dataTransfer.files)
      const validFiles = files.filter(f => 
        f.name.toLowerCase().endsWith('.csv') || 
        f.name.toLowerCase().endsWith('.xlsx')
      )
      processFiles(validFiles)
    }

    async function processFiles(files) {
      if (!files || files.length === 0) return

      loading.value = true

      try {
        for (const file of files) {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('import_mode', 'training')
          formData.append('auto_categorize', 'true')

          await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000
          })

          console.log(`✅ Imported: ${file.name}`)
        }

        await checkTransactions()
        await loadCategories()
        
        emit('add-chat-message', {
          message: `Imported ${files.length} file(s)`,
          response: 'Training data imported! Click "Start Training" to extract patterns.'
        })
        
      } catch (error) {
        console.error('Import failed:', error)
        emit('add-chat-message', {
          response: 'Import failed. Please try again.'
        })
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
      crudComponent.value.createCategory(null, false)
      showCreateMenu.value = false
    }

    function handleEditTypes() {
      showEditTypesModal.value = true
      showCreateMenu.value = false
    }

    async function handleCategoryUpdated() {
      await loadCategories()
      await loadAllPatterns()
    }

    async function handleCategoryDeleted() {
      await loadCategories()
    }

    function addChatMessage(messageData) {
      emit('add-chat-message', messageData)
    }

    async function loadCategoryPatterns(subcategoryId) {
      try {
        const response = await axios.get(
          `${API_BASE}/categories/${subcategoryId}/patterns`,
          { headers: { Authorization: `Bearer ${authStore.token}` } }
        )
        categoryPatterns.value[subcategoryId] = response.data
      } catch (error) {
        console.error('Failed to load patterns:', error)
      }
    }

    async function loadAllPatterns() {
      for (const type of typeCategories.value) {
        for (const cat of type.children || []) {
          for (const subcat of cat.children || []) {
            await loadCategoryPatterns(subcat.id)
          }
        }
      }
    }

    function getKeywords(subcategoryId) {
      return categoryPatterns.value[subcategoryId]?.keywords?.join(', ') || ''
    }

    function getMerchants(subcategoryId) {
      return categoryPatterns.value[subcategoryId]?.merchants || []
    }

    async function updateKeywords(subcategoryId, value) {
      const keywords = value.split(',').map(k => k.trim()).filter(k => k)
      
      try {
        await axios.put(
          `${API_BASE}/categories/${subcategoryId}/keywords`,
          keywords,
          { headers: { Authorization: `Bearer ${authStore.token}` } }
        )
        
        // Update local cache
        if (!categoryPatterns.value[subcategoryId]) {
          categoryPatterns.value[subcategoryId] = {}
        }
        categoryPatterns.value[subcategoryId].keywords = keywords
        
        console.log('✅ Keywords updated')
      } catch (error) {
        console.error('Failed to update keywords:', error)
      }
    }

    // Watch for tab becoming active - reload data
    watch(() => props.isActive, async (isActive) => {
      if (isActive) {
        console.log('🔄 Categories tab became active')
        await checkTransactions()
        await loadCategories()
        await loadAllPatterns()
      }
    })

    watch(allCategories, async (newCats) => {
      if (typeCategories.value.length > 0) {
        await loadAllPatterns()
      }
    })

    onMounted(async () => {
      await checkTransactions()
      await loadCategories()
      scrollContainer.value?.addEventListener('scroll', handleScroll)
    })

    onUnmounted(() => {
      if (scrollTimeout) clearTimeout(scrollTimeout)
      scrollContainer.value?.removeEventListener('scroll', handleScroll)
    })

    return {
      allCategories,
      typeCategories,
      trainedCategories,
      sortedTypes,
      loading,
      activeTypeId,
      scrollContainer,
      crudComponent,
      showCreateMenu,
      showEditTypesModal,
      fileInput,
      hasTransactions,
      transactionCount,
      training,
      trainingMessage,
      hexToRgba,
      scrollToType,
      handleScroll,
      loadCategories,
      checkTransactions,
      startTraining,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
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
.categories-scroll-container {
  flex: 1;
  padding: var(--gap-large);
  margin-left: 4rem;
}

.categories-scroll-container.no-sidebar {
  margin-left: 0;
}

.empty-state-wrapper {
  padding: var(--gap-xxl);
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.empty-categories {
  padding: var(--gap-xxl);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--gap-standard);
  min-height: 50vh;
  text-align: center;
}

.empty-categories h3 {
  margin: 0;
  font-size: var(--text-large);
}

.empty-categories p {
  color: var(--color-text-muted);
  margin: 0;
}

.training-status {
  margin-top: var(--gap-standard);
}

.status-text {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.file-drop-zone {
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  padding: var(--gap-large);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-background-light);
  max-width: 30rem;
}

.file-drop-zone:hover {
  border-color: var(--color-button-active);
  background: rgba(0, 0, 0, 0.02);
}

.file-drop-zone p {
  margin: var(--gap-small) 0;
}

.help-text {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.training-banner {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  box-shadow: var(--shadow);
}

.training-content {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
}

.training-text {
  flex: 1;
}

.training-message {
  font-weight: 600;
  font-size: var(--text-small);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--gap-xxl);
  gap: var(--gap-standard);
  color: var(--color-text-muted);
}

.loading-spinner {
  font-size: 2rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.add-category-button {
  display: flex;
  justify-content: flex-end;
  gap: var(--gap-small);
  margin-bottom: var(--gap-standard);
  position: relative;
}

.btn-menu-dots {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  transition: all 0.2s;
  color: var(--color-text-light);
}

.btn-menu-dots.always-visible {
  opacity: 1 !important;
  color: var(--color-text);
}

.btn-menu-dots:hover {
  opacity: 1 !important;
  background: var(--color-background-dark);
  color: var(--color-text);
}

.create-dropdown {
  position: absolute;
  top: calc(100% + 0.25rem);
  right: 0;
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

.type-actions {
  display: flex;
  gap: var(--gap-small);
}

.categories-layout {
  display: flex;
  min-height: 100%;
}

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

.categories-scroll-container {
  flex: 1;
  padding: var(--gap-large);
  margin-left: 4rem;
}

.all-categories {
  margin: 0 auto;
}

.type-section {
  margin-bottom: 3rem;
  scroll-margin-top: 20px;
}

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
</style>