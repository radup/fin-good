'use client'

import { useState } from 'react'
import { Upload } from 'lucide-react'
import { UploadModal } from '../../../components/UploadModal'
import { ImportBatchManager } from '../../../components/ImportBatchManager'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function DataImportPage() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)

  const handleUploadSuccess = () => {
    setIsUploadModalOpen(false)
    // Could add refresh logic here
  }

  return (
    <CabinetPageLayout title="Data Import" description="Upload and manage data">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload New Data</h2>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <button
                  onClick={() => setIsUploadModalOpen(true)}
                  className="w-full bg-brand-gradient text-white px-6 py-4 rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <Upload className="w-5 h-5" />
                  Upload CSV Files
                </button>
                <p className="text-sm text-gray-600 mt-3">
                  Upload your transaction data in CSV format for processing and categorization.
                </p>
              </div>
            </div>
            
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Import History</h2>
              <ImportBatchManager />
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <UploadModal 
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </CabinetPageLayout>
  )
}
