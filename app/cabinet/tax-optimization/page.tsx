'use client'

import TaxOptimizationDashboard from '../../../components/TaxOptimizationDashboard'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function TaxOptimizationPage() {
  return (
    <CabinetPageLayout title="Tax Optimization" description="Multi-jurisdiction tax planning">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <TaxOptimizationDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
