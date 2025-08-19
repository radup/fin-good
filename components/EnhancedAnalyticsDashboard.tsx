'use client'

import React, { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3, 
  PieChart, 
  Activity,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { enhancedAnalyticsAPI } from '@/lib/api'

interface AnalyticsData {
  cashFlow?: any
  categoryInsights?: any
  vendorAnalysis?: any
  anomalyDetection?: any
  comparativeAnalysis?: any
  trendAnalysis?: any
  dashboardData?: any
}

interface EnhancedAnalyticsDashboardProps {
  className?: string
  startDate?: string
  endDate?: string
}

export default function EnhancedAnalyticsDashboard({ 
  className = '',
  startDate,
  endDate
}: EnhancedAnalyticsDashboardProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState({
    start: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: endDate || new Date().toISOString().split('T')[0]
  })

  const fetchAnalyticsData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = {
        start_date: dateRange.start,
        end_date: dateRange.end
      }

      // Fetch all analytics data in parallel
      const [
        cashFlowResponse,
        categoryInsightsResponse,
        vendorAnalysisResponse,
        anomalyDetectionResponse,
        trendAnalysisResponse,
        dashboardResponse
      ] = await Promise.allSettled([
        enhancedAnalyticsAPI.getCashFlowAnalysis(params),
        enhancedAnalyticsAPI.getCategoryInsights(params),
        enhancedAnalyticsAPI.getVendorAnalysis(params),
        enhancedAnalyticsAPI.getAnomalyDetection(params),
        enhancedAnalyticsAPI.getTrendAnalysis(params),
        enhancedAnalyticsAPI.getDashboardData(params)
      ])

      const newData: AnalyticsData = {}

      // Process successful responses
      if (cashFlowResponse.status === 'fulfilled') {
        newData.cashFlow = cashFlowResponse.value.data
      }
      if (categoryInsightsResponse.status === 'fulfilled') {
        newData.categoryInsights = categoryInsightsResponse.value.data
      }
      if (vendorAnalysisResponse.status === 'fulfilled') {
        newData.vendorAnalysis = vendorAnalysisResponse.value.data
      }
      if (anomalyDetectionResponse.status === 'fulfilled') {
        newData.anomalyDetection = anomalyDetectionResponse.value.data
      }
      if (trendAnalysisResponse.status === 'fulfilled') {
        newData.trendAnalysis = trendAnalysisResponse.value.data
      }
      if (dashboardResponse.status === 'fulfilled') {
        newData.dashboardData = dashboardResponse.value.data
      }

      setAnalyticsData(newData)

    } catch (err: any) {
      console.error('Failed to fetch analytics data:', err)
      setError(err.response?.data?.detail || 'Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalyticsData()
  }, [dateRange])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center gap-2 text-red-600 mb-4">
          <AlertCircle className="w-5 h-5" />
          <h2 className="text-lg font-semibold">Analytics Error</h2>
        </div>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchAnalyticsData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Enhanced Analytics</h2>
            <p className="text-sm text-gray-500">Comprehensive financial insights and trends</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchAnalyticsData}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Export data"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Date Range:</span>
          </div>
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <span className="text-gray-500">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Revenue */}
          <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800">Total Revenue</p>
                <p className="text-2xl font-bold text-green-900">
                  {analyticsData.dashboardData?.total_revenue 
                    ? formatCurrency(analyticsData.dashboardData.total_revenue)
                    : '$0.00'
                  }
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
            {analyticsData.dashboardData?.revenue_growth && (
              <p className="text-sm text-green-700 mt-2">
                +{formatPercentage(analyticsData.dashboardData.revenue_growth)} vs last period
              </p>
            )}
          </div>

          {/* Total Expenses */}
          <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-800">Total Expenses</p>
                <p className="text-2xl font-bold text-red-900">
                  {analyticsData.dashboardData?.total_expenses 
                    ? formatCurrency(analyticsData.dashboardData.total_expenses)
                    : '$0.00'
                  }
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-600" />
            </div>
            {analyticsData.dashboardData?.expense_growth && (
              <p className="text-sm text-red-700 mt-2">
                {analyticsData.dashboardData.expense_growth > 0 ? '+' : ''}
                {formatPercentage(analyticsData.dashboardData.expense_growth)} vs last period
              </p>
            )}
          </div>

          {/* Net Profit */}
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-800">Net Profit</p>
                <p className="text-2xl font-bold text-blue-900">
                  {analyticsData.dashboardData?.net_profit 
                    ? formatCurrency(analyticsData.dashboardData.net_profit)
                    : '$0.00'
                  }
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-600" />
            </div>
            {analyticsData.dashboardData?.profit_margin && (
              <p className="text-sm text-blue-700 mt-2">
                {formatPercentage(analyticsData.dashboardData.profit_margin)} margin
              </p>
            )}
          </div>

          {/* Transaction Count */}
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-800">Transactions</p>
                <p className="text-2xl font-bold text-purple-900">
                  {analyticsData.dashboardData?.total_transactions || 0}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-600" />
            </div>
            {analyticsData.dashboardData?.avg_transaction_value && (
              <p className="text-sm text-purple-700 mt-2">
                Avg: {formatCurrency(analyticsData.dashboardData.avg_transaction_value)}
              </p>
            )}
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cash Flow Analysis */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Cash Flow Analysis
            </h3>
            {analyticsData.cashFlow ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Cash Inflow</span>
                  <span className="font-semibold text-green-600">
                    {formatCurrency(analyticsData.cashFlow.total_inflow || 0)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Cash Outflow</span>
                  <span className="font-semibold text-red-600">
                    {formatCurrency(analyticsData.cashFlow.total_outflow || 0)}
                  </span>
                </div>
                <div className="flex justify-between items-center border-t pt-2">
                  <span className="text-sm font-medium text-gray-700">Net Cash Flow</span>
                  <span className={`font-semibold ${
                    (analyticsData.cashFlow.net_flow || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(analyticsData.cashFlow.net_flow || 0)}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No cash flow data available</p>
            )}
          </div>

          {/* Category Insights */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Top Categories
            </h3>
            {analyticsData.categoryInsights?.top_categories ? (
              <div className="space-y-2">
                {analyticsData.categoryInsights.top_categories.slice(0, 5).map((category: any, index: number) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{category.name}</span>
                    <span className="font-semibold text-gray-900">
                      {formatCurrency(category.amount)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No category data available</p>
            )}
          </div>
        </div>

        {/* Anomaly Detection */}
        {analyticsData.anomalyDetection?.anomalies && analyticsData.anomalyDetection.anomalies.length > 0 && (
          <div className="mt-6 bg-yellow-50 p-4 rounded-lg border border-yellow-200">
            <h3 className="text-lg font-semibold text-yellow-800 mb-3 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Anomaly Detection
            </h3>
            <div className="space-y-2">
              {analyticsData.anomalyDetection.anomalies.slice(0, 3).map((anomaly: any, index: number) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <AlertCircle className="w-4 h-4 text-yellow-600" />
                  <span className="text-yellow-800">{anomaly.description}</span>
                  <span className="text-yellow-600">({formatCurrency(anomaly.amount)})</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Trend Analysis */}
        {analyticsData.trendAnalysis && (
          <div className="mt-6 bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="text-lg font-semibold text-blue-800 mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Trend Analysis
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-blue-600">Revenue Trend</p>
                <p className="text-lg font-semibold text-blue-900">
                  {analyticsData.trendAnalysis.revenue_trend > 0 ? '+' : ''}
                  {formatPercentage(analyticsData.trendAnalysis.revenue_trend || 0)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-blue-600">Expense Trend</p>
                <p className="text-lg font-semibold text-blue-900">
                  {analyticsData.trendAnalysis.expense_trend > 0 ? '+' : ''}
                  {formatPercentage(analyticsData.trendAnalysis.expense_trend || 0)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-blue-600">Growth Rate</p>
                <p className="text-lg font-semibold text-blue-900">
                  {analyticsData.trendAnalysis.growth_rate > 0 ? '+' : ''}
                  {formatPercentage(analyticsData.trendAnalysis.growth_rate || 0)}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
