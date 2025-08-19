// TypeScript interfaces for API responses

// Bulk Categorization Response
export interface BulkCategorizationResponse {
  message: string
  total_transactions: number
  rule_categorized: number
  ml_categorized: number
  failed_categorizations: number
  success_rate: number
  processing_time: number
}

// Confidence Analysis Response
export interface ConfidenceAnalysisResponse {
  transaction_id: number
  current_category: string
  current_subcategory: string
  confidence_score: number
  categorization_method: string
  confidence_breakdown: {
    rule_confidence?: number
    ml_confidence?: number
    user_confidence?: number
    overall_confidence: number
  }
  alternative_categories: Array<{
    category: string
    subcategory: string
    confidence: number
    reasoning?: string
  }>
  ml_reasoning?: string
  rule_applied?: {
    rule_id: number
    rule_name: string
    pattern: string
    priority: number
  }
  last_categorized: string
}

// Feedback Submission Response
export interface FeedbackSubmissionResponse {
  message: string
  feedback_id: string
  transaction_id: number
  feedback_type: 'correct' | 'incorrect' | 'suggest_alternative'
  impact: string
  ml_learning: boolean
}

// Category Suggestions Response
export interface CategorySuggestionsResponse {
  transaction_id: number
  description: string
  amount: number
  current_category: string
  current_subcategory: string
  suggestions: Array<{
    category: string
    subcategory: string
    confidence: number
    method: 'rule' | 'ml' | 'ml_alternative'
    reasoning?: string
    rule_id?: number
    rule_name?: string
    pattern?: string
  }>
  rule_matches: Array<{
    category: string
    subcategory: string
    confidence: number
    method: 'rule'
    rule_id: number
    rule_name: string
    pattern: string
  }>
  ml_predictions: Array<{
    category: string
    subcategory: string
    confidence: number
    method: 'ml'
    reasoning: string
  }>
  confidence_threshold: number
}

// Auto-Improvement Response
export interface AutoImprovementResponse {
  message: string
  rules_created: number
  rules_updated: number
  ml_model_improvements: number
  transactions_reprocessed: number
  improvement_score: number
  processing_time: number
}

// Performance Metrics Response
export interface PerformanceMetricsResponse {
  user_id: number
  period: {
    start_date?: string
    end_date?: string
  }
  overall_metrics: {
    total_transactions: number
    categorized_count: number
    uncategorized_count: number
    categorization_rate: number
    average_confidence: number
  }
  method_breakdown: {
    rule_based: number
    ml_based: number
    user_corrected: number
    unknown: number
  }
  confidence_distribution: {
    high: number
    medium: number
    low: number
  }
  category_performance: Record<string, {
    count: number
    total_amount: number
    average_confidence: number
  }>
  improvement_trends: Record<string, any>
  feedback_analysis: {
    total_feedback: number
    correct_feedback: number
    incorrect_feedback: number
    suggestions_feedback: number
  }
}

// Error Response for Rate Limiting
export interface RateLimitErrorResponse {
  error: string
  retry_after: number
  limit: number
  current_usage: number
}

// Generic API Error Response
export interface ApiErrorResponse {
  detail: string
  error_code?: string
  timestamp?: string
}
