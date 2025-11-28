/**
 * Counter Store - Simple Counter Example
 * 
 * Demo store showing Pinia composition API basics.
 * Demonstrates:
 * - Reactive state (ref)
 * - Computed values (computed)
 * - Actions (functions)
 * 
 * This is a minimal example store, typically used for:
 * - Learning Pinia patterns
 * - Testing store setup
 * - Quick prototyping
 * 
 * Can be removed in production if not used.
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', () => {
  // ========================================
  // STATE
  // ========================================
  
  /** @type {Ref<number>} Current count value */
  const count = ref(0)
  
  // ========================================
  // COMPUTED
  // ========================================
  
  /** 
   * Double the current count
   * @type {ComputedRef<number>} Count multiplied by 2
   */
  const doubleCount = computed(() => count.value * 2)
  
  // ========================================
  // ACTIONS
  // ========================================
  
  /**
   * Increment counter by 1
   * 
   * Simple action demonstrating state mutation.
   * In production stores, this would typically be async
   * and interact with backend APIs.
   */
  function increment() {
    count.value++
  }

  // ========================================
  // EXPOSED API
  // ========================================
  
  return { 
    // State
    count, 
    
    // Computed
    doubleCount, 
    
    // Actions
    increment 
  }
})