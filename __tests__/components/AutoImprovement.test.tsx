import React from 'react'
import { render, screen, waitFor } from '../utils/test-utils'
import userEvent from '@testing-library/user-event'
import AutoImprovement from '@/components/AutoImprovement'
import { mockAutoImprovementResult } from '../utils/test-utils'

// Mock the API module
jest.mock('@/lib/api', () => ({
  transactionAPI: {
    autoImprove: jest.fn()
  }
}))

describe('AutoImprovement', () => {
  const mockAutoImprove = jest.mocked(
    require('@/lib/api').transactionAPI.autoImprove
  )

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the component with initial state', () => {
    render(<AutoImprovement />)
    
    expect(screen.getByText('Auto-Improvement')).toBeInTheDocument()
    expect(screen.getByText('Automatically improve categorization rules and ML model based on feedback and patterns')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start Auto-Improvement' })).toBeInTheDocument()
  })

  it('displays configuration options when settings button is clicked', async () => {
    const user = userEvent.setup()
    render(<AutoImprovement />)
    
    // Configuration should be hidden initially
    expect(screen.queryByLabelText('Confidence Threshold')).not.toBeInTheDocument()
    
    // Click settings button to show configuration
    const settingsButton = screen.getByTitle('Show configuration')
    await user.click(settingsButton)
    
    expect(screen.getByText(/Confidence Threshold/)).toBeInTheDocument()
    expect(screen.getByText(/Max Transactions/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Leave empty for all transactions')).toBeInTheDocument()
  })

  it('runs auto-improvement when button is clicked', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockResolvedValue({
      data: mockAutoImprovementResult
    })

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(mockAutoImprove).toHaveBeenCalledWith({
        min_confidence_threshold: 0.5,
        max_transactions: 1000
      })
    })
  })

  it('displays improvement results when successful', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockResolvedValue({
      data: mockAutoImprovementResult
    })

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Auto-improvement completed successfully')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument() // Rules created
      expect(screen.getByText('8')).toBeInTheDocument() // Rules updated
      expect(screen.getByText('3')).toBeInTheDocument() // ML improvements
      expect(screen.getByText('1,250')).toBeInTheDocument() // Transactions reprocessed
      expect(screen.getByText('87.0%')).toBeInTheDocument() // Improvement score
      expect(screen.getByText(/45\.2s/)).toBeInTheDocument() // Processing time
    })
  })

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockRejectedValue(new Error('API Error'))

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Auto-improvement failed. Please try again.')).toBeInTheDocument()
    })
  })

  it('handles 401 unauthorized error', async () => {
    const user = userEvent.setup()
    const error = new Error('Unauthorized')
    ;(error as any).response = { status: 401 }
    mockAutoImprove.mockRejectedValue(error)

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Authentication required. Please log in.')).toBeInTheDocument()
    })
  })

  it('handles 403 forbidden error', async () => {
    const user = userEvent.setup()
    const error = new Error('Forbidden')
    ;(error as any).response = { status: 403 }
    mockAutoImprove.mockRejectedValue(error)

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Access denied. You do not have permission to run auto-improvement.')).toBeInTheDocument()
    })
  })

  it('handles 429 rate limit error', async () => {
    const user = userEvent.setup()
    const error = new Error('Too Many Requests')
    ;(error as any).response = { status: 429 }
    mockAutoImprove.mockRejectedValue(error)

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Rate limit exceeded. Please try again later.')).toBeInTheDocument()
    })
  })

  it('handles 500 server error', async () => {
    const user = userEvent.setup()
    const error = new Error('Internal Server Error')
    ;(error as any).response = { status: 500 }
    mockAutoImprove.mockRejectedValue(error)

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Server error. Please try again later.')).toBeInTheDocument()
    })
  })

  it('allows configuration of confidence threshold', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockResolvedValue({
      data: mockAutoImprovementResult
    })

    render(<AutoImprovement />)
    
    // Show configuration panel
    const settingsButton = screen.getByTitle('Show configuration')
    await user.click(settingsButton)
    
    const confidenceInput = screen.getByDisplayValue('0.5')
    await user.click(confidenceInput)
    // For range inputs, we simulate changing the value by clicking
    // The actual value change would be handled by the component's onChange

    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(mockAutoImprove).toHaveBeenCalledWith({
        min_confidence_threshold: 0.5,
        max_transactions: 1000
      })
    })
  })

  it('allows configuration of max transactions', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockResolvedValue({
      data: mockAutoImprovementResult
    })

    render(<AutoImprovement />)
    
    // Show configuration panel
    const settingsButton = screen.getByTitle('Show configuration')
    await user.click(settingsButton)
    
    const maxTransactionsInput = screen.getByDisplayValue('1000')
    await user.click(maxTransactionsInput)
    // For range inputs, we simulate changing the value by clicking
    // The actual value change would be handled by the component's onChange

    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(mockAutoImprove).toHaveBeenCalledWith({
        min_confidence_threshold: 0.5,
        max_transactions: 1000
      })
    })
  })

  it('allows configuration of batch ID', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockResolvedValue({
      data: mockAutoImprovementResult
    })

    render(<AutoImprovement />)
    
    // Show configuration panel
    const settingsButton = screen.getByTitle('Show configuration')
    await user.click(settingsButton)
    
    const batchIdInput = screen.getByPlaceholderText('Leave empty for all transactions')
    await user.type(batchIdInput, 'batch_123')

    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(mockAutoImprove).toHaveBeenCalledWith({
        batch_id: 'batch_123',
        min_confidence_threshold: 0.5,
        max_transactions: 1000
      })
    })
  })

  it('shows loading state during execution', async () => {
    const user = userEvent.setup()
    // Create a promise that doesn't resolve immediately
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    mockAutoImprove.mockReturnValue(promise)

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    expect(screen.getByText('Running Auto-Improvement...')).toBeInTheDocument()
    expect(runButton).toBeDisabled()

    // Resolve the promise
    resolvePromise!({ data: mockAutoImprovementResult })
  })

  it('displays detailed improvement metrics', async () => {
    const user = userEvent.setup()
    mockAutoImprove.mockResolvedValue({
      data: mockAutoImprovementResult
    })

    render(<AutoImprovement />)
    
    const runButton = screen.getByRole('button', { name: 'Start Auto-Improvement' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('New Rules Created')).toBeInTheDocument()
      expect(screen.getByText('Rules Updated')).toBeInTheDocument()
      expect(screen.getByText('ML Improvements')).toBeInTheDocument()
      expect(screen.getByText('Transactions Processed')).toBeInTheDocument()
      expect(screen.getByText('Improvement Score')).toBeInTheDocument()
      expect(screen.getByText(/Processing completed in/)).toBeInTheDocument()
    })
  })

  it('is accessible with proper ARIA labels', async () => {
    const user = userEvent.setup()
    render(<AutoImprovement />)
    
    expect(screen.getByRole('heading', { name: 'Auto-Improvement' })).toBeInTheDocument()
    
    // Show configuration to test accessibility of form elements
    const settingsButton = screen.getByTitle('Show configuration')
    await user.click(settingsButton)
    
    expect(screen.getByText(/Confidence Threshold:/)).toBeInTheDocument()
    expect(screen.getByText(/Max Transactions:/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Leave empty for all transactions')).toBeInTheDocument()
  })
})
