'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  TrendingUp, 
  Calendar, 
  BarChart3, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  Settings,
  Download,
  Eye,
  EyeOff,
  DollarSign,
  PieChart,
  AlertCircle,
  TrendingDown,
  Plus,
  Edit,
  Trash2,
  Filter
} from 'lucide-react'
import { budgetAnalysisAPI } from '@/lib/api'
import type { 
  Budget,
  BudgetVarianceAnalysis,
  BudgetRecommendation,
  BudgetScenario,
  BudgetAlertTrigger,
  BudgetPerformanceMetrics,
  BudgetAnalysisSummary
} from '@/types/api'

interface BudgetAnalysisProps {
  className?: string
}

export function BudgetAnalysis({ className = '' }: BudgetAnalysisProps) {
  const [selectedBudget, setSelectedBudget] = useState<string>('')
  const [showCreateBudget, setShowCreateBudget] = useState<boolean>(false)
  const [showScenarios, setShowScenarios] = useState<boolean>(false)
  const [showAlerts, setShowAlerts] = useState<boolean>(false)
  const [filterStatus, setFilterStatus] = useState<string>('all')

  const queryClient = useQueryClient()

  // Fetch budget list
  const { data: budgets, isLoading: budgetsLoading, error: budgetsError } = useQuery({
    queryKey: ['budgets', filterStatus],
    queryFn: () => budgetAnalysisAPI.getBudgets({ status: filterStatus === 'all' ? undefined : filterStatus }),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Fetch budget analysis summary
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['budget-summary'],
    queryFn: () => budgetAnalysisAPI.getSummary(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Fetch selected budget details
  const { data: budgetDetails, isLoading: detailsLoading, error: detailsError } = useQuery({
    queryKey: ['budget-details', selectedBudget],
    queryFn: () => budgetAnalysisAPI.getBudget(selectedBudget),
    enabled: !!selectedBudget,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Fetch budget variance analysis
  const { data: varianceAnalysis, isLoading: varianceLoading, error: varianceError } = useQuery({
    queryKey: ['budget-variance', selectedBudget],
    queryFn: () => budgetAnalysisAPI.getVarianceAnalysis(selectedBudget),
    enabled: !!selectedBudget,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Fetch budget recommendations
  const { data: recommendations, isLoading: recommendationsLoading, error: recommendationsError } = useQuery({
    queryKey: ['budget-recommendations', selectedBudget],
    queryFn: () => budgetAnalysisAPI.getRecommendations(selectedBudget),
    enabled: !!selectedBudget,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    retryDelay: 1000,
  })

  // Apply recommendation mutation
  const applyRecommendationMutation = useMutation({
    mutationFn: ({ budgetId, recommendationId }: { budgetId: string; recommendationId: string }) =>
      budgetAnalysisAPI.applyRecommendation(budgetId, recommendationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget-recommendations', selectedBudget] })
      queryClient.invalidateQueries({ queryKey: ['budget-variance', selectedBudget] })
    },
  })

  const handleApplyRecommendation = (recommendationId: string) => {
    if (selectedBudget) {
      applyRecommendationMutation.mutate({ budgetId: selectedBudget, recommendationId })
    }
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['budgets'] })
    queryClient.invalidateQueries({ queryKey: ['budget-summary'] })
    if (selectedBudget) {
      queryClient.invalidateQueries({ queryKey: ['budget-details', selectedBudget] })
      queryClient.invalidateQueries({ queryKey: ['budget-variance', selectedBudget] })
      queryClient.invalidateQueries({ queryKey: ['budget-recommendations', selectedBudget] })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'under_budget': return 'text-green-600'
      case 'on_budget': return 'text-blue-600'
      case 'over_budget': return 'text-yellow-600'
      case 'critical': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'under_budget': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'on_budget': return <Target className="w-4 h-4 text-blue-600" />
      case 'over_budget': return <AlertTriangle className="w-4 h-4 text-yellow-600" />
      case 'critical': return <AlertCircle className="w-4 h-4 text-red-600" />
      default: return <Clock className="w-4 h-4 text-gray-600" />
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-blue-600" />
            Budget Analysis Dashboard
          </h2>
          <p className="text-gray-600 mt-1">
            Comprehensive budget vs actual analysis with AI-powered recommendations
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {summaryLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-8 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Total Budgets</p>
                <p className="text-2xl font-bold text-blue-900">{summary.total_budgets}</p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Active Budgets</p>
                <p className="text-2xl font-bold text-green-900">{summary.active_budgets}</p>
              </div>
              <Target className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-600 font-medium">Critical Alerts</p>
                <p className="text-2xl font-bold text-yellow-900">{summary.critical_alerts}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-600" />
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600 font-medium">Pending Recommendations</p>
                <p className="text-2xl font-bold text-purple-900">{summary.pending_recommendations}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
          </div>
        </div>
      ) : null}

      {/* Budget Selection and Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1">
          <label htmlFor="budget-select" className="block text-sm font-medium text-gray-700 mb-2">
            Select Budget
          </label>
          <select
            id="budget-select"
            value={selectedBudget}
            onChange={(e) => setSelectedBudget(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Choose a budget...</option>
            {budgets?.budgets?.map((budget) => (
              <option key={budget.budget_id} value={budget.budget_id}>
                {budget.name} - {budget.period_type}
              </option>
            )) || (
              <>
                <option value="demo-budget-1">Demo Budget 1 - Monthly</option>
                <option value="demo-budget-2">Demo Budget 2 - Quarterly</option>
                <option value="demo-budget-3">Demo Budget 3 - Yearly</option>
              </>
            )}
          </select>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateBudget(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Budget
          </button>
          <button
            onClick={() => setShowScenarios(!showScenarios)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            <BarChart3 className="w-4 h-4" />
            Scenarios
          </button>
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            Alerts
          </button>
        </div>
      </div>

      {/* Budget Details */}
      {selectedBudget && budgetDetails ? (
        <div className="space-y-6">
          {/* Budget Overview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Budget</p>
                <p className="text-xl font-bold text-gray-900">
                  ${budgetDetails.budget.total_budget.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Period</p>
                <p className="text-xl font-bold text-gray-900">
                  {budgetDetails.budget.period_type}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <div className="flex items-center gap-2">
                  {getStatusIcon(budgetDetails.budget.status)}
                  <span className="text-xl font-bold capitalize">{budgetDetails.budget.status}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Variance Analysis */}
          {varianceAnalysis && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Variance Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Total Actual</p>
                  <p className="text-xl font-bold text-gray-900">
                    ${varianceAnalysis.variance_analysis.total_actual.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Variance</p>
                  <p className={`text-xl font-bold ${varianceAnalysis.variance_analysis.total_variance >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    ${Math.abs(varianceAnalysis.variance_analysis.total_variance).toLocaleString()}
                    {varianceAnalysis.variance_analysis.total_variance >= 0 ? ' Over' : ' Under'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Variance %</p>
                  <p className={`text-xl font-bold ${varianceAnalysis.variance_analysis.variance_percentage >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {Math.abs(varianceAnalysis.variance_analysis.variance_percentage).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Overall Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(varianceAnalysis.variance_analysis.overall_status)}
                    <span className="text-xl font-bold capitalize">{varianceAnalysis.variance_analysis.overall_status.replace('_', ' ')}</span>
                  </div>
                </div>
              </div>

              {/* Category Breakdown */}
              <div className="mt-6">
                <h4 className="text-md font-semibold text-gray-900 mb-3">Category Breakdown</h4>
                <div className="space-y-2">
                  {varianceAnalysis.variance_analysis.category_breakdown?.map((category) => (
                    <div key={category.category} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-3">
                        <PieChart className="w-4 h-4 text-gray-600" />
                        <div>
                          <p className="font-medium text-gray-900">{category.category}</p>
                          <p className="text-sm text-gray-600">
                            ${category.allocated_amount.toLocaleString()} allocated
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">
                          ${category.actual_amount.toLocaleString()}
                        </p>
                        <p className={`text-sm ${getStatusColor(category.status)}`}>
                          {category.variance_percentage >= 0 ? '+' : ''}{category.variance_percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* AI Recommendations */}
          {recommendations && recommendations.recommendations.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Recommendations</h3>
              <div className="space-y-4">
                {recommendations.recommendations.slice(0, 5).map((recommendation) => (
                  <div key={recommendation.recommendation_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingUp className="w-4 h-4 text-blue-600" />
                          <span className="font-medium text-gray-900 capitalize">
                            {recommendation.recommendation_type.replace('_', ' ')}
                          </span>
                          {recommendation.category && (
                            <span className="text-sm text-gray-600">({recommendation.category})</span>
                          )}
                        </div>
                        <p className="text-gray-700 mb-2">{recommendation.reasoning}</p>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span>Confidence: {Math.round(recommendation.confidence_score * 100)}%</span>
                          <span>Risk: {recommendation.impact_analysis.risk_level}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleApplyRecommendation(recommendation.recommendation_id)}
                        disabled={recommendation.applied || applyRecommendationMutation.isPending}
                        className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {recommendation.applied ? 'Applied' : 'Apply'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          {budgetDetails.performance_metrics && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Accuracy Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(budgetDetails.performance_metrics.accuracy_score * 100)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Adherence Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(budgetDetails.performance_metrics.adherence_rate * 100)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Forecast Accuracy</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(budgetDetails.performance_metrics.forecast_accuracy * 100)}%
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : selectedBudget ? (
        <div className="text-center py-8">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Loading budget details...</p>
        </div>
      ) : (
        <div className="text-center py-8">
          <DollarSign className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Select a budget to view analysis</p>
        </div>
      )}

      {/* Error Display */}
      {(budgetsError || summaryError || detailsError || varianceError || recommendationsError) && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <p className="text-red-800 font-medium">Error loading budget data</p>
          </div>
          <p className="text-red-700 text-sm mt-1">
            Please check your connection and try refreshing the page.
          </p>
        </div>
      )}
    </div>
  )
}
