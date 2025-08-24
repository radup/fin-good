'use client'

import EnhancedAnalyticsDashboard from '../../../components/EnhancedAnalyticsDashboard'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function AnalyticsPage() {
  return (
    <CabinetPageLayout title="Analytics" description="Financial insights and analytics">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <EnhancedAnalyticsDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
