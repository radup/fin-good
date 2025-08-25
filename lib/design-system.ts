// Design System Constants
// Extracted from components to improve maintainability and consistency

export const DESIGN_TOKENS = {
  // Color Classes
  COLORS: {
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
  },

  // Wellness Thresholds
  WELLNESS_THRESHOLDS: {
    CATEGORIZATION_EXCELLENT: 90,
    CATEGORIZATION_GOOD: 70,
    EXPENSE_RATIO_HEALTHY: 70,
    EXPENSE_RATIO_WARNING: 90,
    SAVINGS_RATE_GREAT: 20,
    SAVINGS_RATE_GOOD: 10
  } as const,

  // Animation Classes
  ANIMATIONS: {
    TRANSITION: 'therapeutic-transition',
    HOVER: 'therapeutic-hover'
  },

  // Spacing
  SPACING: {
    SECTION_GAP: 'space-y-6',
    CARD_PADDING: 'p-4',
    BUTTON_PADDING: 'px-4 py-2'
  }
} as const

// Helper function to get color classes based on wellness status
export const getWellnessColorClasses = (status: 'success' | 'warning' | 'danger' | 'info') => {
  const colorMap = {
    success: DESIGN_TOKENS.COLORS.SUCCESS,
    warning: DESIGN_TOKENS.COLORS.WARNING,
    danger: DESIGN_TOKENS.COLORS.DANGER,
    info: DESIGN_TOKENS.COLORS.INFO
  }
  
  return colorMap[status]
}

// Helper function to get badge color classes
export const getBadgeColorClasses = (status: 'success' | 'warning' | 'danger' | 'info') => {
  const colorMap = {
    success: 'bg-emerald-100 text-emerald-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-purple-100 text-purple-800'
  }
  
  return colorMap[status]
}
