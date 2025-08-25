'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { ForecastingDashboard } from '../../../components/ForecastingDashboard'

export default function CashFlowForecastPage() {
  return (
    <CabinetPageLayout title="Cash Flow Forecast" description="ML-powered financial forecasting">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <ForecastingDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
