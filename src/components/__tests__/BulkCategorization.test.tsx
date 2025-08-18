import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TransactionTable } from '../../../components/TransactionTable';

// Mock the API
jest.mock('../../../lib/api', () => ({
  transactionAPI: {
    getTransactions: jest.fn(),
    getTransactionCount: jest.fn(),
    updateCategory: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock the components
jest.mock('../../../components/TransactionFilters', () => ({
  TransactionFilters: ({ onFiltersChange }: any) => (
    <div data-testid="transaction-filters">
      <button onClick={() => onFiltersChange({ category: 'test' })}>Apply Filter</button>
    </div>
  ),
}));

jest.mock('../../../components/Pagination', () => ({
  Pagination: ({ currentPage, totalPages, onPageChange }: any) => (
    <div data-testid="pagination">
      <span>Page {currentPage} of {totalPages}</span>
      <button onClick={() => onPageChange(currentPage + 1)}>Next</button>
    </div>
  ),
}));

jest.mock('../../../components/ComboBox', () => ({
  ComboBox: ({ value, onChange, placeholder }: any) => (
    <select value={value} onChange={(e) => onChange(e.target.value)} data-testid={placeholder?.toLowerCase().replace(/\s+/g, '-')}>
      <option value="">{placeholder}</option>
      <option value="groceries">Groceries</option>
      <option value="entertainment">Entertainment</option>
    </select>
  ),
}));

jest.mock('../../../hooks/useCategories', () => ({
  useCategoryOptions: () => ({
    categories: ['groceries', 'entertainment', 'transportation'],
    getSubcategories: jest.fn(() => ['food', 'drinks']),
    isLoading: false,
  }),
}));

jest.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: jest.fn(),
  }),
}));

const mockTransactions = [
  {
    id: 1,
    date: '2024-01-01',
    description: 'Grocery Store',
    amount: 50.00,
    vendor: 'Walmart',
    category: 'groceries',
    subcategory: 'food',
    is_income: false,
    is_categorized: true,
    confidence_score: 0.95,
  },
  {
    id: 2,
    date: '2024-01-02',
    description: 'Movie Theater',
    amount: 25.00,
    vendor: 'AMC',
    category: 'entertainment',
    subcategory: 'movies',
    is_income: false,
    is_categorized: true,
    confidence_score: 0.88,
  },
  {
    id: 3,
    date: '2024-01-03',
    description: 'Walmart Purchase',
    amount: 75.00,
    vendor: 'Walmart',
    category: null,
    subcategory: null,
    is_income: false,
    is_categorized: false,
    confidence_score: null,
  },
];

