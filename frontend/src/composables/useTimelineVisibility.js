/**
 * Timeline Visibility Composable - Category Visibility Management
 * 
 * Manages visibility state for timeline categories:
 * - Type visibility (income/expenses/transfers/targets)
 * - Category visibility (Food, Transport, etc.)
 * - Subcategory visibility (Groceries, Fuel, etc.)
 * - Category expansion state (for tree UI)
 * 
 * Hierarchy Management:
 * - Toggling type affects all its categories and subcategories
 * - Toggling category affects all its subcategories
 * - Subcategories can be toggled independently
 * 
 * Visibility Logic:
 * - When type is hidden, all children become hidden
 * - When type is shown, all children become visible
 * - Same cascading logic for categories → subcategories
 * 
 * Used by:
 * - TimelineView component
 * - Category filter UI
 * - Timeline chart rendering
 * 
 * @param {Function} expenseCategoriesGetter - Function that returns expense categories
 * @param {Function} incomeCategoriesGetter - Function that returns income categories
 * @param {Function} transferCategoriesGetter - Function that returns transfer categories
 * @param {Function} targetCategoriesGetter - Function that returns target categories
 */

import { ref, computed } from 'vue'

export function useTimelineVisibility(
  expenseCategoriesGetter, 
  incomeCategoriesGetter, 
  transferCategoriesGetter,
  targetCategoriesGetter
) {
  // ========================================
  // STATE
  // ========================================
  
  /** 
   * Visible types (top-level categories)
   * @type {Ref<Array<string>>} Array of type IDs ('income', 'expenses', 'transfers', 'targets')
   */
  const visibleTypes = ref(['income', 'expenses', 'transfers', 'targets'])
  
  /** 
   * Visible categories (Level 2)
   * @type {Ref<Array<string>>} Array of category UUIDs
   */
  const visibleCategories = ref([])
  
  /** 
   * Visible subcategories (Level 3)
   * @type {Ref<Array<string>>} Array of subcategory UUIDs
   */
  const visibleSubcategories = ref([])
  
  /** 
   * Expanded categories in tree UI
   * @type {Ref<Array<string>>} Array of category UUIDs that are expanded
   */
  const expandedCategories = ref([])
  
  // ========================================
  // COMPUTED CATEGORY LISTS
  // ========================================
  
  /** @type {ComputedRef<Array>} Expense categories from store */
  const expenseCategories = computed(() => expenseCategoriesGetter())
  
  /** @type {ComputedRef<Array>} Income categories from store */
  const incomeCategories = computed(() => incomeCategoriesGetter())
  
  /** @type {ComputedRef<Array>} Transfer categories from store */
  const transferCategories = computed(() => transferCategoriesGetter())
  
  /** @type {ComputedRef<Array>} Target categories from store */
  const targetCategories = computed(() => targetCategoriesGetter())
  
  // ========================================
  // VISIBILITY CHECKS
  // ========================================
  
  /**
   * Check if type is visible
   * @param {string} typeId - Type identifier ('income', 'expenses', etc.)
   * @returns {boolean} True if type is visible
   */
  const isTypeVisible = (typeId) => visibleTypes.value.includes(typeId)
  
  /**
   * Check if category is visible
   * @param {string} categoryId - Category UUID
   * @returns {boolean} True if category is visible
   */
  const isCategoryVisible = (categoryId) => visibleCategories.value.includes(categoryId)
  
  /**
   * Check if subcategory is visible
   * @param {string} subcategoryId - Subcategory UUID
   * @returns {boolean} True if subcategory is visible
   */
  const isSubcategoryVisible = (subcategoryId) => visibleSubcategories.value.includes(subcategoryId)
  
  /**
   * Check if category is expanded in tree UI
   * @param {string} categoryId - Category UUID
   * @returns {boolean} True if category is expanded
   */
  const isCategoryExpanded = (categoryId) => expandedCategories.value.includes(categoryId)
  
  // ========================================
  // TOGGLE FUNCTIONS
  // ========================================
  
  /**
   * Toggle category expansion state
   * 
   * Used for tree UI to show/hide subcategories.
   * Does not affect visibility, only UI expansion.
   * 
   * @param {string} categoryId - Category UUID
   */
  function toggleCategoryExpanded(categoryId) {
    const index = expandedCategories.value.indexOf(categoryId)
    if (index > -1) {
      expandedCategories.value.splice(index, 1)
    } else {
      expandedCategories.value.push(categoryId)
    }
  }
  
  /**
   * Toggle type visibility
   * 
   * Cascading logic:
   * - Hiding type: Removes all child categories and subcategories from visible lists
   * - Showing type: Adds all child categories and subcategories to visible lists
   * 
   * Process:
   * 1. Find type's categories based on typeId
   * 2. Toggle type in visibleTypes
   * 3. Add/remove all categories
   * 4. Add/remove all subcategories
   * 
   * @param {string} typeId - Type identifier ('income', 'expenses', 'transfers', 'targets')
   */
  function toggleType(typeId) {
    const index = visibleTypes.value.indexOf(typeId)
    
    if (index > -1) {
      // Hiding type - remove all children
      visibleTypes.value.splice(index, 1)
      
      let categories = []
      if (typeId === 'expenses') {
        categories = expenseCategories.value
      } else if (typeId === 'income') {
        categories = incomeCategories.value
      } else if (typeId === 'transfers') {
        categories = transferCategories.value
      } else if (typeId === 'targets') {
        categories = targetCategories.value
      }
      
      // Remove categories
      categories.forEach(cat => {
        const catIndex = visibleCategories.value.indexOf(cat.id)
        if (catIndex > -1) {
          visibleCategories.value.splice(catIndex, 1)
        }
        
        // Remove subcategories
        if (cat.children) {
          cat.children.forEach(subcat => {
            const subcatIndex = visibleSubcategories.value.indexOf(subcat.id)
            if (subcatIndex > -1) {
              visibleSubcategories.value.splice(subcatIndex, 1)
            }
          })
        }
      })
    } else {
      // Showing type - add all children
      visibleTypes.value.push(typeId)
      
      let categories = []
      if (typeId === 'expenses') {
        categories = expenseCategories.value
      } else if (typeId === 'income') {
        categories = incomeCategories.value
      } else if (typeId === 'transfers') {
        categories = transferCategories.value
      } else if (typeId === 'targets') {
        categories = targetCategories.value
      }
      
      // Add categories
      categories.forEach(cat => {
        if (!visibleCategories.value.includes(cat.id)) {
          visibleCategories.value.push(cat.id)
        }
        
        // Add subcategories
        if (cat.children) {
          cat.children.forEach(subcat => {
            if (!visibleSubcategories.value.includes(subcat.id)) {
              visibleSubcategories.value.push(subcat.id)
            }
          })
        }
      })
    }
  }
  
  /**
   * Toggle category visibility
   * 
   * Cascading logic:
   * - Hiding category: Removes all child subcategories from visible list
   * - Showing category: Adds all child subcategories to visible list
   * 
   * Process:
   * 1. Find category in all type lists
   * 2. Toggle category in visibleCategories
   * 3. Add/remove all subcategories
   * 
   * @param {string} categoryId - Category UUID
   */
  function toggleCategory(categoryId) {
    const index = visibleCategories.value.indexOf(categoryId)
    
    // Find category in all type lists
    let category = null
    for (const categories of [
      expenseCategories.value, 
      incomeCategories.value, 
      transferCategories.value,
      targetCategories.value
    ]) {
      category = categories.find(c => c.id === categoryId)
      if (category) break
    }
    
    if (!category) return
    
    if (index > -1) {
      // Hiding category - remove all subcategories
      visibleCategories.value.splice(index, 1)
      
      if (category.children) {
        category.children.forEach(subcat => {
          const subcatIndex = visibleSubcategories.value.indexOf(subcat.id)
          if (subcatIndex > -1) {
            visibleSubcategories.value.splice(subcatIndex, 1)
          }
        })
      }
    } else {
      // Showing category - add all subcategories
      visibleCategories.value.push(categoryId)
      
      if (category.children) {
        category.children.forEach(subcat => {
          if (!visibleSubcategories.value.includes(subcat.id)) {
            visibleSubcategories.value.push(subcat.id)
          }
        })
      }
    }
  }
  
  /**
   * Toggle subcategory visibility
   * 
   * Independent toggle - does not affect parent category.
   * Allows granular control over which subcategories to display.
   * 
   * @param {string} subcategoryId - Subcategory UUID
   */
  function toggleSubcategory(subcategoryId) {
    const index = visibleSubcategories.value.indexOf(subcategoryId)
    
    if (index > -1) {
      visibleSubcategories.value.splice(index, 1)
    } else {
      visibleSubcategories.value.push(subcategoryId)
    }
  }
  
  // ========================================
  // INITIALIZATION
  // ========================================
  
  /**
   * Initialize visibility with all categories/subcategories visible
   * 
   * Process:
   * 1. Clear existing visibility arrays
   * 2. Iterate through all categories from all types
   * 3. Add all categories to visibleCategories
   * 4. Add all subcategories to visibleSubcategories
   * 
   * Called when:
   * - Component mounts
   * - Category tree is loaded/refreshed
   * - "Show All" is clicked
   */
  function initializeVisibility() {
    visibleCategories.value = []
    visibleSubcategories.value = []
    
    // Combine all categories from all types
    const allCategories = [
      ...expenseCategories.value,
      ...incomeCategories.value,
      ...transferCategories.value,
      ...targetCategories.value
    ]
    
    // Add all categories and subcategories
    allCategories.forEach(cat => {
      visibleCategories.value.push(cat.id)
      
      if (cat.children) {
        cat.children.forEach(subcat => {
          visibleSubcategories.value.push(subcat.id)
        })
      }
    })
  }
  
  // ========================================
  // EXPOSED API
  // ========================================
  
  return {
    // State
    visibleTypes,
    visibleCategories,
    visibleSubcategories,
    expandedCategories,
    
    // Check functions
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded,
    
    // Toggle functions
    toggleType,
    toggleCategory,
    toggleSubcategory,
    toggleCategoryExpanded,
    
    // Initialization
    initializeVisibility
  }
}