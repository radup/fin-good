'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { ForecastingDashboard } from '../../../components/ForecastingDashboard'

export default function CashFlowForecastPage() {
  return (
    <CabinetPageLayout title="Cash Flow Forecast" description="ML-powered financial forecasting">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <ForecastingDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
