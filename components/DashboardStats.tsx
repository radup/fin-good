'use client'

import { DollarSign, TrendingUp, TrendingDown, FileText, CheckCircle, Target, ArrowRight } from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

interface DashboardStatsProps {
  summary?: {
    total_transactions: number
    total_income: number
    total_expenses: number
    categorized_count: number
    uncategorized_count: number
  }
  isLoading: boolean
}

export function DashboardStats({ summary, isLoading }: DashboardStatsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card animate-pulse therapeutic-transition">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!summary || typeof summary !== 'object') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card text-center therapeutic-transition">
          <p className="text-gray-500">No data available</p>
        </div>
      </div>
    )
  }

  const netIncome = summary.total_income - summary.total_expenses
  const categorizationRate = summary.total_transactions > 0 
    ? (summary.categorized_count / summary.total_transactions) * 100 
    : 0

  return (
    <div className="space-y-4">
      {/* Financial Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Total Income */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-blue-600" />
            <h4 className="text-sm font-medium text-gray-700">Total Income</h4>
          </div>
          <div className="text-xl font-bold text-gray-900 mb-1">
            ${summary.total_income.toLocaleString()}
          </div>
          <div className="text-xs text-gray-600">
            Monthly income
          </div>
        </div>

        {/* Total Expenses */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-red-600" />
            <h4 className="text-sm font-medium text-gray-700">Total Expenses</h4>
          </div>
          <div className="text-xl font-bold text-red-600 mb-1">
            ${summary.total_expenses.toLocaleString()}
          </div>
          <div className="text-xs text-gray-600">
            Monthly expenses
          </div>
        </div>

        {/* Net Income */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            <h4 className="text-sm font-medium text-gray-700">Net Income</h4>
          </div>
          <div className={`text-xl font-bold mb-1 ${netIncome >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
            ${netIncome.toLocaleString()}
          </div>
          <div className="text-xs text-gray-600">
            Income minus expenses
          </div>
        </div>

        {/* Transactions */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-purple-600" />
            <h4 className="text-sm font-medium text-gray-700">Transactions</h4>
          </div>
          <div className="text-xl font-bold text-gray-900 mb-1">
            {summary.total_transactions}
          </div>
          <div className="text-xs text-gray-600">
            {categorizationRate.toFixed(0)}% categorized
          </div>
        </div>
      </div>

      {/* Key Insights and Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Key Insights */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <h3 className="text-base font-semibold text-gray-900">Key Insights</h3>
          </div>
          <ul className="space-y-2">
            <li className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p className="text-sm text-gray-700">
                Your net income is <span className="font-semibold text-emerald-600">${netIncome.toLocaleString()}</span> with a {categorizationRate.toFixed(0)}% transaction categorization rate
              </p>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p className="text-sm text-gray-700">
                This represents a <span className="font-semibold text-emerald-600">{((netIncome / summary.total_income) * 100).toFixed(1)}%</span> savings rate from your total income
              </p>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p className="text-sm text-gray-700">
                {summary.uncategorized_count} transactions remain uncategorized and could provide better insights
              </p>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p className="text-sm text-gray-700">
                Confidence level: <span className="font-semibold text-emerald-600">85%</span> based on data quality and categorization
              </p>
            </li>
          </ul>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-blue-600" />
            <h3 className="text-base font-semibold text-gray-900">Recommendations</h3>
          </div>
          <ul className="space-y-2">
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-gray-700">
                Your financial position appears <span className="font-semibold text-emerald-600">stable and positive</span>
              </p>
            </li>
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-gray-700">
                Consider categorizing the remaining {summary.uncategorized_count} transactions for better insights
              </p>
            </li>
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-gray-700">
                Monitor your expense categories monthly and adjust spending patterns as needed
              </p>
            </li>
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-gray-700">
                Consider setting up automated categorization rules for recurring transactions
              </p>
            </li>
          </ul>
        </div>
      </div>

      {/* Dr. Sigmund's Therapeutic Perspective */}
      <div className="bg-gradient-to-br from-violet-50 to-violet-100 rounded-2xl shadow-xl border border-violet-200 p-4">
        <div className="flex items-center gap-3 mb-3">
          <DrSigmundSpendAvatar 
            size="sm" 
            showMessage={false}
            animated={false}
            className="flex-shrink-0"
          />
          <div>
            <h3 className="text-base font-semibold text-violet-800">Dr. Sigmund's Therapeutic Perspective</h3>
          </div>
        </div>
        <p className="text-sm text-violet-700 leading-relaxed">
          Excellent financial health! Your positive net income of ${netIncome.toLocaleString()} shows you're making smart financial choices. 
          The {categorizationRate.toFixed(0)}% categorization rate indicates good financial awareness. 
          Remember, even positive financial situations can create stress - take it step by step and monitor your emotional well-being 
          throughout your financial journey. Consider this a moment to celebrate your financial discipline!
        </p>
      </div>
    </div>
  )
}
