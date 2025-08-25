'use client'

import { useState } from 'react'
import { 
  Calculator,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  Euro,
  Calendar,
  Target,
  BarChart3,
  PieChart,
  Zap,
  Settings,
  Play,
  RotateCcw,
  Brain,
  DollarSign,
  Clock,
  Users,
  Building2,
  FileText,
  Briefcase,
  Shield,
  HelpCircle,
  Heart
} from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

interface ScenarioInput {
  id: string
  name: string
  type: 'income' | 'expense' | 'timing' | 'client' | 'investment'
  currentValue: number
  proposedValue: number
  timeframe: 'immediate' | '1month' | '3months' | '6months' | '12months'
  description: string
  confidence: number
}

interface SimulationResult {
  scenario: string
  cashFlowImpact: number
  netPositionChange: number
  riskScore: number
  timeToBreakeven: number | null
  keyInsights: string[]
  recommendations: string[]
  drSigmundAdvice: string
}

export default function ScenarioSimulationEngine() {
  const [activeScenarios, setActiveScenarios] = useState<ScenarioInput[]>([])
  const [simulationResults, setSimulationResults] = useState<SimulationResult | null>(null)
  const [isSimulating, setIsSimulating] = useState(false)
  const [selectedScenarioType, setSelectedScenarioType] = useState<'income' | 'expense' | 'timing' | 'client' | 'investment'>('income')
  const [gradientOption, setGradientOption] = useState(0)
  const [expandedSection, setExpandedSection] = useState<'howToUse' | 'therapy' | null>(null)

  // Gradient options for the header
  const gradientOptions = [
    { name: 'Full Dark', class: 'bg-brand-primary-dark' },
    { name: 'Diagonal 3-color', class: 'bg-gradient-to-br from-brand-primary-dark via-brand-primary to-brand-primary-light' },
    { name: 'Dark to Primary', class: 'bg-gradient-to-r from-brand-primary-dark to-brand-primary' },
    { name: 'Primary to Accent', class: 'bg-gradient-to-r from-brand-primary to-brand-accent' },
    { name: 'Dark to Light', class: 'bg-gradient-to-br from-brand-primary-dark to-brand-primary-lighter' },
    { name: 'Brand Gradient', class: 'bg-brand-gradient' },
    { name: 'Simple Primary', class: 'bg-brand-primary' },
    { name: 'Dark to Accent', class: 'bg-gradient-to-r from-brand-primary-dark to-brand-accent' },
    { name: 'Primary to Light', class: 'bg-gradient-to-r from-brand-primary to-brand-primary-lighter' },
    { name: 'Accent to Light', class: 'bg-gradient-to-r from-brand-accent to-brand-primary-light' }
  ]

  const scenarioTemplates = {
    income: [
      {
        id: 'income-increase',
        name: 'New Client Revenue',
        description: 'Adding a new recurring client with monthly revenue',
        defaultCurrent: 0,
        defaultProposed: 3500,
        unit: '€/month'
      },
      {
        id: 'rate-increase',
        name: 'Hourly Rate Increase',
        description: 'Increasing your hourly billing rate',
        defaultCurrent: 75,
        defaultProposed: 95,
        unit: '€/hour'
      },
      {
        id: 'project-bonus',
        name: 'One-time Project Bonus',
        description: 'Completing a high-value project',
        defaultCurrent: 0,
        defaultProposed: 15000,
        unit: '€ one-time'
      }
    ],
    expense: [
      {
        id: 'office-rent',
        name: 'Office Space Rental',
        description: 'Monthly office rent vs home office',
        defaultCurrent: 0,
        defaultProposed: 1200,
        unit: '€/month'
      },
      {
        id: 'equipment-purchase',
        name: 'Equipment Investment',
        description: 'New computer, software, or tools',
        defaultCurrent: 0,
        defaultProposed: 5000,
        unit: '€ one-time'
      },
      {
        id: 'marketing-spend',
        name: 'Marketing Investment',
        description: 'Monthly marketing and advertising budget',
        defaultCurrent: 200,
        defaultProposed: 800,
        unit: '€/month'
      }
    ],
    timing: [
      {
        id: 'payment-delay',
        name: 'Client Payment Delay',
        description: 'What if a major client pays 60 days late?',
        defaultCurrent: 30,
        defaultProposed: 90,
        unit: 'days delay'
      },
      {
        id: 'invoice-timing',
        name: 'Invoice Timing Change',
        description: 'Shifting invoice timing for tax optimization',
        defaultCurrent: 0,
        defaultProposed: 30,
        unit: 'days shift'
      },
      {
        id: 'seasonal-adjustment',
        name: 'Seasonal Revenue Drop',
        description: 'Expected seasonal decrease in business',
        defaultCurrent: 100,
        defaultProposed: 70,
        unit: '% of normal'
      }
    ],
    client: [
      {
        id: 'client-loss',
        name: 'Major Client Loss',
        description: 'Losing a significant recurring client',
        defaultCurrent: 4500,
        defaultProposed: 0,
        unit: '€/month'
      },
      {
        id: 'client-expansion',
        name: 'Client Project Expansion',
        description: 'Existing client increases project scope',
        defaultCurrent: 3000,
        defaultProposed: 5500,
        unit: '€/month'
      },
      {
        id: 'payment-terms',
        name: 'Payment Terms Change',
        description: 'Client requests extended payment terms',
        defaultCurrent: 30,
        defaultProposed: 60,
        unit: 'days'
      }
    ],
    investment: [
      {
        id: 'emergency-fund',
        name: 'Emergency Fund Usage',
        description: 'Need to use emergency fund for unexpected expense',
        defaultCurrent: 25000,
        defaultProposed: 15000,
        unit: '€ remaining'
      },
      {
        id: 'equipment-roi',
        name: 'Equipment ROI Scenario',
        description: 'Equipment purchase increases productivity/rates',
        defaultCurrent: 75,
        defaultProposed: 85,
        unit: '€/hour'
      },
      {
        id: 'market-downturn',
        name: 'Investment Portfolio Loss',
        description: 'Market downturn affects investment portfolio',
        defaultCurrent: 50000,
        defaultProposed: 42000,
        unit: '€ portfolio value'
      }
    ]
  }

  const addScenario = (template: any) => {
    const newScenario: ScenarioInput = {
      id: `${template.id}-${Date.now()}`,
      name: template.name,
      type: selectedScenarioType,
      currentValue: template.defaultCurrent,
      proposedValue: template.defaultProposed,
      timeframe: '3months',
      description: template.description,
      confidence: 85
    }
    setActiveScenarios([...activeScenarios, newScenario])
  }

  const updateScenario = (id: string, updates: Partial<ScenarioInput>) => {
    setActiveScenarios(scenarios => 
      scenarios.map(s => s.id === id ? { ...s, ...updates } : s)
    )
  }

  const removeScenario = (id: string) => {
    setActiveScenarios(scenarios => scenarios.filter(s => s.id !== id))
  }

  const runSimulation = async () => {
    if (activeScenarios.length === 0) return
    
    setIsSimulating(true)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Mock simulation calculation
    const totalCashFlowImpact = activeScenarios.reduce((sum, scenario) => {
      const impact = scenario.proposedValue - scenario.currentValue
      const multiplier = scenario.type === 'income' ? 1 : scenario.type === 'expense' ? -1 : 0.5
      return sum + (impact * multiplier)
    }, 0)

    const mockResult: SimulationResult = {
      scenario: `Simulation with ${activeScenarios.length} factor(s)`,
      cashFlowImpact: totalCashFlowImpact,
      netPositionChange: totalCashFlowImpact * 0.85, // After taxes/fees
      riskScore: Math.min(90, Math.max(10, 50 + (activeScenarios.length * 8))),
      timeToBreakeven: totalCashFlowImpact < 0 ? Math.ceil(Math.abs(totalCashFlowImpact) / 3000) : null,
      keyInsights: [
        `Your cash flow would ${totalCashFlowImpact >= 0 ? 'improve' : 'worsen'} by €${Math.abs(totalCashFlowImpact).toLocaleString()} over 12 months`,
        `This represents a ${Math.abs((totalCashFlowImpact / 50000) * 100).toFixed(1)}% change from your baseline position`,
        activeScenarios.some(s => s.type === 'timing') ? 'Payment timing changes create temporary cash flow stress' : 'No immediate liquidity concerns identified',
        `Confidence level: ${Math.round(activeScenarios.reduce((sum, s) => sum + s.confidence, 0) / activeScenarios.length)}% based on scenario inputs`
      ],
      recommendations: [
        totalCashFlowImpact < -5000 ? 'Consider building larger emergency fund before implementing' : 'Scenario appears financially viable',
        activeScenarios.some(s => s.type === 'client') ? 'Diversify client base to reduce dependency risk' : 'Client risk appears manageable',
        'Monitor key metrics monthly and adjust scenario assumptions',
        'Consider implementing changes gradually to test assumptions'
      ],
      drSigmundAdvice: totalCashFlowImpact >= 0 
        ? "This scenario looks promising! The numbers suggest you're making smart financial choices. Remember, even positive changes can create temporary stress - take it step by step and monitor your emotional well-being throughout the transition."
        : "I understand this scenario might feel overwhelming. Remember, we're just exploring possibilities - no decisions are permanent. Focus on what you can control, and consider if there are smaller steps you could take to minimize the impact while still achieving your goals."
    }

    setSimulationResults(mockResult)
    setIsSimulating(false)
  }

  const clearSimulation = () => {
    setActiveScenarios([])
    setSimulationResults(null)
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Scenario Builder */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Settings className="h-5 w-5 text-brand-primary" />
          Build Your Scenario
        </h2>
        
        {/* Scenario Type Selector */}
        <div className="flex space-x-1 mb-6 bg-gray-50 rounded-2xl p-1">
          {(['income', 'expense', 'timing', 'client', 'investment'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setSelectedScenarioType(type)}
              className={`flex-1 py-3 px-4 rounded-xl text-center transition-all ${
                selectedScenarioType === type
                  ? 'bg-white text-brand-primary shadow-sm border border-gray-200'
                  : 'text-gray-600 hover:text-brand-primary hover:bg-white/50'
              }`}
            >
              <div className="flex items-center justify-center mb-1">
                {type === 'income' && <TrendingUp className="h-4 w-4" />}
                {type === 'expense' && <TrendingDown className="h-4 w-4" />}
                {type === 'timing' && <Clock className="h-4 w-4" />}
                {type === 'client' && <Users className="h-4 w-4" />}
                {type === 'investment' && <Building2 className="h-4 w-4" />}
              </div>
              <span className="text-xs font-medium capitalize">{type}</span>
            </button>
          ))}
        </div>

        {/* Scenario Templates */}
        <div className="grid md:grid-cols-3 gap-4 mb-6">
          {scenarioTemplates[selectedScenarioType].map((template) => (
            <div key={template.id} className="border border-gray-200 rounded-2xl p-4 hover:shadow-sm transition-all flex flex-col">
              <h3 className="font-medium text-gray-900 mb-2">{template.name}</h3>
              <p className="text-sm text-gray-600 mb-3 flex-grow">{template.description}</p>
              <div className="flex items-end justify-between mt-auto">
                <div className="text-sm">
                  <span className="text-gray-500">{template.defaultCurrent} → {template.defaultProposed}</span>
                  <span className="text-xs text-gray-400 ml-1">{template.unit}</span>
                </div>
                <button
                  onClick={() => addScenario(template)}
                  className="px-3 py-1 bg-brand-primary text-white rounded-xl text-sm hover:bg-brand-primary-hover transition-colors flex-shrink-0"
                >
                  Add
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Active Scenarios */}
        {activeScenarios.length > 0 && (
          <div className="border-t border-gray-200 pt-6">
            <h3 className="font-medium text-gray-900 mb-4">Active Scenarios ({activeScenarios.length})</h3>
            <div className="space-y-4">
              {activeScenarios.map((scenario) => (
                <div key={scenario.id} className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-2xl p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{scenario.name}</h4>
                      <p className="text-sm text-gray-600">{scenario.description}</p>
                    </div>
                    <button
                      onClick={() => removeScenario(scenario.id)}
                      className="text-red-500 hover:text-red-600 text-sm transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Current Value</label>
                      <input
                        type="number"
                        value={scenario.currentValue}
                        onChange={(e) => updateScenario(scenario.id, { currentValue: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary focus:border-brand-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Proposed Value</label>
                      <input
                        type="number"
                        value={scenario.proposedValue}
                        onChange={(e) => updateScenario(scenario.id, { proposedValue: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary focus:border-brand-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Timeframe</label>
                      <select
                        value={scenario.timeframe}
                        onChange={(e) => updateScenario(scenario.id, { timeframe: e.target.value as any })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary focus:border-brand-primary"
                      >
                        <option value="immediate">Immediate</option>
                        <option value="1month">1 Month</option>
                        <option value="3months">3 Months</option>
                        <option value="6months">6 Months</option>
                        <option value="12months">12 Months</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Confidence %</label>
                      <input
                        type="range"
                        min="10"
                        max="100"
                        value={scenario.confidence}
                        onChange={(e) => updateScenario(scenario.id, { confidence: Number(e.target.value) })}
                        className="w-full accent-brand-primary"
                      />
                      <div className="text-xs text-gray-600 text-center">{scenario.confidence}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-6">
          <div className="flex items-center gap-3">
            <button
              onClick={runSimulation}
              disabled={activeScenarios.length === 0 || isSimulating}
              className="flex items-center gap-2 px-6 py-3 bg-brand-gradient text-white rounded-2xl font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSimulating ? (
                <>
                  <RotateCcw className="h-4 w-4 animate-spin" />
                  Simulating...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Simulation
                </>
              )}
            </button>
            
            <button
              onClick={clearSimulation}
              className="flex items-center gap-2 px-6 py-3 border border-brand-primary-light text-brand-primary-dark rounded-2xl font-medium hover:bg-brand-primary-lightest transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              Clear All
            </button>
          </div>

          {/* Help Links */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setExpandedSection(expandedSection === 'howToUse' ? null : 'howToUse')}
              className="text-sm text-brand-primary hover:text-brand-primary-hover transition-colors flex items-center gap-1 font-medium"
            >
              <HelpCircle className="h-4 w-4" />
              How to Use
            </button>
            <button
              onClick={() => setExpandedSection(expandedSection === 'therapy' ? null : 'therapy')}
              className="text-sm text-brand-primary hover:text-brand-primary-hover transition-colors flex items-center gap-1 font-medium"
            >
              <Heart className="h-4 w-4" />
              Therapy Guide
            </button>
          </div>
        </div>
      </div>

      {/* Simulation Results */}
      {simulationResults && (
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-6 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-brand-primary" />
            Simulation Results
          </h2>

          {/* Key Metrics */}
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <div className={`bg-gradient-to-r ${simulationResults.cashFlowImpact >= 0 ? 'from-emerald-50 to-emerald-100 border-emerald-200' : 'from-red-50 to-red-100 border-red-200'} border rounded-2xl p-4`}>
              <div className="flex items-center gap-2 mb-2">
                {simulationResults.cashFlowImpact >= 0 ? 
                  <TrendingUp className="h-4 w-4 text-emerald-600" /> : 
                  <TrendingDown className="h-4 w-4 text-red-600" />
                }
                <span className={`font-medium ${simulationResults.cashFlowImpact >= 0 ? 'text-emerald-800' : 'text-red-800'}`}>
                  Cash Flow Impact
                </span>
              </div>
              <div className={`text-2xl font-medium ${simulationResults.cashFlowImpact >= 0 ? 'text-emerald-900' : 'text-red-900'}`}>
                €{simulationResults.cashFlowImpact.toLocaleString()}
              </div>
              <div className={`text-sm ${simulationResults.cashFlowImpact >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                12-month projection
              </div>
            </div>

            <div className={`bg-gradient-to-r ${simulationResults.netPositionChange >= 0 ? 'from-emerald-50 to-emerald-100 border-emerald-200' : simulationResults.netPositionChange >= -5000 ? 'from-amber-50 to-amber-100 border-amber-200' : 'from-red-50 to-red-100 border-red-200'} border rounded-2xl p-4`}>
              <div className="flex items-center gap-2 mb-2">
                <Euro className={`h-4 w-4 ${simulationResults.netPositionChange >= 0 ? 'text-emerald-600' : simulationResults.netPositionChange >= -5000 ? 'text-amber-600' : 'text-red-600'}`} />
                <span className={`font-medium ${simulationResults.netPositionChange >= 0 ? 'text-emerald-800' : simulationResults.netPositionChange >= -5000 ? 'text-amber-800' : 'text-red-800'}`}>
                  Net Position
                </span>
              </div>
              <div className={`text-2xl font-medium ${simulationResults.netPositionChange >= 0 ? 'text-emerald-900' : simulationResults.netPositionChange >= -5000 ? 'text-amber-900' : 'text-red-900'}`}>
                €{simulationResults.netPositionChange.toLocaleString()}
              </div>
              <div className={`text-sm ${simulationResults.netPositionChange >= 0 ? 'text-emerald-700' : simulationResults.netPositionChange >= -5000 ? 'text-amber-700' : 'text-red-700'}`}>
                After taxes & fees
              </div>
            </div>

            <div className={`bg-gradient-to-r ${simulationResults.riskScore <= 30 ? 'from-emerald-50 to-emerald-100 border-emerald-200' : simulationResults.riskScore <= 80 ? 'from-amber-50 to-amber-100 border-amber-200' : 'from-red-50 to-red-100 border-red-200'} border rounded-2xl p-4`}>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className={`h-4 w-4 ${simulationResults.riskScore <= 30 ? 'text-emerald-600' : simulationResults.riskScore <= 80 ? 'text-amber-600' : 'text-red-600'}`} />
                <span className={`font-medium ${simulationResults.riskScore <= 30 ? 'text-emerald-800' : simulationResults.riskScore <= 80 ? 'text-amber-800' : 'text-red-800'}`}>
                  Risk Score
                </span>
              </div>
              <div className={`text-2xl font-medium ${simulationResults.riskScore <= 30 ? 'text-emerald-900' : simulationResults.riskScore <= 80 ? 'text-amber-900' : 'text-red-900'}`}>
                {simulationResults.riskScore}/100
              </div>
              <div className={`text-sm ${simulationResults.riskScore <= 30 ? 'text-emerald-700' : simulationResults.riskScore <= 80 ? 'text-amber-700' : 'text-red-700'}`}>
                {simulationResults.riskScore <= 30 ? 'Low risk' : simulationResults.riskScore <= 80 ? 'Medium risk' : 'High risk'}
              </div>
            </div>

            <div className={`bg-gradient-to-r ${simulationResults.timeToBreakeven ? 'from-amber-50 to-amber-100 border-amber-200' : 'from-emerald-50 to-emerald-100 border-emerald-200'} border rounded-2xl p-4`}>
              <div className="flex items-center gap-2 mb-2">
                <Clock className={`h-4 w-4 ${simulationResults.timeToBreakeven ? 'text-amber-600' : 'text-emerald-600'}`} />
                <span className={`font-medium ${simulationResults.timeToBreakeven ? 'text-amber-800' : 'text-emerald-800'}`}>
                  Breakeven
                </span>
              </div>
              <div className={`text-2xl font-medium ${simulationResults.timeToBreakeven ? 'text-amber-900' : 'text-emerald-900'}`}>
                {simulationResults.timeToBreakeven ? `${simulationResults.timeToBreakeven}mo` : 'N/A'}
              </div>
              <div className={`text-sm ${simulationResults.timeToBreakeven ? 'text-amber-700' : 'text-emerald-700'}`}>
                {simulationResults.timeToBreakeven ? 'Recovery time' : 'Positive scenario'}
              </div>
            </div>
          </div>

          {/* Key Insights */}
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                Key Insights
              </h3>
              <div className="space-y-2">
                {simulationResults.keyInsights.map((insight, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <div className="w-1.5 h-1.5 bg-brand-primary rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-gray-700">{insight}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Target className="h-4 w-4 text-brand-primary" />
                Recommendations
              </h3>
              <div className="space-y-2">
                {simulationResults.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <ArrowRight className="h-4 w-4 text-brand-primary mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Dr. Sigmund's Advice */}
          <div className="mt-6 bg-gradient-to-r from-violet-50 to-violet-100 border border-violet-200 rounded-2xl p-6">
            <div className="flex items-start gap-4">
              <DrSigmundSpendAvatar
                size="sm"
                mood={simulationResults.cashFlowImpact >= 0 ? "encouraging" : "reassuring"}
                showMessage={false}
                animated={true}
                variant="professional"
              />
              <div>
                <h3 className="font-medium text-violet-800 mb-2">Dr. Sigmund's Therapeutic Perspective</h3>
                <p className="text-sm text-violet-700 leading-relaxed">{simulationResults.drSigmundAdvice}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Accordion Sections */}
      {expandedSection === 'howToUse' && (
        <div className="mt-6 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <h3 className="font-medium text-gray-900 mb-4">🚀 How to Use the Scenario Engine</h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div className="bg-gradient-to-r from-brand-primary-lightest to-brand-primary-lighter border border-brand-primary-light rounded-xl p-4">
              <div className="font-medium text-brand-primary-dark mb-2">1. Choose Scenario Type</div>
              <p className="text-brand-primary">Select from income, expense, timing, client, or investment scenarios based on your current decision</p>
            </div>
            <div className="bg-gradient-to-r from-brand-primary-lightest to-brand-primary-lighter border border-brand-primary-light rounded-xl p-4">
              <div className="font-medium text-brand-primary-dark mb-2">2. Configure Variables</div>
              <p className="text-brand-primary">Adjust current vs proposed values, timeframes, and confidence levels for realistic modeling</p>
            </div>
            <div className="bg-gradient-to-r from-brand-primary-lightest to-brand-primary-lighter border border-brand-primary-light rounded-xl p-4">
              <div className="font-medium text-brand-primary-dark mb-2">3. Analyze Results</div>
              <p className="text-brand-primary">Review cash flow impact, risk scores, and Dr. Sigmund's therapeutic recommendations</p>
            </div>
          </div>
        </div>
      )}

      {expandedSection === 'therapy' && (
        <div className="mt-6 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <div className="flex items-start gap-6">
            <DrSigmundSpendAvatar
              size="md"
              mood="supportive"
              showMessage={false}
              animated={true}
              variant="professional"
            />
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Financial Decision Therapy</h2>
              <div className="bg-gradient-to-r from-brand-primary-lightest to-brand-primary-lighter border border-brand-primary-light rounded-2xl p-6">
                <h3 className="font-medium text-brand-primary-dark mb-3">Dr. Sigmund's Decision-Making Framework</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm text-brand-primary-dark">
                  <div>
                    <h4 className="font-medium mb-2">🧠 Emotional Intelligence</h4>
                    <ul className="space-y-1 text-brand-primary">
                      <li>• Acknowledge financial anxiety as normal</li>
                      <li>• Use data to reduce uncertainty</li>
                      <li>• Focus on what you can control</li>
                      <li>• Celebrate small wins and progress</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">📊 Analytical Process</h4>
                    <ul className="space-y-1 text-brand-primary">
                      <li>• Start with conservative assumptions</li>
                      <li>• Test multiple scenarios</li>
                      <li>• Consider best/worst/likely cases</li>
                      <li>• Plan for unexpected outcomes</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Disclaimer - Always shown after simulation */}
      {simulationResults && (
        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-medium text-yellow-900 mb-2">Scenario Simulation Disclaimer</h3>
              <p className="text-sm text-yellow-800 leading-relaxed">
                This simulation engine provides estimates for planning purposes only. Actual results may vary based on market conditions, 
                client behavior, and unforeseen circumstances. Dr. Sigmund's advice is designed to reduce anxiety and provide perspective, 
                but should not replace professional financial or business consulting when making major decisions.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}