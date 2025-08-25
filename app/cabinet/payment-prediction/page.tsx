'use client'

import ClientPaymentPredictionDashboard from '../../../components/ClientPaymentPredictionDashboard'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { cardClasses } from '../../../lib/design-utils'

export default function PaymentPredictionPage() {
  return (
    <CabinetPageLayout title="Payment Prediction" description="AI-powered client payment forecasts">
      <div className="space-y-6">
        <div className={cardClasses('default', 'p-6')}>
          <ClientPaymentPredictionDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
