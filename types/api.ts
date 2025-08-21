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
    percentage: number
  }>
  vendor_analysis: Array<{
    vendor: string
    transaction_count: number
    total_amount: number
    average_amount: number
  }>
  trends: {
    spending_trend: 'increasing' | 'decreasing' | 'stable'
    transaction_frequency: 'increasing' | 'decreasing' | 'stable'
    category_distribution: Record<string, number>
  }
}

// Forecasting Types
export interface ForecastRequest {
  forecast_type: 'cash_flow' | 'revenue' | 'expenses' | 'net_income' | 'category_specific'
  horizon: '7_days' | '30_days' | '60_days' | '90_days' | 'custom'
  custom_days?: number
  category_filter?: string
  confidence_level?: number
}

export interface PredictionPoint {
  date: string
  value: number
  confidence_lower: number
  confidence_upper: number
  trend_component?: number
  seasonal_component?: number
}

export interface ForecastResponse {
  forecast_id: string
  user_id: number
  forecast_type: string
  horizon_days: number
  predictions: PredictionPoint[]
  confidence_score: number
  seasonal_pattern: string
  trend_direction: string
  model_accuracy: number
  created_at: string
  metadata: {
    seasonal_strength: number
    trend_strength: number
    volatility: number
    data_points: number
    category_filter?: string
  }
}

export interface AccuracyHistoryResponse {
  user_id: number
  period_days: number
  average_accuracy: number
  forecast_count: number
  accuracy_trend: string
  best_forecast_type: string
  accuracy_by_horizon: {
    '7_days': number
    '30_days': number
    '60_days': number
    '90_days': number
  }
}

export interface ModelPerformance {
  model_type: string
  mae: number
  mse: number
  rmse: number
  mape: number
  r2: number
  training_samples: number
  test_samples: number
}

export interface EnsembleAnalysisResponse {
  ensemble_confidence: number
  model_weights: Record<string, number>
  individual_predictions: Array<{
    value: number
    confidence_lower: number
    confidence_upper: number
    model_type: string
    confidence_score: number
  }>
  model_performances: Record<string, ModelPerformance>
}

// Multi-Model Forecasting Types
export interface MultiModelForecastRequest {
  forecast_type: 'cash_flow' | 'revenue' | 'expenses' | 'net_income' | 'category_specific'
  horizon: '7_days' | '30_days' | '60_days' | '90_days' | 'custom'
  custom_days?: number
  category_filter?: string
  confidence_level?: number
  models?: Array<'prophet' | 'arima' | 'neuralprophet' | 'simple_trend'>
}

export interface ModelResult {
  model_name: string
  predictions: PredictionPoint[]
  accuracy: number
  mse: number
  mae: number
  confidence_score: number
  seasonal_pattern: string
  trend_direction: string
  model_params: Record<string, any>
}

export interface MultiModelForecastResponse {
  forecast_id: string
  user_id: number
  forecast_type: string
  horizon_days: number
  model_results: ModelResult[]
  ensemble_predictions: PredictionPoint[]
  best_model: string
  ensemble_accuracy: number
  created_at: string
  metadata: {
    models_used: string[]
    data_points: number
    category_filter?: string
    confidence_level: number
  }
}

export interface ForecastModelInfo {
  model: string
  name: string
  description: string
  strengths: string[]
  best_for: string
}

export interface BatchForecastRequest {
  forecasts: Array<{
    forecast_type: string
    horizon: string
    custom_days?: number
    category_filter?: string
  }>
}

export interface BatchForecastResponse {
  batch_id: string
  total_forecasts: number
  successful_forecasts: number
  failed_forecasts: number
  processing_time: number
  results: ForecastResponse[]
  errors: Array<{
    index: number
    error: string
  }>
}

export interface ForecastTypeInfo {
  value: string
  label: string
  description: string
  supported_horizons: string[]
}

export interface ForecastHorizonInfo {
  value: string
  label: string
  days: number
  description: string
  recommended_for: string[]
}

export interface ForecastingHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  model_status: {
    ensemble_model: 'ready' | 'training' | 'error'
    individual_models: Record<string, 'ready' | 'training' | 'error'>
  }
  performance_metrics: {
    average_response_time: number
    success_rate: number
    error_rate: number
  }
  system_resources: {
    memory_usage: number
    cpu_usage: number
    active_forecasts: number
  }
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

