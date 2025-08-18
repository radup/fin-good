// Design System Constants
// Extracted from components to improve maintainability and consistency

export const DESIGN_TOKENS = {
  // Color Classes
  COLORS: {
    SUCCESS: {
      BG: 'bg-success-50',
      BORDER: 'border-success-200',
      TEXT: 'text-success-800',
      ICON: 'text-success-600',
      LIGHT_BG: 'bg-success-100',
      LIGHT_TEXT: 'text-success-600'
    },
    WARNING: {
      BG: 'bg-warning-50',
      BORDER: 'border-warning-200',
      TEXT: 'text-warning-800',
      ICON: 'text-warning-600',
      LIGHT_BG: 'bg-warning-100',
      LIGHT_TEXT: 'text-warning-600'
    },
    DANGER: {
      BG: 'bg-danger-50',
      BORDER: 'border-danger-200',
      TEXT: 'text-danger-800',
      ICON: 'text-danger-600',
      LIGHT_BG: 'bg-danger-100',
      LIGHT_TEXT: 'text-danger-600'
    },
    INFO: {
      BG: 'bg-primary-50',
      BORDER: 'border-primary-200',
      TEXT: 'text-primary-800',
      ICON: 'text-primary-600',
      LIGHT_BG: 'bg-primary-100',
      LIGHT_TEXT: 'text-primary-600'
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
    success: 'bg-success-100 text-success-800',
    warning: 'bg-warning-100 text-warning-800',
    danger: 'bg-danger-100 text-danger-800',
    info: 'bg-primary-100 text-primary-800'
  }
  
  return colorMap[status]
}
