<!--
  TimelineCategoryLegend Component - Category Filter Sidebar
  
  Provides interactive legend for timeline chart filtering:
  - Type-level toggles (INCOME, EXPENSES, TRANSFERS, TARGETS)
  - Category-level toggles with color indicators
  - Subcategory expansion and toggles
  - Empty state when no categories exist
  
  Features:
  - Hierarchical category display (Type > Category > Subcategory)
  - Color-coded indicators for each level
  - Expandable/collapsible subcategories
  - Click to toggle visibility in chart
  - Icon mapping for category types
  - Responsive design (mobile stacks vertically)
  
  Props:
  - expenseCategories: Array - Expense category tree
  - incomeCategories: Array - Income category tree
  - transferCategories: Array - Transfer category tree
  - targetCategories: Array - Target category tree
  - visibleTypes: Array - Currently visible type IDs
  - visibleCategories: Array - Currently visible category IDs
  - visibleSubcategories: Array - Currently visible subcategory IDs
  - expandedCategories: Array - Currently expanded category IDs
  
  Events:
  - @toggle-type: Toggle type visibility
  - @toggle-category: Toggle category visibility
  - @toggle-subcategory: Toggle subcategory visibility
  - @toggle-category-expanded: Toggle category expansion
  
  Hierarchy:
  - Level 1 (Type): INCOME, EXPENSES, TRANSFERS, TARGETS
  - Level 2 (Category): Food, Transport, Salary, etc.
  - Level 3 (Subcategory): Groceries, Fuel, etc.
-->

