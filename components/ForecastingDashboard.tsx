'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  TrendingUp, 
  Calendar, 
  BarChart3, 
  Target, 
  AlertTriangle, 
  AlertCircle,
  CheckCircle, 
  Clock,
  RefreshCw,
  Settings,
  Download,
  Eye,
  EyeOff,
  Zap,
  Brain,
  TrendingDown
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Area, 
  ComposedChart,
  ReferenceLine,
  Legend
} from 'recharts'
import { forecastingAPI } from '@/lib/api'
import { 
  cardClasses, buttonClasses, badgeClasses, 
  cn, gradientClasses, textClasses, semantic,
  inputClasses, headerClasses, headerTitleClasses, headerDescClasses
} from '../lib/design-utils'
import type { 
  ForecastRequest, 
  ForecastResponse, 
  ForecastTypeInfo, 
  ForecastHorizonInfo,
  AccuracyHistoryResponse,
  EnsembleAnalysisResponse,
  MultiModelForecastRequest,
  MultiModelForecastResponse,
  ForecastModelInfo
} from '@/types/api'

// Multi-Model Forecast Chart Component
interface MultiModelForecastChartProps {
  data: MultiModelForecastResponse
  showConfidenceIntervals: boolean
}

function MultiModelForecastChart({ data, showConfidenceIntervals }: MultiModelForecastChartProps) {
  // Transform multi-model forecast data for Recharts
  const chartData = data.ensemble_predictions?.map((prediction, index) => {
    const point: any = {
      period: index + 1,
      date: prediction.date,
      ensemble: prediction.value,
      ensemble_lower: prediction.confidence_lower,
      ensemble_upper: prediction.confidence_upper,
    }

    // Add individual model predictions
    data.model_results.forEach(model => {
      if (model.predictions[index]) {
        point[model.model_name.toLowerCase().replace(' ', '_')] = model.predictions[index].value
      }
    })

    return point
  }) || []

  const formatValue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Model colors
  const modelColors = {
    prophet: '#3b82f6',      // Blue
    arima: '#ef4444',        // Red
    neuralprophet: '#10b981', // Green
    simple_trend: '#f59e0b',  // Yellow
    ensemble: '#8b5cf6'       // Purple
  }

  if (!chartData.length) {
    return (
      <div className="h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">No multi-model forecast data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis 
            tickFormatter={formatValue}
            stroke="#6b7280"
            fontSize={12}
          />
          <Tooltip
            labelFormatter={(label) => `Date: ${formatDate(label)}`}
            formatter={(value: number, name: string) => [
              formatValue(value),
              name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ')
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '12px'
            }}
          />
          <Legend />
          
          {/* Confidence interval area for ensemble */}
          {showConfidenceIntervals && (
            <Area
              type="monotone"
              dataKey="ensemble_upper"
              stroke="none"
              fill="#8b5cf6"
              fillOpacity={0.1}
            />
          )}
          {showConfidenceIntervals && (
            <Area
              type="monotone"
              dataKey="ensemble_lower"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
            />
          )}
          
          {/* Individual model lines */}
          {data.model_results.map((model) => {
            const modelKey = model.model_name.toLowerCase().replace(' ', '_')
            const color = (modelColors as any)[modelKey] || '#6b7280'
            
            return (
              <Line
                key={model.model_name}
                type="monotone"
                dataKey={modelKey}
                stroke={color}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 3, fill: color }}
                name={model.model_name}
              />
            )
          })}
          
          {/* Ensemble line (thicker, solid) */}
          <Line
            type="monotone"
            dataKey="ensemble"
            stroke={modelColors.ensemble}
            strokeWidth={4}
            dot={{ r: 5, fill: modelColors.ensemble }}
            activeDot={{ r: 7, fill: '#7c3aed' }}
            name="Ensemble"
          />
          
          {/* Zero line reference */}
          <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

// Fallback single-model chart for compatibility
interface ForecastChartProps {
  data: ForecastResponse
  showConfidenceIntervals: boolean
}

function ForecastChart({ data, showConfidenceIntervals }: ForecastChartProps) {
  // Transform forecast data for Recharts
  const chartData = data.predictions?.map((prediction, index) => ({
    period: index + 1,
    date: prediction.date,
    value: prediction.value,
    upperBound: prediction.confidence_upper || prediction.value * 1.1,
    lowerBound: prediction.confidence_lower || prediction.value * 0.9,
    confidence: data.confidence_score || 0
  })) || []

  const formatValue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  if (!chartData.length) {
    return (
      <div className="h-80 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">No forecast data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis 
            tickFormatter={formatValue}
            stroke="#6b7280"
            fontSize={12}
          />
          <Tooltip
            labelFormatter={(label) => `Date: ${formatDate(label)}`}
            formatter={(value: number, name: string) => [
              formatValue(value),
              name === 'value' ? 'Forecast' : 
              name === 'upperBound' ? 'Upper Bound' : 
              name === 'lowerBound' ? 'Lower Bound' : name
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '12px'
            }}
          />
          
          {/* Confidence interval areas */}
          {showConfidenceIntervals && (
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill="#3b82f6"
              fillOpacity={0.1}
            />
          )}
          {showConfidenceIntervals && (
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
            />
          )}
          
          {/* Main forecast line */}
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ r: 4, fill: '#3b82f6' }}
            activeDot={{ r: 6, fill: '#1d4ed8' }}
          />
          
          {/* Confidence interval lines */}
          {showConfidenceIntervals && (
            <Line
              type="monotone"
              dataKey="upperBound"
              stroke="#93c5fd"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
          {showConfidenceIntervals && (
            <Line
              type="monotone"
              dataKey="lowerBound"
              stroke="#93c5fd"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
          
          {/* Zero line reference */}
          <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

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
  const [isMultiModelMode, setIsMultiModelMode] = useState<boolean>(true)
  const [selectedModels, setSelectedModels] = useState<string[]>(['prophet', 'arima', 'neuralprophet', 'simple_trend'])
  const [forecastResult, setForecastResult] = useState<ForecastResponse | null>(null)
  const [multiModelResult, setMultiModelResult] = useState<MultiModelForecastResponse | null>(null)
  const [forecastError, setForecastError] = useState<string | null>(null)

  const queryClient = useQueryClient()

  // Fetch available forecast types
  const { data: forecastTypes, isLoading: typesLoading, error: typesError } = useQuery({
    queryKey: ['forecast-types'],
    queryFn: () => forecastingAPI.getForecastTypes(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Fetch available horizons
  const { data: horizons, isLoading: horizonsLoading, error: horizonsError } = useQuery({
    queryKey: ['forecast-horizons'],
    queryFn: () => forecastingAPI.getHorizons(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Fetch available models
  const { data: availableModelsResponse, isLoading: modelsLoading } = useQuery({
    queryKey: ['available-models'],
    queryFn: () => forecastingAPI.getAvailableModels(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
    retryDelay: 1000,
  })
  
  // Extract the data from the API response
  const availableModels: ForecastModelInfo[] = availableModelsResponse?.data || []

  // Fetch accuracy history - disabled due to CORS/backend issues
  const { data: accuracyHistory, isLoading: accuracyLoading, error: accuracyError } = useQuery({
    queryKey: ['forecast-accuracy'],
    queryFn: () => forecastingAPI.getAccuracyHistory({ days: 30 }),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
    retryDelay: 1000,
    enabled: false, // Disable until CORS is fixed
  })

  // Generate single-model forecast mutation
  const generateForecastMutation = useMutation({
    mutationFn: (data: ForecastRequest) => forecastingAPI.generateForecast(data),
    onSuccess: (response) => {
      const data = response.data  // Extract actual forecast data from Axios response
      queryClient.setQueryData(['forecast', data.forecast_id], data)
      
      // Defer state updates to avoid render phase warnings
      setTimeout(() => {
        setForecastResult(data)  // Store result in local state for immediate display
        setMultiModelResult(null) // Clear multi-model result when using single model
        setIsGenerating(false)
      }, 0)
    },
    onError: (error: any) => {
      console.error('Forecast generation failed:', error)
      
      // Extract error message from API response with better fallback handling
      let errorMessage = 'An unexpected error occurred while generating the forecast'
      
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error?.message) {
        errorMessage = error.message
      } else if (error?.response?.status === 400) {
        errorMessage = 'Invalid request parameters. Please check your configuration.'
      } else if (error?.response?.status >= 500) {
        errorMessage = 'Server error. Please try again later.'
      }
      
      setForecastError(errorMessage)
      setTimeout(() => {
        setIsGenerating(false)
      }, 0)
    },
  })

  // Generate multi-model forecast mutation
  const generateMultiModelForecastMutation = useMutation({
    mutationFn: (data: MultiModelForecastRequest) => forecastingAPI.generateMultiModelForecast(data),
    onSuccess: (response) => {
      const data = response.data  // Extract actual forecast data from Axios response
      queryClient.setQueryData(['multi-forecast', data.forecast_id], data)
      
      // Defer state updates to avoid render phase warnings
      setTimeout(() => {
        setMultiModelResult(data)  // Store result in local state for immediate display
        setForecastResult(null) // Clear single-model result when using multi-model
        setIsGenerating(false)
      }, 0)
    },
    onError: (error: any) => {
      console.error('Multi-model forecast generation failed:', error)
      
      // Extract error message from API response with better fallback handling
      let errorMessage = 'An unexpected error occurred while generating the multi-model forecast'
      
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error?.message) {
        errorMessage = error.message
      } else if (error?.response?.status === 400) {
        errorMessage = 'Invalid request parameters. Please check your model selection and configuration.'
      } else if (error?.response?.status >= 500) {
        errorMessage = 'Server error. Please try again later.'
      }
      
      setForecastError(errorMessage)
      setTimeout(() => {
        setIsGenerating(false)
      }, 0)
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
    setIsGenerating(true)
    setForecastResult(null) // Clear previous results
    setMultiModelResult(null) // Clear previous multi-model results
    setForecastError(null) // Clear previous errors
    
    if (isMultiModelMode) {
      const request: MultiModelForecastRequest = {
        forecast_type: selectedForecastType as any,
        horizon: selectedHorizon as any,
        custom_days: selectedHorizon === 'custom' ? customDays : undefined,
        category_filter: categoryFilter || undefined,
        confidence_level: confidenceLevel,
        models: selectedModels as any,
      }
      generateMultiModelForecastMutation.mutate(request)
    } else {
      const request: ForecastRequest = {
        forecast_type: selectedForecastType as any,
        horizon: selectedHorizon as any,
        custom_days: selectedHorizon === 'custom' ? customDays : undefined,
        category_filter: categoryFilter || undefined,
        confidence_level: confidenceLevel,
      }
      generateForecastMutation.mutate(request)
    }
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['forecast-accuracy'] })
    queryClient.invalidateQueries({ queryKey: ['forecast-types'] })
    queryClient.invalidateQueries({ queryKey: ['forecast-horizons'] })
  }

  if (typesLoading || horizonsLoading || modelsLoading) {
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
  const backendNotReady = false // Backend Task B4.1 is implemented and available
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
                            className="bg-brand-gradient text-white px-6 py-2 rounded-md transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 disabled:opacity-50"
            disabled
          >
            Generate Forecast (Backend Required)
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className={headerClasses('clean')}>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-brand-primary/10 border border-brand-primary/20 rounded-2xl flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-brand-primary" />
          </div>
          <div>
            <h2 className={headerTitleClasses('2xl')}>
              Cash Flow Forecasting
            </h2>
            <p className={headerDescClasses('default')}>
              AI-powered predictions with multi-model ensemble intelligence
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMultiModelMode(!isMultiModelMode)}
            className={cn(
              buttonClasses(isMultiModelMode ? 'primary' : 'secondary', 'sm')
            )}
          >
              {isMultiModelMode ? <Brain className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
              {isMultiModelMode ? 'Multi-Model' : 'Single Model'}
          </button>
          <button
            onClick={handleRefresh}
            className={cn(
              buttonClasses('secondary', 'sm'),
              isGenerating ? 'opacity-50' : ''
            )}
            disabled={isGenerating}
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowConfidenceIntervals(!showConfidenceIntervals)}
            className={cn(
              buttonClasses('secondary', 'sm')
            )}
          >
              {showConfidenceIntervals ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {showConfidenceIntervals ? 'Hide' : 'Show'} Confidence
            </button>
          </div>
        </div>
      </div>

      {/* Forecast Configuration */}
      <div className={cardClasses('elevated', 'p-6')}>
        <h3 className={cn(textClasses.size('lg'), textClasses.weight('semibold'), semantic.text.primary, 'mb-6')}>
          Forecast Configuration
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Forecast Type */}
          <div>
            <label htmlFor="forecast-type" className={cn(textClasses.size('sm'), textClasses.weight('medium'), semantic.text.secondary, 'block mb-2')}>
              Forecast Type
            </label>
            <select
              id="forecast-type"
              value={selectedForecastType}
              onChange={(e) => setSelectedForecastType(e.target.value)}
              className={inputClasses('default')}
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
            <label htmlFor="forecast-horizon" className={cn(textClasses.size('sm'), textClasses.weight('medium'), semantic.text.secondary, 'block mb-2')}>
              Forecast Horizon
            </label>
            <select
              id="forecast-horizon"
              value={selectedHorizon}
              onChange={(e) => setSelectedHorizon(e.target.value)}
              className={inputClasses('default')}
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
              <label htmlFor="custom-days" className={cn(textClasses.size('sm'), textClasses.weight('medium'), semantic.text.secondary, 'block mb-2')}>
                Custom Days
              </label>
              <input
                id="custom-days"
                type="number"
                value={customDays}
                onChange={(e) => setCustomDays(parseInt(e.target.value) || 30)}
                min="1"
                max="365"
                className={inputClasses('default')}
              />
            </div>
          )}

          {/* Category Filter */}
          <div>
            <label htmlFor="category-filter" className={cn(textClasses.size('sm'), textClasses.weight('medium'), semantic.text.secondary, 'block mb-2')}>
              Category Filter (Optional)
            </label>
            <input
              id="category-filter"
              type="text"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              placeholder="e.g., Food, Transport"
              className={inputClasses('default')}
            />
          </div>
        </div>

        {/* Confidence Level */}
        <div className="mt-6">
          <label htmlFor="confidence-level" className={cn(textClasses.size('sm'), textClasses.weight('medium'), semantic.text.secondary, 'block mb-3')}>
            Confidence Level: <span className="text-brand-primary font-semibold">{Math.round(confidenceLevel * 100)}%</span>
          </label>
          <input
            id="confidence-level"
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={confidenceLevel}
            onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-brand-primary"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>50%</span>
            <span>75%</span>
            <span>90%</span>
            <span>99%</span>
          </div>
        </div>

        {/* Model Selection (only for multi-model mode) */}
        {isMultiModelMode && (
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Models to Compare
            </label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {availableModels.map((model) => (
                <div key={model.model} className="relative">
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedModels.includes(model.model)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedModels([...selectedModels, model.model])
                        } else {
                          setSelectedModels(selectedModels.filter(m => m !== model.model))
                        }
                      }}
                      className="form-checkbox h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{model.name}</div>
                      <div className="text-xs text-gray-500">{model.best_for}</div>
                    </div>
                  </label>
                </div>
              ))}
            </div>
            {selectedModels.length === 0 && (
              <p className="text-sm text-red-500 mt-2">
                Please select at least one model for comparison.
              </p>
            )}
          </div>
        )}

        {/* Generate Button */}
        <div className="mt-6">
          <button
            onClick={handleGenerateForecast}
            disabled={isGenerating || (isMultiModelMode && selectedModels.length === 0)}
            className={cn(
              buttonClasses('gradient', 'lg'),
              'w-full sm:w-auto',
              (isGenerating || (isMultiModelMode && selectedModels.length === 0)) ? 'opacity-50 cursor-not-allowed' : ''
            )}
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                {isMultiModelMode ? 'Generating Multi-Model Forecast...' : 'Generating Forecast...'}
              </>
            ) : (
              <>
                {isMultiModelMode ? <Brain className="w-4 h-4" /> : <Target className="w-4 h-4" />}
                {isMultiModelMode ? 'Generate Multi-Model Forecast' : 'Generate Forecast'}
              </>
            )}
          </button>
          {isMultiModelMode && selectedModels.length === 0 && (
            <p className={cn(textClasses.size('sm'), 'text-red-500 mt-3')}>
              Please select at least one model to generate forecasts.
            </p>
          )}
        </div>
      </div>

      {/* Error Display */}
      {forecastError && (
        <div className={cn(cardClasses('default'), 'p-6 bg-red-50 border-red-200')}>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className={cn(textClasses.weight('medium'), 'text-red-800 mb-2')}>
                Forecast Generation Failed
              </h4>
              <p className={cn(textClasses.size('sm'), 'text-red-700 mb-4')}>
                {forecastError || 'An unknown error occurred. Please try again.'}
              </p>
              
              {forecastError && forecastError.toLowerCase().includes('insufficient historical data') && (
                <div className={cn(textClasses.size('sm'), 'text-red-600 mb-4')}>
                  <p className={cn(textClasses.weight('medium'), 'mb-2')}>
                    Suggestions to resolve this issue:
                  </p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>Upload more transaction data (recommended: 3+ months)</li>
                    <li>Try a shorter forecast horizon (7 or 30 days)</li>
                    <li>Use single-model mode instead of multi-model</li>
                    <li>Remove category filters to include more data</li>
                  </ul>
                </div>
              )}
              
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setForecastError(null)}
                  className={cn(
                    buttonClasses('secondary', 'sm'),
                    'text-red-700 border-red-300 hover:bg-red-100'
                  )}
                >
                  Dismiss
                </button>
                
                {forecastError && forecastError.toLowerCase().includes('insufficient historical data') && (
                  <button
                    onClick={() => setIsMultiModelMode(false)}
                    className={cn(
                      buttonClasses('primary', 'sm'),
                      'bg-red-600 hover:bg-red-700 border-red-600'
                    )}
                  >
                    Try Single Model
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Model Forecast Results */}
      {multiModelResult && (
        <div className={cardClasses('elevated', 'p-6')}>
          <div className="flex items-center justify-between mb-6">
            <h3 className={cn(textClasses.size('lg'), textClasses.weight('semibold'), semantic.text.primary)}>
              Multi-Model Forecast Results
            </h3>
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-brand-accent" />
                <span className={semantic.text.secondary}>
                  Ensemble Accuracy: <span className="text-brand-primary font-semibold">{Math.round((multiModelResult.ensemble_accuracy || 0) * 100)}%</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-brand-primary" />
                <span className={semantic.text.secondary}>
                  Best Model: <span className="text-brand-primary font-semibold">{multiModelResult.best_model}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-green-500" />
                <span className={semantic.text.secondary}>
                  Models: <span className="text-brand-primary font-semibold">{multiModelResult.model_results.length}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Multi-Model Forecast Chart */}
          <MultiModelForecastChart 
            data={multiModelResult} 
            showConfidenceIntervals={showConfidenceIntervals}
          />

          {/* Model Performance Comparison */}
          <div className="mt-8">
            <h4 className={cn(textClasses.size('base'), textClasses.weight('semibold'), semantic.text.primary, 'mb-4')}>
              Model Performance Comparison
            </h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4">
              {multiModelResult.model_results.map((model) => (
                <div key={model.model_name} className={cardClasses('interactive', 'p-4')}>
                  <div className="flex items-center justify-between mb-3">
                    <h5 className={cn(textClasses.weight('medium'), semantic.text.primary)}>
                      {model.model_name}
                    </h5>
                    <span className={cn(
                      badgeClasses(model.model_name === multiModelResult.best_model ? 'success' : 'neutral')
                    )}>
                      {model.model_name === multiModelResult.best_model ? 'Best' : 'Good'}
                    </span>
                  </div>
                  <div className={cn('space-y-2', textClasses.size('sm'))}>
                    <div className="flex justify-between">
                      <span className={semantic.text.muted}>Accuracy:</span>
                      <span className={cn(textClasses.weight('semibold'), 'text-brand-primary')}>
                        {Math.round(model.accuracy * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className={semantic.text.muted}>MAE:</span>
                      <span className={cn(textClasses.weight('semibold'), semantic.text.primary)}>
                        ${model.mae.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className={semantic.text.muted}>Pattern:</span>
                      <span className={cn(textClasses.weight('medium'), semantic.text.secondary, 'capitalize')}>
                        {model.seasonal_pattern}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className={semantic.text.muted}>Trend:</span>
                      <span className={cn(textClasses.weight('medium'), semantic.text.secondary, 'capitalize')}>
                        {model.trend_direction}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Ensemble Summary */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-purple-50 p-4 rounded-lg">
              <h4 className="font-medium text-purple-900">Ensemble Prediction</h4>
              <p className="text-2xl font-bold text-purple-600">
                ${multiModelResult.ensemble_predictions?.reduce((sum, p) => sum + p.value, 0)?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900">Best Model</h4>
              <p className="text-2xl font-bold text-blue-600">
                {multiModelResult.best_model}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900">Data Points</h4>
              <p className="text-2xl font-bold text-green-600">
                {multiModelResult.metadata?.data_points || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Single-Model Forecast Results */}
      {forecastResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Forecast Results</h3>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Confidence: {Math.round((forecastResult.confidence_score || 0) * 100)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <BarChart3 className="w-4 h-4 text-blue-500" />
                <span>Accuracy: {Math.round((forecastResult.model_accuracy || 0) * 100)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-purple-500" />
                <span>Pattern: {forecastResult.seasonal_pattern || 'Unknown'}</span>
              </div>
            </div>
          </div>

          {/* Single-Model Forecast Chart */}
          <ForecastChart 
            data={forecastResult} 
            showConfidenceIntervals={showConfidenceIntervals}
          />

          {/* Forecast Summary */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900">Trend Direction</h4>
              <p className="text-2xl font-bold text-blue-600 capitalize">
                {forecastResult.trend_direction || 'Unknown'}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900">Total Predicted</h4>
              <p className="text-2xl font-bold text-green-600">
                ${forecastResult.predictions?.reduce((sum, p) => sum + p.value, 0)?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h4 className="font-medium text-purple-900">Data Points</h4>
              <p className="text-2xl font-bold text-purple-600">
                {forecastResult.metadata?.data_points || 'N/A'}
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
                {Math.round((accuracyHistory.data?.average_accuracy || 0) * 100)}%
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Forecasts Generated</h4>
              <p className="text-2xl font-bold text-gray-600">
                {accuracyHistory.data?.forecast_count || 0}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Accuracy Trend</h4>
              <p className="text-2xl font-bold text-gray-600 capitalize">
                {accuracyHistory.data?.accuracy_trend || 'stable'}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900">Best Type</h4>
              <p className="text-2xl font-bold text-gray-600 capitalize">
                {(accuracyHistory.data?.best_forecast_type || 'ensemble').replace('_', ' ')}
              </p>
            </div>
          </div>

          {/* Accuracy by Horizon */}
          <div className="mt-6">
            <h4 className="font-medium text-gray-900 mb-3">Accuracy by Horizon</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(accuracyHistory.data?.accuracy_by_horizon || {}).map(([horizon, accuracy]) => (
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

    </div>
  )
}
