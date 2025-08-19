'use client'

import React, { useState } from 'react'
import { 
  PieChart, 
  BarChart3, 
  TrendingUp, 
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
  ChevronRight,
  ChevronDown
} from 'lucide-react'
import { useCategoryInsights } from '@/hooks/useAnalytics'
import { PieChart as RechartsPieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

interface CategoryInsightsProps {
  className?: string
  startDate?: string
  endDate?: string
  onCategoryClick?: (category: string) => void
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B6B', '#4ECDC4', '#45B7D1']

export default function CategoryInsights({ 
  className = '',
  startDate,
  endDate,
  onCategoryClick
}: CategoryInsightsProps) {
  const [dateRange, setDateRange] = useState({
    start: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: endDate || new Date().toISOString().split('T')[0]
  })
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())

  const { data: categoryData, isLoading, error, refetch } = useCategoryInsights({
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
  }

  const toggleCategoryExpansion = (category: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(category)) {
      newExpanded.delete(category)
    } else {
      newExpanded.add(category)
    }
    setExpandedCategories(newExpanded)
  }

  const handleCategoryClick = (category: string) => {
    onCategoryClick?.(category)
  }

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center gap-2 text-red-600 mb-4">
          <AlertCircle className="w-5 h-5" />
          <h2 className="text-lg font-semibold">Category Insights Error</h2>
        </div>
        <p className="text-gray-600 mb-4">Failed to load category insights data</p>
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

  // Prepare data for charts
  const pieChartData = categoryData?.category_insights 
    ? Object.entries(categoryData.category_insights)
        .map(([category, insight]: [string, any]) => ({
          name: category,
          value: Number(insight.total_amount),
          percentage: Number(insight.percentage_of_total)
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
    : []

  const barChartData = categoryData?.category_insights
    ? Object.entries(categoryData.category_insights)
        .map(([category, insight]: [string, any]) => ({
          category,
          amount: Number(insight.total_amount),
          transactions: insight.transaction_count,
          average: Number(insight.average_transaction)
        }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 8)
    : []

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Category Insights</h2>
            <p className="text-sm text-gray-500">Spending patterns and trends by category</p>
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

      {/* Charts Section */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Category Distribution Pie Chart */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Category Distribution
            </h3>
            {pieChartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} (${percentage.toFixed(1)}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No category data available</p>
            )}
          </div>

          {/* Category Spending Bar Chart */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Top Categories by Spending
            </h3>
            {barChartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Bar dataKey="amount" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No category data available</p>
            )}
          </div>
        </div>

        {/* Category Details */}
        {categoryData?.category_insights && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Category Details</h3>
            {Object.entries(categoryData.category_insights)
              .sort(([, a]: [string, any], [, b]: [string, any]) => Number(b.total_amount) - Number(a.total_amount))
              .map(([category, insight]: [string, any]) => (
                <div key={category} className="border border-gray-200 rounded-lg p-4">
                  <div 
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleCategoryExpansion(category)}
                  >
                    <div className="flex items-center gap-3">
                      {expandedCategories.has(category) ? (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-500" />
                      )}
                      <div>
                        <h4 className="font-medium text-gray-900">{category}</h4>
                        <p className="text-sm text-gray-500">
                          {insight.transaction_count} transactions
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">
                        {formatCurrency(Number(insight.total_amount))}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatPercentage(Number(insight.percentage_of_total))} of total
                      </p>
                    </div>
                  </div>

                  {expandedCategories.has(category) && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Average Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(Number(insight.average_transaction))}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">First Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {new Date(insight.first_transaction).toLocaleDateString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Last Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {new Date(insight.last_transaction).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      {/* Trend Analysis */}
                      {insight.trend_analysis && (
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <h5 className="font-medium text-blue-900 mb-2">Trend Analysis</h5>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <p className="text-sm text-blue-600">Growth Rate</p>
                              <p className="font-semibold text-blue-900">
                                {insight.trend_analysis.growth_rate 
                                  ? `${insight.trend_analysis.growth_rate > 0 ? '+' : ''}${formatPercentage(Number(insight.trend_analysis.growth_rate))}`
                                  : 'N/A'
                                }
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-blue-600">Trend Direction</p>
                              <p className="font-semibold text-blue-900">
                                {insight.trend_analysis.trend_direction}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-blue-600">Seasonal Variance</p>
                              <p className="font-semibold text-blue-900">
                                {insight.trend_analysis.seasonal_variance 
                                  ? formatPercentage(Number(insight.trend_analysis.seasonal_variance))
                                  : 'N/A'
                                }
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Monthly Trend Chart */}
                      {insight.monthly_data && insight.monthly_data.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-gray-900 mb-2">Monthly Trends</h5>
                          <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={insight.monthly_data}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                  dataKey="month" 
                                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
                                />
                                <YAxis tickFormatter={(value) => formatCurrency(value)} />
                                <Tooltip 
                                  formatter={(value: any) => formatCurrency(value)}
                                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="amount" 
                                  stroke="#3b82f6" 
                                  strokeWidth={2}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  )
}