<template>
  <div class="timeline-legend-sidebar container">
    <!-- Empty State -->
    <div v-if="!hasCategories" class="legend-empty-state">
      <AppIcon name="apps-sort" size="large" />
      <p class="empty-text">No categories yet</p>
      <p class="empty-subtext">Import transactions to populate categories</p>
    </div>

    <template v-else>
      <!-- EXPENSES Section -->
      <div v-if="expenseCategories.length > 0" class="legend-section">
        <!-- Type Header - Click to toggle all expenses -->
        <div 
          class="legend-type-header" 
          @click="$emit('toggle-type', 'expenses')"
        >
          <span 
            class="legend-indicator" 
            :style="{ backgroundColor: isTypeVisible('expenses') ? getTypeColor('expenses') : '#fff' }"
          ></span>
          <span class="legend-type-name">EXPENSES</span>
        </div>
        
        <!-- Expense Categories List -->
        <div class="legend-categories-list">
          <div 
            class="legend-category-item" 
            v-for="category in expenseCategories" 
            :key="category.id"
          >
            <div class="legend-category-row">
              <!-- Category Header - Click to toggle category -->
              <div 
                class="legend-category-header"
                @click="$emit('toggle-category', category.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-small" 
                  :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ category.name }}</span>
              </div>
              
              <!-- Expand/Collapse Button (if has subcategories) -->
              <button 
                v-if="category.children && category.children.length > 0"
                class="legend-expand-btn"
                @click.stop="$emit('toggle-category-expanded', category.id)"
              >
                <AppIcon 
                  :name="isCategoryExpanded(category.id) ? 'angle-down' : 'angle-right'" 
                  size="small" 
                />
              </button>
            </div>
            
            <!-- Subcategories List (when expanded) -->
            <div 
              v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
              class="legend-subcategories-list"
            >
              <div 
                class="legend-subcat-item" 
                v-for="subcat in category.children" 
                :key="subcat.id"
                @click="$emit('toggle-subcategory', subcat.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-tiny" 
                  :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ subcat.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- INCOME Section -->
      <div v-if="incomeCategories.length > 0" class="legend-section">
        <!-- Type Header - Click to toggle all income -->
        <div 
          class="legend-type-header" 
          @click="$emit('toggle-type', 'income')"
        >
          <span 
            class="legend-indicator" 
            :style="{ backgroundColor: isTypeVisible('income') ? getTypeColor('income') : '#fff' }"
          ></span>
          <span class="legend-type-name">INCOME</span>
        </div>
        
        <!-- Income Categories List -->
        <div class="legend-categories-list">
          <div 
            class="legend-category-item" 
            v-for="category in incomeCategories" 
            :key="category.id"
          >
            <div class="legend-category-row">
              <!-- Category Header -->
              <div 
                class="legend-category-header"
                @click="$emit('toggle-category', category.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-small" 
                  :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ category.name }}</span>
              </div>
              
              <!-- Expand/Collapse Button -->
              <button 
                v-if="category.children && category.children.length > 0"
                class="legend-expand-btn"
                @click.stop="$emit('toggle-category-expanded', category.id)"
              >
                <AppIcon 
                  :name="isCategoryExpanded(category.id) ? 'angle-down' : 'angle-right'" 
                  size="small" 
                />
              </button>
            </div>
            
            <!-- Subcategories List -->
            <div 
              v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
              class="legend-subcategories-list"
            >
              <div 
                class="legend-subcat-item" 
                v-for="subcat in category.children" 
                :key="subcat.id"
                @click="$emit('toggle-subcategory', subcat.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-tiny" 
                  :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ subcat.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TRANSFERS Section -->
      <div v-if="transferCategories.length > 0" class="legend-section">
        <!-- Type Header -->
        <div 
          class="legend-type-header" 
          @click="$emit('toggle-type', 'transfers')"
        >
          <span 
            class="legend-indicator" 
            :style="{ backgroundColor: isTypeVisible('transfers') ? getTypeColor('transfers') : '#fff' }"
          ></span>
          <span class="legend-type-name">TRANSFERS</span>
        </div>
        
        <!-- Transfer Categories List -->
        <div class="legend-categories-list">
          <div 
            class="legend-category-item" 
            v-for="category in transferCategories" 
            :key="category.id"
          >
            <div class="legend-category-row">
              <div 
                class="legend-category-header"
                @click="$emit('toggle-category', category.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-small" 
                  :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ category.name }}</span>
              </div>
              
              <button 
                v-if="category.children && category.children.length > 0"
                class="legend-expand-btn"
                @click.stop="$emit('toggle-category-expanded', category.id)"
              >
                <AppIcon 
                  :name="isCategoryExpanded(category.id) ? 'angle-down' : 'angle-right'" 
                  size="small" 
                />
              </button>
            </div>
            
            <div 
              v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
              class="legend-subcategories-list"
            >
              <div 
                class="legend-subcat-item" 
                v-for="subcat in category.children" 
                :key="subcat.id"
                @click="$emit('toggle-subcategory', subcat.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-tiny" 
                  :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ subcat.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TARGETS Section -->
      <div v-if="targetCategories.length > 0" class="legend-section">
        <!-- Type Header -->
        <div 
          class="legend-type-header" 
          @click="$emit('toggle-type', 'targets')"
        >
          <span 
            class="legend-indicator" 
            :style="{ backgroundColor: isTypeVisible('targets') ? getTypeColor('targets') : '#fff' }"
          ></span>
          <span class="legend-type-name">TARGETS</span>
        </div>
        
        <!-- Target Categories List -->
        <div class="legend-categories-list">
          <div 
            class="legend-category-item" 
            v-for="category in targetCategories" 
            :key="category.id"
          >
            <div class="legend-category-row">
              <div 
                class="legend-category-header"
                @click="$emit('toggle-category', category.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-small" 
                  :style="{ backgroundColor: isCategoryVisible(category.id) ? category.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ category.name }}</span>
              </div>
              
              <button 
                v-if="category.children && category.children.length > 0"
                class="legend-expand-btn"
                @click.stop="$emit('toggle-category-expanded', category.id)"
              >
                <AppIcon 
                  :name="isCategoryExpanded(category.id) ? 'angle-down' : 'angle-right'" 
                  size="small" 
                />
              </button>
            </div>
            
            <div 
              v-if="category.children && category.children.length > 0 && isCategoryExpanded(category.id)" 
              class="legend-subcategories-list"
            >
              <div 
                class="legend-subcat-item" 
                v-for="subcat in category.children" 
                :key="subcat.id"
                @click="$emit('toggle-subcategory', subcat.id)"
              >
                <span 
                  class="legend-indicator legend-indicator-tiny" 
                  :style="{ backgroundColor: isSubcategoryVisible(subcat.id) ? subcat.color : '#fff' }"
                ></span>
                <span class="legend-item-name">{{ subcat.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useCategoryStore } from '@/stores/categories'
import AppIcon from './AppIcon.vue'

export default {
  name: 'CategoryLegend',
  components: {
    AppIcon
  },
  props: {
    expenseCategories: {
      type: Array,
      required: true
    },
    incomeCategories: {
      type: Array,
      required: true
    },
    transferCategories: {
      type: Array,
      required: true
    },
    targetCategories: {
      type: Array,
      required: true
    },
    visibleTypes: {
      type: Array,
      required: true
    },
    visibleCategories: {
      type: Array,
      required: true
    },
    visibleSubcategories: {
      type: Array,
      required: true
    },
    expandedCategories: {
      type: Array,
      required: true
    }
  },
  emits: ['toggle-type', 'toggle-category', 'toggle-subcategory', 'toggle-category-expanded'],
  setup(props) {
    const categoryStore = useCategoryStore()
    
    /** @type {import('vue').ComputedRef<boolean>} */
    const hasCategories = computed(() => {
      return props.expenseCategories.length > 0 || 
             props.incomeCategories.length > 0 || 
             props.transferCategories.length > 0 ||
             props.targetCategories.length > 0
    })
    
    /**
     * Gets color for category type
     * @param {string} typeId - Type identifier (income, expenses, transfers, targets)
     * @returns {string} Hex color code
     */
    function getTypeColor(typeId) {
      const typeMap = {
        'income': '#00C9A0',
        'expenses': '#F17D99',
        'transfers': '#F0C46C',
        'targets': '#b54a4a'
      }
      
      const type = categoryStore.categories?.find(t => t.code === typeId || t.id === typeId)
      if (type?.color) return type.color
      
      return typeMap[typeId] || '#94a3b8'
    }
    
    /**
     * Checks if type is visible
     * @param {string} typeId - Type identifier
     * @returns {boolean} True if type is visible
     */
    function isTypeVisible(typeId) {
      return props.visibleTypes.includes(typeId)
    }
    
    /**
     * Checks if category is visible
     * @param {number} categoryId - Category ID
     * @returns {boolean} True if category is visible
     */
    function isCategoryVisible(categoryId) {
      return props.visibleCategories.includes(categoryId)
    }
    
    /**
     * Checks if subcategory is visible
     * @param {number} subcategoryId - Subcategory ID
     * @returns {boolean} True if subcategory is visible
     */
    function isSubcategoryVisible(subcategoryId) {
      return props.visibleSubcategories.includes(subcategoryId)
    }
    
    /**
     * Checks if category is expanded (showing subcategories)
     * @param {number} categoryId - Category ID
     * @returns {boolean} True if category is expanded
     */
    function isCategoryExpanded(categoryId) {
      return props.expandedCategories.includes(categoryId)
    }
    
    return {
      hasCategories,
      getTypeColor,
      isTypeVisible,
      isCategoryVisible,
      isSubcategoryVisible,
      isCategoryExpanded
    }
  }
}
</script>

<style scoped>
.timeline-legend-sidebar {
  width: 250px;
  flex-shrink: 0;
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-small);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.legend-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--gap-xxl);
  gap: var(--gap-small);
  text-align: center;
  min-height: 300px;
}