// ============================================================================
// BUDGET ANALYSIS SYSTEM TYPES (Task F2.6 - Frontend Integration)
// ============================================================================

// Budget Definition
export interface Budget {
  id: number
  name: string
  description: string | null
  budget_type: 'MONTHLY' | 'QUARTERLY' | 'ANNUAL' | 'PROJECT' | 'GOAL_BASED'
  start_date: string
  end_date: string
  total_income_budget: number
  total_expense_budget: number
  status: 'DRAFT' | 'ACTIVE' | 'COMPLETED' | 'PAUSED' | 'ARCHIVED'
  user_id: number
  warning_threshold: number
  critical_threshold: number
  auto_rollover: boolean
  include_in_forecasting: boolean
  created_from_template: string | null
  tags: string[]
  created_at: string
  updated_at: string | null
  budget_items?: BudgetItem[]
}

export interface BudgetItem {
  id: number
  budget_id: number
  category: string
  subcategory: string | null
  is_income: boolean
  budgeted_amount: number
  use_historical_data: boolean
  forecast_method: string
  notes: string | null
  priority: number
  monthly_breakdown: any | null
  forecast_confidence: number | null
  created_at: string
  updated_at: string | null
}

// Budget Category Allocation
export interface BudgetCategory {
  budget_id: string
  category: string
  subcategory?: string
  allocated_amount: number
  actual_amount: number
  variance_amount: number
  variance_percentage: number
  status: 'under_budget' | 'on_budget' | 'over_budget' | 'critical'
  last_updated: string
}

// Budget vs Actual Analysis
export interface BudgetVarianceAnalysis {
  budget_id: string
  period_start: string
  period_end: string
  total_budget: number
  total_actual: number
  total_variance: number
  variance_percentage: number
  overall_status: 'under_budget' | 'on_budget' | 'over_budget' | 'critical'
  category_breakdown: BudgetCategory[]
  statistical_significance: {
    is_significant: boolean
    confidence_level: number
    p_value: number
    effect_size: number
  }
  trend_analysis: {
    trend_direction: 'improving' | 'stable' | 'worsening'
    trend_strength: number
    trend_confidence: number
  }
}

// Budget Alert Configuration
export interface BudgetAlert {
  alert_id: string
  budget_id: string
  alert_type: 'variance_threshold' | 'category_overrun' | 'trend_warning' | 'forecast_alert'
  threshold_type: 'percentage' | 'absolute_amount'
  threshold_value: number
  condition: 'greater_than' | 'less_than' | 'equals'
  category?: string
  subcategory?: string
  enabled: boolean
  notification_channels: ('email' | 'push' | 'in_app')[]
  created_at: string
  last_triggered?: string
}

// Budget Alert Trigger
export interface BudgetAlertTrigger {
  alert_id: string
  budget_id: string
  trigger_type: string
  trigger_value: number
  threshold_value: number
  variance_amount: number
  variance_percentage: number
  category?: string
  subcategory?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  triggered_at: string
  acknowledged: boolean
  acknowledged_at?: string
  acknowledged_by?: string
}

// Budget Recommendation
export interface BudgetRecommendation {
  recommendation_id: string
  budget_id: string
  recommendation_type: 'category_adjustment' | 'period_extension' | 'spending_reduction' | 'reallocation' | 'forecast_adjustment'
  category?: string
  subcategory?: string
  current_amount: number
  recommended_amount: number
  adjustment_amount: number
  confidence_score: number
  reasoning: string
  impact_analysis: {
    short_term_impact: string
    long_term_impact: string
    risk_level: 'low' | 'medium' | 'high'
  }
  ml_insights: {
    pattern_detected: string
    historical_comparison: string
    seasonal_factor?: number
  }
  created_at: string
  applied: boolean
  applied_at?: string
}

