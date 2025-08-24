'use client'

import ScenarioSimulationEngine from '../../../components/ScenarioSimulationEngine'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function ScenarioEnginePage() {
  return (
    <CabinetPageLayout title="Scenario Engine" description="What-if simulations">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <ScenarioSimulationEngine />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
