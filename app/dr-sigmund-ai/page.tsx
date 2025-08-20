'use client'

import { useEffect, useState } from 'react'
import EnhancedDrSigmundChat from '@/components/EnhancedDrSigmundChat'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import DashboardLayout from '@/components/DashboardLayout'
import { Brain, Heart, Zap } from 'lucide-react'

export default function DrSigmundAIPage() {
  const [showWelcome, setShowWelcome] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false)
    }, 5000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50">
        <div className="container mx-auto px-4 py-8">
          
          {/* Dr. Sigmund Welcome Message */}
          {showWelcome && (
            <div className="mb-8 animate-fade-in">
              <DrSigmundSpendAvatar
                size="lg"
                mood="inspiring"
                message="Welcome to my enhanced AI therapy center! I've been upgraded with powerful financial analysis tools while keeping my compassionate heart. Now I can provide both emotional support AND run real financial simulations, cash flow forecasts, tax optimizations, and investment analysis. Think of me as your wise financial friend who happens to have AI superpowers. What would you like to explore together?"
                showMessage={true}
                animated={true}
                isTyping={false}
                isListening={false}
                variant="expert"
              />
            </div>
          )}

          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Dr. Sigmund Spend AI</h1>
                <p className="text-gray-600 mt-1">Enhanced financial therapy with AI-powered analysis tools</p>
              </div>
            </div>

            {/* Key Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-xl">
                    <Brain className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">AI Financial Analysis</h3>
                    <p className="text-sm text-gray-600">Real-time simulations & forecasts</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 rounded-xl">
                    <Heart className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Therapeutic Approach</h3>
                    <p className="text-sm text-gray-600">Emotional support & guidance</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-xl">
                    <Zap className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Integrated Tools</h3>
                    <p className="text-sm text-gray-600">6 financial analysis engines</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Enhanced Chat Interface */}
          <EnhancedDrSigmundChat />

          {/* How It Works Section */}
          <div className="mt-12 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <Zap className="h-5 w-5 text-purple-600" />
              How Dr. Sigmund's AI Enhancement Works
            </h2>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-medium text-gray-900 mb-4">🧠 Therapeutic Foundation</h3>
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
                <h3 className="font-medium text-gray-900 mb-4">⚡ AI-Powered Analysis</h3>
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
          <div className="mt-8 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-6">
            <h3 className="font-medium text-purple-900 mb-4">💬 Try These Conversation Starters</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="bg-white rounded-xl p-3 border border-purple-200">
                  <div className="font-medium text-purple-800 mb-1">Scenario Planning</div>
                  <p className="text-purple-700">"What if I increase my rates to €95/hour?"</p>
                </div>
                <div className="bg-white rounded-xl p-3 border border-purple-200">
                  <div className="font-medium text-purple-800 mb-1">Cash Flow</div>
                  <p className="text-purple-700">"Can you forecast my cash flow for the next 6 months?"</p>
                </div>
                <div className="bg-white rounded-xl p-3 border border-purple-200">
                  <div className="font-medium text-purple-800 mb-1">Tax Optimization</div>
                  <p className="text-purple-700">"Help me understand my tax optimization options in Belgium"</p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="bg-white rounded-xl p-3 border border-purple-200">
                  <div className="font-medium text-purple-800 mb-1">Client Analysis</div>
                  <p className="text-purple-700">"I'm worried about client payments - can you analyze the risks?"</p>
                </div>
                <div className="bg-white rounded-xl p-3 border border-purple-200">
                  <div className="font-medium text-purple-800 mb-1">Investment Planning</div>
                  <p className="text-purple-700">"What should I do with my surplus cash?"</p>
                </div>
                <div className="bg-white rounded-xl p-3 border border-purple-200">
                  <div className="font-medium text-purple-800 mb-1">Emotional Support</div>
                  <p className="text-purple-700">"I'm feeling anxious about my financial future"</p>
                </div>
              </div>
            </div>
          </div>

          {/* Dr. Sigmund Philosophy */}
          <div className="mt-8 bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
            <div className="flex items-start gap-6">
              <DrSigmundSpendAvatar
                size="md"
                mood="supportive"
                showMessage={false}
                animated={true}
                variant="professional"
              />
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 mb-3">Dr. Sigmund's Enhanced Philosophy</h3>
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-4">
                  <p className="text-sm text-purple-800 leading-relaxed mb-3">
                    "Technology should enhance human connection, not replace it. My AI capabilities are tools to provide you with 
                    better insights and reduce financial uncertainty, but the heart of our work together remains deeply human."
                  </p>
                  <p className="text-sm text-purple-800 leading-relaxed">
                    "Whether I'm running complex financial simulations or simply listening to your money worries, my goal is the same: 
                    to help you feel more confident, informed, and emotionally secure in your financial journey."
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <Brain className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-yellow-900 mb-2">AI Enhancement Disclaimer</h3>
                <p className="text-sm text-yellow-800 leading-relaxed">
                  Dr. Sigmund's AI analysis tools provide sophisticated financial modeling and predictions, but results should be used 
                  for planning and insight purposes only. While the emotional support and therapeutic guidance remain core to his approach, 
                  complex financial decisions should always be validated with qualified financial professionals when appropriate.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}