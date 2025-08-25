'use client'

import ClientPaymentPredictionDashboard from '../../../components/ClientPaymentPredictionDashboard'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function PaymentPredictionPage() {
  return (
    <CabinetPageLayout title="Payment Prediction" description="Client payment forecasts">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <ClientPaymentPredictionDashboard />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
