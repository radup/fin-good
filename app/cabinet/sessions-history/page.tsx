'use client'

import CabinetPageLayout from '../../../components/CabinetPageLayout'
import EnhancedDrSigmundChat from '../../../components/EnhancedDrSigmundChat'

export default function SessionsHistoryPage() {
  return (
    <CabinetPageLayout title="Sessions History" description="Past therapy sessions">
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Previous Sessions</h2>
            <p className="text-gray-600 mb-4">
              Review your past conversations with Dr. Sigmund and track your financial therapy progress.
            </p>
            
            {/* Mock sessions history */}
            <div className="space-y-4">
              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Cash Flow Analysis Session</h3>
                    <p className="text-sm text-gray-600">Discussed monthly cash flow patterns and budgeting strategies</p>
                    <p className="text-xs text-gray-500 mt-1">August 18, 2025 • 45 minutes</p>
                  </div>
                  <button className="px-3 py-1 bg-brand-gradient text-white text-sm rounded-md hover:opacity-90 transition-opacity">
                    View Details
                  </button>
                </div>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Tax Optimization Planning</h3>
                    <p className="text-sm text-gray-600">Explored multi-jurisdiction tax strategies for business optimization</p>
                    <p className="text-xs text-gray-500 mt-1">August 15, 2025 • 32 minutes</p>
                  </div>
                  <button className="px-3 py-1 bg-brand-gradient text-white text-sm rounded-md hover:opacity-90 transition-opacity">
                    View Details
                  </button>
                </div>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Investment Portfolio Review</h3>
                    <p className="text-sm text-gray-600">Analyzed current investments and discussed diversification strategies</p>
                    <p className="text-xs text-gray-500 mt-1">August 12, 2025 • 28 minutes</p>
                  </div>
                  <button className="px-3 py-1 bg-brand-gradient text-white text-sm rounded-md hover:opacity-90 transition-opacity">
                    View Details
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Start New Session</h2>
            <p className="text-gray-600 mb-4">
              Ready to continue your financial therapy journey? Start a new session with Dr. Sigmund.
            </p>
            <EnhancedDrSigmundChat />
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}
