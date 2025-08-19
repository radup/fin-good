import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BudgetAnalysis } from '@/components/BudgetAnalysis'
import { budgetAnalysisAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  budgetAnalysisAPI: {
    getBudgets: jest.fn(),
    getSummary: jest.fn(),
    getBudget: jest.fn(),
    getVarianceAnalysis: jest.fn(),
    getRecommendations: jest.fn(),
    applyRecommendation: jest.fn(),
  },
}))

const mockBudgetAnalysisAPI = budgetAnalysisAPI as jest.Mocked<typeof budgetAnalysisAPI>

// Mock data
const mockBudgets = {
  budgets: [
    {
      budget_id: 'budget-1',
      name: 'Monthly Budget',
      description: 'Monthly budget for Q1',
      period_type: 'monthly',
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      total_budget: 5000,
      currency: 'USD',
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: 'user-1',
    },
    {
      budget_id: 'budget-2',
      name: 'Quarterly Budget',
      description: 'Quarterly budget for Q1',
      period_type: 'quarterly',
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      total_budget: 15000,
      currency: 'USD',
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: 'user-1',
    },
  ],
  total_count: 2,
  page: 1,
  page_size: 10,
}

const mockSummary = {
  total_budgets: 2,
  active_budgets: 2,
  average_variance: -5.2,
  critical_alerts: 1,
  pending_recommendations: 3,
  overall_performance: {
    accuracy_score: 0.85,
    adherence_rate: 0.78,
    forecast_accuracy: 0.82,
  },
  top_performing_categories: [
    {
      category: 'Food',
      accuracy_score: 0.92,
      adherence_rate: 0.88,
    },
  ],
  areas_needing_attention: [
    {
      category: 'Transport',
      variance_percentage: 15.5,
      alert_count: 2,
      recommendation_count: 1,
    },
  ],
  recent_trends: {
    variance_trend: 'improving',
    alert_frequency: 'decreasing',
    recommendation_effectiveness: 0.75,
  },
}

const mockBudgetDetails = {
  budget: {
    budget_id: 'budget-1',
    name: 'Monthly Budget',
    description: 'Monthly budget for Q1',
    period_type: 'monthly',
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    total_budget: 5000,
    currency: 'USD',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    created_by: 'user-1',
  },
  variance_analysis: {
    budget_id: 'budget-1',
    period_start: '2024-01-01',
    period_end: '2024-01-31',
    total_budget: 5000,
    total_actual: 4750,
    total_variance: -250,
    variance_percentage: -5.0,
    overall_status: 'under_budget',
    category_breakdown: [
      {
        budget_id: 'budget-1',
        category: 'Food',
        subcategory: 'Groceries',
        allocated_amount: 1000,
        actual_amount: 950,
        variance_amount: -50,
        variance_percentage: -5.0,
        status: 'under_budget',
        last_updated: '2024-01-15T00:00:00Z',
      },
    ],
    statistical_significance: {
      is_significant: true,
      confidence_level: 0.95,
      p_value: 0.02,
      effect_size: 0.3,
    },
    trend_analysis: {
      trend_direction: 'improving',
      trend_strength: 0.7,
      trend_confidence: 0.85,
    },
  },
  performance_metrics: {
    budget_id: 'budget-1',
    period_start: '2024-01-01',
    period_end: '2024-01-31',
    accuracy_score: 0.85,
    adherence_rate: 0.78,
    forecast_accuracy: 0.82,
    variance_trend: {
      direction: 'improving',
      magnitude: 0.3,
      consistency: 0.8,
    },
    category_performance: [
      {
        category: 'Food',
        subcategory: 'Groceries',
        accuracy_score: 0.92,
        adherence_rate: 0.88,
        variance_trend: -0.05,
        recommendation_count: 1,
        alert_count: 0,
      },
    ],
    historical_comparison: {
      previous_period_accuracy: 0.80,
      improvement_rate: 0.06,
      best_performance_date: '2024-01-15',
      worst_performance_date: '2024-01-01',
    },
    ml_model_performance: {
      prediction_accuracy: 0.88,
      confidence_improvement: 0.05,
      model_learning_rate: 0.02,
    },
  },
  active_alerts: [],
  recent_recommendations: [],
  scenarios: [],
}

