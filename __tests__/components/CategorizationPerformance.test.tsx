import React from 'react'
import { render, screen, waitFor } from '../utils/test-utils'
import userEvent from '@testing-library/user-event'
import CategorizationPerformance from '@/components/CategorizationPerformance'
import { mockCategorizationPerformance } from '../utils/test-utils'

// Mock the API module
jest.mock('@/lib/api', () => ({
  transactionAPI: {
    getCategorizationPerformance: jest.fn()
  }
}))

describe('CategorizationPerformance', () => {
  const mockGetCategorizationPerformance = jest.mocked(
    require('@/lib/api').transactionAPI.getCategorizationPerformance
  )

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the component with loading state initially', () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    expect(screen.getByText('Categorization Performance')).toBeInTheDocument()
    expect(screen.getByText('Track AI categorization performance over time')).toBeInTheDocument()
  })

  it('displays performance metrics when data loads successfully', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('94.5%')).toBeInTheDocument() // Overall accuracy
      expect(screen.getByText('87.2%')).toBeInTheDocument() // Overall confidence
      expect(screen.getByText('12,500')).toBeInTheDocument() // Total transactions
    })
  })

  it('displays method breakdown information', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Rule-Based')).toBeInTheDocument()
      expect(screen.getByText('ML-Based')).toBeInTheDocument()
      expect(screen.getByText('7,500')).toBeInTheDocument() // Rule-based count
      expect(screen.getByText('4,375')).toBeInTheDocument() // ML-based count
    })
  })

  it('handles API errors gracefully', async () => {
    mockGetCategorizationPerformance.mockRejectedValue(new Error('API Error'))

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText(/Error loading performance data/)).toBeInTheDocument()
    })
  })

  it('handles 401 unauthorized error', async () => {
    const error = new Error('Unauthorized')
    ;(error as any).response = { status: 401 }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText(/Please log in to view performance data/)).toBeInTheDocument()
    })
  })

  it('handles 403 forbidden error', async () => {
    const error = new Error('Forbidden')
    ;(error as any).response = { status: 403 }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText(/You don't have permission to view this data/)).toBeInTheDocument()
    })
  })

  it('handles 404 not found error', async () => {
    const error = new Error('Not Found')
    ;(error as any).response = { status: 404 }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText(/Performance data not found/)).toBeInTheDocument()
    })
  })

  it('handles 429 rate limit error', async () => {
    const error = new Error('Too Many Requests')
    ;(error as any).response = { status: 429 }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText(/Too many requests. Please try again later/)).toBeInTheDocument()
    })
  })

  it('handles 500 server error', async () => {
    const error = new Error('Internal Server Error')
    ;(error as any).response = { status: 500 }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText(/Server error. Please try again later/)).toBeInTheDocument()
    })
  })

  it('shows feedback analysis when available', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('1,250')).toBeInTheDocument() // Positive feedback
      expect(screen.getByText('89')).toBeInTheDocument() // Negative feedback
      expect(screen.getByText('234')).toBeInTheDocument() // Improvement suggestions
    })
  })

  it('displays category performance breakdown', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Food & Dining')).toBeInTheDocument()
      expect(screen.getByText('Transportation')).toBeInTheDocument()
      expect(screen.getByText('Shopping')).toBeInTheDocument()
    })
  })

  it('shows learning rate information', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('85%')).toBeInTheDocument() // Learning rate
    })
  })

  it('handles empty or missing data gracefully', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: {
        overall_accuracy: 0,
        overall_confidence: 0,
        total_transactions: 0,
        categorized_transactions: 0,
        uncategorized_transactions: 0,
        method_breakdown: {
          rule_based: { count: 0, accuracy: 0, confidence: 0 },
          ml_based: { count: 0, accuracy: 0, confidence: 0 }
        },
        category_performance: [],
        feedback_analysis: {
          positive_feedback: 0,
          negative_feedback: 0,
          improvement_suggestions: 0,
          learning_rate: 0
        }
      }
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('0%')).toBeInTheDocument() // Overall accuracy
      expect(screen.getByText('0%')).toBeInTheDocument() // Overall confidence
      expect(screen.getByText('0')).toBeInTheDocument() // Total transactions
    })
  })

  it('is accessible with proper ARIA labels', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      // Check for proper heading structure
      expect(screen.getByRole('heading', { name: 'Categorization Performance' })).toBeInTheDocument()
      
      // Check for proper descriptions
      expect(screen.getByText('Track AI categorization performance over time')).toBeInTheDocument()
    })
  })
})
