/**
 * Icon Mappings - Semantic Icon Name Resolution
 * 
 * Maps semantic/functional names to actual fi-rr (Flat Icon Regular) icon names.
 * This abstraction layer allows:
 * - Consistent icon usage across the app
 * - Easy icon library migration (just update mappings)
 * - Semantic naming (e.g., 'add' instead of remembering 'plus')
 * - Centralized icon management
 * 
 * Icon Library: fi-rr (Flat Icon Regular)
 * Usage: Import getIconName() and use semantic names in components
 * 
 * Example:
 * ```js
 * import { getIconName } from '@/utils/iconMappings'
 * const iconClass = `fi-rr-${getIconName('add')}` // Returns: fi-rr-plus
 * ```
 */

// ============================================================================
// ICON MAPPINGS OBJECT
// ============================================================================

/**
 * Semantic icon name mappings
 * 
 * Organized by category for easy maintenance:
 * - App Navigation: Main app sections
 * - User Actions: User-related operations
 * - File Operations: File management
 * - Financial: Money and banking icons
 * - Actions: Common CRUD operations
 * - Status: Success/error/warning states
 * - Navigation: Directional navigation
 * 
 * Each key is a semantic name, value is the actual fi-rr icon name.
 */
export const iconMappings = {
  // ========================================
  // App Navigation
  // ========================================
  'dashboard': 'apps',
  'transactions': 'list-check',
  'categories': 'apps-sort',
  'timeline': 'time-half-past',
  'settings': 'settings-sliders',
  
  // ========================================
  // User Actions
  // ========================================
  'user': 'user',
  'login': 'user',
  'logout': 'power',
  'profile': 'user',
  
  // ========================================
  // File Operations
  // ========================================
  'upload': 'upload',
  'download': 'download',
  'file': 'file',
  'folder': 'folder',
  
  // ========================================
  // Financial
  // ========================================
  'money': 'dollar',
  'bank': 'bank',
  'credit-card': 'credit-card',
  'wallet': 'wallet',
  'chart': 'chart-line-up',
  'calculator': 'calculator',
  
  // ========================================
  // Actions
  // ========================================
  'add': 'plus',
  'edit': 'edit',
  'delete': 'trash',
  'save': 'disk',
  'search': 'search',
  'filter': 'filter',
  
  // ========================================
  // Status
  // ========================================
  'success': 'check',
  'error': 'cross',
  'warning': 'exclamation',
  'info': 'info',
  
  // ========================================
  // Navigation
  // ========================================
  'back': 'arrow-left',
  'forward': 'arrow-right',
  'up': 'arrow-up',
  'down': 'arrow-down',
  'close': 'cross',
  'menu': 'menu-burger',
  
}

// ============================================================================
// HELPER FUNCTION
// ============================================================================

/**
 * Get the correct icon name for a semantic name
 * 
 * Looks up semantic name in mappings and returns actual icon name.
 * Falls back to the input name if no mapping exists (allows direct icon names).
 * 
 * @param {string} semanticName - Semantic icon name (e.g., 'add', 'delete')
 * @returns {string} Actual fi-rr icon name (e.g., 'plus', 'trash')
 * 
 * @example
 * // Using semantic name
 * getIconName('add') // Returns: 'plus'
 * 
 * @example
 * // Fallback to direct name if not mapped
 * getIconName('custom-icon') // Returns: 'custom-icon'
 * 
 * @example
 * // In component
 * const iconClass = `fi-rr-${getIconName('add')}`
 * // Result: 'fi-rr-plus'
 */
export const getIconName = (semanticName) => {
  return iconMappings[semanticName] || semanticName
}