const mockVarianceAnalysis = {
  variance_analysis: {
    budget_id: 'budget-1',
    period_start: '2024-01-01',
    period_end: '2024-01-31',
    total_budget: 5000,
    total_actual: 4750,
    total_variance: -250,
    variance_percentage: -5.0,
    overall_status: 'under_budget',
    category_breakdown: [
      {
        budget_id: 'budget-1',
        category: 'Food',
        subcategory: 'Groceries',
        allocated_amount: 1000,
        actual_amount: 950,
        variance_amount: -50,
        variance_percentage: -5.0,
        status: 'under_budget',
        last_updated: '2024-01-15T00:00:00Z',
      },
    ],
    statistical_significance: {
      is_significant: true,
      confidence_level: 0.95,
      p_value: 0.02,
      effect_size: 0.3,
    },
    trend_analysis: {
      trend_direction: 'improving',
      trend_strength: 0.7,
      trend_confidence: 0.85,
    },
  },
  category_details: [],
  alerts: [],
  recommendations: [],
}

const mockRecommendations = {
  recommendations: [
    {
      recommendation_id: 'rec-1',
      budget_id: 'budget-1',
      recommendation_type: 'category_adjustment',
      category: 'Food',
      subcategory: 'Groceries',
      current_amount: 1000,
      recommended_amount: 950,
      adjustment_amount: -50,
      confidence_score: 0.85,
      reasoning: 'Based on historical spending patterns, you can reduce grocery budget by 5%',
      impact_analysis: {
        short_term_impact: 'Immediate savings of $50',
        long_term_impact: 'Potential annual savings of $600',
        risk_level: 'low',
      },
      ml_insights: {
        pattern_detected: 'Consistent underspending in groceries',
        historical_comparison: 'Average spending is 5% below budget',
        seasonal_factor: 1.0,
      },
      created_at: '2024-01-15T00:00:00Z',
      applied: false,
    },
  ],
  total_count: 1,
  applied_count: 0,
  pending_count: 1,
  average_confidence: 0.85,
}

