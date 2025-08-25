'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import CategorizationPerformance from '../../../components/CategorizationPerformance'

export default function CategorizationPage() {
  return (
    <CabinetPageLayout title="Categorisation" description="AI categorization tools">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="mb-3">
            <h2 className="text-base font-semibold text-gray-900 mb-1">AI Categorization Performance</h2>
            <p className="text-xs text-gray-600">
              Monitor and analyze the performance of our AI-powered transaction categorization system.
            </p>
          </div>
          <CategorizationPerformance />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
