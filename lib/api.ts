import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

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
      window.location.href = '/login'
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