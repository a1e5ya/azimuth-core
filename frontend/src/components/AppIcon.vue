<!--
  AppIcon Component - Dynamic SVG Icon Loader
  
  Dynamically loads and displays SVG icons from the fi-rr (Flat Icon Regular) icon set.
  
  Features:
  - Dynamic SVG import from @/assets/icons
  - Automatic icon name normalization (adds 'fi-rr-' prefix)
  - Multiple size presets (small, medium, large, xl)
  - Custom color support
  - Fallback icon if not found
  - ViewBox auto-addition for proper scaling
  - SVG attribute cleaning (removes stroke, sets fill)
  
  Usage:
  <AppIcon name="user" size="medium" color="#3b82f6" />
  <AppIcon name="fi-rr-check" size="large" />
  
  Props:
  - name: Icon name (with or without 'fi-rr-' prefix)
  - size: Icon size preset (small/medium/large/xl)
  - color: Icon color (hex/rgb/css color)
  
  Size Reference:
  - small: 1rem (16px)
  - medium: 1.5rem (24px) - default
  - large: 2rem (32px)
  - xl: 3rem (48px)
-->

<template>
  <div 
    :class="['icon-wrapper', sizeClass]" 
    v-html="svgContent"
    :style="{ color: color }"
  />
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'

export default {
  name: 'AppIcon',
  
  props: {
    /**
     * Icon name (with or without 'fi-rr-' prefix)
     * Examples: 'user', 'check', 'fi-rr-apps'
     */
    name: {
      type: String,
      required: true
    },
    
    /**
     * Icon size preset
     * Options: 'small' (16px), 'medium' (24px), 'large' (32px), 'xl' (48px)
     */
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large', 'xl'].includes(value)
    },
    
    /**
     * Icon color (any CSS color value)
     * Examples: '#3b82f6', 'rgb(59, 130, 246)', 'blue'
     */
    color: {
      type: String,
      default: '#4a4a4a'
    }
  },
  
  setup(props) {
    /** @type {Ref<string>} SVG content HTML string */
    const svgContent = ref('')
    
    /**
     * Load SVG icon from assets
     * 
     * Process:
     * 1. Normalize icon name (add 'fi-rr-' prefix if missing)
     * 2. Dynamically import SVG file
     * 3. Clean SVG attributes (remove stroke, set fill)
     * 4. Add viewBox if missing for proper scaling
     * 5. Set fallback icon if import fails
     * 
     * SVG Cleaning:
     * - Removes stroke and stroke-width attributes
     * - Replaces all fill attributes with default color
     * - Adds viewBox="0 0 24 24" if missing
     * 
     * Called on:
     * - Component mount
     * - Icon name prop changes
     */
    const loadIcon = async () => {
      try {
        // Clean the icon name - remove 'fi-rr-' prefix if it exists
        const cleanName = props.name.replace(/^fi-rr-/, '')
        const iconName = `fi-rr-${cleanName}`
        
        // Dynamic import of SVG file from assets
        const iconModule = await import(`@/assets/icons/${iconName}.svg?raw`)
        
        // Get the SVG content and clean it up
        let svg = iconModule.default
        
        // Add viewBox if missing for proper scaling
        if (!svg.includes('viewBox')) {
          svg = svg.replace('<svg', '<svg viewBox="0 0 24 24"')
        }
        
        // Remove all stroke attributes (ensures solid fill)
        svg = svg.replace(/stroke="[^"]*"/g, '')
        svg = svg.replace(/stroke-width="[^"]*"/g, '')
        
        // Replace all fill attributes with default color
        svg = svg.replace(/fill="[^"]*"/g, 'fill="#4a4a4a"')
        
        // If no fill attribute exists, add it to svg element
        if (!svg.includes('fill=')) {
          svg = svg.replace('<svg', '<svg fill="#4a4a4a"')
        }
        
        svgContent.value = svg
      } catch (error) {
        console.warn(`Icon "${props.name}" not found:`, error)
        
        // Simple fallback: small circle
        svgContent.value = `
          <svg viewBox="0 0 24 24" fill="#4a4a4a">
            <circle cx="12" cy="12" r="2"/>
          </svg>
        `
      }
    }
    
    // Load icon on mount
    onMounted(loadIcon)
    
    // Reload icon when name changes
    watch(() => props.name, loadIcon)
    
    /**
     * Compute CSS class for icon size
     * @type {ComputedRef<string>} 'icon-small', 'icon-medium', 'icon-large', or 'icon-xl'
     */
    const sizeClass = computed(() => `icon-${props.size}`)
    
    return {
      svgContent,
      sizeClass
    }
  }
}
</script>

<style scoped>
/* Icon wrapper - centers SVG content */
.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

/* SVG element styles - inherits color from wrapper */
.icon-wrapper :deep(svg) {
  width: 1.2rem;
  height: 1.2rem;
  color: inherit;
}

/* Size presets */
.icon-small {
  width: 1rem;
  height: 1rem;
}

.icon-medium {
  width: 1.5rem;
  height: 1.5rem;
}

.icon-large {
  width: 2rem;
  height: 2rem;
}

.icon-xl {
  width: 3rem;
  height: 3rem;
}
</style>