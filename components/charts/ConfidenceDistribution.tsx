'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

interface ConfidenceDistributionProps {
  data?: any[]
  className?: string
}

const mockData = [
  { range: '90-100%', count: 1250, percentage: 25, color: '#10b981' },
  { range: '80-89%', count: 1800, percentage: 36, color: '#3b82f6' },
  { range: '70-79%', count: 950, percentage: 19, color: '#f59e0b' },
  { range: '60-69%', count: 600, percentage: 12, color: '#ef4444' },
  { range: '50-59%', count: 250, percentage: 5, color: '#8b5cf6' },
  { range: '0-49%', count: 150, percentage: 3, color: '#6b7280' }
]

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280']

export default function ConfidenceDistribution({ data = mockData, className = '' }: ConfidenceDistributionProps) {
  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  const formatPercentage = (value: number) => {
    return `${value}%`
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">Confidence: {label}</p>
          <p className="text-sm" style={{ color: data.color }}>
            Transactions: {formatNumber(data.value)}
          </p>
          <p className="text-sm text-gray-600">
            Percentage: {data.payload.percentage}%
          </p>
        </div>
      )
    }
    return null
  }

  const totalTransactions = data.reduce((sum, item) => sum + item.count, 0)
  const averageConfidence = data.reduce((sum, item) => {
    const midPoint = parseInt(item.range.split('-')[0]) + (parseInt(item.range.split('-')[1].replace('%', '')) - parseInt(item.range.split('-')[0])) / 2
    return sum + (midPoint * item.count)
  }, 0) / totalTransactions

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Confidence Distribution</h3>
        <p className="text-sm text-gray-600">Distribution of AI confidence scores across transactions</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="h-64">
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
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Pie Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ percentage }) => `${percentage}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="percentage"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-gray-600">Total Transactions</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatNumber(totalTransactions)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Average Confidence</p>
          <p className="text-lg font-semibold text-blue-600">
            {formatPercentage(averageConfidence.toFixed(1))}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">High Confidence (>80%)</p>
          <p className="text-lg font-semibold text-green-600">
            {formatPercentage(((data[0].count + data[1].count) / totalTransactions * 100).toFixed(1))}
          </p>
        </div>
      </div>
      
      {/* Confidence Levels Breakdown */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Confidence Levels</h4>
        <div className="space-y-2">
          {data.map((item, index) => (
            <div key={item.range} className="flex items-center justify-between">
              <div className="flex items-center">
                <div 
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm text-gray-700">{item.range}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {formatNumber(item.count)}
                </p>
                <p className="text-xs text-gray-500">
                  {formatPercentage(item.percentage)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Quality Indicators */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Quality Indicators</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-600">Excellent (>90%)</p>
            <p className="text-sm font-medium text-green-600">
              {formatNumber(data[0].count)} transactions
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Good (80-89%)</p>
            <p className="text-sm font-medium text-blue-600">
              {formatNumber(data[1].count)} transactions
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Needs Review (<70%)</p>
            <p className="text-sm font-medium text-red-600">
              {formatNumber(data.slice(3).reduce((sum, item) => sum + item.count, 0))} transactions
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Overall Quality</p>
            <p className="text-sm font-medium text-green-600">Excellent</p>
          </div>
        </div>
      </div>
    </div>
  )
}
