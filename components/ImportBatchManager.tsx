'use client'

import { useState, useEffect } from 'react'
import { Trash2, FileText, Calendar, DollarSign, AlertTriangle } from 'lucide-react'
import { transactionAPI } from '@/lib/api'

interface ImportBatch {
  batch_id: string
  transaction_count: number
  import_date: string
  total_amount: number
  filename: string
}

interface ImportBatchManagerProps {
  refreshKey?: number
}

export function ImportBatchManager({ refreshKey }: ImportBatchManagerProps) {
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDeleting, setIsDeleting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBatches()
  }, [refreshKey]) // Add refreshKey to dependency array

  const fetchBatches = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await transactionAPI.listImportBatches()
      setBatches(response.data)
    } catch (error) {
      console.error('Error fetching import batches:', error)
      setError('Failed to load import batches')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteBatch = async (batchId: string) => {
    if (!confirm('Are you sure you want to delete all transactions from this file? This action cannot be undone.')) {
      return
    }

    try {
      setIsDeleting(batchId)
      setError(null)
      
      const response = await transactionAPI.deleteImportBatch(batchId)
      
      // Show success message
      alert(response.data.message)
      
      // Refresh the batches list
      await fetchBatches()
      
      // Trigger a page refresh to update the main transaction list
      window.location.reload()
      
    } catch (error: any) {
      console.error('Error deleting import batch:', error)
      setError(error.response?.data?.detail || 'Failed to delete import batch')
    } finally {
      setIsDeleting(null)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-2 text-gray-600">Loading import batches...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8 text-red-600">
          <AlertTriangle className="w-5 h-5 mr-2" />
          <span>{error}</span>
        </div>
      </div>
    )
  }

  if (batches.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Import Files</h3>
          <p className="text-gray-600">No CSV files have been imported yet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Import Files</h2>
        <span className="text-sm text-gray-500">{batches.length} file{batches.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="space-y-4">
        {batches.map((batch) => (
          <div key={batch.batch_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <FileText className="w-8 h-8 text-primary-600" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {formatDate(batch.import_date)}
                    </div>
                    <div className="flex items-center">
                      <span className="font-medium">{batch.transaction_count}</span>
                      <span className="ml-1">transaction{batch.transaction_count !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="flex items-center">
                      <DollarSign className="w-4 h-4 mr-1" />
                      {formatAmount(batch.total_amount)}
                    </div>
                  </div>
                  
                  <div className="mt-1">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {batch.filename}
                    </div>
                    <code className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {batch.batch_id.substring(0, 8)}...
                    </code>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleDeleteBatch(batch.batch_id)}
                disabled={isDeleting === batch.batch_id}
                className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDeleting === batch.batch_id ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600 mr-2"></div>
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-1" />
                    Delete File
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium">Warning</p>
            <p>Deleting an import file will permanently remove all transactions from that file. This action cannot be undone.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
