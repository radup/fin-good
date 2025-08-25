'use client'

import EnhancedAnalyticsDashboard from '../../../components/EnhancedAnalyticsDashboard'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function AnalyticsPage() {
  return (
    <CabinetPageLayout title="Analytics" description="Financial insights and analytics">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <EnhancedAnalyticsDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
