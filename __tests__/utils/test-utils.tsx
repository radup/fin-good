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
  user_id: 1,
  period: {
    start_date: null,
    end_date: null
  },
  overall_metrics: {
    total_transactions: 1250,
    categorized_count: 1180,
    accuracy_rate: 0.92,
    average_confidence: 0.85,
    success_rate: 0.94
  },
  method_breakdown: {
    rule_based: {
      count: 650,
      accuracy: 0.95,
      average_confidence: 0.90
    },
    ml_based: {
      count: 530,
      accuracy: 0.88,
      average_confidence: 0.78
    }
  },
  confidence_distribution: {
    high_confidence: 850,
    medium_confidence: 280,
    low_confidence: 120
  },
  category_performance: {
    'Food & Dining': {
      count: 180,
      accuracy: 0.95,
      average_confidence: 0.92
    },
    'Transportation': {
      count: 150,
      accuracy: 0.88,
      average_confidence: 0.85
    }
  },
  improvement_trends: {
    daily_accuracy: [
      { date: '2025-08-15', accuracy: 0.89 },
      { date: '2025-08-16', accuracy: 0.91 }
    ],
    weekly_improvement: 0.03
  },
  feedback_analysis: {
    total_feedback: 45,
    positive_feedback: 38,
    negative_feedback: 7,
    feedback_accuracy: 0.84
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
