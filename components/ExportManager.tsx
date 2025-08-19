'use client'

import React, { useState, useEffect } from 'react'
import { 
  Download, 
  FileText, 
  FileSpreadsheet, 
  FilePdf, 
  FileJson,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  History,
  Trash2
} from 'lucide-react'
import { exportAPI } from '@/lib/api'

interface ExportJob {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  download_url?: string
  created_at: string
  estimated_completion?: string
}

interface ExportRequest {
  export_name?: string
  format: 'csv' | 'excel' | 'pdf' | 'json'
  filters: {
    start_date?: string
    end_date?: string
    categories?: string[]
    vendors?: string[]
    min_amount?: number
    max_amount?: number
    is_income?: boolean
    is_categorized?: boolean
  }
  columns?: string[]
  options?: {
    include_headers?: boolean
    date_format?: string
    number_format?: string
  }
}

interface ExportManagerProps {
  className?: string
}

export default function ExportManager({ className = '' }: ExportManagerProps) {
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [activeTab, setActiveTab] = useState<'create' | 'history'>('create')

  // Export form state
  const [exportForm, setExportForm] = useState<ExportRequest>({
    format: 'csv',
    filters: {},
    columns: ['date', 'description', 'amount', 'category', 'subcategory'],
    options: {
      include_headers: true,
      date_format: 'YYYY-MM-DD',
      number_format: '0.00'
    }
  })

  // Fetch export history
  const fetchExportHistory = async () => {
    try {
      setLoading(true)
      const response = await exportAPI.getExportHistory()
      setExportJobs(response.data.jobs || [])
    } catch (err: any) {
      console.error('Failed to fetch export history:', err)
      setError(err.response?.data?.detail || 'Failed to load export history')
    } finally {
      setLoading(false)
    }
  }

  // Create new export job
  const createExport = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await exportAPI.createExport(exportForm)
      const newJob = response.data
      
      setExportJobs(prev => [newJob, ...prev])
      setShowCreateForm(false)
      
      // Reset form
      setExportForm({
        format: 'csv',
        filters: {},
        columns: ['date', 'description', 'amount', 'category', 'subcategory'],
        options: {
          include_headers: true,
          date_format: 'YYYY-MM-DD',
          number_format: '0.00'
        }
      })
      
    } catch (err: any) {
      console.error('Failed to create export:', err)
      setError(err.response?.data?.detail || 'Failed to create export job')
    } finally {
      setLoading(false)
    }
  }

  // Download export file
  const downloadExport = async (jobId: string) => {
    try {
      const blob = await exportAPI.downloadExport(jobId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `export-${jobId}.${exportForm.format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err: any) {
      console.error('Failed to download export:', err)
      setError('Failed to download export file')
    }
  }

  // Cancel export job
  const cancelExport = async (jobId: string) => {
    try {
      await exportAPI.cancelExport(jobId)
      setExportJobs(prev => prev.map(job => 
        job.job_id === jobId 
          ? { ...job, status: 'failed', message: 'Export cancelled' }
          : job
      ))
    } catch (err: any) {
      console.error('Failed to cancel export:', err)
      setError('Failed to cancel export job')
    }
  }

  // Poll for job updates
  useEffect(() => {
    const pollJobs = async () => {
      const activeJobs = exportJobs.filter(job => 
        job.status === 'pending' || job.status === 'processing'
      )
      
      if (activeJobs.length === 0) return
      
      for (const job of activeJobs) {
        try {
          const response = await exportAPI.getExportStatus(job.job_id)
          const updatedJob = response.data
          
          setExportJobs(prev => prev.map(j => 
            j.job_id === job.job_id ? updatedJob : j
          ))
        } catch (err) {
          console.error('Failed to update job status:', err)
        }
      }
    }

    const interval = setInterval(pollJobs, 2000) // Poll every 2 seconds
    return () => clearInterval(interval)
  }, [exportJobs])

  useEffect(() => {
    fetchExportHistory()
  }, [])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'processing':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
      default:
        return <Clock className="w-5 h-5 text-gray-600" />
    }
  }

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'csv':
        return <FileText className="w-4 h-4" />
      case 'excel':
        return <FileSpreadsheet className="w-4 h-4" />
      case 'pdf':
        return <FilePdf className="w-4 h-4" />
      case 'json':
        return <FileJson className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Export Manager</h2>
            <p className="text-sm text-gray-500">Export your data in multiple formats</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchExportHistory}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab('create')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'create'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            Create Export
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'history'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            Export History
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'create' ? (
          <div className="space-y-6">
            {/* Export Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {(['csv', 'excel', 'pdf', 'json'] as const).map((format) => (
                    <button
                      key={format}
                      onClick={() => setExportForm(prev => ({ ...prev, format }))}
                      className={`p-3 border rounded-lg text-left transition-colors ${
                        exportForm.format === format
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {getFormatIcon(format)}
                        <span className="font-medium uppercase">{format}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Export Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Name (Optional)
                </label>
                <input
                  type="text"
                  value={exportForm.export_name || ''}
                  onChange={(e) => setExportForm(prev => ({ 
                    ...prev, 
                    export_name: e.target.value 
                  }))}
                  placeholder="e.g., Monthly Report"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={exportForm.filters.start_date || ''}
                  onChange={(e) => setExportForm(prev => ({ 
                    ...prev, 
                    filters: { ...prev.filters, start_date: e.target.value }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={exportForm.filters.end_date || ''}
                  onChange={(e) => setExportForm(prev => ({ 
                    ...prev, 
                    filters: { ...prev.filters, end_date: e.target.value }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Export Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Options
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportForm.options?.include_headers || false}
                    onChange={(e) => setExportForm(prev => ({ 
                      ...prev, 
                      options: { ...prev.options, include_headers: e.target.checked }
                    }))}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-600">Include headers</span>
                </label>
              </div>
            </div>

            {/* Create Export Button */}
            <div className="flex justify-end">
              <button
                onClick={createExport}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 inline mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 inline mr-2" />
                    Create Export
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Export History */}
            {loading ? (
              <div className="text-center py-8">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
                <p className="text-gray-500 mt-2">Loading export history...</p>
              </div>
            ) : exportJobs.length === 0 ? (
              <div className="text-center py-8">
                <Download className="w-12 h-12 mx-auto text-gray-400" />
                <p className="text-gray-500 mt-2">No export jobs found</p>
              </div>
            ) : (
              <div className="space-y-3">
                {exportJobs.map((job) => (
                  <div
                    key={job.job_id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(job.status)}
                        <div>
                          <p className="font-medium text-gray-900">
                            {job.export_name || `Export ${job.job_id.slice(0, 8)}`}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatDate(job.created_at)}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {job.status === 'processing' && (
                          <div className="text-sm text-gray-500">
                            {job.progress}%
                          </div>
                        )}
                        
                        {job.status === 'completed' && job.download_url && (
                          <button
                            onClick={() => downloadExport(job.job_id)}
                            className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 transition-colors"
                          >
                            <Download className="w-4 h-4 inline mr-1" />
                            Download
                          </button>
                        )}
                        
                        {(job.status === 'pending' || job.status === 'processing') && (
                          <button
                            onClick={() => cancelExport(job.job_id)}
                            className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200 transition-colors"
                          >
                            <XCircle className="w-4 h-4 inline mr-1" />
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                    
                    {job.message && (
                      <p className="text-sm text-gray-600 mt-2">{job.message}</p>
                    )}
                    
                    {job.status === 'processing' && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
