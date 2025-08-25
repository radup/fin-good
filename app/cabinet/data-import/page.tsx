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
      <div className="space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-base font-semibold text-gray-900 mb-3">Upload New Data</h2>
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="w-full bg-brand-gradient text-white px-4 py-3 rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload CSV Files
            </button>
            <p className="text-xs text-gray-600 mt-2">
              Upload your transaction data in CSV format for processing and categorization.
            </p>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-base font-semibold text-gray-900 mb-3">Import History</h2>
            <ImportBatchManager />
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
