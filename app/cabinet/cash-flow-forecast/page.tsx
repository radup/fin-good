'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { ForecastingDashboard } from '../../../components/ForecastingDashboard'
import { cardClasses } from '../../../lib/design-utils'

export default function CashFlowForecastPage() {
  return (
    <CabinetPageLayout title="Cash Flow Forecast" description="AI-powered cash flow predictions & insights">
      <div className="space-y-6">
        <div className={cardClasses('default', 'p-6')}>
          <ForecastingDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
