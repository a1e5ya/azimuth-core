<template>
  <div>
    <!-- Create/Edit Category Modal -->
    <div v-if="editingCategory" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content category-edit-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditing ? 'Edit Category' : 'Add Category' }}</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="edit-form">
            <div class="form-group">
              <label>Name</label>
              <input 
                type="text" 
                v-model="editForm.name"
                class="form-input"
                placeholder="Category name..."
              >
            </div>
            
            <div class="form-group">
              <label>Icon</label>
              <input 
                type="text" 
                v-model="editForm.icon"
                class="form-input"
                placeholder="Icon name..."
              >
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
            :disabled="saving || !editForm.name"
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
                  ❌ This category has {{ deleteCheck.children_count }} subcategories. 
                  Please delete subcategories first.
                </p>
                
                <p v-if="deleteCheck.transaction_count > 0" class="warning-text">
                  {{ deleteCheck.transaction_count }} transactions will be moved to "Uncategorized"
                </p>
                
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
            :disabled="deleting || !deleteCheck?.can_delete"
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
import { ref, computed } from 'vue'
import { useCategoryStore } from '@/stores/categories'

export default {
  name: 'CategoriesCRUD',
  emits: ['category-updated', 'category-deleted', 'add-chat-message'],
  setup(props, { emit }) {
    const categoryStore = useCategoryStore()
    
    const editingCategory = ref(null)
    const deletingCategory = ref(null)
    const deleteCheck = ref(null)
    const saving = ref(false)
    const deleting = ref(false)
    
    const editForm = ref({
      name: '',
      icon: '',
      color: ''
    })

    const isEditing = computed(() => editingCategory.value?.id !== undefined)

    const createCategory = (parent = null) => {
      editingCategory.value = { parent_id: parent?.id || null }
      editForm.value = {
        name: '',
        icon: parent ? 'circle' : 'apps-sort',
        color: parent?.color || '#94a3b8'
      }
    }

    const editCategory = (category) => {
      editingCategory.value = category
      editForm.value = {
        name: category.name || '',
        icon: category.icon || 'circle',
        color: category.color || '#94a3b8'
      }
    }

    const closeEditModal = () => {
      editingCategory.value = null
      editForm.value = { name: '', icon: '', color: '' }
    }

    const saveEdit = async () => {
      if (!editForm.value.name || saving.value) return
      
      saving.value = true
      
      try {
        let result
        
        if (isEditing.value) {
          result = await categoryStore.updateCategory(
            editingCategory.value.id,
            editForm.value
          )
        } else {
          result = await categoryStore.createCategory({
            ...editForm.value,
            parent_id: editingCategory.value.parent_id
          })
        }
        
        if (result.success) {
          emit('add-chat-message', {
            message: isEditing.value ? 'Category updated' : 'Category created',
            response: isEditing.value 
              ? `"${editForm.value.name}" has been updated!`
              : `"${editForm.value.name}" has been created!`
          })
          
          closeEditModal()
          emit('category-updated')
        } else {
          emit('add-chat-message', {
            response: result.error || 'Failed to save category'
          })
        }
        
      } catch (error) {
        console.error('Failed to save category:', error)
        emit('add-chat-message', {
          response: 'An error occurred. Please try again.'
        })
      } finally {
        saving.value = false
      }
    }

    const deleteCategory = async (category) => {
      deletingCategory.value = category
      deleteCheck.value = null
      
      const check = await categoryStore.checkDelete(category.id)
      deleteCheck.value = check
    }

    const closeDeleteModal = () => {
      deletingCategory.value = null
      deleteCheck.value = null
    }

    const confirmDelete = async () => {
      if (!deletingCategory.value || deleting.value || !deleteCheck.value?.can_delete) return
      
      deleting.value = true
      
      try {
        const result = await categoryStore.deleteCategory(deletingCategory.value.id)
        
        if (result.success) {
          emit('add-chat-message', {
            message: 'Category deleted',
            response: `"${deletingCategory.value.name}" has been deleted.`
          })
          
          emit('category-deleted')
          closeDeleteModal()
        } else {
          emit('add-chat-message', {
            response: result.error || 'Failed to delete category'
          })
        }
        
      } catch (error) {
        console.error('Failed to delete category:', error)
        emit('add-chat-message', {
          response: 'An error occurred. Please try again.'
        })
      } finally {
        deleting.value = false
      }
    }

    return {
      editingCategory,
      deletingCategory,
      deleteCheck,
      saving,
      deleting,
      editForm,
      isEditing,
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
.category-edit-modal {
  max-width: 30rem;
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