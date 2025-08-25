'use client'

import TaxOptimizationDashboard from '../../../components/TaxOptimizationDashboard'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function TaxOptimizationPage() {
  return (
    <CabinetPageLayout title="Tax Optimization" description="Multi-jurisdiction tax planning">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <TaxOptimizationDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
