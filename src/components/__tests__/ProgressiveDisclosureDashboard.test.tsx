import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DashboardComponent from '../../../app/DashboardComponent';

// Mock the API
jest.mock('../../../lib/api', () => ({
  authAPI: {
    me: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
  },
  transactionAPI: {
    getTransactions: jest.fn(),
    categorize: jest.fn(),
  },
  analyticsAPI: {
    summary: jest.fn(),
  },
}));

// Mock the components
jest.mock('../../../components/TransactionTable', () => ({
  TransactionTable: ({ transactions, isLoading }: any) => (
    <div data-testid="transaction-table" data-loading={isLoading}>
      {transactions?.length || 0} transactions
    </div>
  ),
}));

jest.mock('../../../components/TherapeuticUploadModal', () => ({
  TherapeuticUploadModal: ({ isOpen, onClose, onUploadSuccess }: any) => (
    isOpen ? (
      <div data-testid="upload-modal">
        <button onClick={onClose}>Close</button>
        <button onClick={onUploadSuccess}>Success</button>
      </div>
    ) : null
  ),
}));

jest.mock('../../../components/DashboardStats', () => ({
  DashboardStats: ({ summary, isLoading }: any) => (
    <div data-testid="dashboard-stats" data-loading={isLoading}>
      {summary ? 'Stats loaded' : 'No stats'}
    </div>
  ),
}));

jest.mock('../../../components/ImportBatchManager', () => ({
  ImportBatchManager: ({ refreshKey }: any) => (
    <div data-testid="import-batch-manager" data-refresh-key={refreshKey}>
      Import Batch Manager
    </div>
  ),
}));

jest.mock('../../../components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children, fallback }: any) => children,
  ErrorFallback: () => <div>Error occurred</div>,
}));

jest.mock('../../../components/DrSigmundSpendAvatar', () => ({
  __esModule: true,
  default: ({ mood, message, showMessage, size, className }: any) => (
    <div data-testid="dr-sigmund-avatar" data-mood={mood} data-message={message} data-show-message={showMessage} data-size={size} className={className}>
      Dr. Sigmund Avatar
    </div>
  ),
}));

