<template>
  <div>
    <!-- Create/Edit Category Modal -->
    <div v-if="editingCategory" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content category-edit-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditing ? 'Edit Category' : (isCreatingType ? 'Add Type' : (isCreatingMainCategory ? 'Add Category' : 'Add Subcategory')) }}</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        
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
            
            <div class="form-group">
              <label>Name *</label>
              <input 
                type="text" 
                v-model="editForm.name"
                class="form-input"
                placeholder="Category name..."
                required
              >
            </div>
            
            <div class="form-group">
              <label>Icon</label>
              <div class="icon-selector">
                <div class="selected-icon" @click="showIconPicker = !showIconPicker">
                  <AppIcon :name="editForm.icon" size="medium" />
                  <span>{{ editForm.icon }}</span>
                </div>
                
                <div v-if="showIconPicker" class="icon-picker">
                  <div class="icon-search">
                    <input 
                      v-model="iconSearch" 
                      type="text" 
                      placeholder="Search icons..."
                      class="form-input"
                    >
                  </div>
                  <div v-if="loadingIcons" class="icon-loading">Loading icons...</div>
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
            
            <div class="form-group">
              <label>Color</label>
              <input 
                type="color" 
                v-model="editForm.color"
                class="form-input color-input"
              >
            </div>
          </div>
        </div>
        
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

    <!-- Delete Confirmation Modal -->
    <div v-if="deletingCategory" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h3>Delete Category</h3>
          <button class="close-btn" @click="closeDeleteModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="delete-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>Are you sure you want to delete "{{ deletingCategory.name }}"?</strong></p>
              
              <div v-if="deleteCheck" class="delete-info">
                <p v-if="deleteCheck.has_children" class="error-text">
                  ❌ This category has subcategories. Please delete subcategories first.
                </p>
                
                <div v-if="deleteCheck.transaction_count > 0">
                  <p class="warning-text">
                    {{ deleteCheck.transaction_count }} transactions will be moved
                  </p>
                  
                  <div class="form-group" style="margin-top: 1rem;">
                    <label>Move transactions to:</label>
                    <select v-model="moveToSubcategoryId" class="form-input" required>
                      <option value="">Select subcategory...</option>
                      <option value="uncategorized">Uncategorized</option>
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
                
                <p v-if="deleteCheck.can_delete && deleteCheck.transaction_count === 0">
                  This category is empty and can be safely deleted.
                </p>
              </div>
              
              <p v-if="deleteCheck?.can_delete">This action cannot be undone.</p>
            </div>
          </div>
        </div>
        
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
    
    const editingCategory = ref(null)
    const deletingCategory = ref(null)
    const deleteCheck = ref(null)
    const moveToSubcategoryId = ref('')
    const saving = ref(false)
    const deleting = ref(false)
    const showIconPicker = ref(false)
    const iconSearch = ref('')
    const availableIcons = ref([])
    const loadingIcons = ref(false)
    const availableTypes = ref([])
    const selectedTypeId = ref('')
    
    const editForm = ref({
      name: '',
      icon: '',
      color: ''
    })

    const isEditing = computed(() => editingCategory.value?.id !== undefined)
    const isCreatingType = computed(() => !isEditing.value && editingCategory.value?.parent_id === null && !editingCategory.value?.isMainCategory)
    const isCreatingMainCategory = computed(() => !isEditing.value && editingCategory.value?.isMainCategory === true)
    const isCreatingSubcategory = computed(() => !isEditing.value && editingCategory.value?.parent_id !== null && !editingCategory.value?.isMainCategory)
    
    const availableTypesForMove = computed(() => availableTypes.value)

    const onTypeChange = () => {
      const selectedType = availableTypes.value.find(t => t.id === selectedTypeId.value)
      if (selectedType) {
        editingCategory.value.parent_id = selectedTypeId.value
        editForm.value.color = selectedType.color || '#94a3b8'
      }
    }

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

    const filteredIcons = computed(() => {
      if (!iconSearch.value) return availableIcons.value
      const search = iconSearch.value.toLowerCase()
      return availableIcons.value.filter(icon => icon.toLowerCase().includes(search))
    })

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
      
      showIconPicker.value = false
      iconSearch.value = ''
    }

    const editCategory = (category) => {
      editingCategory.value = { ...category }
      editForm.value = {
        name: category.name || '',
        icon: category.icon || 'circle',
        color: category.color || '#94a3b8'
      }
      showIconPicker.value = false
      iconSearch.value = ''
    }

    const selectIcon = (icon) => {
      editForm.value.icon = icon
      showIconPicker.value = false
      iconSearch.value = ''
    }

    const closeEditModal = () => {
      editingCategory.value = null
      editForm.value = { name: '', icon: '', color: '' }
      showIconPicker.value = false
      iconSearch.value = ''
      selectedTypeId.value = ''
    }

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

    const closeDeleteModal = () => {
      deletingCategory.value = null
      deleteCheck.value = null
      moveToSubcategoryId.value = ''
    }

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
        // Send move_to_category_id as query parameter instead of body
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

    onMounted(() => {
      loadAvailableIcons()
      loadTypes()
    })

    return {
      editingCategory,
      deletingCategory,
      deleteCheck,
      moveToSubcategoryId,
      saving,
      deleting,
      editForm,
      isEditing,
      isCreatingType,
      isCreatingMainCategory,
      isCreatingSubcategory,
      showIconPicker,
      iconSearch,
      filteredIcons,
      loadingIcons,
      availableTypes,
      availableTypesForMove,
      selectedTypeId,
      onTypeChange,
      createCategory,
      editCategory,
      selectIcon,
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
.category-edit-modal {
  max-width: 35rem;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.color-input {
  height: 3rem;
  cursor: pointer;
}

.icon-selector {
  position: relative;
}

.selected-icon {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: var(--gap-small);
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.selected-icon:hover {
  border-color: var(--color-text-light);
  background: var(--color-background-light);
}

.icon-picker {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.25rem;
  background: var(--color-background);
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  box-shadow: var(--shadow-hover);
  z-index: 1000;
  max-height: 20rem;
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
  background: var(--color-button-active);
}

.icon-name {
  font-size: 0.625rem;
  text-align: center;
  word-break: break-word;
  line-height: 1.2;
}

.delete-modal {
  max-width: 30rem;
}

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
  color: #f59e0b;
  font-weight: 500;
}
</style>