'use client'

import { useState, useEffect } from 'react'
import { 
  Send, 
  Bot, 
  User, 
  Car, 
  FileText, 
  UserPlus,
  TrendingUp, 
  Building,
  CreditCard,
  Home,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Activity,
  Target,
  Calculator,
  BarChart3,
  MessageCircle,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Settings,
  TrendingDown
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ChatMessage {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  scenario?: ScenarioResult
}

interface ScenarioResult {
  title: string
  description: string
  financialImpact: {
    monthlyChange: number
    annualChange: number
    taxImpact: number
    cashFlowImpact: number
  }
  recommendation: string
  confidence: 'high' | 'medium' | 'low'
}

interface QuickScenario {
  id: string
  title: string
  description: string
  icon: any
  color: string
  example: string
}

interface TechnicalParameter {
  id: string
  name: string
  category: string
  currentValue: number
  min: number
  max: number
  step: number
  unit: string
  description: string
}

const TECHNICAL_PARAMETERS: TechnicalParameter[] = [
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
    description: 'Average monthly gross revenue'
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
    description: 'Monthly new client acquisition rate'
  },
  {
    id: 'pricing_adjustment',
    name: 'Service Price Change',
    category: 'Revenue',
    currentValue: 0,
    min: -20,
    max: 30,
    step: 1,
    unit: '%',
    description: 'Price adjustment for services'
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
    description: 'Monthly operational costs'
  },
  {
    id: 'staff_costs',
    name: 'Staff & Contractors',
    category: 'Costs',
    currentValue: 12000,
    min: 0,
    max: 30000,
    step: 1000,
    unit: '€',
    description: 'Monthly employee and contractor costs'
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
    description: 'Monthly marketing budget'
  }
]

const QUICK_SCENARIOS: QuickScenario[] = [
  {
    id: 'afford-purchase',
    title: 'Can I Afford This?',
    description: 'Cash flow timing for purchases',
    icon: Calculator,
    color: 'bg-green-500',
    example: 'When can I afford to buy a €3,000 laptop?'
  },
  {
    id: 'late-payment',
    title: 'Late Payment Impact',
    description: 'Cash flow with payment delays',
    icon: AlertTriangle,
    color: 'bg-red-500',
    example: 'If customer X pays 20 days late, will I have enough for payroll?'
  },
  {
    id: 'company-car',
    title: 'Buy a Company Car',
    description: 'Tax deduction vs lease vs cash flow',
    icon: Car,
    color: 'bg-blue-500',
    example: 'What if I buy a €25,000 company car?'
  },
  {
    id: 'delay-invoice',
    title: 'Delay Big Invoice',
    description: 'Income timing for tax optimization',
    icon: FileText,
    color: 'bg-purple-500',
    example: 'Should I invoice this €15,000 project in January?'
  },
  {
    id: 'hire-help',
    title: 'Hire Someone',
    description: 'Staff costs vs productivity gains',
    icon: UserPlus,
    color: 'bg-orange-500',
    example: 'What if I hire part-time help for €1,500/month?'
  },
  {
    id: 'raise-prices',
    title: 'Raise My Prices',
    description: 'Client retention vs revenue increase',
    icon: TrendingUp,
    color: 'bg-indigo-500',
    example: 'What if I increase my hourly rate by €15?'
  }
]