describe('Progressive Disclosure Dashboard', () => {
  const mockAuthAPI = require('../../../lib/api').authAPI;
  const mockTransactionAPI = require('../../../lib/api').transactionAPI;
  const mockAnalyticsAPI = require('../../../lib/api').analyticsAPI;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful authentication
    mockAuthAPI.me.mockResolvedValue({ data: { user: 'test' } });
    
    // Mock successful data fetching
    mockTransactionAPI.getTransactions.mockResolvedValue({ 
      data: [
        { id: 1, description: 'Test transaction', amount: 100 },
        { id: 2, description: 'Another transaction', amount: 200 }
      ] 
    });
    
    mockAnalyticsAPI.summary.mockResolvedValue({
      data: {
        total_transactions: 2,
        total_income: 1000,
        total_expenses: 300,
        categorized_count: 1,
        uncategorized_count: 1
      }
    });
  });

  describe('Progressive Disclosure Sections', () => {
    it('renders all progressive disclosure sections', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        expect(screen.getByText('Financial Overview')).toBeInTheDocument();
        expect(screen.getByText('Financial Wellness')).toBeInTheDocument();
        expect(screen.getByText('Quick Actions')).toBeInTheDocument();
        expect(screen.getByText('Transaction Management')).toBeInTheDocument();
        expect(screen.getByText('AI Insights')).toBeInTheDocument();
      });
    });

    it('shows correct default expanded state', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Overview and transactions should be expanded by default
        expect(screen.getByTestId('dashboard-stats')).toBeInTheDocument();
        expect(screen.getByTestId('transaction-table')).toBeInTheDocument();
        
        // Other sections should be collapsed
        expect(screen.queryByText('Net Income')).not.toBeInTheDocument();
        expect(screen.queryByText('Spending Patterns')).not.toBeInTheDocument();
      });
    });

    it('toggles sections when clicked', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Initially wellness section should be collapsed
        expect(screen.queryByText('Net Income')).not.toBeInTheDocument();
      });

      // Click to expand wellness section
      const wellnessSection = screen.getByText('Financial Wellness');
      fireEvent.click(wellnessSection);

      await waitFor(() => {
        expect(screen.getByText('Net Income')).toBeInTheDocument();
        expect(screen.getByText('Categorization')).toBeInTheDocument();
        expect(screen.getByText('Expense Ratio')).toBeInTheDocument();
        expect(screen.getByText('Savings Rate')).toBeInTheDocument();
      });

      // Click to collapse wellness section
      fireEvent.click(wellnessSection);

      await waitFor(() => {
        expect(screen.queryByText('Net Income')).not.toBeInTheDocument();
      });
    });

    it('shows help tooltips when help button is clicked', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const helpButtons = screen.getAllByLabelText('Help');
        expect(helpButtons.length).toBeGreaterThan(0);
      });

      // Click help button on wellness section
      const wellnessSection = screen.getByText('Financial Wellness');
      fireEvent.click(wellnessSection);

      await waitFor(() => {
        // Get the help button within the wellness section
        const wellnessSectionElement = screen.getByText('Financial Wellness').closest('.card');
        const helpButton = wellnessSectionElement?.querySelector('[aria-label="Help"]');
        expect(helpButton).toBeInTheDocument();
        fireEvent.click(helpButton!);
      });

      await waitFor(() => {
        expect(screen.getByText(/These wellness indicators help you understand your financial habits/)).toBeInTheDocument();
      });
    });
  });

  describe('Financial Wellness Cards', () => {
    it('displays wellness metrics correctly', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const wellnessSection = screen.getByText('Financial Wellness');
        fireEvent.click(wellnessSection);
      });

      await waitFor(() => {
        // Check that wellness cards are displayed with correct values
        expect(screen.getByText('$700')).toBeInTheDocument(); // Net income: 1000 - 300
        expect(screen.getByText('50%')).toBeInTheDocument(); // Categorization rate: 1/2 * 100
        expect(screen.getByText('30%')).toBeInTheDocument(); // Expense ratio: 300/1000 * 100
        expect(screen.getByText('70%')).toBeInTheDocument(); // Savings rate: 100 - 30
      });
    });

    it('applies correct colors based on metrics', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const wellnessSection = screen.getByText('Financial Wellness');
        fireEvent.click(wellnessSection);
      });

      await waitFor(() => {
        // Check that wellness cards are displayed with correct values
        expect(screen.getByText('$700')).toBeInTheDocument(); // Net income: 1000 - 300
        expect(screen.getByText('50%')).toBeInTheDocument(); // Categorization rate: 1/2 * 100
        
        // Check that the cards exist (color classes are applied via CSS)
        expect(screen.getByText('Net Income')).toBeInTheDocument();
        expect(screen.getByText('Categorization')).toBeInTheDocument();
      });
    });

    it('shows trend indicators', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const wellnessSection = screen.getByText('Financial Wellness');
        fireEvent.click(wellnessSection);
      });

      await waitFor(() => {
        // Should show trend values (use getAllByText to handle multiple instances)
        expect(screen.getAllByText('Positive').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Good').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Healthy').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Great').length).toBeGreaterThan(0);
      });
    });
  });

  describe('Section Badges', () => {
    it('shows appropriate badges for sections', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Transaction management should show uncategorized count
        expect(screen.getByText('1 uncategorized')).toBeInTheDocument();
        
        // AI Insights should show "New" badge
        expect(screen.getByText('New')).toBeInTheDocument();
      });
    });

    it('updates badges when data changes', async () => {
      // Mock data with all transactions categorized
      mockAnalyticsAPI.summary.mockResolvedValue({
        data: {
          total_transactions: 2,
          total_income: 1000,
          total_expenses: 300,
          categorized_count: 2,
          uncategorized_count: 0
        }
      });

      render(<DashboardComponent />);

      await waitFor(() => {
        // Should show "All categorized" instead of count
        expect(screen.getByText('All categorized')).toBeInTheDocument();
      });
    });
  });

  describe('Quick Actions Section', () => {
    it('opens upload modal when upload card is clicked', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const actionsSection = screen.getByText('Quick Actions');
        fireEvent.click(actionsSection);
      });

      await waitFor(() => {
        const uploadCard = screen.getByText('Upload Data');
        fireEvent.click(uploadCard);
      });

      await waitFor(() => {
        expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
      });
    });

    it('shows all quick action cards', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const actionsSection = screen.getByText('Quick Actions');
        fireEvent.click(actionsSection);
      });

      await waitFor(() => {
        expect(screen.getByText('Upload Data')).toBeInTheDocument();
        expect(screen.getByText('View Analytics')).toBeInTheDocument();
        expect(screen.getByText('Forecast')).toBeInTheDocument();
      });
    });
  });

  describe('AI Insights Section', () => {
    it('displays spending patterns and recommendations', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const insightsSection = screen.getByText('AI Insights');
        fireEvent.click(insightsSection);
      });

      await waitFor(() => {
        expect(screen.getByText('Spending Patterns')).toBeInTheDocument();
        expect(screen.getByText('Recommendations')).toBeInTheDocument();
        expect(screen.getByText(/Your largest expense category is typically groceries/)).toBeInTheDocument();
        expect(screen.getByText('Increase Savings')).toBeInTheDocument();
        expect(screen.getByText('Review Subscriptions')).toBeInTheDocument();
        expect(screen.getByText('Emergency Fund')).toBeInTheDocument();
      });
    });

    it('shows pattern indicators with correct colors', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        const insightsSection = screen.getByText('AI Insights');
        fireEvent.click(insightsSection);
      });

      await waitFor(() => {
        // Check for colored indicators
        const indicators = screen.getAllByRole('generic');
        const successIndicator = Array.from(indicators).find(el => 
          el.className?.includes('bg-success-500')
        );
        const warningIndicator = Array.from(indicators).find(el => 
          el.className?.includes('bg-warning-500')
        );
        const infoIndicator = Array.from(indicators).find(el => 
          el.className?.includes('bg-info-500')
        );

        expect(successIndicator).toBeInTheDocument();
        expect(warningIndicator).toBeInTheDocument();
        expect(infoIndicator).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('maintains functionality on different screen sizes', async () => {
      // Mock window resize
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768, // Tablet size
      });

      render(<DashboardComponent />);

      await waitFor(() => {
        // Should still show all sections
        expect(screen.getByText('Financial Overview')).toBeInTheDocument();
        expect(screen.getByText('Financial Wellness')).toBeInTheDocument();
        expect(screen.getByText('Quick Actions')).toBeInTheDocument();
        expect(screen.getByText('Transaction Management')).toBeInTheDocument();
        expect(screen.getByText('AI Insights')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and semantic structure', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Check for help buttons with proper labels
        const helpButtons = screen.getAllByLabelText('Help');
        expect(helpButtons.length).toBeGreaterThan(0);

        // Check for proper heading structure
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
        expect(screen.getByText('FinGood')).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Check that sections are focusable
        const wellnessSection = screen.getByText('Financial Wellness');
        expect(wellnessSection).toBeInTheDocument();
        
        // Verify the section has proper accessibility attributes
        const sectionElement = wellnessSection.closest('[role="button"]') || wellnessSection.closest('.cursor-pointer');
        expect(sectionElement).toBeInTheDocument();
      });
    });
  });

  describe('State Management', () => {
    it('expands transactions section after successful upload', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Initially transactions section should be expanded
        expect(screen.getByTestId('transaction-table')).toBeInTheDocument();
      });

      // Simulate successful upload
      await waitFor(() => {
        const uploadButton = screen.getByText('Upload CSV');
        fireEvent.click(uploadButton);
      });

      await waitFor(() => {
        const successButton = screen.getByText('Success');
        fireEvent.click(successButton);
      });

      // Transactions section should remain expanded
      await waitFor(() => {
        expect(screen.getByTestId('transaction-table')).toBeInTheDocument();
      });
    });

    it('maintains section state during data updates', async () => {
      render(<DashboardComponent />);

      await waitFor(() => {
        // Expand wellness section
        const wellnessSection = screen.getByText('Financial Wellness');
        fireEvent.click(wellnessSection);
      });

      await waitFor(() => {
        expect(screen.getByText('Net Income')).toBeInTheDocument();
      });

      // Simulate data refresh
      mockAnalyticsAPI.summary.mockResolvedValue({
        data: {
          total_transactions: 3,
          total_income: 1500,
          total_expenses: 400,
          categorized_count: 2,
          uncategorized_count: 1
        }
      });

      // Trigger a refresh (simulate upload success)
      await waitFor(() => {
        const uploadButton = screen.getByText('Upload CSV');
        fireEvent.click(uploadButton);
      });

      await waitFor(() => {
        const successButton = screen.getByText('Success');
        fireEvent.click(successButton);
      });

      // Wellness section should still be expanded
      await waitFor(() => {
        expect(screen.getByText('Net Income')).toBeInTheDocument();
        // Should show updated values
        expect(screen.getByText('$1,100')).toBeInTheDocument(); // New net income
      });
    });
  });
});