// Budget Scenario Planning
export interface BudgetScenario {
  scenario_id: string
  budget_id: string
  name: string
  description: string
  scenario_type: 'what_if' | 'optimization' | 'forecast' | 'stress_test'
  base_budget: number
  scenario_budget: number
  adjustments: Array<{
    category: string
    subcategory?: string
    adjustment_type: 'increase' | 'decrease' | 'reallocate'
    amount: number
    percentage: number
    reasoning: string
  }>
  projected_variance: number
  projected_variance_percentage: number
  confidence_level: number
  risk_assessment: {
    risk_level: 'low' | 'medium' | 'high'
    risk_factors: string[]
    mitigation_strategies: string[]
  }
  created_at: string
  created_by: string
}

// Budget Performance Metrics
export interface BudgetPerformanceMetrics {
  budget_id: string
  period_start: string
  period_end: string
  accuracy_score: number
  adherence_rate: number
  forecast_accuracy: number
  variance_trend: {
    direction: 'improving' | 'stable' | 'worsening'
    magnitude: number
    consistency: number
  }
  category_performance: Array<{
    category: string
    subcategory?: string
    accuracy_score: number
    adherence_rate: number
    variance_trend: number
    recommendation_count: number
    alert_count: number
  }>
  historical_comparison: {
    previous_period_accuracy: number
    improvement_rate: number
    best_performance_date: string
    worst_performance_date: string
  }
  ml_model_performance: {
    prediction_accuracy: number
    confidence_improvement: number
    model_learning_rate: number
  }
}

// Budget Analysis Summary
export interface BudgetAnalysisSummary {
  total_budgets: number
  active_budgets: number
  average_variance: number
  critical_alerts: number
  pending_recommendations: number
  overall_performance: {
    accuracy_score: number
    adherence_rate: number
    forecast_accuracy: number
  }
  top_performing_categories: Array<{
    category: string
    accuracy_score: number
    adherence_rate: number
  }>
  areas_needing_attention: Array<{
    category: string
    variance_percentage: number
    alert_count: number
    recommendation_count: number
  }>
  recent_trends: {
    variance_trend: 'improving' | 'stable' | 'worsening'
    alert_frequency: 'increasing' | 'stable' | 'decreasing'
    recommendation_effectiveness: number
  }
}

// Budget Analysis API Responses
export interface BudgetListResponse {
  budgets: Budget[]
  total_count: number
  page: number
  page_size: number
}

export interface BudgetDetailResponse {
  budget: Budget
  variance_analysis: BudgetVarianceAnalysis
  performance_metrics: BudgetPerformanceMetrics
  active_alerts: BudgetAlertTrigger[]
  recent_recommendations: BudgetRecommendation[]
  scenarios: BudgetScenario[]
}

export interface BudgetVarianceResponse {
  variance_analysis: BudgetVarianceAnalysis
  category_details: BudgetCategory[]
  alerts: BudgetAlertTrigger[]
  recommendations: BudgetRecommendation[]
}

export interface BudgetRecommendationsResponse {
  recommendations: BudgetRecommendation[]
  total_count: number
  applied_count: number
  pending_count: number
  average_confidence: number
}

export interface BudgetScenariosResponse {
  scenarios: BudgetScenario[]
  total_count: number
  active_count: number
  average_confidence: number
}

export interface BudgetAlertsResponse {
  alerts: BudgetAlertTrigger[]
  total_count: number
  acknowledged_count: number
  pending_count: number
  critical_count: number
}

export interface BudgetPerformanceResponse {
  performance_metrics: BudgetPerformanceMetrics
  historical_data: Array<{
    period_start: string
    period_end: string
    accuracy_score: number
    adherence_rate: number
    variance_percentage: number
  }>
  trend_analysis: {
    accuracy_trend: 'improving' | 'stable' | 'worsening'
    adherence_trend: 'improving' | 'stable' | 'worsening'
    variance_trend: 'improving' | 'stable' | 'worsening'
  }
}

// Budget Analysis Health Check
export interface BudgetAnalysisHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  system_components: {
    variance_calculator: 'ready' | 'processing' | 'error'
    recommendation_engine: 'ready' | 'processing' | 'error'
    alert_system: 'ready' | 'processing' | 'error'
    ml_models: 'ready' | 'training' | 'error'
  }
  performance_metrics: {
    average_response_time: number
    success_rate: number
    error_rate: number
    active_budgets: number
    pending_alerts: number
  }
  system_resources: {
    memory_usage: number
    cpu_usage: number
    active_analyses: number
  }
}
