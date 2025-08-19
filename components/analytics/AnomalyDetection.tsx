'use client'

import React, { useState } from 'react'
import { 
  AlertTriangle, 
  AlertCircle, 
  Calendar,
  Filter,
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Clock,
  Shield,
  Eye
} from 'lucide-react'
import { useAnomalyDetection } from '@/hooks/useAnalytics'

interface AnomalyDetectionProps {
  className?: string
  startDate?: string
  endDate?: string
  onAnomalyClick?: (anomaly: any) => void
}

export default function AnomalyDetection({ 
  className = '',
  startDate,
  endDate,
  onAnomalyClick
}: AnomalyDetectionProps) {
  const [dateRange, setDateRange] = useState({
    start: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: endDate || new Date().toISOString().split('T')[0]
  })
  const [sensitivity, setSensitivity] = useState(2.0)

  const { data: anomalyData, isLoading, error, refetch } = useAnomalyDetection({
    start_date: dateRange.start,
    end_date: dateRange.end,
    threshold: sensitivity
  })

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    const newRange = { ...dateRange, [field]: value }
    setDateRange(newRange)
  }

  const handleSensitivityChange = (value: number) => {
    setSensitivity(value)
  }

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getRiskLevelIcon = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return <AlertTriangle className="w-5 h-5 text-red-600" />
      case 'medium':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />
      case 'low':
        return <Shield className="w-5 h-5 text-green-600" />
      default:
        return <Eye className="w-5 h-5 text-gray-600" />
    }
  }

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
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
          <h2 className="text-lg font-semibold">Anomaly Detection Error</h2>
        </div>
        <p className="text-gray-600 mb-4">Failed to load anomaly detection data</p>
        <button
          onClick={() => refetch()}
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
            <h2 className="text-xl font-semibold text-gray-900">Anomaly Detection</h2>
            <p className="text-sm text-gray-500">Identify unusual transactions and spending patterns</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
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

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Date Range Selector */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Date Range:</span>
            </div>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => handleDateChange('start', e.target.value)}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => handleDateChange('end', e.target.value)}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Sensitivity Slider */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Sensitivity:</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="5.0"
              step="0.5"
              value={sensitivity}
              onChange={(e) => handleSensitivityChange(parseFloat(e.target.value))}
              className="w-32"
            />
            <span className="text-sm font-medium text-gray-900">{sensitivity}</span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {anomalyData?.summary && (
        <div className="p-6 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-8 h-8 text-red-600" />
                <div>
                  <p className="text-sm font-medium text-red-800">High Risk</p>
                  <p className="text-2xl font-bold text-red-900">
                    {anomalyData.summary.high_risk_count || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-8 h-8 text-yellow-600" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">Medium Risk</p>
                  <p className="text-2xl font-bold text-yellow-900">
                    {anomalyData.summary.medium_risk_count || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center gap-3">
                <Shield className="w-8 h-8 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-800">Low Risk</p>
                  <p className="text-2xl font-bold text-green-900">
                    {anomalyData.summary.low_risk_count || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center gap-3">
                <DollarSign className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-800">Total Value</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {formatCurrency(anomalyData.summary.total_anomaly_value || 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Anomalies List */}
      <div className="p-6">
        {anomalyData?.anomalies && anomalyData.anomalies.length > 0 ? (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Detected Anomalies</h3>
            {anomalyData.anomalies
              .sort((a: any, b: any) => {
                const riskOrder = { high: 3, medium: 2, low: 1 }
                return (riskOrder[b.risk_level as keyof typeof riskOrder] || 0) - (riskOrder[a.risk_level as keyof typeof riskOrder] || 0)
              })
              .map((anomaly: any, index: number) => (
                <div 
                  key={index} 
                  className={`border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow ${getRiskLevelColor(anomaly.risk_level)}`}
                  onClick={() => onAnomalyClick?.(anomaly)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getRiskLevelIcon(anomaly.risk_level)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-medium text-gray-900">{anomaly.anomaly_type}</h4>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskLevelColor(anomaly.risk_level)}`}>
                            {anomaly.risk_level} Risk
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{anomaly.description}</p>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Amount:</span>
                            <span className="font-medium text-gray-900 ml-1">
                              {formatCurrency(anomaly.amount)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Date:</span>
                            <span className="font-medium text-gray-900 ml-1">
                              {new Date(anomaly.date).toLocaleDateString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Confidence:</span>
                            <span className="font-medium text-gray-900 ml-1">
                              {formatPercentage(anomaly.confidence_score)}
                            </span>
                          </div>
                        </div>

                        {anomaly.recommendations && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-sm text-gray-500 mb-1">Recommendations:</p>
                            <ul className="text-sm text-gray-700 space-y-1">
                              {anomaly.recommendations.map((rec: string, recIndex: number) => (
                                <li key={recIndex} className="flex items-start gap-2">
                                  <span className="text-blue-500 mt-1">•</span>
                                  <span>{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Anomalies Detected</h3>
            <p className="text-gray-500">
              Great! No unusual transactions or spending patterns were found in the selected period.
            </p>
          </div>
        )}

        {/* Risk Assessment */}
        {anomalyData?.risk_assessment && (
          <div className="mt-8 bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Overall Risk Level</h4>
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${getRiskLevelColor(anomalyData.risk_assessment.overall_risk_level)}`}>
                  {getRiskLevelIcon(anomalyData.risk_assessment.overall_risk_level)}
                  <span className="font-medium">{anomalyData.risk_assessment.overall_risk_level}</span>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Risk Score</h4>
                <p className="text-2xl font-bold text-gray-900">
                  {anomalyData.risk_assessment.risk_score?.toFixed(1) || 'N/A'}
                </p>
                <p className="text-sm text-gray-500">out of 100</p>
              </div>
            </div>

            {anomalyData.risk_assessment.recommendations && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="font-medium text-gray-900 mb-2">General Recommendations</h4>
                <ul className="text-sm text-gray-700 space-y-1">
                  {anomalyData.risk_assessment.recommendations.map((rec: string, index: number) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-500 mt-1">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