export default function ScenarioSimulationDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'bot',
      content: "Hello! I'm Dr. Sigmund Spend. I'm here to help you work through those \"what if\" financial questions that keep you up at night. What business decision are you thinking about?",
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [currentScenario, setCurrentScenario] = useState<ScenarioResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [technicalParams, setTechnicalParams] = useState<Record<string, number>>({})
  const [advancedResults, setAdvancedResults] = useState<any[]>([])

  const handleSendMessage = async (message?: string) => {
    const messageText = message || inputMessage.trim()
    if (!messageText) return

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: messageText,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsAnalyzing(true)

    // Simulate Dr. Sigmund processing
    setTimeout(() => {
      const botResponse = analyzeScenario(messageText)
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: botResponse.content,
        timestamp: new Date(),
        scenario: botResponse.scenario
      }

      setMessages(prev => [...prev, botMessage])
      setCurrentScenario(botResponse.scenario)
      setIsAnalyzing(false)
    }, 1500)
  }

  const analyzeScenario = (input: string): { content: string; scenario?: ScenarioResult } => {
    const lowerInput = input.toLowerCase()

    // Affordability/timing scenario
    if (lowerInput.includes('afford') || lowerInput.includes('when can i') || lowerInput.includes('laptop') || lowerInput.includes('equipment')) {
      const amount = extractAmount(input) || 3000
      const monthlyCashFlow = 8000 // Assumed monthly available cash flow
      const monthsToSave = Math.ceil(amount / monthlyCashFlow)
      
      return {
        content: `Ah, the classic "can I afford this" anxiety! For a €${amount.toLocaleString()} purchase, let me help you think this through:

Based on typical solopreneur cash flow patterns, if you have €${monthlyCashFlow.toLocaleString()} available monthly after all expenses, you could afford this in ${monthsToSave} month${monthsToSave === 1 ? '' : 's'}.

But here's my therapeutic advice: Can you afford to wait that long? If this purchase helps you earn more or work more efficiently, it might pay for itself.

The sweet spot: Finance it if it generates income, save for it if it's just nice-to-have.`,
        scenario: {
          title: `Purchase Planning - €${amount.toLocaleString()}`,
          description: 'Cash flow timing analysis',
          financialImpact: {
            monthlyChange: amount > monthlyCashFlow ? -Math.round(amount / 12) : -amount, // If financed vs cash
            annualChange: amount > monthlyCashFlow ? -amount : 0,
            taxImpact: Math.round(amount * 0.21), // VAT back if business expense
            cashFlowImpact: -amount
          },
          recommendation: `${monthsToSave <= 2 ? 'Buy now with cash' : 'Consider financing or wait 2-3 months'}`,
          confidence: 'high'
        }
      }
    }

    // Late payment scenario
    if (lowerInput.includes('late') || lowerInput.includes('20 days') || lowerInput.includes('payroll') || lowerInput.includes('customer') && lowerInput.includes('pay')) {
      const invoiceAmount = extractAmount(input) || 10000
      const payrollAmount = 5000 // Assumed monthly payroll
      const currentCash = 15000 // Assumed current cash position
      const daysLate = input.match(/(\d+)\s*days/)?.[1] ? parseInt(input.match(/(\d+)\s*days/)![1]) : 20
      
      return {
        content: `Ugh, late payments - every freelancer's nightmare! Let's work through the math to reduce your anxiety:

If that €${invoiceAmount.toLocaleString()} payment is ${daysLate} days late, and your payroll is €${payrollAmount.toLocaleString()}, here's the situation:

Current runway: With €${currentCash.toLocaleString()} in the bank, you have about ${Math.round(currentCash / payrollAmount)} months of payroll covered.

${currentCash >= payrollAmount * 2 
  ? "Good news: You should be fine for payroll even with the delay." 
  : "Tight situation: You might need a bridge loan or to delay some payments."
}

My advice: Always keep 3 months of fixed costs (including payroll) in the bank. Late payments happen!`,
        scenario: {
          title: `Late Payment Impact - ${daysLate} days`,
          description: 'Cash flow stress test with payment delays',
          financialImpact: {
            monthlyChange: 0, // No change in total income, just timing
            annualChange: 0,
            taxImpact: 0,
            cashFlowImpact: -invoiceAmount // Temporary cash flow impact
          },
          recommendation: currentCash >= payrollAmount * 3 
            ? 'Safe - you have adequate reserves' 
            : 'Consider invoice factoring or line of credit',
          confidence: 'high'
        }
      }
    }

    // Company car scenario
    if (lowerInput.includes('car') || lowerInput.includes('vehicle')) {
      const amount = extractAmount(input) || 25000
      return {
        content: `Ah, a company car! Great thinking for tax optimization. For a €${amount.toLocaleString()} car, here's what I see:

The good news: You'll save about €${Math.round(amount * 0.33)} in taxes through deductions. Plus, fuel, insurance, and maintenance are all deductible.

The reality check: This ties up €${amount.toLocaleString()} in cash flow. Make sure you have 3-6 months of expenses saved first.

My recommendation: If you're driving for business regularly and have stable income, this could save you €200-400 monthly in total transport costs.`,
        scenario: {
          title: `Company Car - €${amount.toLocaleString()}`,
          description: 'Purchase vs lease analysis with tax implications',
          financialImpact: {
            monthlyChange: -Math.round(amount / 48), // 4-year financing
            annualChange: -Math.round(amount * 0.25), // Net cost after tax benefits
            taxImpact: Math.round(amount * 0.33), // Tax savings
            cashFlowImpact: -amount
          },
          recommendation: 'Good investment if business driving >15,000km/year',
          confidence: 'high'
        }
      }
    }

    // Invoice delay scenario
    if (lowerInput.includes('invoice') || lowerInput.includes('delay') || lowerInput.includes('january')) {
      const amount = extractAmount(input) || 15000
      return {
        content: `Smart tax thinking! Delaying that €${amount.toLocaleString()} invoice until January could indeed save you money.

If you're close to jumping tax brackets, this could save you €${Math.round(amount * 0.1)} to €${Math.round(amount * 0.15)} in taxes.

But let's be honest - can you afford to wait for that money? Cash flow beats tax optimization if you need the funds for operations.

The sweet spot: Delay it only if you're comfortable financially and it keeps you in a lower tax bracket.`,
        scenario: {
          title: `Invoice Timing - €${amount.toLocaleString()}`,
          description: 'Tax year optimization strategy',
          financialImpact: {
            monthlyChange: 0,
            annualChange: Math.round(amount * 0.12), // Tax savings
            taxImpact: Math.round(amount * 0.12),
            cashFlowImpact: -amount // Delayed income
          },
          recommendation: 'Delay if cash flow allows and tax bracket benefits exist',
          confidence: 'medium'
        }
      }
    }

    // Hiring scenario
    if (lowerInput.includes('hire') || lowerInput.includes('help') || lowerInput.includes('employee')) {
      const monthlyRate = extractAmount(input) || 1500
      return {
        content: `Hiring help - the eternal solopreneur dilemma! At €${monthlyRate}/month, here's the real math:

Direct cost: €${(monthlyRate * 1.35 * 12).toLocaleString()} annually (including social charges)
But if they free up 20 hours/week of your time, and you bill at €75/hour, that's €78,000 in potential extra revenue.

The anxiety part: Yes, it's scary to have that fixed cost. Start part-time, measure their impact after 3 months.

My advice: If you're turning down work because you're too busy, this pays for itself quickly.`,
        scenario: {
          title: `Hiring Help - €${monthlyRate}/month`,
          description: 'Staff investment vs productivity gains',
          financialImpact: {
            monthlyChange: Math.round(-monthlyRate * 1.35 + (monthlyRate * 0.8)), // Net after productivity
            annualChange: Math.round(monthlyRate * 12 * 0.5), // Conservative estimate
            taxImpact: Math.round(monthlyRate * 12 * 0.33), // Deductible
            cashFlowImpact: Math.round(-monthlyRate * 1.35 * 12)
          },
          recommendation: 'Start part-time if turning down work due to capacity',
          confidence: 'medium'
        }
      }
    }

    // Price increase scenario
    if (lowerInput.includes('price') || lowerInput.includes('rate') || lowerInput.includes('increase')) {
      const increase = extractAmount(input) || 15
      const currentRate = 65 // Assumed current rate
      return {
        content: `Raising your rates - I love this anxiety! From €${currentRate} to €${currentRate + increase}/hour is a ${Math.round((increase/currentRate) * 100)}% increase.

The fear: "I'll lose all my clients!"
The reality: You'll lose maybe 10-20%, but your income will still increase significantly.

At 30 billable hours/week, this adds €${(increase * 30 * 52).toLocaleString()} annually. Even if you lose 3 clients and work 20% less, you're still ahead by €${Math.round(increase * 30 * 52 * 0.8).toLocaleString()}.

Start with new clients first, then gradually increase existing ones.`,
        scenario: {
          title: `Rate Increase - €${increase}/hour`,
          description: 'Revenue increase vs client retention analysis',
          financialImpact: {
            monthlyChange: Math.round(increase * 30 * 4.33 * 0.8), // 20% client loss
            annualChange: Math.round(increase * 30 * 52 * 0.8),
            taxImpact: -Math.round(increase * 30 * 52 * 0.8 * 0.33), // Additional taxes
            cashFlowImpact: Math.round(increase * 30 * 52 * 0.8)
          },
          recommendation: 'Test with new clients first, gradual rollout to existing',
          confidence: 'high'
        }
      }
    }

    // Default response
    return {
      content: `I hear you're thinking about a business decision. I'm here to help work through the financial anxiety! 

Could you tell me more specifically? For example:
- "What if I buy a €25,000 company car?"
- "Should I delay invoicing this €10,000 project until January?"
- "What if I hire someone for €1,200/month?"
- "Should I raise my hourly rate by €10?"

The more specific you are, the better I can help you see the real financial impact!`
    }
  }

  const extractAmount = (text: string): number | null => {
    const match = text.match(/€?(\d{1,3}(?:,\d{3})*|\d+)/g)
    if (match) {
      const cleanAmount = match[0].replace(/[€,]/g, '')
      return parseInt(cleanAmount)
    }
    return null
  }

  const handleQuickScenario = (scenario: QuickScenario) => {
    handleSendMessage(scenario.example)
  }

  // Prepare chart data
  const chartData = currentScenario ? [
    {
      name: 'Monthly Impact',
      current: 0,
      scenario: currentScenario.financialImpact.monthlyChange
    },
    {
      name: 'Annual Impact',
      current: 0,
      scenario: Math.round(currentScenario.financialImpact.annualChange / 12)
    },
    {
      name: 'Tax Impact',
      current: 0,
      scenario: Math.round(currentScenario.financialImpact.taxImpact / 12)
    }
  ] : []

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-medium mb-2">What-If Scenarios with Dr. Sigmund Spend</h1>
            <p className="text-purple-100">Ask me about any business decision that's on your mind</p>
          </div>
          <div className="flex items-center space-x-2">
            <MessageCircle className="h-6 w-6" />
            <span className="text-sm">Ready to chat</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-md flex flex-col h-[600px]">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex items-start space-x-3 ${message.type === 'user' ? 'justify-end' : ''}`}>
                {message.type === 'bot' && (
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white rounded-lg rounded-tr-none' 
                    : 'bg-gray-100 text-gray-900 rounded-lg rounded-tl-none'
                } p-4`}>
                  <div className="whitespace-pre-line text-sm leading-relaxed">
                    {message.content}
                  </div>
                  {message.scenario && (
                    <div className="mt-3 p-3 bg-white bg-opacity-20 rounded-lg text-xs">
                      <div className="font-medium">{message.scenario.title}</div>
                      <div className="text-xs opacity-75 mt-1">Confidence: {message.scenario.confidence}</div>
                    </div>
                  )}
                </div>
                {message.type === 'user' && (
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4 text-gray-600" />
                  </div>
                )}
              </div>
            ))}
            {isAnalyzing && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white animate-pulse" />
                </div>
                <div className="bg-gray-100 rounded-lg rounded-tl-none p-4">
                  <div className="text-sm text-gray-600">Dr. Sigmund is analyzing your scenario...</div>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-3">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about any business decision... What if I..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputMessage.trim()}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* Quick Scenarios */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Lightbulb className="h-5 w-5 text-yellow-500" />
              <h3 className="text-lg font-medium text-gray-900">Common Questions</h3>
            </div>
            <div className="space-y-3">
              {QUICK_SCENARIOS.map((scenario) => (
                <button
                  key={scenario.id}
                  onClick={() => handleQuickScenario(scenario)}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 ${scenario.color} rounded-lg flex items-center justify-center`}>
                      <scenario.icon className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{scenario.title}</div>
                      <div className="text-xs text-gray-500">{scenario.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Current Scenario Results */}
          {currentScenario && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Financial Impact</h3>
              
              {/* Impact Summary */}
              <div className="space-y-3 mb-6">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Monthly Change</span>
                  <span className={`text-sm font-medium ${
                    currentScenario.financialImpact.monthlyChange >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {currentScenario.financialImpact.monthlyChange >= 0 ? '+' : ''}€{currentScenario.financialImpact.monthlyChange.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Annual Impact</span>
                  <span className={`text-sm font-medium ${
                    currentScenario.financialImpact.annualChange >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {currentScenario.financialImpact.annualChange >= 0 ? '+' : ''}€{currentScenario.financialImpact.annualChange.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Tax Impact</span>
                  <span className={`text-sm font-medium ${
                    currentScenario.financialImpact.taxImpact >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {currentScenario.financialImpact.taxImpact >= 0 ? '+' : ''}€{currentScenario.financialImpact.taxImpact.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Quick Chart */}
              {chartData.length > 0 && (
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip formatter={(value: number) => [`€${value}`, 'Impact']} />
                      <Bar dataKey="scenario" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Confidence Indicator */}
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Target className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-900">
                    Confidence: {currentScenario.confidence}
                  </span>
                </div>
                <p className="text-xs text-blue-700 mt-1">
                  {currentScenario.recommendation}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Advanced Technical Simulation (Collapsed by default) */}
      <div className="bg-white rounded-xl shadow-md">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full p-6 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Settings className="h-5 w-5 text-gray-600" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Advanced Parameter Simulation</h3>
              <p className="text-sm text-gray-500">For power users who want granular control over business variables</p>
            </div>
          </div>
          {showAdvanced ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {showAdvanced && (
          <div className="border-t border-gray-200 p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Technical Parameters */}
              <div className="lg:col-span-2 space-y-6">
                {Object.entries(
                  TECHNICAL_PARAMETERS.reduce((acc, param) => {
                    if (!acc[param.category]) acc[param.category] = []
                    acc[param.category].push(param)
                    return acc
                  }, {} as Record<string, TechnicalParameter[]>)
                ).map(([category, params]) => (
                  <div key={category} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                      {category === 'Revenue' && <TrendingUp className="h-4 w-4 mr-2 text-green-600" />}
                      {category === 'Costs' && <TrendingDown className="h-4 w-4 mr-2 text-red-600" />}
                      {category}
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {params.map(param => (
                        <div key={param.id}>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-xs font-medium text-gray-600">
                              {param.name}
                            </label>
                            <span className="text-sm font-medium text-gray-900">
                              {param.unit === '€' ? '€' : ''}{(technicalParams[param.id] || param.currentValue).toLocaleString()}{param.unit === '%' ? '%' : ''}
                            </span>
                          </div>
                          <input
                            type="range"
                            min={param.min}
                            max={param.max}
                            step={param.step}
                            value={technicalParams[param.id] || param.currentValue}
                            onChange={(e) => setTechnicalParams(prev => ({
                              ...prev,
                              [param.id]: Number(e.target.value)
                            }))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                          />
                          <p className="text-xs text-gray-500 mt-1">{param.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Advanced Results */}
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Calculated Metrics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Net Monthly Profit</span>
                      <span className="font-medium">€{calculateAdvancedNetProfit().toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Annual Cash Flow</span>
                      <span className="font-medium">€{(calculateAdvancedNetProfit() * 12).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Break-even Days</span>
                      <span className="font-medium">{calculateAdvancedBreakeven()} days</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Marketing ROI</span>
                      <span className="font-medium">{calculateAdvancedMarketingROI()}%</span>
                    </div>
                  </div>
                </div>

                <div className="text-xs text-gray-500 p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <Target className="h-3 w-3 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-blue-900">Advanced Mode</p>
                      <p>These parameters provide granular control for detailed financial modeling and scenario analysis.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )

  function calculateAdvancedNetProfit(): number {
    const revenue = technicalParams.monthly_revenue || 45000
    const growth = (technicalParams.client_growth_rate || 15) / 100
    const pricing = (technicalParams.pricing_adjustment || 0) / 100
    const costs = (technicalParams.operating_expenses || 18000) + 
                  (technicalParams.staff_costs || 12000) + 
                  (technicalParams.marketing_spend || 3000)
    
    const adjustedRevenue = revenue * (1 + growth * 0.5) * (1 + pricing)
    return Math.round(adjustedRevenue - costs)
  }

  function calculateAdvancedBreakeven(): number {
    const fixedCosts = (technicalParams.operating_expenses || 18000) + (technicalParams.staff_costs || 12000)
    const revenue = technicalParams.monthly_revenue || 45000
    const variableCostRatio = 0.3
    const dailyRevenue = revenue / 30
    const dailyFixedCosts = fixedCosts / 30
    
    return Math.round(dailyFixedCosts / (dailyRevenue * (1 - variableCostRatio)))
  }

  function calculateAdvancedMarketingROI(): number {
    const marketingSpend = technicalParams.marketing_spend || 3000
    const growth = (technicalParams.client_growth_rate || 15) / 100
    const revenue = technicalParams.monthly_revenue || 45000
    const attributedRevenue = revenue * growth * 0.6
    
    return Math.round((attributedRevenue / marketingSpend) * 100)
  }
}