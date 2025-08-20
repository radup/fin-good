'use client'

import React, { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  DollarSign,
  Users,
  FileText,
  Calendar,
  Target,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  BarChart3,
  PieChart,
  CreditCard,
  Send,
  Download,
  Filter,
  Search,
  Eye,
  Edit,
  Phone,
  Mail,
  MapPin,
  Heart
} from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

// Mock data for client risk management
const mockClients = [
  {
    id: 1,
    name: 'TechFlow Solutions BV',
    contact: 'Sarah van der Berg',
    email: 'sarah@techflow.nl',
    phone: '+31 20 123 4567',
    location: 'Amsterdam, NL',
    riskScore: 85,
    riskLevel: 'low',
    totalOutstanding: 12500,
    overdue: 0,
    avgPaymentDays: 28,
    lastPayment: '2024-08-15',
    invoiceCount: 14,
    relationshipDuration: '2.5 years',
    industry: 'Technology',
    paymentHistory: [30, 25, 32, 28, 27, 29],
    creditLimit: 25000,
    nextInvoiceDue: '2024-08-25'
  },
  {
    id: 2,
    name: 'Creative Studio SPRL',
    contact: 'Jean-Baptiste Dupont',
    email: 'jb@creativestudio.be',
    phone: '+32 2 987 6543',
    location: 'Brussels, BE',
    riskScore: 65,
    riskLevel: 'medium',
    totalOutstanding: 8750,
    overdue: 2250,
    avgPaymentDays: 45,
    lastPayment: '2024-07-20',
    invoiceCount: 8,
    relationshipDuration: '1.2 years',
    industry: 'Marketing',
    paymentHistory: [45, 52, 38, 60, 42, 48],
    creditLimit: 15000,
    nextInvoiceDue: '2024-08-22'
  },
  {
    id: 3,
    name: 'Retail Express S.à r.l.',
    contact: 'Marie Leblanc',
    email: 'marie@retailexpress.lu',
    phone: '+352 123 456',
    location: 'Luxembourg City, LU',
    riskScore: 35,
    riskLevel: 'high',
    totalOutstanding: 15600,
    overdue: 9800,
    avgPaymentDays: 72,
    lastPayment: '2024-06-10',
    invoiceCount: 12,
    relationshipDuration: '3.1 years',
    industry: 'Retail',
    paymentHistory: [65, 78, 85, 62, 90, 75],
    creditLimit: 20000,
    nextInvoiceDue: '2024-08-20'
  },
  {
    id: 4,
    name: 'EuroLogistics GmbH',
    contact: 'Klaus Weber',
    email: 'klaus@eurologistics.de',
    phone: '+49 30 555 0123',
    location: 'Berlin, DE',
    riskScore: 78,
    riskLevel: 'low',
    totalOutstanding: 22100,
    overdue: 1200,
    avgPaymentDays: 35,
    lastPayment: '2024-08-12',
    invoiceCount: 18,
    relationshipDuration: '4.2 years',
    industry: 'Logistics',
    paymentHistory: [32, 38, 35, 30, 40, 33],
    creditLimit: 50000,
    nextInvoiceDue: '2024-08-28'
  }
]

