'use client'

import React, { useState } from 'react'
import { 
  Building2, 
  BarChart3, 
  TrendingUp, 
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Users,
  Clock,
  DollarSign
} from 'lucide-react'
import { useVendorAnalysis } from '@/hooks/useAnalytics'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

interface VendorAnalysisProps {
  className?: string
  startDate?: string
  endDate?: string
  onVendorClick?: (vendor: string) => void
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B6B', '#4ECDC4', '#45B7D1']

export default function VendorAnalysis({ 
  className = '',
  startDate,
  endDate,
  onVendorClick
}: VendorAnalysisProps) {
  const [dateRange, setDateRange] = useState({
    start: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: endDate || new Date().toISOString().split('T')[0]
  })
  const [expandedVendors, setExpandedVendors] = useState<Set<string>>(new Set())

  const { data: vendorData, isLoading, error, refetch } = useVendorAnalysis({
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

  const toggleVendorExpansion = (vendor: string) => {
    const newExpanded = new Set(expandedVendors)
    if (newExpanded.has(vendor)) {
      newExpanded.delete(vendor)
    } else {
      newExpanded.add(vendor)
    }
    setExpandedVendors(newExpanded)
  }

  const handleVendorClick = (vendor: string) => {
    onVendorClick?.(vendor)
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
          <h2 className="text-lg font-semibold">Vendor Analysis Error</h2>
        </div>
        <p className="text-gray-600 mb-4">Failed to load vendor analysis data</p>
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
  const topVendorsData = vendorData?.vendor_insights 
    ? vendorData.vendor_insights
        .sort((a: any, b: any) => Number(b.total_spent) - Number(a.total_spent))
        .slice(0, 10)
        .map((vendor: any) => ({
          vendor: vendor.vendor,
          amount: Number(vendor.total_spent),
          transactions: vendor.transaction_count,
          average: Number(vendor.average_transaction)
        }))
    : []

  const spendingPatternsData = vendorData?.spending_patterns 
    ? [
        { name: 'Regular', value: vendorData.spending_patterns.regular_vendors, color: '#10b981' },
        { name: 'Occasional', value: vendorData.spending_patterns.occasional_vendors, color: '#f59e0b' },
        { name: 'One-time', value: vendorData.spending_patterns.one_time_vendors, color: '#ef4444' }
      ]
    : []

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Vendor Analysis</h2>
            <p className="text-sm text-gray-500">Spending patterns and vendor insights</p>
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

      {/* Summary Cards */}
      {vendorData?.summary && (
        <div className="p-6 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center gap-3">
                <Building2 className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-800">Total Vendors</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {vendorData.summary.total_unique_vendors}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center gap-3">
                <DollarSign className="w-8 h-8 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-800">Total Spending</p>
                  <p className="text-2xl font-bold text-green-900">
                    {formatCurrency(Number(vendorData.summary.total_vendor_spending))}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <div className="flex items-center gap-3">
                <Users className="w-8 h-8 text-purple-600" />
                <div>
                  <p className="text-sm font-medium text-purple-800">Avg per Vendor</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {formatCurrency(Number(vendorData.summary.average_vendor_spend))}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Top Vendors Bar Chart */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Top Vendors by Spending
            </h3>
            {topVendorsData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topVendorsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="vendor" angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Bar dataKey="amount" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No vendor data available</p>
            )}
          </div>

          {/* Spending Patterns Pie Chart */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Vendor Spending Patterns
            </h3>
            {spendingPatternsData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={spendingPatternsData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {spendingPatternsData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No pattern data available</p>
            )}
          </div>
        </div>

        {/* Vendor Details */}
        {vendorData?.vendor_insights && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Vendor Details</h3>
            {vendorData.vendor_insights
              .sort((a: any, b: any) => Number(b.total_spent) - Number(a.total_spent))
              .map((vendor: any) => (
                <div key={vendor.vendor} className="border border-gray-200 rounded-lg p-4">
                  <div 
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleVendorExpansion(vendor.vendor)}
                  >
                    <div className="flex items-center gap-3">
                      {expandedVendors.has(vendor.vendor) ? (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-500" />
                      )}
                      <div>
                        <h4 className="font-medium text-gray-900">{vendor.vendor}</h4>
                        <p className="text-sm text-gray-500">
                          {vendor.transaction_count} transactions
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">
                        {formatCurrency(Number(vendor.total_spent))}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatPercentage(Number(vendor.percentage_of_spending))} of total
                      </p>
                    </div>
                  </div>

                  {expandedVendors.has(vendor.vendor) && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Average Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(Number(vendor.average_transaction))}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Min Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(Number(vendor.min_transaction))}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Max Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(Number(vendor.max_transaction))}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Frequency</p>
                          <p className="font-semibold text-gray-900">
                            {Number(vendor.transaction_frequency).toFixed(1)}/month
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">First Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {new Date(vendor.first_transaction).toLocaleDateString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Last Transaction</p>
                          <p className="font-semibold text-gray-900">
                            {new Date(vendor.last_transaction).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      <div className="bg-blue-50 p-3 rounded-lg">
                        <h5 className="font-medium text-blue-900 mb-2">Vendor Insights</h5>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-blue-600">Primary Category</p>
                            <p className="font-semibold text-blue-900">
                              {vendor.primary_category || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-blue-600">Spending Consistency</p>
                            <p className="font-semibold text-blue-900">
                              {vendor.spending_consistency}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
          </div>
        )}

        {/* Spending Patterns Summary */}
        {vendorData?.spending_patterns && (
          <div className="mt-6 bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending Patterns Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600">Regular Vendors</p>
                <p className="text-lg font-semibold text-green-600">
                  {vendorData.spending_patterns.regular_vendors}
                </p>
                <p className="text-xs text-gray-500">Consistent spending patterns</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Occasional Vendors</p>
                <p className="text-lg font-semibold text-yellow-600">
                  {vendorData.spending_patterns.occasional_vendors}
                </p>
                <p className="text-xs text-gray-500">Intermittent spending</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">One-time Vendors</p>
                <p className="text-lg font-semibold text-red-600">
                  {vendorData.spending_patterns.one_time_vendors}
                </p>
                <p className="text-xs text-gray-500">Single transactions</p>
              </div>
            </div>
            {vendorData.spending_patterns.top_vendor && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">Top Spending Vendor</p>
                <p className="font-semibold text-gray-900">
                  {vendorData.spending_patterns.top_vendor}
                </p>
                <p className="text-sm text-gray-500">
                  {formatPercentage(Number(vendorData.spending_patterns.vendor_concentration))} of total spending
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
