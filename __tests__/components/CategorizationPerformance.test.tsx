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
    
    expect(screen.getByText('Loading performance data...')).toBeInTheDocument()
  })

  it('displays performance metrics when data loads successfully', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('92.0%')).toBeInTheDocument() // Accuracy rate
      expect(screen.getByText('85.0%')).toBeInTheDocument() // Average confidence
      expect(screen.getByText('1,250')).toBeInTheDocument() // Total transactions
    })
  })

  it('displays method breakdown information', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Categorization Performance')).toBeInTheDocument()
      expect(screen.getByText('Comprehensive metrics and insights for transaction categorization')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    mockGetCategorizationPerformance.mockRejectedValue(new Error('API Error'))

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load performance data')).toBeInTheDocument()
    })
  })

  it('handles 401 unauthorized error', async () => {
    const error = new Error('Unauthorized')
    ;(error as any).response = { status: 401, data: { detail: 'Please log in to view performance data' } }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Please log in to view performance data')).toBeInTheDocument()
    })
  })

  it('handles 403 forbidden error', async () => {
    const error = new Error('Forbidden')
    ;(error as any).response = { status: 403, data: { detail: 'You don\'t have permission to view this data' } }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('You don\'t have permission to view this data')).toBeInTheDocument()
    })
  })

  it('handles 404 not found error', async () => {
    const error = new Error('Not Found')
    ;(error as any).response = { status: 404, data: { detail: 'Performance data not found' } }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Performance data not found')).toBeInTheDocument()
    })
  })

  it('handles 429 rate limit error', async () => {
    const error = new Error('Too Many Requests')
    ;(error as any).response = { status: 429, data: { detail: 'Too many requests. Please try again later' } }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Too many requests. Please try again later')).toBeInTheDocument()
    })
  })

  it('handles 500 server error', async () => {
    const error = new Error('Internal Server Error')
    ;(error as any).response = { status: 500, data: { detail: 'Server error. Please try again later' } }
    mockGetCategorizationPerformance.mockRejectedValue(error)

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Server error. Please try again later')).toBeInTheDocument()
    })
  })

  it('shows feedback analysis when available', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('1,180')).toBeInTheDocument() // Categorized count
      expect(screen.getByText('94.4%')).toBeInTheDocument() // Categorized percentage
    })
  })

  it('displays category performance breakdown', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Transactions')).toBeInTheDocument()
      expect(screen.getByText('Categorized')).toBeInTheDocument()
      expect(screen.getByText('Accuracy Rate')).toBeInTheDocument()
      expect(screen.getByText('Avg Confidence')).toBeInTheDocument()
    })
  })

  it('shows learning rate information', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: mockCategorizationPerformance
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getByTitle('Refresh data')).toBeInTheDocument() // Refresh button
    })
  })

  it('handles empty or missing data gracefully', async () => {
    mockGetCategorizationPerformance.mockResolvedValue({
      data: {
        user_id: 1,
        period: { start_date: null, end_date: null },
        overall_metrics: {
          total_transactions: 0,
          categorized_count: 0,
          accuracy_rate: 0,
          average_confidence: 0,
          success_rate: 0
        },
        method_breakdown: {
          rule_based: { count: 0, accuracy: 0, average_confidence: 0 },
          ml_based: { count: 0, accuracy: 0, average_confidence: 0 }
        },
        confidence_distribution: { high_confidence: 0, medium_confidence: 0, low_confidence: 0 },
        category_performance: {},
        improvement_trends: { daily_accuracy: [], weekly_improvement: 0 },
        feedback_analysis: { total_feedback: 0, positive_feedback: 0, negative_feedback: 0, feedback_accuracy: 0 }
      }
    })

    render(<CategorizationPerformance />)
    
    await waitFor(() => {
      expect(screen.getAllByText('0')[0]).toBeInTheDocument() // Total transactions
      expect(screen.getAllByText('0.0%')[0]).toBeInTheDocument() // Accuracy rate
      expect(screen.getAllByText('0.0%')[1]).toBeInTheDocument() // Average confidence
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
      expect(screen.getByText('Comprehensive metrics and insights for transaction categorization')).toBeInTheDocument()
    })
  })
})