const mockInvoices = [
  {
    id: 'INV-2024-0856',
    clientId: 1,
    client: 'TechFlow Solutions BV',
    amount: 4500,
    issueDate: '2024-07-25',
    dueDate: '2024-08-25',
    status: 'pending',
    daysPastDue: 0,
    paymentProbability: 92,
    riskFactors: [],
    description: 'Web development services - Q3 2024'
  },
  {
    id: 'INV-2024-0847',
    clientId: 2,
    client: 'Creative Studio SPRL',
    amount: 2250,
    issueDate: '2024-06-20',
    dueDate: '2024-07-20',
    status: 'overdue',
    daysPastDue: 31,
    paymentProbability: 58,
    riskFactors: ['Late payment history', 'Industry downturn'],
    description: 'Brand identity package'
  },
  {
    id: 'INV-2024-0832',
    clientId: 3,
    client: 'Retail Express S.à r.l.',
    amount: 7800,
    issueDate: '2024-05-15',
    dueDate: '2024-06-15',
    status: 'overdue',
    daysPastDue: 66,
    paymentProbability: 35,
    riskFactors: ['Chronic late payer', 'High outstanding balance', 'Credit limit exceeded'],
    description: 'E-commerce platform development'
  },
  {
    id: 'INV-2024-0823',
    clientId: 4,
    client: 'EuroLogistics GmbH',
    amount: 1200,
    issueDate: '2024-07-10',
    dueDate: '2024-08-10',
    status: 'overdue',
    daysPastDue: 10,
    paymentProbability: 85,
    riskFactors: ['Minor delay - good track record'],
    description: 'API integration services'
  }
]

