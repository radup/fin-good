'use client'

import React, { useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { UploadModal } from '@/components/UploadModal'
import { ImportBatchManager } from '@/components/ImportBatchManager'

export default function UploadPage() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)

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
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Upload CSV File</h3>
                <p className="text-gray-600 mb-6">
                  Import your financial transactions from a CSV file for AI-powered categorization and analysis.
                </p>
                <button
                  onClick={() => setIsUploadModalOpen(true)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Choose File
                </button>
              </div>
            </div>
          </div>
          
          {/* Import Batch Manager */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Import History</h2>
            <ImportBatchManager />
          </div>
        </div>

        {/* Upload Modal */}
        <UploadModal 
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUploadSuccess={() => {
            setIsUploadModalOpen(false)
            // Could trigger a refresh here
          }}
        />
      </div>
    </DashboardLayout>
  )
}
