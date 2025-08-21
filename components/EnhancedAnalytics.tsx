import React, { useState, useEffect } from 'react'
import { enhancedAnalyticsAPI } from '@/lib/api'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { TrendingUp, AlertTriangle, BarChart3, PieChart, Calendar, Download, Filter, RefreshCw } from 'lucide-react'
import { EnhancedPerformanceMetrics, PredictiveInsights, EnhancedVendorAnalysis, AnalyticsSummary } from '@/types/api'

const EnhancedAnalytics: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [performanceMetrics, setPerformanceMetrics] = useState<EnhancedPerformanceMetrics | null>(null)
  const [predictiveInsights, setPredictiveInsights] = useState<PredictiveInsights | null>(null)
  const [vendorAnalysis, setVendorAnalysis] = useState<EnhancedVendorAnalysis | null>(null)
  const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState('30d')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const fetchAnalyticsData = async () => {
    try {
      setError(null)
      const [metricsRes, insightsRes, vendorRes, summaryRes] = await Promise.all([
        enhancedAnalyticsAPI.getPerformanceMetrics(),
        enhancedAnalyticsAPI.getPredictiveInsights(),
        enhancedAnalyticsAPI.getEnhancedVendorAnalysis(),
        enhancedAnalyticsAPI.getAnalyticsSummary()
      ])

      setPerformanceMetrics(metricsRes.data)
      setPredictiveInsights(insightsRes.data)
      setVendorAnalysis(vendorRes.data)
      setAnalyticsSummary(summaryRes.data)
    } catch (err) {
      setError('Failed to fetch analytics data')
      console.error('Error fetching analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchAnalyticsData()
    setRefreshing(false)
  }

  const handleClearCache = async () => {
    try {
      await enhancedAnalyticsAPI.clearEnhancedCache()
      await handleRefresh()
    } catch (err) {
      setError('Failed to clear cache')
    }
  }

  useEffect(() => {
    fetchAnalyticsData()
  }, [])

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
      case 'increasing':
        return <TrendingUp className="w-4 h-4 text-green-600" />
      case 'down':
      case 'decreasing':
        return <TrendingUp className="w-4 h-4 text-red-600 rotate-180" />
      default:
        return <BarChart3 className="w-4 h-4 text-gray-600" />
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4" />
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-6" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded" />
            ))}
          </div>
          <div className="space-y-4">
            <div className="h-64 bg-gray-200 rounded" />
            <div className="h-48 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Analytics</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="btn-primary"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="bg-white rounded-lg shadow">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Enhanced Analytics Dashboard</h2>
              <p className="text-sm text-gray-500">
                Advanced insights and predictive analytics for your financial data
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
              </select>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="btn-secondary disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={handleClearCache}
                className="btn-secondary"
              >
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        {performanceMetrics && (
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">API Response Time</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {performanceMetrics.api_response_times.average.toFixed(1)}ms
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-blue-500" />
                </div>
              </div>
              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Cache Hit Rate</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {(performanceMetrics.cache_performance.hit_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <PieChart className="w-8 h-8 text-green-500" />
                </div>
              </div>
              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">System Uptime</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {performanceMetrics.system_health.uptime.toFixed(1)}h
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-purple-500" />
                </div>
              </div>
              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Active Jobs</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {performanceMetrics.background_jobs.active_jobs}
                    </p>
                  </div>
                  <Calendar className="w-8 h-8 text-orange-500" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Predictive Insights */}
            {predictiveInsights && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Predictive Insights</h3>
                  {getTrendIcon(predictiveInsights.spending_forecast[0]?.trend || 'stable')}
                </div>
                
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Spending Forecast</h4>
                    <p className="text-2xl font-bold text-blue-900">
                      ${predictiveInsights.spending_forecast[0]?.predicted_amount.toLocaleString() || 0}
                    </p>
                    <p className="text-sm text-blue-700">
                      Predicted for next month
                    </p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Budget Recommendations</h4>
                    <ul className="space-y-1">
                      {predictiveInsights.budget_recommendations.slice(0, 3).map((rec, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-center">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
                          {rec.category}: ${rec.recommended_budget.toLocaleString()}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Financial Health</h4>
                    <p className="text-lg font-bold text-gray-900">
                      {predictiveInsights.financial_health_score.overall_score.toFixed(1)}/10
                    </p>
                    <ul className="space-y-1 mt-2">
                      {predictiveInsights.financial_health_score.recommendations.slice(0, 2).map((rec, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-center">
                          <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {predictiveInsights.anomaly_detection.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded p-4">
                      <h4 className="font-medium text-red-900 mb-2">Anomaly Detection</h4>
                      <ul className="space-y-1">
                        {predictiveInsights.anomaly_detection.slice(0, 2).map((anomaly, index) => (
                          <li key={index} className="text-sm text-red-700 flex items-center">
                            <AlertTriangle className="w-4 h-4 mr-2" />
                            {anomaly.description}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Enhanced Vendor Analysis */}
            {vendorAnalysis && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Top Vendors Analysis</h3>
                
                <div className="space-y-4">
                  {vendorAnalysis.vendor_performance.slice(0, 5).map((vendor, index) => (
                    <div key={index} className="border border-gray-200 rounded p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{vendor.vendor}</h4>
                        <span className="text-sm text-gray-500">Risk: {vendor.risk_score.toFixed(1)}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">Total Spent</p>
                          <p className="font-medium">${vendor.total_amount.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Transactions</p>
                          <p className="font-medium">{vendor.total_transactions}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6">
                  <h4 className="font-medium text-gray-900 mb-2">Vendor Insights</h4>
                  <div className="space-y-2">
                    {vendorAnalysis.vendor_insights.top_vendors.slice(0, 3).map((vendor, index) => (
                      <div key={index} className="text-sm text-gray-600 flex items-center">
                        <div className="w-2 h-2 bg-purple-500 rounded-full mr-2" />
                        {vendor.vendor}: ${vendor.total_spent.toLocaleString()}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Analytics Summary */}
          {analyticsSummary && (
            <div className="mt-6 bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Analytics Summary</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Total Transactions:</span>
                  <span className="text-lg font-bold text-gray-900">
                    {analyticsSummary.overall_metrics.total_transactions.toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Overall Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Amount</span>
                      <span className="font-medium">${analyticsSummary.overall_metrics.total_amount.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Unique Vendors</span>
                      <span className="font-medium">{analyticsSummary.overall_metrics.unique_vendors}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Categories Used</span>
                      <span className="font-medium">{analyticsSummary.overall_metrics.categories_used}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Category Breakdown</h4>
                  <div className="space-y-2">
                    {analyticsSummary.category_breakdown.slice(0, 3).map((category, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-600">{category.category}</span>
                        <span className="font-medium">${category.total_amount.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Summary</h4>
                  <p className="text-sm text-gray-600">
                    Analytics data loaded successfully with comprehensive insights and trends.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default EnhancedAnalytics
