'use client'

import React, { useState, useEffect } from 'react'
import { Download, FileText, FileSpreadsheet, FileJson, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react'
import { exportAPI } from '@/lib/api'
import { ErrorBoundary } from './ErrorBoundary'

interface ExportJob {
  job_id: string
  export_name: string
  export_format: 'csv' | 'excel' | 'pdf' | 'json'
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  completed_at?: string
  total_records?: number
  file_size_bytes?: number
  download_count?: number
  download_url?: string
  error_message?: string
}

interface ExportProgress {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress_percentage: number
  current_step: string
  message: string
  estimated_completion?: string
}

export function ExportManager() {
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'excel' | 'pdf' | 'json'>('csv')
  const [exportName, setExportName] = useState('')
  const [isCreatingJob, setIsCreatingJob] = useState(false)
  const [activeJobs, setActiveJobs] = useState<Set<string>>(new Set())

  // Load export history on component mount
  useEffect(() => {
    loadExportHistory()
  }, [])

  // Poll for progress updates on active jobs
  useEffect(() => {
    const interval = setInterval(() => {
      activeJobs.forEach(jobId => {
        updateJobProgress(jobId)
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [activeJobs])

  const loadExportHistory = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await exportAPI.getHistory(50)
      setExportJobs(response.data)
      
      // Update active jobs set
      const active = new Set<string>()
      response.data.forEach((job: ExportJob) => {
        if (job.status === 'pending' || job.status === 'processing') {
          active.add(job.job_id)
        }
      })
      setActiveJobs(active)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load export history')
    } finally {
      setIsLoading(false)
    }
  }

  const updateJobProgress = async (jobId: string) => {
    try {
      const response = await exportAPI.getProgress(jobId)
      const progress: ExportProgress = response.data
      
      setExportJobs(prev => prev.map(job => 
        job.job_id === jobId 
          ? { ...job, ...progress }
          : job
      ))

      // Remove from active jobs if completed or failed
      if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
        setActiveJobs(prev => {
          const newSet = new Set(prev)
          newSet.delete(jobId)
          return newSet
        })
      }
    } catch (err) {
      console.error(`Failed to update progress for job ${jobId}:`, err)
    }
  }

  const createExportJob = async () => {
    try {
      setIsCreatingJob(true)
      setError(null)
      
      const jobData = {
        export_format: selectedFormat,
        export_name: exportName || `Export_${new Date().toISOString().split('T')[0]}`,
        filters: {}, // Add filter options here
        columns_config: {}, // Add column configuration here
        options_config: {} // Add export options here
      }

      const response = await exportAPI.createJob(jobData)
      const newJob: ExportJob = response.data
      
      setExportJobs(prev => [newJob, ...prev])
      setActiveJobs(prev => new Set(prev).add(newJob.job_id))
      setExportName('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create export job')
    } finally {
      setIsCreatingJob(false)
    }
  }

  const cancelExportJob = async (jobId: string) => {
    try {
      await exportAPI.cancelJob(jobId)
      setExportJobs(prev => prev.map(job => 
        job.job_id === jobId 
          ? { ...job, status: 'cancelled' as const }
          : job
      ))
      setActiveJobs(prev => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel export job')
    }
  }

  const downloadExport = async (job: ExportJob) => {
    if (!job.download_url) return
    
    try {
      const response = await exportAPI.download(job.download_url.split('/').pop() || '')
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${job.export_name}.${job.export_format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to download export')
    }
  }

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'csv': return <FileText className="w-4 h-4" />
      case 'excel': return <FileSpreadsheet className="w-4 h-4" />
              case 'pdf': return <FileText className="w-4 h-4" />
      case 'json': return <FileJson className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />
      case 'processing': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />
      case 'cancelled': return <XCircle className="w-4 h-4 text-gray-500" />
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 border-green-200'
      case 'failed': return 'text-red-600 bg-red-50 border-red-200'
      case 'processing': return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'pending': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'cancelled': return 'text-gray-600 bg-gray-50 border-gray-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Export Manager</h2>
            <p className="text-gray-600">Export your financial data in multiple formats</p>
          </div>
          <button
            onClick={loadExportHistory}
            disabled={isLoading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Create Export Job */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Export</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Export Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Format
              </label>
              <select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="csv">CSV</option>
                <option value="excel">Excel</option>
                <option value="pdf">PDF</option>
                <option value="json">JSON</option>
              </select>
            </div>

            {/* Export Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Name (Optional)
              </label>
              <input
                type="text"
                value={exportName}
                onChange={(e) => setExportName(e.target.value)}
                placeholder="My Export"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Create Button */}
            <div className="flex items-end">
              <button
                onClick={createExportJob}
                disabled={isCreatingJob}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isCreatingJob ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Create Export
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Format Information */}
          <div className="bg-gray-50 rounded-md p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Format Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <strong>CSV:</strong> Comma-separated values, ideal for spreadsheet applications
              </div>
              <div>
                <strong>Excel:</strong> Microsoft Excel format with formatting and multiple sheets
              </div>
              <div>
                <strong>PDF:</strong> Portable Document Format for professional reports
              </div>
              <div>
                <strong>JSON:</strong> JavaScript Object Notation for API integration
              </div>
            </div>
          </div>
        </div>

        {/* Export History */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Export History</h3>
          </div>
          
          {isLoading ? (
            <div className="p-6 text-center">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-gray-400" />
              <p className="text-gray-500 mt-2">Loading export history...</p>
            </div>
          ) : exportJobs.length === 0 ? (
            <div className="p-6 text-center">
              <FileText className="w-12 h-12 mx-auto text-gray-400" />
              <p className="text-gray-500 mt-2">No exports found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Export
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Format
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {exportJobs.map((job) => (
                    <tr key={job.job_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {job.export_name}
                        </div>
                        {job.total_records && (
                          <div className="text-sm text-gray-500">
                            {job.total_records.toLocaleString()} records
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getFormatIcon(job.export_format)}
                          <span className="text-sm text-gray-900 uppercase">
                            {job.export_format}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(job.status)}`}>
                          {getStatusIcon(job.status)}
                          <span className="capitalize">{job.status}</span>
                        </div>
                        {job.error_message && (
                          <div className="text-xs text-red-600 mt-1">
                            {job.error_message}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(job.created_at).toLocaleDateString()}
                        <br />
                        {new Date(job.created_at).toLocaleTimeString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          {job.status === 'completed' && job.download_url && (
                            <button
                              onClick={() => downloadExport(job)}
                              className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                            >
                              <Download className="w-4 h-4" />
                              Download
                            </button>
                          )}
                          {(job.status === 'pending' || job.status === 'processing') && (
                            <button
                              onClick={() => cancelExportJob(job.job_id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  )
}
