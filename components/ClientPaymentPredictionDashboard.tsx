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
import { 
  cardClasses, 
  buttonClasses, 
  inputClasses, 
  badgeClasses, 
  cn, 
  gradientClasses, 
  focusRing,
  textClasses,
  shadowClasses,
  headerClasses,
  headerTitleClasses,
  headerDescClasses
} from '../lib/design-utils'
import { semantic, components } from '../lib/design-system'

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
      case 'low_risk': return badgeClasses('success')
      case 'medium_risk': return badgeClasses('warning') 
      case 'high_risk': return badgeClasses('error')
      default: return badgeClasses('neutral')
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
      <div className={headerClasses('clean')}>
        <div>
          <h1 className={headerTitleClasses('2xl')}>
            Client Payment Prediction Center
          </h1>
          <p className={headerDescClasses('default')}>
            AI-powered late payment prediction and client risk assessment
          </p>
        </div>
        <div className="text-right">
          <div className={cn(
            textClasses.size('sm'),
            semantic.text.muted,
            'mb-1'
          )}>
            Total Outstanding
          </div>
          <div className={cn(
            textClasses.size('3xl'),
            textClasses.weight('bold'),
            semantic.text.primary
          )}>
            €{totalOutstanding.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className={cardClasses('default', 'p-6')}>
          <div className="flex items-center gap-3 mb-3">
            <Euro className="h-5 w-5 text-brand-primary" />
            <span className={cn(
              textClasses.size('sm'),
              textClasses.weight('medium'),
              semantic.text.secondary
            )}>
              Outstanding
            </span>
          </div>
          <div className={cn(
            textClasses.size('2xl'),
            textClasses.weight('bold'),
            semantic.text.primary,
            'mb-1'
          )}>
            €{totalOutstanding.toLocaleString()}
          </div>
          <div className={cn(textClasses.size('sm'), semantic.text.muted)}>
            {invoices.length} invoices
          </div>
        </div>

        <div className={cardClasses('default', 'p-6')}>
          <div className="flex items-center gap-3 mb-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <span className={cn(
              textClasses.size('sm'),
              textClasses.weight('medium'),
              semantic.text.secondary
            )}>
              Overdue
            </span>
          </div>
          <div className={cn(
            textClasses.size('2xl'),
            textClasses.weight('bold'),
            'text-red-600 mb-1'
          )}>
            €{overdueAmount.toLocaleString()}
          </div>
          <div className={cn(textClasses.size('sm'), semantic.text.muted)}>
            {invoices.filter(inv => inv.status === 'overdue').length} invoices
          </div>
        </div>

        <div className={cardClasses('default', 'p-6')}>
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <span className={cn(
              textClasses.size('sm'),
              textClasses.weight('medium'),
              semantic.text.secondary
            )}>
              High Risk
            </span>
          </div>
          <div className={cn(
            textClasses.size('2xl'),
            textClasses.weight('bold'),
            'text-yellow-600 mb-1'
          )}>
            €{highRiskAmount.toLocaleString()}
          </div>
          <div className={cn(textClasses.size('sm'), semantic.text.muted)}>
            {invoices.filter(inv => inv.latePaymentProbability > 70).length} invoices
          </div>
        </div>

        <div className={cardClasses('default', 'p-6')}>
          <div className="flex items-center gap-3 mb-3">
            <Clock className="h-5 w-5 text-brand-primary" />
            <span className={cn(
              textClasses.size('sm'),
              textClasses.weight('medium'),
              semantic.text.secondary
            )}>
              Avg Payment
            </span>
          </div>
          <div className={cn(
            textClasses.size('2xl'),
            textClasses.weight('bold'),
            'text-brand-primary mb-1'
          )}>
            {avgPaymentTime.toFixed(0)}
          </div>
          <div className={cn(textClasses.size('sm'), semantic.text.muted)}>
            days average
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className={cardClasses('elevated', 'p-6')}>
        <div className="flex flex-col md:flex-row gap-6 items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search invoices or clients..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={cn(
                  inputClasses('default'),
                  'pl-10 pr-4 w-64'
                )}
              />
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className={cn(
                inputClasses('default'),
                'px-4 py-2 w-48'
              )}
            >
              <option value="all">All Risk Levels</option>
              <option value="high_risk">High Risk</option>
              <option value="medium_risk">Medium Risk</option>
              <option value="low_risk">Low Risk</option>
            </select>
          </div>
          
          <div className="flex items-center gap-3">
            <span className={cn(
              textClasses.size('sm'),
              semantic.text.secondary
            )}>
              Timeframe:
            </span>
            <div className={cn(
              semantic.background.secondary,
              'flex rounded-xl p-1'
            )}>
              {(['7d', '30d', '90d', '180d'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => setSelectedTimeframe(period)}
                  className={cn(
                    buttonClasses(
                      selectedTimeframe === period ? 'primary' : 'ghost',
                      'sm'
                    ),
                    'min-w-12'
                  )}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Payment Predictions Table */}
      <div className={cardClasses('elevated', 'p-6')}>
        <h2 className={cn(
          textClasses.size('lg'),
          textClasses.weight('semibold'),
          semantic.text.primary,
          'mb-6 flex items-center gap-3'
        )}>
          <Target className="h-5 w-5 text-brand-primary" />
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
                      <div className={
                        invoice.latePaymentProbability <= 20 ? badgeClasses('success') :
                        invoice.latePaymentProbability <= 50 ? badgeClasses('warning') :
                        badgeClasses('error')
                      }>
                        {invoice.latePaymentProbability}%
                      </div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className={getRiskColor(riskLevel)}>
                        {riskLevel.replace('_', ' ').toUpperCase()}
                      </div>
                    </td>
                    
                    <td className="p-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button className={cn(
                          'p-2 text-brand-primary hover:bg-brand-primary/10 rounded-lg',
                          'transition-colors duration-150'
                        )}>
                          <FileText className="h-4 w-4" />
                        </button>
                        <button className={cn(
                          'p-2 text-gray-600 hover:bg-gray-100 rounded-lg',
                          'transition-colors duration-150'
                        )}>
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
      <div className={cardClasses('elevated', 'p-6')}>
        <h2 className={cn(
          textClasses.size('lg'),
          textClasses.weight('semibold'),
          semantic.text.primary,
          'mb-6 flex items-center gap-3'
        )}>
          <Shield className="h-5 w-5 text-brand-primary" />
          Client Risk Overview
        </h2>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clients.map((client) => {
            const riskLevel = getRiskLevel(client.riskScore)
            
            return (
              <div key={client.id} className={cardClasses('interactive', 'p-5')}>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className={cn(
                      textClasses.weight('semibold'),
                      semantic.text.primary
                    )}>
                      {client.name}
                    </h3>
                    <p className={cn(
                      textClasses.size('sm'),
                      semantic.text.muted
                    )}>
                      {client.industry}
                    </p>
                  </div>
                  <div className={cn(
                    getRiskColor(riskLevel),
                    'text-xs font-bold'
                  )}>
                    {client.riskScore}
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className={cn(textClasses.size('sm'), semantic.text.secondary)}>
                      Outstanding:
                    </span>
                    <span className={cn(
                      textClasses.size('sm'),
                      textClasses.weight('semibold'),
                      semantic.text.primary
                    )}>
                      €{client.currentOutstanding.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={cn(textClasses.size('sm'), semantic.text.secondary)}>
                      Avg Payment:
                    </span>
                    <span className={cn(
                      textClasses.size('sm'),
                      textClasses.weight('semibold'),
                      semantic.text.primary
                    )}>
                      {client.paymentHistory.averageDays} days
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={cn(textClasses.size('sm'), semantic.text.secondary)}>
                      On-time Rate:
                    </span>
                    <span className={cn(
                      textClasses.size('sm'),
                      textClasses.weight('semibold'),
                      client.paymentHistory.onTimeRate >= 70 ? 'text-green-600' : 
                      client.paymentHistory.onTimeRate >= 40 ? 'text-yellow-600' : 'text-red-600'
                    )}>
                      {client.paymentHistory.onTimeRate}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={cn(textClasses.size('sm'), semantic.text.secondary)}>
                      Total Invoices:
                    </span>
                    <span className={cn(
                      textClasses.size('sm'),
                      textClasses.weight('semibold'),
                      semantic.text.primary
                    )}>
                      {client.paymentHistory.totalInvoices}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Action Recommendations */}
      <div className={cn(
        'bg-gradient-to-r from-brand-primary/5 to-brand-accent/5',
        'border border-brand-primary/20 rounded-2xl p-6'
      )}>
        <h2 className={cn(
          textClasses.size('lg'),
          textClasses.weight('semibold'),
          'text-brand-primary-dark mb-6 flex items-center gap-3'
        )}>
          <Target className="h-5 w-5 text-brand-primary" />
          AI-Powered Action Recommendations
        </h2>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className={cn(
              textClasses.weight('semibold'),
              'text-brand-primary-dark mb-4'
            )}>
              Immediate Actions
            </h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                <span className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Follow up on 1 overdue invoice (€{overdueAmount.toLocaleString()} total)
                </span>
              </div>
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <span className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Monitor 2 high-risk invoices closely for early intervention
                </span>
              </div>
              <div className="flex items-start gap-3">
                <Clock className="h-5 w-5 text-brand-primary mt-0.5 flex-shrink-0" />
                <span className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Consider payment terms adjustment for high-risk clients
                </span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className={cn(
              textClasses.weight('semibold'),
              'text-brand-primary-dark mb-4'
            )}>
              Strategic Actions
            </h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <DollarSign className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                <span className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Implement early payment discounts for slower-paying clients
                </span>
              </div>
              <div className="flex items-start gap-3">
                <CreditCard className="h-5 w-5 text-brand-primary mt-0.5 flex-shrink-0" />
                <span className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Diversify client base to reduce concentration risk
                </span>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="h-5 w-5 text-brand-primary mt-0.5 flex-shrink-0" />
                <span className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Review and strengthen contracts with high-risk clients
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dr. Sigmund Cash Flow Therapy Section */}
      <div className={cn(
        cardClasses('elevated', 'p-8'),
        'mt-12'
      )}>
        <div className="flex items-start gap-8">
          <div className={cn(
            'w-20 h-20 rounded-full flex items-center justify-center flex-shrink-0',
            gradientClasses('primary-subtle')
          )}>
            <Target className="h-10 w-10 text-white" />
          </div>
          <div className="flex-1">
            <h2 className={cn(
              textClasses.size('xl'),
              textClasses.weight('bold'),
              semantic.text.primary,
              'mb-6'
            )}>
              Dr. Sigmund's Cash Flow Therapy
            </h2>
            <div className={cn(
              'bg-gradient-to-r from-brand-primary/5 to-brand-accent/10',
              'border border-brand-primary/20 rounded-2xl p-6'
            )}>
              <h3 className={cn(
                textClasses.weight('semibold'),
                'text-brand-primary-dark mb-4'
              )}>
                Payment Anxiety Relief Strategy
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className={cn(
                    textClasses.weight('semibold'),
                    'text-brand-primary mb-3'
                  )}>
                    🎯 Predictive Peace of Mind
                  </h4>
                  <ul className="space-y-2">
                    {[
                      'Know which payments might be late before they happen',
                      'Plan cash flow around realistic payment timelines',
                      'Take early action instead of reactive panic',
                      'Focus energy on high-impact interventions'
                    ].map((item, index) => (
                      <li key={index} className={cn(
                        textClasses.size('sm'),
                        'text-brand-primary-dark flex items-start gap-2'
                      )}>
                        <span className="text-brand-primary mt-1">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className={cn(
                    textClasses.weight('semibold'),
                    'text-brand-primary mb-3'
                  )}>
                    🔍 Smart Client Management
                  </h4>
                  <ul className="space-y-2">
                    {[
                      'Identify clients who need closer follow-up',
                      'Adjust payment terms based on reliability data',
                      'Build stronger relationships through understanding',
                      'Make informed decisions about new clients'
                    ].map((item, index) => (
                      <li key={index} className={cn(
                        textClasses.size('sm'),
                        'text-brand-primary-dark flex items-start gap-2'
                      )}>
                        <span className="text-brand-primary mt-1">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ML Model Information */}
      <div className={cn(
        'mt-8 bg-gradient-to-r from-brand-primary/5 to-brand-accent/10',
        'border border-brand-primary/20 rounded-2xl p-6'
      )}>
        <h3 className={cn(
          textClasses.weight('semibold'),
          'text-brand-primary-dark mb-6'
        )}>
          🤖 How Our Payment Prediction Works
        </h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div className={cardClasses('default', 'p-5 border-brand-primary/20')}>
            <div className={cn(
              textClasses.weight('semibold'),
              'text-brand-primary mb-3'
            )}>
              1. Historical Analysis
            </div>
            <p className={cn(
              textClasses.size('sm'),
              'text-brand-primary-dark'
            )}>
              Our AI analyzes each client's payment history, identifying patterns in timing, seasonality, and payment behavior changes
            </p>
          </div>
          <div className={cardClasses('default', 'p-5 border-brand-primary/20')}>
            <div className={cn(
              textClasses.weight('semibold'),
              'text-brand-primary mb-3'
            )}>
              2. Risk Scoring
            </div>
            <p className={cn(
              textClasses.size('sm'),
              'text-brand-primary-dark'
            )}>
              Machine learning models consider invoice amount, payment terms, client industry, and economic factors to calculate risk
            </p>
          </div>
          <div className={cardClasses('default', 'p-5 border-brand-primary/20')}>
            <div className={cn(
              textClasses.weight('semibold'),
              'text-brand-primary mb-3'
            )}>
              3. Actionable Insights
            </div>
            <p className={cn(
              textClasses.size('sm'),
              'text-brand-primary-dark'
            )}>
              Predictions come with confidence scores and specific recommendations for managing each client relationship
            </p>
          </div>
        </div>
      </div>

      {/* Best Practices */}
      <div className={cn(cardClasses('elevated', 'p-6'), 'mt-8')}>
        <h3 className={cn(
          textClasses.weight('semibold'),
          semantic.text.primary,
          'mb-6 flex items-center gap-3'
        )}>
          <Shield className="h-5 w-5 text-brand-primary" />
          Payment Management Best Practices
        </h3>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h4 className={cn(
              textClasses.weight('semibold'),
              semantic.text.secondary,
              'mb-4'
            )}>
              Proactive Strategies
            </h4>
            <ul className="space-y-3">
              {[
                'Send payment reminders 5-7 days before due date for high-risk clients',
                'Offer early payment discounts to incentivize faster payment',
                'Build stronger relationships with slow-paying but reliable clients',
                'Consider shorter payment terms for new or high-risk clients'
              ].map((item, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="text-green-600 mt-1 text-sm">•</span>
                  <span className={cn(
                    textClasses.size('sm'),
                    semantic.text.primary
                  )}>
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className={cn(
              textClasses.weight('semibold'),
              semantic.text.secondary,
              'mb-4'
            )}>
              Risk Mitigation
            </h4>
            <ul className="space-y-3">
              {[
                'Diversify client base to reduce concentration risk',
                'Maintain emergency fund based on payment prediction data',
                'Regular contract reviews with problematic clients',
                'Consider payment protection or factoring for high-value clients'
              ].map((item, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="text-brand-primary mt-1 text-sm">•</span>
                  <span className={cn(
                    textClasses.size('sm'),
                    semantic.text.primary
                  )}>
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className={cn(
        'mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6'
      )}>
        <div className="flex items-start gap-4">
          <Target className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className={cn(
              textClasses.weight('semibold'),
              'text-yellow-900 mb-3'
            )}>
              Prediction Accuracy Disclaimer
            </h3>
            <p className={cn(
              textClasses.size('sm'),
              'text-yellow-800 leading-relaxed'
            )}>
              Payment predictions are based on historical data and machine learning models. While our algorithms are highly accurate, 
              actual payment behavior may vary due to client circumstances, economic conditions, or other unforeseen factors. 
              Use predictions as guidance for planning and early intervention, not as guarantees of payment timing.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}