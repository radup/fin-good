'use client'

import { useEffect, useState } from 'react'
import TaxOptimizationDashboard from '@/components/TaxOptimizationDashboard'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import DashboardLayout from '@/components/DashboardLayout'
import { Calculator, Shield, Globe } from 'lucide-react'

export default function TaxOptimizationPage() {
  const [showWelcome, setShowWelcome] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
        <div className="container mx-auto px-4 py-8">
          
          {/* Dr. Sigmund Welcome Message */}
          {showWelcome && (
            <div className="mb-8 animate-fade-in">
              <DrSigmundSpendAvatar
                size="lg"
                mood="analytical"
                message="Welcome to your tax optimization center! I'm here to help you navigate complex tax strategies with confidence and reduce any anxiety around tax planning. Let's explore smart, compliant ways to optimize your tax position across Belgium, Luxembourg, and the EU."
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
              <div className="p-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-lg">
                <Calculator className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Tax Optimization Center</h1>
                <p className="text-gray-600 mt-1">Benelux-focused tax planning with therapeutic guidance</p>
              </div>
            </div>

            {/* Key Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-xl">
                    <Shield className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Compliance-First</h3>
                    <p className="text-sm text-gray-600">Conservative, safe strategies</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-xl">
                    <Globe className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Multi-Jurisdiction</h3>
                    <p className="text-sm text-gray-600">Belgium, Luxembourg & EU</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-xl">
                    <Calculator className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Real-Time Calculations</h3>
                    <p className="text-sm text-gray-600">Instant tax savings estimates</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Tax Optimization Dashboard */}
          <TaxOptimizationDashboard />

          {/* Dr. Sigmund Tax Therapy Section */}
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
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Dr. Sigmund's Tax Therapy Corner</h2>
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-6">
                  <h3 className="font-medium text-purple-900 mb-3">Tax Anxiety Relief Tips</h3>
                  <ul className="space-y-2 text-sm text-purple-800">
                    <li className="flex items-start gap-2">
                      <span className="text-purple-600 mt-1">•</span>
                      <span>Remember: tax optimization is about making informed, legal choices to minimize your burden</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-600 mt-1">•</span>
                      <span>Start with simple strategies (expense optimization) before considering complex structures</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-600 mt-1">•</span>
                      <span>Always consult with a qualified tax professional for high-complexity strategies</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-600 mt-1">•</span>
                      <span>Focus on long-term financial health, not just immediate tax savings</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <Shield className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-medium text-yellow-900 mb-2">Important Disclaimer</h3>
                <p className="text-sm text-yellow-800 leading-relaxed">
                  This tool provides general information and estimates for educational purposes only. Tax laws are complex and change frequently. 
                  Always consult with qualified tax professionals in Belgium, Luxembourg, or your target jurisdiction before implementing any tax strategy. 
                  Spend's Analysis and Dr. Sigmund Spend do not provide professional tax advice.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}