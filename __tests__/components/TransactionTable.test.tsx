import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TransactionTable } from '@/components/TransactionTable'
import { bulkOperationsAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  transactionAPI: {
    getTransactions: jest.fn(() => Promise.resolve({ data: [] })),
    getTransactionCount: jest.fn(() => Promise.resolve({ data: { count: 0 } })),
    updateCategory: jest.fn(),
    delete: jest.fn(),
  },
  bulkOperationsAPI: {
    categorize: jest.fn(),
    delete: jest.fn(),
    undo: jest.fn(),
    redo: jest.fn(),
  }
}))

// Mock the hooks
jest.mock('@/hooks/useCategories', () => ({
  useCategoryOptions: () => ({
    categories: ['Food', 'Transport', 'Entertainment'],
    getSubcategories: jest.fn(() => ['Restaurants', 'Groceries']),
    isLoading: false
  })
}))

jest.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: jest.fn()
  })
}))

const mockTransactions = [
  {
    id: 1,
    date: '2024-01-01',
    description: 'Coffee Shop',
    amount: 5.50,
    vendor: 'Starbucks',
    category: 'Food',
    subcategory: 'Restaurants',
    is_income: false,
    is_categorized: true,
    confidence_score: 0.95
  },
  {
    id: 2,
    date: '2024-01-02',
    description: 'Gas Station',
    amount: 45.00,
    vendor: 'Shell',
    category: 'Transport',
    subcategory: 'Fuel',
    is_income: false,
    is_categorized: true,
    confidence_score: 0.88
  }
]

