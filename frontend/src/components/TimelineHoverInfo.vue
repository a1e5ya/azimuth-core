<template>
  <div class="hover-info-field" :class="{ 'hover-info-empty': !hoveredData }">
    <div v-if="!hoveredData" class="hover-info-placeholder">
      
    </div>
    
    <template v-else>
      <div class="hover-info-header">
        <div class="hover-header-left">
          <h4>{{ hoveredData.periodName }}</h4>
        </div>
        <div></div>
        <div class="hover-header-right">
          <span class="hover-balance-label">Balance</span>
          <span class="hover-balance-value" :class="hoveredData.balance >= 0 ? 'positive' : 'negative'">
            {{ formatCurrency(hoveredData.balance) }}
          </span>
        </div>
        
        <button class="btn btn-icon hover-close-btn" @click="$emit('unpin')">
          <AppIcon name="cross" size="small" />
        </button>
      </div>
      
      <div class="hover-info-content">
        <!-- 2-Column Grid: Income+Transfers | Expenses -->
        <div class="hover-info-grid">
          <!-- LEFT COLUMN: Income + Transfers -->
          <div class="hover-info-column">
            <!-- INCOME Section -->
            <div v-if="hoveredData.income > 0" class="hover-info-type-section">
              <div class="hover-type-header">
                <AppIcon name="apps-add" size="small" />
                <span class="hover-type-label">INCOME</span>
                <span class="hover-type-total positive">{{ formatCurrency(hoveredData.income) }}</span>
              </div>
              
              <div class="hover-info-tree" v-if="hoveredData.incomeByCategory">
                <template v-for="item in buildCategoryTree(hoveredData.incomeByCategory, 'income')" :key="item.id">
                  <div class="hover-tree-main">
                    <AppIcon :name="item.icon" size="small" />
                    <span class="hover-tree-name">{{ item.name }}</span>
                    <span class="hover-tree-amount">{{ formatCurrency(item.total) }}</span>
                  </div>
                  
                  <div v-for="subcat in item.subcategories" :key="subcat.id" class="hover-tree-sub">
                    <AppIcon :name="subcat.icon" size="small" />
                    <span class="hover-tree-name">{{ subcat.name }}</span>
                    <span class="hover-tree-amount">{{ formatCurrency(subcat.amount) }}</span>
                  </div>
                </template>
              </div>
            </div>

            <!-- TRANSFERS Section -->
            <div v-if="hoveredData.transfers > 0" class="hover-info-type-section">
              <div class="hover-type-header">
                <AppIcon name="apps-sort" size="small" />
                <span class="hover-type-label">TRANSFERS</span>
                <span class="hover-type-total neutral">{{ formatCurrency(hoveredData.transfers) }}</span>
              </div>
              
              <div class="hover-info-tree" v-if="hoveredData.transfersByCategory">
                <template v-for="item in buildCategoryTree(hoveredData.transfersByCategory, 'transfers')" :key="item.id">
                  <div class="hover-tree-main">
                    <AppIcon :name="item.icon" size="small" />
                    <span class="hover-tree-name">{{ item.name }}</span>
                    <span class="hover-tree-amount">{{ formatCurrency(item.total) }}</span>
                  </div>
                  
                  <div v-for="subcat in item.subcategories" :key="subcat.id" class="hover-tree-sub">
                    <AppIcon :name="subcat.icon" size="small" />
                    <span class="hover-tree-name">{{ subcat.name }}</span>
                    <span class="hover-tree-amount">{{ formatCurrency(subcat.amount) }}</span>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- RIGHT COLUMN: Expenses -->
          <div class="hover-info-column">
            <!-- EXPENSES Section -->
            <div v-if="hoveredData.expenses > 0" class="hover-info-type-section">
              <div class="hover-type-header">
                <AppIcon name="apps-delete" size="small" />
                <span class="hover-type-label">EXPENSES</span>
                <span class="hover-type-total negative">{{ formatCurrency(hoveredData.expenses) }}</span>
              </div>
              
              <div class="hover-info-tree" v-if="hoveredData.expensesByCategory">
                <template v-for="item in buildCategoryTree(hoveredData.expensesByCategory, 'expenses')" :key="item.id">
                  <div class="hover-tree-main">
                    <AppIcon :name="item.icon" size="small" />
                    <span class="hover-tree-name">{{ item.name }}</span>
                    <span class="hover-tree-amount">{{ formatCurrency(item.total) }}</span>
                  </div>
                  
                  <div v-for="subcat in item.subcategories" :key="subcat.id" class="hover-tree-sub">
                    <AppIcon :name="subcat.icon" size="small" />
                    <span class="hover-tree-name">{{ subcat.name }}</span>
                    <span class="hover-tree-amount">{{ formatCurrency(subcat.amount) }}</span>
                  </div>
                </template>
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
import AppIcon from './AppIcon.vue'
import { formatCurrency } from '@/utils/timelineHelpers'
import { useCategoryStore } from '@/stores/categories'

