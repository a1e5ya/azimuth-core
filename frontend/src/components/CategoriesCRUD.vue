<!--
  CategoriesCRUD Component - Category Create/Update/Delete Modals
  
  Provides modal dialogs for category management operations:
  - Create Type (top-level category like INCOME, EXPENSES)
  - Create Category (mid-level like Food, Transport)
  - Create Subcategory (bottom-level like Groceries, Fuel)
  - Edit existing category
  - Delete category with transaction relocation
  
  Features:
  - Icon picker with search (300+ fi-rr icons)
  - Color picker
  - Type selector for new categories
  - Delete safety checks (has children? has transactions?)
  - Transaction relocation on delete
  - Loading states
  - Validation
  - Chat notifications on success/error
  
  Events:
  - @category-updated: Category created or edited
  - @category-deleted: Category deleted
  - @add-chat-message: Show message in chat component
  
  Usage:
  <CategoriesCRUD 
    ref="crud"
    @category-updated="refreshCategories"
    @add-chat-message="addMessage"
  />
  
  // Call from parent:
  crud.value.createCategory(parentCategory, isMainCategory)
  crud.value.editCategory(category)
  crud.value.deleteCategory(category)
  
  Category Hierarchy:
  - Type (Level 1): INCOME, EXPENSES, TRANSFERS, TARGETS
  - Category (Level 2): Food, Transport, etc.
  - Subcategory (Level 3): Groceries, Fuel, etc.
-->