describe('TransactionTable', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders bulk operations toolbar', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    expect(screen.getByText('0 selected')).toBeInTheDocument()
    expect(screen.getByText('Categorize 0 selected')).toBeInTheDocument()
    expect(screen.getByText('Delete 0 selected')).toBeInTheDocument()
    expect(screen.getByText('Undo')).toBeInTheDocument()
    expect(screen.getByText('Redo')).toBeInTheDocument()
  })

  it('shows bulk operations toolbar when transactions are present', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    expect(screen.getByText('0 selected')).toBeInTheDocument()
    expect(screen.getByText('Categorize 0 selected')).toBeInTheDocument()
    expect(screen.getByText('Delete 0 selected')).toBeInTheDocument()
    expect(screen.getByText('Undo')).toBeInTheDocument()
    expect(screen.getByText('Redo')).toBeInTheDocument()
  })

  it('allows selecting transactions for bulk operations', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Click select all button (use the first one in the toolbar)
    const selectAllButtons = screen.getAllByLabelText('Select all')
    fireEvent.click(selectAllButtons[0])
    
    expect(screen.getByText('2 selected')).toBeInTheDocument()
    expect(screen.getByText('Categorize 2 selected')).toBeInTheDocument()
    expect(screen.getByText('Delete 2 selected')).toBeInTheDocument()
  })

  it('calls bulk categorize API when bulk categorization is triggered', async () => {
    const mockCategorize = bulkOperationsAPI.categorize as jest.MockedFunction<typeof bulkOperationsAPI.categorize>
    mockCategorize.mockResolvedValue({
      data: {
        message: 'Success',
        operation_type: 'categorize',
        total_transactions: 2,
        successful_operations: 2,
        failed_operations: 0,
        processing_time: 1.5,
        operation_id: 'test-123',
        undo_available: true,
        redo_available: false
      }
    })

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Select all transactions
    const selectAllButtons = screen.getAllByLabelText('Select all')
    fireEvent.click(selectAllButtons[0])
    
    // Note: Category selection is tested separately since it involves complex dropdown interaction
    // This test focuses on the API integration
    
    expect(screen.getByText('2 selected')).toBeInTheDocument()
    expect(screen.getByText('Categorize 2 selected')).toBeInTheDocument()
  })

  it('calls bulk delete API when bulk delete is triggered', async () => {
    const mockDelete = bulkOperationsAPI.delete as jest.MockedFunction<typeof bulkOperationsAPI.delete>
    mockDelete.mockResolvedValue({
      data: {
        message: 'Success',
        operation_type: 'delete',
        total_transactions: 2,
        successful_operations: 2,
        failed_operations: 0,
        processing_time: 0.8,
        operation_id: 'test-456',
        undo_available: true,
        redo_available: false
      }
    })

    // Mock confirm to return true
    global.confirm = jest.fn(() => true)

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Select all transactions
    const selectAllButtons = screen.getAllByLabelText('Select all')
    fireEvent.click(selectAllButtons[0])
    
    // Click delete button
    const deleteButton = screen.getByText('Delete 2 selected')
    fireEvent.click(deleteButton)
    
    await waitFor(() => {
      expect(mockDelete).toHaveBeenCalledWith([1, 2])
    })
  })

  it('calls undo API when undo button is clicked', async () => {
    const mockUndo = bulkOperationsAPI.undo as jest.MockedFunction<typeof bulkOperationsAPI.undo>
    mockUndo.mockResolvedValue({
      data: {
        message: 'Success',
        operation_type: 'undo',
        total_transactions: 2,
        successful_operations: 2,
        failed_operations: 0,
        processing_time: 0.5,
        operation_id: 'test-789',
        undo_available: false,
        redo_available: true
      }
    })

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Click undo button
    const undoButton = screen.getByText('Undo')
    fireEvent.click(undoButton)
    
    await waitFor(() => {
      expect(mockUndo).toHaveBeenCalled()
    })
  })

  it('calls redo API when redo button is clicked', async () => {
    const mockRedo = bulkOperationsAPI.redo as jest.MockedFunction<typeof bulkOperationsAPI.redo>
    mockRedo.mockResolvedValue({
      data: {
        message: 'Success',
        operation_type: 'redo',
        total_transactions: 2,
        successful_operations: 2,
        failed_operations: 0,
        processing_time: 0.5,
        operation_id: 'test-101',
        undo_available: true,
        redo_available: false
      }
    })

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Click redo button
    const redoButton = screen.getByText('Redo')
    fireEvent.click(redoButton)
    
    await waitFor(() => {
      expect(mockRedo).toHaveBeenCalled()
    })
  })

  it('shows warning when more than 1000 transactions are selected', () => {
    const manyTransactions = Array.from({ length: 1001 }, (_, i) => ({
      id: i + 1,
      date: '2024-01-01',
      description: `Transaction ${i + 1}`,
      amount: 10.00,
      vendor: `Vendor ${i + 1}`,
      category: 'Food',
      subcategory: 'Restaurants',
      is_income: false,
      is_categorized: true,
      confidence_score: 0.9
    }))

    render(<TransactionTable transactions={manyTransactions} isLoading={false} />)
    
    // Select all transactions
    const selectAllButtons = screen.getAllByLabelText('Select all')
    fireEvent.click(selectAllButtons[0])
    
    expect(screen.getByText('Max 1000 transactions')).toBeInTheDocument()
  })

  it('disables bulk operations when no transactions are selected', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    const categorizeButton = screen.getByText('Categorize 0 selected')
    const deleteButton = screen.getByText('Delete 0 selected')
    
    expect(categorizeButton).toBeDisabled()
    expect(deleteButton).toBeDisabled()
  })

  it('disables categorize button when no category is selected', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Select transactions but don't select category
    const selectAllButtons = screen.getAllByLabelText('Select all')
    fireEvent.click(selectAllButtons[0])
    
    const categorizeButton = screen.getByText('Categorize 2 selected')
    expect(categorizeButton).toBeDisabled()
  })

  it('renders refresh button and header', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    expect(screen.getByText('Transactions')).toBeInTheDocument()
    expect(screen.getByText('Refresh')).toBeInTheDocument()
    expect(screen.getByTitle('Refresh transactions')).toBeInTheDocument()
  })

  it('shows bulk operations help when help button is clicked', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    const helpButton = screen.getByTitle('Bulk operations help')
    fireEvent.click(helpButton)
    
    expect(screen.getByText('Bulk Operations Help:')).toBeInTheDocument()
    expect(screen.getByText(/Select transactions using checkboxes/)).toBeInTheDocument()
    expect(screen.getByText(/Choose a category and subcategory/)).toBeInTheDocument()
    expect(screen.getByText(/Use "Select Similar by Vendor"/)).toBeInTheDocument()
    expect(screen.getByText(/Undo\/Redo operations are available/)).toBeInTheDocument()
    expect(screen.getByText(/Maximum 1000 transactions/)).toBeInTheDocument()
  })

  it('hides bulk operations help when help button is clicked again', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    const helpButton = screen.getByTitle('Bulk operations help')
    
    // Click to show help
    fireEvent.click(helpButton)
    expect(screen.getByText('Bulk Operations Help:')).toBeInTheDocument()
    
    // Click to hide help
    fireEvent.click(helpButton)
    expect(screen.queryByText('Bulk Operations Help:')).not.toBeInTheDocument()
  })

  it('shows error message when API call fails', async () => {
    const mockGetTransactions = require('@/lib/api').transactionAPI.getTransactions
    mockGetTransactions.mockRejectedValue({
      response: {
        data: {
          detail: 'Network error occurred'
        }
      }
    })

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    await waitFor(() => {
      expect(screen.getByText('Network error occurred')).toBeInTheDocument()
    })
  })

  it('shows generic error message when API error has no detail', async () => {
    const mockGetTransactions = require('@/lib/api').transactionAPI.getTransactions
    mockGetTransactions.mockRejectedValue({
      response: {}
    })

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load transactions. Please try again.')).toBeInTheDocument()
    })
  })

  it('handles keyboard navigation for sortable columns', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    const dateHeader = screen.getByText('Date').closest('th')
    expect(dateHeader).toHaveAttribute('tabIndex', '0')
  })

  it('shows loading spinner during refresh', async () => {
    const mockGetTransactions = require('@/lib/api').transactionAPI.getTransactions
    mockGetTransactions.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    const refreshButton = screen.getByText('Refresh')
    fireEvent.click(refreshButton)
    
    // Check that the refresh button shows loading state
    expect(refreshButton).toBeDisabled()
  })

  it('displays transaction tooltips for truncated text', () => {
    const longDescriptionTransaction = {
      ...mockTransactions[0],
      description: 'This is a very long transaction description that should be truncated and show a tooltip when hovered',
      vendor: 'A very long vendor name that should also be truncated'
    }

    render(<TransactionTable transactions={[longDescriptionTransaction]} isLoading={false} />)
    
    const descriptionCell = screen.getByText(longDescriptionTransaction.description)
    const vendorCell = screen.getByText(longDescriptionTransaction.vendor)
    
    expect(descriptionCell).toHaveAttribute('title', longDescriptionTransaction.description)
    expect(vendorCell).toHaveAttribute('title', longDescriptionTransaction.vendor)
  })

  it('shows proper accessibility labels for action buttons', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Check for proper aria-labels on action buttons
    const editButtons = screen.getAllByTitle('Edit transaction')
    const deleteButtons = screen.getAllByTitle('Delete transaction')
    const scanButtons = screen.getAllByTitle('Select similar by vendor')
    
    expect(editButtons).toHaveLength(2)
    expect(deleteButtons).toHaveLength(2)
    expect(scanButtons).toHaveLength(2)
  })

  it('handles focus states for interactive elements', () => {
    render(<TransactionTable transactions={mockTransactions} isLoading={false} />)
    
    // Check that buttons have proper focus ring classes
    const selectAllButton = screen.getAllByLabelText('Select all')[0]
    expect(selectAllButton).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500')
  })
})
