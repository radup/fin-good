'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { BudgetAnalysis } from '../../../components/BudgetAnalysis'

export default function BudgetAnalysisPage() {
  return (
    <CabinetPageLayout title="Budget Analysis" description="Budget planning and analysis">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <BudgetAnalysis />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
