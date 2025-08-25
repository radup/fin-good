/**
 * Design System Utility Functions
 * Helper functions for working with design tokens
 */

import { 
  ButtonVariant, 
  ButtonSize, 
  CardVariant, 
  InputVariant, 
  BadgeVariant,
  ClassNameBuilder,
  ComponentVariantBuilder
} from '../types/design-system'
import { components, semantic } from './design-system'

/**
 * Combines multiple class names, filtering out falsy values
 */
export const cn: ClassNameBuilder = (...classes) => {
  return classes.filter(Boolean).join(' ')
}

/**
 * Builds component class names with variants
 */
export const buildVariantClasses: ComponentVariantBuilder<string> = (
  base,
  variants,
  selectedVariant,
  className = ''
) => {
  return cn(base, variants[selectedVariant], className)
}

/**
 * Button class name builder
 */
export const buttonClasses = (
  variant: ButtonVariant = 'primary',
  size: ButtonSize = 'base',
  className?: string
) => {
  return cn(
    components.button.base,
    components.button.variants[variant],
    components.button.sizes[size],
    className
  )
}

/**
 * Card class name builder
 */
export const cardClasses = (
  variant: CardVariant = 'default',
  className?: string
) => {
  return cn(
    components.card.base,
    components.card.variants[variant],
    className
  )
}

/**
 * Input class name builder
 */
export const inputClasses = (
  variant: InputVariant = 'default',
  className?: string
) => {
  return cn(
    components.input.base,
    components.input.variants[variant],
    className
  )
}

/**
 * Badge class name builder
 */
export const badgeClasses = (
  variant: BadgeVariant = 'primary',
  className?: string
) => {
  return cn(
    components.badge.base,
    components.badge.variants[variant],
    className
  )
}

/**
 * Responsive grid class builder
 */
export const gridClasses = (
  cols: number = 1,
  gap: 'sm' | 'base' | 'lg' = 'base',
  className?: string
) => {
  const colsClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    6: 'grid-cols-6',
    12: 'grid-cols-12'
  }[cols] || 'grid-cols-1'

  const gapClass = {
    sm: 'gap-4',
    base: 'gap-6',
    lg: 'gap-8'
  }[gap]

  return cn('grid', colsClass, gapClass, className)
}

/**
 * Responsive container class builder
 */
export const containerClasses = (
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' = 'xl',
  className?: string
) => {
  const sizeClass = `max-w-screen-${size}`
  return cn('container mx-auto px-4', sizeClass, className)
}

/**
 * Spacing utility - converts design system spacing tokens to classes
 */
export const spacing = {
  p: (size: string | number) => `p-${size}`,
  px: (size: string | number) => `px-${size}`,
  py: (size: string | number) => `py-${size}`,
  pt: (size: string | number) => `pt-${size}`,
  pb: (size: string | number) => `pb-${size}`,
  pl: (size: string | number) => `pl-${size}`,
  pr: (size: string | number) => `pr-${size}`,
  m: (size: string | number) => `m-${size}`,
  mx: (size: string | number) => `mx-${size}`,
  my: (size: string | number) => `my-${size}`,
  mt: (size: string | number) => `mt-${size}`,
  mb: (size: string | number) => `mb-${size}`,
  ml: (size: string | number) => `ml-${size}`,
  mr: (size: string | number) => `mr-${size}`,
}

/**
 * Shadow utility builder
 */
export const shadowClasses = (
  size: 'sm' | 'base' | 'md' | 'lg' | 'xl' | '2xl' | 'inner' | 'none' = 'base',
  className?: string
) => {
  const shadowClass = size === 'base' ? 'shadow' : `shadow-${size}`
  return cn(shadowClass, className)
}

/**
 * Border radius utility
 */
export const roundedClasses = (
  size: 'none' | 'sm' | 'base' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full' = 'base',
  className?: string
) => {
  const roundedClass = size === 'base' ? 'rounded' : `rounded-${size}`
  return cn(roundedClass, className)
}

/**
 * Animation utility builder
 */