.empty-text {
  margin: 0;
  font-weight: 600;
  color: var(--color-text);
}

.empty-subtext {
  margin: 0;
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.legend-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.legend-type-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  font-weight: 600;
  font-size: var(--text-small);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.legend-type-header:hover {
  background: var(--color-background-dark);
}

.legend-type-name {
  user-select: none;
}

.legend-indicator {
  width: 1rem;
  height: 1rem;
  border-radius: 0.25rem;
  border: 2px solid var(--color-background-dark);
  flex-shrink: 0;
  transition: all 0.2s;
}

.legend-indicator-small {
  width: 0.875rem;
  height: 0.875rem;
}

.legend-indicator-tiny {
  width: 0.625rem;
  height: 0.625rem;
}

.legend-categories-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.legend-category-item {
  display: flex;
  flex-direction: column;
}

.legend-category-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.25rem;
}

.legend-category-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.8125rem;
  flex: 1;
}

.legend-category-header:hover {
  background: var(--color-background-dark);
}

.legend-item-name {
  user-select: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.legend-expand-btn {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-light);
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
  padding: 0;
}

.legend-expand-btn:hover {
  background: var(--color-background-dark);
}

.legend-subcategories-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-left: 1rem;
  margin-top: 0.25rem;
}

.legend-subcat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.375rem;
  background: var(--color-background-light);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.75rem;
}

.legend-subcat-item:hover {
  background: var(--color-background-dark);
}

@media (max-width: 64rem) {
  .timeline-legend-sidebar {
    width: 100%;
    max-height: 300px;
  }
}

@media (max-width: 48rem) {
  .timeline-legend-sidebar {
    padding: var(--gap-small);
  }
}

@media (max-width: 30rem) {
  .legend-type-header {
    font-size: 0.75rem;
    padding: 0.375rem 0.5rem;
  }
  
  .legend-category-header {
    font-size: 0.75rem;
  }
  
  .legend-subcat-item {
    font-size: 0.6875rem;
  }
}
</style>