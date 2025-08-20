'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  User, 
  Lightbulb, 
  Target, 
  BarChart3, 
  TrendingUp, 
  Heart, 
  Brain,
  Calculator,
  DollarSign,
  Shield,
  Zap,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Euro,
  Building2,
  PieChart
} from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  type?: 'text' | 'insight' | 'chart' | 'recommendation' | 'tool_result' | 'scenario_analysis'
  metadata?: {
    chartData?: any
    insightType?: string
    confidence?: number
    toolUsed?: string
    financialTool?: string
  }
}

interface FinancialTool {
  name: string
  description: string
  icon: React.ReactNode
  action: () => any
}

export default function EnhancedDrSigmundChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello! I'm Dr. Sigmund Spend, your AI financial therapist with enhanced analytical capabilities. 

I can now help you with:
• **Emotional financial guidance** - Understanding your money feelings
• **Scenario analysis** - "What if" simulations for big decisions  
• **Cash flow forecasting** - Predicting your financial future
• **Tax optimization** - Multi-jurisdiction strategies
• **Client payment prediction** - For business owners
• **Investment analysis** - Portfolio and treasury management

How are you feeling about your finances today? What would you like to explore together?`,
      timestamp: new Date(),
      type: 'text'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [availableTools, setAvailableTools] = useState<FinancialTool[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Financial Tools Available to Dr. Sigmund
  const financialTools: FinancialTool[] = [
    {
      name: 'Scenario Simulation',
      description: 'Run what-if financial scenarios',
      icon: <Brain className="h-4 w-4" />,
      action: () => generateScenarioAnalysis()
    },
    {
      name: 'Cash Flow Forecast',
      description: 'Predict future cash flow',
      icon: <TrendingUp className="h-4 w-4" />,
      action: () => generateCashFlowForecast()
    },
    {
      name: 'Tax Optimization',
      description: 'Multi-jurisdiction tax strategies',
      icon: <Calculator className="h-4 w-4" />,
      action: () => generateTaxOptimization()
    },
    {
      name: 'Client Payment Prediction',
      description: 'Predict late payments and client risk',
      icon: <Clock className="h-4 w-4" />,
      action: () => generatePaymentPrediction()
    },
    {
      name: 'Investment Analysis',
      description: 'Portfolio and treasury analysis',
      icon: <PieChart className="h-4 w-4" />,
      action: () => generateInvestmentAnalysis()
    },
    {
      name: 'Budget Variance Analysis',
      description: 'Analyze budget performance',
      icon: <BarChart3 className="h-4 w-4" />,
      action: () => generateBudgetAnalysis()
    }
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const generateScenarioAnalysis = () => {
    return {
      type: 'scenario_analysis',
      data: {
        scenarios: [
          {
            name: 'Income Increase',
            description: 'Increasing hourly rate from €75 to €95',
            impact: '+€2,400/month',
            risk: 'Low',
            confidence: 85
          },
          {
            name: 'New Client',
            description: 'Adding a recurring €3,500/month client',
            impact: '+€3,500/month',
            risk: 'Medium',
            confidence: 70
          },
          {
            name: 'Office Expense',
            description: 'Renting office space at €1,200/month',
            impact: '-€1,200/month',
            risk: 'Low',
            confidence: 95
          }
        ],
        netImpact: '+€4,700/month',
        timeToBreakeven: 'Immediate positive impact',
        riskScore: 25
      }
    }
  }

  const generateCashFlowForecast = () => {
    return {
      type: 'cash_flow_forecast',
      data: {
        forecast: [
          { month: 'Feb 2025', income: 14200, expenses: 8800, net: 5400 },
          { month: 'Mar 2025', income: 15600, expenses: 9100, net: 6500 },
          { month: 'Apr 2025', income: 13800, expenses: 8500, net: 5300 },
          { month: 'May 2025', income: 16200, expenses: 9300, net: 6900 },
          { month: 'Jun 2025', income: 15400, expenses: 9000, net: 6400 }
        ],
        trends: {
          avgMonthlyNet: 6120,
          growthRate: 8.5,
          volatility: 'Low'
        },
        insights: [
          'Strong positive cash flow trend',
          'Income growing faster than expenses',
          'Good consistency month-to-month'
        ]
      }
    }
  }

  const generateTaxOptimization = () => {
    return {
      type: 'tax_optimization',
      data: {
        jurisdiction: 'Belgium',
        currentTaxBurden: 42000,
        optimizedTaxBurden: 36500,
        savings: 5500,
        strategies: [
          {
            name: 'Business Expense Optimization',
            savings: 2800,
            complexity: 'Medium',
            description: 'Maximize home office, training, and equipment deductions'
          },
          {
            name: 'Professional vs Company Structure',
            savings: 2700,
            complexity: 'High',
            description: 'Consider BVBA/SRL incorporation for tax efficiency'
          }
        ],
        confidence: 88
      }
    }
  }

  const generatePaymentPrediction = () => {
    return {
      type: 'payment_prediction',
      data: {
        totalOutstanding: 43500,
        overdueAmount: 3200,
        highRiskAmount: 8200,
        predictions: [
          {
            client: 'Tech Solutions Inc.',
            amount: 4500,
            dueDate: '2025-02-14',
            predictedDate: '2025-02-18',
            lateRisk: 25,
            riskLevel: 'Low'
          },
          {
            client: 'StartUp Ventures',
            amount: 8200,
            dueDate: '2025-02-09',
            predictedDate: '2025-02-25',
            lateRisk: 78,
            riskLevel: 'High'
          }
        ],
        avgPaymentTime: 34
      }
    }
  }

  const generateInvestmentAnalysis = () => {
    return {
      type: 'investment_analysis',
      data: {
        surplusAvailable: 42300,
        emergencyFundTarget: 30000,
        availableForInvestment: 12300,
        recommendations: [
          {
            name: 'EU Government Bonds',
            expectedReturn: 3.2,
            risk: 'Low',
            allocation: 40
          },
          {
            name: 'EU ETF Portfolio',
            expectedReturn: 6.5,
            risk: 'Medium',
            allocation: 60
          }
        ],
        portfolioReturn: 5.2,
        riskScore: 35
      }
    }
  }

  const generateBudgetAnalysis = () => {
    return {
      type: 'budget_analysis',
      data: {
        totalBudget: 12000,
        actualSpending: 11200,
        variance: -800,
        categories: [
          { name: 'Business Tools', budget: 800, actual: 950, variance: 150 },
          { name: 'Marketing', budget: 1200, actual: 980, variance: -220 },
          { name: 'Office Expenses', budget: 600, actual: 580, variance: -20 }
        ],
        performance: 93.3,
        insights: [
          'Overall spending under budget by 6.7%',
          'Business tools category over budget',
          'Marketing spend efficiently managed'
        ]
      }
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
      type: 'text'
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response with tool integration
    setTimeout(() => {
      const assistantMessage = generateEnhancedResponse(inputValue)
      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1500 + Math.random() * 1000)
  }

  const generateEnhancedResponse = (userInput: string): Message => {
    const input = userInput.toLowerCase()
    
    // Enhanced responses with tool integration
    if (input.includes('scenario') || input.includes('what if') || input.includes('simulation')) {
      const scenarioData = generateScenarioAnalysis()
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Let me run a scenario analysis for you using my advanced simulation tools...

**Current Scenario Results:**

**Scenarios Analyzed:**
${scenarioData.data.scenarios.map(s => 
  `• **${s.name}**: ${s.description} (Impact: ${s.impact}, Risk: ${s.risk})`
).join('\n')}

**Net Impact**: ${scenarioData.data.netImpact}
**Risk Score**: ${scenarioData.data.riskScore}/100 (Low risk)
**Breakeven**: ${scenarioData.data.timeToBreakeven}

**Therapeutic Insight:**
These scenarios show positive potential! The anxiety around "what if" often comes from not having concrete data. Now that we can see the numbers, how does this make you feel? 

The risk levels are manageable, and the financial impact is strongly positive. Remember, every successful business decision starts with asking "what if" - and now you have the analytical power to explore these possibilities safely.

Would you like to explore any specific scenario in more detail, or adjust the assumptions?`,
        timestamp: new Date(),
        type: 'tool_result',
        metadata: { 
          toolUsed: 'scenario_simulation',
          confidence: 0.87,
          financialTool: 'Scenario Engine'
        }
      }
    }

    if (input.includes('cash flow') || input.includes('forecast') || input.includes('predict')) {
      const forecastData = generateCashFlowForecast()
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I've analyzed your cash flow patterns using my forecasting models...

**Cash Flow Forecast - Next 5 Months:**

${forecastData.data.forecast.map(month => 
  `**${month.month}**: Income €${month.income.toLocaleString()} | Expenses €${month.expenses.toLocaleString()} | Net €${month.net.toLocaleString()}`
).join('\n')}

**Key Insights:**
• Average monthly net cash flow: €${forecastData.data.trends.avgMonthlyNet.toLocaleString()}
• Growth rate: ${forecastData.data.trends.growthRate}% positive trend
• Volatility: ${forecastData.data.trends.volatility}

**AI Analysis:**
${forecastData.data.insights.join('\n• ')}

**Therapeutic Perspective:**
These numbers show a healthy, growing financial position! Cash flow anxiety is common, but your data reveals strong fundamentals. The consistency and growth trends suggest you're making sound financial decisions.

How does seeing this concrete forecast impact your feelings about financial security? Sometimes the anticipation is worse than the reality.`,
        timestamp: new Date(),
        type: 'tool_result',
        metadata: { 
          toolUsed: 'cash_flow_forecast',
          confidence: 0.91,
          financialTool: 'Forecasting Engine'
        }
      }
    }

    if (input.includes('tax') || input.includes('optimization') || input.includes('deduction')) {
      const taxData = generateTaxOptimization()
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I've analyzed your tax situation using multi-jurisdiction optimization models...

**Tax Optimization Analysis (${taxData.data.jurisdiction}):**

**Current vs Optimized:**
• Current tax burden: €${taxData.data.currentTaxBurden.toLocaleString()}
• Optimized tax burden: €${taxData.data.optimizedTaxBurden.toLocaleString()}
• **Potential savings: €${taxData.data.savings.toLocaleString()}/year**

**Recommended Strategies:**
${taxData.data.strategies.map(strategy => 
  `• **${strategy.name}** (${strategy.complexity} complexity): €${strategy.savings.toLocaleString()} savings\n  ${strategy.description}`
).join('\n\n')}

**Confidence Level:** ${taxData.data.confidence}%

**Therapeutic Approach to Tax Optimization:**
Tax anxiety often comes from feeling like we're "doing something wrong" or that it's too complex. But legal tax optimization is self-care - you're taking responsibility for your financial future.

These strategies are conservative and compliant. The savings represent money you can redirect toward your goals rather than unnecessary tax burden.

How do you feel about exploring these optimization strategies? Remember, we'll approach this step-by-step, ensuring you're comfortable with each decision.`,
        timestamp: new Date(),
        type: 'tool_result',
        metadata: { 
          toolUsed: 'tax_optimization',
          confidence: 0.88,
          financialTool: 'Tax Engine'
        }
      }
    }

    if (input.includes('client') || input.includes('payment') || input.includes('invoice')) {
      const paymentData = generatePaymentPrediction()
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Let me analyze your client payment patterns using AI prediction models...

**Payment Prediction Analysis:**

**Portfolio Overview:**
• Total outstanding: €${paymentData.data.totalOutstanding.toLocaleString()}
• Currently overdue: €${paymentData.data.overdueAmount.toLocaleString()}
• High-risk amount: €${paymentData.data.highRiskAmount.toLocaleString()}
• Average payment time: ${paymentData.data.avgPaymentTime} days

**Client Risk Assessment:**
${paymentData.data.predictions.map(client => 
  `• **${client.client}**: €${client.amount.toLocaleString()} due ${client.dueDate}\n  Predicted payment: ${client.predictedDate} (${client.lateRisk}% late risk - ${client.riskLevel})`
).join('\n\n')}

**Therapeutic Insight on Payment Anxiety:**
One of the biggest sources of business stress is uncertainty about when clients will pay. Now you have data-driven insights instead of worry spirals.

**Action Plan:**
• Monitor StartUp Ventures closely (high risk)
• Consider early payment incentives for slower clients
• Your overall client portfolio shows healthy diversity

How does having this predictive information change your feelings about client management? Knowledge often transforms anxiety into actionable confidence.`,
        timestamp: new Date(),
        type: 'tool_result',
        metadata: { 
          toolUsed: 'payment_prediction',
          confidence: 0.84,
          financialTool: 'Payment Intelligence'
        }
      }
    }

    if (input.includes('invest') || input.includes('portfolio') || input.includes('surplus')) {
      const investmentData = generateInvestmentAnalysis()
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I've analyzed your investment opportunities using treasury management models...

**Investment Analysis:**

**Available Capital:**
• Current surplus: €${investmentData.data.surplusAvailable.toLocaleString()}
• Emergency fund target: €${investmentData.data.emergencyFundTarget.toLocaleString()}
• **Available for investment: €${investmentData.data.availableForInvestment.toLocaleString()}**

**Recommended Portfolio Allocation:**
${investmentData.data.recommendations.map(rec => 
  `• **${rec.name}**: ${rec.allocation}% allocation\n  Expected return: ${rec.expectedReturn}% (${rec.risk} risk)`
).join('\n\n')}

**Portfolio Metrics:**
• Expected portfolio return: ${investmentData.data.portfolioReturn}%
• Overall risk score: ${investmentData.data.riskScore}/100 (Conservative-Moderate)

**Therapeutic Investment Philosophy:**
Investment anxiety often comes from fear of loss or not understanding the options. This analysis shows conservative strategies that preserve capital while generating reasonable returns.

Remember: investing surplus cash should reduce anxiety, not create it. We're looking at low-risk options that match your risk tolerance.

How do you feel about taking this next step in your financial journey? We can start small and build confidence over time.`,
        timestamp: new Date(),
        type: 'tool_result',
        metadata: { 
          toolUsed: 'investment_analysis',
          confidence: 0.89,
          financialTool: 'Treasury Engine'
        }
      }
    }

    if (input.includes('budget') || input.includes('variance') || input.includes('spending')) {
      const budgetData = generateBudgetAnalysis()
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Let me analyze your budget performance using advanced tracking algorithms...

**Budget Variance Analysis:**

**Overall Performance:**
• Total budget: €${budgetData.data.totalBudget.toLocaleString()}
• Actual spending: €${budgetData.data.actualSpending.toLocaleString()}
• Variance: €${budgetData.data.variance.toLocaleString()} (${budgetData.data.performance}% of budget)

**Category Breakdown:**
${budgetData.data.categories.map(cat => 
  `• **${cat.name}**: Budget €${cat.budget} | Actual €${cat.actual} | Variance €${cat.variance}`
).join('\n')}

**AI Insights:**
${budgetData.data.insights.map(insight => `• ${insight}`).join('\n')}

**Therapeutic Budgeting Approach:**
You're performing excellently! Being under budget by 6.7% shows discipline without deprivation. The slight overage in business tools likely represents smart investments in your productivity.

**Emotional Budgeting Reflection:**
How does seeing this data make you feel about your spending habits? Many people judge themselves harshly for any budget variance, but your performance shows healthy financial management.

Remember: budgets are tools for empowerment, not restriction. You're using money intentionally to support your goals.`,
        timestamp: new Date(),
        type: 'tool_result',
        metadata: { 
          toolUsed: 'budget_analysis',
          confidence: 0.92,
          financialTool: 'Budget Analyzer'
        }
      }
    }

    // Enhanced default response with tool awareness
    return {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `I hear you, and I want you to know that whatever you're experiencing with your finances is completely valid.

As your enhanced AI financial therapist, I now have access to powerful analytical tools that can transform financial anxiety into actionable insights:

**I can help you with:**
• **Scenario planning** - Explore "what if" possibilities safely
• **Cash flow forecasting** - Predict your financial future with confidence
• **Tax optimization** - Legal strategies to minimize your tax burden
• **Client payment prediction** - Reduce uncertainty about when you'll be paid
• **Investment analysis** - Make informed decisions about surplus cash
• **Budget analysis** - Understand your spending patterns

**My Enhanced Approach:**
I combine deep financial analysis with therapeutic support. Numbers without emotional context can feel cold, but data with compassionate guidance builds both confidence and competence.

What area of your finances would you like to explore together? I can run real analysis while helping you process the emotional aspects of financial decision-making.

Some starting points:
• "Can you analyze my cash flow forecasts?"
• "What scenarios should I consider for my business?"
• "Help me understand my tax optimization options"
• "I'm worried about client payments - can you predict them?"

What feels most important to address right now?`,
      timestamp: new Date(),
      type: 'insight',
      metadata: { 
        insightType: 'enhanced_capabilities',
        confidence: 0.95
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const renderToolResult = (data: any, type: string) => {
    switch (type) {
      case 'scenario_analysis':
        return (
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-4 mt-3">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="h-4 w-4 text-indigo-600" />
              <span className="font-medium text-indigo-800">Scenario Analysis Results</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-white rounded-lg p-3">
                <div className="font-medium text-gray-800">Net Impact</div>
                <div className="text-lg font-bold text-green-600">{data.netImpact}</div>
              </div>
              <div className="bg-white rounded-lg p-3">
                <div className="font-medium text-gray-800">Risk Score</div>
                <div className="text-lg font-bold text-blue-600">{data.riskScore}/100</div>
              </div>
            </div>
          </div>
        )
      
      case 'cash_flow_forecast':
        return (
          <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-xl p-4 mt-3">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="font-medium text-green-800">Cash Flow Forecast</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-white rounded-lg p-2 text-center">
                <div className="font-medium text-gray-600">Avg Monthly</div>
                <div className="text-sm font-bold text-green-600">€{data.trends.avgMonthlyNet.toLocaleString()}</div>
              </div>
              <div className="bg-white rounded-lg p-2 text-center">
                <div className="font-medium text-gray-600">Growth</div>
                <div className="text-sm font-bold text-blue-600">{data.trends.growthRate}%</div>
              </div>
              <div className="bg-white rounded-lg p-2 text-center">
                <div className="font-medium text-gray-600">Volatility</div>
                <div className="text-sm font-bold text-purple-600">{data.trends.volatility}</div>
              </div>
            </div>
          </div>
        )
      
      default:
        return null
    }
  }

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user'

    return (
      <div key={message.id} className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''}`}>
        {message.role === 'assistant' && (
          <DrSigmundSpendAvatar 
            size="sm" 
            showMessage={false} 
            mood={message.type === 'tool_result' ? 'analytical' : 'supportive'}
            animated={true}
          />
        )}
        
        <div className={`rounded-2xl p-4 max-w-lg ${
          isUser 
            ? 'bg-gray-100 rounded-tr-md' 
            : 'bg-gradient-to-r from-purple-50 to-blue-50 rounded-tl-md border border-purple-100'
        }`}>
          {/* Enhanced Message Type Indicator */}
          {!isUser && message.type !== 'text' && (
            <div className="flex items-center space-x-2 mb-3 pb-2 border-b border-purple-100">
              {message.type === 'insight' && <Lightbulb className="h-4 w-4 text-yellow-500" />}
              {message.type === 'recommendation' && <Target className="h-4 w-4 text-purple-500" />}
              {message.type === 'tool_result' && <Zap className="h-4 w-4 text-indigo-500" />}
              {message.type === 'scenario_analysis' && <Brain className="h-4 w-4 text-indigo-500" />}
              
              <span className="text-xs font-medium text-purple-600 capitalize">
                {message.type === 'tool_result' ? `${message.metadata?.financialTool || 'Financial Tool'} Analysis` :
                 message.type === 'insight' ? 'Therapeutic Insight' : 
                 message.type === 'recommendation' ? 'Personalized Recommendation' : 
                 'AI Analysis'}
              </span>
              
              {message.metadata?.confidence && (
                <span className="text-xs text-purple-500">
                  {Math.round(message.metadata.confidence * 100)}% confidence
                </span>
              )}
            </div>
          )}

          <div className="text-sm text-gray-800 leading-relaxed">
            {message.content.split('\n').map((paragraph, index) => {
              if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
                return <h4 key={index} className="font-semibold mt-3 mb-2 text-gray-900">{paragraph.slice(2, -2)}</h4>
              } else if (paragraph.startsWith('• ')) {
                return <li key={index} className="ml-4 mb-1 text-gray-700">{paragraph.slice(2)}</li>
              } else if (paragraph.startsWith('- ')) {
                return <li key={index} className="ml-4 mb-1 text-gray-700">{paragraph.slice(2)}</li>
              } else if (paragraph.trim()) {
                return <p key={index} className="mb-2 text-gray-800">{paragraph}</p>
              } else {
                return <br key={index} />
              }
            })}
          </div>

          {/* Render Tool Results */}
          {message.metadata?.toolUsed && (
            <div className="mt-3">
              <div className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs">
                <Zap className="h-3 w-3" />
                Tool: {message.metadata.financialTool}
              </div>
            </div>
          )}
        </div>

        {message.role === 'user' && (
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5 text-gray-600" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 p-6">
      {/* Main Chat Card */}
      <div className="max-w-4xl mx-auto w-full">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          {/* Enhanced Chat Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <DrSigmundSpendAvatar size="sm" showMessage={false} animated={true} />
                <div>
                  <h3 className="font-bold text-white">Dr. Sigmund Spend AI</h3>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-purple-100 text-sm">Enhanced • Financial Therapist + AI Tools</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1 text-purple-100 text-xs">
                <Brain className="h-3 w-3" />
                <span>6 AI Tools Active</span>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="p-6 space-y-4 h-96 overflow-y-auto flex flex-col">
            {messages.map(renderMessage)}
            
            {/* Enhanced Typing Indicator */}
            {isTyping && (
              <div className="flex items-start gap-3">
                <DrSigmundSpendAvatar size="sm" showMessage={false} isTyping={true} animated={true} />
                <div className="rounded-2xl p-4 max-w-sm rounded-tl-md bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-100">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm text-gray-500">Dr. Spend is analyzing...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Enhanced Chat Input */}
          <div className="p-4 border-t border-gray-100 bg-gradient-to-r from-purple-50 to-blue-50">
            <div className="flex items-center gap-2 bg-white rounded-full px-4 py-3 border border-gray-200 shadow-sm">
              <input 
                type="text" 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask Dr. Sigmund about scenarios, forecasts, tax optimization, or share your feelings..."
                className="flex-1 bg-transparent outline-none text-sm text-gray-600"
                disabled={isTyping}
              />
              <button 
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isTyping}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
                  inputValue.trim() && !isTyping
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
                    : 'bg-gray-200 cursor-not-allowed'
                }`}
              >
                <Send className={`w-4 h-4 ${
                  inputValue.trim() && !isTyping ? 'text-white' : 'text-gray-400'
                }`} />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Enhanced Dr. Sigmund with AI-powered financial analysis tools • Therapeutic guidance + Data insights
            </p>
          </div>
        </div>

        {/* Enhanced Info Section with Tool Showcase */}
        <div className="mt-8 bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-600" />
            Enhanced Dr. Sigmund Spend - AI Financial Therapist
          </h3>
          
          <p className="text-gray-700 text-sm leading-relaxed mb-4">
            Dr. Sigmund now combines therapeutic emotional support with powerful AI financial analysis tools. 
            He can run real financial simulations, predict cash flows, optimize taxes, and provide data-driven insights 
            while maintaining his compassionate, non-judgmental approach to your money feelings.
          </p>

          {/* Available Tools */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            {financialTools.map((tool, index) => (
              <div key={index} className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-3">
                <div className="flex items-center gap-2 mb-1">
                  {tool.icon}
                  <span className="text-xs font-medium text-indigo-800">{tool.name}</span>
                </div>
                <p className="text-xs text-indigo-600">{tool.description}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              <span>Advanced Analytics</span>
            </div>
            <div className="flex items-center gap-2">
              <Heart className="w-4 h-4 text-gray-400" />
              <span>Therapeutic Approach</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 w-4 text-gray-400" />
              <span>Real-Time AI Tools</span>
            </div>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mt-8 bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-purple-600" />
            How Dr. Sigmund's AI Enhancement Works
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">🧠 Therapeutic Foundation</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Emotional financial intelligence and anxiety reduction</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Non-judgmental approach to money decisions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Understanding your relationship with money</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Building confidence through knowledge</span>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-3">⚡ AI-Powered Analysis</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Real-time scenario simulations and "what-if" analysis</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Cash flow forecasting with machine learning</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Multi-jurisdiction tax optimization strategies</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Client payment prediction and risk assessment</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Sample Conversations */}
        <div className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-4">
          <h4 className="font-medium text-purple-900 mb-3">💬 Try These Conversation Starters</h4>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div className="space-y-2">
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="font-medium text-purple-800 text-xs">Scenario Planning</div>
                <p className="text-purple-700 text-xs">"What if I increase my rates to €95/hour?"</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="font-medium text-purple-800 text-xs">Cash Flow</div>
                <p className="text-purple-700 text-xs">"Can you forecast my cash flow for the next 6 months?"</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="font-medium text-purple-800 text-xs">Tax Optimization</div>
                <p className="text-purple-700 text-xs">"Help me understand my tax optimization options in Belgium"</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="font-medium text-purple-800 text-xs">Client Analysis</div>
                <p className="text-purple-700 text-xs">"I'm worried about client payments - can you analyze the risks?"</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="font-medium text-purple-800 text-xs">Investment Planning</div>
                <p className="text-purple-700 text-xs">"What should I do with my surplus cash?"</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="font-medium text-purple-800 text-xs">Emotional Support</div>
                <p className="text-purple-700 text-xs">"I'm feeling anxious about my financial future"</p>
              </div>
            </div>
          </div>
        </div>

        {/* Dr. Sigmund Philosophy */}
        <div className="mt-6 bg-white rounded-2xl shadow-xl border border-gray-100 p-4">
          <div className="flex items-start gap-4">
            <DrSigmundSpendAvatar
              size="sm"
              mood="supportive"
              showMessage={false}
              animated={true}
              variant="professional"
            />
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 mb-2">Dr. Sigmund's Enhanced Philosophy</h4>
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-3">
                <p className="text-xs text-purple-800 leading-relaxed mb-2">
                  "Technology should enhance human connection, not replace it. My AI capabilities are tools to provide you with 
                  better insights and reduce financial uncertainty, but the heart of our work together remains deeply human."
                </p>
                <p className="text-xs text-purple-800 leading-relaxed">
                  "Whether I'm running complex financial simulations or simply listening to your money worries, my goal is the same: 
                  to help you feel more confident, informed, and emotionally secure in your financial journey."
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}