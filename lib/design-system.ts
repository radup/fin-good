/**
 * Spend's Analysis Design System
 * Centralized design tokens and component definitions
 */

// Brand Colors
export const colors = {
  brand: {
    primary: '#00A8CC',        // Primary Blue from logo
    'primary-hover': '#006B7D', // Deep Teal  
    'primary-dark': '#031d24',  // Dark Navy
    accent: '#00E5FF',         // Bright Cyan
  },
  
  // Semantic Colors
  semantic: {
    success: '#22c55e',
    warning: '#f59e0b', 
    error: '#ef4444',
    info: '#3b82f6',
  },
  
  // Neutral Palette
  neutral: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
  
  // Background Colors
  background: {
    primary: '#ffffff',
    secondary: '#f8fafc',
    dark: '#031d24',
    card: '#ffffff',
    'card-hover': '#f8fafc',
  }
}

// Gradients
export const gradients = {
  primary: 'linear-gradient(135deg, #00A8CC 0%, #00E5FF 100%)',
  'primary-subtle': 'linear-gradient(135deg, #00A8CC 0%, #006B7D 100%)',
  data: 'linear-gradient(90deg, #00A8CC 0%, #00E5FF 50%, #006B7D 100%)',
  hero: 'linear-gradient(135deg, #031d24 0%, #006B7D 50%, #00A8CC 100%)',
}

// Typography Scale
export const typography = {
  fontFamilies: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
    display: ['Inter', 'system-ui', 'sans-serif'],
  },
  
  fontSizes: {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
    '5xl': '3rem',     // 48px
  },
  
  fontWeights: {
    normal: '400',
    medium: '500', 
    semibold: '600',
    bold: '700',
  },
  
  lineHeights: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  }
}

// Spacing System (based on 0.25rem = 4px)
export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
}

// Border Radius
export const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  '3xl': '1.5rem',  // 24px
  full: '9999px',
}

// Shadow System
export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  base: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  none: '0 0 #0000',
}

