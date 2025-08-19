'use client'

import React, { useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { UploadModal } from '@/components/UploadModal'
import { ImportBatchManager } from '@/components/ImportBatchManager'

export default function UploadPage() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleUploadSuccess = () => {
    setIsUploadModalOpen(false)
    setRefreshKey(prev => prev + 1)
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Upload</h1>
          <p className="mt-1 text-sm text-gray-500">
            Import and map your financial data files
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Modal */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload New File</h2>
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="btn-primary"
            >
              Upload CSV File
            </button>
            <UploadModal 
              isOpen={isUploadModalOpen}
              onClose={() => setIsUploadModalOpen(false)}
              onUploadSuccess={handleUploadSuccess}
            />
          </div>
          
          {/* Import Batch Manager */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Import History</h2>
            <ImportBatchManager refreshKey={refreshKey} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
