'use client'

import TaxOptimizationDashboard from '../../../components/TaxOptimizationDashboard'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { cardClasses } from '../../../lib/design-utils'

export default function TaxOptimizationPage() {
  return (
    <CabinetPageLayout title="Tax Optimization" description="Multi-jurisdiction tax planning & strategies">
      <div className="space-y-6">
        <div className={cardClasses('default', 'p-6')}>
          <TaxOptimizationDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
