'use client'

import { useState } from 'react'
import { 
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Euro,
  Building2,
  User,
  FileText,
  BarChart3,
  Target,
  ArrowRight,
  Filter,
  Search,
  DollarSign,
  CreditCard,
  AlertCircle,
  Shield
} from 'lucide-react'

interface Invoice {
  id: string
  clientName: string
  clientId: string
  amount: number
  invoiceDate: string
  dueDate: string
  paymentTerms: number
  status: 'pending' | 'overdue' | 'paid'
  daysOverdue?: number
  predictedPaymentDate: string
  latePaymentProbability: number
  paymentConfidence: number
  clientRiskScore: number
  historicalPaymentAvg: number
}

interface Client {
  id: string
  name: string
  industry: string
  paymentHistory: {
    averageDays: number
    onTimeRate: number
    totalInvoices: number
  }
  riskScore: number
  currentOutstanding: number
}

export default function ClientPaymentPredictionDashboard() {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'7d' | '30d' | '90d' | '180d'>('30d')
  const [filterStatus, setFilterStatus] = useState<'all' | 'high_risk' | 'medium_risk' | 'low_risk'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  // Mock data
  const invoices: Invoice[] = [
    {
      id: 'INV-001',
      clientName: 'Tech Solutions Inc.',
      clientId: 'CLIENT-001',
      amount: 4500,
      invoiceDate: '2025-01-15',
      dueDate: '2025-02-14',
      paymentTerms: 30,
      status: 'pending',
      predictedPaymentDate: '2025-02-18',
      latePaymentProbability: 25,
      paymentConfidence: 75,
      clientRiskScore: 35,
      historicalPaymentAvg: 34
    },
    {
      id: 'INV-002',
      clientName: 'StartUp Ventures Ltd.',
      clientId: 'CLIENT-002',
      amount: 8200,
      invoiceDate: '2025-01-10',
      dueDate: '2025-02-09',
      paymentTerms: 30,
      status: 'pending',
      predictedPaymentDate: '2025-02-25',
      latePaymentProbability: 78,
      paymentConfidence: 22,
      clientRiskScore: 85,
      historicalPaymentAvg: 52
    },
    {
      id: 'INV-003',
      clientName: 'Enterprise Corp.',
      clientId: 'CLIENT-003',
      amount: 12000,
      invoiceDate: '2025-01-20',
      dueDate: '2025-02-19',
      paymentTerms: 30,
      status: 'pending',
      predictedPaymentDate: '2025-02-17',
      latePaymentProbability: 8,
      paymentConfidence: 92,
      clientRiskScore: 15,
      historicalPaymentAvg: 28
    },
    {
      id: 'INV-004',
      clientName: 'Retail Chain Plus',
      clientId: 'CLIENT-004',
      amount: 3200,
      invoiceDate: '2025-01-05',
      dueDate: '2025-01-20',
      paymentTerms: 15,
      status: 'overdue',
      daysOverdue: 11,
      predictedPaymentDate: '2025-02-10',
      latePaymentProbability: 95,
      paymentConfidence: 15,
      clientRiskScore: 70,
      historicalPaymentAvg: 43
    },
    {
      id: 'INV-005',
      clientName: 'Government Agency',
      clientId: 'CLIENT-005',
      amount: 15600,
      invoiceDate: '2025-01-08',
      dueDate: '2025-03-08',
      paymentTerms: 60,
      status: 'pending',
      predictedPaymentDate: '2025-03-05',
      latePaymentProbability: 5,
      paymentConfidence: 95,
      clientRiskScore: 10,
      historicalPaymentAvg: 58
    }
  ]

  const clients: Client[] = [
    {
      id: 'CLIENT-001',
      name: 'Tech Solutions Inc.',
      industry: 'Technology',
      paymentHistory: { averageDays: 34, onTimeRate: 75, totalInvoices: 24 },
      riskScore: 35,
      currentOutstanding: 4500
    },
    {
      id: 'CLIENT-002',
      name: 'StartUp Ventures Ltd.',
      industry: 'Startup',
      paymentHistory: { averageDays: 52, onTimeRate: 22, totalInvoices: 8 },
      riskScore: 85,
      currentOutstanding: 8200
    },
    {
      id: 'CLIENT-003',
      name: 'Enterprise Corp.',
      industry: 'Enterprise',
      paymentHistory: { averageDays: 28, onTimeRate: 92, totalInvoices: 36 },
      riskScore: 15,
      currentOutstanding: 12000
    },
    {
      id: 'CLIENT-004',
      name: 'Retail Chain Plus',
      industry: 'Retail',
      paymentHistory: { averageDays: 43, onTimeRate: 45, totalInvoices: 18 },
      riskScore: 70,
      currentOutstanding: 3200
    },
    {
      id: 'CLIENT-005',
      name: 'Government Agency',
      industry: 'Public Sector',
      paymentHistory: { averageDays: 58, onTimeRate: 95, totalInvoices: 12 },
      riskScore: 10,
      currentOutstanding: 15600
    }
  ]

  const getRiskLevel = (score: number) => {
    if (score <= 30) return 'low_risk'
    if (score <= 60) return 'medium_risk'
    return 'high_risk'
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low_risk': return 'text-green-600 bg-green-100'
      case 'medium_risk': return 'text-yellow-600 bg-yellow-100'
      case 'high_risk': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch = invoice.clientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         invoice.id.toLowerCase().includes(searchTerm.toLowerCase())
    
    if (filterStatus === 'all') return matchesSearch
    
    const riskLevel = getRiskLevel(invoice.clientRiskScore)
    return matchesSearch && riskLevel === filterStatus
  })

  const totalOutstanding = invoices.reduce((sum, inv) => sum + inv.amount, 0)
  const overdueAmount = invoices.filter(inv => inv.status === 'overdue').reduce((sum, inv) => sum + inv.amount, 0)
  const highRiskAmount = invoices.filter(inv => inv.latePaymentProbability > 70).reduce((sum, inv) => sum + inv.amount, 0)
  const avgPaymentTime = invoices.reduce((sum, inv) => sum + inv.historicalPaymentAvg, 0) / invoices.length

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-medium mb-2">Client Payment Prediction Center</h1>
            <p className="text-blue-100">AI-powered late payment prediction and client risk assessment</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-blue-100">Total Outstanding</div>
            <div className="text-3xl font-medium">€{totalOutstanding.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Euro className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">Outstanding</span>
          </div>
          <div className="text-2xl font-medium text-gray-900">€{totalOutstanding.toLocaleString()}</div>
          <div className="text-sm text-gray-600">{invoices.length} invoices</div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-gray-700">Overdue</span>
          </div>
          <div className="text-2xl font-medium text-red-600">€{overdueAmount.toLocaleString()}</div>
          <div className="text-sm text-gray-600">{invoices.filter(inv => inv.status === 'overdue').length} invoices</div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            <span className="text-sm font-medium text-gray-700">High Risk</span>
          </div>
          <div className="text-2xl font-medium text-orange-600">€{highRiskAmount.toLocaleString()}</div>
          <div className="text-sm text-gray-600">{invoices.filter(inv => inv.latePaymentProbability > 70).length} invoices</div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">Avg Payment</span>
          </div>
          <div className="text-2xl font-medium text-purple-600">{avgPaymentTime.toFixed(0)}</div>
          <div className="text-sm text-gray-600">days average</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search invoices or clients..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Risk Levels</option>
              <option value="high_risk">High Risk</option>
              <option value="medium_risk">Medium Risk</option>
              <option value="low_risk">Low Risk</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Timeframe:</span>
            <div className="flex bg-gray-100 rounded-xl p-1">
              {(['7d', '30d', '90d', '180d'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => setSelectedTimeframe(period)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                    selectedTimeframe === period
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Payment Predictions Table */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Target className="h-5 w-5 text-blue-600" />
          Payment Predictions & Risk Assessment
        </h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left p-3 font-medium text-gray-900">Invoice</th>
                <th className="text-left p-3 font-medium text-gray-900">Client</th>
                <th className="text-right p-3 font-medium text-gray-900">Amount</th>
                <th className="text-center p-3 font-medium text-gray-900">Due Date</th>
                <th className="text-center p-3 font-medium text-gray-900">Predicted Payment</th>
                <th className="text-center p-3 font-medium text-gray-900">Late Risk</th>
                <th className="text-center p-3 font-medium text-gray-900">Client Risk</th>
                <th className="text-center p-3 font-medium text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.map((invoice) => {
                const riskLevel = getRiskLevel(invoice.clientRiskScore)
                const isOverdue = invoice.status === 'overdue'
                
                return (
                  <tr key={invoice.id} className={`border-b border-gray-100 hover:bg-gray-50 ${isOverdue ? 'bg-red-50' : ''}`}>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-gray-400" />
                        <div>
                          <div className="font-medium text-gray-900">{invoice.id}</div>
                          <div className="text-xs text-gray-500">
                            {isOverdue && <span className="text-red-600 font-medium">{invoice.daysOverdue} days overdue</span>}
                          </div>
                        </div>
                      </div>
                    </td>
                    
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <div>
                          <div className="font-medium text-gray-900">{invoice.clientName}</div>
                          <div className="text-xs text-gray-500">{invoice.paymentTerms} day terms</div>
                        </div>
                      </div>
                    </td>
                    
                    <td className="p-3 text-right">
                      <div className="font-medium text-gray-900">€{invoice.amount.toLocaleString()}</div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className={`text-sm ${isOverdue ? 'text-red-600 font-medium' : 'text-gray-700'}`}>
                        {new Date(invoice.dueDate).toLocaleDateString()}
                      </div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className="text-sm text-gray-700">
                        {new Date(invoice.predictedPaymentDate).toLocaleDateString()}
                      </div>
                      <div className={`text-xs ${invoice.paymentConfidence >= 70 ? 'text-green-600' : invoice.paymentConfidence >= 40 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {invoice.paymentConfidence}% confidence
                      </div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        invoice.latePaymentProbability <= 20 ? 'bg-green-100 text-green-800' :
                        invoice.latePaymentProbability <= 50 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {invoice.latePaymentProbability}%
                      </div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(riskLevel)}`}>
                        {riskLevel.replace('_', ' ').toUpperCase()}
                      </div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button className="p-1 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors">
                          <FileText className="h-4 w-4" />
                        </button>
                        <button className="p-1 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Client Risk Overview */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5 text-blue-600" />
          Client Risk Overview
        </h2>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clients.map((client) => {
            const riskLevel = getRiskLevel(client.riskScore)
            
            return (
              <div key={client.id} className="border border-gray-200 rounded-2xl p-4 hover:shadow-sm transition-all">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-medium text-gray-900">{client.name}</h3>
                    <p className="text-sm text-gray-600">{client.industry}</p>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(riskLevel)}`}>
                    {client.riskScore}
                  </div>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Outstanding:</span>
                    <span className="font-medium text-gray-900">€{client.currentOutstanding.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Payment:</span>
                    <span className="font-medium text-gray-900">{client.paymentHistory.averageDays} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">On-time Rate:</span>
                    <span className={`font-medium ${client.paymentHistory.onTimeRate >= 70 ? 'text-green-600' : client.paymentHistory.onTimeRate >= 40 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {client.paymentHistory.onTimeRate}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Invoices:</span>
                    <span className="font-medium text-gray-900">{client.paymentHistory.totalInvoices}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Action Recommendations */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6">
        <h2 className="text-lg font-medium text-blue-900 mb-4 flex items-center gap-2">
          <Target className="h-5 w-5 text-blue-600" />
          AI-Powered Action Recommendations
        </h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-blue-800 mb-3">Immediate Actions</h3>
            <div className="space-y-2 text-sm text-blue-700">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <span>Follow up on 1 overdue invoice (€{overdueAmount.toLocaleString()} total)</span>
              </div>
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                <span>Monitor 2 high-risk invoices closely for early intervention</span>
              </div>
              <div className="flex items-start gap-2">
                <Clock className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                <span>Consider payment terms adjustment for high-risk clients</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium text-blue-800 mb-3">Strategic Actions</h3>
            <div className="space-y-2 text-sm text-blue-700">
              <div className="flex items-start gap-2">
                <DollarSign className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span>Implement early payment discounts for slower-paying clients</span>
              </div>
              <div className="flex items-start gap-2">
                <CreditCard className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <span>Diversify client base to reduce concentration risk</span>
              </div>
              <div className="flex items-start gap-2">
                <FileText className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                <span>Review and strengthen contracts with high-risk clients</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}