'use client'

import { useState } from 'react'
import { 
  LineChart as RechartsLineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { 
  TrendingUp,
  TrendingDown,
  Calendar,
  BarChart3,
  LineChart,
  PieChart,
  Target,
  AlertTriangle,
  CheckCircle,
  Info,
  Zap,
  Brain,
  Activity,
  DollarSign,
  ArrowUp,
  ArrowDown,
  Clock,
  Users,
  Building
} from 'lucide-react'

interface ForecastData {
  date: string
  actual?: number
  prophet_forecast: number
  xgboost_adjustment: number
  ensemble_prediction: number
  lower_bound: number
  upper_bound: number
  confidence: number
  seasonal_component: number
  trend_component: number
}

interface ModelMetrics {
  model: 'prophet' | 'xgboost' | 'ensemble'
  mape: number
  rmse: number
  mae: number
  confidence: number
  lastTrained: string
}

export default function CashFlowForecastingDashboard() {
  const [timeHorizon, setTimeHorizon] = useState<'1month' | '3months' | '6months' | '1year'>('3months')
  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'expenses' | 'net_cash'>('net_cash')
  const [showConfidenceIntervals, setShowConfidenceIntervals] = useState(true)
  const [selectedModel, setSelectedModel] = useState<'prophet' | 'xgboost' | 'ensemble'>('ensemble')

  // Mock data - in real implementation this would come from the forecasting engine
  const forecastData: ForecastData[] = [
    {
      date: '2024-09-01',
      actual: 42000,
      prophet_forecast: 41500,
      xgboost_adjustment: 500,
      ensemble_prediction: 42000,
      lower_bound: 38000,
      upper_bound: 46000,
      confidence: 0.92,
      seasonal_component: 2000,
      trend_component: 40000
    },
    {
      date: '2024-10-01',
      actual: 48000,
      prophet_forecast: 47500,
      xgboost_adjustment: 500,
      ensemble_prediction: 48000,
      lower_bound: 44000,
      upper_bound: 52000,
      confidence: 0.89,
      seasonal_component: 3500,
      trend_component: 44500
    },
    {
      date: '2024-11-01',
      actual: 45000,
      prophet_forecast: 44800,
      xgboost_adjustment: 200,
      ensemble_prediction: 45000,
      lower_bound: 41000,
      upper_bound: 49000,
      confidence: 0.86,
      seasonal_component: 2200,
      trend_component: 42800
    },
    {
      date: '2024-12-01',
      actual: 46000,
      prophet_forecast: 45500,
      xgboost_adjustment: 500,
      ensemble_prediction: 46000,
      lower_bound: 42000,
      upper_bound: 50000,
      confidence: 0.88,
      seasonal_component: 1800,
      trend_component: 44200
    },
    {
      date: '2025-01-01',
      prophet_forecast: 47000,
      xgboost_adjustment: -1200,
      ensemble_prediction: 45800,
      lower_bound: 41200,
      upper_bound: 50400,
      confidence: 0.85,
      seasonal_component: 2400,
      trend_component: 43600
    },
    {
      date: '2025-02-01',
      prophet_forecast: 49000,
      xgboost_adjustment: -800,
      ensemble_prediction: 48200,
      lower_bound: 43800,
      upper_bound: 52600,
      confidence: 0.82,
      seasonal_component: 1800,
      trend_component: 46400
    },
    {
      date: '2025-03-01',
      prophet_forecast: 52000,
      xgboost_adjustment: -500,
      ensemble_prediction: 51500,
      lower_bound: 46800,
      upper_bound: 56200,
      confidence: 0.80,
      seasonal_component: 3200,
      trend_component: 48300
    },
    {
      date: '2025-04-01',
      prophet_forecast: 54000,
      xgboost_adjustment: -300,
      ensemble_prediction: 53700,
      lower_bound: 48600,
      upper_bound: 58800,
      confidence: 0.78,
      seasonal_component: 2800,
      trend_component: 50900
    }
  ]

  const modelMetrics: ModelMetrics[] = [
    {
      model: 'prophet',
      mape: 12.4,
      rmse: 4200,
      mae: 3100,
      confidence: 0.87,
      lastTrained: '2025-01-15'
    },
    {
      model: 'xgboost',
      mape: 15.2,
      rmse: 3800,
      mae: 2900,
      confidence: 0.83,
      lastTrained: '2025-01-15'
    },
    {
      model: 'ensemble',
      mape: 10.8,
      rmse: 3500,
      mae: 2600,
      confidence: 0.91,
      lastTrained: '2025-01-15'
    }
  ]

  const currentMetrics = modelMetrics.find(m => m.model === selectedModel)
  const averageConfidence = forecastData.reduce((sum, d) => sum + d.confidence, 0) / forecastData.length
  const totalForecast = forecastData.reduce((sum, d) => sum + d.ensemble_prediction, 0)
  const monthlyAverage = totalForecast / forecastData.length

  const seasonalFactors = [
    { month: 'Jan', factor: 0.95, revenue: 45000, expenses: 38000 },
    { month: 'Feb', factor: 0.88, revenue: 42000, expenses: 36000 },
    { month: 'Mar', factor: 1.12, revenue: 54000, expenses: 41000 },
    { month: 'Apr', factor: 1.18, revenue: 56000, expenses: 42000 },
    { month: 'May', factor: 1.08, revenue: 52000, expenses: 40000 },
    { month: 'Jun', factor: 1.15, revenue: 55000, expenses: 43000 },
    { month: 'Jul', factor: 0.92, revenue: 44000, expenses: 37000 },
    { month: 'Aug', factor: 0.85, revenue: 41000, expenses: 35000 },
    { month: 'Sep', factor: 1.05, revenue: 50000, expenses: 39000 },
    { month: 'Oct', factor: 1.22, revenue: 58000, expenses: 44000 },
    { month: 'Nov', factor: 1.08, revenue: 52000, expenses: 40000 },
    { month: 'Dec', factor: 0.98, revenue: 47000, expenses: 38000 }
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-medium mb-2">Advanced Cash Flow Forecasting</h1>
            <p className="text-purple-100">Prophet + XGBoost ensemble model with uncertainty quantification</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-purple-100">Average Monthly Forecast</div>
            <div className="text-3xl font-medium">€{monthlyAverage.toLocaleString()}</div>
            <div className="text-sm text-purple-200">
              {averageConfidence > 0.85 ? '🟢' : averageConfidence > 0.75 ? '🟡' : '🟠'} 
              {(averageConfidence * 100).toFixed(1)}% confidence
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Time Horizon */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Time Horizon</label>
            <select
              value={timeHorizon}
              onChange={(e) => setTimeHorizon(e.target.value as any)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="1month">1 Month</option>
              <option value="3months">3 Months</option>
              <option value="6months">6 Months</option>
              <option value="1year">1 Year</option>
            </select>
          </div>

          {/* Metric Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Forecast Metric</label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as any)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="net_cash">Net Cash Flow</option>
              <option value="revenue">Revenue</option>
              <option value="expenses">Expenses</option>
            </select>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as any)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="ensemble">Ensemble (Recommended)</option>
              <option value="prophet">Prophet</option>
              <option value="xgboost">XGBoost</option>
            </select>
          </div>

          {/* Confidence Intervals Toggle */}
          <div className="flex items-end">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={showConfidenceIntervals}
                onChange={(e) => setShowConfidenceIntervals(e.target.checked)}
                className="sr-only"
              />
              <div className={`relative w-12 h-6 rounded-full transition-colors ${
                showConfidenceIntervals ? 'bg-purple-600' : 'bg-gray-300'
              }`}>
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  showConfidenceIntervals ? 'translate-x-7' : 'translate-x-1'
                }`}></div>
              </div>
              <span className="ml-2 text-sm text-gray-700">Show Uncertainty</span>
            </label>
          </div>
        </div>
      </div>

      {/* Model Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modelMetrics.map((metric) => (
          <div
            key={metric.model}
            className={`bg-white rounded-2xl shadow-xl border p-6 cursor-pointer transition-all ${
              selectedModel === metric.model
                ? 'border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50'
                : 'border-gray-100 hover:border-gray-300 hover:shadow-lg'
            }`}
            onClick={() => setSelectedModel(metric.model)}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-gray-900 capitalize flex items-center gap-2">
                {metric.model === 'prophet' && <TrendingUp className="h-4 w-4 text-blue-600" />}
                {metric.model === 'xgboost' && <Zap className="h-4 w-4 text-orange-600" />}
                {metric.model === 'ensemble' && <Brain className="h-4 w-4 text-purple-600" />}
                {metric.model}
              </h3>
              <span className={`text-xs px-2 py-1 rounded-full ${
                metric.confidence > 0.85 ? 'bg-green-100 text-green-800' : 
                metric.confidence > 0.75 ? 'bg-yellow-100 text-yellow-800' : 
                'bg-red-100 text-red-800'
              }`}>
                {(metric.confidence * 100).toFixed(1)}%
              </span>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">MAPE:</span>
                <span className="font-medium">{metric.mape}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">RMSE:</span>
                <span className="font-medium">€{metric.rmse.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">MAE:</span>
                <span className="font-medium">€{metric.mae.toLocaleString()}</span>
              </div>
            </div>
            
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Clock className="h-3 w-3" />
                <span>Last trained: {metric.lastTrained}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Forecast Chart Visualization */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <LineChart className="h-5 w-5 text-purple-600" />
            Cash Flow Forecast - {selectedModel.charAt(0).toUpperCase() + selectedModel.slice(1)} Model
          </h2>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-600 rounded-full"></div>
              <span>Forecast</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
              <span>Actual</span>
            </div>
            {showConfidenceIntervals && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-200 rounded-full"></div>
                <span>Confidence Interval</span>
              </div>
            )}
          </div>
        </div>

        {/* Interactive Chart */}
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={forecastData.map(d => ({
                ...d,
                month: new Date(d.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
                forecast: selectedModel === 'prophet' ? d.prophet_forecast : 
                         selectedModel === 'xgboost' ? d.prophet_forecast + d.xgboost_adjustment :
                         d.ensemble_prediction
              }))}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <defs>
                <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#c4b5fd" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#c4b5fd" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="month" 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#6b7280' }}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={(value) => `€${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
                  fontSize: '12px'
                }}
                formatter={(value, name) => [
                  `€${Number(value).toLocaleString()}`, 
                  name === 'forecast' ? `${selectedModel.charAt(0).toUpperCase() + selectedModel.slice(1)} Forecast` :
                  name === 'actual' ? 'Actual' :
                  name === 'upper_bound' ? 'Upper Bound' :
                  name === 'lower_bound' ? 'Lower Bound' : name
                ]}
                labelFormatter={(label) => `Period: ${label}`}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              />
              
              {/* Confidence interval area */}
              {showConfidenceIntervals && (
                <Area
                  type="monotone"
                  dataKey="upper_bound"
                  stroke="none"
                  fill="url(#colorConfidence)"
                  name="Confidence Interval"
                />
              )}
              
              {showConfidenceIntervals && (
                <Area
                  type="monotone"
                  dataKey="lower_bound"
                  stroke="none"
                  fill="#ffffff"
                  fillOpacity={0.8}
                />
              )}
              
              {/* Main forecast line */}
              <Area
                type="monotone"
                dataKey="forecast"
                stroke="#7c3aed"
                strokeWidth={3}
                fill="url(#colorForecast)"
                name={`${selectedModel.charAt(0).toUpperCase() + selectedModel.slice(1)} Forecast`}
              />
              
              {/* Actual data line */}
              <Area
                type="monotone"
                dataKey="actual"
                stroke="#3b82f6"
                strokeWidth={3}
                fill="none"
                strokeDasharray="0"
                name="Actual"
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
              
              {/* Reference line for current date */}
              <ReferenceLine 
                x="Dec 24" 
                stroke="#ef4444" 
                strokeDasharray="5 5" 
                label={{ value: "Today", position: "topRight", fontSize: 10, fill: '#ef4444' }} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Seasonal Pattern Analysis */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-6 flex items-center gap-2">
          <Activity className="h-5 w-5 text-purple-600" />
          Seasonal Pattern Analysis
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {seasonalFactors.map((season) => (
            <div key={season.month} className="text-center">
              <div className={`w-full h-20 rounded-xl mb-2 flex flex-col justify-between p-2 ${
                season.factor > 1.1 ? 'bg-gradient-to-b from-green-200 to-green-300' :
                season.factor < 0.9 ? 'bg-gradient-to-b from-red-200 to-red-300' :
                'bg-gradient-to-b from-blue-200 to-blue-300'
              }`}>
                <span className="text-xs font-medium text-gray-700">{season.month}</span>
                <div className="text-center">
                  <div className="text-sm font-medium">
                    {season.factor > 1 ? '+' : ''}{((season.factor - 1) * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-600">
                <div>Rev: €{(season.revenue / 1000).toFixed(0)}k</div>
                <div>Exp: €{(season.expenses / 1000).toFixed(0)}k</div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-xl border border-green-200">
            <div className="text-green-700 font-medium">Peak Season</div>
            <div className="text-sm text-green-600">Oct, Apr, Jun</div>
            <div className="text-xs text-green-500 mt-1">+12-22% above average</div>
          </div>
          <div className="p-4 bg-gradient-to-r from-red-50 to-red-100 rounded-xl border border-red-200">
            <div className="text-red-700 font-medium">Low Season</div>
            <div className="text-sm text-red-600">Aug, Feb, Jul</div>
            <div className="text-xs text-red-500 mt-1">-8-15% below average</div>
          </div>
          <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl border border-blue-200">
            <div className="text-blue-700 font-medium">Stable Season</div>
            <div className="text-sm text-blue-600">Jan, Sep, Dec</div>
            <div className="text-xs text-blue-500 mt-1">±5% of average</div>
          </div>
        </div>
      </div>

      {/* Key Insights */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Target className="h-5 w-5 text-purple-600" />
          Key Insights & Recommendations
        </h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-xl border border-green-200">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <div className="font-medium text-green-800">Model Performance Strong</div>
                <div className="text-sm text-green-700">
                  Ensemble model achieving 91% confidence with 10.8% MAPE - excellent accuracy for {timeHorizon} forecasting.
                </div>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl border border-purple-200">
              <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5" />
              <div>
                <div className="font-medium text-purple-800">Positive Trend Detected</div>
                <div className="text-sm text-purple-700">
                  Underlying trend component shows 12% quarter-over-quarter growth in cash flow.
                </div>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl border border-blue-200">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <div className="font-medium text-blue-800">Seasonal Optimization</div>
                <div className="text-sm text-blue-700">
                  Consider cash flow strategies for Aug-Feb low season. Plan major expenses for high-confidence periods.
                </div>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-xl border border-yellow-200">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <div className="font-medium text-yellow-800">Model Retraining Due</div>
                <div className="text-sm text-yellow-700">
                  Last training: Jan 15. Recommend monthly retraining for optimal accuracy with fresh data.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}