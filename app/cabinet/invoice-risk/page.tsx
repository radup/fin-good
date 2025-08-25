'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import InvoiceRiskDashboard from '../../../components/InvoiceRiskDashboard'
import { cardClasses } from '../../../lib/design-utils'

export default function InvoiceRiskPage() {
  return (
    <CabinetPageLayout title="Invoice & Risk" description="Invoice analysis and risk assessment">
      <div className="space-y-6">
        <div className={cardClasses('default', 'p-6')}>
          <InvoiceRiskDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
