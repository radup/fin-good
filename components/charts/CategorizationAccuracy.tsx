'use client'

import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts'

interface CategorizationAccuracyProps {
  data?: any[]
  className?: string
}

const mockData = [
  { month: 'Jan', accuracy: 85, confidence: 78, transactions: 1200 },
  { month: 'Feb', accuracy: 87, confidence: 82, transactions: 1350 },
  { month: 'Mar', accuracy: 89, confidence: 85, transactions: 1100 },
  { month: 'Apr', accuracy: 91, confidence: 88, transactions: 1400 },
  { month: 'May', accuracy: 88, confidence: 84, transactions: 1250 },
  { month: 'Jun', accuracy: 92, confidence: 90, transactions: 1600 },
  { month: 'Jul', accuracy: 94, confidence: 92, transactions: 1450 },
  { month: 'Aug', accuracy: 93, confidence: 91, transactions: 1300 },
  { month: 'Sep', accuracy: 95, confidence: 93, transactions: 1550 },
  { month: 'Oct', accuracy: 96, confidence: 94, transactions: 1700 },
  { month: 'Nov', accuracy: 97, confidence: 95, transactions: 1650 },
  { month: 'Dec', accuracy: 98, confidence: 96, transactions: 1800 }
]

export default function CategorizationAccuracy({ data = mockData, className = '' }: CategorizationAccuracyProps) {
  const formatPercentage = (value: number) => {
    return `${value}%`
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {entry.name === 'transactions' ? formatNumber(entry.value) : formatPercentage(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const averageAccuracy = data.reduce((sum, item) => sum + item.accuracy, 0) / data.length
  const averageConfidence = data.reduce((sum, item) => sum + item.confidence, 0) / data.length
  const totalTransactions = data.reduce((sum, item) => sum + item.transactions, 0)

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Categorization Accuracy</h3>
        <p className="text-sm text-gray-600">Track AI categorization performance over time</p>
      </div>
      
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="month" 
              stroke="#6b7280"
              fontSize={12}
            />
            <YAxis 
              stroke="#6b7280"
              fontSize={12}
              tickFormatter={formatPercentage}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
              name="Accuracy"
            />
            <Line
              type="monotone"
              dataKey="confidence"
              stroke="#10b981"
              strokeWidth={3}
              dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
              name="Confidence"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-gray-600">Average Accuracy</p>
          <p className="text-lg font-semibold text-blue-600">
            {formatPercentage(averageAccuracy.toFixed(1))}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Average Confidence</p>
          <p className="text-lg font-semibold text-green-600">
            {formatPercentage(averageConfidence.toFixed(1))}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Total Transactions</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatNumber(totalTransactions)}
          </p>
        </div>
      </div>
      
      {/* Transaction Volume Chart */}
      <div className="mt-8">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Transaction Volume</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="month" 
                stroke="#6b7280"
                fontSize={10}
              />
              <YAxis 
                stroke="#6b7280"
                fontSize={10}
                tickFormatter={formatNumber}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="transactions" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Performance Indicators */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Performance Indicators</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-600">Trend</p>
            <p className="text-sm font-medium text-green-600">↗ Improving</p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Status</p>
            <p className="text-sm font-medium text-blue-600">Excellent</p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Best Month</p>
            <p className="text-sm font-medium text-gray-900">December (98%)</p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Improvement</p>
            <p className="text-sm font-medium text-green-600">+13%</p>
          </div>
        </div>
      </div>
    </div>
  )
}