export const animationClasses = {
  transition: (type: 'all' | 'colors' | 'opacity' | 'shadow' | 'transform' = 'all') => 
    `transition-${type}`,
  duration: (speed: 'fast' | 'normal' | 'slow' = 'normal') => {
    const durationMap = {
      fast: 'duration-150',
      normal: 'duration-300',
      slow: 'duration-500'
    }
    return durationMap[speed]
  },
  ease: (timing: 'linear' | 'in' | 'out' | 'in-out' = 'out') => `ease-${timing}`,
}

/**
 * Gradient utility builder
 */
export const gradientClasses = (
  type: 'primary' | 'primary-subtle' | 'data' | 'hero' = 'primary',
  className?: string
) => {
  const gradientStyles = {
    primary: 'bg-gradient-to-r from-brand-primary to-brand-accent',
    'primary-subtle': 'bg-gradient-to-r from-brand-primary to-brand-primary-hover',
    data: 'bg-gradient-to-r from-brand-primary via-brand-accent to-brand-primary-hover',
    hero: 'bg-gradient-to-br from-brand-primary-dark via-brand-primary-hover to-brand-primary'
  }
  
  return cn(gradientStyles[type], className)
}

/**
 * Focus ring utility
 */
export const focusRing = (color: 'brand' | 'red' | 'green' | 'blue' = 'brand') => {
  const colorMap = {
    brand: 'focus:ring-brand-primary',
    red: 'focus:ring-red-500',
    green: 'focus:ring-green-500', 
    blue: 'focus:ring-blue-500'
  }
  return `focus:outline-none focus:ring-2 focus:ring-offset-2 ${colorMap[color]}`
}

/**
 * Hover utility builder
 */
export const hoverClasses = {
  scale: (amount: '95' | '105' | '110' = '105') => `hover:scale-${amount}`,
  shadow: (size: 'sm' | 'md' | 'lg' | 'xl' = 'md') => `hover:shadow-${size}`,
  brightness: (amount: '95' | '105' | '110' = '105') => `hover:brightness-${amount}`,
}

/**
 * Text utility builder
 */
