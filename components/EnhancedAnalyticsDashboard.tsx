'use client'

import React, { useState, useEffect } from 'react'
import { 
  BarChart3,
  TrendingUp,
  Brain,
  Target,
  Activity,
  Zap,
  CheckCircle,
  AlertTriangle,
  Eye,
  Settings,
  Layers,
  PieChart,
  LineChart,
  Award,
  Filter,
  Search,
  Download,
  RefreshCw,
  Clock,
  DollarSign,
  Percent,
  ArrowUp,
  ArrowDown,
  ArrowRight,
  Info,
  Lightbulb
} from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

// Mock data for enhanced analytics
const mockCategorizedTransactions = [
  {
    id: 'txn_001',
    description: 'Office supplies from Staples',
    amount: 145.67,
    date: '2024-08-15',
    predictedCategory: 'Office Supplies',
    confidence: 0.94,
    finbertScore: 0.92,
    alternativeCategories: [
      { category: 'Equipment', confidence: 0.74 },
      { category: 'General Business', confidence: 0.68 }
    ],
    modelExplanation: 'High confidence: "supplies" and "office" are strong indicators',
    manualOverride: false,
    vendor: 'Staples Inc.'
  },
  {
    id: 'txn_002',
    description: 'Lunch meeting with client - Restaurant Le Bernardin',
    amount: 89.50,
    date: '2024-08-14',
    predictedCategory: 'Meals & Entertainment',
    confidence: 0.87,
    finbertScore: 0.89,
    alternativeCategories: [
      { category: 'Travel', confidence: 0.45 },
      { category: 'General Business', confidence: 0.32 }
    ],
    modelExplanation: 'Medium-high confidence: "lunch" and "restaurant" suggest meals category',
    manualOverride: false,
    vendor: 'Le Bernardin'
  },
  {
    id: 'txn_003',
    description: 'AWS cloud hosting services monthly',
    amount: 234.12,
    date: '2024-08-13',
    predictedCategory: 'Software & Technology',
    confidence: 0.96,
    finbertScore: 0.95,
    alternativeCategories: [
      { category: 'Utilities', confidence: 0.78 },
      { category: 'Professional Services', confidence: 0.54 }
    ],
    modelExplanation: 'Very high confidence: "AWS" and "cloud hosting" are strong tech indicators',
    manualOverride: false,
    vendor: 'Amazon Web Services'
  },
  {
    id: 'txn_004',
    description: 'Payment to John Smith for consulting',
    amount: 1250.00,
    date: '2024-08-12',
    predictedCategory: 'Professional Services',
    confidence: 0.73,
    finbertScore: 0.71,
    alternativeCategories: [
      { category: 'Contractor Payments', confidence: 0.69 },
      { category: 'General Business', confidence: 0.52 }
    ],
    modelExplanation: 'Medium confidence: "consulting" suggests professional services, but individual name creates ambiguity',
    manualOverride: false,
    vendor: 'John Smith Consulting'
  },
  {
    id: 'txn_005',
    description: 'Coffee beans for office kitchen',
    amount: 45.30,
    date: '2024-08-11',
    predictedCategory: 'Office Supplies',
    confidence: 0.65,
    finbertScore: 0.63,
    alternativeCategories: [
      { category: 'Meals & Entertainment', confidence: 0.58 },
      { category: 'General Business', confidence: 0.41 }
    ],
    modelExplanation: 'Lower confidence: "coffee" could be meals or office supplies depending on context',
    manualOverride: false,
    vendor: 'Blue Bottle Coffee'
  }
]

const modelPerformanceData = {
  overall: {
    accuracy: 94.2,
    precision: 91.8,
    recall: 89.5,
    f1Score: 90.6,
    totalTransactions: 12847,
    correctPredictions: 12104,
    humanOverrides: 743
  },
  byCategory: [
    { category: 'Software & Technology', accuracy: 97.1, transactions: 2340, avgConfidence: 0.92 },
    { category: 'Office Supplies', accuracy: 93.8, transactions: 1890, avgConfidence: 0.87 },
    { category: 'Professional Services', accuracy: 89.2, transactions: 1560, avgConfidence: 0.81 },
    { category: 'Meals & Entertainment', accuracy: 91.5, transactions: 1200, avgConfidence: 0.83 },
    { category: 'Travel', accuracy: 95.3, transactions: 980, avgConfidence: 0.89 },
    { category: 'Marketing', accuracy: 88.7, transactions: 760, avgConfidence: 0.79 },
    { category: 'Utilities', accuracy: 96.8, transactions: 680, avgConfidence: 0.94 },
    { category: 'Equipment', accuracy: 92.4, transactions: 520, avgConfidence: 0.85 }
  ],
  confidenceDistribution: {
    high: { range: '90-100%', count: 8945, percentage: 69.6 },
    medium: { range: '70-89%', count: 2834, percentage: 22.1 },
    low: { range: '50-69%', count: 1068, percentage: 8.3 }
  }
}

