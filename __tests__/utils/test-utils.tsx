import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Mock data for common test scenarios
export const mockCategorizationPerformance = {
  overall_accuracy: 94.5,
  overall_confidence: 87.2,
  total_transactions: 12500,
  categorized_transactions: 11875,
  uncategorized_transactions: 625,
  method_breakdown: {
    rule_based: { count: 7500, accuracy: 96.2, confidence: 89.1 },
    ml_based: { count: 4375, accuracy: 91.8, confidence: 84.3 }
  },
  category_performance: [
    { category: 'Food & Dining', accuracy: 97.1, confidence: 92.3, count: 2100 },
    { category: 'Transportation', accuracy: 95.8, confidence: 88.7, count: 1800 },
    { category: 'Shopping', accuracy: 93.2, confidence: 85.4, count: 3200 }
  ],
  feedback_analysis: {
    positive_feedback: 1250,
    negative_feedback: 89,
    improvement_suggestions: 234,
    learning_rate: 0.85
  }
}

export const mockAutoImprovementResult = {
  message: 'Auto-improvement completed successfully',
  rules_created: 12,
  rules_updated: 8,
  ml_model_improvements: 3,
  transactions_reprocessed: 1250,
  improvement_score: 0.87,
  processing_time: 45.2
}

export const mockCategorySuggestions = {
  transaction_id: 1,
  description: 'STARBUCKS COFFEE',
  amount: 4.50,
  current_category: 'Food & Dining',
  current_subcategory: 'Coffee Shops',
  suggestions: [
    { category: 'Food & Dining', subcategory: 'Coffee Shops', confidence: 0.95, source: 'rule' as const, reasoning: 'Exact match with existing rule' },
    { category: 'Food & Dining', subcategory: 'Restaurants', confidence: 0.82, source: 'ml' as const, reasoning: 'ML model prediction based on similar transactions' }
  ],
  rule_matches: [
    { category: 'Food & Dining', subcategory: 'Coffee Shops', confidence: 0.95, source: 'rule' as const, reasoning: 'Exact match with existing rule' }
  ],
  ml_predictions: [
    { category: 'Food & Dining', subcategory: 'Restaurants', confidence: 0.82, source: 'ml' as const, reasoning: 'ML model prediction based on similar transactions' }
  ],
  confidence_threshold: 0.8
}

export const mockRateLimitInfo = {
  retry_after: 60,
  limit: 100,
  reset_time: '2024-01-15T10:30:00Z',
  message: 'Rate limit exceeded. Please try again in 60 seconds.'
}

export const mockFeedbackResult = {
  message: 'Feedback submitted successfully',
  feedback_id: 'fb_12345',
  transaction_id: 1,
  feedback_type: 'correct' as const,
  impact: 'This feedback will improve future categorizations',
  ml_learning: true
}
