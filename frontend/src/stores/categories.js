import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

export const useCategoryStore = defineStore('categories', () => {
  const authStore = useAuthStore()
  
  const categories = ref([])
  const selectedType = ref(null)
  const selectedCategory = ref(null)
  const selectedSubcategory = ref(null)
  const categorySummary = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  const categoryTree = computed(() => categories.value)
  
  const selectedLevel = computed(() => {
    if (selectedSubcategory.value) return 'subcategory'
    if (selectedCategory.value) return 'category'
    if (selectedType.value) return 'type'
    return null
  })
  
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
  
  async function loadCategories() {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.get(`${API_BASE}/categories/tree`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      categories.value = response.data.tree || []
      console.log('✅ Categories loaded:', categories.value.length)
      console.log('🎨 First category color:', categories.value[0]?.color)
      
    } catch (err) {
      console.error('❌ Failed to load categories:', err)
      error.value = err.response?.data?.detail || 'Failed to load categories'
      
      if (err.response?.status === 401) {
        await authStore.verifyToken()
      }
    } finally {
      loading.value = false
    }
  }
  
  async function selectType(type) {
    selectedType.value = type
    selectedCategory.value = null
    selectedSubcategory.value = null
    
    console.log('Selected: type', type.name)
    await loadSummary(type.code, 'type')
  }
  
  async function selectCategory(category) {
    selectedCategory.value = category
    selectedSubcategory.value = null
    
    const parentType = categories.value.find(t => 
      t.children && t.children.some(c => c.id === category.id)
    )
    if (parentType) {
      selectedType.value = parentType
    }
    
    console.log('Selected: category', category.name)
    await loadSummary(category.id, 'category')
  }
  
  async function selectSubcategory(subcategory) {
    selectedSubcategory.value = subcategory
    
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
  
  async function loadSummary(id, level, startDate = null, endDate = null) {
    loading.value = true
    error.value = null
    categorySummary.value = null
    
    try {
      let url = ''
      const params = new URLSearchParams()
      
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
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
  
  async function createCategory(categoryData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.post(`${API_BASE}/categories`, categoryData, {
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
  
  async function deleteCategory(categoryId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.delete(`${API_BASE}/categories/${categoryId}`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      
      console.log('✅ Category deleted:', response.data)
      await loadCategories()
      
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
  
  function clearSelection() {
    selectedType.value = null
    selectedCategory.value = null
    selectedSubcategory.value = null
    categorySummary.value = null
  }
  
  return {
    categories,
    selectedType,
    selectedCategory,
    selectedSubcategory,
    categorySummary,
    loading,
    error,
    categoryTree,
    selectedLevel,
    breadcrumb,
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