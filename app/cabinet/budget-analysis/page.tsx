'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { BudgetAnalysis } from '../../../components/BudgetAnalysis'
import { cardClasses } from '../../../lib/design-utils'

export default function BudgetAnalysisPage() {
  return (
    <CabinetPageLayout title="Budget Analysis" description="Budget planning and analysis">
      <div className="space-y-6">
        <div className={cardClasses('default', 'p-6')}>
          <BudgetAnalysis />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
