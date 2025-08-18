'use client'

import React from 'react'
import { CheckCircle, AlertCircle, Loader2, Wifi, WifiOff, RotateCcw, Shield, FileText, Database, Tag, Search } from 'lucide-react'
import { ProgressMessage } from '@/hooks/useWebSocket'

interface UploadProgressProps {
  isConnected: boolean
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error'
  progress: number
  status: string
  stage: string
  message: string
  details?: any
  error?: string | null
  onReconnect?: () => void
  className?: string
}

export function UploadProgress({
  isConnected,
  connectionState,
  progress,
  status,
  stage,
  message,
  details,
  error,
  onReconnect,
  className = ''
}: UploadProgressProps) {
  // Stage configuration
  const stageConfig = {
    initialization: {
      icon: Loader2,
      label: 'Initializing',
      color: 'text-blue-500',
      bgColor: 'bg-blue-50 border-blue-200'
    },
    validation: {
      icon: Shield,
      label: 'Validating File',
      color: 'text-orange-500',
      bgColor: 'bg-orange-50 border-orange-200'
    },
    scanning: {
      icon: Search,
      label: 'Security Scanning',
      color: 'text-red-500',
      bgColor: 'bg-red-50 border-red-200'
    },
    parsing: {
      icon: FileText,
      label: 'Parsing Data',
      color: 'text-purple-500',
      bgColor: 'bg-purple-50 border-purple-200'
    },
    database: {
      icon: Database,
      label: 'Saving Transactions',
      color: 'text-green-500',
      bgColor: 'bg-green-50 border-green-200'
    },
    categorization: {
      icon: Tag,
      label: 'Categorizing',
      color: 'text-indigo-500',
      bgColor: 'bg-indigo-50 border-indigo-200'
    }
  }

  const currentStage = stageConfig[stage as keyof typeof stageConfig] || stageConfig.initialization
  const StageIcon = currentStage.icon

  // Progress bar color based on status
  const getProgressBarColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      case 'connected':
      case 'processing':
        return 'bg-blue-500'
      default:
        return 'bg-gray-400'
    }
  }

  // Connection status indicator
  const ConnectionStatus = () => {
    switch (connectionState) {
      case 'connecting':
        return (
          <div className="flex items-center gap-2 text-orange-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Connecting...</span>
          </div>
        )
      case 'connected':
        return (
          <div className="flex items-center gap-2 text-green-600">
            <Wifi className="w-4 h-4" />
            <span className="text-sm">Connected</span>
          </div>
        )
      case 'disconnected':
        return (
          <div className="flex items-center gap-2 text-gray-600">
            <WifiOff className="w-4 h-4" />
            <span className="text-sm">Disconnected</span>
            {onReconnect && (
              <button
                onClick={onReconnect}
                className="text-blue-600 hover:text-blue-700 ml-2"
                title="Reconnect"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        )
      case 'error':
        return (
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">Connection Error</span>
            {onReconnect && (
              <button
                onClick={onReconnect}
                className="text-blue-600 hover:text-blue-700 ml-2"
                title="Retry connection"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      {/* Header with connection status */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Upload Progress</h3>
        <ConnectionStatus />
      </div>

      {/* Current stage indicator */}
      <div className={`rounded-lg p-4 border ${currentStage.bgColor} mb-4`}>
        <div className="flex items-center gap-3">
          <div className={`${currentStage.color}`}>
            <StageIcon className={`w-5 h-5 ${status === 'processing' && stage !== 'initialization' ? 'animate-pulse' : ''}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className={`font-medium ${currentStage.color}`}>
                {currentStage.label}
              </span>
              <span className="text-sm font-medium text-gray-700">
                {Math.round(progress)}%
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{message}</p>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ease-out ${getProgressBarColor()}`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      </div>

      {/* Status message */}
      {status === 'completed' && (
        <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
          <CheckCircle className="w-5 h-5" />
          <span className="font-medium">Upload completed successfully!</span>
        </div>
      )}

      {status === 'error' && error && (
        <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <AlertCircle className="w-5 h-5" />
          <div>
            <p className="font-medium">Upload failed</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Details section */}
      {details && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Details</h4>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {details.filename && (
                <div>
                  <span className="text-gray-500">Filename:</span>
                  <span className="ml-2 font-medium">{details.filename}</span>
                </div>
              )}
              {details.size && (
                <div>
                  <span className="text-gray-500">Size:</span>
                  <span className="ml-2 font-medium">{formatFileSize(details.size)}</span>
                </div>
              )}
              {details.processed !== undefined && details.total !== undefined && (
                <div>
                  <span className="text-gray-500">Processed:</span>
                  <span className="ml-2 font-medium">{details.processed} / {details.total}</span>
                </div>
              )}
              {details.errors !== undefined && details.errors > 0 && (
                <div>
                  <span className="text-gray-500">Errors:</span>
                  <span className="ml-2 font-medium text-red-600">{details.errors}</span>
                </div>
              )}
              {details.threat_level && (
                <div>
                  <span className="text-gray-500">Security:</span>
                  <span className={`ml-2 font-medium ${getThreatLevelColor(details.threat_level)}`}>
                    {details.threat_level}
                  </span>
                </div>
              )}
              {details.categorized_count !== undefined && (
                <div>
                  <span className="text-gray-500">Categorized:</span>
                  <span className="ml-2 font-medium">{details.categorized_count}</span>
                </div>
              )}
              {details.categorization_rate !== undefined && (
                <div>
                  <span className="text-gray-500">Category Rate:</span>
                  <span className="ml-2 font-medium">{details.categorization_rate}%</span>
                </div>
              )}
              {details.overall_success_rate !== undefined && (
                <div>
                  <span className="text-gray-500">Success Rate:</span>
                  <span className="ml-2 font-medium text-green-600">{details.overall_success_rate}%</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Stage progress indicators */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Process Stages</h4>
        <div className="space-y-2">
          {Object.entries(stageConfig).map(([stageKey, config], index) => {
            const StageIconComp = config.icon
            const isCurrentStage = stage === stageKey
            const isCompletedStage = getStageProgress(stageKey) <= progress
            const isPendingStage = !isCompletedStage && !isCurrentStage

            return (
              <div
                key={stageKey}
                className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                  isCurrentStage ? config.bgColor : 
                  isCompletedStage ? 'bg-green-50 border border-green-200' :
                  'bg-gray-50'
                }`}
              >
                <div className={`
                  ${isCurrentStage ? config.color :
                    isCompletedStage ? 'text-green-500' :
                    'text-gray-400'}
                `}>
                  {isCompletedStage && !isCurrentStage ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    <StageIconComp className={`w-4 h-4 ${isCurrentStage && status === 'processing' ? 'animate-pulse' : ''}`} />
                  )}
                </div>
                <span className={`text-sm font-medium ${
                  isCurrentStage ? config.color.replace('text-', 'text-') :
                  isCompletedStage ? 'text-green-700' :
                  'text-gray-500'
                }`}>
                  {config.label}
                </span>
                {isCurrentStage && (
                  <div className="ml-auto">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  </div>
                )}
                {isCompletedStage && !isCurrentStage && (
                  <div className="ml-auto">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// Helper functions
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function getThreatLevelColor(threatLevel: string): string {
  switch (threatLevel.toLowerCase()) {
    case 'low':
      return 'text-green-600'
    case 'medium':
      return 'text-yellow-600'
    case 'high':
      return 'text-orange-600'
    case 'critical':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

function getStageProgress(stage: string): number {
  const stageProgressMap: Record<string, number> = {
    'initialization': 5,
    'validation': 20,
    'scanning': 40,
    'parsing': 60,
    'database': 80,
    'categorization': 100
  }
  return stageProgressMap[stage] || 0
}

export default UploadProgress