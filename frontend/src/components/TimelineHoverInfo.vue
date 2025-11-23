<template>
  <div class="hover-info-field" :class="{ 'hover-info-empty': !hoveredData }">
    <div v-if="!hoveredData" class="hover-info-placeholder">
      
    </div>
    
    <template v-else>
      <!-- Header with period name and total balance -->
      <div class="hover-info-header">
        <div class="hover-header-left">
          <h4>{{ hoveredData.periodName }}</h4>
        </div>
        <div></div>
        <div class="hover-header-right">
          <span class="hover-balance-label">Total Balance</span>
          <span class="hover-balance-value" :class="totalBalance >= 0 ? 'positive' : 'negative'">
            {{ formatCurrency(totalBalance) }}
          </span>
        </div>
        
        <button class="btn btn-icon hover-close-btn" @click="$emit('unpin')">
          <AppIcon name="cross" size="small" />
        </button>
      </div>
      
      <!-- Breakdown sections - multi-column when multiple breakdowns -->
      <div class="hover-info-content" :class="contentGridClass">
        <div 
          v-for="(data, key) in hoveredData.breakdownData" 
          :key="key"
          class="breakdown-section"
        >
          <!-- Breakdown header (Owner/Account name) -->
          <div v-if="hoveredData.breakdownMode !== 'all'" class="breakdown-header">
            <h5>{{ key }}</h5>
            <span class="breakdown-balance" :class="data.balance >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(data.balance) }}
            </span>
          </div>
          
          <!-- 2-Column Grid: Income+Transfers | Expenses -->
          <div class="hover-info-grid">
            <!-- LEFT COLUMN -->
            <div class="hover-info-column">
              <!-- INCOME -->
              <div v-if="data.income > 0" class="hover-info-type-section">
                <div class="hover-type-header">
                  <AppIcon name="apps-add" size="small" />
                  <span class="hover-type-label">INCOME</span>
                  <span class="hover-type-total positive">{{ formatCurrency(data.income) }}</span>
                </div>
                
                <div class="hover-info-tree" v-if="data.incomeByCategory">
                  <template v-for="item in buildCategoryTree(data.incomeByCategory, 'income')" :key="item.id">
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

              <!-- TRANSFERS OUT -->
              <div v-if="data.transfersOut > 0" class="hover-info-type-section">
                <div class="hover-type-header">
                  <AppIcon name="apps-sort" size="small" />
                  <span class="hover-type-label">TRANSFERS OUT</span>
                  <span class="hover-type-total neutral">{{ formatCurrency(data.transfersOut) }}</span>
                </div>
                
                <div class="hover-info-tree" v-if="data.transfersOutByCategory">
                  <template v-for="item in buildCategoryTree(data.transfersOutByCategory, 'transfers')" :key="item.id + '-out'">
                    <div class="hover-tree-main">
                      <AppIcon :name="item.icon" size="small" />
                      <span class="hover-tree-name">{{ item.name }}</span>
                      <span class="hover-tree-amount">{{ formatCurrency(item.total) }}</span>
                    </div>
                    
                    <div v-for="subcat in item.subcategories" :key="subcat.id + '-out'" class="hover-tree-sub">
                      <AppIcon :name="subcat.icon" size="small" />
                      <span class="hover-tree-name">{{ subcat.name }}</span>
                      <span class="hover-tree-amount">{{ formatCurrency(subcat.amount) }}</span>
                    </div>
                  </template>
                </div>
              </div>
              
              <!-- TRANSFERS IN -->
              <div v-if="data.transfersIn > 0" class="hover-info-type-section">
                <div class="hover-type-header">
                  <AppIcon name="apps-sort" size="small" />
                  <span class="hover-type-label">TRANSFERS IN</span>
                  <span class="hover-type-total neutral">{{ formatCurrency(data.transfersIn) }}</span>
                </div>
                
                <div class="hover-info-tree" v-if="data.transfersInByCategory">
                  <template v-for="item in buildCategoryTree(data.transfersInByCategory, 'transfers')" :key="item.id + '-in'">
                    <div class="hover-tree-main">
                      <AppIcon :name="item.icon" size="small" />
                      <span class="hover-tree-name">{{ item.name }}</span>
                      <span class="hover-tree-amount">{{ formatCurrency(item.total) }}</span>
                    </div>
                    
                    <div v-for="subcat in item.subcategories" :key="subcat.id + '-in'" class="hover-tree-sub">
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
              <!-- EXPENSES -->
              <div v-if="data.expenses > 0" class="hover-info-type-section">
                <div class="hover-type-header">
                  <AppIcon name="apps-delete" size="small" />
                  <span class="hover-type-label">EXPENSES</span>
                  <span class="hover-type-total negative">{{ formatCurrency(data.expenses) }}</span>
                </div>
                
                <div class="hover-info-tree" v-if="data.expensesByCategory">
                  <template v-for="item in buildCategoryTree(data.expensesByCategory, 'expenses')" :key="item.id">
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
    
    // Calculate total balance across all breakdowns
    const totalBalance = computed(() => {
      if (!props.hoveredData?.breakdownData) return 0
      
      return Object.values(props.hoveredData.breakdownData).reduce((sum, data) => {
        return sum + (data.balance || 0)
      }, 0)
    })
    
    // Determine grid columns based on number of breakdowns
    const contentGridClass = computed(() => {
      if (!props.hoveredData?.breakdownData) return ''
      
      const count = Object.keys(props.hoveredData.breakdownData).length
      
      if (count === 1) return 'grid-single'
      if (count === 2) return 'grid-two'
      return 'grid-three' // 3+ breakdowns
    })
    
    function findCategory(categoryName, typeCode) {
      if (!categoryStore.categories) return null
      
      const type = categoryStore.categories.find(t => t.code === typeCode)
      if (!type?.children) return null
      
      for (const mainCat of type.children) {
        if (mainCat.name === categoryName) return mainCat
        
        if (mainCat.children) {
          for (const subcat of mainCat.children) {
            if (subcat.name === categoryName) return subcat
          }
        }
      }
      
      return null
    }
    
    function buildCategoryTree(categoryData, typeCode) {
      if (!categoryData) return []
      
      const mainCategories = {}
      
      Object.entries(categoryData).forEach(([catName, amount]) => {
        if (amount <= 0) return
        
        const catInfo = findCategory(catName, typeCode)
        
        if (!catInfo) {
          // Category not found in tree - show it anyway with default icon
          const fallbackId = `fallback-${catName}`
          if (!mainCategories[fallbackId]) {
            mainCategories[fallbackId] = {
              id: fallbackId,
              name: catName,
              icon: 'circle',
              total: amount,
              subcategories: []
            }
          } else {
            mainCategories[fallbackId].total += amount
          }
          return
        }
        
        if (catInfo.parent_id) {
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
      
      Object.values(mainCategories).forEach(mainCat => {
        mainCat.subcategories.sort((a, b) => b.amount - a.amount)
      })
      
      return Object.values(mainCategories).sort((a, b) => b.total - a.total)
    }
    
    return {
      formatCurrency,
      buildCategoryTree,
      totalBalance,
      contentGridClass
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

.breakdown-section {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.breakdown-section + .breakdown-section {
  margin-top: var(--gap-large);
  padding-top: var(--gap-large);
  border-top: 2px solid var(--color-background-dark);
}

.breakdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--gap-small);
  background: var(--color-background-light);
  border-radius: var(--radius);
  margin-bottom: var(--gap-small);
}

.breakdown-header h5 {
  margin: 0;
  font-size: var(--text-medium);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.breakdown-balance {
  font-size: var(--text-large);
  font-weight: 700;
}

.breakdown-balance.positive {
  color: rgb(30, 155, 126);
}

.breakdown-balance.negative {
  color: rgb(106, 91, 155);
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

/* Multi-column grid layouts for multiple breakdowns */
.hover-info-content.grid-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-large);
}

.hover-info-content.grid-three {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--gap-large);
}

/* Remove vertical spacing when using grid */
.grid-two .breakdown-section + .breakdown-section,
.grid-three .breakdown-section + .breakdown-section {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
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
  padding: 0.5rem 0 0.25rem 1.25rem;
  font-size: 0.75rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  font-weight: 500;
}

.hover-tree-sub {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0 0.25rem 2.5rem;
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