import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ForecastingDashboard } from '@/components/ForecastingDashboard'
import { forecastingAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  forecastingAPI: {
    getForecastTypes: jest.fn(),
    getHorizons: jest.fn(),
    getAccuracyHistory: jest.fn(),
    generateForecast: jest.fn(),
  },
}))

const mockForecastTypes = [
  {
    value: 'cash_flow',
    label: 'Cash Flow',
    description: 'Predict cash flow patterns',
    supported_horizons: ['7_days', '30_days', '60_days', '90_days', 'custom']
  },
  {
    value: 'revenue',
    label: 'Revenue',
    description: 'Predict revenue trends',
    supported_horizons: ['7_days', '30_days', '60_days', '90_days', 'custom']
  },
  {
    value: 'expenses',
    label: 'Expenses',
    description: 'Predict expense patterns',
    supported_horizons: ['7_days', '30_days', '60_days', '90_days', 'custom']
  }
]

const mockHorizons = [
  {
    value: '7_days',
    label: '7 Days',
    days: 7,
    description: 'Short-term forecast',
    recommended_for: ['cash_flow', 'revenue']
  },
  {
    value: '30_days',
    label: '30 Days',
    days: 30,
    description: 'Medium-term forecast',
    recommended_for: ['cash_flow', 'revenue', 'expenses']
  },
  {
    value: '60_days',
    label: '60 Days',
    days: 60,
    description: 'Long-term forecast',
    recommended_for: ['revenue', 'expenses']
  },
  {
    value: '90_days',
    label: '90 Days',
    days: 90,
    description: 'Extended forecast',
    recommended_for: ['revenue', 'expenses']
  },
  {
    value: 'custom',
    label: 'Custom',
    days: 0,
    description: 'Custom forecast period',
    recommended_for: ['cash_flow', 'revenue', 'expenses']
  }
]

const mockAccuracyHistory = {
  user_id: 1,
  period_days: 30,
  average_accuracy: 0.85,
  forecast_count: 15,
  accuracy_trend: 'improving',
  best_forecast_type: 'cash_flow',
  accuracy_by_horizon: {
    '7_days': 0.92,
    '30_days': 0.85,
    '60_days': 0.78,
    '90_days': 0.72
  }
}

const mockForecastResponse = {
  forecast_id: 'forecast_123',
  user_id: 1,
  forecast_type: 'cash_flow',
  horizon_days: 30,
  predictions: [
    {
      date: '2024-01-01',
      value: 1500.00,
      confidence_lower: 1400.00,
      confidence_upper: 1600.00,
      trend_component: 1450.00,
      seasonal_component: 50.00
    },
    {
      date: '2024-01-02',
      value: 1550.00,
      confidence_lower: 1450.00,
      confidence_upper: 1650.00,
      trend_component: 1475.00,
      seasonal_component: 75.00
    }
  ],
  confidence_score: 0.92,
  seasonal_pattern: 'weekly',
  trend_direction: 'increasing',
  model_accuracy: 0.88,
  created_at: '2024-01-01T10:00:00Z',
  metadata: {
    seasonal_strength: 0.75,
    trend_strength: 0.85,
    volatility: 0.12,
    data_points: 100,
    category_filter: undefined
  }
}

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
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

