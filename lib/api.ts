import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

// Types for categorization performance
export interface CategorizationPerformance {
  user_id: number
  period: {
    start_date: string | null
    end_date: string | null
  }
  overall_metrics: {
    total_transactions: number
    categorized_count: number
    accuracy_rate: number
    average_confidence: number
    success_rate: number
  }
  method_breakdown: {
    rule_based: {
      count: number
      accuracy: number
      average_confidence: number
    }
    ml_based: {
      count: number
      accuracy: number
      average_confidence: number
    }
  }
  confidence_distribution: {
    high_confidence: number
    medium_confidence: number
    low_confidence: number
  }
  category_performance: {
    [category: string]: {
      count: number
      accuracy: number
      average_confidence: number
    }
  }
  improvement_trends: {
    daily_accuracy: Array<{
      date: string
      accuracy: number
    }>
    weekly_improvement: number
  }
  feedback_analysis: {
    total_feedback: number
    positive_feedback: number
    negative_feedback: number
    feedback_accuracy: number
  }
}

// Types for auto-improvement
export interface AutoImprovementResult {
  message: string
  rules_created: number
  rules_updated: number
  ml_model_improvements: number
  transactions_reprocessed: number
  improvement_score: number
  processing_time: number
}

// Types for category suggestions
export interface CategorySuggestion {
  category: string
  subcategory?: string
  confidence: number
  source: 'rule' | 'ml'
  reasoning?: string
}

export interface CategorySuggestions {
  transaction_id: number
  description: string
  amount: number
  current_category: string
  current_subcategory?: string
  suggestions: CategorySuggestion[]
  rule_matches: CategorySuggestion[]
  ml_predictions: CategorySuggestion[]
  confidence_threshold: number
}

// Types for feedback
export interface FeedbackResult {
  message: string
  feedback_id: string
  transaction_id: number
  feedback_type: 'correct' | 'incorrect' | 'suggest_alternative'
  impact: string
  ml_learning: boolean
}

// Types for confidence analysis
export interface ConfidenceAnalysis {
  transaction_id: number
  description: string
  amount: number
  current_category: string
  current_subcategory?: string
  confidence_score: number
  categorization_method: 'rule' | 'ml' | 'manual'
  alternatives: Array<{
    category: string
    subcategory?: string
    confidence: number
    reasoning?: string
  }>
  last_updated: string | null
}

// Types for bulk categorization
export interface BulkCategorizationRequest {
  transaction_ids: number[]
  use_ml_fallback: boolean
}

export interface BulkCategorizationResponse {
  message: string
  total_transactions: number
  rule_categorized: number
  ml_categorized: number
  failed_categorizations: number
  success_rate: number
  processing_time: number
}

// Types for rate limit handling
export interface RateLimitInfo {
  limit: number
  reset_time: string
  message: string
}

// Types for categorization rules
export interface CategorizationRule {
  id: number
  user_id: number
  pattern: string
  pattern_type: string
  category: string
  subcategory?: string
  priority: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RuleCreate {
  pattern: string
  pattern_type: string
  category: string
  subcategory?: string
  priority?: number
  is_active?: boolean
}

export interface RuleUpdate {
  pattern?: string
  pattern_type?: string
  category?: string
  subcategory?: string
  priority?: number
  is_active?: boolean
}

export interface RuleListResponse {
  rules: CategorizationRule[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_prev: boolean
}

export interface RuleTestRequest {
  pattern: string
  pattern_type: string
  test_text: string
}

export interface RuleTestResponse {
  matches: boolean
  matched_text?: string
  confidence?: number
}

// Types for reports
export interface ReportRequest {
  report_type: 'cash_flow' | 'spending_analysis' | 'vendor_performance' | 'category_breakdown' | 'monthly_summary' | 'quarterly_summary' | 'custom_kpi' | 'categorization_quality'
  start_date?: string
  end_date?: string
  group_by?: 'none' | 'category' | 'subcategory' | 'vendor' | 'month' | 'quarter' | 'year' | 'week'
  filters?: {
    categories?: string[]
    vendors?: string[]
    min_amount?: number
    max_amount?: number
    is_income?: boolean
    is_categorized?: boolean
    description_contains?: string
  }
  aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max'
  export_format?: 'json' | 'csv'
}

export interface ReportResponse {
  report_id: string
  report_type: string
  data: any
  generated_at: string
  cache_hit: boolean
}

// Types for export
export interface ExportRequest {
  export_name?: string
  format: 'csv' | 'excel' | 'pdf' | 'json'
  filters: {
    start_date?: string
    end_date?: string
    categories?: string[]
    vendors?: string[]
    min_amount?: number
    max_amount?: number
    is_income?: boolean
    is_categorized?: boolean
  }
  columns?: string[]
  options?: {
    include_headers?: boolean
    date_format?: string
    number_format?: string
  }
}

export interface ExportJobResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  download_url?: string
  created_at: string
  estimated_completion?: string
}

export interface ExportProgress {
  job_id: string
  status: string
  progress: number
  message: string
  download_url?: string
}

// Types for ML categorization
export interface MLCategorizationResult {
  transaction_id: number
  categorization_result: {
    categorized: boolean
    method: 'ml' | 'rule'
    confidence: number
    category: string
    subcategory?: string
    reasoning?: string
    alternatives?: Array<{
      category: string
      confidence: number
    }>
  }
}

export interface MLSuggestions {
  transaction_id: number
  transaction_details: {
    description: string
    vendor?: string
    amount: number
  }
  suggestions: {
    has_suggestions: boolean
    primary_suggestion?: {
      category: string
      subcategory?: string
      confidence: number
      reasoning?: string
    }
    alternatives?: Array<{
      category: string
      confidence: number
    }>
  }
}

export interface MLPerformanceMetrics {
  user_id: number
  ml_performance: {
    total_predictions: number
    correct_predictions: number
    accuracy: number
    average_response_time: number
    cache_size: number
    last_updated: string
  }
}

// Types for cache management
export interface CacheStats {
  hit_rate: number
  miss_rate: number
  total_requests: number
  memory_usage: number
  cache_size: number
  eviction_count: number
}

// Types for monitoring
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  environment: string
  metrics: {
    total_errors_last_hour: number
    critical_errors_last_hour: number
    unique_error_codes: number
    affected_users: number
    affected_ips: number
  }
}

