'use client'

import { DollarSign, TrendingUp, TrendingDown, FileText } from 'lucide-react'

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
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      {/* Total Income */}
      <div className="card therapeutic-hover therapeutic-transition">
        <div className="flex items-center">
          <div className="p-2 bg-success-100 rounded-lg">
            <TrendingUp className="w-6 h-6 text-success-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Total Income</p>
            <p className="text-2xl font-bold text-success-600">
              ${summary.total_income.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Total Expenses */}
      <div className="card therapeutic-hover therapeutic-transition">
        <div className="flex items-center">
          <div className="p-2 bg-danger-100 rounded-lg">
            <TrendingDown className="w-6 h-6 text-danger-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Total Expenses</p>
            <p className="text-2xl font-bold text-danger-600">
              ${summary.total_expenses.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Net Income */}
      <div className="card therapeutic-hover therapeutic-transition">
        <div className="flex items-center">
          <div className="p-2 bg-primary-100 rounded-lg">
            <DollarSign className="w-6 h-6 text-primary-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Net Income</p>
            <p className={`text-2xl font-bold ${netIncome >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
              ${netIncome.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Transactions */}
      <div className="card therapeutic-hover therapeutic-transition">
        <div className="flex items-center">
          <div className="p-2 bg-gray-100 rounded-lg">
            <FileText className="w-6 h-6 text-gray-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Transactions</p>
            <p className="text-2xl font-bold text-gray-900">
              {summary.total_transactions}
            </p>
            <p className="text-xs text-gray-500">
              {categorizationRate.toFixed(0)}% categorized
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
