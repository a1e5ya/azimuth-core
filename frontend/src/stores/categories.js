/**
 * Categories Store - Category Management State
 * 
 * Manages category tree and selection state:
 * - Category hierarchy (3 levels: Type → Category → Subcategory)
 * - Category selection and navigation
 * - Category CRUD operations
 * - Category summaries with transaction stats
 * - Breadcrumb navigation
 * 
 * Category Hierarchy:
 * - Level 1 (Type): INCOME, EXPENSES, TRANSFERS, TARGETS
 * - Level 2 (Category): Food, Transport, etc.
 * - Level 3 (Subcategory): Groceries, Fuel, etc.
 * 
 * Selection State:
 * - Tracks currently selected type, category, and subcategory
 * - Automatically loads summary for selected item
 * - Updates breadcrumb trail
 * 
 * API Integration:
 * - Loads category tree from backend
 * - CRUD operations (create, update, delete)
 * - Summary statistics with date filtering
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

export const useCategoryStore = defineStore('categories', () => {
  const authStore = useAuthStore()
  
  // ========================================
  // STATE
  // ========================================
  
  /** @type {Ref<Array>} Category tree (hierarchical structure) */
  const categories = ref([])
  
  /** @type {Ref<Object|null>} Selected type (Level 1) */
  const selectedType = ref(null)
  
  /** @type {Ref<Object|null>} Selected category (Level 2) */
  const selectedCategory = ref(null)
  
  /** @type {Ref<Object|null>} Selected subcategory (Level 3) */
  const selectedSubcategory = ref(null)
  
  /** @type {Ref<Object|null>} Summary data for selected category */
  const categorySummary = ref(null)
  
  /** @type {Ref<boolean>} Loading state for async operations */
  const loading = ref(false)
  
  /** @type {Ref<string|null>} Error message */
  const error = ref(null)
  
  // ========================================
  // COMPUTED
  // ========================================
  
  /** @type {ComputedRef<Array>} Category tree (alias for categories) */
  const categoryTree = computed(() => categories.value)
  
  /**
   * Determine which level is currently selected
   * @type {ComputedRef<string|null>} 'type', 'category', 'subcategory', or null
   */
  const selectedLevel = computed(() => {
    if (selectedSubcategory.value) return 'subcategory'
    if (selectedCategory.value) return 'category'
    if (selectedType.value) return 'type'
    return null
  })
  
  /**
   * Generate breadcrumb trail for current selection
   * @type {ComputedRef<Array>} Array of breadcrumb objects
   * 
   * @example
   * // For selected Groceries under Food under EXPENSES:
   * [
   *   { name: 'EXPENSES', level: 'type', id: '...' },
   *   { name: 'Food', level: 'category', id: '...' },
   *   { name: 'Groceries', level: 'subcategory', id: '...' }
   * ]
   */
  const breadcrumb = computed(() => {
    const crumbs = []
    if (selectedType.value) {
      crumbs.push({ name: selectedType.value.name, level: 'type', id: selectedType.value.id })
    }
    if (selectedCategory.value) {
      crumbs.push({ name: selectedCategory.value.name, level: 'category', id: selectedCategory.value.id })
    }
    if (selectedSubcategory.value) {
      crumbs.push({ name: selectedSubcategory.value.name, level: 'subcategory', id: selectedSubcategory.value.id })
    }
    return crumbs
  })
  
  // ========================================
  // CATEGORY LOADING
  // ========================================
  
  /**
   * Load category tree from backend
   * 
   * Fetches complete category hierarchy with:
   * - All types, categories, subcategories
   * - Transaction counts per category
   * - Total amounts per category
   * 
   * Called on:
   * - App initialization
   * - After category CRUD operations
   * - After category tree modifications
   * 
   * @returns {Promise<void>}
   */
  async function loadCategories() {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.get(`${API_BASE}/categories/tree`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      categories.value = response.data.tree || []
      console.log('✅ Categories loaded:', categories.value.length)
      
    } catch (err) {
      console.error('❌ Failed to load categories:', err)
      error.value = err.response?.data?.detail || 'Failed to load categories'
      
      // Token might be expired, verify
      if (err.response?.status === 401) {
        await authStore.verifyToken()
      }
    } finally {
      loading.value = false
    }
  }
  
  // ========================================
  // CATEGORY SELECTION
  // ========================================
  
  /**
   * Select a type (Level 1)
   * 
   * Actions:
   * 1. Set selectedType
   * 2. Clear category and subcategory selection
   * 3. Load summary for type
   * 
   * @param {Object} type - Type object (INCOME, EXPENSES, etc.)
   * @returns {Promise<void>}
   * 
   * @example
   * await selectType({ id: '...', name: 'EXPENSES', code: 'expenses' })
   */
  async function selectType(type) {
    selectedType.value = type
    selectedCategory.value = null
    selectedSubcategory.value = null
    
    console.log('Selected: type', type.name)
    await loadSummary(type.code, 'type')
  }
  
  /**
   * Select a category (Level 2)
   * 
   * Actions:
   * 1. Set selectedCategory
   * 2. Clear subcategory selection
   * 3. Find and set parent type
   * 4. Load summary for category
   * 
   * @param {Object} category - Category object (Food, Transport, etc.)
   * @returns {Promise<void>}
   */
  async function selectCategory(category) {
    selectedCategory.value = category
    selectedSubcategory.value = null
    
    // Find parent type
    const parentType = categories.value.find(t => 
      t.children && t.children.some(c => c.id === category.id)
    )
    if (parentType) {
      selectedType.value = parentType
    }
    
    console.log('Selected: category', category.name)
    await loadSummary(category.id, 'category')
  }
  
  /**
   * Select a subcategory (Level 3)
   * 
   * Actions:
   * 1. Set selectedSubcategory
   * 2. Find and set parent category and type
   * 3. Load summary for subcategory
   * 
   * @param {Object} subcategory - Subcategory object (Groceries, Fuel, etc.)
   * @returns {Promise<void>}
   */
  async function selectSubcategory(subcategory) {
    selectedSubcategory.value = subcategory
    
    // Find parent category and type
    for (const type of categories.value) {
      if (type.children) {
        for (const cat of type.children) {
          if (cat.children && cat.children.some(s => s.id === subcategory.id)) {
            selectedType.value = type
            selectedCategory.value = cat
            break
          }
        }
      }
    }
    
    console.log('Selected: subcategory', subcategory.name)
    await loadSummary(subcategory.id, 'subcategory')
  }
  
  // ========================================
  // CATEGORY SUMMARY
  // ========================================
  
  /**
   * Load summary statistics for selected category
   * 
   * Summary includes:
   * - Total transaction count
   * - Total amount
   * - Average amount
   * - Breakdown by child categories (if applicable)
   * 
   * Optional date filtering:
   * - startDate: Include only transactions after this date
   * - endDate: Include only transactions before this date
   * 
   * @param {string} id - Category ID or type code
   * @param {string} level - 'type', 'category', or 'subcategory'
   * @param {string|null} startDate - Start date filter (YYYY-MM-DD)
   * @param {string|null} endDate - End date filter (YYYY-MM-DD)
   * @returns {Promise<void>}
   */
  async function loadSummary(id, level, startDate = null, endDate = null) {
    loading.value = true
    error.value = null
    categorySummary.value = null
    
    try {
      let url = ''
      const params = new URLSearchParams()
      
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      // Build URL based on level
      if (level === 'type') {
        url = `${API_BASE}/categories/type/${id}/summary`
      } else if (level === 'category') {
        url = `${API_BASE}/categories/${id}/summary`
      } else if (level === 'subcategory') {
        url = `${API_BASE}/categories/${id}/summary`
      }
      
      const queryString = params.toString()
      if (queryString) {
        url += `?${queryString}`
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      categorySummary.value = response.data
      console.log('✅ Summary loaded for', level, id)
      
    } catch (err) {
      console.error('❌ Failed to load summary:', err)
      error.value = err.response?.data?.detail || 'Failed to load summary'
      
      if (err.response?.status === 401) {
        await authStore.verifyToken()
      }
    } finally {
      loading.value = false
    }
  }
  
  // ========================================
  // CATEGORY CRUD OPERATIONS
  // ========================================
  
  /**
   * Create new category
   * 
   * Category data should include:
   * - name: Category name
   * - parent_id: Parent category ID (null for type-level)
   * - icon: Icon identifier
   * - color: Hex color code (optional)
   * 
   * @param {Object} categoryData - Category creation data
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   * 
   * @example
   * const result = await createCategory({
   *   name: 'New Category',
   *   parent_id: 'parent-uuid',
   *   icon: 'icon-name',
   *   color: '#ff0000'
   * })
   */
  async function createCategory(categoryData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.post(`${API_BASE}/categories/`, categoryData, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      console.log('✅ Category created:', response.data)
      await loadCategories()
      
      return { success: true, data: response.data }
      
    } catch (err) {
      console.error('❌ Failed to create category:', err)
      error.value = err.response?.data?.detail || 'Failed to create category'
      
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Update existing category
   * 
   * Updates can include:
   * - name: New category name
   * - icon: New icon
   * - color: New color
   * 
   * @param {string} categoryId - Category UUID
   * @param {Object} updates - Fields to update
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   * 
   * @example
   * const result = await updateCategory('category-uuid', {
   *   name: 'Updated Name',
   *   color: '#00ff00'
   * })
   */
  async function updateCategory(categoryId, updates) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.put(`${API_BASE}/categories/${categoryId}`, updates, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      console.log('✅ Category updated:', response.data)
      await loadCategories()
      
      return { success: true, data: response.data }
      
    } catch (err) {
      console.error('❌ Failed to update category:', err)
      error.value = err.response?.data?.detail || 'Failed to update category'
      
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Check if category can be deleted
   * 
   * Checks:
   * - Does category have children? (cannot delete if yes)
   * - How many transactions use this category?
   * 
   * Returns warning message for user.
   * 
   * @param {string} categoryId - Category UUID
   * @returns {Promise<{can_delete: boolean, transaction_count: number, warning_message: string}>}
   * 
   * @example
   * const check = await checkDelete('category-uuid')
   * if (!check.can_delete) {
   *   alert(check.warning_message)
   * }
   */
  async function checkDelete(categoryId) {
    try {
      const response = await axios.get(`${API_BASE}/categories/${categoryId}/check-delete`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      return response.data
      
    } catch (err) {
      console.error('❌ Failed to check delete:', err)
      return { can_delete: false, warning_message: 'Failed to check category' }
    }
  }

  /**
   * Delete category
   * 
   * Deletes category and moves transactions to "Uncategorized".
   * Cannot delete categories with children (subcategories).
   * 
   * Process:
   * 1. Check if category can be deleted
   * 2. Move transactions to Uncategorized
   * 3. Delete category
   * 4. Reload category tree
   * 5. Clear selection
   * 
   * @param {string} categoryId - Category UUID
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   */
  async function deleteCategory(categoryId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.delete(`${API_BASE}/categories/${categoryId}`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      console.log('✅ Category deleted:', response.data)
      await loadCategories()
      
      // Clear selection
      selectedType.value = null
      selectedCategory.value = null
      selectedSubcategory.value = null
      categorySummary.value = null
      
      return { success: true, data: response.data }
      
    } catch (err) {
      console.error('❌ Failed to delete category:', err)
      error.value = err.response?.data?.detail || 'Failed to delete category'
      
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }
  
  // ========================================
  // CATEGORY INITIALIZATION
  // ========================================
  
  /**
   * Initialize default categories
   * 
   * Creates default category structure:
   * - INCOME (Employment, Benefits, Investment, Other)
   * - EXPENSES (Food, Family, Housing, Shopping, Health, Transport, etc.)
   * - TRANSFERS (Account transfers, Savings)
   * - TARGETS (Savings targets, Expense limits, Income goals)
   * 
   * Called when user has no categories (first-time setup).
   * 
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async function initializeCategories() {
    try {
      const response = await axios.post(`${API_BASE}/categories/initialize`, {}, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      console.log('✅ Categories initialized:', response.data)
      await loadCategories()
      
      return { success: true }
      
    } catch (err) {
      console.error('❌ Failed to initialize categories:', err)
      return { success: false, error: err.response?.data?.detail }
    }
  }
  
  // ========================================
  // UTILITIES
  // ========================================
  
  /**
   * Clear category selection
   * 
   * Resets all selection state:
   * - selectedType
   * - selectedCategory
   * - selectedSubcategory
   * - categorySummary
   */
  function clearSelection() {
    selectedType.value = null
    selectedCategory.value = null
    selectedSubcategory.value = null
    categorySummary.value = null
  }
  
  // ========================================
  // EXPOSED API
  // ========================================
  
  return {
    // State
    categories,
    selectedType,
    selectedCategory,
    selectedSubcategory,
    categorySummary,
    loading,
    error,
    
    // Computed
    categoryTree,
    selectedLevel,
    breadcrumb,
    
    // Actions
    loadCategories,
    selectType,
    selectCategory,
    selectSubcategory,
    loadSummary,
    createCategory,
    updateCategory,
    checkDelete,
    deleteCategory,
    initializeCategories,
    clearSelection
  }
})