// Global CSRF token storage
let globalCsrfToken: string | null = null

// Get CSRF token from cookies
const getCsrfTokenFromCookie = () => {
  if (typeof document === 'undefined') return null
  
  const csrfCookie = document.cookie
    .split('; ')
    .find(row => row.startsWith('fingood_auth_csrf='))
  
  return csrfCookie ? csrfCookie.split('=')[1] : null
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Include cookies for authentication
})

// Request interceptor to add CSRF token for state-changing operations
api.interceptors.request.use((config) => {
  // Add CSRF token for POST, PUT, DELETE, PATCH requests
  if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase() || '')) {
    const csrfToken = globalCsrfToken || getCsrfTokenFromCookie()
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      // Clear any stored CSRF token
      globalCsrfToken = null
      window.location.href = '/login'
    } else if (error.response?.status === 429) {
      // Handle rate limiting
      const retryAfter = error.response.data?.retry_after || 60
      console.warn(`Rate limit exceeded. Retry after ${retryAfter} seconds.`)
      
      // You can add a global rate limit handler here
      // For example, show a toast notification or disable buttons temporarily
      if (typeof window !== 'undefined') {
        // Show user-friendly rate limit message
        const event = new CustomEvent('rate-limit-exceeded', {
          detail: {
            retryAfter,
            limit: error.response.data?.limit,
            currentUsage: error.response.data?.current_usage
          }
        })
        window.dispatchEvent(event)
      }
    }
    return Promise.reject(error)
  }
)

