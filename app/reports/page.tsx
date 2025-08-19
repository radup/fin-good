'use client'

import React from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { BarChart3, TrendingUp, PieChart, Calendar, Download } from 'lucide-react'

export default function ReportsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="mt-1 text-sm text-gray-500">
            Analytics, insights, and financial reporting
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Spending Trends */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Spending Trends</h3>
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Track your spending patterns over time
            </p>
            <div className="h-32 bg-gray-100 rounded flex items-center justify-center">
              <span className="text-gray-500">Chart placeholder</span>
            </div>
          </div>
          
          {/* Category Distribution */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Category Distribution</h3>
              <PieChart className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-sm text-gray-600 mb-4">
              See how your spending is distributed across categories
            </p>
            <div className="h-32 bg-gray-100 rounded flex items-center justify-center">
              <span className="text-gray-500">Chart placeholder</span>
            </div>
          </div>
          
          {/* Income vs Expenses */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Income vs Expenses</h3>
              <BarChart3 className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Compare your income and expenses
            </p>
            <div className="h-32 bg-gray-100 rounded flex items-center justify-center">
              <span className="text-gray-500">Chart placeholder</span>
            </div>
          </div>
          
          {/* Monthly Summary */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Monthly Summary</h3>
              <Calendar className="w-5 h-5 text-orange-600" />
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Monthly financial summary and insights
            </p>
            <div className="h-32 bg-gray-100 rounded flex items-center justify-center">
              <span className="text-gray-500">Chart placeholder</span>
            </div>
          </div>
          
          {/* Export Options */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Export Reports</h3>
              <Download className="w-5 h-5 text-indigo-600" />
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Export your data and reports in various formats
            </p>
            <div className="space-y-2">
              <button className="w-full px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                Export CSV
              </button>
              <button className="w-full px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                Export PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
