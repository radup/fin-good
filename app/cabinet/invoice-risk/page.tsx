'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import InvoiceRiskDashboard from '../../../components/InvoiceRiskDashboard'

export default function InvoiceRiskPage() {
  return (
    <CabinetPageLayout title="Invoice & Risk" description="Invoice analysis and risk assessment">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <InvoiceRiskDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