<template>
  <div>
    <!-- ============================================================================
         CREATE/EDIT CATEGORY MODAL
         ============================================================================ -->
    <div v-if="editingCategory" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content category-edit-modal" @click.stop>
        <!-- Modal Header -->
        <div class="modal-header">
          <h3>{{ isEditing ? 'Edit Category' : (isCreatingType ? 'Add Type' : (isCreatingMainCategory ? 'Add Category' : 'Add Subcategory')) }}</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          <div class="edit-form">
            <!-- Type Selector (only when creating main category) -->
            <div v-if="isCreatingMainCategory" class="form-group">
              <label>Type *</label>
              <select v-model="selectedTypeId" class="form-input" @change="onTypeChange" required>
                <option value="">Select type...</option>
                <option v-for="type in availableTypes" :key="type.id" :value="type.id">
                  {{ type.name }}
                </option>
              </select>
            </div>

            <!-- Name and Color Row -->
            <div class="form-group-row">
                <!-- Name Input -->
                <div class="form-group">
                <label>Name *</label>
                <input 
                    type="text" 
                    v-model="editForm.name"
                    class="form-input"
                    placeholder=""
                    required
                >
                </div>

                <!-- Color Picker -->
                <div class="form-group">
                <label>Color</label>
                <input 
                    type="color" 
                    v-model="editForm.color"
                    class="form-input color-input"
                >
                </div>
            </div>
            
            <!-- Icon Selector -->
            <div class="form-group">
              <label>Icon</label>
              <div class="icon-selector">
                <!-- Selected Icon Display -->
                <div class="selected-icon">
                  <AppIcon :name="editForm.icon" size="medium" />
                  <span>{{ editForm.icon }}</span>
                </div>
                
                <!-- Icon Picker -->
                <div class="icon-picker">
                  <!-- Search Input -->
                  <div class="icon-search">
                    <input 
                      v-model="iconSearch" 
                      type="text" 
                      placeholder="Search icons..."
                      class="form-input"
                    >
                  </div>
                  
                  <!-- Loading State -->
                  <div v-if="loadingIcons" class="icon-loading">Loading icons...</div>
                  
                  <!-- Icon Grid -->
                  <div v-else class="icon-grid">
                    <div 
                      v-for="icon in filteredIcons" 
                      :key="icon"
                      class="icon-option"
                      :class="{ selected: editForm.icon === icon }"
                      @click="selectIcon(icon)"
                    >
                      <AppIcon :name="icon" size="medium" />
                      <span class="icon-name">{{ icon }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
        
        <!-- Modal Actions -->
        <div class="modal-actions">
          <button 
            class="btn" 
            @click="saveEdit"
            :disabled="saving || !editForm.name || (isCreatingMainCategory && !selectedTypeId)"
          >
            {{ saving ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create') }}
          </button>
          <button class="btn btn-link" @click="closeEditModal" :disabled="saving">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- ============================================================================
         DELETE CONFIRMATION MODAL
         ============================================================================ -->
    <div v-if="deletingCategory" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-content delete-modal" @click.stop>
        <!-- Modal Header -->
        <div class="modal-header">
          <h3>Delete Category</h3>
          <button class="close-btn" @click="closeDeleteModal">×</button>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          <div class="delete-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>Are you sure you want to delete "{{ deletingCategory.name }}"?</strong></p>
              
              <!-- Delete Safety Check Info -->
              <div v-if="deleteCheck" class="delete-info">
                <!-- Has Children Error -->
                <p v-if="deleteCheck.has_children" class="error-text">
                  ❌ This category has subcategories. Please delete subcategories first.
                </p>
                
                <!-- Transaction Count & Move Selector -->
                <div v-if="deleteCheck.transaction_count > 0">
                  <p class="warning-text">
                    {{ deleteCheck.transaction_count }} transactions will be moved
                  </p>
                  
                  <!-- Move To Category Selector -->
                  <div class="form-group" style="margin-top: 1rem;">
                    <label>Move transactions to:</label>
                    <select v-model="moveToSubcategoryId" class="form-input" required>
                      <option value="">Select subcategory...</option>
                      <option value="uncategorized">Uncategorized</option>
                      
                      <!-- Nested Category Options -->
                      <template v-for="type in availableTypesForMove" :key="type.id">
                        <template v-for="cat in type.children" :key="cat.id">
                          <option 
                            v-for="subcat in cat.children"
                            :key="subcat.id"
                            :value="subcat.id"
                            :disabled="subcat.id === deletingCategory.id"
                          >
                            {{ type.name }} → {{ cat.name }} → {{ subcat.name }}
                          </option>
                        </template>
                      </template>
                    </select>
                  </div>
                </div>
                
                <!-- Empty Category Message -->
                <p v-if="deleteCheck.can_delete && deleteCheck.transaction_count === 0">
                  This category is empty and can be safely deleted.
                </p>
              </div>
              
              <!-- Warning -->
              <p v-if="deleteCheck?.can_delete">This action cannot be undone.</p>
            </div>
          </div>
        </div>
        
        <!-- Modal Actions -->
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmDelete"
            :disabled="deleting || !deleteCheck?.can_delete || (deleteCheck?.transaction_count > 0 && !moveToSubcategoryId)"
          >
            {{ deleting ? 'Deleting...' : 'Yes, Delete' }}
          </button>
          <button class="btn btn-link" @click="closeDeleteModal" :disabled="deleting">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import AppIcon from './AppIcon.vue'

export default {
  name: 'CategoriesCRUD',
  components: { AppIcon },
  
  emits: ['category-updated', 'category-deleted', 'add-chat-message'],
  
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    const authStore = useAuthStore()
    
    // ========================================
    // STATE
    // ========================================
    
    /** @type {Ref<Object|null>} Category being edited/created */
    const editingCategory = ref(null)
    
    /** @type {Ref<Object|null>} Category being deleted */
    const deletingCategory = ref(null)
    
    /** @type {Ref<Object|null>} Delete safety check results */
    const deleteCheck = ref(null)
    
    /** @type {Ref<string>} Target category ID for transaction relocation */
    const moveToSubcategoryId = ref('')
    
    /** @type {Ref<boolean>} Saving state */
    const saving = ref(false)
    
    /** @type {Ref<boolean>} Deleting state */
    const deleting = ref(false)
    
    /** @type {Ref<string>} Icon search query */
    const iconSearch = ref('')
    
    /** @type {Ref<Array<string>>} Available icon names */
    const availableIcons = ref([])
    
    /** @type {Ref<boolean>} Loading icons state */
    const loadingIcons = ref(false)
    
    /** @type {Ref<Array>} Available type categories (INCOME, EXPENSES, etc.) */
    const availableTypes = ref([])
    
    /** @type {Ref<string>} Selected type ID when creating main category */
    const selectedTypeId = ref('')
    
    /** @type {Ref<Object>} Edit form data */
    const editForm = ref({
      name: '',
      icon: '',
      color: ''
    })

    // ========================================
    // COMPUTED
    // ========================================
    
    /**
     * Check if editing existing category (has ID)
     * @type {ComputedRef<boolean>}
     */
    const isEditing = computed(() => editingCategory.value?.id !== undefined)
    
    /**
     * Check if creating new type (top level, no parent, not flagged as main category)
     * @type {ComputedRef<boolean>}
     */
    const isCreatingType = computed(() => 
      !isEditing.value && 
      editingCategory.value?.parent_id === null && 
      !editingCategory.value?.isMainCategory
    )
    
    /**
     * Check if creating main category (mid level, needs type selection)
     * @type {ComputedRef<boolean>}
     */
    const isCreatingMainCategory = computed(() => 
      !isEditing.value && 
      editingCategory.value?.isMainCategory === true
    )
    
    /**
     * Check if creating subcategory (bottom level, has parent)
     * @type {ComputedRef<boolean>}
     */
    const isCreatingSubcategory = computed(() => 
      !isEditing.value && 
      editingCategory.value?.parent_id !== null && 
      !editingCategory.value?.isMainCategory
    )
    
    /**
     * Available types for move-to selector
     * @type {ComputedRef<Array>}
     */
    const availableTypesForMove = computed(() => availableTypes.value)

    // ========================================
    // TYPE HANDLING
    // ========================================
    
    /**
     * Handle type selection change
     * 
     * When creating main category, sets parent_id and inherits type color.
     */
    const onTypeChange = () => {
      const selectedType = availableTypes.value.find(t => t.id === selectedTypeId.value)
      if (selectedType) {
        editingCategory.value.parent_id = selectedTypeId.value
        editForm.value.color = selectedType.color || '#94a3b8'
      }
    }

    /**
     * Load available types from backend
     * 
     * Fetches category tree and filters for top-level types.
     */
    const loadTypes = async () => {
      try {
        const response = await axios.get(`${API_BASE}/categories/tree`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        
        availableTypes.value = (response.data.tree || []).filter(cat => !cat.parent_id)
        console.log('✅ Types loaded:', availableTypes.value.length)
      } catch (error) {
        console.error('Failed to load types:', error)
      }
    }

    // ========================================
    // ICON HANDLING
    // ========================================
    
    /**
     * Filter icons by search query
     * @type {ComputedRef<Array<string>>}
     */
    const filteredIcons = computed(() => {
      if (!iconSearch.value) return availableIcons.value
      const search = iconSearch.value.toLowerCase()
      return availableIcons.value.filter(icon => icon.toLowerCase().includes(search))
    })

    /**
     * Load available icons from assets
     * 
     * Uses Vite's import.meta.glob to discover all fi-rr-*.svg files.
     * Extracts icon names (without fi-rr- prefix and .svg extension).
     */
    const loadAvailableIcons = async () => {
      loadingIcons.value = true
      try {
        const iconModules = import.meta.glob('@/assets/icons/fi-rr-*.svg')
        const iconNames = Object.keys(iconModules).map(path => {
          const filename = path.split('/').pop()
          return filename.replace('fi-rr-', '').replace('.svg', '')
        })
        availableIcons.value = iconNames.sort()
        console.log('✅ Loaded icons:', availableIcons.value.length)
      } catch (error) {
        console.error('Failed to load icons:', error)
      } finally {
        loadingIcons.value = false
      }
    }

    /**
     * Select an icon from picker
     * 
     * @param {string} icon - Icon name
     */
    const selectIcon = (icon) => {
      editForm.value.icon = icon
      iconSearch.value = ''
    }

    // ========================================
    // MODAL CONTROLS
    // ========================================
    
    /**
     * Open create category modal
     * 
     * @param {Object|null} parent - Parent category (null for type creation)
     * @param {boolean} isMainCategory - True if creating main category (needs type selection)
     * 
     * Default values:
     * - Type: icon='apps-sort', color='#94a3b8'
     * - Main category: icon='circle', inherits type color
     * - Subcategory: icon='circle', inherits parent color
     */
    const createCategory = (parent = null, isMainCategory = false) => {
      editingCategory.value = { 
        parent_id: parent?.id || null,
        isMainCategory: isMainCategory 
      }
      
      if (isMainCategory) {
        // Creating main category - must select type
        selectedTypeId.value = ''
        editForm.value = {
          name: '',
          icon: 'circle',
          color: '#94a3b8'
        }
      } else if (!parent) {
        // Creating a type (no parent)
        editForm.value = {
          name: '',
          icon: 'apps-sort',
          color: '#94a3b8'
        }
      } else {
        // Creating a subcategory
        editForm.value = {
          name: '',
          icon: 'circle',
          color: parent?.color || '#94a3b8'
        }
      }
      
      iconSearch.value = ''
    }

    /**
     * Open edit category modal
     * 
     * @param {Object} category - Category to edit
     */
    const editCategory = (category) => {
      editingCategory.value = { ...category }
      editForm.value = {
        name: category.name || '',
        icon: category.icon || 'circle',
        color: category.color || '#94a3b8'
      }
      iconSearch.value = ''
    }

    /**
     * Close edit modal and reset form
     */
    const closeEditModal = () => {
      editingCategory.value = null
      editForm.value = { name: '', icon: '', color: '' }
      iconSearch.value = ''
      selectedTypeId.value = ''
    }

    // ========================================
    // SAVE/UPDATE
    // ========================================
    
    /**
     * Save category (create or update)
     * 
     * Process:
     * 1. Validate form data
     * 2. Call POST (create) or PUT (update) endpoint
     * 3. Emit success message
     * 4. Emit category-updated event
     * 5. Close modal
     * 
     * Validation:
     * - Name is required
     * - Type selection required when creating main category
     */
    const saveEdit = async () => {
      if (!editForm.value.name || saving.value) return
      
      // Validate type selection if needed
      if (isCreatingMainCategory.value && !selectedTypeId.value) {
        emit('add-chat-message', {
          response: 'Please select a type'
        })
        return
      }
      
      saving.value = true
      
      try {
        let response
        
        if (isEditing.value) {
          // Update existing category
          response = await axios.put(
            `${API_BASE}/categories/${editingCategory.value.id}`,
            editForm.value,
            { headers: { Authorization: `Bearer ${authStore.token}` }}
          )
        } else {
          // Create new category
          response = await axios.post(
            `${API_BASE}/categories/`,
            {
              ...editForm.value,
              parent_id: editingCategory.value.parent_id
            },
            { headers: { Authorization: `Bearer ${authStore.token}` }}
          )
        }
        
        console.log('✅ Category saved:', response.data)
        
        emit('add-chat-message', {
          message: isEditing.value ? 'Category updated' : 'Category created',
          response: isEditing.value 
            ? `"${editForm.value.name}" has been updated!`
            : `"${editForm.value.name}" has been created!`
        })
        
        closeEditModal()
        emit('category-updated')
        
      } catch (error) {
        console.error('Failed to save category:', error)
        emit('add-chat-message', {
          response: error.response?.data?.detail || 'Failed to save category. Please try again.'
        })
      } finally {
        saving.value = false
      }
    }

    // ========================================
    // DELETE
    // ========================================
    
    /**
     * Open delete confirmation modal
     * 
     * Process:
     * 1. Set category to delete
     * 2. Check if category can be deleted (no children)
     * 3. Check transaction count
     * 4. Show modal with results
     * 
     * @param {Object} category - Category to delete
     */
    const deleteCategory = async (category) => {
      deletingCategory.value = category
      deleteCheck.value = null
      moveToSubcategoryId.value = ''
      
      try {
        const response = await axios.get(
          `${API_BASE}/categories/${category.id}/check-delete`,
          { headers: { Authorization: `Bearer ${authStore.token}` }}
        )
        
        deleteCheck.value = response.data
      } catch (error) {
        console.error('Failed to check delete:', error)
        deleteCheck.value = { 
          can_delete: false, 
          warning_message: 'Failed to check category' 
        }
      }
    }

    /**
     * Close delete modal and reset state
     */
    const closeDeleteModal = () => {
      deletingCategory.value = null
      deleteCheck.value = null
      moveToSubcategoryId.value = ''
    }

    /**
     * Confirm and execute category deletion
     * 
     * Process:
     * 1. Validate move-to selection if needed
     * 2. Call DELETE endpoint with move_to_category_id param
     * 3. Emit success message
     * 4. Emit category-deleted event
     * 5. Close modal
     * 
     * Safety:
     * - Cannot delete if has children
     * - Must specify move-to category if has transactions
     */
    const confirmDelete = async () => {
      if (!deletingCategory.value || deleting.value || !deleteCheck.value?.can_delete) return
      
      // Validate move-to selection if there are transactions
      if (deleteCheck.value.transaction_count > 0 && !moveToSubcategoryId.value) {
        emit('add-chat-message', {
          response: 'Please select where to move transactions'
        })
        return
      }
      
      deleting.value = true
      
      try {
        // Send move_to_category_id as query parameter
        const params = moveToSubcategoryId.value 
          ? `?move_to_category_id=${moveToSubcategoryId.value}` 
          : ''
        
        const response = await axios.delete(
          `${API_BASE}/categories/${deletingCategory.value.id}${params}`,
          { headers: { Authorization: `Bearer ${authStore.token}` }}
        )
        
        console.log('✅ Category deleted:', response.data)
        
        emit('add-chat-message', {
          message: 'Category deleted',
          response: `"${deletingCategory.value.name}" has been deleted.`
        })
        
        emit('category-deleted')
        closeDeleteModal()
        
      } catch (error) {
        console.error('Failed to delete category:', error)
        emit('add-chat-message', {
          response: error.response?.data?.detail || 'Failed to delete category. Please try again.'
        })
      } finally {
        deleting.value = false
      }
    }

    // ========================================
    // INITIALIZATION
    // ========================================
    
    onMounted(() => {
      loadAvailableIcons()
      loadTypes()
    })

    // ========================================
    // EXPOSED API
    // ========================================
    
    return {
      // State
      editingCategory,
      deletingCategory,
      deleteCheck,
      moveToSubcategoryId,
      saving,
      deleting,
      editForm,
      
      // Computed
      isEditing,
      isCreatingType,
      isCreatingMainCategory,
      isCreatingSubcategory,
      
      // Icon handling
      iconSearch,
      filteredIcons,
      loadingIcons,
      selectIcon,
      
      // Type handling
      availableTypes,
      availableTypesForMove,
      selectedTypeId,
      onTypeChange,
      
      // Actions
      createCategory,
      editCategory,
      closeEditModal,
      saveEdit,
      deleteCategory,
      closeDeleteModal,
      confirmDelete
    }
  }
}
</script>

<style scoped>
/* ============================================================================
   MODAL SIZING
   ============================================================================ */

.category-edit-modal {
  max-width: 35rem;
  min-height: fit-content;
}

.delete-modal {
  max-width: 30rem;
}

/* ============================================================================
   EDIT FORM
   ============================================================================ */

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.form-group-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: var(--gap-large);
}

/* ============================================================================
   COLOR PICKER
   ============================================================================ */

.color-input {
  width: 100%;
  cursor: pointer;
  padding: 0;
  background: none;
  border: none;
  margin: 0;
}

/* ============================================================================
   ICON SELECTOR
   ============================================================================ */

.icon-selector {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.selected-icon {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: var(--gap-small);
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  background: var(--color-background-light);
}

.icon-picker {
  background: var(--color-background);
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.icon-search {
  padding: var(--gap-small);
  border-bottom: 1px solid var(--color-background-dark);
}

.icon-search input {
  margin: 0;
}

.icon-loading {
  padding: var(--gap-large);
  text-align: center;
  color: var(--color-text-light);
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(5rem, 1fr));
  gap: 0.25rem;
  padding: var(--gap-small);
  overflow-y: auto;
  max-height: 16rem;
}

.icon-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: var(--gap-small);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-option:hover {
  background: var(--color-background-light);
}

.icon-option.selected {
  border: #2a2a2a 1px dashed;
}

.icon-name {
  font-size: 0.625rem;
  text-align: center;
  word-break: break-word;
  line-height: 1.2;
}

/* ============================================================================
   DELETE MODAL
   ============================================================================ */

.delete-info {
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
  margin: var(--gap-small) 0;
  font-size: var(--text-small);
}

.error-text {
  color: #ef4444;
  font-weight: 500;
}

.warning-text {
  color: #292929;
  font-weight: 500;
}
</style>