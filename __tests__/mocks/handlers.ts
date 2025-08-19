import { http, HttpResponse } from 'msw'
import { mockCategorizationPerformance, mockAutoImprovementResult, mockCategorySuggestions, mockRateLimitInfo, mockFeedbackResult } from '../utils/test-utils'

export const handlers = [
  // Categorization Performance
  http.get('/api/v1/transactions/categorize/performance', () => {
    return HttpResponse.json({ data: mockCategorizationPerformance })
  }),

  // Auto Improvement
  http.post('/api/v1/transactions/categorize/auto-improve', () => {
    return HttpResponse.json({ data: mockAutoImprovementResult })
  }),

  // Category Suggestions
  http.get('/api/v1/transactions/categorize/suggestions/:id', () => {
    return HttpResponse.json({ data: mockCategorySuggestions })
  }),

  // Submit Feedback
  http.post('/api/v1/transactions/categorize/feedback', () => {
    return HttpResponse.json({ data: mockFeedbackResult })
  }),

  // Rate Limit Error
  http.post('/api/v1/transactions/categorize/feedback', ({ request }) => {
    const url = new URL(request.url)
    if (url.searchParams.get('simulate_rate_limit') === 'true') {
      return new HttpResponse(null, {
        status: 429,
        headers: {
          'X-RateLimit-Limit': '100',
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': '1642237800',
          'Retry-After': '60'
        }
      })
    }
    return HttpResponse.json({ data: mockFeedbackResult })
  }),

  // Error scenarios
  http.get('/api/v1/transactions/categorize/performance', ({ request }) => {
    const url = new URL(request.url)
    if (url.searchParams.get('error') === '401') {
      return new HttpResponse(null, { status: 401 })
    }
    if (url.searchParams.get('error') === '403') {
      return new HttpResponse(null, { status: 403 })
    }
    if (url.searchParams.get('error') === '404') {
      return new HttpResponse(null, { status: 404 })
    }
    if (url.searchParams.get('error') === '500') {
      return new HttpResponse(null, { status: 500 })
    }
    return HttpResponse.json({ data: mockCategorizationPerformance })
  })
]