// Auth endpoints
export const authAPI = {
  login: (email: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    return api.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  
  register: (userData: {
    email: string
    password: string
    full_name?: string
    company_name?: string
    business_type?: string
  }) => api.post('/api/v1/auth/register', userData),
  
  me: () => api.get('/api/v1/auth/me'),
  
  logout: () => api.post('/api/v1/auth/logout'),
  
  refreshCsrf: () => api.post('/api/v1/auth/refresh-csrf'),
  
  getWebSocketToken: () => api.post('/api/v1/auth/websocket-token'),
}

// Transaction endpoints
export const transactionAPI = {
  // Get transactions with filtering and pagination
  getTransactions: (params?: {
    skip?: number
    limit?: number
    category?: string
    subcategory?: string
    vendor?: string
    description?: string
    start_date?: string
    end_date?: string
    is_income?: boolean
    is_categorized?: boolean
    min_amount?: number
    max_amount?: number
    sort_by?: string
    sort_order?: string
  }) => 
    api.get('/api/v1/transactions/', { params }),

  // Get transaction count for pagination
  getTransactionCount: (params?: {
    category?: string
    subcategory?: string
    vendor?: string
    description?: string
    start_date?: string
    end_date?: string
    is_income?: boolean
    is_categorized?: boolean
    min_amount?: number
    max_amount?: number
  }) => 
    api.get('/api/v1/transactions/count', { params }),
  
  getById: (id: number) => api.get(`/api/v1/transactions/${id}`),
  
  update: (id: number, data: { category?: string; subcategory?: string; create_rule?: boolean }) =>
    api.put(`/api/v1/transactions/${id}`, data),
  
  delete: (id: number) => api.delete(`/api/v1/transactions/${id}`),
  
  categorize: () => api.post('/api/v1/transactions/categorize'),
  
  getAvailableCategories: () => api.get('/api/v1/transactions/categories/available'),
  
  updateCategory: (id: number, category: string, subcategory?: string) =>
    api.put(`/api/v1/transactions/${id}/category`, null, {
      params: { category, subcategory }
    }),

  // NEW: Get categorization performance metrics
  getCategorizationPerformance: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<{ data: CategorizationPerformance }> =>
    api.get('/api/v1/transactions/categorize/performance', { params }),

  // NEW: Auto-improve categorization based on user feedback and patterns
  autoImprove: (params?: {
    batch_id?: string
    min_confidence_threshold?: number
    max_transactions?: number
  }): Promise<{ data: AutoImprovementResult }> =>
    api.post('/api/v1/transactions/categorize/auto-improve', null, { params }),

  // NEW: Get category suggestions for a transaction
  getCategorySuggestions: (transactionId: number, params?: {
    include_ml?: boolean
    include_rules?: boolean
  }): Promise<{ data: CategorySuggestions }> =>
    api.get(`/api/v1/transactions/categorize/suggestions/${transactionId}`, { params }),

  // NEW: Submit categorization feedback
  submitFeedback: (transactionId: number, params: {
    feedback_type: 'correct' | 'incorrect' | 'suggest_alternative'
    suggested_category?: string
    suggested_subcategory?: string
    feedback_comment?: string
  }): Promise<{ data: FeedbackResult }> =>
    api.post(`/api/v1/transactions/categorize/feedback`, null, { 
      params: { transaction_id: transactionId, ...params }
    }),

  // NEW: Bulk categorization with transaction IDs
  bulkCategorize: (transactionIds: number[], useMlFallback: boolean = true): Promise<{ data: BulkCategorizationResponse }> =>
    api.post('/api/v1/transactions/categorize/bulk', { 
      transaction_ids: transactionIds, 
      use_ml_fallback: useMlFallback 
    }),

  // NEW: Confidence analysis for individual transactions
  getConfidence: (transactionId: number): Promise<{ data: ConfidenceAnalysis }> =>
    api.get(`/api/v1/transactions/categorize/confidence/${transactionId}`),

  // List import batches (files)
  listImportBatches: () => 
    api.get('/api/v1/transactions/import-batches'),

  // Delete transactions by import batch
  deleteImportBatch: (batchId: string) => 
    api.delete(`/api/v1/transactions/import-batch/${batchId}`),
}

// Upload endpoints
export const uploadAPI = {
  csv: (file: File, batchId?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (batchId) {
      formData.append('batch_id', batchId)
    }
    return api.post('/api/v1/upload/csv', formData)
  },
  
  getStatus: (batchId: string) => api.get(`/api/v1/upload/status/${batchId}`),
}

// Analytics endpoints
export const analyticsAPI = {
  summary: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/api/v1/analytics/summary/', { params }),
  
  monthly: (year: number) => api.get('/api/v1/analytics/monthly/', { params: { year } }),
  
  topCategories: (params?: {
    limit?: number
    start_date?: string
    end_date?: string
  }) => api.get('/api/v1/analytics/top-categories/', { params }),
}

// Category endpoints
export const categoryAPI = {
  getAll: () => api.get('/api/v1/categories'),
  
  create: (data: { name: string; parent_category?: string; color?: string }) =>
    api.post('/api/v1/categories', data),
  
  getRules: () => api.get('/api/v1/categories/rules'),
  
  createRule: (data: {
    pattern: string
    pattern_type: string
    category: string
    subcategory?: string
    priority?: number
  }) => api.post('/api/v1/categories/rules', data),
}

// Categorization Rules endpoints
export const categorizationRulesAPI = {
  // Get paginated list of categorization rules
  getRules: (params?: {
    page?: number
    page_size?: number
    active_only?: boolean
    category?: string
    pattern_type?: string
    search?: string
    sort_by?: string
    sort_desc?: boolean
  }): Promise<{ data: RuleListResponse }> =>
    api.get('/api/v1/categorization-rules/', { params }),

  // Create a new categorization rule
  createRule: (ruleData: RuleCreate): Promise<{ data: CategorizationRule }> =>
    api.post('/api/v1/categorization-rules/', ruleData),

  // Get a specific rule
  getRule: (ruleId: number): Promise<{ data: CategorizationRule }> =>
    api.get(`/api/v1/categorization-rules/${ruleId}`),

  // Update a rule
  updateRule: (ruleId: number, ruleData: RuleUpdate): Promise<{ data: CategorizationRule }> =>
    api.put(`/api/v1/categorization-rules/${ruleId}`, ruleData),

  // Delete a rule
  deleteRule: (ruleId: number): Promise<{ data: { message: string } }> =>
    api.delete(`/api/v1/categorization-rules/${ruleId}`),

  // Test a rule
  testRule: (testData: RuleTestRequest): Promise<{ data: RuleTestResponse }> =>
    api.post('/api/v1/categorization-rules/test', testData),
}

// Reports endpoints
export const reportsAPI = {
  // Generate a report
  generateReport: (reportRequest: ReportRequest): Promise<{ data: ReportResponse }> =>
    api.post('/api/v1/reports/generate', reportRequest),

  // Get report by ID
  getReport: (reportId: string): Promise<{ data: ReportResponse }> =>
    api.get(`/api/v1/reports/${reportId}`),

  // Get available report types
  getReportTypes: (): Promise<{ data: string[] }> =>
    api.get('/api/v1/reports/types'),

  // Get report templates
  getTemplates: (): Promise<{ data: any[] }> =>
    api.get('/api/v1/reports/templates'),
}

// Export endpoints
export const exportAPI = {
  // Create export job
  createExport: (exportRequest: ExportRequest): Promise<{ data: ExportJobResponse }> =>
    api.post('/api/v1/export/create', exportRequest),

  // Get export job status
  getExportStatus: (jobId: string): Promise<{ data: ExportProgress }> =>
    api.get(`/api/v1/export/status/${jobId}`),

  // Download export file
  downloadExport: (jobId: string): Promise<Blob> =>
    api.get(`/api/v1/export/download/${jobId}`, { responseType: 'blob' }),

  // Get export history
  getExportHistory: (params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/export/history', { params }),

  // Cancel export job
  cancelExport: (jobId: string): Promise<{ data: { message: string } }> =>
    api.post(`/api/v1/export/cancel/${jobId}`),
}

// ML Categorization endpoints
export const mlAPI = {
  // Categorize transaction with ML
  categorizeTransaction: (transactionId: number): Promise<{ data: MLCategorizationResult }> =>
    api.post(`/api/v1/ml/${transactionId}/categorize`),

  // Get ML suggestions for transaction
  getSuggestions: (transactionId: number): Promise<{ data: MLSuggestions }> =>
    api.get(`/api/v1/ml/${transactionId}/suggestions`),

  // Get ML performance metrics
  getPerformanceMetrics: (): Promise<{ data: MLPerformanceMetrics }> =>
    api.get('/api/v1/ml/performance-metrics'),

  // Get ML health status
  getHealthStatus: (): Promise<{ data: any }> =>
    api.get('/api/v1/ml/health-status'),

  // Get training data
  getTrainingData: (): Promise<{ data: any }> =>
    api.get('/api/v1/ml/training-data'),
}

// Cache Management endpoints
export const cacheAPI = {
  // Get cache statistics
  getStats: (): Promise<{ data: CacheStats }> =>
    api.get('/api/v1/cache/stats'),

  // Cleanup expired cache
  cleanup: (): Promise<{ data: { message: string } }> =>
    api.post('/api/v1/cache/cleanup'),

  // Invalidate user cache
  invalidateUserCache: (): Promise<{ data: { message: string } }> =>
    api.post('/api/v1/cache/invalidate-user'),
}

// Monitoring endpoints
export const monitoringAPI = {
  // Get system health status
  getHealth: (): Promise<{ data: HealthStatus }> =>
    api.get('/api/v1/monitoring/health'),

  // Get error metrics
  getErrorMetrics: (params?: {
    hours?: number
  }): Promise<{ data: any }> =>
    api.get('/api/v1/monitoring/metrics', { params }),
}

// Enhanced Analytics endpoints
export const enhancedAnalyticsAPI = {
  // Get cash flow analysis
  getCashFlowAnalysis: (params?: {
    start_date?: string
    end_date?: string
    group_by?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/cash-flow', { params }),

  // Get category insights
  getCategoryInsights: (params?: {
    start_date?: string
    end_date?: string
    category?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/category-insights', { params }),

  // Get vendor analysis
  getVendorAnalysis: (params?: {
    start_date?: string
    end_date?: string
    vendor?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/vendor-analysis', { params }),

  // Get anomaly detection
  getAnomalyDetection: (params?: {
    start_date?: string
    end_date?: string
    threshold?: number
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/anomaly-detection', { params }),

  // Get comparative analysis
  getComparativeAnalysis: (params?: {
    period1_start?: string
    period1_end?: string
    period2_start?: string
    period2_end?: string
    metric?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/comparative', { params }),

  // Get trend analysis
  getTrendAnalysis: (params?: {
    start_date?: string
    end_date?: string
    metric?: string
    period_type?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/trends', { params }),

  // Get dashboard data
  getDashboardData: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<{ data: any }> =>
    api.get('/api/v1/analytics/dashboard', { params }),
}