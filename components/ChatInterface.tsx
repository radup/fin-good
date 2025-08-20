'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Smile, MoreHorizontal, Copy, RefreshCw, User, Bot, TrendingUp, DollarSign, AlertTriangle, Lightbulb, BarChart3, Target, Heart, Brain } from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  type?: 'text' | 'insight' | 'chart' | 'recommendation'
  metadata?: {
    chartData?: any
    insightType?: string
    confidence?: number
  }
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm Dr. Sigmund Spend. How are you feeling about money today?",
      timestamp: new Date(),
      type: 'text'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

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

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    // Simulate AI response with delay
    setTimeout(() => {
      const assistantMessage = generateAssistantResponse(inputValue)
      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1500 + Math.random() * 1000)
  }

  const generateAssistantResponse = (userInput: string): Message => {
    const input = userInput.toLowerCase()
    
    // Mock responses based on keywords
    if (input.includes('budget') || input.includes('budgeting')) {
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I understand you're interested in budgeting. This is a wonderful step toward financial wellness! 

Budgeting often brings up feelings of restriction or anxiety, but I prefer to think of it as creating a loving framework for your money. Let me help you approach this therapeutically:

**Key Questions to Consider:**
• What emotions come up when you think about tracking expenses?
• Are there spending categories that make you feel guilty or stressed?
• What are your core financial values and priorities?

Would you like to explore your budgeting goals together? I can help you create a plan that feels nurturing rather than restrictive.`,
        timestamp: new Date(),
        type: 'insight',
        metadata: { insightType: 'budgeting', confidence: 0.92 }
      }
    }
    
    if (input.includes('spend') || input.includes('spending') || input.includes('expense')) {
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Your spending patterns tell a story about your relationship with money. Let's explore this together with compassion and curiosity.

**Common Spending Triggers:**
• Emotional states (stress, celebration, boredom)
• Social pressure or comparison
• Unmet emotional needs
• Habitual patterns from childhood

**Therapeutic Approach:**
Instead of judgment, let's practice awareness. When you make purchases, try asking yourself:
- What am I really seeking right now?
- How do I feel before, during, and after spending?
- What would my ideal spending pattern look like?

Would you like to share a recent spending decision that's been on your mind? We can explore it together without judgment.`,
        timestamp: new Date(),
        type: 'insight',
        metadata: { insightType: 'spending_analysis', confidence: 0.87 }
      }
    }

    if (input.includes('anxious') || input.includes('worried') || input.includes('stress')) {
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Thank you for sharing your feelings with me. Financial anxiety is incredibly common and completely understandable - money touches every aspect of our lives.

**Immediate Grounding Techniques:**
• Take three deep breaths with me right now
• Remind yourself: "I am safe in this moment"
• Focus on what you *can* control today

**Understanding Your Anxiety:**
Financial anxiety often stems from:
- Past experiences or family money patterns
- Uncertainty about the future
- Feeling out of control
- Comparing yourself to others

Remember: You don't have to carry this burden alone. Your awareness of these feelings is already a sign of strength and growth.

What specific aspect of your finances feels most overwhelming right now? Let's break it down into manageable pieces together.`,
        timestamp: new Date(),
        type: 'insight',
        metadata: { insightType: 'emotional_support', confidence: 0.95 }
      }
    }

    if (input.includes('scenario') || input.includes('what if') || input.includes('simulation')) {
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Scenario planning is such a powerful tool for both financial security AND emotional well-being! When we can visualize different possibilities, we reduce anxiety about the unknown.

**The Psychology of "What-If" Thinking:**
Our brains naturally worry about worst-case scenarios. By intentionally exploring various outcomes, we can transform anxious "what-ifs" into empowering preparation.

**Therapeutic Scenario Framework:**
Let's explore three key scenarios together:

• **Optimistic Scenario**: What happens if things go better than expected?
• **Realistic Scenario**: Based on your current patterns and trends
• **Challenge Scenario**: How would you adapt if facing difficulties?

**Emotional Benefits:**
- Reduces financial anxiety through preparation
- Builds confidence in your ability to handle uncertainty  
- Helps identify both opportunities and potential risks
- Creates actionable plans rather than worry loops

What specific situation would you like to explore through scenario planning? Perhaps a career change, major purchase, or income fluctuation? I'm here to help you think through the possibilities with both analytical rigor and emotional support.`,
        timestamp: new Date(),
        type: 'recommendation',
        metadata: { insightType: 'scenario_planning', confidence: 0.91 }
      }
    }

    if (input.includes('tax') || input.includes('taxes') || input.includes('deduction') || input.includes('optimization')) {
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Ah, taxes - one of the most emotionally charged financial topics! Many people feel overwhelmed, anxious, or even guilty about tax planning. Let's approach this with both strategic thinking and emotional awareness.

**The Emotional Side of Tax Planning:**
Tax anxiety often stems from:
- Fear of making mistakes or "getting in trouble"
- Feeling overwhelmed by complexity
- Guilt about legally minimizing tax burden
- Procrastination due to emotional avoidance

**Therapeutic Tax Optimization Approach:**
Instead of just crunching numbers, let's consider your whole relationship with taxes:

**Mindset Shifts:**
• Tax planning is self-care - you're taking responsibility for your financial future
• Optimization is different from evasion - it's using the system as designed
• Small, consistent actions reduce year-end stress

**Key Areas to Explore:**
- Retirement contributions (401k, IRA limits)
- Health Savings Accounts (HSA) - triple tax advantage
- Business expense tracking and deductions
- Charitable giving strategies
- Tax-loss harvesting for investments

**Emotional Preparation:**
How do you currently feel about tax season? Do you avoid it, stress about it, or feel confident? Understanding your emotional relationship with taxes can help us develop strategies that feel manageable rather than overwhelming.

What aspect of tax optimization feels most important or stressful for you right now?`,
        timestamp: new Date(),
        type: 'insight',
        metadata: { insightType: 'tax_optimization', confidence: 0.88 }
      }
    }

    if (input.includes('forecast') || input.includes('predict') || input.includes('future')) {
      return {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Ah, you're thinking about your financial future - that shows wonderful foresight and responsibility! 

**The Psychology of Financial Planning:**
Planning ahead can reduce anxiety by giving us a sense of control, but it can also trigger worry about uncertain outcomes. This is completely normal.

**My Therapeutic Approach to Forecasting:**
Instead of rigid predictions, I help you create flexible scenarios that honor both your practical needs and emotional well-being:

• **Optimistic Scenario**: What could go well?
• **Realistic Scenario**: Based on current patterns
• **Challenging Scenario**: How would you cope if things got tough?

This approach builds resilience while maintaining hope. Would you like me to help you explore any of these scenarios? I can also analyze your transaction patterns to provide insights about your financial trends.

What time horizon are you most curious about - next month, quarter, or year?`,
        timestamp: new Date(),
        type: 'recommendation',
        metadata: { insightType: 'forecasting', confidence: 0.89 }
      }
    }

    // Default response
    return {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `I hear you, and I want you to know that whatever you're experiencing with your finances is valid and understandable.

Every person's relationship with money is unique, shaped by their experiences, values, and circumstances. There's no judgment here - only curiosity and support.

Could you tell me a bit more about what's on your mind? I'm here to listen and help you explore your thoughts and feelings about money in a safe, supportive space.

Some areas we could explore together:
• Daily spending habits and how they make you feel
• Financial goals and what they mean to you
• Money-related stress or anxiety
• Budgeting and planning in a sustainable way
• Understanding your financial patterns and behaviors

What feels most important to discuss right now?`,
      timestamp: new Date(),
      type: 'text'
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user'

    return (
      <div key={message.id} className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''}`}>
        {message.role === 'assistant' && (
          <DrSigmundSpendAvatar size="sm" showMessage={false} />
        )}
        
        <div className={`rounded-2xl p-4 max-w-sm ${
          isUser 
            ? 'bg-gray-100 rounded-tr-md' 
            : 'bg-gradient-to-r from-purple-50 to-blue-50 rounded-tl-md border border-purple-100'
        }`}>
          {/* Message Type Indicator */}
          {!isUser && message.type !== 'text' && (
            <div className="flex items-center space-x-2 mb-3 pb-2 border-b border-purple-100">
              {message.type === 'insight' && <Lightbulb className="h-4 w-4 text-yellow-500" />}
              {message.type === 'recommendation' && <Target className="h-4 w-4 text-purple-500" />}
              {message.type === 'chart' && <BarChart3 className="h-4 w-4 text-blue-500" />}
              <span className="text-xs font-medium text-purple-600 capitalize">
                {message.type === 'insight' ? 'Therapeutic Insight' : 
                 message.type === 'recommendation' ? 'Personalized Recommendation' : 
                 message.type === 'chart' ? 'Data Visualization' : 'Analysis'}
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
                return <p key={index} className={`mb-2 ${isUser ? 'text-gray-800' : 'text-gray-800'}`}>{paragraph}</p>
              } else {
                return <br key={index} />
              }
            })}
          </div>
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
    <div className="flex flex-col h-full bg-gray-50 p-6">
      {/* Main Chat Card */}
      <div className="max-w-4xl mx-auto w-full">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4">
            <div className="flex items-center gap-3">
              <DrSigmundSpendAvatar size="sm" showMessage={false} />
              <div>
                <h3 className="font-bold text-white">Dr. Sigmund Spend</h3>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-purple-100 text-sm">Online • Financial Therapist</span>
                </div>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="p-6 space-y-4 h-96 overflow-y-auto flex flex-col">
            {messages.map(renderMessage)}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex items-start gap-3">
                <DrSigmundSpendAvatar size="sm" showMessage={false} />
                <div className="rounded-2xl p-4 max-w-sm rounded-tl-md bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-100">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm text-gray-500">Dr. Spend is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <div className="p-4 border-t border-gray-100 bg-gray-50">
            <div className="flex items-center gap-2 bg-white rounded-full px-4 py-3 border border-gray-200">
              <input 
                type="text" 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Share your money feelings with Dr. Sigmund..."
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
              Dr. Sigmund is here to help with your financial feelings. Ask him anything about money, spending, or financial anxiety.
            </p>
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">About Dr. Sigmund Spend</h3>
          <p className="text-gray-700 text-sm leading-relaxed">
            Dr. Sigmund Spend is a compassionate financial therapist who combines psychological insights with financial wisdom. 
            He helps people understand their relationship with money through gentle, non-judgmental conversations. 
            His approach focuses on emotional safety, understanding patterns, and building healthy financial habits.
          </p>
          <div className="flex items-center gap-6 mt-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              <span>Financial Analysis</span>
            </div>
            <div className="flex items-center gap-2">
              <Heart className="w-4 h-4 text-gray-400" />
              <span>Therapeutic Approach</span>
            </div>
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-gray-400" />
              <span>AI-Powered Insights</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}