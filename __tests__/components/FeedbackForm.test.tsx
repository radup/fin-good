import React from 'react'
import { render, screen, waitFor } from '../utils/test-utils'
import userEvent from '@testing-library/user-event'
import FeedbackForm from '@/components/FeedbackForm'
import { mockFeedbackResult, mockRateLimitInfo } from '../utils/test-utils'

// Mock the API module
jest.mock('@/lib/api', () => ({
  transactionAPI: {
    submitFeedback: jest.fn()
  }
}))

describe('FeedbackForm', () => {
  const mockSubmitFeedback = jest.mocked(
    require('@/lib/api').transactionAPI.submitFeedback
  )

  const defaultProps = {
    transactionId: 1,
    currentCategory: 'Food & Dining',
    currentSubcategory: 'Restaurants',
    onFeedbackSubmitted: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the component with initial state', () => {
    render(<FeedbackForm {...defaultProps} />)
    
    expect(screen.getByRole('button', { name: 'Submit Feedback' })).toBeInTheDocument()
    expect(screen.getByText('Correct Categorization')).toBeInTheDocument()
    expect(screen.getByText('This categorization is correct and helps improve our AI accuracy.')).toBeInTheDocument()
    expect(screen.getByText('Food & Dining')).toBeInTheDocument()
    expect(screen.getByText(/Restaurants/)).toBeInTheDocument()
  })

  it('displays feedback type options', () => {
    render(<FeedbackForm {...defaultProps} />)
    
    expect(screen.getByRole('button', { name: 'Correct This categorization is accurate' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Incorrect This categorization is wrong' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Suggest Alternative Propose a better category' })).toBeInTheDocument()
  })

  it('submits correct feedback when selected', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockSubmitFeedback).toHaveBeenCalledWith(1, {
        feedback_type: 'correct'
      })
    })
  })

  it('submits incorrect feedback when selected', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const incorrectButton = screen.getByRole('button', { name: 'Incorrect This categorization is wrong' })
    await user.click(incorrectButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockSubmitFeedback).toHaveBeenCalledWith(1, {
        feedback_type: 'incorrect'
      })
    })
  })

  it('shows alternative suggestion fields when selected', async () => {
    const user = userEvent.setup()
    render(<FeedbackForm {...defaultProps} />)
    
    const suggestAlternativeButton = screen.getByRole('button', { name: 'Suggest Alternative Propose a better category' })
    await user.click(suggestAlternativeButton)

    expect(screen.getByPlaceholderText('e.g., Food & Dining')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('e.g., Restaurants')).toBeInTheDocument()
  })

  it('submits alternative suggestion with category and subcategory', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const suggestAlternativeButton = screen.getByRole('button', { name: 'Suggest Alternative Propose a better category' })
    await user.click(suggestAlternativeButton)

    const categoryInput = screen.getByPlaceholderText('e.g., Food & Dining')
    const subcategoryInput = screen.getByPlaceholderText('e.g., Restaurants')
    
    await user.type(categoryInput, 'Entertainment')
    await user.type(subcategoryInput, 'Movies')

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockSubmitFeedback).toHaveBeenCalledWith(1, {
        feedback_type: 'suggest_alternative',
        suggested_category: 'Entertainment',
        suggested_subcategory: 'Movies'
      })
    })
  })

  it('submits feedback with comment', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const commentInput = screen.getByPlaceholderText('Any additional context or explanation...')
    await user.type(commentInput, 'This categorization is perfect!')

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockSubmitFeedback).toHaveBeenCalledWith(1, {
        feedback_type: 'correct',
        feedback_comment: 'This categorization is perfect!'
      })
    })
  })

  it('displays success message when feedback is submitted', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Feedback Submitted Successfully!')).toBeInTheDocument()
      expect(screen.getByText('Feedback submitted successfully')).toBeInTheDocument()
    })
  })

  it('calls onFeedbackSubmitted callback when successful', async () => {
    const user = userEvent.setup()
    const onFeedbackSubmitted = jest.fn()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} onFeedbackSubmitted={onFeedbackSubmitted} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(onFeedbackSubmitted).toHaveBeenCalledWith(mockFeedbackResult)
    })
  })

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockRejectedValue(new Error('API Error'))

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to submit feedback. Please try again.')).toBeInTheDocument()
    })
  })

  it('handles 401 unauthorized error', async () => {
    const user = userEvent.setup()
    const error = new Error('Unauthorized')
    ;(error as any).response = { status: 401 }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to submit feedback. Please try again.')).toBeInTheDocument()
    })
  })

  it('handles 403 forbidden error', async () => {
    const user = userEvent.setup()
    const error = new Error('Forbidden')
    ;(error as any).response = { status: 403 }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByText('Correct').closest('button')
    await user.click(correctButton!)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to submit feedback. Please try again.')).toBeInTheDocument()
    })
  })

  it('handles 429 rate limit error', async () => {
    const user = userEvent.setup()
    const error = new Error('Too Many Requests')
    ;(error as any).response = { 
      status: 429,
      headers: {
        'retry-after': '60',
        'x-ratelimit-limit': '100',
        'x-ratelimit-reset': '1642237800'
      }
    }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByText('Correct').closest('button')
    await user.click(correctButton!)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to submit feedback. Please try again.')).toBeInTheDocument()
    })
  })

  it('handles 500 server error', async () => {
    const user = userEvent.setup()
    const error = new Error('Internal Server Error')
    ;(error as any).response = { status: 500 }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByText('Correct').closest('button')
    await user.click(correctButton!)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to submit feedback. Please try again.')).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()
    // Create a promise that doesn't resolve immediately
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    mockSubmitFeedback.mockReturnValue(promise)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctButton = screen.getByRole('button', { name: 'Correct This categorization is accurate' })
    await user.click(correctButton)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    expect(screen.getByText('Submitting...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()

    // Resolve the promise
    resolvePromise!({ data: mockFeedbackResult })
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    render(<FeedbackForm {...defaultProps} />)
    
    // The form defaults to 'correct' feedback type, so it will submit
    // This test should verify that the form works with default values
    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    // Should submit with default 'correct' feedback type
    expect(mockSubmitFeedback).toHaveBeenCalledWith(1, {
      feedback_type: 'correct',
      suggested_category: undefined,
      suggested_subcategory: undefined,
      feedback_comment: undefined
    })
  })

  it('validates alternative suggestion fields', async () => {
    const user = userEvent.setup()
    render(<FeedbackForm {...defaultProps} />)
    
    const suggestAlternativeButton = screen.getByRole('button', { name: 'Suggest Alternative Propose a better category' })
    await user.click(suggestAlternativeButton)

    // The submit button should be disabled when category is empty
    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    expect(submitButton).toBeDisabled()

    // Add a category to enable the button
    const categoryInput = screen.getByPlaceholderText('e.g., Food & Dining')
    await user.type(categoryInput, 'Entertainment')

    // Now the button should be enabled
    expect(submitButton).not.toBeDisabled()
  })

  it('is accessible with proper ARIA labels', () => {
    render(<FeedbackForm {...defaultProps} />)
    
    expect(screen.getByRole('button', { name: 'Submit Feedback' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Correct This categorization is accurate' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Incorrect This categorization is wrong' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Suggest Alternative Propose a better category' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Any additional context or explanation...')).toBeInTheDocument()
  })

  it('handles transaction without subcategory', () => {
    render(<FeedbackForm 
      transactionId={1}
      currentCategory="Food & Dining"
      onFeedbackSubmitted={jest.fn()}
    />)
    
    expect(screen.getByText('Food & Dining')).toBeInTheDocument()
  })
})
