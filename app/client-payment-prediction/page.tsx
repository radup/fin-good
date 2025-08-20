'use client'

import { useEffect, useState } from 'react'
import ClientPaymentPredictionDashboard from '@/components/ClientPaymentPredictionDashboard'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import DashboardLayout from '@/components/DashboardLayout'
import { Target, Brain, Shield } from 'lucide-react'

export default function ClientPaymentPredictionPage() {
  const [showWelcome, setShowWelcome] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false)
    }, 3500)

    return () => clearTimeout(timer)
  }, [])

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="container mx-auto px-4 py-8">
          
          {/* Dr. Sigmund Welcome Message */}
          {showWelcome && (
            <div className="mb-8 animate-fade-in">
              <DrSigmundSpendAvatar
                size="lg"
                mood="analytical"
                message="Welcome to your Client Payment Intelligence Center! One of the biggest sources of business anxiety is uncertainty about when clients will pay. My AI models analyze payment patterns and predict potential delays, so you can plan ahead and take action early. Let's turn payment uncertainty into manageable insights."
                showMessage={true}
                animated={true}
                isTyping={false}
                isListening={false}
                variant="professional"
              />
            </div>
          )}

          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg">
                <Target className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Client Payment Prediction</h1>
                <p className="text-gray-600 mt-1">AI-powered late payment prediction and client risk assessment</p>
              </div>
            </div>

            {/* Key Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-xl">
                    <Brain className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">ML Prediction Models</h3>
                    <p className="text-sm text-gray-600">Advanced payment pattern analysis</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 rounded-xl">
                    <Target className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Early Intervention</h3>
                    <p className="text-sm text-gray-600">Proactive payment management</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-xl">
                    <Shield className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Risk Assessment</h3>
                    <p className="text-sm text-gray-600">Client reliability scoring</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Client Payment Prediction Dashboard */}
          <ClientPaymentPredictionDashboard />

          {/* Dr. Sigmund Cash Flow Therapy Section */}
          <div className="mt-12 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
            <div className="flex items-start gap-6">
              <DrSigmundSpendAvatar
                size="md"
                mood="reassuring"
                showMessage={false}
                animated={true}
                variant="expert"
              />
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Dr. Sigmund's Cash Flow Therapy</h2>
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6">
                  <h3 className="font-medium text-blue-900 mb-3">Payment Anxiety Relief Strategy</h3>
                  <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
                    <div>
                      <h4 className="font-medium mb-2">🎯 Predictive Peace of Mind</h4>
                      <ul className="space-y-1 text-blue-700">
                        <li>• Know which payments might be late before they happen</li>
                        <li>• Plan cash flow around realistic payment timelines</li>
                        <li>• Take early action instead of reactive panic</li>
                        <li>• Focus energy on high-impact interventions</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">🔍 Smart Client Management</h4>
                      <ul className="space-y-1 text-blue-700">
                        <li>• Identify clients who need closer follow-up</li>
                        <li>• Adjust payment terms based on reliability data</li>
                        <li>• Build stronger relationships through understanding</li>
                        <li>• Make informed decisions about new clients</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ML Model Information */}
          <div className="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl p-6">
            <h3 className="font-medium text-indigo-900 mb-4">🤖 How Our Payment Prediction Works</h3>
            <div className="grid md:grid-cols-3 gap-6 text-sm">
              <div className="bg-white rounded-xl p-4 border border-indigo-200">
                <div className="font-medium text-indigo-800 mb-2">1. Historical Analysis</div>
                <p className="text-indigo-700">Our AI analyzes each client's payment history, identifying patterns in timing, seasonality, and payment behavior changes</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-indigo-200">
                <div className="font-medium text-indigo-800 mb-2">2. Risk Scoring</div>
                <p className="text-indigo-700">Machine learning models consider invoice amount, payment terms, client industry, and economic factors to calculate risk</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-indigo-200">
                <div className="font-medium text-indigo-800 mb-2">3. Actionable Insights</div>
                <p className="text-indigo-700">Predictions come with confidence scores and specific recommendations for managing each client relationship</p>
              </div>
            </div>
          </div>

          {/* Best Practices */}
          <div className="mt-8 bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
            <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              Payment Management Best Practices
            </h3>
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <h4 className="font-medium text-gray-800 mb-3">Proactive Strategies</h4>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>Send payment reminders 5-7 days before due date for high-risk clients</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>Offer early payment discounts to incentivize faster payment</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>Build stronger relationships with slow-paying but reliable clients</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>Consider shorter payment terms for new or high-risk clients</span>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-800 mb-3">Risk Mitigation</h4>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>Diversify client base to reduce concentration risk</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>Maintain emergency fund based on payment prediction data</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>Regular contract reviews with problematic clients</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>Consider payment protection or factoring for high-value clients</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <Target className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-yellow-900 mb-2">Prediction Accuracy Disclaimer</h3>
                <p className="text-sm text-yellow-800 leading-relaxed">
                  Payment predictions are based on historical data and machine learning models. While our algorithms are highly accurate, 
                  actual payment behavior may vary due to client circumstances, economic conditions, or other unforeseen factors. 
                  Use predictions as guidance for planning and early intervention, not as guarantees of payment timing.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}