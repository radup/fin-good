'use client'

import { useState, useCallback } from 'react'
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
      setUploadStatus({
        success: false,
        message: error.response?.data?.detail || 'Upload failed',
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

  const getErrorIcon = (errorType: string) => {
    switch (errorType) {
      case 'ValueError':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />
      case 'database_error':
        return <AlertCircle className="w-4 h-4 text-danger-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getWarningIcon = (warningType: string) => {
    switch (warningType) {
      case 'large_amount':
      case 'future_date':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />
      default:
        return <Info className="w-4 h-4 text-blue-500" />
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Upload CSV File</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {!uploadStatus ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-primary-600">Drop the CSV file here...</p>
            ) : (
              <div>
                <p className="text-gray-600 mb-2">
                  Drag and drop a CSV file here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supported format: CSV with date, amount, and description columns
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {uploadStatus.success ? (
              <>
                {/* Success Header */}
                <div className="text-center">
                  <CheckCircle className="w-12 h-12 text-success-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Upload Successful!
                  </h3>
                  <p className="text-gray-600">{uploadStatus.message}</p>
                </div>

                {/* File Info */}
                {uploadStatus.file_info && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-3">File Information</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
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

                {/* Summary Statistics */}
                {uploadStatus.summary && (
                  <div className="bg-success-50 border border-success-200 rounded-lg p-4">
                    <h4 className="font-medium text-success-900 mb-3">Summary</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
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

                {/* Detailed Results */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Parsing Results */}
                  {uploadStatus.parsing_results && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900 mb-3">Parsing Results</h4>
                      <div className="space-y-2 text-sm">
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
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-900 mb-3">Database Results</h4>
                      <div className="space-y-2 text-sm">
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
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <h4 className="font-medium text-purple-900 mb-3">Categorization Results</h4>
                      <div className="space-y-2 text-sm">
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

                {/* Detailed Errors and Warnings */}
                {showDetails && (
                  <div className="space-y-4">
                    {/* Errors */}
                    {uploadStatus.errors && uploadStatus.errors.length > 0 && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <h4 className="font-medium text-red-900 mb-3 flex items-center gap-2">
                          <AlertCircle className="w-5 h-5" />
                          Errors ({uploadStatus.errors.length})
                        </h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {uploadStatus.errors.slice(0, 10).map((error, index) => (
                            <div key={index} className="flex items-start gap-2 text-sm">
                              {getErrorIcon(error.error_type)}
                              <div className="flex-1">
                                <p className="text-red-800 font-medium">
                                  Row {error.row_number || 'Unknown'}: {error.message}
                                </p>
                                {error.raw_data && (
                                  <p className="text-red-600 text-xs">
                                    Data: {JSON.stringify(error.raw_data)}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                          {uploadStatus.errors.length > 10 && (
                            <p className="text-red-600 text-xs">
                              ... and {uploadStatus.errors.length - 10} more errors
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Warnings */}
                    {uploadStatus.warnings && uploadStatus.warnings.length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <h4 className="font-medium text-yellow-900 mb-3 flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5" />
                          Warnings ({uploadStatus.warnings.length})
                        </h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {uploadStatus.warnings.slice(0, 10).map((warning, index) => (
                            <div key={index} className="flex items-start gap-2 text-sm">
                              {getWarningIcon(warning.warning_type)}
                              <div className="flex-1">
                                <p className="text-yellow-800 font-medium">
                                  Row {warning.row_number}: {warning.message}
                                </p>
                                {warning.details && (
                                  <p className="text-yellow-600 text-xs">
                                    Details: {JSON.stringify(warning.details)}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                          {uploadStatus.warnings.length > 10 && (
                            <p className="text-yellow-600 text-xs">
                              ... and {uploadStatus.warnings.length - 10} more warnings
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-danger-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Upload Failed
                </h3>
                <p className="text-gray-600 mb-4">{uploadStatus.message}</p>
              </div>
            )}
          </div>
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
                setUploadStatus(null)
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
  )
}
