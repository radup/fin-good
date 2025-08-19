import axios from 'axios'
import {
  BulkOperationResponse,
  BulkOperationRequest,
  DuplicateGroup,
  DuplicateScanResponse,
  DuplicateMergeResponse,
  Pattern,
  PatternAnalysisResponse,
  PatternRuleGenerationResponse,
  EnhancedPerformanceMetrics,
  PredictiveInsights,
  EnhancedVendorAnalysis,
  AnalyticsSummary,
  ReportTemplate,
  ReportJob,
  ReportSchedule,
  ForecastRequest,
  ForecastResponse,
  AccuracyHistoryResponse,
  EnsembleAnalysisResponse,
  BatchForecastRequest,
  BatchForecastResponse,
  ForecastTypeInfo,
  ForecastHorizonInfo,
  ForecastingHealth,
  Budget,
  BudgetListResponse,
  BudgetDetailResponse,
  BudgetVarianceResponse,
  BudgetRecommendationsResponse,
  BudgetScenariosResponse,
  BudgetScenario,
  BudgetAlertsResponse,
  BudgetAlert,
  BudgetPerformanceResponse,
  BudgetAnalysisSummary,
  BudgetAnalysisHealth
} from '@/types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

// Types for rate limit handling
export interface RateLimitInfo {
  retry_after: number
  limit: number
  reset_time: string
  message: string
}

// Global CSRF token storage
let globalCsrfToken: string | null = null

export const setGlobalCsrfToken = (token: string | null) => {
  globalCsrfToken = token
}

export const getGlobalCsrfToken = () => globalCsrfToken

