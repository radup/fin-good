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
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="mb-3">
            <h2 className="text-base font-semibold text-gray-900 mb-1">Reports</h2>
            <p className="text-xs text-gray-600">
              Analytics, insights, and financial reporting
            </p>
          </div>
        </div>
        
        {/* Main Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SpendingTrends />
          <CategoryDistribution />
        </div>
        
        {/* Categorization Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CategorizationAccuracy />
          <ConfidenceDistribution />
        </div>
        
        {/* Export Options */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-gray-900">Export Reports</h3>
            <Download className="w-4 h-4 text-brand-primary" />
          </div>
          <p className="text-xs text-gray-600 mb-3">
            Export your data and reports in various formats
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg hover:shadow-lg transition-all">
              Export CSV
            </button>
            <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg hover:shadow-lg transition-all">
              Export PDF
            </button>
            <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg hover:shadow-lg transition-all">
              Export Excel
            </button>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}
