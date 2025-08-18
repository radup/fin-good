/**
 * Mock Service Worker (MSW) handlers for API mocking in tests.
 * Provides realistic API responses for frontend testing.
 */

import { http, HttpResponse } from 'msw'
import { 
  mockUser, 
  mockAdminUser, 
  generateMockTransaction, 
  generateMockTransactions,
  generateMockAnalytics,
  mockPaginatedResponse 
} from './index'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// ================================
// AUTH HANDLERS
// ================================

export const authHandlers = [
  // Login
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = await request.formData()
    const username = body.get('username')
    const password = body.get('password')
    
    // Simulate authentication logic
    if (username === 'test@example.com' && password === 'password123') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer'
      })
    }
    
    if (username === 'admin@example.com' && password === 'admin123') {
      return HttpResponse.json({
        access_token: 'mock-admin-jwt-token',
        token_type: 'bearer'
      })
    }
    
    return HttpResponse.json(
      { detail: 'Incorrect email or password' },
      { status: 401 }
    )
  }),

  // Register
  http.post(`${API_BASE_URL}/auth/register`, async ({ request }) => {
    const body = await request.json()
    
    // Simulate validation
    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        { detail: 'Email already registered' },
        { status: 400 }
      )
    }
    
    return HttpResponse.json({
      id: 123,
      email: body.email,
      first_name: body.first_name,
      last_name: body.last_name,
      is_active: true,
      is_admin: false,
      created_at: new Date().toISOString()
    }, { status: 201 })
  }),

  // Get current user
  http.get(`${API_BASE_URL}/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    const token = authHeader.replace('Bearer ', '')
    
    if (token === 'mock-jwt-token') {
      return HttpResponse.json(mockUser)
    }
    
    if (token === 'mock-admin-jwt-token') {
      return HttpResponse.json(mockAdminUser)
    }
    
    return HttpResponse.json(
      { detail: 'Could not validate credentials' },
      { status: 401 }
    )
  }),
]

// ================================
// TRANSACTION HANDLERS
// ================================

let mockTransactions = generateMockTransactions(50)

export const transactionHandlers = [
  // Get transactions
  http.get(`${API_BASE_URL}/transactions/`, ({ request }) => {
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const size = parseInt(url.searchParams.get('size') || '20')
    const category = url.searchParams.get('category')
    const startDate = url.searchParams.get('start_date')
    const endDate = url.searchParams.get('end_date')
    
    // Filter transactions
    let filteredTransactions = [...mockTransactions]
    
    if (category) {
      filteredTransactions = filteredTransactions.filter(t => t.category === category)
    }
    
    if (startDate) {
      filteredTransactions = filteredTransactions.filter(t => t.date >= startDate)
    }
    
    if (endDate) {
      filteredTransactions = filteredTransactions.filter(t => t.date <= endDate)
    }
    
    // Paginate
    const startIndex = (page - 1) * size
    const endIndex = startIndex + size
    const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex)
    
    return HttpResponse.json(
      mockPaginatedResponse(paginatedTransactions, page, size, filteredTransactions.length)
    )
  }),

  // Get single transaction
  http.get(`${API_BASE_URL}/transactions/:id`, ({ params }) => {
    const id = parseInt(params.id as string)
    const transaction = mockTransactions.find(t => t.id === id)
    
    if (!transaction) {
      return HttpResponse.json(
        { detail: 'Transaction not found' },
        { status: 404 }
      )
    }
    
    return HttpResponse.json(transaction)
  }),

  // Create transaction
  http.post(`${API_BASE_URL}/transactions/`, async ({ request }) => {
    const body = await request.json()
    
    const newTransaction = {
      ...generateMockTransaction(),
      ...body,
      id: Math.max(...mockTransactions.map(t => t.id)) + 1,
      created_at: new Date().toISOString()
    }
    
    mockTransactions.push(newTransaction)
    
    return HttpResponse.json(newTransaction, { status: 201 })
  }),

  // Update transaction
  http.put(`${API_BASE_URL}/transactions/:id`, async ({ params, request }) => {
    const id = parseInt(params.id as string)
    const body = await request.json()
    
    const transactionIndex = mockTransactions.findIndex(t => t.id === id)
    
    if (transactionIndex === -1) {
      return HttpResponse.json(
        { detail: 'Transaction not found' },
        { status: 404 }
      )
    }
    
    mockTransactions[transactionIndex] = {
      ...mockTransactions[transactionIndex],
      ...body
    }
    
    return HttpResponse.json(mockTransactions[transactionIndex])
  }),

  // Delete transaction
  http.delete(`${API_BASE_URL}/transactions/:id`, ({ params }) => {
    const id = parseInt(params.id as string)
    const transactionIndex = mockTransactions.findIndex(t => t.id === id)
    
    if (transactionIndex === -1) {
      return HttpResponse.json(
        { detail: 'Transaction not found' },
        { status: 404 }
      )
    }
    
    mockTransactions.splice(transactionIndex, 1)
    
    return new HttpResponse(null, { status: 204 })
  }),
]

// ================================
// ANALYTICS HANDLERS
// ================================

export const analyticsHandlers = [
  // Get analytics
  http.get(`${API_BASE_URL}/analytics/`, ({ request }) => {
    const url = new URL(request.url)
    const startDate = url.searchParams.get('start_date')
    const endDate = url.searchParams.get('end_date')
    
    // In a real implementation, this would filter based on dates
    return HttpResponse.json(generateMockAnalytics())
  }),
]

// ================================
// CATEGORY HANDLERS
// ================================

export const categoryHandlers = [
  // Get categories
  http.get(`${API_BASE_URL}/categories/`, () => {
    return HttpResponse.json([
      'Food & Dining',
      'Transportation',
      'Shopping',
      'Entertainment',
      'Bills & Utilities',
      'Income',
      'Healthcare',
      'Travel',
      'Education',
      'Personal Care',
      'Gifts & Donations',
      'Investments'
    ])
  }),

  // Categorize transaction
  http.post(`${API_BASE_URL}/categories/categorize`, async ({ request }) => {
    const body = await request.json()
    
    // Simple categorization based on description keywords
    const description = body.description.toLowerCase()
    let category = 'Other'
    
    if (description.includes('grocery') || description.includes('restaurant') || description.includes('food')) {
      category = 'Food & Dining'
    } else if (description.includes('gas') || description.includes('uber') || description.includes('transport')) {
      category = 'Transportation'
    } else if (description.includes('amazon') || description.includes('store') || description.includes('shop')) {
      category = 'Shopping'
    } else if (description.includes('salary') || description.includes('income') || description.includes('paycheck')) {
      category = 'Income'
    }
    
    return HttpResponse.json({
      category,
      confidence: 0.85
    })
  }),
]

// ================================
// UPLOAD HANDLERS
// ================================

export const uploadHandlers = [
  // Upload CSV
  http.post(`${API_BASE_URL}/upload/csv`, async ({ request }) => {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return HttpResponse.json(
        { detail: 'No file provided' },
        { status: 400 }
      )
    }
    
    if (!file.name.endsWith('.csv')) {
      return HttpResponse.json(
        { detail: 'Invalid file type. Only CSV files are allowed.' },
        { status: 400 }
      )
    }
    
    // Simulate processing
    const mockResults = {
      total_rows: 100,
      successful: 95,
      failed: 5,
      errors: [
        { row: 10, error: 'Invalid date format' },
        { row: 25, error: 'Missing amount' },
        { row: 50, error: 'Invalid amount format' },
        { row: 75, error: 'Missing description' },
        { row: 90, error: 'Duplicate transaction' },
      ]
    }
    
    return HttpResponse.json(mockResults, { status: 201 })
  }),
]

// ================================
// ERROR HANDLERS
// ================================

export const errorHandlers = [
  // Simulate server error
  http.get(`${API_BASE_URL}/error/500`, () => {
    return HttpResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }),

  // Simulate network error
  http.get(`${API_BASE_URL}/error/network`, () => {
    return HttpResponse.error()
  }),

  // Simulate timeout
  http.get(`${API_BASE_URL}/error/timeout`, async () => {
    await new Promise(resolve => setTimeout(resolve, 10000))
    return HttpResponse.json({ message: 'This should timeout' })
  }),
]

// ================================
// COMBINED HANDLERS
// ================================

export const handlers = [
  ...authHandlers,
  ...transactionHandlers,
  ...analyticsHandlers,
  ...categoryHandlers,
  ...uploadHandlers,
  ...errorHandlers,
]

export default handlers