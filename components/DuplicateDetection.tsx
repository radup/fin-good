'use client'

import React, { useState, useEffect } from 'react'
import { Search, Merge, X, AlertTriangle, CheckCircle, Clock, RefreshCw } from 'lucide-react'
import { duplicateDetectionAPI } from '@/lib/api'
import { DuplicateGroup, DuplicateScanResponse } from '@/types/api'
import { ErrorBoundary } from './ErrorBoundary'

interface DuplicateDetectionProps {
  className?: string
}

export function DuplicateDetection({ className = '' }: DuplicateDetectionProps) {
  const [duplicateGroups, setDuplicateGroups] = useState<DuplicateGroup[]>([])
  const [isScanning, setIsScanning] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [scanResults, setScanResults] = useState<DuplicateScanResponse | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<string | null>('group-1') // Expand first group by default
  const [message, setMessage] = useState<string | null>(null)
  const [stats, setStats] = useState<any>(null)

  // Fetch duplicate groups on mount
  useEffect(() => {
    fetchDuplicateGroups()
    fetchStats()
  }, [])

  const fetchDuplicateGroups = async () => {
    setIsLoading(true)
    try {
      const response = await duplicateDetectionAPI.getGroups({ limit: 50 })
      setDuplicateGroups(response.data)
    } catch (error) {
      console.error('Error fetching duplicate groups:', error)
      setMessage('Error loading duplicate groups')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await duplicateDetectionAPI.getStats()
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching duplicate stats:', error)
    }
  }

  const handleScan = async () => {
    setIsScanning(true)
    setMessage(null)
    
    try {
      const response = await duplicateDetectionAPI.scan({
        confidence_threshold: 0.8,
        max_results: 100
      })
      
      setScanResults(response.data)
      setMessage(
        `Scan completed: Found ${response.data.duplicate_groups_found} groups with ${response.data.total_duplicates} duplicates. ` +
        `Scan duration: ${response.data.scan_duration.toFixed(2)}s`
      )
      
      // Refresh the groups list
      await fetchDuplicateGroups()
    } catch (error: any) {
      console.error('Scan failed:', error)
      setMessage('Scan failed. Please try again.')
    } finally {
      setIsScanning(false)
    }
  }

  const handleMerge = async (groupId: string, primaryTransactionId: number, fieldsToMerge: string[]) => {
    try {
      const response = await duplicateDetectionAPI.merge(groupId, primaryTransactionId, fieldsToMerge)
      setMessage(`Merge completed: ${response.data.merged_transaction_ids.length} transactions merged`)
      
      // Remove the merged group from the list
      setDuplicateGroups(prev => prev.filter(group => group.group_id !== groupId))
      setSelectedGroup(null)
      
      // Refresh stats
      await fetchStats()
    } catch (error: any) {
      console.error('Merge failed:', error)
      setMessage('Merge failed. Please try again.')
    }
  }

  const handleDismiss = async (groupId: string, reason?: string) => {
    try {
      await duplicateDetectionAPI.dismiss(groupId, reason)
      setMessage('Duplicate group dismissed')
      
      // Remove the dismissed group from the list
      setDuplicateGroups(prev => prev.filter(group => group.group_id !== groupId))
      setSelectedGroup(null)
      
      // Refresh stats
      await fetchStats()
    } catch (error: any) {
      console.error('Dismiss failed:', error)
      setMessage('Dismiss failed. Please try again.')
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600'
    if (confidence >= 0.7) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.9) return <CheckCircle className="w-4 h-4 text-green-600" />
    if (confidence >= 0.7) return <AlertTriangle className="w-4 h-4 text-yellow-600" />
    return <AlertTriangle className="w-4 h-4 text-red-600" />
  }

  return (
    <ErrorBoundary>
      <div className={`bg-white rounded-lg shadow ${className}`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Duplicate Detection</h2>
              <p className="text-sm text-gray-500">
                Find and manage duplicate transactions in your data
              </p>
            </div>
            <button
              onClick={handleScan}
              disabled={isScanning}
              className="btn-primary disabled:opacity-50 flex items-center gap-2"
            >
              {isScanning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Scan for Duplicates
                </>
              )}
            </button>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Total Groups:</span>
                <span className="ml-2 font-medium">{stats.total_groups || 0}</span>
              </div>
              <div>
                <span className="text-gray-500">Total Duplicates:</span>
                <span className="ml-2 font-medium">{stats.total_duplicates || 0}</span>
              </div>
              <div>
                <span className="text-gray-500">Merged:</span>
                <span className="ml-2 font-medium">{stats.merged_count || 0}</span>
              </div>
              <div>
                <span className="text-gray-500">Dismissed:</span>
                <span className="ml-2 font-medium">{stats.dismissed_count || 0}</span>
              </div>
            </div>
          </div>
        )}

        {/* Message */}
        {message && (
          <div className="px-6 py-3 bg-blue-50 border-b border-blue-200">
            <p className="text-sm text-blue-800">{message}</p>
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
              <p className="mt-2 text-gray-500">Loading duplicate groups...</p>
            </div>
          ) : duplicateGroups.length === 0 ? (
            <div className="text-center py-8">
              <Search className="w-12 h-12 mx-auto text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No duplicates found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Click "Scan for Duplicates" to find potential duplicates in your data.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {duplicateGroups.map((group) => (
                <div
                  key={group.group_id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  {/* Group Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {getConfidenceIcon(group.confidence_score)}
                      <div>
                        <h3 className="font-medium text-gray-900">
                          Duplicate Group ({group.transactions.length} transactions)
                        </h3>
                        <p className="text-sm text-gray-500">
                          Algorithm: {group.algorithm_used} • 
                          Confidence: <span className={getConfidenceColor(group.confidence_score)}>
                            {(group.confidence_score * 100).toFixed(1)}%
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedGroup(selectedGroup === group.group_id ? null : group.group_id)}
                        className="text-sm text-primary-600 hover:text-primary-700"
                      >
                        {selectedGroup === group.group_id ? 'Hide Details' : 'Show Details'}
                      </button>
                    </div>
                  </div>

                  {/* Transactions */}
                  {selectedGroup === group.group_id && (
                    <div className="space-y-3">
                      {group.transactions.map((transaction) => (
                        <div
                          key={transaction.id}
                          className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded"
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-4">
                              <span className="font-medium text-gray-900">
                                ${transaction.amount.toFixed(2)}
                              </span>
                              <span className="text-gray-700">{transaction.description}</span>
                              <span className="text-gray-500">{transaction.vendor}</span>
                              <span className="text-gray-500">
                                {new Date(transaction.date).toLocaleDateString()}
                              </span>
                            </div>
                            <div className="mt-1 text-sm text-gray-500">
                              {transaction.category} {transaction.subcategory && `• ${transaction.subcategory}`}
                              <span className="ml-2">
                                Similarity: {(transaction.similarity_score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}

                      {/* Merge Suggestions */}
                      {group.merge_suggestions.length > 0 && (
                        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                          <h4 className="font-medium text-blue-900 mb-2">Merge Suggestions</h4>
                          {group.merge_suggestions.map((suggestion, index) => (
                            <div key={index} className="flex items-center justify-between">
                              <div>
                                <span className="text-sm text-blue-800">
                                  Primary: Transaction #{suggestion.primary_transaction_id}
                                </span>
                                <span className="text-sm text-blue-600 ml-2">
                                  Fields: {suggestion.fields_to_merge.join(', ')}
                                </span>
                              </div>
                              <button
                                onClick={() => handleMerge(
                                  group.group_id,
                                  suggestion.primary_transaction_id,
                                  suggestion.fields_to_merge
                                )}
                                className="btn-primary text-sm"
                              >
                                <Merge className="w-4 h-4 mr-1" />
                                Merge
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-200">
                        <button
                          onClick={() => handleDismiss(group.group_id, 'False positive')}
                          className="btn-secondary text-sm"
                        >
                          <X className="w-4 h-4 mr-1" />
                          Dismiss
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  )
}
