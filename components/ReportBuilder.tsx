'use client'

import React, { useState, useEffect } from 'react'
import { 
  FileText, 
  BarChart3, 
  PieChart, 
  TrendingUp, 
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Settings,
  Eye,
  Share2,
  Clock,
  Save
} from 'lucide-react'
import { reportsAPI } from '@/lib/api'

interface ReportTemplate {
  id: string
  name: string
  description: string
  type: string
  icon: string
  category: string
}

interface ReportRequest {
  report_type: 'cash_flow' | 'spending_analysis' | 'vendor_performance' | 'category_breakdown' | 'monthly_summary' | 'quarterly_summary' | 'custom_kpi' | 'categorization_quality'
  start_date?: string
  end_date?: string
  group_by?: 'none' | 'category' | 'subcategory' | 'vendor' | 'month' | 'quarter' | 'year' | 'week'
  filters?: {
    categories?: string[]
    vendors?: string[]
    min_amount?: number
    max_amount?: number
    is_income?: boolean
    is_categorized?: boolean
    description_contains?: string
  }
  aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max'
  export_format?: 'json' | 'csv'
}

interface ReportResponse {
  report_id: string
  report_type: string
  data: any
  generated_at: string
  cache_hit: boolean
}

interface ReportBuilderProps {
  className?: string
}

