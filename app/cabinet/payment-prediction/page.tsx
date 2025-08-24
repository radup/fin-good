'use client'

import ClientPaymentPredictionDashboard from '../../../components/ClientPaymentPredictionDashboard'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function PaymentPredictionPage() {
  return (
    <CabinetPageLayout title="Payment Prediction" description="Client payment forecasts">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <ClientPaymentPredictionDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
