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
    queryFn: () => budgetAnalysisAPI.getBudgets(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Fetch budget summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['budget-summary'],
    queryFn: () => budgetAnalysisAPI.getSummary(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  // Fetch performance metrics
  const { data: performance, isLoading: performanceLoading } = useQuery({
    queryKey: ['budget-performance'],
    queryFn: () => budgetAnalysisAPI.getPerformanceMetrics(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Variance analysis mutation
  const varianceMutation = useMutation({
    mutationFn: (budgetId: number) => 
      budgetAnalysisAPI.getVarianceAnalysis(budgetId),
    onSuccess: (data) => {
      queryClient.setQueryData(['budget-variance', selectedBudget?.id], data)
    },
  })

  // Create budget mutation
  const createBudgetMutation = useMutation({
    mutationFn: (budgetData: any) => budgetAnalysisAPI.createBudget(budgetData),
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
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Budget Analysis</h2>
            <p className="text-gray-600">Comprehensive budget management and analysis</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefresh}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              title="Refresh data"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
            <button
              onClick={() => setIsCreatingBudget(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Budget
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-600">Total Budgeted Income</p>
                  <p className="text-2xl font-bold text-green-900">
                    ${summary.total_budgeted_income?.toLocaleString() || '0'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingDown className="h-8 w-8 text-red-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-600">Total Budgeted Expenses</p>
                  <p className="text-2xl font-bold text-red-900">
                    ${summary.total_budgeted_expenses?.toLocaleString() || '0'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <Target className="h-8 w-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-blue-600">Active Budgets</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {summary.active_budgets || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-purple-600">Overall Variance</p>
                  <p className={`text-2xl font-bold ${
                    (summary.overall_variance_percentage || 0) >= 0 
                      ? 'text-green-900' 
                      : 'text-red-900'
                  }`}>
                    {summary.overall_variance_percentage?.toFixed(1) || '0'}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Budget List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
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
                          ? 'bg-blue-50 border border-blue-200'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">{budget.name}</h4>
                          <p className="text-sm text-gray-600">{budget.budget_type}</p>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          budget.status === 'active' 
                            ? 'bg-green-100 text-green-800'
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
                  <p className="text-gray-500">No budgets created yet</p>
                  <button
                    onClick={() => setIsCreatingBudget(true)}
                    className="mt-2 text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Create your first budget
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Analysis Content */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow">
            {/* Tabs */}
            <div className="border-b border-gray-200">
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
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
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
                            <dd className="font-medium text-green-600">
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
                                ? 'text-green-600'
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
                  {varianceMutation.isLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-gray-500 mt-2">Analyzing variance...</p>
                    </div>
                  ) : varianceMutation.data ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-2">Net Variance</h4>
                          <p className={`text-2xl font-bold ${
                            (varianceMutation.data.net_variance_amount || 0) >= 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}>
                            ${(varianceMutation.data.net_variance_amount || 0).toLocaleString()}
                          </p>
                          <p className="text-sm text-gray-600">
                            {varianceMutation.data.net_variance_percentage?.toFixed(1)}% variance
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-2">Income Variance</h4>
                          <p className={`text-2xl font-bold ${
                            (varianceMutation.data.total_income_actual || 0) >= (varianceMutation.data.total_income_budgeted || 0)
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}>
                            ${((varianceMutation.data.total_income_actual || 0) - (varianceMutation.data.total_income_budgeted || 0)).toLocaleString()}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-2">Expense Variance</h4>
                          <p className={`text-2xl font-bold ${
                            (varianceMutation.data.total_expense_actual || 0) <= (varianceMutation.data.total_expense_budgeted || 0)
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}>
                            ${((varianceMutation.data.total_expense_actual || 0) - (varianceMutation.data.total_expense_budgeted || 0)).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {varianceMutation.data.recommendations && varianceMutation.data.recommendations.length > 0 && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h4 className="font-medium text-blue-900 mb-2">Recommendations</h4>
                          <ul className="space-y-1">
                            {varianceMutation.data.recommendations.map((rec, index) => (
                              <li key={index} className="text-blue-800 text-sm flex items-start">
                                <CheckCircle className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                                {rec}
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
                            <dd className="font-medium">{(performance.accuracy_score * 100).toFixed(1)}%</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Budget Adherence:</dt>
                            <dd className="font-medium">{(performance.budget_adherence_rate * 100).toFixed(1)}%</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Variance Stability:</dt>
                            <dd className="font-medium">{(performance.variance_stability * 100).toFixed(1)}%</dd>
                          </div>
                        </dl>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">Engagement & Trends</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">User Engagement:</dt>
                            <dd className="font-medium">{(performance.user_engagement_score * 100).toFixed(1)}%</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Forecast Improvement:</dt>
                            <dd className="font-medium">{(performance.forecasting_improvement * 100).toFixed(1)}%</dd>
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
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
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
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="annual">Annual</option>
                    <option value="project">Project-based</option>
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
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createBudgetMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
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
