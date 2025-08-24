'use client'

import dynamic from 'next/dynamic'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { Target, Plus, TrendingUp, Calendar, DollarSign, PiggyBank } from 'lucide-react'

export default function GoalSettingsPage() {
  return (
    <CabinetPageLayout title="Goal Settings" description="Set financial goals">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Financial Goal Settings</h2>
            <p className="text-gray-600">
              Set and track your financial goals with AI-powered insights and progress monitoring.
            </p>
          </div>

          {/* Current Goals */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Current Goals</h3>
              <button className="px-4 py-2 bg-brand-gradient text-white rounded-md hover:opacity-90 transition-opacity flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Add New Goal
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Emergency Fund Goal */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                    <PiggyBank className="w-5 h-5 text-brand-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Emergency Fund</h4>
                    <p className="text-sm text-gray-500">Target: €10,000</p>
                  </div>
                </div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Progress</span>
                    <span className="text-gray-900 font-medium">67%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-brand-gradient h-2 rounded-full" style={{ width: '67%' }}></div>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600">
                  <p>Current: €6,700</p>
                  <p>Remaining: €3,300</p>
                </div>
              </div>

              {/* Business Investment Goal */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-brand-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Business Investment</h4>
                    <p className="text-sm text-gray-500">Target: €25,000</p>
                  </div>
                </div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Progress</span>
                    <span className="text-gray-900 font-medium">32%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-brand-gradient h-2 rounded-full" style={{ width: '32%' }}></div>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600">
                  <p>Current: €8,000</p>
                  <p>Remaining: €17,000</p>
                </div>
              </div>

              {/* Tax Optimization Goal */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-brand-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Tax Savings</h4>
                    <p className="text-sm text-gray-500">Target: €5,000/year</p>
                  </div>
                </div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Progress</span>
                    <span className="text-gray-900 font-medium">85%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-brand-gradient h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600">
                  <p>Current: €4,250</p>
                  <p>Remaining: €750</p>
                </div>
              </div>
            </div>
          </div>

          {/* Goal Categories */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Short-term Goals */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-brand-primary" />
                Short-term Goals (3-6 months)
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900">Increase Monthly Savings</h4>
                    <p className="text-sm text-gray-600">From €1,500 to €2,000</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-brand-primary">On Track</p>
                    <p className="text-xs text-gray-500">Due: Dec 2025</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900">Reduce Dining Expenses</h4>
                    <p className="text-sm text-gray-600">Cut by 20%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-green-600">Completed</p>
                    <p className="text-xs text-gray-500">Achieved: Aug 2025</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Long-term Goals */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-brand-primary" />
                Long-term Goals (1-5 years)
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900">Retirement Fund</h4>
                    <p className="text-sm text-gray-600">Target: €500,000</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-brand-primary">On Track</p>
                    <p className="text-xs text-gray-500">Due: 2030</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900">Business Expansion</h4>
                    <p className="text-sm text-gray-600">Open second location</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-yellow-600">Planning</p>
                    <p className="text-xs text-gray-500">Due: 2026</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="mt-8 bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Goal Recommendations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 bg-brand-primary-lightest rounded-lg">
                <h4 className="font-medium text-brand-primary mb-2">Based on Your Spending Patterns</h4>
                <p className="text-sm text-gray-700">
                  Consider setting a goal to reduce subscription expenses by 15% - you currently have 8 active subscriptions totaling €127/month.
                </p>
              </div>
              
              <div className="p-4 bg-brand-primary-lightest rounded-lg">
                <h4 className="font-medium text-brand-primary mb-2">Based on Your Income Growth</h4>
                <p className="text-sm text-gray-700">
                  With your projected income increase, you could accelerate your emergency fund goal by 3 months by increasing monthly contributions to €1,200.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}
