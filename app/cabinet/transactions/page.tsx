'use client'

import { useState, useEffect } from 'react'
import { TransactionTable } from '../../../components/TransactionTable'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { transactionAPI } from '../../../lib/api'

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setIsLoading(true)
        const response = await transactionAPI.getTransactions()
        setTransactions(response.data || [])
      } catch (error) {
        console.error('Failed to fetch transactions:', error)
        setTransactions([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchTransactions()
  }, [])

  return (
    <CabinetPageLayout title="Transactions" description="Manage financial transactions">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <TransactionTable 
            transactions={transactions}
            isLoading={isLoading}
          />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