describe('ForecastingDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Setup default mocks
    ;(forecastingAPI.getForecastTypes as jest.Mock).mockResolvedValue(mockForecastTypes)
    ;(forecastingAPI.getHorizons as jest.Mock).mockResolvedValue(mockHorizons)
    ;(forecastingAPI.getAccuracyHistory as jest.Mock).mockResolvedValue(mockAccuracyHistory)
    ;(forecastingAPI.generateForecast as jest.Mock).mockResolvedValue(mockForecastResponse)
  })

  it('renders the forecasting dashboard with header', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Cash Flow Forecasting')).toBeInTheDocument()
      expect(screen.getByText('ML-powered predictions with confidence intervals')).toBeInTheDocument()
    })
  })

  it('displays forecast configuration form', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Forecast Configuration')).toBeInTheDocument()
      expect(screen.getByLabelText('Forecast Type')).toBeInTheDocument()
      expect(screen.getByLabelText('Forecast Horizon')).toBeInTheDocument()
      expect(screen.getByLabelText('Category Filter (Optional)')).toBeInTheDocument()
    })
  })

  it('populates forecast types dropdown', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const forecastTypeSelect = screen.getByLabelText('Forecast Type')
      expect(forecastTypeSelect).toHaveValue('cash_flow')
      
      // Check that all forecast types are available
      expect(screen.getByText('Cash Flow')).toBeInTheDocument()
      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Expenses')).toBeInTheDocument()
    })
  })

  it('populates horizons dropdown', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const horizonSelect = screen.getByLabelText('Forecast Horizon')
      expect(horizonSelect).toHaveValue('30_days')
      
      // Check that all horizons are available
      expect(screen.getByText('7 Days')).toBeInTheDocument()
      expect(screen.getByText('30 Days')).toBeInTheDocument()
      expect(screen.getByText('60 Days')).toBeInTheDocument()
      expect(screen.getByText('90 Days')).toBeInTheDocument()
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })
  })

  it('shows custom days input when custom horizon is selected', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const horizonSelect = screen.getByLabelText('Forecast Horizon')
      fireEvent.change(horizonSelect, { target: { value: 'custom' } })
      
      expect(screen.getByLabelText('Custom Days')).toBeInTheDocument()
      expect(screen.getByDisplayValue('30')).toBeInTheDocument()
    })
  })

  it('updates confidence level slider', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const confidenceSlider = screen.getByRole('slider')
      expect(confidenceSlider).toHaveValue('0.95')
      
      fireEvent.change(confidenceSlider, { target: { value: '0.90' } })
      expect(confidenceSlider).toHaveValue('0.90')
      expect(screen.getByText('Confidence Level: 90%')).toBeInTheDocument()
    })
  })

  it('generates forecast when button is clicked', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const generateButton = screen.getByText('Generate Forecast')
      fireEvent.click(generateButton)
    })
    
    await waitFor(() => {
      expect(forecastingAPI.generateForecast).toHaveBeenCalledWith({
        forecast_type: 'cash_flow',
        horizon: '30_days',
        custom_days: undefined,
        category_filter: undefined,
        confidence_level: 0.95,
      })
    })
  })

  it('shows loading state during forecast generation', async () => {
    // Mock a delayed response
    ;(forecastingAPI.generateForecast as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockForecastResponse), 100))
    )
    
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const generateButton = screen.getByText('Generate Forecast')
      fireEvent.click(generateButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Generating Forecast...')).toBeInTheDocument()
      expect(screen.getByText('Generate Forecast')).toBeDisabled()
    })
  })

  it('displays forecast results after generation', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const generateButton = screen.getByText('Generate Forecast')
      fireEvent.click(generateButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Forecast Results')).toBeInTheDocument()
      expect(screen.getByText('Confidence: 92%')).toBeInTheDocument()
      expect(screen.getByText('Accuracy: 88%')).toBeInTheDocument()
      expect(screen.getByText('Pattern: weekly')).toBeInTheDocument()
      expect(screen.getByText('Trend Direction')).toBeInTheDocument()
      expect(screen.getByText('increasing')).toBeInTheDocument()
      expect(screen.getByText('Total Predicted')).toBeInTheDocument()
      expect(screen.getByText('$3050.00')).toBeInTheDocument()
      expect(screen.getByText('Data Points')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays accuracy history', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Forecast Accuracy History')).toBeInTheDocument()
      expect(screen.getByText('Average Accuracy')).toBeInTheDocument()
      expect(screen.getAllByText('85%')).toHaveLength(2) // Both average accuracy and 30 days
      expect(screen.getByText('Forecasts Generated')).toBeInTheDocument()
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('Accuracy Trend')).toBeInTheDocument()
      expect(screen.getByText('improving')).toBeInTheDocument()
      expect(screen.getByText('Best Type')).toBeInTheDocument()
      expect(screen.getByText('cash flow')).toBeInTheDocument()
    })
  })

  it('displays accuracy by horizon', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Accuracy by Horizon')).toBeInTheDocument()
      expect(screen.getByText('7 days')).toBeInTheDocument()
      expect(screen.getByText('92%')).toBeInTheDocument()
      expect(screen.getByText('30 days')).toBeInTheDocument()
      expect(screen.getAllByText('85%')).toHaveLength(2) // Both average accuracy and 30 days
      expect(screen.getByText('60 days')).toBeInTheDocument()
      expect(screen.getByText('78%')).toBeInTheDocument()
      expect(screen.getByText('90 days')).toBeInTheDocument()
      expect(screen.getByText('72%')).toBeInTheDocument()
    })
  })

  it('handles forecast generation error', async () => {
    const errorMessage = 'Failed to generate forecast: Insufficient data'
    ;(forecastingAPI.generateForecast as jest.Mock).mockRejectedValue(
      new Error(errorMessage)
    )
    
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const generateButton = screen.getByText('Generate Forecast')
      fireEvent.click(generateButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Forecast Generation Failed')).toBeInTheDocument()
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('toggles confidence intervals visibility', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const toggleButton = screen.getByText('Hide Confidence')
      fireEvent.click(toggleButton)
      
      expect(screen.getByText('Show Confidence')).toBeInTheDocument()
      
      fireEvent.click(toggleButton)
      expect(screen.getByText('Hide Confidence')).toBeInTheDocument()
    })
  })

  it('refreshes data when refresh button is clicked', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)
    })
    
    await waitFor(() => {
      expect(forecastingAPI.getAccuracyHistory).toHaveBeenCalledTimes(2) // Initial + refresh
      expect(forecastingAPI.getForecastTypes).toHaveBeenCalledTimes(2)
      expect(forecastingAPI.getHorizons).toHaveBeenCalledTimes(2)
    })
  })

  it('updates forecast type selection', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const forecastTypeSelect = screen.getByLabelText('Forecast Type')
      fireEvent.change(forecastTypeSelect, { target: { value: 'revenue' } })
      
      expect(forecastTypeSelect).toHaveValue('revenue')
    })
  })

  it('updates horizon selection', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const horizonSelect = screen.getByLabelText('Forecast Horizon')
      fireEvent.change(horizonSelect, { target: { value: '60_days' } })
      
      expect(horizonSelect).toHaveValue('60_days')
    })
  })

  it('updates category filter', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const categoryInput = screen.getByLabelText('Category Filter (Optional)')
      fireEvent.change(categoryInput, { target: { value: 'Food' } })
      
      expect(categoryInput).toHaveValue('Food')
    })
  })

  it('updates custom days when custom horizon is selected', async () => {
    renderWithQueryClient(<ForecastingDashboard />)
    
    await waitFor(() => {
      const horizonSelect = screen.getByLabelText('Forecast Horizon')
      fireEvent.change(horizonSelect, { target: { value: 'custom' } })
      
      const customDaysInput = screen.getByLabelText('Custom Days')
      fireEvent.change(customDaysInput, { target: { value: '45' } })
      
      expect(customDaysInput).toHaveValue(45)
    })
  })

  it('shows loading skeleton during initial load', async () => {
    // Mock slow loading
    ;(forecastingAPI.getForecastTypes as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockForecastTypes), 100))
    )
    
    renderWithQueryClient(<ForecastingDashboard />)
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Forecast Configuration')).toBeInTheDocument()
    }, { timeout: 2000 })
  })
})
