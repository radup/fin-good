'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import DashboardComponent from '../../DashboardComponent'

export default function DashboardPage() {
  return (
    <CabinetPageLayout title="Dashboard" description="Overview and summary">
      <div className="p-6">
        <DashboardComponent />
      </div>
    </CabinetPageLayout>
  )
}
