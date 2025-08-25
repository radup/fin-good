'use client'

import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  DollarSign,
  Calendar,
  BarChart3,
  PieChart,
  Settings,
  RefreshCw,
  Download,
  Eye,
  Edit,
  Trash2,
  Filter,
  Search,
  MoreHorizontal
} from 'lucide-react'
import { budgetAnalysisAPI } from '@/lib/api'
import { 
  cardClasses, buttonClasses, badgeClasses, 
  cn, gradientClasses, textClasses,
  headerClasses, headerTitleClasses, headerDescClasses 
} from '@/lib/design-utils'
import type { 
  Budget, 
  BudgetVarianceAnalysis, 
  BudgetRecommendation, 
  BudgetScenario,
  BudgetPerformanceMetrics,
  BudgetAnalysisSummary 
} from '@/types/api'

interface BudgetAnalysisProps {
  className?: string
}

export function BudgetAnalysis({ className = '' }: BudgetAnalysisProps) {
  const queryClient = useQueryClient()
  const [selectedBudget, setSelectedBudget] = useState<Budget | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'variance' | 'forecast' | 'performance'>('overview')
  const [isCreatingBudget, setIsCreatingBudget] = useState(false)

  // Fetch budgets
  const { data: budgets, isLoading: budgetsLoading, error: budgetsError } = useQuery({
    queryKey: ['budgets'],
    queryFn: async () => {
      const response = await budgetAnalysisAPI.getBudgets()
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Debug logging
  console.log('BudgetAnalysis Debug:', { 
    budgets, 
    budgetsLoading, 
    budgetsError,
    budgetsLength: budgets?.length 
  })

  // Fetch budget summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['budget-summary'],
    queryFn: async () => {
      const response = await budgetAnalysisAPI.getSummary()
      return response.data
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  // Fetch performance metrics
  const { data: performance, isLoading: performanceLoading } = useQuery({
    queryKey: ['budget-performance', selectedBudget?.id],
    queryFn: async () => {
      if (!selectedBudget) return null
      const response = await budgetAnalysisAPI.getPerformance(selectedBudget.id.toString())
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!selectedBudget
  })

  // Variance analysis mutation
  const varianceMutation = useMutation({
    mutationFn: async (budgetId: number) => {
      const response = await budgetAnalysisAPI.getVarianceAnalysis(budgetId.toString())
      return response.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['budget-variance', selectedBudget?.id], data)
    },
  })

  // Create budget mutation
  const createBudgetMutation = useMutation({
    mutationFn: async (budgetData: any) => {
      const response = await budgetAnalysisAPI.createBudget(budgetData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['budget-summary'] })
      setIsCreatingBudget(false)
    },
  })

  // Refresh data
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['budgets'] })
    queryClient.invalidateQueries({ queryKey: ['budget-summary'] })
    queryClient.invalidateQueries({ queryKey: ['budget-performance'] })
  }

  // Handle budget selection
  const handleBudgetSelect = (budget: Budget) => {
    setSelectedBudget(budget)
    varianceMutation.mutate(budget.id)
  }

  // Handle create budget
  const handleCreateBudget = (budgetData: any) => {
    createBudgetMutation.mutate(budgetData)
  }

  if (budgetsLoading || summaryLoading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (budgetsError) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
          <h3 className="text-red-800 font-medium">Error Loading Budget Data</h3>
        </div>
        <p className="text-red-600 mt-2">
          Unable to load budget information. Please try refreshing the page.
        </p>
        <button
          onClick={handleRefresh}
          className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
        >
          <RefreshCw className="h-4 w-4 inline mr-2" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className={headerClasses('clean')}>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-brand-primary/10 border border-brand-primary/20 rounded-2xl flex items-center justify-center">
            <PieChart className="w-6 h-6 text-brand-primary" />
          </div>
          <div>
            <h2 className={headerTitleClasses('2xl')}>
              Budget Analysis & Management
            </h2>
            <p className={headerDescClasses('default')}>
              Comprehensive budget planning with AI-powered variance analysis
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
              onClick={handleRefresh}
              className={cn(
                buttonClasses('secondary', 'sm')
              )}
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={() => setIsCreatingBudget(true)}
              className={cn(
                buttonClasses('primary', 'sm')
              )}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Budget
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-emerald-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-emerald-600">Active Budgets</p>
                <p className="text-2xl font-bold text-emerald-900">
                  {summary.active_budgets}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center">
              <TrendingDown className="h-8 w-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-600">Critical Alerts</p>
                <p className="text-2xl font-bold text-red-700">
                  {summary.critical_alerts}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-cyan-50 border border-cyan-200 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center">
              <Target className="h-8 w-8" style={{color: '#00A8CC'}} />
              <div className="ml-3">
                <p className="text-sm font-medium" style={{color: '#006B7D'}}>Total Budgets</p>
                <p className="text-2xl font-bold" style={{color: '#031d24'}}>
                  {summary.active_budgets || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-violet-50 border border-violet-200 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-violet-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-violet-600">Average Variance</p>
                <p className={`text-2xl font-bold ${
                  (summary.average_variance || 0) >= 0 
                    ? 'text-emerald-700' 
                    : 'text-red-700'
                }`}>
                  {summary.average_variance?.toFixed(1) || '0'}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Budget List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
            <div className="p-4 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900">Budgets</h3>
            </div>
            <div className="p-4">
              {budgets && budgets.length > 0 ? (
                <div className="space-y-2">
                  {budgets.map((budget) => (
                    <div
                      key={budget.id}
                      onClick={() => handleBudgetSelect(budget)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedBudget?.id === budget.id
                          ? 'bg-cyan-50 border border-cyan-200'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      style={selectedBudget?.id === budget.id ? {
                        backgroundColor: '#E6F7FF',
                        borderColor: '#00A8CC'
                      } : {}}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">{budget.name}</h4>
                          <p className="text-sm text-gray-600">{budget.budget_type}</p>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          budget.status === 'ACTIVE' 
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {budget.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No budgets created yet</p>
                  <button
                    onClick={() => setIsCreatingBudget(true)}
                    className={cn(buttonClasses('gradient', 'sm'))}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create your first budget
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Analysis Content */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
            {/* Tabs */}
            <div className="border-b border-gray-100">
              <nav className="flex space-x-8 px-6">
                {[
                  { id: 'overview', label: 'Overview', icon: Eye },
                  { id: 'variance', label: 'Variance Analysis', icon: TrendingUp },
                  { id: 'forecast', label: 'Forecasting', icon: BarChart3 },
                  { id: 'performance', label: 'Performance', icon: PieChart },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'text-gray-900'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    style={activeTab === tab.id ? {
                      borderBottomColor: '#00A8CC',
                      color: '#031d24'
                    } : {}}
                  >
                    <tab.icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-gray-900">Budget Overview</h3>
                  {selectedBudget ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3">Budget Details</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Name:</dt>
                            <dd className="font-medium">{selectedBudget.name}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Type:</dt>
                            <dd className="font-medium">{selectedBudget.budget_type}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Status:</dt>
                            <dd className="font-medium">{selectedBudget.status}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Period:</dt>
                            <dd className="font-medium">
                              {new Date(selectedBudget.start_date).toLocaleDateString()} - 
                              {new Date(selectedBudget.end_date).toLocaleDateString()}
                            </dd>
                          </div>
                        </dl>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3">Financial Summary</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Budgeted Income:</dt>
                            <dd className="font-medium text-emerald-600">
                              ${selectedBudget.total_income_budget?.toLocaleString()}
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Budgeted Expenses:</dt>
                            <dd className="font-medium text-red-600">
                              ${selectedBudget.total_expense_budget?.toLocaleString()}
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Net Budget:</dt>
                            <dd className={`font-medium ${
                              (selectedBudget.total_income_budget || 0) - (selectedBudget.total_expense_budget || 0) >= 0
                                ? 'text-emerald-600'
                                : 'text-red-600'
                            }`}>
                              ${((selectedBudget.total_income_budget || 0) - (selectedBudget.total_expense_budget || 0)).toLocaleString()}
                            </dd>
                          </div>
                        </dl>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Select a budget to view details</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'variance' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-gray-900">Variance Analysis</h3>
                  {varianceMutation.isPending ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-gray-500 mt-2">Analyzing variance...</p>
                    </div>
                  ) : varianceMutation.data ? (
                    <div className="space-y-4">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h4 className="font-medium text-blue-900 mb-2">Variance Analysis Available</h4>
                        <p className="text-blue-800 text-sm">
                          Variance analysis data has been loaded successfully. The analysis includes category details, alerts, and recommendations.
                        </p>
                      </div>

                      {varianceMutation.data.recommendations && varianceMutation.data.recommendations.length > 0 && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h4 className="font-medium text-green-900 mb-2">Recommendations</h4>
                          <ul className="space-y-1">
                            {varianceMutation.data.recommendations.map((rec, index) => (
                              <li key={index} className="text-green-800 text-sm flex items-start">
                                <CheckCircle className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                                {rec.reasoning || `Recommendation ${index + 1}`}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Select a budget to analyze variance</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'forecast' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-gray-900">Budget Forecasting</h3>
                  <div className="text-center py-8">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Forecasting features coming soon</p>
                  </div>
                </div>
              )}

              {activeTab === 'performance' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-gray-900">Performance Metrics</h3>
                  {performanceLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-gray-500 mt-2">Loading performance data...</p>
                    </div>
                  ) : performance ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">Accuracy Metrics</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Overall Accuracy:</dt>
                            <dd className="font-medium">{(performance.performance_metrics.accuracy_score * 100).toFixed(1)}%</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Budget Adherence:</dt>
                            <dd className="font-medium">{(performance.performance_metrics.adherence_rate * 100).toFixed(1)}%</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Forecast Accuracy:</dt>
                            <dd className="font-medium">{(performance.performance_metrics.forecast_accuracy * 100).toFixed(1)}%</dd>
                          </div>
                        </dl>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">Trend Analysis</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Accuracy Trend:</dt>
                            <dd className="font-medium capitalize">{performance.trend_analysis.accuracy_trend}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Adherence Trend:</dt>
                            <dd className="font-medium capitalize">{performance.trend_analysis.adherence_trend}</dd>
                          </div>
                        </dl>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">No performance data available</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Budget Modal */}
      {isCreatingBudget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Budget</h3>
            <form onSubmit={(e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              handleCreateBudget({
                name: formData.get('name'),
                description: formData.get('description'),
                budget_type: formData.get('budget_type'),
                start_date: formData.get('start_date'),
                end_date: formData.get('end_date'),
              })
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Budget Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Monthly Budget 2024"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Optional description"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Budget Type
                  </label>
                  <select
                    name="budget_type"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="MONTHLY">Monthly</option>
                    <option value="QUARTERLY">Quarterly</option>
                    <option value="ANNUAL">Annual</option>
                    <option value="PROJECT">Project-based</option>
                    <option value="GOAL_BASED">Goal-based</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      name="start_date"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      name="end_date"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setIsCreatingBudget(false)}
                  className={buttonClasses('secondary', 'base')}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createBudgetMutation.isPending}
                  className={`${buttonClasses('gradient', 'base')} disabled:opacity-50`}
                >
                  {createBudgetMutation.isPending ? 'Creating...' : 'Create Budget'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
