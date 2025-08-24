'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import CategorizationPerformance from '../../../components/CategorizationPerformance'

export default function CategorizationPage() {
  return (
    <CabinetPageLayout title="Categorisation" description="AI categorization tools">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">AI Categorization Performance</h2>
            <p className="text-gray-600">
              Monitor and analyze the performance of our AI-powered transaction categorization system.
            </p>
          </div>
          <CategorizationPerformance />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
