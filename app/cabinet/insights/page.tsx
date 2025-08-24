'use client'

import dynamic from 'next/dynamic'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { Brain, TrendingUp, Target, Heart, Zap, BarChart3 } from 'lucide-react'

export default function InsightsPage() {
  return (
    <CabinetPageLayout title="Insights" description="Personalized financial insights">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Personalized Financial Insights</h2>
            <p className="text-gray-600">
              AI-powered insights based on your financial patterns and emotional check-ins.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Spending Pattern Insights */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-brand-primary" />
                </div>
                <h3 className="font-semibold text-gray-900">Spending Patterns</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Your spending on dining out has increased by 23% this month compared to last month.
              </p>
              <div className="text-xs text-gray-500">
                Based on 45 transactions analyzed
              </div>
            </div>

            {/* Emotional Trends */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                  <Heart className="w-5 h-5 text-brand-primary" />
                </div>
                <h3 className="font-semibold text-gray-900">Emotional Trends</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Your financial stress levels have decreased by 15% since starting therapy sessions.
              </p>
              <div className="text-xs text-gray-500">
                Based on 8 emotional check-ins
              </div>
            </div>

            {/* Goal Progress */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                  <Target className="w-5 h-5 text-brand-primary" />
                </div>
                <h3 className="font-semibold text-gray-900">Goal Progress</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                You're 67% of the way to your emergency fund goal of €10,000.
              </p>
              <div className="text-xs text-gray-500">
                Updated 2 hours ago
              </div>
            </div>

            {/* AI Recommendations */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-brand-primary" />
                </div>
                <h3 className="font-semibold text-gray-900">AI Recommendations</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Consider increasing your tax-deductible business expenses to optimize your tax position.
              </p>
              <div className="text-xs text-gray-500">
                Based on recent transactions
              </div>
            </div>

            {/* Cash Flow Insights */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-brand-primary" />
                </div>
                <h3 className="font-semibold text-gray-900">Cash Flow Insights</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Your projected cash flow for next month shows a 12% increase due to expected client payments.
              </p>
              <div className="text-xs text-gray-500">
                Based on payment predictions
              </div>
            </div>

            {/* Risk Assessment */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-primary-lightest rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-brand-primary" />
                </div>
                <h3 className="font-semibold text-gray-900">Risk Assessment</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Low risk profile detected. Your diversified income streams provide good stability.
              </p>
              <div className="text-xs text-gray-500">
                Updated daily
              </div>
            </div>
          </div>

          {/* Action Items */}
          <div className="mt-8 bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Actions</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-brand-primary-lightest rounded-lg">
                <div className="w-2 h-2 bg-brand-primary rounded-full"></div>
                <span className="text-sm text-gray-700">Schedule a session with Dr. Sigmund to discuss tax optimization strategies</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-brand-primary-lightest rounded-lg">
                <div className="w-2 h-2 bg-brand-primary rounded-full"></div>
                <span className="text-sm text-gray-700">Review your emergency fund contributions to reach your goal faster</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-brand-primary-lightest rounded-lg">
                <div className="w-2 h-2 bg-brand-primary rounded-full"></div>
                <span className="text-sm text-gray-700">Complete your weekly emotional check-in to track your financial wellness</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}