describe('Bulk Categorization Features', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    const { transactionAPI } = require('../../../lib/api');
    transactionAPI.getTransactions.mockResolvedValue({ data: mockTransactions });
    transactionAPI.getTransactionCount.mockResolvedValue({ data: { count: 3 } });
    transactionAPI.updateCategory.mockResolvedValue({ 
      data: { 
        message: 'Success', 
        auto_categorized_count: 0,
        new_rule_created: false 
      } 
    });
  });

  describe('Bulk Selection', () => {
    it('renders bulk selection toolbar', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        expect(screen.getByText('0 selected')).toBeInTheDocument();
        expect(screen.getByLabelText('Select all')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Bulk category')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Bulk subcategory')).toBeInTheDocument();
        expect(screen.getByText('Apply to selected')).toBeInTheDocument();
        expect(screen.getByText('Undo last bulk')).toBeInTheDocument();
      });
    });

    it('selects individual rows', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        const selectButtons = screen.getAllByLabelText('Select row');
        fireEvent.click(selectButtons[0]);
        expect(screen.getByText('1 selected')).toBeInTheDocument();
      });
    });

    it('selects all rows with master checkbox', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        const toolbarCheckbox = masterCheckboxes[0]; // Use the toolbar checkbox
        fireEvent.click(toolbarCheckbox);
        expect(screen.getByText('3 selected')).toBeInTheDocument();
      });
    });

    it('deselects all rows when master checkbox is clicked again', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        const toolbarCheckbox = masterCheckboxes[0]; // Use the toolbar checkbox
        fireEvent.click(toolbarCheckbox);
        expect(screen.getByText('3 selected')).toBeInTheDocument();
        
        fireEvent.click(toolbarCheckbox);
        expect(screen.getByText('0 selected')).toBeInTheDocument();
      });
    });
  });

  describe('Select Similar by Vendor', () => {
    it('selects transactions with same vendor', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Wait for the table to render with scan buttons
        const scanButtons = screen.getAllByLabelText('Select similar by vendor');
        expect(scanButtons.length).toBeGreaterThan(0);
        // Click on the first Walmart transaction
        fireEvent.click(scanButtons[0]);
        expect(screen.getByText('2 selected')).toBeInTheDocument();
      });
    });

    it('handles vendor selection when vendor is null', async () => {
      const transactionsWithNullVendor = [
        { ...mockTransactions[0], vendor: null },
        { ...mockTransactions[1], vendor: null },
      ];
      
      render(<TransactionTable transactions={transactionsWithNullVendor} isLoading={false} />);
      
      await waitFor(() => {
        const scanButtons = screen.getAllByLabelText('Select similar by vendor');
        fireEvent.click(scanButtons[0]);
        // Should not select any additional transactions
        expect(screen.getByText('0 selected')).toBeInTheDocument();
      });
    });
  });

  describe('Bulk Apply Categorization', () => {
    it('applies category to selected transactions', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory.mockResolvedValue({ 
        data: { 
          message: 'Success', 
          auto_categorized_count: 2,
          new_rule_created: true 
        } 
      });

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Select all transactions
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        const toolbarCheckbox = masterCheckboxes[0]; // Use the toolbar checkbox
        fireEvent.click(toolbarCheckbox);
        expect(screen.getByText('3 selected')).toBeInTheDocument();

        // Choose bulk category
        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        // Apply bulk categorization
        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        expect(transactionAPI.updateCategory).toHaveBeenCalledTimes(3);
        expect(screen.getByText(/Applied to 3 transaction\(s\)/)).toBeInTheDocument();
      });
    });

    it('shows error when no transactions are selected', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
        expect(screen.getByText('Please select at least one transaction')).toBeInTheDocument();
      });
    });

    it('shows error when no category is selected', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Select a transaction
        const selectButtons = screen.getAllByLabelText('Select row');
        fireEvent.click(selectButtons[0]);
        
        // Try to apply without category
        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
        expect(screen.getByText('Please choose a category to apply')).toBeInTheDocument();
      });
    });

    it('handles bulk operation failures gracefully', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory
        .mockResolvedValueOnce({ data: { message: 'Success' } })
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce({ data: { message: 'Success' } });

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Select all transactions
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        const toolbarCheckbox = masterCheckboxes[0]; // Use the toolbar checkbox
        fireEvent.click(toolbarCheckbox);

        // Choose bulk category
        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        // Apply bulk categorization
        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Applied to 2 transaction\(s\)\. 1 failed\./)).toBeInTheDocument();
      });
    });
  });

  describe('Undo Last Bulk Operation', () => {
    it('enables undo button after bulk operation', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory.mockResolvedValue({ data: { message: 'Success' } });

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Initially undo should be disabled
        const undoButton = screen.getByText('Undo last bulk');
        expect(undoButton).toBeDisabled();

        // Perform bulk operation
        const masterCheckbox = screen.getByLabelText('Select all');
        fireEvent.click(masterCheckbox);

        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        // After bulk operation, undo should be enabled
        const undoButton = screen.getByText('Undo last bulk');
        expect(undoButton).not.toBeDisabled();
      });
    });

    it('undoes last bulk operation', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory.mockResolvedValue({ data: { message: 'Success' } });

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Perform bulk operation
        const masterCheckbox = screen.getByLabelText('Select all');
        fireEvent.click(masterCheckbox);

        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        // Undo the operation
        const undoButton = screen.getByText('Undo last bulk');
        fireEvent.click(undoButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Undo complete: restored 3 transaction\(s\)/)).toBeInTheDocument();
        // Undo button should be disabled again
        const undoButton = screen.getByText('Undo last bulk');
        expect(undoButton).toBeDisabled();
      });
    });

    it('handles undo operation failures', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory
        .mockResolvedValue({ data: { message: 'Success' } }) // For initial bulk operation
        .mockResolvedValueOnce({ data: { message: 'Success' } }) // For first undo
        .mockRejectedValueOnce(new Error('API Error')) // For second undo
        .mockResolvedValueOnce({ data: { message: 'Success' } }); // For third undo

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Perform bulk operation
        const masterCheckbox = screen.getByLabelText('Select all');
        fireEvent.click(masterCheckbox);

        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        // Undo the operation
        const undoButton = screen.getByText('Undo last bulk');
        fireEvent.click(undoButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Undo complete: restored 2 transaction\(s\)\. 1 failed\./)).toBeInTheDocument();
      });
    });
  });

  describe('Bulk Operations UI States', () => {
    it('shows loading state during bulk operation', async () => {
      const { transactionAPI } = require('../../../lib/api');
      // Mock a delayed response
      transactionAPI.updateCategory.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: { message: 'Success' } }), 100))
      );

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Select transactions and start bulk operation
        const masterCheckbox = screen.getByLabelText('Select all');
        fireEvent.click(masterCheckbox);

        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);

        // Should show loading state
        expect(screen.getByText('Applying...')).toBeInTheDocument();
        expect(screen.getByText('Applying...')).toBeDisabled();
      });
    });

    it('clears selection after successful bulk operation', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory.mockResolvedValue({ data: { message: 'Success' } });

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Select all transactions
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        const toolbarCheckbox = masterCheckboxes[0]; // Use the toolbar checkbox
        fireEvent.click(toolbarCheckbox);
        expect(screen.getByText('3 selected')).toBeInTheDocument();

        // Perform bulk operation
        const bulkCategorySelect = screen.getByTestId('bulk-category');
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });

        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        // Selection should be cleared
        expect(screen.getByText('0 selected')).toBeInTheDocument();
      });
    });

    it('clears bulk category fields after operation', async () => {
      const { transactionAPI } = require('../../../lib/api');
      transactionAPI.updateCategory.mockResolvedValue({ data: { message: 'Success' } });

      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        // Select transactions
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        const toolbarCheckbox = masterCheckboxes[0]; // Use the toolbar checkbox
        fireEvent.click(toolbarCheckbox);

        // Set bulk category and subcategory
        const bulkCategorySelect = screen.getByTestId('bulk-category');
        const bulkSubcategorySelect = screen.getByTestId('bulk-subcategory');
        
        fireEvent.change(bulkCategorySelect, { target: { value: 'groceries' } });
        fireEvent.change(bulkSubcategorySelect, { target: { value: 'food' } });

        // Perform bulk operation
        const applyButton = screen.getByText('Apply to selected');
        fireEvent.click(applyButton);
      });

      await waitFor(() => {
        // Fields should be cleared
        const bulkCategorySelect = screen.getByTestId('bulk-category');
        const bulkSubcategorySelect = screen.getByTestId('bulk-subcategory');
        
        expect(bulkCategorySelect).toHaveValue('');
        expect(bulkSubcategorySelect).toHaveValue('');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for bulk selection', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        const masterCheckboxes = screen.getAllByLabelText('Select all');
        expect(masterCheckboxes.length).toBeGreaterThan(0);
        const selectButtons = screen.getAllByLabelText('Select row');
        expect(selectButtons).toHaveLength(3);
      });
    });

    it('has proper ARIA labels for scan similar button', async () => {
      render(<TransactionTable transactions={mockTransactions} isLoading={false} />);
      
      await waitFor(() => {
        const scanButtons = screen.getAllByLabelText('Select similar by vendor');
        expect(scanButtons.length).toBeGreaterThan(0);
      });
    });
  });
});
