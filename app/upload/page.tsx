'use client'

import React from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import UploadModal from '@/components/UploadModal'
import ImportBatchManager from '@/components/ImportBatchManager'

export default function UploadPage() {
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
            <UploadModal />
          </div>
          
          {/* Import Batch Manager */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Import History</h2>
            <ImportBatchManager />
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
