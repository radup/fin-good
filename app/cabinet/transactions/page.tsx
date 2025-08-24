'use client'

import { TransactionTable } from '../../../components/TransactionTable'

import CabinetPageLayout from '../../../components/CabinetPageLayout'

export default function TransactionsPage() {
  return (
    <CabinetPageLayout title="Transactions" description="Manage financial transactions">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <TransactionTable />
        </div>
      </div>
    </CabinetPageLayout>
  )
}
