'use client'

import { useState, useCallback, useEffect } from 'react'
import { Upload, X, FileText, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { uploadAPI } from '@/lib/api'

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUploadSuccess?: () => void
}

interface UploadStatus {
  success?: boolean
  message?: string
  file_info?: {
    filename: string
    file_size: number
    total_rows: number
  }
  parsing_results?: {
    successful_parsing: number
    failed_parsing: number
    success_rate: number
    warning_count: number
  }
  database_results?: {
    processed_count: number
    database_errors: number
  }
  categorization_results?: {
    categorized_count: number
    categorization_rate: number
  }
  statistics?: {
    total_rows: number
    successful_parsing: number
    failed_parsing: number
    success_rate: number
    warning_count: number
    error_types: Record<string, number>
    warning_types: Record<string, number>
    amount_range: { min: number; max: number; avg: number }
    date_range: { earliest: string | null; latest: string | null }
    income_count: number
    expense_count: number
  }
  errors?: Array<{
    row_number?: number
    error_type: string
    message: string
    raw_data?: any
    column_mapping?: any
  }>
  warnings?: Array<{
    row_number: number
    warning_type: string
    message: string
    details: any
  }>
  summary?: {
    total_transactions: number
    successfully_categorized: number
    overall_success_rate: number
  }
}

