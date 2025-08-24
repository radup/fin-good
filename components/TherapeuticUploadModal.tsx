'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react';
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar';
import TherapeuticUploadProgress from './TherapeuticUploadProgress';
import { 
  ArrowUpTrayIcon,
  XMarkIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  SparklesIcon,
  PhotoIcon,
  FolderIcon
} from '@heroicons/react/24/outline';
import { useDropzone } from 'react-dropzone'
import { uploadAPI } from '@/lib/api'

interface TherapeuticUploadModalProps {
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

export function TherapeuticUploadModal({ isOpen, onClose, onUploadSuccess }: TherapeuticUploadModalProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [uploadStage, setUploadStage] = useState<'uploading' | 'processing' | 'categorizing' | 'complete'>('uploading')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isMobile, setIsMobile] = useState(false)

  // Detect mobile device
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Reset state whenever the modal opens
  useEffect(() => {
    if (isOpen) {
      setUploading(false)
      setUploadStatus(null)
      setShowDetails(false)
      setUploadStage('uploading')
      setUploadProgress(0)
    }
  }, [isOpen])

  // Simulate upload progress stages
  useEffect(() => {
    if (uploading) {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev < 25) {
            setUploadStage('uploading')
            return prev + 5
          } else if (prev < 50) {
            setUploadStage('processing')
            return prev + 3
          } else if (prev < 85) {
            setUploadStage('categorizing')
            return prev + 2
          } else {
            setUploadStage('complete')
            return 100
          }
        })
      }, 200)

      return () => clearInterval(progressInterval)
    }
  }, [uploading])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    setUploading(true)
    setUploadStatus(null)
    setShowDetails(false)
    setUploadProgress(0)
    setUploadStage('uploading')

    try {
      const response = await uploadAPI.csv(file)

      setUploadStatus({
        success: true,
        message: 'Your financial data has been successfully processed!',
        ...response.data
      })
      
      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (error: any) {
      let errorMessage = 'We encountered an issue processing your file'
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else if (error.response.data.detail.message) {
          errorMessage = String(error.response.data.detail.message)
        } else {
          errorMessage = 'There was a problem with your file format'
        }
      }
      
      setUploadStatus({
        success: false,
        message: errorMessage,
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
    noClick: false, // Allow clicking on mobile
    noDrag: isMobile, // Disable drag on mobile for better UX
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
        return <ExclamationTriangleIcon className="w-4 h-4 text-warning-500" />
      case 'ValidationError':
        return <ExclamationTriangleIcon className="w-4 h-4 text-danger-500" />
      default:
        return <InformationCircleIcon className="w-4 h-4 text-info-500" />
    }
  }

  const getWarningIcon = (warningType: any) => {
    const type = String(warningType || 'unknown')
    switch (type) {
      case 'DataQualityWarning':
        return <ExclamationTriangleIcon className="w-4 h-4 text-warning-500" />
      default:
        return <InformationCircleIcon className="w-4 h-4 text-info-500" />
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={`bg-white rounded-lg shadow-xl w-full max-h-[90vh] overflow-y-auto ${
        isMobile ? 'max-w-full mx-0' : 'max-w-2xl mx-4'
      }`}>
        <div className={`${isMobile ? 'p-4' : 'p-6'}`}>
          {/* Header - Mobile Optimized */}
          <div className={`flex justify-between items-center mb-6 ${
            isMobile ? 'mb-4' : 'mb-6'
          }`}>
            <div className={`flex items-center gap-3 ${
              isMobile ? 'flex-1 min-w-0' : ''
            }`}>
              <h2 className={`font-bold text-gray-900 ${
                isMobile ? 'text-xl' : 'text-2xl'
              } ${isMobile ? 'truncate' : ''}`}>
                Upload Your Financial Data
              </h2>
              {!isMobile && (
                <DrSigmundSpendAvatar 
                  size="sm" 
                  mood="encouraging"
                  message="I'm here to help you understand your finances!"
                  showMessage={false}
                />
              )}
            </div>
            <button
              onClick={onClose}
              className={`text-gray-400 hover:text-gray-600 transition-colors therapeutic-transition ${
                isMobile ? 'p-2 -m-2' : ''
              }`}
              aria-label="Close modal"
            >
              <XMarkIcon className={`${isMobile ? 'w-5 h-5' : 'w-6 h-6'}`} />
            </button>
          </div>

          {/* Mobile Avatar - Show below header on mobile */}
          {isMobile && (
            <div className="flex justify-center mb-4">
              <DrSigmundSpendAvatar 
                size="sm" 
                mood="encouraging"
                message="I'm here to help you understand your finances!"
                showMessage={true}
              />
            </div>
          )}

          {!uploadStatus && !uploading && (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg text-center cursor-pointer therapeutic-transition therapeutic-hover ${
                isMobile 
                  ? 'p-6 border-gray-300 hover:border-blue-400' 
                  : 'p-8 border-gray-300 hover:border-blue-400'
              } ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400'
              }`}
            >
              <input {...getInputProps()} />
              
              {/* Mobile-optimized upload area */}
              {isMobile ? (
                <div className="space-y-4">
                  <div className="flex justify-center">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                      <PhotoIcon className="w-8 h-8 text-blue-600" />
                    </div>
                  </div>
                  <div>
                    <p className="text-lg font-medium text-gray-900 mb-2">
                      Tap to select your CSV file
                    </p>
                    <p className="text-sm text-gray-600 mb-4">
                      We'll help you understand your finances
                    </p>
                  </div>
                  
                  {/* Mobile file selection buttons */}
                  <div className="space-y-3">
                    <button
                      type="button"
                      className="w-full bg-brand-gradient text-white py-3 px-4 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105"
                      onClick={() => (document.querySelector('input[type="file"]') as HTMLInputElement)?.click()}
                    >
                      <div className="flex items-center justify-center gap-2">
                        <FolderIcon className="w-5 h-5" />
                        Choose File
                      </div>
                    </button>
                    
                    <div className="text-xs text-gray-500">
                      Supported: CSV files only
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mb-4">
                  <ArrowUpTrayIcon className="w-12 h-12 text-blue-400 mx-auto" />
                </div>
              )}
              
              {!isMobile && (
                <>
                  <p className="text-lg font-medium text-gray-900 mb-2">
                    {isDragActive ? 'Drop your file here' : 'Drag & drop your CSV file here'}
                  </p>
                  <p className="text-gray-600 mb-4">
                    or click to select a file
                  </p>
                </>
              )}
              
              {/* Security message - Mobile optimized */}
              <div className={`bg-blue-50 rounded-lg border border-blue-200 ${
                isMobile ? 'p-3 mt-4' : 'p-4'
              }`}>
                <div className={`flex items-center gap-2 text-sm text-blue-700 mb-2 ${
                  isMobile ? 'justify-center' : ''
                }`}>
                  <ShieldCheckIcon className="w-4 h-4" />
                  <span className="font-medium">Your data is secure</span>
                </div>
                <p className={`text-blue-600 ${
                  isMobile ? 'text-xs text-center' : 'text-xs'
                }`}>
                  We use bank-level encryption and never share your personal information
                </p>
              </div>
            </div>
          )}

          {uploading && (
            <TherapeuticUploadProgress
              progress={uploadProgress}
              stage={uploadStage}
              filename="your file"
              className="mb-4"
              isMobile={isMobile}
            />
          )}

          {uploadStatus && (
            <>
              <div className={`rounded-lg mb-6 therapeutic-transition ${
                uploadStatus.success 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              } ${isMobile ? 'p-4' : 'p-6'}`}>
                <div className={`flex items-start gap-4 ${
                  isMobile ? 'flex-col text-center' : ''
                }`}>
                  {uploadStatus.success ? (
                    <div className={`bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isMobile ? 'w-12 h-12 mx-auto' : 'w-12 h-12'
                    }`}>
                      <CheckCircleIcon className="w-6 h-6 text-green-600" />
                    </div>
                  ) : (
                    <div className={`bg-red-100 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isMobile ? 'w-12 h-12 mx-auto' : 'w-12 h-12'
                    }`}>
                      <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className={`font-medium text-gray-900 mb-2 ${
                      isMobile ? 'text-center' : ''
                    }`}>
                      {uploadStatus.success ? 'Upload Successful!' : 'Upload Failed'}
                    </h3>
                    <p className={`text-gray-600 mb-3 ${
                      isMobile ? 'text-center' : ''
                    }`}>{uploadStatus.message}</p>
                    
                    {uploadStatus.success && (
                      <div className={isMobile ? 'flex justify-center' : ''}>
                        <DrSigmundSpendAvatar 
                          size="sm" 
                          mood="celebrating"
                          message="Excellent! Your financial insights are ready to explore."
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* File Info - Mobile optimized */}
                {uploadStatus.file_info && (
                  <div className={`mt-6 bg-gray-50 rounded-lg ${
                    isMobile ? 'p-3' : 'p-4'
                  }`}>
                    <h4 className={`font-medium text-gray-900 mb-3 ${
                      isMobile ? 'text-center' : ''
                    }`}>File Information</h4>
                    <div className={`gap-4 ${
                      isMobile 
                        ? 'space-y-3' 
                        : 'grid grid-cols-3 gap-4'
                    }`}>
                      <div className={isMobile ? 'text-center' : ''}>
                        <p className="text-gray-500 text-sm">Filename</p>
                        <p className={`font-medium ${isMobile ? 'text-sm truncate' : ''}`}>
                          {uploadStatus.file_info.filename}
                        </p>
                      </div>
                      <div className={isMobile ? 'text-center' : ''}>
                        <p className="text-gray-500 text-sm">File Size</p>
                        <p className="font-medium">{formatFileSize(uploadStatus.file_info.file_size)}</p>
                      </div>
                      <div className={isMobile ? 'text-center' : ''}>
                        <p className="text-gray-500 text-sm">Total Rows</p>
                        <p className="font-medium">{uploadStatus.file_info.total_rows}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Summary - Mobile optimized */}
                {uploadStatus.summary && (
                  <div className={`mt-6 bg-green-50 rounded-lg border border-green-200 ${
                    isMobile ? 'p-3' : 'p-4'
                  }`}>
                    <h4 className={`font-medium text-green-900 mb-3 ${
                      isMobile ? 'text-center' : ''
                    }`}>Processing Summary</h4>
                    <div className={`gap-4 ${
                      isMobile 
                        ? 'space-y-3' 
                        : 'grid grid-cols-3 gap-4'
                    }`}>
                      <div className={isMobile ? 'text-center' : ''}>
                        <p className="text-green-700 text-sm">Total Transactions</p>
                        <p className="font-medium text-green-900">{uploadStatus.summary.total_transactions}</p>
                      </div>
                      <div className={isMobile ? 'text-center' : ''}>
                        <p className="text-green-700 text-sm">Successfully Categorized</p>
                        <p className="font-medium text-green-900">{uploadStatus.summary.successfully_categorized}</p>
                      </div>
                      <div className={isMobile ? 'text-center' : ''}>
                        <p className="text-green-700 text-sm">Success Rate</p>
                        <p className="font-medium text-green-900">{uploadStatus.summary.overall_success_rate}%</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Parsing Results - Mobile optimized */}
                {uploadStatus.parsing_results && (
                  <div className={`mt-6 bg-blue-50 rounded-lg border border-blue-200 ${
                    isMobile ? 'p-3' : 'p-4'
                  }`}>
                    <h4 className={`font-medium text-blue-900 mb-3 ${
                      isMobile ? 'text-center' : ''
                    }`}>Data Processing Results</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-700 text-sm">Successfully processed:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.successful_parsing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700 text-sm">Issues found:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.failed_parsing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700 text-sm">Success rate:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.success_rate}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700 text-sm">Warnings:</span>
                        <span className="font-medium text-blue-900">{uploadStatus.parsing_results.warning_count}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Database Results - Mobile optimized */}
                {uploadStatus.database_results && (
                  <div className={`mt-6 bg-purple-50 rounded-lg border border-purple-200 ${
                    isMobile ? 'p-3' : 'p-4'
                  }`}>
                    <h4 className={`font-medium text-purple-900 mb-3 ${
                      isMobile ? 'text-center' : ''
                    }`}>Database Processing</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-purple-700 text-sm">Processed:</span>
                        <span className="font-medium text-purple-900">{uploadStatus.database_results.processed_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-purple-700 text-sm">Errors:</span>
                        <span className="font-medium text-purple-900">{uploadStatus.database_results.database_errors}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Categorization Results - Mobile optimized */}
                {uploadStatus.categorization_results && (
                  <div className={`mt-6 bg-orange-50 rounded-lg border border-orange-200 ${
                    isMobile ? 'p-3' : 'p-4'
                  }`}>
                    <h4 className={`font-medium text-orange-900 mb-3 ${
                      isMobile ? 'text-center' : ''
                    }`}>AI Categorization</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-orange-700 text-sm">Categorized:</span>
                        <span className="font-medium text-orange-900">{uploadStatus.categorization_results.categorized_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-orange-700 text-sm">Categorization rate:</span>
                        <span className="font-medium text-orange-900">{uploadStatus.categorization_results.categorization_rate}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Errors - Mobile optimized */}
                {uploadStatus.errors && uploadStatus.errors.length > 0 && (
                  <div className="mt-6">
                    <button
                      onClick={() => setShowDetails(!showDetails)}
                      className={`text-blue-600 hover:text-blue-800 text-sm font-medium therapeutic-transition ${
                        isMobile ? 'w-full text-center py-2' : ''
                      }`}
                    >
                      {showDetails ? 'Hide' : 'Show'} Error Details ({uploadStatus.errors.length})
                    </button>
                    
                    {showDetails && (
                      <div className={`mt-4 space-y-2 ${
                        isMobile ? 'max-h-60 overflow-y-auto' : ''
                      }`}>
                        {uploadStatus.errors.map((error, index) => (
                          <div key={index} className="p-3 bg-red-50 rounded-lg border border-red-200">
                            <div className="flex items-start gap-2">
                              {getErrorIcon(error.error_type)}
                              <div className="flex-1">
                                <p className="text-sm font-medium text-red-800">
                                  Row {error.row_number}: {error.error_type}
                                </p>
                                <p className="text-sm text-red-700">{error.message}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Warnings - Mobile optimized */}
                {uploadStatus.warnings && uploadStatus.warnings.length > 0 && (
                  <div className="mt-6">
                    <button
                      onClick={() => setShowDetails(!showDetails)}
                      className={`text-yellow-600 hover:text-yellow-800 text-sm font-medium therapeutic-transition ${
                        isMobile ? 'w-full text-center py-2' : ''
                      }`}
                    >
                      {showDetails ? 'Hide' : 'Show'} Warning Details ({uploadStatus.warnings.length})
                    </button>
                    
                    {showDetails && (
                      <div className={`mt-4 space-y-2 ${
                        isMobile ? 'max-h-60 overflow-y-auto' : ''
                      }`}>
                        {uploadStatus.warnings.map((warning, index) => (
                          <div key={index} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                            <div className="flex items-start gap-2">
                              {getWarningIcon(warning.warning_type)}
                              <div className="flex-1">
                                <p className="text-sm font-medium text-yellow-800">
                                  Row {warning.row_number}: {warning.warning_type}
                                </p>
                                <p className="text-sm text-yellow-700">{warning.message}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Action buttons - Mobile optimized */}
              <div className={`flex gap-3 ${
                isMobile ? 'flex-col' : 'justify-end'
              }`}>
                <button
                  onClick={onClose}
                  className={`text-gray-600 hover:text-gray-800 therapeutic-transition ${
                    isMobile 
                      ? 'w-full py-3 px-4 border border-gray-300 rounded-lg' 
                      : 'px-4 py-2'
                  }`}
                >
                  Close
                </button>
                {uploadStatus.success && (
                  <button
                    onClick={onClose}
                    className={`bg-brand-gradient text-white rounded-lg transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 ${
                      isMobile 
                        ? 'w-full py-3 px-4 font-medium' 
                        : 'px-4 py-2'
                    }`}
                  >
                    View Your Data
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
