import { ForecastingDashboard } from '@/components/ForecastingDashboard'

export default function ForecastingDemoPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Forecasting Demo</h1>
          <p className="text-gray-600 mt-2">
            Experience the power of ML-powered cash flow forecasting with confidence intervals and trend analysis.
          </p>
        </div>
        
        <ForecastingDashboard />
      </div>
    </div>
  )
}
