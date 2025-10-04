<template>
  <div class="category-tree">
    <div v-for="type in categories" :key="type.id" class="category-type-group">
      <button
        class="category-btn"
        :class="{ active: isSelected(type.id) }"
        @click="$emit('select', type, 'type')"
      >
        <AppIcon :name="type.icon" size="medium" />
        <span>{{ type.name }}</span>
        <span v-if="showStats" class="category-stats">
          ({{ formatAmount(type.total_amount) }})
        </span>
      </button>

      <div v-if="type.children && type.children.length > 0" class="category-children">
        <div v-for="category in type.children" :key="category.id" class="category-item">
          <div class="category-header">
            <button
              class="category-btn category-indent"
              :class="{ active: isSelected(category.id) }"
              @click="$emit('select', category, 'category')"
            >
              <AppIcon :name="category.icon" size="medium" />
              <span>{{ category.name }}</span>
              <span v-if="showStats" class="category-stats">
                ({{ formatAmount(category.total_amount) }})
              </span>
            </button>

            <button
              v-if="category.children && category.children.length > 0"
              class="toggle-btn"
              @click="toggleExpanded(category.id)"
            >
              {{ isExpanded(category.id) ? '−' : '+' }}
            </button>
          </div>

          <div 
            v-if="category.children && category.children.length > 0 && isExpanded(category.id)"
            class="subcategories"
          >
            <button
              v-for="subcategory in category.children"
              :key="subcategory.id"
              class="category-btn category-indent-2"
              :class="{ active: isSelected(subcategory.id) }"
              @click="$emit('select', subcategory, 'subcategory')"
            >
              <AppIcon :name="subcategory.icon" size="medium" />
              <span>{{ subcategory.name }}</span>
              <span v-if="showStats" class="category-stats">
                ({{ formatAmount(subcategory.total_amount) }})
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'

export default {
  name: 'CategoryTree',
  components: { AppIcon },
  props: {
    categories: {
      type: Array,
      required: true
    },
    selectedId: {
      type: String,
      default: null
    },
    showStats: {
      type: Boolean,
      default: true
    }
  },
  emits: ['select'],
  setup(props) {
    const expandedCategories = ref({})

    function toggleExpanded(categoryId) {
      expandedCategories.value = {
        ...expandedCategories.value,
        [categoryId]: !expandedCategories.value[categoryId]
      }
    }

    function isExpanded(categoryId) {
      return !!expandedCategories.value[categoryId]
    }

    function isSelected(id) {
      return props.selectedId === id
    }

    function formatAmount(amount) {
      if (!amount) return '€0'
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(Math.abs(amount))
    }

    return {
      expandedCategories,
      toggleExpanded,
      isExpanded,
      isSelected,
      formatAmount
    }
  }
}
</script>

<style scoped>
.category-tree {
  display: flex;
  flex-direction: column;
  gap: var(--gap-small);
}

.category-type-group {
  display: flex;
  flex-direction: column;
}

.category-children {
  display: flex;
  flex-direction: column;
}

.category-item {
  display: flex;
  flex-direction: column;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  width: 100%;
  border-radius: var(--radius);
  transition: background 0.2s;
  font-family: "Livvic", sans-serif;
  font-weight: 400;
  color: var(--color-text-light);
}

.category-btn:hover {
  background: var(--color-background-light);
}

.category-btn.active {
  background: var(--color-background);
  font-weight: 600;
  color: var(--color-text);
}

.category-btn.active span {
  font-family: "MuseoModerno", sans-serif;
  font-style: italic;
}

.category-indent {
  margin-left: 0.5rem;
}

.category-indent-2 {
  margin-left: 1.5rem;
}

.category-stats {
  margin-left: auto;
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  font-size: var(--text-medium);
  font-weight: bold;
  color: var(--color-text-light);
}

.toggle-btn:hover {
  color: var(--color-text);
}

.subcategories {
  display: flex;
  flex-direction: column;
}
</style>