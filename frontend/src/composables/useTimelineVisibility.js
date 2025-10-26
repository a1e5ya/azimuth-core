// frontend/src/composables/useTimelineVisibility.js

import { ref, computed } from 'vue'

/**
 * Composable for managing timeline visibility state
 * Handles toggling of types, categories, and subcategories
 */
export function useTimelineVisibility(expenseCategoriesGetter, incomeCategoriesGetter, transferCategoriesGetter) {
  // Visibility state
  const visibleTypes = ref(['income', 'expenses', 'transfers'])
  const visibleCategories = ref([])
  const visibleSubcategories = ref([])
  const expandedCategories = ref([])
  
  // Convert getters to computed properties
  const expenseCategories = computed(() => expenseCategoriesGetter())
  const incomeCategories = computed(() => incomeCategoriesGetter())
  const transferCategories = computed(() => transferCategoriesGetter())
  
  // Check visibility
  const isTypeVisible = (typeId) => visibleTypes.value.includes(typeId)
  const isCategoryVisible = (categoryId) => visibleCategories.value.includes(categoryId)
  const isSubcategoryVisible = (subcategoryId) => visibleSubcategories.value.includes(subcategoryId)
  const isCategoryExpanded = (categoryId) => expandedCategories.value.includes(categoryId)
  
  /**
   * Toggle category expansion state
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
   * Toggle type visibility (income, expenses, transfers)
   */
  function toggleType(typeId) {
    const index = visibleTypes.value.indexOf(typeId)
    
    if (index > -1) {
      // Hide type
      visibleTypes.value.splice(index, 1)
      
      // Get categories for this type
      let categories = []
      if (typeId === 'expenses') {
        categories = expenseCategories.value
      } else if (typeId === 'income') {
        categories = incomeCategories.value
      } else if (typeId === 'transfers') {
        categories = transferCategories.value
      }
      
      // Hide all categories and subcategories
      categories.forEach(cat => {
        const catIndex = visibleCategories.value.indexOf(cat.id)
        if (catIndex > -1) {
          visibleCategories.value.splice(catIndex, 1)
        }
        
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
      // Show type
      visibleTypes.value.push(typeId)
      
      // Get categories for this type
      let categories = []
      if (typeId === 'expenses') {
        categories = expenseCategories.value
      } else if (typeId === 'income') {
        categories = incomeCategories.value
      } else if (typeId === 'transfers') {
        categories = transferCategories.value
      }
      
      // Show all categories and subcategories
      categories.forEach(cat => {
        if (!visibleCategories.value.includes(cat.id)) {
          visibleCategories.value.push(cat.id)
        }
        
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
   */
  function toggleCategory(categoryId) {
    const index = visibleCategories.value.indexOf(categoryId)
    
    // Find the category
    let category = null
    for (const categories of [expenseCategories.value, incomeCategories.value, transferCategories.value]) {
      category = categories.find(c => c.id === categoryId)
      if (category) break
    }
    
    if (!category) return
    
    if (index > -1) {
      // Hide category
      visibleCategories.value.splice(index, 1)
      
      // Hide all subcategories
      if (category.children) {
        category.children.forEach(subcat => {
          const subcatIndex = visibleSubcategories.value.indexOf(subcat.id)
          if (subcatIndex > -1) {
            visibleSubcategories.value.splice(subcatIndex, 1)
          }
        })
      }
    } else {
      // Show category
      visibleCategories.value.push(categoryId)
      
      // Show all subcategories
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
   */
  function toggleSubcategory(subcategoryId) {
    const index = visibleSubcategories.value.indexOf(subcategoryId)
    
    if (index > -1) {
      visibleSubcategories.value.splice(index, 1)
    } else {
      visibleSubcategories.value.push(subcategoryId)
    }
  }
  
  /**
   * Initialize visibility - show all categories and subcategories
   */
  function initializeVisibility() {
    visibleCategories.value = []
    visibleSubcategories.value = []
    
    const allCategories = [
      ...expenseCategories.value,
      ...incomeCategories.value,
      ...transferCategories.value
    ]
    
    allCategories.forEach(cat => {
      visibleCategories.value.push(cat.id)
      
      if (cat.children) {
        cat.children.forEach(subcat => {
          visibleSubcategories.value.push(subcat.id)
        })
      }
    })
  }
  
  return {
    // State
    visibleTypes,
    visibleCategories,
    visibleSubcategories,
    expandedCategories,
    
    // Checkers
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded,
    
    // Actions
    toggleType,
    toggleCategory,
    toggleSubcategory,
    toggleCategoryExpanded,
    initializeVisibility
  }
}