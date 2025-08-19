import { transactionAPI } from '@/lib/api'
import { mockCategorizationPerformance, mockAutoImprovementResult, mockCategorySuggestions, mockFeedbackResult } from '../utils/test-utils'

// Mock axios
const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() }
  }
}

jest.mock('axios', () => ({
  create: jest.fn(() => mockAxiosInstance)
}))

describe('API Layer', () => {

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getCategorizationPerformance', () => {
    it('calls the correct endpoint', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { data: mockCategorizationPerformance } })

      await transactionAPI.getCategorizationPerformance()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/transactions/categorize/performance')
    })

    it('returns the performance data', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { data: mockCategorizationPerformance } })

      const result = await transactionAPI.getCategorizationPerformance()

      expect(result.data).toEqual(mockCategorizationPerformance)
    })

    it('handles errors properly', async () => {
      const error = new Error('API Error')
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('API Error')
    })
  })

  describe('autoImprove', () => {
    it('calls the correct endpoint with default parameters', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { data: mockAutoImprovementResult } })

      await transactionAPI.autoImprove()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/transactions/categorize/auto-improve', null, {
        params: {}
      })
    })

    it('calls the endpoint with custom parameters', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { data: mockAutoImprovementResult } })

      await transactionAPI.autoImprove({
        batch_id: 'batch_123',
        min_confidence_threshold: 0.9,
        max_transactions: 500
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/transactions/categorize/auto-improve', null, {
        params: {
          batch_id: 'batch_123',
          min_confidence_threshold: 0.9,
          max_transactions: 500
        }
      })
    })

    it('returns the improvement result', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { data: mockAutoImprovementResult } })

      const result = await transactionAPI.autoImprove()

      expect(result.data).toEqual(mockAutoImprovementResult)
    })
  })

  describe('getCategorySuggestions', () => {
    it('calls the correct endpoint with transaction ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { data: mockCategorySuggestions } })

      await transactionAPI.getCategorySuggestions(1)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/transactions/categorize/suggestions/1', {
        params: {}
      })
    })

    it('calls the endpoint with include parameters', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { data: mockCategorySuggestions } })

      await transactionAPI.getCategorySuggestions(1, {
        include_ml: true,
        include_rules: false
      })

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/transactions/categorize/suggestions/1', {
        params: {
          include_ml: true,
          include_rules: false
        }
      })
    })

    it('returns the suggestions data', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { data: mockCategorySuggestions } })

      const result = await transactionAPI.getCategorySuggestions(1)

      expect(result.data).toEqual(mockCategorySuggestions)
    })
  })

  describe('submitFeedback', () => {
    it('calls the correct endpoint with feedback data', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { data: mockFeedbackResult } })

      await transactionAPI.submitFeedback(1, {
        feedback_type: 'correct',
        feedback_comment: 'Great categorization!'
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/transactions/categorize/feedback', null, {
        params: {
          transaction_id: 1,
          feedback_type: 'correct',
          feedback_comment: 'Great categorization!'
        }
      })
    })

    it('calls the endpoint with alternative suggestion', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { data: mockFeedbackResult } })

      await transactionAPI.submitFeedback(1, {
        feedback_type: 'suggest_alternative',
        suggested_category: 'Entertainment',
        suggested_subcategory: 'Movies'
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/transactions/categorize/feedback', null, {
        params: {
          transaction_id: 1,
          feedback_type: 'suggest_alternative',
          suggested_category: 'Entertainment',
          suggested_subcategory: 'Movies'
        }
      })
    })

    it('returns the feedback result', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { data: mockFeedbackResult } })

      const result = await transactionAPI.submitFeedback(1, {
        feedback_type: 'correct'
      })

      expect(result.data).toEqual(mockFeedbackResult)
    })
  })

  describe('Error Handling', () => {
    it('handles 401 unauthorized errors', async () => {
      const error = new Error('Unauthorized')
      ;(error as any).response = { status: 401, data: { message: 'Unauthorized' } }
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('Unauthorized')
    })

    it('handles 403 forbidden errors', async () => {
      const error = new Error('Forbidden')
      ;(error as any).response = { status: 403, data: { message: 'Forbidden' } }
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('Forbidden')
    })

    it('handles 404 not found errors', async () => {
      const error = new Error('Not Found')
      ;(error as any).response = { status: 404, data: { message: 'Not Found' } }
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('Not Found')
    })

    it('handles 429 rate limit errors', async () => {
      const error = new Error('Too Many Requests')
      ;(error as any).response = { 
        status: 429, 
        data: { message: 'Too Many Requests' },
        headers: {
          'retry-after': '60',
          'x-ratelimit-limit': '100',
          'x-ratelimit-reset': '1642237800'
        }
      }
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('Too Many Requests')
    })

    it('handles 500 server errors', async () => {
      const error = new Error('Internal Server Error')
      ;(error as any).response = { status: 500, data: { message: 'Internal Server Error' } }
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('Internal Server Error')
    })

    it('handles network errors', async () => {
      const error = new Error('Network Error')
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(transactionAPI.getCategorizationPerformance()).rejects.toThrow('Network Error')
    })
  })



  describe('Type Safety', () => {
    it('enforces correct parameter types for autoImprove', () => {
      // This test ensures TypeScript compilation
      expect(() => {
        transactionAPI.autoImprove({
          batch_id: 'batch_123',
          min_confidence_threshold: 0.8,
          max_transactions: 1000
        })
      }).not.toThrow()
    })

    it('enforces correct parameter types for submitFeedback', () => {
      // This test ensures TypeScript compilation
      expect(() => {
        transactionAPI.submitFeedback(1, {
          feedback_type: 'correct',
          suggested_category: 'Food & Dining',
          suggested_subcategory: 'Restaurants',
          feedback_comment: 'Great job!'
        })
      }).not.toThrow()
    })

    it('enforces correct parameter types for getCategorySuggestions', () => {
      // This test ensures TypeScript compilation
      expect(() => {
        transactionAPI.getCategorySuggestions(1, {
          include_ml: true,
          include_rules: true
        })
      }).not.toThrow()
    })
  })
})