export default {
  name: 'TimelineHoverInfo',
  components: {
    AppIcon
  },
  props: {
    hoveredData: {
      type: Object,
      default: null
    }
  },
  emits: ['unpin'],
  setup(props) {
    const categoryStore = useCategoryStore()
    
    /**
     * Find category info by name
     */
    function findCategory(categoryName, typeCode) {
      if (!categoryStore.categories) return null
      
      const type = categoryStore.categories.find(t => t.code === typeCode)
      if (!type?.children) return null
      
      // Search in main categories
      for (const mainCat of type.children) {
        if (mainCat.name === categoryName) return mainCat
        
        // Search in subcategories
        if (mainCat.children) {
          for (const subcat of mainCat.children) {
            if (subcat.name === categoryName) return subcat
          }
        }
      }
      
      return null
    }
    
    /**
     * Build hierarchical tree from flat category list
     */
    function buildCategoryTree(categoryData, typeCode) {
      if (!categoryData) return []
      
      const mainCategories = {}
      
      // Group by main category
      Object.entries(categoryData).forEach(([catName, amount]) => {
        if (amount <= 0) return
        
        const catInfo = findCategory(catName, typeCode)
        if (!catInfo) return
        
        // Check if this is a subcategory
        if (catInfo.parent_id) {
          // Find parent
          const type = categoryStore.categories?.find(t => t.code === typeCode)
          const parent = type?.children?.find(c => c.id === catInfo.parent_id)
          
          if (parent) {
            if (!mainCategories[parent.id]) {
              mainCategories[parent.id] = {
                id: parent.id,
                name: parent.name,
                icon: parent.icon || 'circle',
                total: 0,
                subcategories: []
              }
            }
            
            mainCategories[parent.id].total += amount
            mainCategories[parent.id].subcategories.push({
              id: catInfo.id,
              name: catInfo.name,
              icon: catInfo.icon || 'circle',
              amount: amount
            })
          }
        } else {
          // This is a main category
          if (!mainCategories[catInfo.id]) {
            mainCategories[catInfo.id] = {
              id: catInfo.id,
              name: catInfo.name,
              icon: catInfo.icon || 'circle',
              total: amount,
              subcategories: []
            }
          } else {
            mainCategories[catInfo.id].total += amount
          }
        }
      })
      
      // Sort subcategories by amount
      Object.values(mainCategories).forEach(mainCat => {
        mainCat.subcategories.sort((a, b) => b.amount - a.amount)
      })
      
      // Sort main categories by total
      return Object.values(mainCategories).sort((a, b) => b.total - a.total)
    }
    
    return {
      formatCurrency,
      buildCategoryTree
    }
  }
}
</script>

<style scoped>
.hover-info-field {
  background: var(--color-background);
  border-radius: var(--radius);
  padding: var(--gap-standard);
  border: 2px solid var(--color-background-dark);
  min-height: 8rem;
}

.hover-info-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.hover-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--gap-standard);
  padding-bottom: var(--gap-small);
  border-bottom: 2px solid var(--color-background-dark);
  gap: var(--gap-standard);
}

.hover-header-left h4 {
  margin: 0;
  font-size: var(--text-medium);
  font-weight: 600;
}

.hover-header-right {
  display: flex;
  align-items: center;
  gap: var(--gap-large);
}

.hover-balance-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  color: var(--color-text-light);
}

.hover-balance-value {
  font-size: var(--text-large);
  font-weight: 700;
}

.hover-balance-value.positive {
  color: rgb(30, 155, 126);
}

.hover-balance-value.negative {
  color: rgb(106, 91, 155);
}

.hover-close-btn {
  width: 1.5rem;
  height: 1.5rem;
  padding: 0.25rem;
  background: transparent;
  box-shadow: none;
  margin: 0;
}

.hover-close-btn:hover {
  background: var(--color-background-dark);
}

.hover-info-content {
  display: flex;
  flex-direction: column;
}

.hover-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-large);
}

.hover-info-column {
  display: flex;
  flex-direction: column;
  gap: var(--gap-standard);
}

.hover-info-type-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.hover-type-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgb(58 50 50 / 20%);
  font-weight: 600;
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.hover-type-label {
  flex: 1;
}

.hover-type-total {
  font-size: var(--text-medium);
  font-weight: 700;
}

.hover-type-total.positive {
  color: rgb(30, 155, 126);
}

.hover-type-total.negative {
  color: rgb(106, 91, 155);
}

.hover-type-total.neutral {
  color: rgb(212, 166, 71);
}

.hover-info-tree {
  display: flex;
  flex-direction: column;
}

.hover-tree-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0 0.25rem 1.25rem;
  font-size: 0.75rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  font-weight: 500;
}

.hover-tree-sub {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0 0.5rem 2.5rem;
  font-size: 0.6875rem;
  opacity: 0.85;
}

.hover-tree-sub:last-child {
  border-bottom: none;
}

.hover-tree-name {
  flex: 1;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hover-tree-main .hover-tree-name {
font-weight: 600;
}

.hover-tree-amount {
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  font-size: 0.75rem;
}

.hover-tree-sub .hover-tree-amount {
  font-weight: 400;
  font-size: 0.6875rem;
}
</style>