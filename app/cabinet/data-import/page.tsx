'use client'

import { UploadModal } from '../../../components/UploadModal'
import { ImportBatchManager } from '../../../components/ImportBatchManager'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function DataImportPage() {
  return (
    <CabinetPageLayout title="Data Import" description="Upload and manage data">
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload New Data</h2>
              <UploadModal />
            </div>
            
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Import History</h2>
              <ImportBatchManager />
            </div>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}