// Animation Presets
export const animations = {
  durations: {
    fast: '150ms',
    normal: '300ms', 
    slow: '500ms',
  },
  
  easings: {
    linear: 'linear',
    'ease-in': 'cubic-bezier(0.4, 0, 1, 1)',
    'ease-out': 'cubic-bezier(0, 0, 0.2, 1)', 
    'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
  
  transitions: {
    all: 'all 300ms cubic-bezier(0, 0, 0.2, 1)',
    colors: 'color 150ms cubic-bezier(0, 0, 0.2, 1), background-color 150ms cubic-bezier(0, 0, 0.2, 1), border-color 150ms cubic-bezier(0, 0, 0.2, 1)',
    opacity: 'opacity 150ms cubic-bezier(0, 0, 0.2, 1)',
    shadow: 'box-shadow 150ms cubic-bezier(0, 0, 0.2, 1)',
    transform: 'transform 150ms cubic-bezier(0, 0, 0.2, 1)',
  }
}

// Component Style Definitions
export const components = {
  // Button Variants
  button: {
    base: 'inline-flex items-center justify-center font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
    
    variants: {
      primary: 'bg-brand-primary text-white hover:bg-brand-primary-hover focus:ring-brand-primary',
      secondary: 'bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 focus:ring-brand-primary',
      ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-brand-primary',
      gradient: 'bg-gradient-to-r from-brand-primary to-brand-accent text-white hover:shadow-lg hover:scale-105 focus:ring-brand-accent',
    },
    
    sizes: {
      sm: 'px-3 py-1.5 text-sm rounded-md',
      base: 'px-4 py-2 text-base rounded-lg', 
      lg: 'px-6 py-3 text-lg rounded-xl',
    }
  },
  
  // Card Variants
  card: {
    base: 'bg-white border border-gray-100 shadow-sm transition-all',
    
    variants: {
      default: 'rounded-2xl',
      interactive: 'rounded-2xl hover:shadow-md hover:border-gray-200 cursor-pointer',
      elevated: 'rounded-2xl shadow-md',
    }
  },
  
  // Input Variants
  input: {
    base: 'block w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent transition-all',
    
    variants: {
      default: '',
      error: 'border-red-500 focus:ring-red-500',
      success: 'border-green-500 focus:ring-green-500',
    }
  },
  
  // Badge Variants
  badge: {
    base: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
    
    variants: {
      primary: 'bg-brand-primary/10 text-brand-primary',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      neutral: 'bg-gray-100 text-gray-800',
    }
  }
}

// Layout Tokens
export const layout = {
  containers: {
    xs: '480px',
    sm: '640px', 
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  
  sidebar: {
    width: '256px',        // 16rem
    collapsedWidth: '64px', // 4rem
  },
  
  header: {
    height: '64px',         // 4rem
  },
  
  grid: {
    columns: {
      1: 'grid-cols-1',
      2: 'grid-cols-2', 
      3: 'grid-cols-3',
      4: 'grid-cols-4',
      12: 'grid-cols-12',
    },
    
    gaps: {
      sm: 'gap-4',   // 1rem
      base: 'gap-6', // 1.5rem
      lg: 'gap-8',   // 2rem
    }
  }
}

// Semantic Tokens (context-specific)
export const semantic = {
  text: {
    primary: 'text-gray-900',
    secondary: 'text-gray-600', 
    muted: 'text-gray-500',
    inverse: 'text-white',
    brand: 'text-brand-primary',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
  },
  
  background: {
    primary: 'bg-white',
    secondary: 'bg-gray-50',
    brand: 'bg-brand-primary',
    'brand-dark': 'bg-brand-primary-dark',
    success: 'bg-green-50',
    warning: 'bg-yellow-50', 
    error: 'bg-red-50',
  },
  
  border: {
    default: 'border-gray-200',
    light: 'border-gray-100',
    brand: 'border-brand-primary',
    success: 'border-green-200',
    warning: 'border-yellow-200',
    error: 'border-red-200',
  }
}

// Wellness Thresholds for Financial Health Assessment
export const WELLNESS_THRESHOLDS = {
  // Categorization thresholds (percentage of transactions categorized)
  CATEGORIZATION_EXCELLENT: 95,  // 95%+ categorized = excellent
  CATEGORIZATION_GOOD: 80,       // 80-94% categorized = good
  
  // Expense ratio thresholds (expenses as % of income)
  EXPENSE_RATIO_HEALTHY: 70,     // ≤70% expenses = healthy
  EXPENSE_RATIO_WARNING: 85,     // 71-85% expenses = warning
  
  // Savings rate thresholds (savings as % of income)
  SAVINGS_RATE_GREAT: 20,        // ≥20% savings = great
  SAVINGS_RATE_GOOD: 10,         // 10-19% savings = good
  
  // Net income thresholds
  NET_INCOME_POSITIVE: 0,        // >0 = positive
  
  // Debt-to-income ratio thresholds
  DEBT_RATIO_HEALTHY: 30,        // ≤30% = healthy
  DEBT_RATIO_WARNING: 43,        // 31-43% = warning
}

// Main Design Tokens Object (combines all tokens)
export const DESIGN_TOKENS = {
  colors,
  gradients,
  typography,
  spacing,
  borderRadius,
  shadows,
  animations,
  components,
  layout,
  semantic,
  WELLNESS_THRESHOLDS,
}

// Legacy export for backward compatibility
export const getBadgeColorClasses = (status: 'success' | 'warning' | 'danger' | 'info') => {
  const colorMap = {
    success: 'bg-emerald-100 text-emerald-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-purple-100 text-purple-800'
  }
  return colorMap[status] || colorMap.info
}

// Legacy color constants for backward compatibility
export const COLORS = {
  SUCCESS: {
    BG: 'bg-emerald-50',
    BORDER: 'border-emerald-200',
    TEXT: 'text-emerald-800',
    ICON: 'text-emerald-600',
    LIGHT_BG: 'bg-emerald-100',
    LIGHT_TEXT: 'text-emerald-600'
  },
  WARNING: {
    BG: 'bg-amber-50',
    BORDER: 'border-amber-200',
    TEXT: 'text-amber-800',
    ICON: 'text-amber-600',
    LIGHT_BG: 'bg-amber-100',
    LIGHT_TEXT: 'text-amber-600'
  },
  DANGER: {
    BG: 'bg-red-50',
    BORDER: 'border-red-200',
    TEXT: 'text-red-800',
    ICON: 'text-red-600',
    LIGHT_BG: 'bg-red-100',
    LIGHT_TEXT: 'text-red-600'
  },
  INFO: {
    BG: 'bg-brand-primary-lightest',
    BORDER: 'border-brand-primary-light',
    TEXT: 'text-brand-primary-dark',
    ICON: 'text-brand-primary',
    LIGHT_BG: 'bg-brand-primary-lightest',
    LIGHT_TEXT: 'text-brand-primary'
  }
}