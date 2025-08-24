'use client'

import React, { useState, useEffect } from 'react'
import { BarChart3, CheckCircle, Target, Brain, RefreshCw, XCircle } from 'lucide-react'
import { transactionAPI } from '@/lib/api'
import type { CategorizationPerformance } from '@/lib/api'

interface CategorizationPerformanceProps {
  className?: string
}

export default function CategorizationPerformance({ 
  className = '' 
}: CategorizationPerformanceProps) {
  const [performanceData, setPerformanceData] = useState<CategorizationPerformance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPerformanceData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await transactionAPI.getCategorizationPerformance({})
      setPerformanceData(response.data)
    } catch (err: any) {
      console.error('Failed to fetch performance data:', err)
      
      // For development/testing, provide mock data when API is not available
      if (process.env.NODE_ENV === 'development') {
        console.log('Using mock data for development')
        setPerformanceData({
          user_id: 1,
          period: {
            start_date: null,
            end_date: null
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
            }
          },
          improvement_trends: {
            daily_accuracy: [
              { date: '2025-08-15', accuracy: 0.89 },
              { date: '2025-08-16', accuracy: 0.91 }
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
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPerformanceData()
  }, [])

  const formatPercentage = (value: number | undefined | null) => {
    if (value === undefined || value === null) return '0.0%'
    return `${(value * 100).toFixed(1)}%`
  }
  const formatNumber = (value: number | undefined | null) => {
    if (value === undefined || value === null) return '0'
    return value.toLocaleString()
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

  const { overall_metrics } = performanceData || {}

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Categorization Performance</h2>
            <p className="text-sm text-gray-600 mt-1">
              Comprehensive metrics and insights for transaction categorization
            </p>
          </div>
          <button
            onClick={fetchPerformanceData}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            title="Refresh data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-700">Total Transactions</p>
                <p className="text-2xl font-bold text-blue-900">
                  {formatNumber(overall_metrics?.total_transactions)}
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
                  {formatNumber(overall_metrics?.categorized_count)}
                </p>
                <p className="text-sm text-green-600">
                  {formatPercentage(
                    overall_metrics?.total_transactions && overall_metrics?.categorized_count 
                      ? overall_metrics.categorized_count / overall_metrics.total_transactions 
                      : 0
                  )}
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
                  {formatPercentage(overall_metrics?.accuracy_rate)}
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-700">Avg Confidence</p>
                <p className="text-2xl font-bold text-orange-900">
                  {formatPercentage(overall_metrics?.average_confidence)}
                </p>
              </div>
              <Brain className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

