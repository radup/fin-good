'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

interface ConfidenceDistributionProps {
  data?: any[]
  className?: string
}

const mockData = [
  { range: '90-100%', count: 1250, percentage: 25 },
  { range: '80-89%', count: 1800, percentage: 36 },
  { range: '70-79%', count: 950, percentage: 19 },
  { range: '60-69%', count: 600, percentage: 12 },
  { range: '50-59%', count: 250, percentage: 5 },
  { range: '0-49%', count: 150, percentage: 3 }
]

export default function ConfidenceDistribution({ data = mockData, className = '' }: ConfidenceDistributionProps) {
  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  const totalTransactions = data.reduce((sum, item) => sum + item.count, 0)

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Confidence Distribution</h3>
        <p className="text-sm text-gray-600">Distribution of AI confidence scores across transactions</p>
      </div>
      
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="range" 
              stroke="#6b7280"
              fontSize={10}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              stroke="#6b7280"
              fontSize={10}
              tickFormatter={formatNumber}
            />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-gray-600">Total Transactions</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatNumber(totalTransactions)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">High Confidence</p>
          <p className="text-lg font-semibold text-green-600">
            {((data[0].count + data[1].count) / totalTransactions * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Quality Score</p>
          <p className="text-lg font-semibold text-green-600">Excellent</p>
        </div>
      </div>
    </div>
  )
}