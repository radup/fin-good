'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import InvoiceRiskDashboard from '../../../components/InvoiceRiskDashboard'

export default function InvoiceRiskPage() {
  return (
    <CabinetPageLayout title="Invoice & Risk" description="Invoice analysis and risk assessment">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <InvoiceRiskDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
