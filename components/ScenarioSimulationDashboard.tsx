'use client'

import { useState, useEffect } from 'react'
import { 
  PlayCircle, 
  RotateCcw, 
  Save, 
  Layers, 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Users,
  ShoppingCart,
  PieChart,
  AlertTriangle,
  CheckCircle,
  Activity,
  Target,
  Calculator,
  BarChart3
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'

interface ScenarioParameter {
  id: string
  name: string
  category: string
  currentValue: number
  min: number
  max: number
  step: number
  unit: string
  description: string
  impact: 'high' | 'medium' | 'low'
}

interface ScenarioResult {
  metric: string
  current: number
  scenario: number
  change: number
  changePercent: number
  impact: 'positive' | 'negative' | 'neutral'
  category: string
}

interface MonteCarloResult {
  scenario: string
  probability: number
  outcome: number
  confidence: number
}

const SCENARIO_PARAMETERS: ScenarioParameter[] = [
  // Revenue Parameters
  {
    id: 'monthly_revenue',
    name: 'Monthly Revenue',
    category: 'Revenue',
    currentValue: 45000,
    min: 20000,
    max: 100000,
    step: 1000,
    unit: '€',
    description: 'Average monthly gross revenue',
    impact: 'high'
  },
  {
    id: 'client_growth_rate',
    name: 'Client Growth Rate',
    category: 'Revenue',
    currentValue: 15,
    min: -10,
    max: 50,
    step: 1,
    unit: '%',
    description: 'Monthly new client acquisition rate',
    impact: 'high'
  },
  {
    id: 'pricing_increase',
    name: 'Pricing Adjustment',
    category: 'Revenue',
    currentValue: 0,
    min: -20,
    max: 30,
    step: 1,
    unit: '%',
    description: 'Price change for existing services',
    impact: 'high'
  },
  
  // Cost Parameters  
  {
    id: 'operating_expenses',
    name: 'Operating Expenses',
    category: 'Costs',
    currentValue: 18000,
    min: 10000,
    max: 40000,
    step: 500,
    unit: '€',
    description: 'Monthly operational costs',
    impact: 'high'
  },
  {
    id: 'staff_costs',
    name: 'Staff Costs',
    category: 'Costs',
    currentValue: 12000,
    min: 0,
    max: 30000,
    step: 1000,
    unit: '€',
    description: 'Monthly employee and contractor costs',
    impact: 'medium'
  },
  {
    id: 'marketing_spend',
    name: 'Marketing Investment',
    category: 'Costs',
    currentValue: 3000,
    min: 500,
    max: 15000,
    step: 250,
    unit: '€',
    description: 'Monthly marketing and advertising budget',
    impact: 'medium'
  },
  
  // Tax Parameters
  {
    id: 'tax_optimization',
    name: 'Tax Optimization Level',
    category: 'Tax',
    currentValue: 25,
    min: 15,
    max: 45,
    step: 1,
    unit: '%',
    description: 'Effective tax rate after optimizations',
    impact: 'high'
  },
  {
    id: 'vat_rate',
    name: 'VAT Rate',
    category: 'Tax',
    currentValue: 21,
    min: 6,
    max: 21,
    step: 1,
    unit: '%',
    description: 'Applicable VAT rate on services',
    impact: 'medium'
  }
]

export default function ScenarioSimulationDashboard() {
  const [parameters, setParameters] = useState<Record<string, number>>({})
  const [simulationResults, setSimulationResults] = useState<ScenarioResult[]>([])
  const [isSimulating, setIsSimulating] = useState(false)
  const [savedScenarios, setSavedScenarios] = useState<string[]>(['Current State', 'Growth Scenario', 'Conservative Scenario'])
  const [selectedScenario, setSelectedScenario] = useState('Custom Scenario')
  const [monteCarloResults, setMonteCarloResults] = useState<MonteCarloResult[]>([])
  const [showMonteCarlo, setShowMonteCarlo] = useState(false)

  // Initialize parameters with current values
  useEffect(() => {
    const initialParams: Record<string, number> = {}
    SCENARIO_PARAMETERS.forEach(param => {
      initialParams[param.id] = param.currentValue
    })
    setParameters(initialParams)
  }, [])

  // Simulate scenario results in real-time
  useEffect(() => {
    if (Object.keys(parameters).length > 0) {
      simulateScenario()
    }
  }, [parameters])

  const simulateScenario = () => {
    setIsSimulating(true)
    
    // Simulate calculation delay
    setTimeout(() => {
      const results: ScenarioResult[] = [
        {
          metric: 'Monthly Net Profit',
          current: 15000,
          scenario: calculateNetProfit(),
          change: 0,
          changePercent: 0,
          impact: 'neutral',
          category: 'Profitability'
        },
        {
          metric: 'Annual Cash Flow',
          current: 180000,
          scenario: calculateAnnualCashFlow(),
          change: 0,
          changePercent: 0,
          impact: 'neutral',
          category: 'Cash Flow'
        },
        {
          metric: 'Tax Liability',
          current: 54000,
          scenario: calculateTaxLiability(),
          change: 0,
          changePercent: 0,
          impact: 'neutral',
          category: 'Tax'
        },
        {
          metric: 'ROI on Marketing',
          current: 450,
          scenario: calculateMarketingROI(),
          change: 0,
          changePercent: 0,
          impact: 'neutral',
          category: 'Marketing'
        },
        {
          metric: 'Break-even Point',
          current: 28,
          scenario: calculateBreakEven(),
          change: 0,
          changePercent: 0,
          impact: 'neutral',
          category: 'Risk'
        },
        {
          metric: 'Working Capital',
          current: 35000,
          scenario: calculateWorkingCapital(),
          change: 0,
          changePercent: 0,
          impact: 'neutral',
          category: 'Liquidity'
        }
      ]

      // Calculate changes and impact
      results.forEach(result => {
        result.change = result.scenario - result.current
        result.changePercent = (result.change / result.current) * 100
        result.impact = result.change > 0 ? 'positive' : result.change < 0 ? 'negative' : 'neutral'
      })

      setSimulationResults(results)
      setIsSimulating(false)

      // Generate Monte Carlo results
      generateMonteCarloResults()
    }, 800)
  }

  const calculateNetProfit = (): number => {
    const revenue = parameters.monthly_revenue || 45000
    const growth = (parameters.client_growth_rate || 15) / 100
    const pricing = (parameters.pricing_increase || 0) / 100
    const costs = (parameters.operating_expenses || 18000) + (parameters.staff_costs || 12000) + (parameters.marketing_spend || 3000)
    
    const adjustedRevenue = revenue * (1 + growth * 0.5) * (1 + pricing)
    return Math.round(adjustedRevenue - costs)
  }

  const calculateAnnualCashFlow = (): number => {
    return calculateNetProfit() * 12
  }

  const calculateTaxLiability = (): number => {
    const profit = calculateNetProfit() * 12
    const taxRate = (parameters.tax_optimization || 25) / 100
    return Math.round(profit * taxRate)
  }

  const calculateMarketingROI = (): number => {
    const marketingSpend = parameters.marketing_spend || 3000
    const revenueGrowth = (parameters.client_growth_rate || 15) / 100
    const revenue = parameters.monthly_revenue || 45000
    const attributedRevenue = revenue * revenueGrowth * 0.6 // 60% attributed to marketing
    return Math.round((attributedRevenue / marketingSpend) * 100)
  }

  const calculateBreakEven = (): number => {
    const fixedCosts = (parameters.operating_expenses || 18000) + (parameters.staff_costs || 12000)
    const variableCostRatio = 0.3 // 30% variable costs
    const revenue = parameters.monthly_revenue || 45000
    const marginRatio = 1 - variableCostRatio
    return Math.round(fixedCosts / (revenue * marginRatio / 30)) // Days to break-even
  }

  const calculateWorkingCapital = (): number => {
    const revenue = parameters.monthly_revenue || 45000
    const costs = (parameters.operating_expenses || 18000) + (parameters.staff_costs || 12000)
    return Math.round((revenue - costs) * 1.5) // 1.5 months of operating buffer
  }

  const generateMonteCarloResults = () => {
    const scenarios = [
      { scenario: 'Best Case', probability: 0.15, outcome: calculateNetProfit() * 1.3, confidence: 0.85 },
      { scenario: 'Likely Case', probability: 0.60, outcome: calculateNetProfit(), confidence: 0.95 },
      { scenario: 'Worst Case', probability: 0.25, outcome: calculateNetProfit() * 0.7, confidence: 0.80 },
    ]
    setMonteCarloResults(scenarios)
  }

  const handleParameterChange = (paramId: string, value: number) => {
    setParameters(prev => ({
      ...prev,
      [paramId]: value
    }))
  }

  const resetToDefaults = () => {
    const defaultParams: Record<string, number> = {}
    SCENARIO_PARAMETERS.forEach(param => {
      defaultParams[param.id] = param.currentValue
    })
    setParameters(defaultParams)
  }

  const saveCurrentScenario = () => {
    const scenarioName = `Scenario ${savedScenarios.length + 1}`
    setSavedScenarios(prev => [...prev, scenarioName])
    setSelectedScenario(scenarioName)
  }

  // Group parameters by category
  const parametersByCategory = SCENARIO_PARAMETERS.reduce((acc, param) => {
    if (!acc[param.category]) acc[param.category] = []
    acc[param.category].push(param)
    return acc
  }, {} as Record<string, ScenarioParameter[]>)

  // Prepare chart data
  const impactChartData = simulationResults.map(result => ({
    name: result.metric.replace(' ', '\n'),
    current: result.current,
    scenario: result.scenario,
    change: result.change
  }))

  const categoryImpactData = [
    { category: 'Profitability', score: 85 },
    { category: 'Cash Flow', score: 78 },
    { category: 'Tax Efficiency', score: 92 },
    { category: 'Marketing', score: 67 },
    { category: 'Risk Management', score: 74 },
    { category: 'Liquidity', score: 88 }
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-medium mb-2">What-If Scenario Simulation</h1>
            <p className="text-purple-100">Experiment with different business parameters and see real-time impacts</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${isSimulating ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></div>
            <span className="text-sm">{isSimulating ? 'Simulating...' : 'Ready'}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parameter Controls */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Scenario Parameters</h2>
              <div className="flex space-x-2">
                <button
                  onClick={resetToDefaults}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Reset to defaults"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
                <button
                  onClick={saveCurrentScenario}
                  className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Save scenario"
                >
                  <Save className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Scenario Selector */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scenario Template
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {savedScenarios.map(scenario => (
                  <option key={scenario} value={scenario}>{scenario}</option>
                ))}
                <option value="Custom Scenario">Custom Scenario</option>
              </select>
            </div>

            {/* Parameter Controls by Category */}
            <div className="space-y-6">
              {Object.entries(parametersByCategory).map(([category, params]) => (
                <div key={category} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                    {category === 'Revenue' && <TrendingUp className="h-4 w-4 mr-2 text-green-600" />}
                    {category === 'Costs' && <TrendingDown className="h-4 w-4 mr-2 text-red-600" />}
                    {category === 'Tax' && <Calculator className="h-4 w-4 mr-2 text-blue-600" />}
                    {category}
                  </h3>
                  <div className="space-y-4">
                    {params.map(param => (
                      <div key={param.id}>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-xs font-medium text-gray-600">
                            {param.name}
                          </label>
                          <div className="flex items-center space-x-1">
                            <span className="text-sm font-medium text-gray-900">
                              {param.unit === '€' ? '€' : ''}{parameters[param.id]?.toLocaleString() || param.currentValue.toLocaleString()}{param.unit === '%' ? '%' : ''}
                            </span>
                            <div className={`w-2 h-2 rounded-full ${
                              param.impact === 'high' ? 'bg-red-400' : 
                              param.impact === 'medium' ? 'bg-yellow-400' : 
                              'bg-green-400'
                            }`} title={`${param.impact} impact`}></div>
                          </div>
                        </div>
                        <input
                          type="range"
                          min={param.min}
                          max={param.max}
                          step={param.step}
                          value={parameters[param.id] || param.currentValue}
                          onChange={(e) => handleParameterChange(param.id, Number(e.target.value))}
                          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                        />
                        <p className="text-xs text-gray-500 mt-1">{param.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Results Display */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key Metrics */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Simulation Results</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {simulationResults.map((result, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-gray-700">{result.metric}</h3>
                    {result.impact === 'positive' ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : result.impact === 'negative' ? (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    ) : (
                      <Activity className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Current:</span>
                      <span className="font-medium">
                        {result.metric.includes('€') || result.metric.includes('Cash') || result.metric.includes('Tax') || result.metric.includes('Capital') || result.metric.includes('Profit') ? '€' : ''}
                        {result.current.toLocaleString()}
                        {result.metric.includes('ROI') || result.metric.includes('Break-even') ? (result.metric.includes('ROI') ? '%' : ' days') : ''}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Scenario:</span>
                      <span className="font-medium">
                        {result.metric.includes('€') || result.metric.includes('Cash') || result.metric.includes('Tax') || result.metric.includes('Capital') || result.metric.includes('Profit') ? '€' : ''}
                        {result.scenario.toLocaleString()}
                        {result.metric.includes('ROI') || result.metric.includes('Break-even') ? (result.metric.includes('ROI') ? '%' : ' days') : ''}
                      </span>
                    </div>
                    <div className={`flex justify-between text-sm font-medium ${
                      result.impact === 'positive' ? 'text-green-600' : 
                      result.impact === 'negative' ? 'text-red-600' : 
                      'text-gray-600'
                    }`}>
                      <span>Change:</span>
                      <span>
                        {result.change > 0 ? '+' : ''}{result.changePercent.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Impact Visualization */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Impact Comparison</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={impactChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 12 }}
                  interval={0}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    `€${value.toLocaleString()}`, 
                    name === 'current' ? 'Current' : 'Scenario'
                  ]}
                />
                <Legend />
                <Bar dataKey="current" fill="#8b5cf6" name="Current" radius={[4, 4, 0, 0]} />
                <Bar dataKey="scenario" fill="#3b82f6" name="Scenario" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Monte Carlo Simulation */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Uncertainty Analysis</h2>
              <button
                onClick={() => setShowMonteCarlo(!showMonteCarlo)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  showMonteCarlo 
                    ? 'bg-purple-100 text-purple-700' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Layers className="h-4 w-4" />
                  <span>Monte Carlo</span>
                </div>
              </button>
            </div>

            {showMonteCarlo && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Probability Scenarios</h3>
                  <div className="space-y-3">
                    {monteCarloResults.map((result, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{result.scenario}</div>
                          <div className="text-xs text-gray-500">
                            {(result.probability * 100).toFixed(0)}% probability
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">
                            €{result.outcome.toLocaleString()}
                          </div>
                          <div className="text-xs text-gray-500">
                            {result.confidence * 100}% confidence
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Business Health Radar</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <RadarChart data={categoryImpactData}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis dataKey="category" tick={{ fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                      <Radar
                        name="Health Score"
                        dataKey="score"
                        stroke="#8b5cf6"
                        fill="#8b5cf6"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}