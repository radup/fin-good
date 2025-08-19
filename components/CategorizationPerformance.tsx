'use client'

import React, { useState, useEffect } from 'react'
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Users, 
  Brain,
  Activity,
  PieChart,
  Calendar,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react'
import { transactionAPI, CategorizationPerformance } from '@/lib/api'

interface CategorizationPerformanceProps {
  className?: string
}

export default function CategorizationPerformance({ 
  className = '' 
}: CategorizationPerformanceProps) {
  const [performanceData, setPerformanceData] = useState<CategorizationPerformance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState<{
    start_date?: string
    end_date?: string
  }>({})

  const fetchPerformanceData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await transactionAPI.getCategorizationPerformance(dateRange)
      setPerformanceData(response.data)
    } catch (err: any) {
      console.error('Failed to fetch performance data:', err)
      
      // Handle different types of errors
      if (err.response?.status === 401) {
        setError('Authentication required. Please log in.')
      } else if (err.response?.status === 403) {
        setError('Access denied. You do not have permission to view this data.')
      } else if (err.response?.status === 404) {
        setError('Performance data not found for the selected date range.')
      } else if (err.response?.status === 429) {
        setError('Rate limit exceeded. Please try again later.')
      } else if (err.response?.status >= 500) {
        setError('Server error. Please try again later.')
      } else {
        // For development/testing, provide mock data when API is not available
        if (process.env.NODE_ENV === 'development') {
          console.log('Using mock data for development')
          setPerformanceData({
            user_id: 1,
            period: {
              start_date: dateRange.start_date || null,
              end_date: dateRange.end_date || null
            },
            overall_metrics: {
              total_transactions: 1250,
              categorized_count: 1180,
              accuracy_rate: 0.92,
              average_confidence: 0.85,
              success_rate: 0.94
            },
            method_breakdown: {
              rule_based: {
                count: 650,
                accuracy: 0.95,
                average_confidence: 0.90
              },
              ml_based: {
                count: 530,
                accuracy: 0.88,
                average_confidence: 0.78
              }
            },
            confidence_distribution: {
              high_confidence: 850,
              medium_confidence: 280,
              low_confidence: 120
            },
            category_performance: {
              'Food & Dining': {
                count: 180,
                accuracy: 0.95,
                average_confidence: 0.92
              },
              'Transportation': {
                count: 150,
                accuracy: 0.88,
                average_confidence: 0.85
              },
              'Shopping': {
                count: 200,
                accuracy: 0.90,
                average_confidence: 0.87
              },
              'Utilities': {
                count: 120,
                accuracy: 0.98,
                average_confidence: 0.95
              },
              'Entertainment': {
                count: 80,
                accuracy: 0.85,
                average_confidence: 0.80
              }
            },
            improvement_trends: {
              daily_accuracy: [
                { date: '2025-08-15', accuracy: 0.89 },
                { date: '2025-08-16', accuracy: 0.91 },
                { date: '2025-08-17', accuracy: 0.92 },
                { date: '2025-08-18', accuracy: 0.93 },
                { date: '2025-08-19', accuracy: 0.92 }
              ],
              weekly_improvement: 0.03
            },
            feedback_analysis: {
              total_feedback: 45,
              positive_feedback: 38,
              negative_feedback: 7,
              feedback_accuracy: 0.84
            }
          })
          return
        }
        
        setError(err.response?.data?.detail || 'Failed to load performance data')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPerformanceData()
  }, [dateRange])

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`
  const formatNumber = (value: number) => value.toLocaleString()

  const getPerformanceColor = (value: number, threshold: number) => {
    if (value >= threshold) return 'text-green-600'
    if (value >= threshold * 0.8) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getPerformanceIcon = (value: number, threshold: number) => {
    if (value >= threshold) return <TrendingUp className="w-4 h-4 text-green-600" />
    if (value >= threshold * 0.8) return <Target className="w-4 h-4 text-yellow-600" />
    return <TrendingDown className="w-4 h-4 text-red-600" />
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-gray-600">Loading performance data...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Data</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={fetchPerformanceData}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!performanceData) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Performance Data</h3>
            <p className="text-gray-600">No categorization performance data available.</p>
          </div>
        </div>
      </div>
    )
  }

  const { overall_metrics, method_breakdown, confidence_distribution, category_performance, improvement_trends, feedback_analysis } = performanceData

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Categorization Performance</h2>
            <p className="text-sm text-gray-600 mt-1">
              Comprehensive metrics and insights for transaction categorization
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchPerformanceData}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              title="Export data"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Date Range:</span>
          </div>
          <input
            type="date"
            value={dateRange.start_date || ''}
            onChange={(e) => setDateRange(prev => ({ ...prev, start_date: e.target.value }))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          />
          <span className="text-gray-500">to</span>
          <input
            type="date"
            value={dateRange.end_date || ''}
            onChange={(e) => setDateRange(prev => ({ ...prev, end_date: e.target.value }))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          />
          <button
            onClick={() => setDateRange({})}
            className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Overall Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-700">Total Transactions</p>
                <p className="text-2xl font-bold text-blue-900">
                  {formatNumber(overall_metrics.total_transactions)}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-700">Categorized</p>
                <p className="text-2xl font-bold text-green-900">
                  {formatNumber(overall_metrics.categorized_count)}
                </p>
                <p className="text-sm text-green-600">
                  {formatPercentage(overall_metrics.categorized_count / overall_metrics.total_transactions)}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700">Accuracy Rate</p>
                <p className="text-2xl font-bold text-purple-900">
                  {formatPercentage(overall_metrics.accuracy_rate)}
                </p>
                <div className="flex items-center mt-1">
                  {getPerformanceIcon(overall_metrics.accuracy_rate, 0.9)}
                  <span className={`text-sm ml-1 ${getPerformanceColor(overall_metrics.accuracy_rate, 0.9)}`}>
                    {overall_metrics.accuracy_rate >= 0.9 ? 'Excellent' : 
                     overall_metrics.accuracy_rate >= 0.8 ? 'Good' : 'Needs Improvement'}
                  </span>
                </div>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-700">Avg Confidence</p>
                <p className="text-2xl font-bold text-orange-900">
                  {formatPercentage(overall_metrics.average_confidence)}
                </p>
                <div className="flex items-center mt-1">
                  {getPerformanceIcon(overall_metrics.average_confidence, 0.8)}
                  <span className={`text-sm ml-1 ${getPerformanceColor(overall_metrics.average_confidence, 0.8)}`}>
                    {overall_metrics.average_confidence >= 0.8 ? 'High' : 
                     overall_metrics.average_confidence >= 0.6 ? 'Medium' : 'Low'}
                  </span>
                </div>
              </div>
              <Brain className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>

        {/* Method Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-600" />
              Method Breakdown
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                  <span className="font-medium text-gray-900">Rule-Based</span>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">{formatNumber(method_breakdown.rule_based.count)}</p>
                  <p className="text-sm text-gray-600">{formatPercentage(method_breakdown.rule_based.accuracy)} accuracy</p>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                  <span className="font-medium text-gray-900">ML-Based</span>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">{formatNumber(method_breakdown.ml_based.count)}</p>
                  <p className="text-sm text-gray-600">{formatPercentage(method_breakdown.ml_based.accuracy)} accuracy</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <PieChart className="w-5 h-5 mr-2 text-purple-600" />
              Confidence Distribution
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">High Confidence (≥80%)</span>
                <span className="font-semibold text-green-600">{formatNumber(confidence_distribution.high_confidence)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${(confidence_distribution.high_confidence / overall_metrics.total_transactions) * 100}%` }}
                ></div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Medium Confidence (60-79%)</span>
                <span className="font-semibold text-yellow-600">{formatNumber(confidence_distribution.medium_confidence)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-yellow-500 h-2 rounded-full" 
                  style={{ width: `${(confidence_distribution.medium_confidence / overall_metrics.total_transactions) * 100}%` }}
                ></div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Low Confidence (<60%)</span>
                <span className="font-semibold text-red-600">{formatNumber(confidence_distribution.low_confidence)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full" 
                  style={{ width: `${(confidence_distribution.low_confidence / overall_metrics.total_transactions) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Category Performance */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2 text-indigo-600" />
            Category Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transactions</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Accuracy</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Confidence</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(category_performance).map(([category, data]) => (
                  <tr key={category} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(data.count)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={getPerformanceColor(data.accuracy, 0.9)}>
                        {formatPercentage(data.accuracy)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={getPerformanceColor(data.average_confidence, 0.8)}>
                        {formatPercentage(data.average_confidence)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Feedback Analysis */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Brain className="w-5 h-5 mr-2 text-teal-600" />
            Feedback Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{formatNumber(feedback_analysis.positive_feedback)}</p>
              <p className="text-sm text-green-700">Positive Feedback</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{formatNumber(feedback_analysis.negative_feedback)}</p>
              <p className="text-sm text-red-700">Negative Feedback</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{formatPercentage(feedback_analysis.feedback_accuracy)}</p>
              <p className="text-sm text-blue-700">Feedback Accuracy</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
