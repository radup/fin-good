'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  TrendingUp, 
  Calendar, 
  BarChart3, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  Settings,
  Download,
  Eye,
  EyeOff
} from 'lucide-react'
import { forecastingAPI } from '@/lib/api'
import type { 
  ForecastRequest, 
  ForecastResponse, 
  ForecastTypeInfo, 
  ForecastHorizonInfo,
  AccuracyHistoryResponse,
  EnsembleAnalysisResponse
} from '@/types/api'

interface ForecastingDashboardProps {
  className?: string
}

export function ForecastingDashboard({ className = '' }: ForecastingDashboardProps) {
  const [selectedForecastType, setSelectedForecastType] = useState<string>('cash_flow')
  const [selectedHorizon, setSelectedHorizon] = useState<string>('30_days')
  const [customDays, setCustomDays] = useState<number>(30)
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95)
  const [showConfidenceIntervals, setShowConfidenceIntervals] = useState<boolean>(true)
  const [isGenerating, setIsGenerating] = useState<boolean>(false)

  const queryClient = useQueryClient()

  // Fetch available forecast types
  const { data: forecastTypes, isLoading: typesLoading, error: typesError } = useQuery({
    queryKey: ['forecast-types'],
    queryFn: () => forecastingAPI.getForecastTypes(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
    enabled: false, // Disable until backend is ready
  })

  // Fetch available horizons
  const { data: horizons, isLoading: horizonsLoading, error: horizonsError } = useQuery({
    queryKey: ['forecast-horizons'],
    queryFn: () => forecastingAPI.getHorizons(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
    enabled: false, // Disable until backend is ready
  })

  // Fetch accuracy history
  const { data: accuracyHistory, isLoading: accuracyLoading, error: accuracyError } = useQuery({
    queryKey: ['forecast-accuracy'],
    queryFn: () => forecastingAPI.getAccuracyHistory({ days: 30 }),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
    retryDelay: 1000,
    enabled: false, // Disable until backend is ready
  })

  // Generate forecast mutation
  const generateForecastMutation = useMutation({
    mutationFn: (data: ForecastRequest) => forecastingAPI.generateForecast(data),
    onSuccess: (data) => {
      queryClient.setQueryData(['forecast', data.forecast_id], data)
      setIsGenerating(false)
    },
    onError: (error) => {
      console.error('Forecast generation failed:', error)
      setIsGenerating(false)
    },
  })

  // Get latest forecast
  const { data: latestForecast, isLoading: forecastLoading } = useQuery({
    queryKey: ['latest-forecast', selectedForecastType, selectedHorizon, categoryFilter],
    queryFn: () => {
      const request: ForecastRequest = {
        forecast_type: selectedForecastType as any,
        horizon: selectedHorizon as any,
        custom_days: selectedHorizon === 'custom' ? customDays : undefined,
        category_filter: categoryFilter || undefined,
        confidence_level: confidenceLevel,
      }
      return forecastingAPI.generateForecast(request)
    },
    enabled: false, // Don't auto-fetch, only on demand
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const handleGenerateForecast = () => {
    // Disabled until backend is ready
    console.log('Forecast generation disabled - backend not implemented yet')
    return
  }

  const handleRefresh = () => {
    // Disabled until backend is ready
    console.log('Refresh disabled - backend not implemented yet')
    return
  }

  if (typesLoading || horizonsLoading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-4">
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  // Show backend not ready message - since queries are disabled, backend is not ready
  const backendNotReady = true // TODO: Change to false when backend Task B4.1 is implemented
  if (backendNotReady) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Cash Flow Forecasting</h2>
              <p className="text-gray-600">ML-powered predictions with confidence intervals</p>
            </div>
          </div>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-yellow-600" />
            <div>
              <h3 className="text-lg font-semibold text-yellow-800">Backend Not Ready</h3>
              <p className="text-yellow-700 mt-1">
                The forecasting backend is not yet implemented. This is a frontend demo with mock data.
              </p>
              <p className="text-yellow-600 text-sm mt-2">
                Backend Task B4.1 (Predictive Analytics System) needs to be completed first.
              </p>
            </div>
          </div>
        </div>

        {/* Show demo interface with mock data */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Demo Interface</h3>
          <p className="text-gray-600 mb-4">
            This shows how the interface will look when the backend is implemented.
          </p>
          
          {/* Demo form */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Forecast Type
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="cash_flow">Cash Flow Forecasting</option>
                <option value="spending">Spending Forecasting</option>
                <option value="revenue">Revenue Forecasting</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Forecast Horizon
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="7_days">7 Days</option>
                <option value="30_days">30 Days</option>
                <option value="60_days">60 Days</option>
                <option value="90_days">90 Days</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category Filter
              </label>
              <input
                type="text"
                placeholder="e.g., Food, Transport"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confidence Level: 85%
              </label>
              <input
                type="range"
                min="0.5"
                max="0.99"
                step="0.01"
                defaultValue="0.85"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
          
          <button
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled
          >
            Generate Forecast (Backend Required)
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Cash Flow Forecasting</h2>
            <p className="text-gray-600">ML-powered predictions with confidence intervals</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
            disabled={isGenerating}
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowConfidenceIntervals(!showConfidenceIntervals)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
          >
            {showConfidenceIntervals ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showConfidenceIntervals ? 'Hide' : 'Show'} Confidence
          </button>
        </div>
      </div>

      {/* Forecast Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Forecast Type */}
          <div>
            <label htmlFor="forecast-type" className="block text-sm font-medium text-gray-700 mb-2">
              Forecast Type
            </label>
            <select
              id="forecast-type"
              value={selectedForecastType}
              onChange={(e) => setSelectedForecastType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Array.isArray(forecastTypes) ? forecastTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              )) : (
                <>
                  <option value="cash_flow">Cash Flow Forecasting</option>
                  <option value="spending">Spending Forecasting</option>
                  <option value="revenue">Revenue Forecasting</option>
                </>
              )}
            </select>
          </div>

          {/* Horizon */}
          <div>
            <label htmlFor="forecast-horizon" className="block text-sm font-medium text-gray-700 mb-2">
              Forecast Horizon
            </label>
            <select
              id="forecast-horizon"
              value={selectedHorizon}
              onChange={(e) => setSelectedHorizon(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Array.isArray(horizons) ? horizons.map((horizon) => (
                <option key={horizon.value} value={horizon.value}>
                  {horizon.label}
                </option>
              )) : (
                <>
                  <option value="7_days">7 Days</option>
                  <option value="30_days">30 Days</option>
                  <option value="60_days">60 Days</option>
                  <option value="90_days">90 Days</option>
                  <option value="custom">Custom</option>
                </>
              )}
            </select>
          </div>

          {/* Custom Days */}
          {selectedHorizon === 'custom' && (
            <div>
              <label htmlFor="custom-days" className="block text-sm font-medium text-gray-700 mb-2">
                Custom Days
              </label>
              <input
                id="custom-days"
                type="number"
                value={customDays}
                onChange={(e) => setCustomDays(parseInt(e.target.value) || 30)}
                min="1"
                max="365"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Category Filter */}
          <div>
            <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Category Filter (Optional)
            </label>
            <input
              id="category-filter"
              type="text"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              placeholder="e.g., Food, Transport"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Confidence Level */}
        <div className="mt-4">
          <label htmlFor="confidence-level" className="block text-sm font-medium text-gray-700 mb-2">
            Confidence Level: {Math.round(confidenceLevel * 100)}%
          </label>
          <input
            id="confidence-level"
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={confidenceLevel}
            onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>50%</span>
            <span>75%</span>
            <span>90%</span>
            <span>99%</span>
          </div>
        </div>

        {/* Generate Button */}
        <div className="mt-6">
          <button
            onClick={handleGenerateForecast}
            disabled={isGenerating}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Generating Forecast...
              </>
            ) : (
              <>
                <Target className="w-4 h-4" />
                Generate Forecast
              </>
            )}
          </button>
        </div>
      </div>

      {/* Forecast Results */}
      {latestForecast && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Forecast Results</h3>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Confidence: {Math.round(latestForecast.confidence_score * 100)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <BarChart3 className="w-4 h-4 text-blue-500" />
                <span>Accuracy: {Math.round(latestForecast.model_accuracy * 100)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-purple-500" />
                <span>Pattern: {latestForecast.seasonal_pattern}</span>
              </div>
            </div>
          </div>

          {/* Forecast Chart Placeholder */}
          <div className="h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">Forecast visualization will be implemented here</p>
              <p className="text-sm text-gray-400">Showing {latestForecast.predictions.length} prediction points</p>
            </div>
          </div>

          {/* Forecast Summary */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900">Trend Direction</h4>
              <p className="text-2xl font-bold text-blue-600 capitalize">
                {latestForecast.trend_direction}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900">Total Predicted</h4>
              <p className="text-2xl font-bold text-green-600">
                ${latestForecast.predictions.reduce((sum, p) => sum + p.value, 0).toFixed(2)}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h4 className="font-medium text-purple-900">Data Points</h4>
              <p className="text-2xl font-bold text-purple-600">
                {latestForecast.metadata.data_points}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Accuracy History */}
      {accuracyHistory && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Accuracy History</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Average Accuracy</h4>
              <p className="text-2xl font-bold text-gray-600">
                {Math.round(accuracyHistory.average_accuracy * 100)}%
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Forecasts Generated</h4>
              <p className="text-2xl font-bold text-gray-600">
                {accuracyHistory.forecast_count}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Accuracy Trend</h4>
              <p className="text-2xl font-bold text-gray-600 capitalize">
                {accuracyHistory.accuracy_trend}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Best Type</h4>
              <p className="text-2xl font-bold text-gray-600 capitalize">
                {accuracyHistory.best_forecast_type.replace('_', ' ')}
              </p>
            </div>
          </div>

          {/* Accuracy by Horizon */}
          <div className="mt-6">
            <h4 className="font-medium text-gray-900 mb-3">Accuracy by Horizon</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(accuracyHistory.accuracy_by_horizon).map(([horizon, accuracy]) => (
                <div key={horizon} className="bg-blue-50 p-3 rounded-lg">
                  <h5 className="text-sm font-medium text-blue-900 capitalize">
                    {horizon.replace('_', ' ')}
                  </h5>
                  <p className="text-xl font-bold text-blue-600">
                    {Math.round(accuracy * 100)}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {generateForecastMutation.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <h3 className="font-medium text-red-900">Forecast Generation Failed</h3>
          </div>
          <p className="text-red-700 mt-1">
            {generateForecastMutation.error instanceof Error 
              ? generateForecastMutation.error.message 
              : 'An unexpected error occurred while generating the forecast.'
            }
          </p>
        </div>
      )}
    </div>
  )
}