export default function InvoiceRiskDashboard() {
  const [selectedClient, setSelectedClient] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'overview' | 'clients' | 'invoices' | 'predictions'>('overview')
  const [filterRisk, setFilterRisk] = useState<'all' | 'low' | 'medium' | 'high'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [showDrAdviceDetails, setShowDrAdviceDetails] = useState(false)

  // Calculate overall portfolio metrics
  const totalOutstanding = mockClients.reduce((sum, client) => sum + client.totalOutstanding, 0)
  const totalOverdue = mockClients.reduce((sum, client) => sum + client.overdue, 0)
  const averageRiskScore = Math.round(mockClients.reduce((sum, client) => sum + client.riskScore, 0) / mockClients.length)
  const clientsAtRisk = mockClients.filter(client => client.riskLevel === 'high' || client.overdue > 0).length

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'high': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'text-green-600 bg-green-100'
      case 'pending': return 'text-blue-600 bg-blue-100'
      case 'overdue': return 'text-red-600 bg-red-100'
      case 'disputed': return 'text-orange-600 bg-orange-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const filteredClients = mockClients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.contact.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterRisk === 'all' || client.riskLevel === filterRisk
    return matchesSearch && matchesFilter
  })

  const DrSigmundAdvice = () => (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 overflow-hidden">
      {/* Main Banner */}
      <div className="p-4 flex items-center space-x-4">
        <DrSigmundSpendAvatar 
          size="sm"
          mood="analytical"
          message=""
          showMessage={false}
          animated={true}
        />
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-semibold text-blue-800">Dr. Sigmund Spend</span>
            <span className="text-xs text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">Risk Advisory</span>
          </div>
          <p className="text-sm text-gray-700">
            I notice you have <span className="font-medium text-red-600">€15,600 at risk</span> with high-risk clients. 
            Consider implementing payment plans or requiring deposits for new work.
          </p>
        </div>
        <button 
          onClick={() => setShowDrAdviceDetails(!showDrAdviceDetails)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 hover:bg-blue-100 rounded transition-colors flex items-center space-x-1"
        >
          <span>{showDrAdviceDetails ? 'Hide Details' : 'View Details'}</span>
          <svg 
            className={`w-4 h-4 transition-transform ${showDrAdviceDetails ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Expanded Details */}
      {showDrAdviceDetails && (
        <div className="border-t border-blue-200 bg-white p-6">
          <div className="space-y-6">
            {/* Risk Analysis Header */}
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-4 h-4 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Detailed Risk Analysis & Recommendations</h3>
            </div>

            {/* Risk Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <h4 className="font-medium text-red-900">Critical Risk</h4>
                </div>
                <p className="text-sm text-red-800 mb-2">
                  <span className="font-semibold">Retail Express S.à r.l.</span> has €9,800 overdue (66 days)
                </p>
                <p className="text-xs text-red-600">Immediate action required</p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Clock className="w-4 h-4 text-yellow-600" />
                  <h4 className="font-medium text-yellow-900">Medium Risk</h4>
                </div>
                <p className="text-sm text-yellow-800 mb-2">
                  <span className="font-semibold">Creative Studio SPRL</span> averages 45-day payments
                </p>
                <p className="text-xs text-yellow-600">Monitor closely</p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <h4 className="font-medium text-green-900">Performing Well</h4>
                </div>
                <p className="text-sm text-green-800 mb-2">
                  <span className="font-semibold">TechFlow Solutions</span> & <span className="font-semibold">EuroLogistics</span>
                </p>
                <p className="text-xs text-green-600">Reliable payment history</p>
              </div>
            </div>

            {/* Therapeutic Recommendations */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900 flex items-center space-x-2">
                <Heart className="w-4 h-4 text-purple-600" />
                <span>Financial Therapy Insights</span>
              </h4>
              
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h5 className="font-medium text-purple-900 mb-2">Emotional Patterns I've Noticed:</h5>
                <ul className="text-sm text-purple-800 space-y-1 ml-4">
                  <li>• You tend to avoid confronting late-paying clients (avoidance pattern)</li>
                  <li>• There's anxiety around demanding payment from "relationship" clients</li>
                  <li>• You're prioritizing client comfort over your financial health</li>
                </ul>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h5 className="font-medium text-blue-900 mb-2">Immediate Action Steps:</h5>
                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <span className="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded-full">1</span>
                    <div>
                      <p className="text-sm font-medium text-blue-900">Address Critical Risk</p>
                      <p className="text-xs text-blue-700">Call Retail Express today. Set up payment plan if needed.</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <span className="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded-full">2</span>
                    <div>
                      <p className="text-sm font-medium text-blue-900">Implement Payment Terms</p>
                      <p className="text-xs text-blue-700">Require 50% deposits for new projects over €5,000.</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <span className="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded-full">3</span>
                    <div>
                      <p className="text-sm font-medium text-blue-900">Weekly Check-ins</p>
                      <p className="text-xs text-blue-700">Schedule follow-ups every Tuesday at 10 AM.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h5 className="font-medium text-green-900 mb-2">Long-term Health Strategies:</h5>
                <ul className="text-sm text-green-800 space-y-1 ml-4">
                  <li>• Set credit limits based on risk scores (already implemented!)</li>
                  <li>• Create standard payment reminder templates to reduce emotional labor</li>
                  <li>• Celebrate on-time payments - acknowledge good behavior</li>
                  <li>• Practice saying "payment is due" without apology</li>
                </ul>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="border-t border-gray-200 pt-4">
              <h4 className="font-medium text-gray-900 mb-3">Quick Actions</h4>
              <div className="flex flex-wrap gap-2">
                <button className="bg-red-600 text-white px-3 py-1.5 rounded text-sm hover:bg-red-700 transition-colors">
                  Call Retail Express
                </button>
                <button className="bg-yellow-600 text-white px-3 py-1.5 rounded text-sm hover:bg-yellow-700 transition-colors">
                  Email Payment Reminders
                </button>
                <button className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 transition-colors">
                  Update Payment Terms
                </button>
                <button className="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700 transition-colors">
                  Schedule Follow-ups
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const OverviewView = () => (
    <div className="space-y-6">
      {/* Portfolio Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Outstanding</p>
              <p className="text-2xl font-bold text-gray-900">€{totalOutstanding.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">Across {mockClients.length} clients</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overdue Amount</p>
              <p className="text-2xl font-bold text-red-600">€{totalOverdue.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">{Math.round((totalOverdue/totalOutstanding)*100)}% of total</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Average Risk Score</p>
              <p className="text-2xl font-bold text-gray-900">{averageRiskScore}</p>
              <p className="text-xs text-green-600 mt-1">↗ +3 from last month</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Clients at Risk</p>
              <p className="text-2xl font-bold text-orange-600">{clientsAtRisk}</p>
              <p className="text-xs text-gray-500 mt-1">Require attention</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Dr. Sigmund Advice */}
      <DrSigmundAdvice />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Client Risk Distribution</h3>
          <div className="space-y-4">
            {[
              { level: 'Low Risk (70-100)', count: mockClients.filter(c => c.riskScore >= 70).length, color: 'bg-green-500', amount: mockClients.filter(c => c.riskScore >= 70).reduce((sum, c) => sum + c.totalOutstanding, 0), percentage: Math.round((mockClients.filter(c => c.riskScore >= 70).length / mockClients.length) * 100) },
              { level: 'Medium Risk (40-69)', count: mockClients.filter(c => c.riskScore >= 40 && c.riskScore < 70).length, color: 'bg-yellow-500', amount: mockClients.filter(c => c.riskScore >= 40 && c.riskScore < 70).reduce((sum, c) => sum + c.totalOutstanding, 0), percentage: Math.round((mockClients.filter(c => c.riskScore >= 40 && c.riskScore < 70).length / mockClients.length) * 100) },
              { level: 'High Risk (0-39)', count: mockClients.filter(c => c.riskScore < 40).length, color: 'bg-red-500', amount: mockClients.filter(c => c.riskScore < 40).reduce((sum, c) => sum + c.totalOutstanding, 0), percentage: Math.round((mockClients.filter(c => c.riskScore < 40).length / mockClients.length) * 100) }
            ].map((risk, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded ${risk.color}`}></div>
                    <span className="text-sm font-medium text-gray-700">{risk.level}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">{risk.count} clients ({risk.percentage}%)</p>
                    <p className="text-xs text-gray-500">€{risk.amount.toLocaleString()}</p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className={`h-2 rounded-full ${risk.color}`} style={{ width: `${risk.percentage}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Payment Trends Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Trends (Last 6 Months)</h3>
          <div className="space-y-4">
            {/* Average Payment Days Trend */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-700">Average Payment Days</p>
                <p className="text-2xl font-bold text-gray-900">42 days</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-red-600">↗ +5 days</p>
                <p className="text-xs text-gray-500">vs last month</p>
              </div>
            </div>
            
            {/* Payment Success Rate */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-700">On-Time Payment Rate</p>
                <p className="text-2xl font-bold text-green-600">78%</p>
              </div>
              <div className="w-16 h-16 relative">
                <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 32 32">
                  <circle cx="16" cy="16" r="12" fill="none" stroke="#e5e7eb" strokeWidth="4"/>
                  <circle cx="16" cy="16" r="12" fill="none" stroke="#10b981" strokeWidth="4" 
                    strokeDasharray={`${78 * 0.75} ${100 * 0.75}`} strokeLinecap="round"/>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-semibold text-green-600">78%</span>
                </div>
              </div>
            </div>

            {/* Collection Effectiveness */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Collection Effectiveness</span>
                <span className="font-medium text-gray-900">85%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '85%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Timeline Visualization */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Payment Timeline</h3>
        <div className="space-y-4">
          {/* Timeline bars showing upcoming payments */}
          {[
            { date: 'Aug 20', client: 'Retail Express', amount: 2000, status: 'critical', days: -2 },
            { date: 'Aug 22', client: 'Creative Studio', amount: 6500, status: 'warning', days: 0 },
            { date: 'Aug 25', client: 'TechFlow Solutions', amount: 4500, status: 'good', days: 3 },
            { date: 'Aug 28', client: 'EuroLogistics', amount: 3200, status: 'good', days: 6 }
          ].map((payment, index) => (
            <div key={index} className="flex items-center space-x-4 p-3 rounded-lg border border-gray-200">
              <div className={`w-3 h-3 rounded-full ${
                payment.status === 'critical' ? 'bg-red-500' : 
                payment.status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
              }`}></div>
              <div className="flex-1 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{payment.client}</p>
                  <p className="text-xs text-gray-500">Due {payment.date} ({payment.days < 0 ? `${Math.abs(payment.days)} days overdue` : payment.days === 0 ? 'Today' : `in ${payment.days} days`})</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">€{payment.amount.toLocaleString()}</p>
                  <div className={`text-xs px-2 py-1 rounded-full ${
                    payment.status === 'critical' ? 'bg-red-100 text-red-700' : 
                    payment.status === 'warning' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {payment.status === 'critical' ? 'Overdue' : payment.status === 'warning' ? 'Due Soon' : 'On Track'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity & Alerts</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-900">Payment 66 days overdue</p>
              <p className="text-xs text-red-700">Retail Express S.à r.l. - €7,800 invoice #INV-2024-0832</p>
              <p className="text-xs text-red-600 mt-1">Consider collection action</p>
            </div>
            <span className="text-xs text-red-600">Critical</span>
          </div>

          <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <Clock className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-900">Invoice due in 3 days</p>
              <p className="text-xs text-yellow-700">TechFlow Solutions BV - €4,500 invoice #INV-2024-0856</p>
              <p className="text-xs text-yellow-600 mt-1">92% payment probability</p>
            </div>
            <span className="text-xs text-yellow-600">Monitor</span>
          </div>

          <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg border border-green-200">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-green-900">Payment received</p>
              <p className="text-xs text-green-700">EuroLogistics GmbH - €3,200 processed successfully</p>
              <p className="text-xs text-green-600 mt-1">2 days early payment</p>
            </div>
            <span className="text-xs text-green-600">Positive</span>
          </div>
        </div>
      </div>
    </div>
  )

  const InvoicesView = () => {
    const [invoiceFilter, setInvoiceFilter] = useState<'all' | 'pending' | 'overdue' | 'paid' | 'disputed'>('all')
    const [sortBy, setSortBy] = useState<'dueDate' | 'amount' | 'client' | 'status'>('dueDate')
    
    const filteredInvoices = mockInvoices.filter(invoice => {
      if (invoiceFilter === 'all') return true
      return invoice.status === invoiceFilter
    }).sort((a, b) => {
      switch (sortBy) {
        case 'dueDate': return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
        case 'amount': return b.amount - a.amount
        case 'client': return a.client.localeCompare(b.client)
        case 'status': return a.status.localeCompare(b.status)
        default: return 0
      }
    })

    return (
      <div className="space-y-6">
        {/* Invoice Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Invoices</p>
                <p className="text-2xl font-bold text-gray-900">{mockInvoices.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-blue-600">{mockInvoices.filter(i => i.status === 'pending').length}</p>
              </div>
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overdue</p>
                <p className="text-2xl font-bold text-red-600">{mockInvoices.filter(i => i.status === 'overdue').length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900">€{mockInvoices.reduce((sum, i) => sum + i.amount, 0).toLocaleString()}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search invoices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={invoiceFilter}
              onChange={(e) => setInvoiceFilter(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="overdue">Overdue</option>
              <option value="paid">Paid</option>
              <option value="disputed">Disputed</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="dueDate">Sort by Due Date</option>
              <option value="amount">Sort by Amount</option>
              <option value="client">Sort by Client</option>
              <option value="status">Sort by Status</option>
            </select>
          </div>
        </div>

        {/* Invoices Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment Probability</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredInvoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{invoice.id}</div>
                      <div className="text-sm text-gray-500">{invoice.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{invoice.client}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      €{invoice.amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{new Date(invoice.dueDate).toLocaleDateString()}</div>
                      {invoice.daysPastDue > 0 && (
                        <div className="text-xs text-red-600">{invoice.daysPastDue} days overdue</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
                        {invoice.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className={`h-2 rounded-full ${
                              invoice.paymentProbability >= 80 ? 'bg-green-500' :
                              invoice.paymentProbability >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${invoice.paymentProbability}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-900">{invoice.paymentProbability}%</span>
                      </div>
                      {invoice.riskFactors.length > 0 && (
                        <div className="text-xs text-gray-500 mt-1">
                          {invoice.riskFactors.slice(0, 2).join(', ')}
                          {invoice.riskFactors.length > 2 && '...'}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="text-green-600 hover:text-green-900">
                          <Send className="w-4 h-4" />
                        </button>
                        <button className="text-gray-400 hover:text-gray-600">
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Invoice Actions */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Bulk Actions</h3>
          <div className="flex flex-wrap gap-3">
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
              <Send className="w-4 h-4" />
              <span>Send Reminders</span>
            </button>
            <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
              <CheckCircle className="w-4 h-4" />
              <span>Mark as Paid</span>
            </button>
            <button className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors flex items-center space-x-2">
              <Edit className="w-4 h-4" />
              <span>Update Terms</span>
            </button>
            <button className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2">
              <Download className="w-4 h-4" />
              <span>Export Report</span>
            </button>
          </div>
        </div>
      </div>
    )
  }

  const ClientsView = () => (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search clients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Risk Levels</option>
            <option value="low">Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
          </select>
        </div>
      </div>

      {/* Clients Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Outstanding</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Overdue</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Payment</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredClients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span className="text-sm font-semibold text-blue-600">
                          {client.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{client.name}</div>
                        <div className="text-sm text-gray-500">{client.contact}</div>
                        <div className="text-xs text-gray-400">{client.location}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm font-semibold text-gray-900">{client.riskScore}</span>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskColor(client.riskLevel)}`}>
                        {client.riskLevel}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    €{client.totalOutstanding.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {client.overdue > 0 ? (
                      <span className="text-sm font-medium text-red-600">€{client.overdue.toLocaleString()}</span>
                    ) : (
                      <span className="text-sm text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {client.avgPaymentDays} days
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => setSelectedClient(client.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="text-gray-400 hover:text-gray-600">
                        <Phone className="w-4 h-4" />
                      </button>
                      <button className="text-gray-400 hover:text-gray-600">
                        <Mail className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )

  const PredictionsView = () => {
    const [predictionTimeframe, setPredictionTimeframe] = useState<'30' | '60' | '90'>('30')
    const [modelType, setModelType] = useState<'ensemble' | 'neural' | 'statistical'>('ensemble')
    
    // Mock prediction data
    const predictionData = {
      '30': {
        totalExpected: 42150,
        totalInvoices: 8,
        onTimePayments: 6,
        latePayments: 2,
        confidenceScore: 92,
        riskFactors: ['Retail Express payment delay', 'Economic uncertainty in Luxembourg'],
        cashFlowPrediction: [
          { week: 'Week 1', expected: 12500, confidence: 95, invoices: ['TechFlow Solutions'] },
          { week: 'Week 2', expected: 8750, confidence: 78, invoices: ['Creative Studio'] },
          { week: 'Week 3', expected: 15600, confidence: 45, invoices: ['Retail Express'] },
          { week: 'Week 4', expected: 5300, confidence: 88, invoices: ['EuroLogistics'] }
        ]
      },
      '60': {
        totalExpected: 68200,
        totalInvoices: 12,
        onTimePayments: 9,
        latePayments: 3,
        confidenceScore: 85,
        riskFactors: ['Market volatility', 'Seasonal payment patterns'],
        cashFlowPrediction: [
          { week: 'Weeks 1-2', expected: 21250, confidence: 90, invoices: ['Multiple clients'] },
          { week: 'Weeks 3-4', expected: 23850, confidence: 72, invoices: ['Mixed reliability'] },
          { week: 'Weeks 5-6', expected: 12400, confidence: 68, invoices: ['New projects'] },
          { week: 'Weeks 7-8', expected: 10700, confidence: 81, invoices: ['Recurring clients'] }
        ]
      },
      '90': {
        totalExpected: 95600,
        totalInvoices: 18,
        onTimePayments: 13,
        latePayments: 5,
        confidenceScore: 78,
        riskFactors: ['Economic downturn risk', 'Client industry changes'],
        cashFlowPrediction: [
          { week: 'Month 1', expected: 42150, confidence: 85, invoices: ['Current pipeline'] },
          { week: 'Month 2', expected: 28450, confidence: 65, invoices: ['Projected work'] },
          { week: 'Month 3', expected: 25000, confidence: 55, invoices: ['New opportunities'] }
        ]
      }
    }

    const currentPrediction = predictionData[predictionTimeframe]

    return (
      <div className="space-y-6">
        {/* Prediction Controls */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Payment Predictions</h3>
              <p className="text-sm text-gray-600">Advanced forecasting using ensemble ML models</p>
            </div>
            <div className="flex gap-3">
              <select
                value={predictionTimeframe}
                onChange={(e) => setPredictionTimeframe(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="30">Next 30 Days</option>
                <option value="60">Next 60 Days</option>
                <option value="90">Next 90 Days</option>
              </select>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ensemble">Ensemble Model</option>
                <option value="neural">Neural Network</option>
                <option value="statistical">Statistical Model</option>
              </select>
            </div>
          </div>
        </div>

        {/* Prediction Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Expected Revenue</p>
                <p className="text-2xl font-bold text-green-600">€{currentPrediction.totalExpected.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{currentPrediction.totalInvoices} invoices</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">On-Time Payments</p>
                <p className="text-2xl font-bold text-blue-600">{currentPrediction.onTimePayments}</p>
                <p className="text-xs text-gray-500 mt-1">{Math.round((currentPrediction.onTimePayments/currentPrediction.totalInvoices)*100)}% expected</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Late Payments</p>
                <p className="text-2xl font-bold text-red-600">{currentPrediction.latePayments}</p>
                <p className="text-xs text-gray-500 mt-1">{Math.round((currentPrediction.latePayments/currentPrediction.totalInvoices)*100)}% risk</p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Model Confidence</p>
                <p className="text-2xl font-bold text-purple-600">{currentPrediction.confidenceScore}%</p>
                <p className="text-xs text-gray-500 mt-1">{modelType} model</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Target className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Cash Flow Timeline Prediction */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Predicted Cash Flow Timeline</h3>
          <div className="space-y-4">
            {currentPrediction.cashFlowPrediction.map((period, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 font-semibold">{index + 1}</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{period.week}</h4>
                    <p className="text-sm text-gray-600">{period.invoices.join(', ')}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-gray-900">€{period.expected.toLocaleString()}</p>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          period.confidence >= 80 ? 'bg-green-500' :
                          period.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${period.confidence}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500">{period.confidence}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Performance & Risk Factors */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Model Performance */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Accuracy (Last 30 days)</span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '94%' }}></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">94%</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Precision</span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '91%' }}></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">91%</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Recall</span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: '89%' }}></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">89%</span>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-2">Model Features:</p>
                <div className="flex flex-wrap gap-1">
                  {['Payment History', 'Client Risk Score', 'Invoice Amount', 'Industry Trends', 'Economic Indicators'].map((feature, index) => (
                    <span key={index} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Risk Factors */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Identified Risk Factors</h3>
            <div className="space-y-3">
              {currentPrediction.riskFactors.map((factor, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-yellow-900">{factor}</p>
                    <p className="text-xs text-yellow-700 mt-1">
                      {index === 0 ? 'High impact on payment probability' : 'Moderate impact on cash flow timing'}
                    </p>
                  </div>
                </div>
              ))}
              
              <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-900">Strong Client Relationships</p>
                  <p className="text-xs text-green-700 mt-1">TechFlow and EuroLogistics show consistent payment patterns</p>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Recommendation Actions:</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• Follow up with Retail Express within 5 days</li>
                <li>• Consider offering early payment discounts</li>
                <li>• Implement automated payment reminders</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Dr. Sigmund AI Insights */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
          <div className="flex items-start space-x-4">
            <DrSigmundSpendAvatar size="sm" mood="analytical" />
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-semibold text-purple-900">AI Payment Psychology Insights</h3>
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">Predictive Analysis</span>
              </div>
              <div className="space-y-3 text-sm text-purple-800">
                <p>
                  Based on payment behavior patterns, I predict Retail Express is experiencing cash flow stress. 
                  Their delayed payments correlate with month-end cycles, suggesting they're managing limited liquidity.
                </p>
                <p>
                  <strong>Therapeutic Approach:</strong> Rather than aggressive collection, consider offering a structured 
                  payment plan. This maintains the relationship while securing payment commitment.
                </p>
                <div className="bg-white/60 rounded-lg p-3 mt-3">
                  <p className="font-medium text-purple-900 mb-1">Predicted Client Emotions:</p>
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">Retail Express: Stressed</span>
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">TechFlow: Confident</span>
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">Creative Studio: Uncertain</span>
                  </div>
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
          <h1 className="text-2xl font-bold text-gray-900">Invoice & Client Risk Management</h1>
          <p className="text-gray-600 mt-1">Monitor client payment patterns, predict risks, and optimize cash flow</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
            <Send className="w-4 h-4" />
            <span>Send Reminders</span>
          </button>
          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2">
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'clients', label: 'Clients', icon: Users },
          { id: 'invoices', label: 'Invoices', icon: FileText },
          { id: 'predictions', label: 'Predictions', icon: TrendingUp }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setViewMode(tab.id as any)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
              viewMode === tab.id
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
      {viewMode === 'overview' && <OverviewView />}
      {viewMode === 'clients' && <ClientsView />}
      {viewMode === 'invoices' && <InvoicesView />}
      {viewMode === 'predictions' && <PredictionsView />}

      {/* Client Detail Modal */}
      {selectedClient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Client Details</h2>
                <button 
                  onClick={() => setSelectedClient(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <XCircle className="w-5 h-5 text-gray-500" />
                </button>
              </div>
              
              {(() => {
                const client = mockClients.find(c => c.id === selectedClient)
                if (!client) return null
                
                return (
                  <div className="space-y-6">
                    {/* Client Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
                          <span className="text-xl font-bold text-blue-600">
                            {client.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                          </span>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{client.name}</h3>
                          <p className="text-gray-600">{client.contact}</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span className="flex items-center space-x-1">
                              <Mail className="w-4 h-4" />
                              <span>{client.email}</span>
                            </span>
                            <span className="flex items-center space-x-1">
                              <Phone className="w-4 h-4" />
                              <span>{client.phone}</span>
                            </span>
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-4 h-4" />
                              <span>{client.location}</span>
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-2xl font-bold text-gray-900">{client.riskScore}</span>
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(client.riskLevel)}`}>
                            {client.riskLevel} risk
                          </span>
                        </div>
                        <p className="text-sm text-gray-500">Risk Score</p>
                      </div>
                    </div>

                    {/* Client Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-medium text-gray-600">Total Outstanding</p>
                        <p className="text-xl font-bold text-gray-900">€{client.totalOutstanding.toLocaleString()}</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-medium text-gray-600">Overdue Amount</p>
                        <p className="text-xl font-bold text-red-600">€{client.overdue.toLocaleString()}</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-medium text-gray-600">Avg Payment Days</p>
                        <p className="text-xl font-bold text-gray-900">{client.avgPaymentDays}</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-medium text-gray-600">Relationship</p>
                        <p className="text-xl font-bold text-gray-900">{client.relationshipDuration}</p>
                      </div>
                    </div>

                    {/* Payment History Chart */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-4">Payment History (Last 6 Months)</h4>
                      <div className="flex items-end space-x-2 h-32">
                        {client.paymentHistory.map((days, index) => (
                          <div key={index} className="flex-1 flex flex-col items-center">
                            <div 
                              className="w-full bg-blue-500 rounded-t"
                              style={{ height: `${(days / 100) * 100}%` }}
                            ></div>
                            <span className="text-xs text-gray-500 mt-1">{days}d</span>
                          </div>
                        ))}
                      </div>
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