<template>
  <div class="filters-panel-compact" v-if="show">
    <!-- First Row: Date Range & Amounts -->
    <div class="filters-row">
      <div class="filter-group-compact">
        <label>From Date</label>
        <input 
          type="date" 
          v-model="localFilters.startDate"
          class="filter-input-compact"
          @change="emitFilters"
        >
      </div>
      
      <div class="filter-group-compact">
        <label>To Date</label>
        <input 
          type="date" 
          v-model="localFilters.endDate"
          class="filter-input-compact"
          @change="emitFilters"
        >
      </div>
      
      <div class="filter-group-compact">
        <label>Min Amount</label>
        <input 
          type="number" 
          v-model.number="localFilters.minAmount"
          class="filter-input-compact"
          placeholder="0.00"
          step="0.01"
          @change="emitFilters"
        >
      </div>
      
      <div class="filter-group-compact">
        <label>Max Amount</label>
        <input 
          type="number" 
          v-model.number="localFilters.maxAmount"
          class="filter-input-compact"
          placeholder="1000.00"
          step="0.01"
          @change="emitFilters"
        >
      </div>
    </div>
    
    <!-- Second Row: Owner & Account Type -->
    <div class="filters-row">
      <div class="filter-group-compact">
        <label>Owner</label>
        <select 
          v-model="localFilters.owners" 
          class="filter-input-compact"
          multiple
          size="3"
          @change="handleOwnerChange"
        >
          <option 
            v-for="owner in availableOwners" 
            :key="owner" 
            :value="owner"
          >
            {{ owner }}
          </option>
        </select>
      </div>
      
      <div class="filter-group-compact">
        <label>Account Type</label>
        <select 
          v-model="localFilters.accountTypes" 
          class="filter-input-compact"
          multiple
          size="3"
          @change="handleAccountTypeChange"
        >
          <option 
            v-for="type in availableAccountTypes" 
            :key="type" 
            :value="type"
          >
            {{ type }}
          </option>
        </select>
      </div>
      
      <div class="filter-group-compact">
        <label>Type</label>
        <select 
          v-model="localFilters.types" 
          class="filter-input-compact"
          multiple
          size="3"
          @change="handleTypeChange"
        >
          <option 
            v-for="type in availableTypes" 
            :key="type" 
            :value="type"
          >
            {{ type }}
          </option>
        </select>
      </div>
      
      <div class="filter-group-compact">
        <label>Category</label>
        <select 
          v-model="localFilters.categories" 
          class="filter-input-compact"
          multiple
          size="3"
          :disabled="localFilters.types.length === 0"
          @change="handleCategoryChange"
        >
          <option 
            v-for="category in availableCategories" 
            :key="category" 
            :value="category"
          >
            {{ category }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- Third Row: Subcategories & Search -->
    <div class="filters-row filters-row-actions">
      <div class="filter-group-compact">
        <label>Subcategory</label>
        <select 
          v-model="localFilters.subcategories" 
          class="filter-input-compact"
          multiple
          size="3"
          :disabled="localFilters.categories.length === 0"
          @change="emitFilters"
        >
          <option 
            v-for="subcategory in availableSubcategories" 
            :key="subcategory" 
            :value="subcategory"
          >
            {{ subcategory }}
          </option>
        </select>
      </div>
      
      <div class="filter-group-compact filter-search-compact">
        <label>Search</label>
        <input 
          type="text" 
          v-model="localFilters.merchant"
          class="filter-input-compact"
          placeholder="Search merchant, message..."
          @input="emitFilters"
        >
      </div>
      
      <div class="filter-actions-compact">
        <button class="btn btn-small" @click="clearAllFilters">Clear</button>
        <button class="btn btn-small" @click="$emit('update:show', false)">Hide</button>
      </div>
    </div>
  </div>
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
  emits: ['update:modelValue', 'update:show'],
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

    // Initialize from parent
    watch(() => props.modelValue, (newVal) => {
      localFilters.value = { ...newVal }
    }, { immediate: true, deep: true })

    // Available owners - all unique owners
    const availableOwners = computed(() => {
      if (!props.filterOptions.ownerAccountMap) return []
      return Object.keys(props.filterOptions.ownerAccountMap).sort()
    })

    // Available account types - filtered by selected owners
    const availableAccountTypes = computed(() => {
      if (!props.filterOptions.ownerAccountMap) return []
      
      // If no owners selected, show all account types
      if (localFilters.value.owners.length === 0) {
        const allTypes = new Set()
        Object.values(props.filterOptions.ownerAccountMap).forEach(types => {
          types.forEach(type => allTypes.add(type))
        })
        return Array.from(allTypes).sort()
      }
      
      // Show only account types for selected owners
      const types = new Set()
      localFilters.value.owners.forEach(owner => {
        const ownerTypes = props.filterOptions.ownerAccountMap[owner] || []
        ownerTypes.forEach(type => types.add(type))
      })
      return Array.from(types).sort()
    })

    // Available types (main categories)
    const availableTypes = computed(() => {
      return props.filterOptions.mainCategories || []
    })

    // Available categories - filtered by selected types
    const availableCategories = computed(() => {
      if (!props.filterOptions.categoryMap) return []
      
      // If no types selected, show no categories
      if (localFilters.value.types.length === 0) return []
      
      const categories = new Set()
      localFilters.value.types.forEach(type => {
        const typeCats = props.filterOptions.categoryMap[type] || []
        typeCats.forEach(cat => categories.add(cat))
      })
      return Array.from(categories).sort()
    })

    // Available subcategories - filtered by selected categories
    const availableSubcategories = computed(() => {
      if (!props.filterOptions.subcategoryMap) return []
      
      // If no categories selected, show no subcategories
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

    const emitFilters = () => {
      emit('update:modelValue', { ...localFilters.value })
    }

    const handleOwnerChange = () => {
      // Filter out account types that are no longer available
      const validTypes = availableAccountTypes.value
      localFilters.value.accountTypes = localFilters.value.accountTypes.filter(
        type => validTypes.includes(type)
      )
      emitFilters()
    }

    const handleAccountTypeChange = () => {
      emitFilters()
    }

    const handleTypeChange = () => {
      // Filter out categories that are no longer available
      const validCategories = availableCategories.value
      localFilters.value.categories = localFilters.value.categories.filter(
        cat => validCategories.includes(cat)
      )
      
      // Filter out subcategories that are no longer available
      const validSubcategories = availableSubcategories.value
      localFilters.value.subcategories = localFilters.value.subcategories.filter(
        sub => validSubcategories.includes(sub)
      )
      
      emitFilters()
    }

    const handleCategoryChange = () => {
      // Filter out subcategories that are no longer available
      const validSubcategories = availableSubcategories.value
      localFilters.value.subcategories = localFilters.value.subcategories.filter(
        sub => validSubcategories.includes(sub)
      )
      
      emitFilters()
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
      emitFilters()
    }

    return {
      localFilters,
      availableOwners,
      availableAccountTypes,
      availableTypes,
      availableCategories,
      availableSubcategories,
      emitFilters,
      handleOwnerChange,
      handleAccountTypeChange,
      handleTypeChange,
      handleCategoryChange,
      clearAllFilters
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

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
  }
  to {
    opacity: 1;
    max-height: 30rem;
    padding-top: var(--gap-standard);
    padding-bottom: var(--gap-standard);
  }
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
  grid-template-columns: 1fr 1fr auto;
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

.filter-input-compact {
  padding: 0.375rem 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  background: var(--color-button);
  font-size: var(--text-small);
  transition: border-color 0.2s ease;
}

.filter-input-compact:focus {
  outline: none;
  border-color: var(--color-button-active);
}

.filter-input-compact[multiple] {
  padding: 0.25rem;
}

.filter-input-compact[multiple] option {
  padding: 0.25rem;
  cursor: pointer;
}

.filter-input-compact[multiple] option:hover {
  background: var(--color-background-dark);
}

.filter-input-compact:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filter-search-compact {
  flex: 1;
}

.filter-actions-compact {
  display: flex;
  gap: var(--gap-small);
  align-items: flex-end;
  justify-content: flex-end;
}
</style>