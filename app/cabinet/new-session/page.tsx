'use client'

import EnhancedDrSigmundChat from '../../../components/EnhancedDrSigmundChat'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function NewSessionPage() {
  return (
    <CabinetPageLayout title="New Session" description="AI-powered financial therapy">
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <EnhancedDrSigmundChat />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
