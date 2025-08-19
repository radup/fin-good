import { BudgetAnalysis } from '@/components/BudgetAnalysis'

export default function BudgetAnalysisDemoPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Budget Analysis Demo</h1>
          <p className="text-gray-600 mt-2">
            Experience comprehensive budget vs actual analysis with AI-powered recommendations and variance tracking.
          </p>
        </div>
        
        <BudgetAnalysis />
      </div>
    </div>
  )
}
