'use client'

import React, { useState } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { useCashFlowAnalysis } from '@/hooks/useAnalytics'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface CashFlowAnalysisProps {
  className?: string
  startDate?: string
  endDate?: string
  onDateRangeChange?: (start: string, end: string) => void
}

export default function CashFlowAnalysis({ 
  className = '',
  startDate,
  endDate,
  onDateRangeChange
}: CashFlowAnalysisProps) {
  const [dateRange, setDateRange] = useState({
    start: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: endDate || new Date().toISOString().split('T')[0]
  })

  const { data: cashFlowData, isLoading, error, refetch } = useCashFlowAnalysis({
    start_date: dateRange.start,
    end_date: dateRange.end
  })

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    const newRange = { ...dateRange, [field]: value }
    setDateRange(newRange)
    onDateRangeChange?.(newRange.start, newRange.end)
  }

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center gap-2 text-red-600 mb-4">
          <AlertCircle className="w-5 h-5" />
          <h2 className="text-lg font-semibold">Cash Flow Analysis Error</h2>
        </div>
        <p className="text-gray-600 mb-4">Failed to load cash flow data</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Cash Flow Analysis</h2>
            <p className="text-sm text-gray-500">Income, expenses, and net cash flow trends</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Export data"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Date Range:</span>
          </div>
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => handleDateChange('start', e.target.value)}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <span className="text-gray-500">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => handleDateChange('end', e.target.value)}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Total Income */}
          <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800">Total Income</p>
                <p className="text-2xl font-bold text-green-900">
                  {cashFlowData?.summary?.total_income 
                    ? formatCurrency(Number(cashFlowData.summary.total_income))
                    : '$0.00'
                  }
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
            {cashFlowData?.summary?.income_growth_rate && (
              <p className="text-sm text-green-700 mt-2">
                +{formatPercentage(Number(cashFlowData.summary.income_growth_rate))} vs last period
              </p>
            )}
          </div>

          {/* Total Expenses */}
          <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-800">Total Expenses</p>
                <p className="text-2xl font-bold text-red-900">
                  {cashFlowData?.summary?.total_expenses 
                    ? formatCurrency(Number(cashFlowData.summary.total_expenses))
                    : '$0.00'
                  }
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-600" />
            </div>
            {cashFlowData?.summary?.expense_growth_rate && (
              <p className="text-sm text-red-700 mt-2">
                {Number(cashFlowData.summary.expense_growth_rate) > 0 ? '+' : ''}
                {formatPercentage(Number(cashFlowData.summary.expense_growth_rate))} vs last period
              </p>
            )}
          </div>

          {/* Net Cash Flow */}
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-800">Net Cash Flow</p>
                <p className="text-2xl font-bold text-blue-900">
                  {cashFlowData?.summary?.net_total 
                    ? formatCurrency(Number(cashFlowData.summary.net_total))
                    : '$0.00'
                  }
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-600" />
            </div>
            {cashFlowData?.financial_health?.savings_rate && (
              <p className="text-sm text-blue-700 mt-2">
                {formatPercentage(Number(cashFlowData.financial_health.savings_rate))} savings rate
              </p>
            )}
          </div>
        </div>

        {/* Cash Flow Chart */}
        {cashFlowData?.cash_flow_data && cashFlowData.cash_flow_data.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cash Flow Trends</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={cashFlowData.cash_flow_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis tickFormatter={(value) => formatCurrency(value)} />
                  <Tooltip 
                    formatter={(value: any) => [formatCurrency(value), '']}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="income" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Income"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="expenses" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    name="Expenses"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="net_flow" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    name="Net Flow"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Financial Health Metrics */}
        {cashFlowData?.financial_health && (
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Health</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600">Expense Ratio</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatPercentage(Number(cashFlowData.financial_health.expense_ratio))}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Savings Rate</p>
                <p className="text-lg font-semibold text-green-600">
                  {formatPercentage(Number(cashFlowData.financial_health.savings_rate))}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Stability</p>
                <p className="text-lg font-semibold text-blue-600">
                  {cashFlowData.financial_health.financial_stability}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
