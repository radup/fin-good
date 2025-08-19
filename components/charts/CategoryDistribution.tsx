'use client'

import React from 'react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts'

interface CategoryDistributionProps {
  data?: any[]
  className?: string
}

const mockData = [
  { name: 'Food & Dining', value: 2400, color: '#3b82f6' },
  { name: 'Transportation', value: 1398, color: '#10b981' },
  { name: 'Shopping', value: 9800, color: '#f59e0b' },
  { name: 'Entertainment', value: 3908, color: '#ef4444' },
  { name: 'Healthcare', value: 4800, color: '#8b5cf6' },
  { name: 'Utilities', value: 3800, color: '#06b6d4' },
  { name: 'Other', value: 4300, color: '#84cc16' }
]

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16']

export default function CategoryDistribution({ data = mockData, className = '' }: CategoryDistributionProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatPercentage = (value: number, total: number) => {
    return `${((value / total) * 100).toFixed(1)}%`
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      const total = mockData.reduce((sum, item) => sum + item.value, 0)
      const percentage = ((data.value / total) * 100).toFixed(1)
      
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm" style={{ color: data.color }}>
            Amount: {formatCurrency(data.value)}
          </p>
          <p className="text-sm text-gray-600">
            Percentage: {percentage}%
          </p>
        </div>
      )
    }
    return null
  }

  const total = data.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Category Distribution</h3>
        <p className="text-sm text-gray-600">See how your spending is distributed across categories</p>
      </div>
      
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Spending</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(total)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Categories</p>
            <p className="text-lg font-semibold text-gray-900">
              {data.length}
            </p>
          </div>
        </div>
        
        <div className="mt-4 space-y-2">
          {data.slice(0, 5).map((item, index) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center">
                <div 
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm text-gray-700">{item.name}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {formatCurrency(item.value)}
                </p>
                <p className="text-xs text-gray-500">
                  {formatPercentage(item.value, total)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
