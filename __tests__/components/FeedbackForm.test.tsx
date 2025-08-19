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
    
    expect(screen.getByText('Submit Feedback')).toBeInTheDocument()
    expect(screen.getByText('Help improve categorization accuracy')).toBeInTheDocument()
    expect(screen.getByText('Current: Food & Dining > Restaurants')).toBeInTheDocument()
  })

  it('displays feedback type options', () => {
    render(<FeedbackForm {...defaultProps} />)
    
    expect(screen.getByLabelText('Correct')).toBeInTheDocument()
    expect(screen.getByLabelText('Incorrect')).toBeInTheDocument()
    expect(screen.getByLabelText('Suggest Alternative')).toBeInTheDocument()
  })

  it('submits correct feedback when selected', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

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
    
    const incorrectRadio = screen.getByLabelText('Incorrect')
    await user.click(incorrectRadio)

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
    
    const suggestAlternativeRadio = screen.getByLabelText('Suggest Alternative')
    await user.click(suggestAlternativeRadio)

    expect(screen.getByLabelText('Suggested Category')).toBeInTheDocument()
    expect(screen.getByLabelText('Suggested Subcategory')).toBeInTheDocument()
  })

  it('submits alternative suggestion with category and subcategory', async () => {
    const user = userEvent.setup()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} />)
    
    const suggestAlternativeRadio = screen.getByLabelText('Suggest Alternative')
    await user.click(suggestAlternativeRadio)

    const categoryInput = screen.getByLabelText('Suggested Category')
    const subcategoryInput = screen.getByLabelText('Suggested Subcategory')
    
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
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const commentInput = screen.getByLabelText('Comment (Optional)')
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
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Feedback submitted successfully')).toBeInTheDocument()
      expect(screen.getByText('This feedback will improve future categorizations')).toBeInTheDocument()
    })
  })

  it('calls onFeedbackSubmitted callback when successful', async () => {
    const user = userEvent.setup()
    const onFeedbackSubmitted = jest.fn()
    mockSubmitFeedback.mockResolvedValue({
      data: mockFeedbackResult
    })

    render(<FeedbackForm {...defaultProps} onFeedbackSubmitted={onFeedbackSubmitted} />)
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

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
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Error submitting feedback/)).toBeInTheDocument()
    })
  })

  it('handles 401 unauthorized error', async () => {
    const user = userEvent.setup()
    const error = new Error('Unauthorized')
    ;(error as any).response = { status: 401 }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Please log in to submit feedback/)).toBeInTheDocument()
    })
  })

  it('handles 403 forbidden error', async () => {
    const user = userEvent.setup()
    const error = new Error('Forbidden')
    ;(error as any).response = { status: 403 }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/You don't have permission to submit feedback/)).toBeInTheDocument()
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
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Too many requests. Please try again later/)).toBeInTheDocument()
    })
  })

  it('handles 500 server error', async () => {
    const user = userEvent.setup()
    const error = new Error('Internal Server Error')
    ;(error as any).response = { status: 500 }
    mockSubmitFeedback.mockRejectedValue(error)

    render(<FeedbackForm {...defaultProps} />)
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Server error. Please try again later/)).toBeInTheDocument()
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
    
    const correctRadio = screen.getByLabelText('Correct')
    await user.click(correctRadio)

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
    
    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    // Should not submit without selecting a feedback type
    expect(mockSubmitFeedback).not.toHaveBeenCalled()
  })

  it('validates alternative suggestion fields', async () => {
    const user = userEvent.setup()
    render(<FeedbackForm {...defaultProps} />)
    
    const suggestAlternativeRadio = screen.getByLabelText('Suggest Alternative')
    await user.click(suggestAlternativeRadio)

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' })
    await user.click(submitButton)

    // Should show validation error for missing category
    expect(screen.getByText(/Please provide a suggested category/)).toBeInTheDocument()
  })

  it('is accessible with proper ARIA labels', () => {
    render(<FeedbackForm {...defaultProps} />)
    
    expect(screen.getByRole('heading', { name: 'Submit Feedback' })).toBeInTheDocument()
    expect(screen.getByLabelText('Correct')).toBeInTheDocument()
    expect(screen.getByLabelText('Incorrect')).toBeInTheDocument()
    expect(screen.getByLabelText('Suggest Alternative')).toBeInTheDocument()
    expect(screen.getByLabelText('Comment (Optional)')).toBeInTheDocument()
  })

  it('handles transaction without subcategory', () => {
    render(<FeedbackForm 
      transactionId={1}
      currentCategory="Food & Dining"
      onFeedbackSubmitted={jest.fn()}
    />)
    
    expect(screen.getByText('Current: Food & Dining')).toBeInTheDocument()
  })
})
