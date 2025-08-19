import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import EnhancedAnalytics from '@/components/EnhancedAnalytics'
import { enhancedAnalyticsAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  enhancedAnalyticsAPI: {
    getPerformanceMetrics: jest.fn(),
    getPredictiveInsights: jest.fn(),
    getEnhancedVendorAnalysis: jest.fn(),
    getAnalyticsSummary: jest.fn(),
    clearEnhancedCache: jest.fn(),
  }
}))

// Mock the ErrorBoundary component
jest.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

const mockPerformanceMetrics = {
  api_response_times: {
    average: 150,
    p95: 300,
    p99: 500,
    slowest_endpoints: []
  },
  cache_performance: {
    hit_rate: 0.85,
    miss_rate: 0.15,
    total_requests: 1000,
    cache_size: 100
  },
  database_performance: {
    query_count: 500,
    average_query_time: 50,
    slow_queries: []
  },
  background_jobs: {
    active_jobs: 5,
    completed_jobs: 100,
    failed_jobs: 2,
    average_processing_time: 30
  },
  system_health: {
    memory_usage: 75,
    cpu_usage: 60,
    disk_usage: 45,
    uptime: 168
  }
}

const mockPredictiveInsights = {
  spending_forecast: [{
    period: '2024-02',
    predicted_amount: 4500,
    confidence_interval: { lower: 4000, upper: 5000 },
    trend: 'increasing' as const
  }],
  budget_recommendations: [{
    category: 'Food',
    current_spending: 800,
    recommended_budget: 600,
    reasoning: 'High spending detected',
    confidence: 0.85
  }],
  anomaly_detection: [{
    transaction_id: 123,
    anomaly_type: 'unusual_amount' as const,
    confidence: 0.9,
    description: 'Unusual spending pattern detected',
    suggested_action: 'Review transaction'
  }],
  financial_health_score: {
    overall_score: 8.5,
    spending_efficiency: 7.8,
    budget_adherence: 8.2,
    savings_rate: 0.25,
    debt_ratio: 0.15,
    recommendations: ['Review spending patterns weekly']
  }
}

const mockVendorAnalysis = {
  vendor_performance: [{
    vendor: 'Starbucks',
    total_transactions: 45,
    total_amount: 850,
    average_amount: 18.89,
    frequency: 15,
    categories: [{ category: 'Food', count: 45, amount: 850 }],
    spending_trend: [{ month: '2024-01', amount: 850, transaction_count: 45 }],
    risk_score: 0.3,
    recommendations: ['Consider bulk purchases']
  }],
  vendor_insights: {
    top_vendors: [{
      vendor: 'Starbucks',
      total_spent: 850,
      transaction_count: 45,
      category_distribution: { 'Food': 100 }
    }],
    vendor_categories: [],
    vendor_anomalies: []
  }
}

const mockAnalyticsSummary = {
  overall_metrics: {
    total_transactions: 1250,
    total_amount: 15000,
    average_transaction_amount: 12,
    unique_vendors: 50,
    categories_used: 15
  },
  time_series_data: [],
  category_breakdown: [{
    category: 'Food',
    transaction_count: 200,
    total_amount: 3000,
    percentage_of_total: 20
  }],
  vendor_breakdown: [],
  insights: [{
    type: 'spending',
    title: 'High spending in Food category',
    description: 'Consider setting budget alerts',
    impact: 'negative' as const,
    confidence: 0.8
  }]
}

describe('EnhancedAnalytics', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    const mockGetMetrics = enhancedAnalyticsAPI.getPerformanceMetrics as jest.MockedFunction<typeof enhancedAnalyticsAPI.getPerformanceMetrics>
    const mockGetInsights = enhancedAnalyticsAPI.getPredictiveInsights as jest.MockedFunction<typeof enhancedAnalyticsAPI.getPredictiveInsights>
    const mockGetVendor = enhancedAnalyticsAPI.getEnhancedVendorAnalysis as jest.MockedFunction<typeof enhancedAnalyticsAPI.getEnhancedVendorAnalysis>
    const mockGetSummary = enhancedAnalyticsAPI.getAnalyticsSummary as jest.MockedFunction<typeof enhancedAnalyticsAPI.getAnalyticsSummary>
    
    mockGetMetrics.mockResolvedValue({ 
      data: mockPerformanceMetrics,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    })
    mockGetInsights.mockResolvedValue({ 
      data: mockPredictiveInsights,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    })
    mockGetVendor.mockResolvedValue({ 
      data: mockVendorAnalysis,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    })
    mockGetSummary.mockResolvedValue({ 
      data: mockAnalyticsSummary,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    })
  })

  it('renders the component with header and controls', async () => {
    render(<EnhancedAnalytics />)
    
    await waitFor(() => {
      expect(screen.getByText('Enhanced Analytics Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Advanced insights and predictive analytics for your financial data')).toBeInTheDocument()
    })
  })

  it('displays performance metrics when available', async () => {
    render(<EnhancedAnalytics />)
    
    await waitFor(() => {
      expect(screen.getByText('API Response Time')).toBeInTheDocument()
      expect(screen.getByText('Cache Hit Rate')).toBeInTheDocument()
      expect(screen.getByText('System Uptime')).toBeInTheDocument()
    })
  })

  it('displays predictive insights when available', async () => {
    render(<EnhancedAnalytics />)
    
    await waitFor(() => {
      expect(screen.getByText('Predictive Insights')).toBeInTheDocument()
      expect(screen.getByText('Spending Forecast')).toBeInTheDocument()
      expect(screen.getByText('$4,500')).toBeInTheDocument()
    })
  })

  it('displays vendor analysis when available', async () => {
    render(<EnhancedAnalytics />)
    
    await waitFor(() => {
      expect(screen.getByText('Top Vendors Analysis')).toBeInTheDocument()
      expect(screen.getByText('Starbucks')).toBeInTheDocument()
    })
  })

  it('displays analytics summary when available', async () => {
    render(<EnhancedAnalytics />)
    
    await waitFor(() => {
      expect(screen.getByText('Analytics Summary')).toBeInTheDocument()
      expect(screen.getByText('8.5/10')).toBeInTheDocument()
    })
  })

  it('shows error message when API calls fail', async () => {
    const mockGetMetrics = enhancedAnalyticsAPI.getPerformanceMetrics as jest.MockedFunction<typeof enhancedAnalyticsAPI.getPerformanceMetrics>
    mockGetMetrics.mockRejectedValue(new Error('API Error'))
    
    render(<EnhancedAnalytics />)
    
    await waitFor(() => {
      expect(screen.getByText('Error Loading Analytics')).toBeInTheDocument()
      expect(screen.getByText('Failed to fetch analytics data')).toBeInTheDocument()
    })
  })
})
