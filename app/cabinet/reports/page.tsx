'use client'

import React from 'react'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import SpendingTrends from '@/components/charts/SpendingTrends'
import CategoryDistribution from '@/components/charts/CategoryDistribution'
import CategorizationAccuracy from '@/components/charts/CategorizationAccuracy'
import ConfidenceDistribution from '@/components/charts/ConfidenceDistribution'
import { Download } from 'lucide-react'

export default function ReportsPage() {
  return (
    <CabinetPageLayout title="Reports" description="Financial reports and analytics">
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="mt-1 text-sm text-gray-500">
            Analytics, insights, and financial reporting
          </p>
        </div>
        
        {/* Main Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <SpendingTrends />
          <CategoryDistribution />
        </div>
        
        {/* Categorization Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <CategorizationAccuracy />
          <ConfidenceDistribution />
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
              Export CSV
            </button>
            <button className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
              Export PDF
            </button>
            <button className="px-4 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors">
              Export Excel
            </button>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}