export const textClasses = {
  size: (size: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' = 'base') => 
    size === 'base' ? 'text-base' : `text-${size}`,
  weight: (weight: 'normal' | 'medium' | 'semibold' | 'bold' = 'normal') => 
    weight === 'normal' ? 'font-normal' : `font-${weight}`,
  color: (color: 'primary' | 'secondary' | 'muted' | 'brand' | 'success' | 'warning' | 'error' = 'primary') => {
    const colorMap = {
      primary: 'text-gray-900',
      secondary: 'text-gray-600',
      muted: 'text-gray-500',
      brand: 'text-brand-primary',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600'
    }
    return colorMap[color]
  }
}

/**
 * Layout utility helpers
 */
export const layoutClasses = {
  flex: {
    center: 'flex items-center justify-center',
    between: 'flex items-center justify-between',
    start: 'flex items-center justify-start',
    end: 'flex items-center justify-end',
    col: 'flex flex-col',
    colCenter: 'flex flex-col items-center justify-center'
  },
  position: {
    absolute: {
      center: 'absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2',
      topRight: 'absolute top-0 right-0',
      topLeft: 'absolute top-0 left-0',
      bottomRight: 'absolute bottom-0 right-0',
      bottomLeft: 'absolute bottom-0 left-0'
    }
  }
}

/**
 * Validation helper for design system values
 */
export const validateDesignToken = <T extends string>(
  value: T,
  allowedValues: readonly T[],
  defaultValue: T
): T => {
  return allowedValues.includes(value) ? value : defaultValue
}

/**
 * Dr. Sigmund Advice Card styling utility
 * Creates consistent styling for Dr. Sigmund advice containers
 */
export const drSigmundAdviceClasses = (
  variant: 'default' | 'risk' | 'insights' | 'ml' | 'business' = 'default',
  className?: string
) => {
  const variantStyles = {
    default: 'bg-gradient-to-r from-cyan-50 to-violet-50 border-cyan-200',
    risk: 'bg-gradient-to-r from-cyan-50 to-violet-50 border-cyan-200',
    insights: 'bg-gradient-to-r from-violet-50 to-cyan-50 border-violet-200',
    ml: 'bg-gradient-to-r from-violet-50 to-cyan-50 border-violet-200',
    business: 'bg-gradient-to-r from-emerald-50 to-cyan-50 border-emerald-200'
  }
  
  return cn(
    'rounded-xl p-6 border overflow-hidden',
    variantStyles[variant],
    className
  )
}

/**
 * Dr. Sigmund Header styling utility
 * For the header section with avatar, title, and badge
 */
export const drSigmundHeaderClasses = (
  variant: 'default' | 'risk' | 'insights' | 'ml' | 'business' = 'default'
) => {
  const textColors = {
    default: 'text-cyan-900',
    risk: 'text-cyan-900',
    insights: 'text-violet-900', 
    ml: 'text-violet-900',
    business: 'text-emerald-900'
  }
  
  const badgeColors = {
    default: 'bg-cyan-100 text-cyan-700',
    risk: 'bg-cyan-100 text-cyan-700',
    insights: 'bg-violet-100 text-violet-700',
    ml: 'bg-violet-100 text-violet-700',
    business: 'bg-emerald-100 text-emerald-700'
  }
  
  return {
    title: cn('text-lg font-semibold', textColors[variant]),
    badge: cn('text-xs px-2 py-1 rounded-full', badgeColors[variant]),
    content: cn('space-y-3 text-sm', textColors[variant].replace('900', '800'))
  }
}

/**
 * Dr. Sigmund Toggle Button styling utility
 */
export const drSigmundToggleClasses = (
  variant: 'default' | 'risk' | 'insights' | 'ml' | 'business' = 'default'
) => {
  const colors = {
    default: 'text-cyan-600 hover:text-cyan-800 hover:bg-cyan-100',
    risk: 'text-cyan-600 hover:text-cyan-800 hover:bg-cyan-100',
    insights: 'text-violet-600 hover:text-violet-800 hover:bg-violet-100',
    ml: 'text-violet-600 hover:text-violet-800 hover:bg-violet-100',
    business: 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-100'
  }
  
  return cn(
    'text-sm font-medium px-3 py-1 rounded transition-colors flex items-center space-x-1',
    colors[variant]
  )
}

/**
 * Dr. Sigmund Expandable Border styling utility
 */
export const drSigmundExpandableBorderClasses = (
  variant: 'default' | 'risk' | 'insights' | 'ml' | 'business' = 'default'
) => {
  const borderColors = {
    default: 'border-cyan-200',
    risk: 'border-cyan-200',
    insights: 'border-violet-200',
    ml: 'border-violet-200',
    business: 'border-emerald-200'
  }
  
  return cn('border-t bg-white p-6', borderColors[variant])
}

/**
 * Page header utility builder
 * Creates clean, consistent headers like the analytics page
 */
export const headerClasses = (
  variant: 'default' | 'clean' | 'minimal' = 'clean',
  className?: string
) => {
  const baseClasses = 'flex items-center justify-between mb-8'
  
  const variants = {
    default: baseClasses,
    clean: baseClasses, // Analytics-style clean header
    minimal: 'flex items-center justify-between mb-6'
  }
  
  return cn(variants[variant], className)
}

/**
 * Page header title utility
 */
export const headerTitleClasses = (
  size: 'lg' | 'xl' | '2xl' | '3xl' = '2xl',
  className?: string
) => {
  const titleClasses = {
    lg: 'text-lg font-semibold text-gray-900',
    xl: 'text-xl font-bold text-gray-900', 
    '2xl': 'text-2xl font-bold text-gray-900',
    '3xl': 'text-3xl font-bold text-gray-900'
  }
  
  return cn(titleClasses[size], className)
}

/**
 * Page header description utility
 */
export const headerDescClasses = (
  variant: 'default' | 'muted' = 'default',
  className?: string
) => {
  const variants = {
    default: 'text-gray-600 mt-1',
    muted: 'text-gray-500 mt-1 text-sm'
  }
  
  return cn(variants[variant], className)
}

/**
 * Semantic color tokens export
 */
export { semantic }