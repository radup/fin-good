'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import EmotionalCheckIn from '../../../components/EmotionalCheckIn'

export default function EmotionalCheckInPage() {
  return (
    <CabinetPageLayout title="Emotional Check-In" description="Track financial emotions">
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Financial Wellness Check-In</h2>
            <p className="text-gray-600">
              Take a moment to reflect on your financial emotions and well-being. This helps Dr. Sigmund provide more personalized guidance.
            </p>
          </div>
          <EmotionalCheckIn />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
