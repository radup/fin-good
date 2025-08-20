'use client'

import { useEffect, useState } from 'react'
import ScenarioSimulationEngine from '@/components/ScenarioSimulationEngine'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import DashboardLayout from '@/components/DashboardLayout'
import { Brain, Target, Zap } from 'lucide-react'

export default function ScenarioSimulationPage() {
  const [showWelcome, setShowWelcome] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false)
    }, 4000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
        <div className="container mx-auto px-4 py-8">
          
          {/* Dr. Sigmund Welcome Message */}
          {showWelcome && (
            <div className="mb-8 animate-fade-in">
              <DrSigmundSpendAvatar
                size="lg"
                mood="inspiring"
                message="Welcome to my What-If Scenario Engine! This is where we turn financial anxiety into empowerment. Instead of worrying about 'what could happen', let's explore scenarios together with confidence. Every great business decision starts with asking 'what if' - and I'm here to guide you through the answers."
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
              <div className="p-3 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl shadow-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Scenario Simulation Center</h1>
                <p className="text-gray-600 mt-1">Dr. Sigmund's core financial decision-making tool</p>
              </div>
            </div>

            {/* Key Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 rounded-xl">
                    <Brain className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">AI-Powered Analysis</h3>
                    <p className="text-sm text-gray-600">Intelligent scenario modeling</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-xl">
                    <Target className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Risk Assessment</h3>
                    <p className="text-sm text-gray-600">Comprehensive risk scoring</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-pink-100 rounded-xl">
                    <Zap className="h-5 w-5 text-pink-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Real-Time Results</h3>
                    <p className="text-sm text-gray-600">Instant scenario analysis</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Scenario Simulation Engine */}
          <ScenarioSimulationEngine />

          {/* Dr. Sigmund Therapy Section */}
          <div className="mt-12 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
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
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl p-6">
                  <h3 className="font-medium text-indigo-900 mb-3">Dr. Sigmund's Decision-Making Framework</h3>
                  <div className="grid md:grid-cols-2 gap-4 text-sm text-indigo-800">
                    <div>
                      <h4 className="font-medium mb-2">🧠 Emotional Intelligence</h4>
                      <ul className="space-y-1 text-indigo-700">
                        <li>• Acknowledge financial anxiety as normal</li>
                        <li>• Use data to reduce uncertainty</li>
                        <li>• Focus on what you can control</li>
                        <li>• Celebrate small wins and progress</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">📊 Analytical Process</h4>
                      <ul className="space-y-1 text-indigo-700">
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

          {/* Getting Started Guide */}
          <div className="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl p-6">
            <h3 className="font-medium text-indigo-900 mb-4">🚀 How to Use the Scenario Engine</h3>
            <div className="grid md:grid-cols-3 gap-6 text-sm">
              <div className="bg-white rounded-xl p-4 border border-indigo-200">
                <div className="font-medium text-indigo-800 mb-2">1. Choose Scenario Type</div>
                <p className="text-indigo-700">Select from income, expense, timing, client, or investment scenarios based on your current decision</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-indigo-200">
                <div className="font-medium text-indigo-800 mb-2">2. Configure Variables</div>
                <p className="text-indigo-700">Adjust current vs proposed values, timeframes, and confidence levels for realistic modeling</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-indigo-200">
                <div className="font-medium text-indigo-800 mb-2">3. Analyze Results</div>
                <p className="text-indigo-700">Review cash flow impact, risk scores, and Dr. Sigmund's therapeutic recommendations</p>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <Target className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
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
        </div>
      </div>
    </DashboardLayout>
  )
}