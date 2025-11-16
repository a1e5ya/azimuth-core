<template>
  <transition name="slide-down">
    <div class="filters-panel-compact" v-if="show">
    <!-- First Row: Date Range & Amounts -->
    <div class="filters-row">
      <div class="filter-group-compact">
        <label>From Date</label>
        <input 
          type="date" 
          v-model="localFilters.startDate"
          class="form-input filter-input-compact"
          @change="applyFilters"
        >
      </div>
      
      <div class="filter-group-compact">
        <label>To Date</label>
        <input 
          type="date" 
          v-model="localFilters.endDate"
          class="form-input filter-input-compact"
          @change="applyFilters"
        >
      </div>
      
      <div class="filter-group-compact">
        <label>Min Amount</label>
        <input 
          type="number" 
          v-model.number="localFilters.minAmount"
          class="form-input filter-input-compact"
          placeholder="-1000 (expenses)"
          step="any"
          @change="applyFilters"
        >
        <small class="hint-text">Negative for expenses</small>
      </div>
      
      <div class="filter-group-compact">
        <label>Max Amount</label>
        <input 
          type="number" 
          v-model.number="localFilters.maxAmount"
          class="form-input filter-input-compact"
          placeholder="-50 (expenses)"
          step="any"
          @change="applyFilters"
        >
        <small class="hint-text">Negative for expenses</small>
      </div>
    </div>
    
    <!-- Second Row: Categories -->
    <div class="filters-row filters-row-actions">
      <div class="filter-group-compact">
        <label>Type</label>
        <div class="checkbox-list">
          <label 
            v-for="type in availableTypes" 
            :key="type"
            class="checkbox-item"
          >
            <input 
              type="checkbox" 
              :value="type"
              :checked="localFilters.types.includes(type)"
              @change="toggleArrayItem(localFilters.types, type); handleTypeChange()"
            >
            <span>{{ type }}</span>
          </label>
        </div>
      </div>

      <div class="filter-group-compact">
        <label>Category</label>
        <div class="checkbox-list">
          <label 
            v-for="category in availableCategories" 
            :key="category"
            class="checkbox-item"
            :class="{ disabled: localFilters.types.length === 0 }"
          >
            <input 
              type="checkbox" 
              :value="category"
              :checked="localFilters.categories.includes(category)"
              :disabled="localFilters.types.length === 0"
              @change="toggleArrayItem(localFilters.categories, category); handleCategoryChange()"
            >
            <span>{{ category }}</span>
          </label>
        </div>
      </div>

      <div class="filter-group-compact">
        <label>Subcategory</label>
        <div class="checkbox-list">
          <label 
            v-for="subcategory in availableSubcategories" 
            :key="subcategory"
            class="checkbox-item"
            :class="{ disabled: localFilters.categories.length === 0 }"
          >
            <input 
              type="checkbox" 
              :value="subcategory"
              :checked="localFilters.subcategories.includes(subcategory)"
              :disabled="localFilters.categories.length === 0"
              @change="toggleArrayItem(localFilters.subcategories, subcategory); applyFilters()"
            >
            <span>{{ subcategory }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Third Row: Owner & Account Type -->
    <div class="filters-row third-row">
      <div class="filter-group-compact">
        <label>Owner</label>
        <div class="checkbox-list">
          <label 
            v-for="owner in availableOwners" 
            :key="owner"
            class="checkbox-item"
          >
            <input 
              type="checkbox" 
              :value="owner"
              :checked="localFilters.owners.includes(owner)"
              @change="toggleArrayItem(localFilters.owners, owner); handleOwnerChange()"
            >
            <span>{{ owner }}</span>
          </label>
        </div>
      </div>
      
      <div class="filter-group-compact">
        <label>Account Type</label>
        <div class="checkbox-list">
          <label 
            v-for="type in availableAccountTypes" 
            :key="type"
            class="checkbox-item"
          >
            <input 
              type="checkbox" 
              :value="type"
              :checked="localFilters.accountTypes.includes(type)"
              @change="toggleArrayItem(localFilters.accountTypes, type); applyFilters()"
            >
            <span>{{ type }}</span>
          </label>
        </div>
      </div>

      <div class="filter-group-compact filter-search-compact">
        <label>Search</label>
        <input 
          type="text" 
          v-model="localFilters.merchant"
          class="form-input filter-input-compact"
          placeholder="Search merchant, message..."
          @input="debounceSearch"
        >
        <div class="filter-actions-compact">
          <button class="btn btn-small" @click="filterUncategorized">Uncategorized</button>
          <div></div>
          <button class="btn btn-small" @click="clearAllFilters">Clear</button>
          <button class="btn btn-small" @click="$emit('update:show', false)">Hide</button>
        </div>
      </div>
    </div>
  </div>
  </transition>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'TransactionsFilters',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    filterOptions: {
      type: Object,
      required: true
    },
    modelValue: {
      type: Object,
      required: true
    }
  },
  emits: ['update:modelValue', 'update:show', 'apply'],
  setup(props, { emit }) {
    const localFilters = ref({
      startDate: '',
      endDate: '',
      minAmount: null,
      maxAmount: null,
      merchant: '',
      owners: [],
      accountTypes: [],
      types: [],
      categories: [],
      subcategories: []
    })

    let searchTimeout = null

    watch(() => props.modelValue, (newVal) => {
      // Force complete sync with proper array cloning
      localFilters.value = {
        startDate: newVal.startDate || '',
        endDate: newVal.endDate || '',
        minAmount: newVal.minAmount,
        maxAmount: newVal.maxAmount,
        merchant: newVal.merchant || '',
        owners: [...(newVal.owners || [])],
        accountTypes: [...(newVal.accountTypes || [])],
        types: [...(newVal.types || [])],
        categories: [...(newVal.categories || [])],
        subcategories: [...(newVal.subcategories || [])]
      }
    }, { immediate: true, deep: true })

    const availableOwners = computed(() => {
      if (!props.filterOptions.ownerAccountMap) return []
      return Object.keys(props.filterOptions.ownerAccountMap).sort()
    })

    const availableAccountTypes = computed(() => {
      if (!props.filterOptions.ownerAccountMap) return []
      
      if (localFilters.value.owners.length === 0) {
        const allTypes = new Set()
        Object.values(props.filterOptions.ownerAccountMap).forEach(types => {
          types.forEach(type => allTypes.add(type))
        })
        return Array.from(allTypes).sort()
      }
      
      const types = new Set()
      localFilters.value.owners.forEach(owner => {
        const ownerTypes = props.filterOptions.ownerAccountMap[owner] || []
        ownerTypes.forEach(type => types.add(type))
      })
      return Array.from(types).sort()
    })

    const availableTypes = computed(() => {
      return props.filterOptions.mainCategories || []
    })

    const availableCategories = computed(() => {
      if (!props.filterOptions.categoryMap) return []
      
      if (localFilters.value.types.length === 0) return []
      
      const categories = new Set()
      localFilters.value.types.forEach(type => {
        const typeCats = props.filterOptions.categoryMap[type] || []
        typeCats.forEach(cat => categories.add(cat))
      })
      return Array.from(categories).sort()
    })

    const availableSubcategories = computed(() => {
      if (!props.filterOptions.subcategoryMap) return []
      
      if (localFilters.value.categories.length === 0) return []
      
      const subcategories = new Set()
      localFilters.value.types.forEach(type => {
        localFilters.value.categories.forEach(category => {
          const key = `${type}|${category}`
          const subs = props.filterOptions.subcategoryMap[key] || []
          subs.forEach(sub => subcategories.add(sub))
        })
      })
      return Array.from(subcategories).sort()
    })

    const toggleArrayItem = (array, item) => {
      const index = array.indexOf(item)
      if (index > -1) {
        array.splice(index, 1)
      } else {
        array.push(item)
      }
    }

    const applyFilters = () => {
      emit('update:modelValue', { ...localFilters.value })
      emit('apply')
    }

    const debounceSearch = () => {
      if (searchTimeout) clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        applyFilters()
      }, 500)
    }

    const handleOwnerChange = () => {
      const validTypes = availableAccountTypes.value
      localFilters.value.accountTypes = localFilters.value.accountTypes.filter(
        type => validTypes.includes(type)
      )
      applyFilters()
    }

    const handleTypeChange = () => {
      const validCategories = availableCategories.value
      localFilters.value.categories = localFilters.value.categories.filter(
        cat => validCategories.includes(cat)
      )
      
      const validSubcategories = availableSubcategories.value
      localFilters.value.subcategories = localFilters.value.subcategories.filter(
        sub => validSubcategories.includes(sub)
      )
      
      applyFilters()
    }

    const handleCategoryChange = () => {
      const validSubcategories = availableSubcategories.value
      localFilters.value.subcategories = localFilters.value.subcategories.filter(
        sub => validSubcategories.includes(sub)
      )
      
      applyFilters()
    }

    const clearAllFilters = () => {
      localFilters.value = {
        startDate: '',
        endDate: '',
        minAmount: null,
        maxAmount: null,
        merchant: '',
        owners: [],
        accountTypes: [],
        types: [],
        categories: [],
        subcategories: []
      }
      applyFilters()
    }

    const filterUncategorized = () => {
      localFilters.value.categories = ['Uncategorized']
      applyFilters()
    }

    return {
      localFilters,
      availableOwners,
      availableAccountTypes,
      availableTypes,
      availableCategories,
      availableSubcategories,
      applyFilters,
      debounceSearch,
      handleOwnerChange,
      handleTypeChange,
      handleCategoryChange,
      clearAllFilters,
      filterUncategorized,
      toggleArrayItem
    }
  }
}
</script>