export default function ReportBuilder({ className = '' }: ReportBuilderProps) {
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null)
  const [reportConfig, setReportConfig] = useState<ReportRequest>({
    report_type: 'cash_flow',
    group_by: 'month',
    aggregation: 'sum'
  })
  const [generatedReport, setGeneratedReport] = useState<ReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'templates' | 'customize' | 'preview'>('templates')

  // Report templates
  const defaultTemplates: ReportTemplate[] = [
    {
      id: 'cash_flow',
      name: 'Cash Flow Analysis',
      description: 'Track income vs expenses over time',
      type: 'cash_flow',
      icon: 'TrendingUp',
      category: 'Financial'
    },
    {
      id: 'spending_analysis',
      name: 'Spending Analysis',
      description: 'Analyze spending patterns by category',
      type: 'spending_analysis',
      icon: 'PieChart',
      category: 'Analytics'
    },
    {
      id: 'vendor_performance',
      name: 'Vendor Performance',
      description: 'Track spending by vendor',
      type: 'vendor_performance',
      icon: 'BarChart3',
      category: 'Business'
    },
    {
      id: 'category_breakdown',
      name: 'Category Breakdown',
      description: 'Detailed category analysis',
      type: 'category_breakdown',
      icon: 'PieChart',
      category: 'Analytics'
    },
    {
      id: 'monthly_summary',
      name: 'Monthly Summary',
      description: 'Monthly financial overview',
      type: 'monthly_summary',
      icon: 'Calendar',
      category: 'Financial'
    },
    {
      id: 'quarterly_summary',
      name: 'Quarterly Summary',
      description: 'Quarterly financial overview',
      type: 'quarterly_summary',
      icon: 'Calendar',
      category: 'Financial'
    },
    {
      id: 'custom_kpi',
      name: 'Custom KPI',
      description: 'Custom key performance indicators',
      type: 'custom_kpi',
      icon: 'BarChart3',
      category: 'Business'
    },
    {
      id: 'categorization_quality',
      name: 'Categorization Quality',
      description: 'AI categorization performance metrics',
      type: 'categorization_quality',
      icon: 'CheckCircle',
      category: 'AI'
    }
  ]

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      setLoading(true)
      const response = await reportsAPI.getTemplates()
      setTemplates(response.data.length > 0 ? response.data : defaultTemplates)
    } catch (err: any) {
      console.error('Failed to fetch templates:', err)
      // Use default templates as fallback
      setTemplates(defaultTemplates)
    } finally {
      setLoading(false)
    }
  }

  // Generate report
  const generateReport = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await reportsAPI.generateReport(reportConfig)
      setGeneratedReport(response.data)
      setActiveTab('preview')
    } catch (err: any) {
      console.error('Failed to generate report:', err)
      setError(err.response?.data?.detail || 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  // Select template
  const selectTemplate = (template: ReportTemplate) => {
    setSelectedTemplate(template)
    setReportConfig(prev => ({
      ...prev,
      report_type: template.type as any
    }))
    setActiveTab('customize')
  }

  useEffect(() => {
    fetchTemplates()
  }, [])

  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'TrendingUp':
        return <TrendingUp className="w-6 h-6" />
      case 'PieChart':
        return <PieChart className="w-6 h-6" />
      case 'BarChart3':
        return <BarChart3 className="w-6 h-6" />
      case 'Calendar':
        return <Calendar className="w-6 h-6" />
      case 'CheckCircle':
        return <CheckCircle className="w-6 h-6" />
      default:
        return <FileText className="w-6 h-6" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Financial':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'Analytics':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'Business':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'AI':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Report Builder</h2>
            <p className="text-sm text-gray-500">Create dynamic financial reports</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchTemplates}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh templates"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center space-x-4">
          <div className={`flex items-center ${activeTab === 'templates' ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              activeTab === 'templates' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              1
            </div>
            <span className="ml-2 text-sm font-medium">Template</span>
          </div>
          <div className={`flex items-center ${activeTab === 'customize' ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              activeTab === 'customize' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              2
            </div>
            <span className="ml-2 text-sm font-medium">Customize</span>
          </div>
          <div className={`flex items-center ${activeTab === 'preview' ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              activeTab === 'preview' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              3
            </div>
            <span className="ml-2 text-sm font-medium">Preview</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'templates' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose a Report Template</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => selectTemplate(template)}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="text-blue-600">
                        {getIconComponent(template.icon)}
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(template.category)}`}>
                        {template.category}
                      </span>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-1">{template.name}</h4>
                    <p className="text-sm text-gray-600">{template.description}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'customize' && selectedTemplate && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Customize Report</h3>
              <button
                onClick={() => setActiveTab('templates')}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                ← Back to Templates
              </button>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center gap-3">
                <div className="text-blue-600">
                  {getIconComponent(selectedTemplate.icon)}
                </div>
                <div>
                  <h4 className="font-semibold text-blue-900">{selectedTemplate.name}</h4>
                  <p className="text-sm text-blue-700">{selectedTemplate.description}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date Range
                </label>
                <div className="space-y-2">
                  <input
                    type="date"
                    value={reportConfig.start_date || ''}
                    onChange={(e) => setReportConfig(prev => ({ 
                      ...prev, 
                      start_date: e.target.value 
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Start date"
                  />
                  <input
                    type="date"
                    value={reportConfig.end_date || ''}
                    onChange={(e) => setReportConfig(prev => ({ 
                      ...prev, 
                      end_date: e.target.value 
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="End date"
                  />
                </div>
              </div>

              {/* Group By */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Group By
                </label>
                <select
                  value={reportConfig.group_by || 'none'}
                  onChange={(e) => setReportConfig(prev => ({ 
                    ...prev, 
                    group_by: e.target.value as any 
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="none">No Grouping</option>
                  <option value="category">Category</option>
                  <option value="subcategory">Subcategory</option>
                  <option value="vendor">Vendor</option>
                  <option value="month">Month</option>
                  <option value="quarter">Quarter</option>
                  <option value="year">Year</option>
                  <option value="week">Week</option>
                </select>
              </div>
            </div>

            {/* Filters */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filters (Optional)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Minimum Amount</label>
                  <input
                    type="number"
                    value={reportConfig.filters?.min_amount || ''}
                    onChange={(e) => setReportConfig(prev => ({ 
                      ...prev, 
                      filters: { 
                        ...prev.filters, 
                        min_amount: e.target.value ? parseFloat(e.target.value) : undefined 
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Maximum Amount</label>
                  <input
                    type="number"
                    value={reportConfig.filters?.max_amount || ''}
                    onChange={(e) => setReportConfig(prev => ({ 
                      ...prev, 
                      filters: { 
                        ...prev.filters, 
                        max_amount: e.target.value ? parseFloat(e.target.value) : undefined 
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="1000.00"
                  />
                </div>
              </div>
            </div>

            {/* Generate Button */}
            <div className="flex justify-end">
              <button
                onClick={generateReport}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 inline mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4 inline mr-2" />
                    Generate Report
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'preview' && generatedReport && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Report Preview</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('customize')}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  ← Back to Customize
                </button>
                <button
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Download className="w-4 h-4 inline mr-2" />
                  Export
                </button>
              </div>
            </div>

            {/* Report Info */}
            <div className="bg-gray-50 p-4 rounded-lg border">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-gray-900">{selectedTemplate?.name}</h4>
                  <p className="text-sm text-gray-600">
                    Generated on {new Date(generatedReport.generated_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {generatedReport.cache_hit && (
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                      Cached
                    </span>
                  )}
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    {generatedReport.report_type}
                  </span>
                </div>
              </div>
            </div>

            {/* Report Data Preview */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-4">Report Data</h4>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="text-sm text-gray-700 overflow-auto max-h-96">
                  {JSON.stringify(generatedReport.data, null, 2)}
                </pre>
              </div>
            </div>

            {/* Report Actions */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="flex items-center gap-4">
                <button className="flex items-center gap-2 text-gray-600 hover:text-gray-800">
                  <Share2 className="w-4 h-4" />
                  <span className="text-sm">Share</span>
                </button>
                <button className="flex items-center gap-2 text-gray-600 hover:text-gray-800">
                  <Save className="w-4 h-4" />
                  <span className="text-sm">Save Template</span>
                </button>
              </div>
              <button
                onClick={() => setActiveTab('templates')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create New Report
              </button>
            </div>
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