export function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  // Reset state whenever the modal opens so previous results don't persist
  useEffect(() => {
    if (isOpen) {
      setUploading(false)
      setUploadStatus(null)
      setShowDetails(false)
    }
  }, [isOpen])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    setUploading(true)
    setUploadStatus(null)
    setShowDetails(false)

    try {
      const response = await uploadAPI.csv(file)

      setUploadStatus({
        success: true,
        message: 'File uploaded successfully!',
        ...response.data
      })
      
      // Notify parent component that upload was successful
      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (error: any) {
      let errorMessage = 'Upload failed'
      
      if (error.response?.data?.detail) {
        // Handle different error response structures
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else if (error.response.data.detail.message) {
          errorMessage = String(error.response.data.detail.message)
        } else {
          errorMessage = 'Upload validation failed'
        }
      }
      
      setUploadStatus({
        success: false,
        message: String(errorMessage),
      })
    } finally {
      setUploading(false)
    }
  }, [onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
  })

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getErrorIcon = (errorType: any) => {
    const type = String(errorType || 'unknown')
    switch (type) {
      case 'ValueError':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />
      case 'ValidationError':
        return <AlertCircle className="w-4 h-4 text-danger-500" />
      default:
        return <Info className="w-4 h-4 text-info-500" />
    }
  }

  const getWarningIcon = (warningType: any) => {
    const type = String(warningType || 'unknown')
    switch (type) {
      case 'DataQualityWarning':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />
      default:
        return <Info className="w-4 h-4 text-info-500" />
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Upload CSV File</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {!uploadStatus && (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop the file here' : 'Drag & drop a CSV file here'}
              </p>
              <p className="text-gray-600 mb-4">
                or click to select a file
              </p>
              <p className="text-sm text-gray-500">
                Supported format: CSV files only
              </p>
            </div>
          )}

          {uploading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Uploading and processing file...</p>
            </div>
          )}

          {uploadStatus && (
            <>
              <div className={`p-4 rounded-lg mb-6 ${
                uploadStatus.success 
                  ? 'bg-success-50 border border-success-200' 
                  : 'bg-danger-50 border border-danger-200'
              }`}>
                <div className="flex items-center">
                  {uploadStatus.success ? (
                    <CheckCircle className="w-6 h-6 text-success-600 mr-3" />
                  ) : (
                    <AlertCircle className="w-6 h-6 text-danger-600 mr-3" />
                  )}
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {uploadStatus.success ? 'Upload Successful!' : 'Upload Failed'}
                    </h3>
                    <p className="text-gray-600">{uploadStatus.message}</p>
                  </div>
                </div>

                {/* File Info */}
                {uploadStatus.file_info && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-3">File Information</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <p className="text-gray-500">Filename</p>
                        <p className="font-medium">{uploadStatus.file_info.filename}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">File Size</p>
                        <p className="font-medium">{formatFileSize(uploadStatus.file_info.file_size)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Total Rows</p>
                        <p className="font-medium">{uploadStatus.file_info.total_rows}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Summary */}
                {uploadStatus.summary && (
                  <div className="mt-4 p-4 bg-success-50 rounded-lg">
                    <h4 className="font-medium text-success-900 mb-3">Upload Summary</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <p className="text-success-700">Total Transactions</p>
                        <p className="font-medium text-success-900">{uploadStatus.summary.total_transactions}</p>
                      </div>
                      <div>
                        <p className="text-success-700">Successfully Categorized</p>
                        <p className="font-medium text-success-900">{uploadStatus.summary.successfully_categorized}</p>
                      </div>
                      <div>
                        <p className="text-success-700">Overall Success Rate</p>
                        <p className="font-medium text-success-900">{uploadStatus.summary.overall_success_rate}%</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Parsing Results */}
                {uploadStatus.parsing_results && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-3">Parsing Results</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-700">Successful:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.successful_parsing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Failed:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.failed_parsing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Success Rate:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.success_rate}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Warnings:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.warning_count}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Database Results */}
                {uploadStatus.database_results && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-3">Database Results</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-green-700">Processed:</span>
                        <span className="font-medium text-green-900">{uploadStatus.database_results.processed_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-green-700">Database Errors:</span>
                        <span className="font-medium text-green-900">{uploadStatus.database_results.database_errors}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Categorization Results */}
                {uploadStatus.categorization_results && (
                  <div className="mt-4 p-4 bg-purple-50 rounded-lg">
                    <h4 className="font-medium text-purple-900 mb-3">Categorization Results</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-purple-700">Categorized:</span>
                        <span className="font-medium text-purple-900">{uploadStatus.categorization_results.categorized_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-purple-700">Categorization Rate:</span>
                        <span className="font-medium text-purple-900">{uploadStatus.categorization_results.categorization_rate}%</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Toggle Details */}
              {(uploadStatus.errors?.length || uploadStatus.warnings?.length) && (
                <div className="text-center">
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="btn-secondary"
                  >
                    {showDetails ? 'Hide' : 'Show'} Details
                  </button>
                </div>
              )}

              {/* Error Details */}
              {showDetails && uploadStatus.errors && uploadStatus.errors.length > 0 && (
                <div className="mt-4 p-4 bg-danger-50 rounded-lg">
                  <h4 className="font-medium text-danger-900 mb-3">
                    Errors ({uploadStatus.errors.length})
                  </h4>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {uploadStatus.errors.slice(0, 10).map((error: any, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        {getErrorIcon(error.error_type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium text-danger-900">
                            {String(error.error_type || 'Error')}
                            {error.row_number && ` (Row ${error.row_number})`}
                          </p>
                          <p className="text-sm text-danger-700">{String(error.message || 'Unknown error')}</p>
                        </div>
                      </div>
                    ))}
                    {uploadStatus.errors.length > 10 && (
                      <p className="text-sm text-danger-600">
                        ... and {uploadStatus.errors.length - 10} more errors
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Warning Details */}
              {showDetails && uploadStatus.warnings && uploadStatus.warnings.length > 0 && (
                <div className="mt-4 p-4 bg-warning-50 rounded-lg">
                  <h4 className="font-medium text-warning-900 mb-3">
                    Warnings ({uploadStatus.warnings.length})
                  </h4>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {uploadStatus.warnings.slice(0, 10).map((warning: any, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        {getWarningIcon(warning.warning_type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium text-warning-900">
                            {String(warning.warning_type || 'Warning')} (Row {warning.row_number})
                          </p>
                          <p className="text-sm text-warning-700">{String(warning.message || 'Unknown warning')}</p>
                        </div>
                      </div>
                    ))}
                    {uploadStatus.warnings.length > 10 && (
                      <p className="text-sm text-warning-600">
                        ... and {uploadStatus.warnings.length - 10} more warnings
                      </p>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={onClose}
              className="btn-secondary"
              disabled={uploading}
            >
              {uploadStatus ? 'Close' : 'Cancel'}
            </button>
            {uploadStatus?.success && (
              <button
                onClick={() => {
                  onClose()
                  // Notify parent component to refresh data
                  if (onUploadSuccess) {
                    onUploadSuccess()
                  }
                }}
                className="btn-primary"
              >
                View Transactions
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