<style scoped>
.filters-panel-compact {
  background: var(--color-background-light);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  margin-bottom: var(--gap-standard);
  animation: slideDown 0.3s ease;
}

.filters-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--gap-small);
  margin-bottom: var(--gap-small);
}

.filters-row:last-child {
  margin-bottom: 0;
}

.filters-row-actions {
  grid-template-columns: repeat(3, 1fr);
}

.third-row {
  grid-template-columns: 1fr 1fr 2fr auto;
}

.filter-group-compact {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group-compact label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-light);
}

.hint-text {
  font-size: 0.65rem;
  color: var(--color-text-muted);
  font-style: italic;
  margin-top: -0.125rem;
}

.filter-input-compact {
  padding: 0.375rem var(--gap-small);
  font-size: var(--text-small);
  min-height: 33px;
}

.filter-input-compact[multiple] {
  padding: 0.25rem;
  min-height: 90px;
}

.filter-input-compact[multiple] option {
  padding: 0.25rem;
  cursor: pointer;
}

.filter-input-compact[multiple] option:hover {
  background: var(--color-background-dark);
}

.filter-search-compact {
  flex: 1;
  justify-content: space-between;
}

.filter-actions-compact {
  display: flex;
  gap: var(--gap-small);
  align-items: flex-start;
  justify-content: space-evenly;
}

.filter-actions-compact .btn-small {
  margin: 0;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-down-enter-active {
  animation: slideDown 0.3s ease;
}

.slide-down-leave-active {
  animation: slideDown 0.2s ease reverse;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: fit-content;
  min-height: 90px;
  overflow-y: auto;
  padding: 0.25rem;
  border: 1px solid var(--color-background-dark);
  border-radius: var(--radius);
  background: #fff;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  border-radius: 0.25rem;
  transition: background 0.2s;
  font-size: var(--text-small);
}

.checkbox-item:hover {
  background: var(--color-background-light);
}

.checkbox-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-item input[type="checkbox"] {
  cursor: pointer;
  margin: 0;
}

.checkbox-item.disabled input[type="checkbox"] {
  cursor: not-allowed;
}

.checkbox-item span {
  user-select: none;
}


</style>