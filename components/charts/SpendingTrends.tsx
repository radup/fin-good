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
  Area,
  AreaChart
} from 'recharts'

interface SpendingTrendsProps {
  data?: any[]
  className?: string
}

const mockData = [
  { month: 'Jan', spending: 2400, income: 4000, net: 1600 },
  { month: 'Feb', spending: 1398, income: 3000, net: 1602 },
  { month: 'Mar', spending: 9800, income: 2000, net: -7800 },
  { month: 'Apr', spending: 3908, income: 2780, net: -1128 },
  { month: 'May', spending: 4800, income: 1890, net: -2910 },
  { month: 'Jun', spending: 3800, income: 2390, net: -1410 },
  { month: 'Jul', spending: 4300, income: 3490, net: -810 },
  { month: 'Aug', spending: 2400, income: 4000, net: 1600 },
  { month: 'Sep', spending: 1398, income: 3000, net: 1602 },
  { month: 'Oct', spending: 9800, income: 2000, net: -7800 },
  { month: 'Nov', spending: 3908, income: 2780, net: -1128 },
  { month: 'Dec', spending: 4800, income: 1890, net: -2910 }
]

export default function SpendingTrends({ data = mockData, className = '' }: SpendingTrendsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Spending Trends</h3>
        <p className="text-sm text-gray-600">Track your spending patterns over time</p>
      </div>
      
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="month" 
              stroke="#6b7280"
              fontSize={12}
            />
            <YAxis 
              stroke="#6b7280"
              fontSize={12}
              tickFormatter={formatCurrency}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="income"
              stackId="1"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.3}
              name="Income"
            />
            <Area
              type="monotone"
              dataKey="spending"
              stackId="1"
              stroke="#ef4444"
              fill="#ef4444"
              fillOpacity={0.3}
              name="Spending"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-gray-600">Total Income</p>
          <p className="text-lg font-semibold text-green-600">
            {formatCurrency(data.reduce((sum, item) => sum + item.income, 0))}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Total Spending</p>
          <p className="text-lg font-semibold text-red-600">
            {formatCurrency(data.reduce((sum, item) => sum + item.spending, 0))}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Net</p>
          <p className={`text-lg font-semibold ${
            data.reduce((sum, item) => sum + item.net, 0) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(data.reduce((sum, item) => sum + item.net, 0))}
          </p>
        </div>
      </div>
    </div>
  )
}