// Test setup
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('BudgetAnalysis', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default mock implementations
    mockBudgetAnalysisAPI.getBudgets.mockResolvedValue({ data: mockBudgets })
    mockBudgetAnalysisAPI.getSummary.mockResolvedValue({ data: mockSummary })
    mockBudgetAnalysisAPI.getBudget.mockResolvedValue({ data: mockBudgetDetails })
    mockBudgetAnalysisAPI.getVarianceAnalysis.mockResolvedValue({ data: mockVarianceAnalysis })
    mockBudgetAnalysisAPI.getRecommendations.mockResolvedValue({ data: mockRecommendations })
    mockBudgetAnalysisAPI.applyRecommendation.mockResolvedValue({ data: { success: true } })
  })

  it('renders budget analysis dashboard', () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    expect(screen.getByText('Budget Analysis Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Comprehensive budget vs actual analysis with AI-powered recommendations')).toBeInTheDocument()
  })

  it('displays summary cards when data is loaded', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Budgets')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('Active Budgets')).toBeInTheDocument()
      expect(screen.getByText('Critical Alerts')).toBeInTheDocument()
      expect(screen.getByText('Pending Recommendations')).toBeInTheDocument()
    })
  })

  it('displays budget selection dropdown', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      expect(screen.getByLabelText('Select Budget')).toBeInTheDocument()
    })
  })

  it('shows action buttons', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      expect(screen.getByText('New Budget')).toBeInTheDocument()
      expect(screen.getByText('Scenarios')).toBeInTheDocument()
      expect(screen.getByText('Alerts')).toBeInTheDocument()
    })
  })

  it('displays budget details when a budget is selected', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Budget Overview')).toBeInTheDocument()
      expect(screen.getByText('$5,000')).toBeInTheDocument()
      expect(screen.getByText('monthly')).toBeInTheDocument()
    })
  })

  it('displays variance analysis when budget is selected', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Variance Analysis')).toBeInTheDocument()
      expect(screen.getByText('$4,750')).toBeInTheDocument()
      expect(screen.getByText('$250 Under')).toBeInTheDocument()
      expect(screen.getByText('5.0%')).toBeInTheDocument()
    })
  })

  it('displays AI recommendations when available', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      expect(screen.getByText('AI Recommendations')).toBeInTheDocument()
      expect(screen.getByText('category adjustment')).toBeInTheDocument()
      expect(screen.getByText(/Based on historical spending patterns/)).toBeInTheDocument()
      expect(screen.getByText('Confidence: 85%')).toBeInTheDocument()
    })
  })

  it('allows applying recommendations', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      const applyButton = screen.getByText('Apply')
      fireEvent.click(applyButton)
    })
    
    await waitFor(() => {
      expect(mockBudgetAnalysisAPI.applyRecommendation).toHaveBeenCalledWith({
        budgetId: 'budget-1',
        recommendationId: 'rec-1',
      })
    })
  })

  it('displays performance metrics when available', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument() // Accuracy Score
      expect(screen.getByText('78%')).toBeInTheDocument() // Adherence Rate
      expect(screen.getByText('82%')).toBeInTheDocument() // Forecast Accuracy
    })
  })

  it('handles refresh button click', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)
    })
    
    // The refresh should trigger API calls
    await waitFor(() => {
      expect(mockBudgetAnalysisAPI.getBudgets).toHaveBeenCalled()
      expect(mockBudgetAnalysisAPI.getSummary).toHaveBeenCalled()
    })
  })

  it('displays loading states', () => {
    // Mock loading state
    mockBudgetAnalysisAPI.getSummary.mockImplementation(() => new Promise(() => {}))
    
    renderWithQueryClient(<BudgetAnalysis />)
    
    // Should show loading skeleton
    expect(screen.getByText('Budget Analysis Dashboard')).toBeInTheDocument()
  })

  it('displays error states', async () => {
    // Mock error
    mockBudgetAnalysisAPI.getSummary.mockRejectedValue(new Error('API Error'))
    
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading budget data')).toBeInTheDocument()
      expect(screen.getByText('Please check your connection and try refreshing the page.')).toBeInTheDocument()
    })
  })

  it('shows category breakdown in variance analysis', async () => {
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Category Breakdown')).toBeInTheDocument()
      expect(screen.getByText('Food')).toBeInTheDocument()
      expect(screen.getByText('$1,000 allocated')).toBeInTheDocument()
      expect(screen.getByText('$950')).toBeInTheDocument()
      expect(screen.getByText('-5.0%')).toBeInTheDocument()
    })
  })

  it('handles empty budget list gracefully', async () => {
    mockBudgetAnalysisAPI.getBudgets.mockResolvedValue({ 
      data: { budgets: [], total_count: 0, page: 1, page_size: 10 } 
    })
    
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      expect(screen.getByText('Choose a budget...')).toBeInTheDocument()
      expect(screen.getByText('Demo Budget 1 - Monthly')).toBeInTheDocument()
    })
  })

  it('handles empty recommendations gracefully', async () => {
    mockBudgetAnalysisAPI.getRecommendations.mockResolvedValue({ 
      data: { recommendations: [], total_count: 0, applied_count: 0, pending_count: 0, average_confidence: 0 } 
    })
    
    renderWithQueryClient(<BudgetAnalysis />)
    
    await waitFor(() => {
      const budgetSelect = screen.getByLabelText('Select Budget')
      fireEvent.change(budgetSelect, { target: { value: 'budget-1' } })
    })
    
    await waitFor(() => {
      // Should not show AI Recommendations section when empty
      expect(screen.queryByText('AI Recommendations')).not.toBeInTheDocument()
    })
  })
})
