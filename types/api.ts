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

// ============================================================================
// NEW INTERFACES FOR PHASE 2 BACKEND FEATURES
// ============================================================================

// Bulk Operations Response
export interface BulkOperationResponse {
  message: string
  operation_type: 'categorize' | 'update' | 'delete' | 'undo' | 'redo'
  total_transactions: number
  successful_operations: number
  failed_operations: number
  processing_time: number
  operation_id: string
  undo_available: boolean
  redo_available: boolean
  details?: {
    categorized_count?: number
    updated_count?: number
    deleted_count?: number
    errors?: Array<{
      transaction_id: number
      error: string
    }>
  }
}

// Bulk Operation Request
export interface BulkOperationRequest {
  transaction_ids: number[]
  operation_type: 'categorize' | 'update' | 'delete'
  category?: string
  subcategory?: string
  description?: string
  vendor?: string
  amount?: number
  date?: string
}

// Duplicate Detection Response
export interface DuplicateGroup {
  group_id: string
  confidence_score: number
  algorithm_used: string
  transactions: Array<{
    id: number
    description: string
    amount: number
    date: string
    vendor: string
    category: string
    subcategory: string
    similarity_score: number
  }>
  merge_suggestions: Array<{
    primary_transaction_id: number
    fields_to_merge: string[]
    confidence: number
  }>
  created_at: string
}

export interface DuplicateScanResponse {
  message: string
  scan_id: string
  total_transactions_scanned: number
  duplicate_groups_found: number
  total_duplicates: number
  scan_duration: number
  algorithms_used: string[]
  confidence_threshold: number
}

export interface DuplicateMergeResponse {
  message: string
  merge_id: string
  primary_transaction_id: number
  merged_transaction_ids: number[]
  merged_fields: string[]
  new_transaction: {
    id: number
    description: string
    amount: number
    date: string
    vendor: string
    category: string
    subcategory: string
  }
}

// Pattern Recognition Response
export interface Pattern {
  pattern_id: string
  pattern_type: 'vendor' | 'amount' | 'frequency' | 'behavioral' | 'temporal' | 'category' | 'combined'
  confidence_score: number
  support_count: number
  pattern_data: {
    vendor_pattern?: string
    amount_range?: { min: number; max: number }
    frequency?: { type: string; value: number }
    category?: string
    subcategory?: string
    time_pattern?: string
    behavioral_indicators?: string[]
  }
  example_transactions: Array<{
    id: number
    description: string
    amount: number
    date: string
    vendor: string
  }>
  generated_rules: Array<{
    rule_id: number
    pattern: string
    category: string
    subcategory?: string
    confidence: number
  }>
  accuracy_metrics: {
    precision: number
    recall: number
    f1_score: number
    usage_count: number
  }
  created_at: string
  last_updated: string
}

export interface PatternAnalysisResponse {
  message: string
  analysis_id: string
  patterns_discovered: number
  rules_generated: number
  analysis_duration: number
  pattern_types_found: string[]
  confidence_distribution: {
    high: number
    medium: number
    low: number
  }
}

export interface PatternRuleGenerationResponse {
  message: string
  rules_created: number
  rules_updated: number
  patterns_analyzed: number
  average_confidence: number
  processing_time: number
}

// Enhanced Analytics Response
export interface EnhancedPerformanceMetrics {
  api_response_times: {
    average: number
    p95: number
    p99: number
    slowest_endpoints: Array<{
      endpoint: string
      average_time: number
      call_count: number
    }>
  }
  cache_performance: {
    hit_rate: number
    miss_rate: number
    total_requests: number
    cache_size: number
  }
  database_performance: {
    query_count: number
    average_query_time: number
    slow_queries: Array<{
      query: string
      execution_time: number
      call_count: number
    }>
  }
  background_jobs: {
    active_jobs: number
    completed_jobs: number
    failed_jobs: number
    average_processing_time: number
  }
  system_health: {
    memory_usage: number
    cpu_usage: number
    disk_usage: number
    uptime: number
  }
}

export interface PredictiveInsights {
  spending_forecast: Array<{
    period: string
    predicted_amount: number
    confidence_interval: { lower: number; upper: number }
    trend: 'increasing' | 'decreasing' | 'stable'
  }>
  budget_recommendations: Array<{
    category: string
    current_spending: number
    recommended_budget: number
    reasoning: string
    confidence: number
  }>
  anomaly_detection: Array<{
    transaction_id: number
    anomaly_type: 'unusual_amount' | 'unusual_vendor' | 'unusual_timing' | 'unusual_category'
    confidence: number
    description: string
    suggested_action: string
  }>
  financial_health_score: {
    overall_score: number
    spending_efficiency: number
    budget_adherence: number
    savings_rate: number
    debt_ratio: number
    recommendations: string[]
  }
}

export interface EnhancedVendorAnalysis {
  vendor_performance: Array<{
    vendor: string
    total_transactions: number
    total_amount: number
    average_amount: number
    frequency: number
    categories: Array<{
      category: string
      count: number
      amount: number
    }>
    spending_trend: Array<{
      month: string
      amount: number
      transaction_count: number
    }>
    risk_score: number
    recommendations: string[]
  }>
  vendor_insights: {
    top_vendors: Array<{
      vendor: string
      total_spent: number
      transaction_count: number
      category_distribution: Record<string, number>
    }>
    vendor_categories: Array<{
      category: string
      vendor_count: number
      total_spent: number
      average_spent_per_vendor: number
    }>
    vendor_anomalies: Array<{
      vendor: string
      anomaly_type: string
      description: string
      confidence: number
    }>
  }
}

export interface AnalyticsSummary {
  overall_metrics: {
    total_transactions: number
    total_amount: number
    average_transaction_amount: number
    unique_vendors: number
    categories_used: number
  }
  time_series_data: Array<{
    date: string
    transaction_count: number
    total_amount: number
    average_amount: number
  }>
  category_breakdown: Array<{
    category: string
    transaction_count: number
    total_amount: number
    percentage_of_total: number
  }>
  vendor_breakdown: Array<{
    vendor: string
    transaction_count: number
    total_amount: number
    percentage_of_total: number
  }>
  insights: Array<{
    type: string
    title: string
    description: string
    impact: 'positive' | 'negative' | 'neutral'
    confidence: number
  }>
}

// Report Builder Response
export interface ReportTemplate {
  template_id: string
  name: string
  description: string
  report_type: 'cash_flow' | 'spending_analysis' | 'vendor_performance' | 'category_breakdown' | 'budget_tracking' | 'financial_health' | 'custom'
  format: 'pdf' | 'excel' | 'html' | 'csv' | 'json'
  parameters: Array<{
    name: string
    type: 'date_range' | 'category' | 'vendor' | 'amount_range' | 'boolean' | 'string'
    required: boolean
    default_value?: any
    options?: any[]
  }>
  created_at: string
  updated_at: string
}

export interface ReportJob {
  job_id: string
  template_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  parameters: Record<string, any>
  progress: number
  estimated_completion?: string
  created_at: string
  completed_at?: string
  download_url?: string
  error_message?: string
}

export interface ReportSchedule {
  schedule_id: string
  template_id: string
  name: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  next_run: string
  parameters: Record<string, any>
  recipients: string[]
  active: boolean
  created_at: string
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