export default function EnhancedAnalyticsDashboard() {
  const [selectedTab, setSelectedTab] = useState<'categorization' | 'intelligence' | 'performance'>('categorization')
  const [filterConfidence, setFilterConfidence] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTransaction, setSelectedTransaction] = useState<string | null>(null)

  const filteredTransactions = mockCategorizedTransactions.filter(txn => {
    const matchesSearch = txn.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         txn.vendor.toLowerCase().includes(searchTerm.toLowerCase())
    
    let matchesFilter = true
    if (filterConfidence !== 'all') {
      if (filterConfidence === 'high' && txn.confidence < 0.9) matchesFilter = false
      if (filterConfidence === 'medium' && (txn.confidence < 0.7 || txn.confidence >= 0.9)) matchesFilter = false
      if (filterConfidence === 'low' && txn.confidence >= 0.7) matchesFilter = false
    }
    
    return matchesSearch && matchesFilter
  })

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-100'
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'High'
    if (confidence >= 0.7) return 'Medium'
    return 'Low'
  }

  const CategorizationView = () => (
    <div className="space-y-6">
      {/* Model Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overall Accuracy</p>
              <p className="text-2xl font-bold text-green-600">{modelPerformanceData.overall.accuracy}%</p>
              <p className="text-xs text-gray-500 mt-1">FinBERT Enhanced</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Transactions Processed</p>
              <p className="text-2xl font-bold text-blue-600">{modelPerformanceData.overall.totalTransactions.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">This month</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Auto-Categorized</p>
              <p className="text-2xl font-bold text-purple-600">{Math.round((modelPerformanceData.overall.correctPredictions / modelPerformanceData.overall.totalTransactions) * 100)}%</p>
              <p className="text-xs text-gray-500 mt-1">No manual review needed</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Zap className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Human Overrides</p>
              <p className="text-2xl font-bold text-orange-600">{modelPerformanceData.overall.humanOverrides}</p>
              <p className="text-xs text-gray-500 mt-1">{Math.round((modelPerformanceData.overall.humanOverrides / modelPerformanceData.overall.totalTransactions) * 100)}% of total</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Eye className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Dr. Sigmund AI Insights */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
        <div className="flex items-start space-x-4">
          <DrSigmundSpendAvatar size="sm" mood="analytical" />
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-lg font-semibold text-blue-900">FinBERT Categorization Insights</h3>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">ML Analysis</span>
            </div>
            <div className="space-y-3 text-sm text-blue-800">
              <p>
                Your expense categorization is performing exceptionally well at <strong>94.2% accuracy</strong>. 
                The FinBERT model is particularly strong with technology and utility expenses.
              </p>
              <p>
                <strong>Areas for improvement:</strong> Professional services and consulting payments show lower confidence. 
                Consider adding more context in transaction descriptions for better classification.
              </p>
              <div className="bg-white/60 rounded-lg p-3 mt-3">
                <p className="font-medium text-blue-900 mb-2">Recommendation:</p>
                <p className="text-xs text-blue-700">
                  Review the {modelPerformanceData.overall.humanOverrides} flagged transactions to help the model learn your specific categorization preferences. 
                  This will improve future accuracy and reduce manual review time.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={filterConfidence}
            onChange={(e) => setFilterConfidence(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Confidence Levels</option>
            <option value="high">High Confidence (90%+)</option>
            <option value="medium">Medium Confidence (70-89%)</option>
            <option value="low">Low Confidence (50-69%)</option>
          </select>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
            <RefreshCw className="w-4 h-4" />
            <span>Retrain Model</span>
          </button>
        </div>
      </div>

      {/* Transaction Analysis Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900">Recent Categorization Results</h3>
          <p className="text-sm text-gray-600 mt-1">AI-powered expense classification with confidence scores</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Predicted Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FinBERT Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTransactions.map((txn) => (
                <tr key={txn.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{txn.description}</div>
                      <div className="text-sm text-gray-500">{txn.vendor} • {new Date(txn.date).toLocaleDateString()}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {txn.predictedCategory}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            txn.confidence >= 0.9 ? 'bg-green-500' :
                            txn.confidence >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${txn.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${getConfidenceColor(txn.confidence)}`}>
                        {Math.round(txn.confidence * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      <Brain className="w-4 h-4 text-purple-600" />
                      <span className="text-sm text-gray-900">{Math.round(txn.finbertScore * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    €{txn.amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => setSelectedTransaction(txn.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="text-green-600 hover:text-green-900">
                        <CheckCircle className="w-4 h-4" />
                      </button>
                      <button className="text-gray-400 hover:text-gray-600">
                        <Settings className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confidence Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confidence Breakdown */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Confidence Distribution</h3>
          <div className="space-y-4">
            {Object.entries(modelPerformanceData.confidenceDistribution).map(([level, data]) => (
              <div key={level} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      level === 'high' ? 'bg-green-500' :
                      level === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                    <span className="text-sm font-medium text-gray-700 capitalize">{level} Confidence ({data.range})</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">{data.count.toLocaleString()} transactions</p>
                    <p className="text-xs text-gray-500">{data.percentage}%</p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      level === 'high' ? 'bg-green-500' :
                      level === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} 
                    style={{ width: `${data.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Category Performance */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Categories</h3>
          <div className="space-y-3">
            {modelPerformanceData.byCategory.slice(0, 6).map((cat, index) => (
              <div key={cat.category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 font-semibold text-sm">{index + 1}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{cat.category}</p>
                    <p className="text-xs text-gray-500">{cat.transactions} transactions</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-green-600">{cat.accuracy}%</p>
                  <p className="text-xs text-gray-500">avg confidence: {Math.round(cat.avgConfidence * 100)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  const PerformanceView = () => {
    const performanceMetrics = {
      trainingHistory: [
        { epoch: 1, accuracy: 0.72, loss: 0.65, valAccuracy: 0.68, valLoss: 0.71 },
        { epoch: 2, accuracy: 0.81, loss: 0.52, valAccuracy: 0.78, valLoss: 0.58 },
        { epoch: 3, accuracy: 0.87, loss: 0.41, valAccuracy: 0.84, valLoss: 0.47 },
        { epoch: 4, accuracy: 0.91, loss: 0.32, valAccuracy: 0.89, valLoss: 0.38 },
        { epoch: 5, accuracy: 0.94, loss: 0.24, valAccuracy: 0.92, valLoss: 0.29 }
      ],
      featureImportance: [
        { feature: 'Transaction Description', importance: 0.35, examples: ['office supplies', 'software subscription'] },
        { feature: 'Vendor Name', importance: 0.28, examples: ['AWS', 'Staples', 'Adobe'] },
        { feature: 'Amount Range', importance: 0.18, examples: ['< €100', '€100-€1000', '> €1000'] },
        { feature: 'Transaction Frequency', importance: 0.12, examples: ['Monthly recurring', 'One-time'] },
        { feature: 'Date Pattern', importance: 0.07, examples: ['Month-end', 'Weekly', 'Irregular'] }
      ],
      confusionMatrix: {
        categories: ['Technology', 'Office', 'Professional', 'Travel', 'Marketing'],
        matrix: [
          [0.96, 0.02, 0.01, 0.01, 0.00], // Technology actual
          [0.03, 0.94, 0.02, 0.01, 0.00], // Office actual
          [0.01, 0.01, 0.89, 0.07, 0.02], // Professional actual
          [0.00, 0.01, 0.04, 0.95, 0.00], // Travel actual
          [0.02, 0.01, 0.03, 0.01, 0.93]  // Marketing actual
        ]
      },
      modelComparison: [
        { model: 'FinBERT (Current)', accuracy: 94.2, precision: 91.8, recall: 89.5, f1Score: 90.6, inferenceTime: 45 },
        { model: 'BERT Base', accuracy: 89.7, precision: 87.2, recall: 85.1, f1Score: 86.1, inferenceTime: 38 },
        { model: 'Random Forest', accuracy: 82.3, precision: 79.8, recall: 77.4, f1Score: 78.6, inferenceTime: 12 },
        { model: 'SVM', accuracy: 78.9, precision: 75.3, recall: 73.1, f1Score: 74.2, inferenceTime: 8 },
        { model: 'Naive Bayes', accuracy: 71.4, precision: 68.7, recall: 66.2, f1Score: 67.4, inferenceTime: 3 }
      ]
    }

    return (
      <div className="space-y-6">
        {/* Performance Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Current Accuracy</p>
                <p className="text-2xl font-bold text-green-600">{modelPerformanceData.overall.accuracy}%</p>
                <p className="text-xs text-green-600 mt-1">↗ +2.1% vs last model</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Target className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Inference Time</p>
                <p className="text-2xl font-bold text-blue-600">45ms</p>
                <p className="text-xs text-gray-500 mt-1">Per transaction</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Training Epochs</p>
                <p className="text-2xl font-bold text-purple-600">{performanceMetrics.trainingHistory.length}</p>
                <p className="text-xs text-gray-500 mt-1">Converged optimally</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">F1-Score</p>
                <p className="text-2xl font-bold text-orange-600">{modelPerformanceData.overall.f1Score}%</p>
                <p className="text-xs text-gray-500 mt-1">Balanced performance</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <Award className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Dr. Sigmund ML Performance Insights */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
          <div className="flex items-start space-x-4">
            <DrSigmundSpendAvatar size="sm" mood="analytical" />
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-semibold text-purple-900">ML Performance Psychology</h3>
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">Model Insights</span>
              </div>
              <div className="space-y-3 text-sm text-purple-800">
                <p>
                  Your FinBERT model is performing exceptionally well with <strong>94.2% accuracy</strong>. 
                  The convergence in just 5 epochs suggests optimal hyperparameter tuning.
                </p>
                <p>
                  <strong>Key Strength:</strong> The model excels at technology and office supply categorization (96% and 94% accuracy respectively), 
                  reflecting your business's clear transaction patterns in these areas.
                </p>
                <div className="bg-white/60 rounded-lg p-3 mt-3">
                  <p className="font-medium text-purple-900 mb-1">Improvement Opportunity:</p>
                  <p className="text-xs text-purple-700">
                    Professional services show some confusion with contractor payments (89% accuracy vs 96% for tech). 
                    Consider adding more contextual features like payment frequency patterns.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Training History */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Training Progress</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Accuracy Progress */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Accuracy Evolution</h4>
                <div className="space-y-2">
                  {performanceMetrics.trainingHistory.map((epoch, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium text-gray-700">Epoch {epoch.epoch}</span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-600">Train:</span>
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${epoch.accuracy * 100}%` }}></div>
                          </div>
                          <span className="font-medium text-gray-900">{Math.round(epoch.accuracy * 100)}%</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-600">Val:</span>
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div className="bg-green-500 h-2 rounded-full" style={{ width: `${epoch.valAccuracy * 100}%` }}></div>
                          </div>
                          <span className="font-medium text-gray-900">{Math.round(epoch.valAccuracy * 100)}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Loss Progress */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Loss Reduction</h4>
                <div className="space-y-2">
                  {performanceMetrics.trainingHistory.map((epoch, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium text-gray-700">Epoch {epoch.epoch}</span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-600">Train:</span>
                          <span className="font-medium text-gray-900">{epoch.loss.toFixed(3)}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-600">Val:</span>
                          <span className="font-medium text-gray-900">{epoch.valLoss.toFixed(3)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Importance */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Importance Analysis</h3>
          <div className="space-y-4">
            {performanceMetrics.featureImportance.map((feature, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{feature.feature}</h4>
                    <p className="text-xs text-gray-500">Examples: {feature.examples.join(', ')}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">{Math.round(feature.importance * 100)}%</p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${
                      index === 0 ? 'bg-blue-500' :
                      index === 1 ? 'bg-green-500' :
                      index === 2 ? 'bg-yellow-500' :
                      index === 3 ? 'bg-purple-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${feature.importance * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Comparison */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900">Model Comparison</h3>
            <p className="text-sm text-gray-600 mt-1">Performance benchmarks across different algorithms</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Accuracy</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precision</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recall</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">F1-Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inference Time</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {performanceMetrics.modelComparison.map((model, index) => (
                  <tr key={index} className={`hover:bg-gray-50 ${index === 0 ? 'bg-blue-50' : ''}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{model.model}</div>
                        {index === 0 && (
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Active
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{ width: `${model.accuracy}%` }}></div>
                        </div>
                        <span className="text-sm text-gray-900">{model.accuracy}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{model.precision}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{model.recall}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{model.f1Score}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{model.inferenceTime}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Confusion Matrix */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Confusion Matrix - Top Categories</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="text-left p-2 font-medium text-gray-900">Actual / Predicted</th>
                  {performanceMetrics.confusionMatrix.categories.map((cat, index) => (
                    <th key={index} className="text-center p-2 font-medium text-gray-900">{cat}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {performanceMetrics.confusionMatrix.matrix.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    <td className="p-2 font-medium text-gray-900">{performanceMetrics.confusionMatrix.categories[rowIndex]}</td>
                    {row.map((value, colIndex) => (
                      <td key={colIndex} className="text-center p-2">
                        <div className={`rounded px-2 py-1 text-xs font-medium ${
                          rowIndex === colIndex 
                            ? 'bg-green-100 text-green-800' 
                            : value > 0.05 
                              ? 'bg-yellow-100 text-yellow-800' 
                              : 'bg-gray-100 text-gray-600'
                        }`}>
                          {Math.round(value * 100)}%
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-xs text-gray-600">
            <p><strong>Green:</strong> Correct predictions (diagonal) | <strong>Yellow:</strong> Common misclassifications | <strong>Gray:</strong> Rare errors</p>
          </div>
        </div>
      </div>
    )
  }

  const IntelligenceView = () => {
    const businessMetrics = {
      cashConversion: {
        cycle: 45, // days
        trend: -3, // improvement
        components: {
          receivables: 28,
          inventory: 12,
          payables: -15
        }
      },
      vendorAnalysis: [
        { vendor: 'Amazon Web Services', totalSpent: 15640, frequency: 12, avgAmount: 1303, category: 'Technology', riskScore: 'Low', paymentTerms: 'Net 30' },
        { vendor: 'Staples Office Supplies', totalSpent: 8920, frequency: 24, avgAmount: 372, category: 'Office', riskScore: 'Low', paymentTerms: 'Net 15' },
        { vendor: 'Blue Bottle Coffee', totalSpent: 6780, frequency: 36, avgAmount: 188, category: 'Office', riskScore: 'Medium', paymentTerms: 'Immediate' },
        { vendor: 'EuroLogistics Consulting', totalSpent: 12500, frequency: 4, avgAmount: 3125, category: 'Professional', riskScore: 'Medium', paymentTerms: 'Net 60' },
        { vendor: 'Adobe Creative Suite', totalSpent: 4200, frequency: 12, avgAmount: 350, category: 'Technology', riskScore: 'Low', paymentTerms: 'Net 30' }
      ],
      spendingInsights: {
        totalSpend: 147280,
        monthlyAverage: 12273,
        growthRate: 8.5,
        topCategories: [
          { category: 'Technology', amount: 45230, percentage: 30.7, trend: 12 },
          { category: 'Professional Services', amount: 32100, percentage: 21.8, trend: -5 },
          { category: 'Office & Supplies', amount: 28950, percentage: 19.6, trend: 3 },
          { category: 'Marketing', amount: 18600, percentage: 12.6, trend: 18 },
          { category: 'Travel', amount: 15400, percentage: 10.5, trend: -12 }
        ]
      }
    }

    return (
      <div className="space-y-6">
        {/* Business Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Cash Conversion Cycle</p>
                <p className="text-2xl font-bold text-blue-600">{businessMetrics.cashConversion.cycle} days</p>
                <p className="text-xs text-green-600 mt-1">
                  {businessMetrics.cashConversion.trend > 0 ? '↗' : '↘'} {Math.abs(businessMetrics.cashConversion.trend)} days vs last quarter
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Vendor Spend</p>
                <p className="text-2xl font-bold text-green-600">€{businessMetrics.spendingInsights.totalSpend.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">This quarter</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Vendors</p>
                <p className="text-2xl font-bold text-purple-600">{businessMetrics.vendorAnalysis.length}</p>
                <p className="text-xs text-gray-500 mt-1">Regular suppliers</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Spend Growth Rate</p>
                <p className="text-2xl font-bold text-orange-600">{businessMetrics.spendingInsights.growthRate}%</p>
                <p className="text-xs text-gray-500 mt-1">Year over year</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Dr. Sigmund Business Intelligence Insights */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border border-green-200">
          <div className="flex items-start space-x-4">
            <DrSigmundSpendAvatar size="sm" mood="thoughtful" />
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-semibold text-green-900">Business Intelligence Insights</h3>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Cash Flow Analysis</span>
              </div>
              <div className="space-y-3 text-sm text-green-800">
                <p>
                  Your <strong>45-day cash conversion cycle</strong> is improving! The 3-day reduction shows better working capital management. 
                  Focus on optimizing vendor payment terms further.
                </p>
                <p>
                  <strong>Spending Pattern:</strong> Technology investments (30.7% of spend) are driving growth. 
                  Consider negotiating annual contracts with AWS for better rates.
                </p>
                <div className="bg-white/60 rounded-lg p-3 mt-3">
                  <p className="font-medium text-green-900 mb-1">Optimization Opportunity:</p>
                  <p className="text-xs text-green-700">
                    EuroLogistics has Net 60 terms while most others are Net 30. This asymmetry affects your cash flow. 
                    Consider standardizing payment terms across suppliers.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Cash Conversion Cycle Breakdown */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cash Conversion Cycle Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <h4 className="font-medium text-blue-900">Days Sales Outstanding</h4>
              </div>
              <p className="text-2xl font-bold text-blue-600">{businessMetrics.cashConversion.components.receivables} days</p>
              <p className="text-sm text-blue-700 mt-1">Time to collect receivables</p>
              <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '70%' }}></div>
              </div>
            </div>

            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="w-4 h-4 text-yellow-600" />
                <h4 className="font-medium text-yellow-900">Days Inventory Outstanding</h4>
              </div>
              <p className="text-2xl font-bold text-yellow-600">{businessMetrics.cashConversion.components.inventory} days</p>
              <p className="text-sm text-yellow-700 mt-1">Inventory conversion time</p>
              <div className="w-full bg-yellow-200 rounded-full h-2 mt-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '40%' }}></div>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <DollarSign className="w-4 h-4 text-green-600" />
                <h4 className="font-medium text-green-900">Days Payable Outstanding</h4>
              </div>
              <p className="text-2xl font-bold text-green-600">{Math.abs(businessMetrics.cashConversion.components.payables)} days</p>
              <p className="text-sm text-green-700 mt-1">Payment delay advantage</p>
              <div className="w-full bg-green-200 rounded-full h-2 mt-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '50%' }}></div>
              </div>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-700">
              <strong>Formula:</strong> Cash Conversion Cycle = Days Sales Outstanding + Days Inventory Outstanding - Days Payable Outstanding
            </p>
            <p className="text-sm text-gray-600 mt-1">
              ({businessMetrics.cashConversion.components.receivables} + {businessMetrics.cashConversion.components.inventory} - {Math.abs(businessMetrics.cashConversion.components.payables)}) = {businessMetrics.cashConversion.cycle} days
            </p>
          </div>
        </div>

        {/* Vendor Analysis */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900">Vendor Performance Analysis</h3>
            <p className="text-sm text-gray-600 mt-1">Strategic supplier relationships and spending patterns</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Frequency</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment Terms</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {businessMetrics.vendorAnalysis.map((vendor, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{vendor.vendor}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      €{vendor.totalSpent.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vendor.frequency} transactions
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      €{vendor.avgAmount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {vendor.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vendor.paymentTerms}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        vendor.riskScore === 'Low' ? 'bg-green-100 text-green-800' :
                        vendor.riskScore === 'Medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {vendor.riskScore}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Spending Category Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Category Breakdown */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending by Category</h3>
            <div className="space-y-4">
              {businessMetrics.spendingInsights.topCategories.map((cat, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-4 h-4 rounded ${
                        index === 0 ? 'bg-blue-500' :
                        index === 1 ? 'bg-green-500' :
                        index === 2 ? 'bg-yellow-500' :
                        index === 3 ? 'bg-purple-500' : 'bg-red-500'
                      }`}></div>
                      <span className="text-sm font-medium text-gray-700">{cat.category}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900">€{cat.amount.toLocaleString()}</p>
                      <div className="flex items-center space-x-1">
                        <p className="text-xs text-gray-500">{cat.percentage}%</p>
                        <span className={`text-xs ${cat.trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {cat.trend > 0 ? '↗' : '↘'} {Math.abs(cat.trend)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        index === 0 ? 'bg-blue-500' :
                        index === 1 ? 'bg-green-500' :
                        index === 2 ? 'bg-yellow-500' :
                        index === 3 ? 'bg-purple-500' : 'bg-red-500'
                      }`} 
                      style={{ width: `${cat.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Optimization Recommendations */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Opportunities</h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <Lightbulb className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-blue-900">Volume Discounts</p>
                  <p className="text-xs text-blue-700 mt-1">
                    AWS spending (€15,640) qualifies for enterprise discounts. Potential 15-20% savings.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <Target className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-900">Payment Terms</p>
                  <p className="text-xs text-green-700 mt-1">
                    Standardize to Net 30 across vendors. EuroLogistics Net 60 terms hurt cash flow.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                <Award className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-purple-900">Vendor Consolidation</p>
                  <p className="text-xs text-purple-700 mt-1">
                    Consolidate office supplies to single vendor for better rates and simplified management.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <Activity className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-yellow-900">Spend Analytics</p>
                  <p className="text-xs text-yellow-700 mt-1">
                    Marketing spend up 18% - ensure ROI tracking aligns with growth investments.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enhanced Analytics & Reporting</h1>
          <p className="text-gray-600 mt-1">AI-powered expense categorization and business intelligence</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
            <Download className="w-4 h-4" />
            <span>Export Analysis</span>
          </button>
          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2">
            <Settings className="w-4 h-4" />
            <span>Configure</span>
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'categorization', label: 'Categorization', icon: Brain },
          { id: 'intelligence', label: 'Business Intelligence', icon: BarChart3 },
          { id: 'performance', label: 'Model Performance', icon: TrendingUp }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
              selectedTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      {selectedTab === 'categorization' && <CategorizationView />}
      {selectedTab === 'performance' && <PerformanceView />}
      {selectedTab === 'intelligence' && <IntelligenceView />}

      {/* Transaction Detail Modal */}
      {selectedTransaction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Transaction Analysis Details</h2>
                <button 
                  onClick={() => setSelectedTransaction(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <ArrowRight className="w-5 h-5 text-gray-500 rotate-45" />
                </button>
              </div>
              
              {(() => {
                const txn = mockCategorizedTransactions.find(t => t.id === selectedTransaction)
                if (!txn) return null
                
                return (
                  <div className="space-y-6">
                    {/* Transaction Header */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-2">{txn.description}</h3>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Amount:</span>
                          <span className="ml-2 font-medium">€{txn.amount}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Date:</span>
                          <span className="ml-2 font-medium">{new Date(txn.date).toLocaleDateString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Vendor:</span>
                          <span className="ml-2 font-medium">{txn.vendor}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Transaction ID:</span>
                          <span className="ml-2 font-medium">{txn.id}</span>
                        </div>
                      </div>
                    </div>

                    {/* AI Analysis */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-900">AI Classification Analysis</h4>
                      
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Brain className="w-4 h-4 text-blue-600" />
                          <span className="font-medium text-blue-900">Primary Prediction</span>
                        </div>
                        <p className="text-blue-800 font-semibold">{txn.predictedCategory}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-blue-700">Confidence:</span>
                            <span className="font-medium text-blue-900">{Math.round(txn.confidence * 100)}%</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-blue-700">FinBERT Score:</span>
                            <span className="font-medium text-blue-900">{Math.round(txn.finbertScore * 100)}%</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <h5 className="font-medium text-gray-900 mb-2">Model Explanation</h5>
                        <p className="text-sm text-gray-700">{txn.modelExplanation}</p>
                      </div>

                      <div>
                        <h5 className="font-medium text-gray-900 mb-3">Alternative Categories</h5>
                        <div className="space-y-2">
                          {txn.alternativeCategories.map((alt, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <span className="text-sm text-gray-700">{alt.category}</span>
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-gray-400 h-2 rounded-full"
                                    style={{ width: `${alt.confidence * 100}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm text-gray-600">{Math.round(alt.confidence * 100)}%</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-3 pt-4 border-t border-gray-200">
                      <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4" />
                        <span>Confirm Category</span>
                      </button>
                      <button className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors">
                        Override Category
                      </button>
                      <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        Provide Feedback
                      </button>
                    </div>
                  </div>
                )
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}