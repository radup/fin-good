'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { BudgetAnalysis } from '../../../components/BudgetAnalysis'

export default function BudgetAnalysisPage() {
  return (
    <CabinetPageLayout title="Budget Analysis" description="Budget planning and analysis">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <BudgetAnalysis />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
