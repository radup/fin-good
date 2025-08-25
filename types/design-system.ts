/**
 * TypeScript definitions for Spend's Analysis Design System
 */

// Color Types
export interface BrandColors {
  primary: string
  'primary-hover': string
  'primary-dark': string
  accent: string
}

export interface SemanticColors {
  success: string
  warning: string
  error: string
  info: string
}

export interface NeutralColors {
  50: string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  800: string
  900: string
}

export interface BackgroundColors {
  primary: string
  secondary: string
  dark: string
  card: string
  'card-hover': string
}

export interface ColorPalette {
  brand: BrandColors
  semantic: SemanticColors
  neutral: NeutralColors
  background: BackgroundColors
}

// Typography Types
export interface FontFamilies {
  sans: string[]
  mono: string[]
  display: string[]
}

export interface FontSizes {
  xs: string
  sm: string
  base: string
  lg: string
  xl: string
  '2xl': string
  '3xl': string
  '4xl': string
  '5xl': string
}

export interface FontWeights {
  normal: string
  medium: string
  semibold: string
  bold: string
}

export interface LineHeights {
  tight: string
  normal: string
  relaxed: string
}

export interface Typography {
  fontFamilies: FontFamilies
  fontSizes: FontSizes
  fontWeights: FontWeights
  lineHeights: LineHeights
}

// Animation Types
export interface AnimationDurations {
  fast: string
  normal: string
  slow: string
}

export interface AnimationEasings {
  linear: string
  'ease-in': string
  'ease-out': string
  'ease-in-out': string
  bounce: string
}

export interface AnimationTransitions {
  all: string
  colors: string
  opacity: string
  shadow: string
  transform: string
}

export interface Animations {
  durations: AnimationDurations
  easings: AnimationEasings
  transitions: AnimationTransitions
}

// Component Types
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'gradient'
export type ButtonSize = 'sm' | 'base' | 'lg'
export type CardVariant = 'default' | 'interactive' | 'elevated'
export type InputVariant = 'default' | 'error' | 'success'
export type BadgeVariant = 'primary' | 'success' | 'warning' | 'error' | 'neutral'

export interface ButtonStyles {
  base: string
  variants: Record<ButtonVariant, string>
  sizes: Record<ButtonSize, string>
}

export interface CardStyles {
  base: string
  variants: Record<CardVariant, string>
}

export interface InputStyles {
  base: string
  variants: Record<InputVariant, string>
}

export interface BadgeStyles {
  base: string
  variants: Record<BadgeVariant, string>
}

export interface ComponentStyles {
  button: ButtonStyles
  card: CardStyles
  input: InputStyles
  badge: BadgeStyles
}

// Layout Types
export interface ContainerSizes {
  xs: string
  sm: string
  md: string
  lg: string
  xl: string
  '2xl': string
}

export interface SidebarDimensions {
  width: string
  collapsedWidth: string
}

export interface HeaderDimensions {
  height: string
}

export interface GridColumns {
  1: string
  2: string
  3: string
  4: string
  12: string
}

export interface GridGaps {
  sm: string
  base: string
  lg: string
}

export interface GridSystem {
  columns: GridColumns
  gaps: GridGaps
}

export interface LayoutTokens {
  containers: ContainerSizes
  sidebar: SidebarDimensions
  header: HeaderDimensions
  grid: GridSystem
}

// Semantic Token Types
export interface TextClasses {
  primary: string
  secondary: string
  muted: string
  inverse: string
  brand: string
  success: string
  warning: string
  error: string
}

export interface BackgroundClasses {
  primary: string
  secondary: string
  brand: string
  'brand-dark': string
  success: string
  warning: string
  error: string
}

export interface BorderClasses {
  default: string
  light: string
  brand: string
  success: string
  warning: string
  error: string
}

export interface SemanticTokens {
  text: TextClasses
  background: BackgroundClasses
  border: BorderClasses
}

// Utility Types for Design System Usage
export interface DesignSystemTokens {
  colors: ColorPalette
  gradients: Record<string, string>
  typography: Typography
  spacing: Record<string | number, string>
  borderRadius: Record<string, string>
  shadows: Record<string, string>
  animations: Animations
  components: ComponentStyles
  layout: LayoutTokens
  semantic: SemanticTokens
}

// Component Props Types
export interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  children: React.ReactNode
  className?: string
  onClick?: () => void
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}

export interface CardProps {
  variant?: CardVariant
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

export interface InputProps {
  variant?: InputVariant
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  className?: string
  type?: string
  disabled?: boolean
}

// Theme Context Types
export interface ThemeContextType {
  tokens: DesignSystemTokens
  isDark?: boolean
  toggleTheme?: () => void
}

// Utility function types
export type ClassNameBuilder = (...classes: (string | undefined | null)[]) => string
export type ComponentVariantBuilder<T extends string> = (
  base: string,
  variants: Record<T, string>,
  selectedVariant: T,
  className?: string
) => string