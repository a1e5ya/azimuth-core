// frontend/src/composables/useTimelineVisibility.js

import { ref, computed } from 'vue'

/**
 * Composable for managing timeline visibility state
 * Handles toggling of types, categories, and subcategories
 */
export function useTimelineVisibility(
  expenseCategoriesGetter, 
  incomeCategoriesGetter, 
  transferCategoriesGetter,
  targetCategoriesGetter
) {
  const visibleTypes = ref(['income', 'expenses', 'transfers', 'targets'])
  const visibleCategories = ref([])
  const visibleSubcategories = ref([])
  const expandedCategories = ref([])
  
  const expenseCategories = computed(() => expenseCategoriesGetter())
  const incomeCategories = computed(() => incomeCategoriesGetter())
  const transferCategories = computed(() => transferCategoriesGetter())
  const targetCategories = computed(() => targetCategoriesGetter())
  
  const isTypeVisible = (typeId) => visibleTypes.value.includes(typeId)
  const isCategoryVisible = (categoryId) => visibleCategories.value.includes(categoryId)
  const isSubcategoryVisible = (subcategoryId) => visibleSubcategories.value.includes(subcategoryId)
  const isCategoryExpanded = (categoryId) => expandedCategories.value.includes(categoryId)
  
  function toggleCategoryExpanded(categoryId) {
    const index = expandedCategories.value.indexOf(categoryId)
    if (index > -1) {
      expandedCategories.value.splice(index, 1)
    } else {
      expandedCategories.value.push(categoryId)
    }
  }
  
  function toggleType(typeId) {
    const index = visibleTypes.value.indexOf(typeId)
    
    if (index > -1) {
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
  
  function toggleCategory(categoryId) {
    const index = visibleCategories.value.indexOf(categoryId)
    
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
  
  function toggleSubcategory(subcategoryId) {
    const index = visibleSubcategories.value.indexOf(subcategoryId)
    
    if (index > -1) {
      visibleSubcategories.value.splice(index, 1)
    } else {
      visibleSubcategories.value.push(subcategoryId)
    }
  }
  
  function initializeVisibility() {
    visibleCategories.value = []
    visibleSubcategories.value = []
    
    const allCategories = [
      ...expenseCategories.value,
      ...incomeCategories.value,
      ...transferCategories.value,
      ...targetCategories.value
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
    visibleTypes,
    visibleCategories,
    visibleSubcategories,
    expandedCategories,
    isTypeVisible,
    isCategoryVisible,
    isSubcategoryVisible,
    isCategoryExpanded,
    toggleType,
    toggleCategory,
    toggleSubcategory,
    toggleCategoryExpanded,
    initializeVisibility
  }
}