// Helper function to extract CSRF token from cookie
const getCsrfTokenFromCookie = (): string | null => {
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
      
      // Don't redirect if we're already on the login page or if it's a login request
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      const isAuthCheckRequest = error.config?.url?.includes('/auth/me')
      const isRefreshCsrfRequest = error.config?.url?.includes('/auth/refresh-csrf')
      const isOnLoginPage = typeof window !== 'undefined' && window.location.pathname === '/login'
      
      if (!isLoginRequest && !isAuthCheckRequest && !isRefreshCsrfRequest && !isOnLoginPage) {
        window.location.href = '/login'
      }
    } else if (error.response?.status === 429) {
      // Handle rate limiting
      const retryAfter = error.response.data?.retry_after || 60
      const limit = error.response.data?.limit
      const currentUsage = error.response.data?.current_usage
      
      console.warn(`Rate limit exceeded. Retry after ${retryAfter} seconds.`)
      
      // Enhanced rate limit handling with detailed information
      if (typeof window !== 'undefined') {
        // Show user-friendly rate limit message
        const event = new CustomEvent('rate-limit-exceeded', {
          detail: {
            retryAfter,
            limit,
            currentUsage,
            endpoint: error.config?.url,
            method: error.config?.method
          }
        })
        window.dispatchEvent(event)
      }
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error:', error.response?.data)
      
      if (typeof window !== 'undefined') {
        const event = new CustomEvent('server-error', {
          detail: {
            status: error.response?.status,
            message: error.response?.data?.detail || 'An unexpected error occurred',
            endpoint: error.config?.url
          }
        })
        window.dispatchEvent(event)
      }
    } else if (error.response?.status >= 400) {
      // Handle client errors
      console.warn('Client error:', error.response?.data)
      
      if (typeof window !== 'undefined') {
        const event = new CustomEvent('client-error', {
          detail: {
            status: error.response?.status,
            message: error.response?.data?.detail || 'Invalid request',
            endpoint: error.config?.url
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

  // Get categorization performance metrics
  getCategorizationPerformance: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<{ data: CategorizationPerformance }> =>
    api.get('/api/v1/transactions/categorize/performance', { params }),

  // Auto-improve categorization based on user feedback and patterns
  autoImprove: (params?: {
    batch_id?: string
    min_confidence_threshold?: number
    max_transactions?: number
  }): Promise<{ data: AutoImprovementResult }> =>
    api.post('/api/v1/transactions/categorize/auto-improve', null, { params }),

  // Get category suggestions for a transaction
  getCategorySuggestions: (transactionId: number, params?: {
    include_ml?: boolean
    include_rules?: boolean
  }): Promise<{ data: CategorySuggestions }> =>
    api.get(`/api/v1/transactions/categorize/suggestions/${transactionId}`, { params }),

  // Submit categorization feedback
  submitFeedback: (transactionId: number, params: {
    feedback_type: 'correct' | 'incorrect' | 'suggest_alternative'
    suggested_category?: string
    suggested_subcategory?: string
    feedback_comment?: string
  }): Promise<{ data: FeedbackResult }> =>
    api.post(`/api/v1/transactions/categorize/feedback`, null, { 
      params: { transaction_id: transactionId, ...params }
    }),

  // List import batches (files)
  listImportBatches: () => 
    api.get('/api/v1/transactions/import-batches'),

  // Delete transactions by import batch
  deleteImportBatch: (batchId: string) => 
    api.delete(`/api/v1/transactions/import-batch/${batchId}`),

  // NEW: Bulk categorization with transaction IDs
  bulkCategorize: (transactionIds: number[], useMlFallback?: boolean) =>
    api.post('/api/v1/transactions/categorize/bulk', { 
      transaction_ids: transactionIds, 
      use_ml_fallback: useMlFallback 
    }),

  // NEW: Confidence analysis for individual transactions
  getConfidence: (transactionId: number) =>
    api.get(`/api/v1/transactions/categorize/confidence/${transactionId}`),

  // NEW: Category suggestions with rule-based and ML-based recommendations
  getSuggestions: (transactionId: number, includeMl?: boolean, includeRules?: boolean) =>
    api.get(`/api/v1/transactions/categorize/suggestions/${transactionId}`, {
      params: { include_ml: includeMl, include_rules: includeRules }
    }),

  // NEW: Categorization performance metrics
  getPerformance: (params?: { start_date?: string, end_date?: string }) =>
    api.get('/api/v1/transactions/categorize/performance', { params }),
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

// Export endpoints
export const exportAPI = {
  // Create export job
  createJob: (data: {
    export_format: 'csv' | 'excel' | 'pdf' | 'json'
    export_name?: string
    filters?: any
    columns_config?: any
    options_config?: any
  }) => api.post('/api/v1/export/create', data),
  
  // Get export progress
  getProgress: (jobId: string) => api.get(`/api/v1/export/progress/${jobId}`),
  
  // Download export file
  download: (downloadToken: string) => api.get(`/api/v1/export/download/${downloadToken}`),
  
  // Get export history
  getHistory: (limit?: number) => api.get('/api/v1/export/history', { params: { limit } }),
  
  // Cancel export job
  cancelJob: (jobId: string) => api.delete(`/api/v1/export/cancel/${jobId}`),
  
  // Get export templates
  getTemplates: () => api.get('/api/v1/export/templates'),
  
  // Get export statistics
  getStats: () => api.get('/api/v1/export/stats'),
  
  // Cleanup expired exports
  cleanup: () => api.post('/api/v1/export/cleanup'),
}

// ============================================================================
// NEW API ENDPOINTS FOR PHASE 2 BACKEND FEATURES
// ============================================================================

// Bulk Operations API
export const bulkOperationsAPI = {
  // Bulk categorize transactions
  categorize: (transactionIds: number[], category: string, subcategory?: string) =>
    api.post<BulkOperationResponse>('/api/v1/transactions/bulk/categorize', {
      transaction_ids: transactionIds,
      category,
      subcategory
    }),

  // Bulk update transactions
  update: (request: BulkOperationRequest) =>
    api.put<BulkOperationResponse>('/api/v1/transactions/bulk/update', request),

  // Bulk delete transactions
  delete: (transactionIds: number[]) =>
    api.delete<BulkOperationResponse>('/api/v1/transactions/bulk/delete', {
      data: { transaction_ids: transactionIds }
    }),

  // Undo last bulk operation
  undo: () => api.post<BulkOperationResponse>('/api/v1/transactions/bulk/undo'),

  // Redo last undone bulk operation
  redo: () => api.post<BulkOperationResponse>('/api/v1/transactions/bulk/redo'),

  // Get bulk operation history
  getHistory: (limit?: number) =>
    api.get<BulkOperationResponse[]>('/api/v1/transactions/bulk/history', { params: { limit } }),
}

// Duplicate Detection API
export const duplicateDetectionAPI = {
  // Scan for duplicates
  scan: (params?: {
    confidence_threshold?: number
    algorithms?: string[]
    max_results?: number
  }) => api.post<DuplicateScanResponse>('/api/v1/duplicates/scan', null, { params }),

  // Get duplicate groups
  getGroups: (params?: {
    limit?: number
    offset?: number
    min_confidence?: number
    algorithm?: string
  }) => api.get<DuplicateGroup[]>('/api/v1/duplicates/groups', { params }),

  // Get specific duplicate group
  getGroup: (groupId: string) => api.get<DuplicateGroup>(`/api/v1/duplicates/groups/${groupId}`),

  // Merge duplicate transactions
  merge: (groupId: string, primaryTransactionId: number, fieldsToMerge: string[]) =>
    api.post<DuplicateMergeResponse>('/api/v1/duplicates/merge', {
      group_id: groupId,
      primary_transaction_id: primaryTransactionId,
      fields_to_merge: fieldsToMerge
    }),

  // Dismiss duplicate group (mark as false positive)
  dismiss: (groupId: string, reason?: string) =>
    api.post('/api/v1/duplicates/dismiss', {
      group_id: groupId,
      reason
    }),

  // Get duplicate statistics
  getStats: () => api.get('/api/v1/duplicates/stats'),

  // Get duplicate scan history
  getScanHistory: (limit?: number) =>
    api.get('/api/v1/duplicates/scan-history', { params: { limit } }),
}

// Pattern Recognition API
export const patternRecognitionAPI = {
  // Analyze patterns in transactions
  analyze: (params?: {
    pattern_types?: string[]
    min_confidence?: number
    min_support?: number
    max_patterns?: number
  }) => api.post<PatternAnalysisResponse>('/api/v1/patterns/analyze', null, { params }),

  // Get recognized patterns
  getRecognized: (params?: {
    pattern_type?: string
    min_confidence?: number
    limit?: number
    offset?: number
  }) => api.get<Pattern[]>('/api/v1/patterns/recognized', { params }),

  // Get specific pattern
  getPattern: (patternId: string) => api.get<Pattern>(`/api/v1/patterns/${patternId}`),

  // Generate rules from patterns
  generateRules: (params?: {
    pattern_ids?: string[]
    min_confidence?: number
    auto_apply?: boolean
  }) => api.post<PatternRuleGenerationResponse>('/api/v1/patterns/generate-rules', null, { params }),

  // Get pattern statistics
  getStats: () => api.get('/api/v1/patterns/stats'),

  // Get user pattern profile
  getUserProfile: () => api.get('/api/v1/patterns/user-profile'),

  // Update pattern accuracy feedback
  updateAccuracy: (patternId: string, accuracy: number, feedback?: string) =>
    api.put(`/api/v1/patterns/${patternId}/accuracy`, {
      accuracy,
      feedback
    }),
}

// Enhanced Analytics API
export const enhancedAnalyticsAPI = {
  // Get enhanced performance metrics
  getPerformanceMetrics: () => api.get<EnhancedPerformanceMetrics>('/api/v1/analytics/v2/performance-metrics'),

  // Get predictive insights
  getPredictiveInsights: (params?: {
    forecast_periods?: number
    confidence_level?: number
  }) => api.get<PredictiveInsights>('/api/v1/analytics/v2/predictive-insights', { params }),

  // Get enhanced vendor analysis
  getEnhancedVendorAnalysis: (params?: {
    vendor?: string
    date_range?: string
    include_anomalies?: boolean
  }) => api.get<EnhancedVendorAnalysis>('/api/v1/analytics/v2/enhanced-vendor-analysis', { params }),

  // Clear enhanced cache
  clearEnhancedCache: () => api.post('/api/v1/analytics/v2/clear-enhanced-cache'),

  // Get comprehensive analytics summary
  getAnalyticsSummary: (params?: {
    start_date?: string
    end_date?: string
    include_predictions?: boolean
  }) => api.get<AnalyticsSummary>('/api/v1/analytics/v2/analytics-summary', { params }),
}

// Report Builder API
export const reportBuilderAPI = {
  // Create report job
  createReport: (data: {
    template_id: string
    parameters: Record<string, any>
    format?: 'pdf' | 'excel' | 'html' | 'csv' | 'json'
  }) => api.post<ReportJob>('/api/v1/reports/v2/create', data),

  // Get report templates
  getTemplates: (params?: {
    report_type?: string
    format?: string
  }) => api.get<ReportTemplate[]>('/api/v1/reports/v2/templates', { params }),

  // Get specific template
  getTemplate: (templateId: string) => api.get<ReportTemplate>(`/api/v1/reports/v2/templates/${templateId}`),

  // Get report progress
  getProgress: (jobId: string) => api.get<ReportJob>(`/api/v1/reports/v2/progress/${jobId}`),

  // Download report
  download: (downloadToken: string) => api.get(`/api/v1/reports/v2/download/${downloadToken}`),

  // Get report history
  getHistory: (params?: {
    limit?: number
    offset?: number
    status?: string
  }) => api.get<ReportJob[]>('/api/v1/reports/v2/history', { params }),

  // Schedule report
  scheduleReport: (data: {
    template_id: string
    name: string
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
    parameters: Record<string, any>
    recipients: string[]
  }) => api.post<ReportSchedule>('/api/v1/reports/v2/schedule', data),

  // Get scheduled reports
  getScheduledReports: () => api.get<ReportSchedule[]>('/api/v1/reports/v2/scheduled'),

  // Update scheduled report
  updateScheduledReport: (scheduleId: string, data: Partial<ReportSchedule>) =>
    api.put<ReportSchedule>(`/api/v1/reports/v2/scheduled/${scheduleId}`, data),

  // Delete scheduled report
  deleteScheduledReport: (scheduleId: string) =>
    api.delete(`/api/v1/reports/v2/scheduled/${scheduleId}`),

  // Cancel report job
  cancelJob: (jobId: string) => api.delete(`/api/v1/reports/v2/cancel/${jobId}`),
}

// Forecasting API
export const forecastingAPI = {
  // Generate forecast
  generateForecast: (data: ForecastRequest) => {
    const { forecast_type, ...kwargs } = data
    const params = {
      args: forecast_type,
      kwargs: JSON.stringify(kwargs)
    }
    return api.post<ForecastResponse>('/api/v1/forecasting/generate', null, { params })
  },

  // Get forecast accuracy history
  getAccuracyHistory: (params?: {
    days?: number
  }) => {
    const apiParams = {
      args: 'accuracy_history',
      kwargs: JSON.stringify(params || {})
    }
    return api.get<AccuracyHistoryResponse>('/api/v1/forecasting/accuracy-history', { params: apiParams })
  },

  // Get model analysis
  getModelAnalysis: (params?: {
    forecast_type?: string
    horizon?: string
  }) => {
    const apiParams = {
      args: 'model_analysis',
      kwargs: JSON.stringify(params || {})
    }
    return api.get<EnsembleAnalysisResponse>('/api/v1/forecasting/model-analysis', { params: apiParams })
  },

  // Batch forecast
  batchForecast: (data: BatchForecastRequest) => {
    const apiParams = {
      args: 'batch_forecast',
      kwargs: JSON.stringify(data)
    }
    return api.post<BatchForecastResponse>('/api/v1/forecasting/batch-forecast', null, { params: apiParams })
  },

  // Get available forecast types
  getForecastTypes: () => {
    const params = {
      args: 'forecast_types',
      kwargs: '{}'
    }
    return api.get<ForecastTypeInfo[]>('/api/v1/forecasting/forecast-types', { params })
  },

  // Get available horizons
  getHorizons: () => {
    const params = {
      args: 'horizons',
      kwargs: '{}'
    }
    return api.get<ForecastHorizonInfo[]>('/api/v1/forecasting/horizons', { params })
  },

  // Get forecasting health status
  getHealth: () => api.get<ForecastingHealth>('/api/v1/forecasting/health'),
}

// Budget Analysis API
export const budgetAnalysisAPI = {
  // Get budget list
  getBudgets: (params?: {
    page?: number
    page_size?: number
    status?: string
  }) => api.get<BudgetListResponse>('/api/v1/budgets', { params }),

  // Get budget details
  getBudget: (budgetId: string) => 
    api.get<BudgetDetailResponse>(`/api/v1/budgets/${budgetId}`),

  // Create budget
  createBudget: (data: {
    name: string
    description: string
    period_type: 'monthly' | 'quarterly' | 'yearly' | 'custom'
    start_date: string
    end_date: string
    total_budget: number
    currency: string
  }) => api.post<Budget>('/api/v1/budgets', data),

  // Update budget
  updateBudget: (budgetId: string, data: Partial<Budget>) =>
    api.put<Budget>(`/api/v1/budgets/${budgetId}`, data),

  // Delete budget
  deleteBudget: (budgetId: string) =>
    api.delete(`/api/v1/budgets/${budgetId}`),

  // Get budget variance analysis
  getVarianceAnalysis: (budgetId: string, params?: {
    period_start?: string
    period_end?: string
  }) => api.get<BudgetVarianceResponse>(`/api/v1/budgets/${budgetId}/variance`, { params }),

  // Get budget recommendations
  getRecommendations: (budgetId: string, params?: {
    limit?: number
    applied?: boolean
  }) => api.get<BudgetRecommendationsResponse>(`/api/v1/budgets/${budgetId}/recommendations`, { params }),

  // Apply recommendation
  applyRecommendation: (budgetId: string, recommendationId: string) =>
    api.post(`/api/v1/budgets/${budgetId}/recommendations/${recommendationId}/apply`),

  // Get budget scenarios
  getScenarios: (budgetId: string, params?: {
    scenario_type?: string
    limit?: number
  }) => api.get<BudgetScenariosResponse>(`/api/v1/budgets/${budgetId}/scenarios`, { params }),

  // Create budget scenario
  createScenario: (budgetId: string, data: {
    name: string
    description: string
    scenario_type: 'what_if' | 'optimization' | 'forecast' | 'stress_test'
    adjustments: Array<{
      category: string
      subcategory?: string
      adjustment_type: 'increase' | 'decrease' | 'reallocate'
      amount: number
      percentage: number
      reasoning: string
    }>
  }) => api.post<BudgetScenario>(`/api/v1/budgets/${budgetId}/scenarios`, data),

  // Get budget alerts
  getAlerts: (budgetId: string, params?: {
    acknowledged?: boolean
    severity?: string
    limit?: number
  }) => api.get<BudgetAlertsResponse>(`/api/v1/budgets/${budgetId}/alerts`, { params }),

  // Acknowledge alert
  acknowledgeAlert: (budgetId: string, alertId: string) =>
    api.post(`/api/v1/budgets/${budgetId}/alerts/${alertId}/acknowledge`),

  // Create budget alert
  createAlert: (budgetId: string, data: {
    alert_type: 'variance_threshold' | 'category_overrun' | 'trend_warning' | 'forecast_alert'
    threshold_type: 'percentage' | 'absolute_amount'
    threshold_value: number
    condition: 'greater_than' | 'less_than' | 'equals'
    category?: string
    subcategory?: string
    notification_channels: ('email' | 'push' | 'in_app')[]
  }) => api.post<BudgetAlert>(`/api/v1/budgets/${budgetId}/alerts`, data),

  // Get budget performance metrics
  getPerformance: (budgetId: string, params?: {
    period_start?: string
    period_end?: string
  }) => api.get<BudgetPerformanceResponse>(`/api/v1/budgets/${budgetId}/performance`, { params }),

  // Get budget analysis summary
  getSummary: () => api.get<BudgetAnalysisSummary>('/api/v1/budgets/summary'),

  // Get budget analysis health
  getHealth: () => api.get<BudgetAnalysisHealth>('/api/v1/budgets/health'),
}