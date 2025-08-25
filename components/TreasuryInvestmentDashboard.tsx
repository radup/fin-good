'use client'

import { useState } from 'react'
import { 
  TrendingUp,
  DollarSign,
  PieChart,
  BarChart3,
  Shield,
  AlertTriangle,
  CheckCircle,
  Euro,
  Calendar,
  Target,
  ArrowRight,
  Info,
  Briefcase,
  Building,
  CreditCard,
  Percent,
  Clock,
  TrendingDown
} from 'lucide-react'
import DrSigmundAdviceCard from './DrSigmundAdviceCard'

interface InvestmentOption {
  id: string
  name: string
  category: 'conservative' | 'moderate' | 'growth'
  expectedReturn: number
  risk: 'low' | 'medium' | 'high'
  minimumInvestment: number
  liquidity: 'high' | 'medium' | 'low'
  timeHorizon: string
  description: string
  pros: string[]
  cons: string[]
}

interface CashForecast {
  month: string
  projectedIncome: number
  projectedExpenses: number
  netCashFlow: number
  cumulativeCash: number
  surplusAvailable: number
  emergencyReserve: number
}

export default function TreasuryInvestmentDashboard() {
  const [selectedTimeHorizon, setSelectedTimeHorizon] = useState<'3m' | '6m' | '12m' | '24m'>('12m')
  const [riskTolerance, setRiskTolerance] = useState<'conservative' | 'moderate' | 'growth'>('moderate')
  const [selectedInvestment, setSelectedInvestment] = useState<InvestmentOption | null>(null)
  const [emergencyMonths, setEmergencyMonths] = useState<number>(6)

  // Mock cash flow forecast data
  const cashForecast: CashForecast[] = [
    {
      month: 'Jan 2025',
      projectedIncome: 12500,
      projectedExpenses: 8200,
      netCashFlow: 4300,
      cumulativeCash: 45300,
      surplusAvailable: 15300,
      emergencyReserve: 30000
    },
    {
      month: 'Feb 2025',
      projectedIncome: 14200,
      projectedExpenses: 8800,
      netCashFlow: 5400,
      cumulativeCash: 50700,
      surplusAvailable: 20700,
      emergencyReserve: 30000
    },
    {
      month: 'Mar 2025',
      projectedIncome: 13800,
      projectedExpenses: 9100,
      netCashFlow: 4700,
      cumulativeCash: 55400,
      surplusAvailable: 25400,
      emergencyReserve: 30000
    },
    {
      month: 'Apr 2025',
      projectedIncome: 11900,
      projectedExpenses: 8500,
      netCashFlow: 3400,
      cumulativeCash: 58800,
      surplusAvailable: 28800,
      emergencyReserve: 30000
    },
    {
      month: 'May 2025',
      projectedIncome: 15600,
      projectedExpenses: 9300,
      netCashFlow: 6300,
      cumulativeCash: 65100,
      surplusAvailable: 35100,
      emergencyReserve: 30000
    },
    {
      month: 'Jun 2025',
      projectedIncome: 16800,
      projectedExpenses: 9600,
      netCashFlow: 7200,
      cumulativeCash: 72300,
      surplusAvailable: 42300,
      emergencyReserve: 30000
    }
  ]

  const investmentOptions: InvestmentOption[] = [
    {
      id: 'eu-bonds',
      name: 'EU Government Bonds',
      category: 'conservative',
      expectedReturn: 3.2,
      risk: 'low',
      minimumInvestment: 1000,
      liquidity: 'medium',
      timeHorizon: '1-5 years',
      description: 'Stable government bonds from highly-rated EU countries including Germany, Netherlands, and France',
      pros: ['Capital preservation', 'Predictable income', 'Low volatility', 'Tax advantages in some jurisdictions'],
      cons: ['Lower returns', 'Interest rate risk', 'Inflation risk', 'Limited growth potential']
    },
    {
      id: 'eu-corporate-bonds',
      name: 'EU Corporate Bonds',
      category: 'moderate',
      expectedReturn: 4.8,
      risk: 'medium',
      minimumInvestment: 5000,
      liquidity: 'medium',
      timeHorizon: '2-7 years',
      description: 'Investment-grade corporate bonds from established European companies',
      pros: ['Higher yields than government bonds', 'Diversification', 'Regular income', 'Currency stability'],
      cons: ['Credit risk', 'Interest rate sensitivity', 'Market volatility', 'Liquidity constraints']
    },
    {
      id: 'etf-portfolio',
      name: 'Diversified EU ETF Portfolio',
      category: 'moderate',
      expectedReturn: 6.5,
      risk: 'medium',
      minimumInvestment: 500,
      liquidity: 'high',
      timeHorizon: '3-10 years',
      description: 'Broad market exposure through low-cost European ETFs covering multiple sectors and countries',
      pros: ['Diversification', 'Low fees', 'High liquidity', 'Professional management', 'Tax efficiency'],
      cons: ['Market risk', 'Volatility', 'No guaranteed returns', 'Currency exposure']
    },
    {
      id: 'growth-stocks',
      name: 'EU Growth Stocks',
      category: 'growth',
      expectedReturn: 8.2,
      risk: 'high',
      minimumInvestment: 2000,
      liquidity: 'high',
      timeHorizon: '5-15 years',
      description: 'High-growth potential stocks from emerging and established European companies',
      pros: ['High growth potential', 'Inflation hedge', 'Liquidity', 'Dividend potential'],
      cons: ['High volatility', 'Market risk', 'Individual company risk', 'Requires research']
    },
    {
      id: 'money-market',
      name: 'EU Money Market Funds',
      category: 'conservative',
      expectedReturn: 2.1,
      risk: 'low',
      minimumInvestment: 100,
      liquidity: 'high',
      timeHorizon: '0-1 years',
      description: 'Short-term, high-quality debt instruments for maximum liquidity and capital preservation',
      pros: ['Maximum liquidity', 'Capital preservation', 'Low minimum', 'Daily access'],
      cons: ['Very low returns', 'Inflation risk', 'Opportunity cost', 'No growth potential']
    },
    {
      id: 'real-estate-reit',
      name: 'EU Real Estate REITs',
      category: 'moderate',
      expectedReturn: 5.8,
      risk: 'medium',
      minimumInvestment: 1000,
      liquidity: 'medium',
      timeHorizon: '5-15 years',
      description: 'Real Estate Investment Trusts focused on European commercial and residential properties',
      pros: ['Inflation hedge', 'Dividend income', 'Diversification', 'Professional management'],
      cons: ['Interest rate sensitivity', 'Property market risk', 'Lower liquidity', 'Economic sensitivity']
    }
  ]

  const filteredInvestments = investmentOptions.filter(option => 
    riskTolerance === 'conservative' ? option.risk === 'low' :
    riskTolerance === 'moderate' ? ['low', 'medium'].includes(option.risk) :
    true
  )

  const totalSurplus = cashForecast[cashForecast.length - 1]?.surplusAvailable || 0
  const avgMonthlyCashFlow = cashForecast.reduce((sum, month) => sum + month.netCashFlow, 0) / cashForecast.length
  const emergencyFundTarget = emergencyMonths * 5000 // Assuming ~5k monthly expenses

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-medium mb-2">Treasury & Investment Management</h1>
            <p className="text-green-100">Surplus cash forecasting and investment scenario analysis</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-green-100">Available Surplus</div>
            <div className="text-3xl font-medium">€{totalSurplus.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Risk Profile & Emergency Fund Settings */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Target className="h-5 w-5 text-green-600" />
            Risk Profile
          </h2>
          <div className="space-y-3">
            {(['conservative', 'moderate', 'growth'] as const).map((risk) => (
              <button
                key={risk}
                onClick={() => setRiskTolerance(risk)}
                className={`w-full p-4 rounded-2xl border-2 text-left transition-all ${
                  riskTolerance === risk
                    ? 'border-green-500 bg-gradient-to-r from-green-50 to-blue-50 text-green-700'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium capitalize">{risk}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    risk === 'conservative' ? 'bg-green-100 text-green-800' :
                    risk === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {risk === 'conservative' ? 'Low Risk' : risk === 'moderate' ? 'Medium Risk' : 'High Risk'}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {risk === 'conservative' && 'Focus on capital preservation and stability'}
                  {risk === 'moderate' && 'Balanced approach with moderate growth potential'}
                  {risk === 'growth' && 'Higher risk for potentially higher returns'}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-600" />
            Emergency Fund Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Emergency Fund Target (months of expenses)
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="3"
                  max="12"
                  value={emergencyMonths}
                  onChange={(e) => setEmergencyMonths(Number(e.target.value))}
                  className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-lg font-medium text-gray-900 w-8">{emergencyMonths}</span>
              </div>
            </div>
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-800">Emergency Fund Target</span>
              </div>
              <div className="text-2xl font-medium text-green-900">€{emergencyFundTarget.toLocaleString()}</div>
              <div className="text-sm text-green-700">
                {emergencyMonths} months × €5,000 average monthly expenses
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cash Flow Forecast */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-green-600" />
          Surplus Cash Forecast
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left p-3 font-medium text-gray-900">Month</th>
                <th className="text-right p-3 font-medium text-gray-900">Income</th>
                <th className="text-right p-3 font-medium text-gray-900">Expenses</th>
                <th className="text-right p-3 font-medium text-gray-900">Net Cash Flow</th>
                <th className="text-right p-3 font-medium text-gray-900">Cumulative</th>
                <th className="text-right p-3 font-medium text-gray-900">Available Surplus</th>
              </tr>
            </thead>
            <tbody>
              {cashForecast.map((month, index) => (
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-3 font-medium text-gray-900">{month.month}</td>
                  <td className="p-3 text-right text-green-600">€{month.projectedIncome.toLocaleString()}</td>
                  <td className="p-3 text-right text-red-600">€{month.projectedExpenses.toLocaleString()}</td>
                  <td className={`p-3 text-right font-medium ${month.netCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    €{month.netCashFlow.toLocaleString()}
                  </td>
                  <td className="p-3 text-right font-medium text-gray-900">€{month.cumulativeCash.toLocaleString()}</td>
                  <td className="p-3 text-right font-medium text-blue-600">€{month.surplusAvailable.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="bg-gradient-to-r from-green-50 to-green-100 border border-green-200 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="font-medium text-green-800">Avg Monthly Cash Flow</span>
            </div>
            <div className="text-2xl font-medium text-green-900">€{avgMonthlyCashFlow.toLocaleString()}</div>
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="h-4 w-4 text-blue-600" />
              <span className="font-medium text-blue-800">Emergency Reserve</span>
            </div>
            <div className="text-2xl font-medium text-blue-900">€{emergencyFundTarget.toLocaleString()}</div>
          </div>
          
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 border border-purple-200 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Euro className="h-4 w-4 text-purple-600" />
              <span className="font-medium text-purple-800">Available for Investment</span>
            </div>
            <div className="text-2xl font-medium text-purple-900">€{Math.max(0, totalSurplus - emergencyFundTarget).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Investment Options */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <PieChart className="h-5 w-5 text-green-600" />
          Investment Options ({riskTolerance} profile)
        </h2>
        <div className="grid gap-4">
          {filteredInvestments.map((investment) => (
            <div
              key={investment.id}
              className={`border-2 rounded-2xl p-4 cursor-pointer transition-all shadow-sm hover:shadow-md ${
                selectedInvestment?.id === investment.id
                  ? 'border-green-500 bg-gradient-to-r from-green-50 to-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedInvestment(investment)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium text-gray-900">{investment.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      investment.risk === 'low' 
                        ? 'bg-green-100 text-green-800'
                        : investment.risk === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {investment.risk} risk
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {investment.timeHorizon}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{investment.description}</p>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1 text-green-600">
                      <Percent className="h-4 w-4" />
                      <span className="font-medium">{investment.expectedReturn}% expected return</span>
                    </div>
                    <div className="flex items-center gap-1 text-blue-600">
                      <Euro className="h-4 w-4" />
                      <span>Min: €{investment.minimumInvestment.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1 text-purple-600">
                      <Clock className="h-4 w-4" />
                      <span>{investment.liquidity} liquidity</span>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-gray-400 mt-2" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Investment Details */}
      {selectedInvestment && (
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Info className="h-5 w-5 text-green-600" />
            Investment Analysis: {selectedInvestment.name}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-3 text-green-700">Advantages</h3>
              <div className="space-y-2">
                {selectedInvestment.pros.map((pro, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{pro}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-3 text-red-700">Considerations</h3>
              <div className="space-y-2">
                {selectedInvestment.cons.map((con, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{con}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="mt-6 grid md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-r from-green-50 to-green-100 border border-green-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-800">Expected Annual Return</span>
              </div>
              <div className="text-2xl font-medium text-green-900">{selectedInvestment.expectedReturn}%</div>
            </div>
            
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Euro className="h-4 w-4 text-blue-600" />
                <span className="font-medium text-blue-800">Minimum Investment</span>
              </div>
              <div className="text-2xl font-medium text-blue-900">€{selectedInvestment.minimumInvestment.toLocaleString()}</div>
            </div>
            
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 border border-purple-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-purple-600" />
                <span className="font-medium text-purple-800">Liquidity</span>
              </div>
              <div className="text-2xl font-medium text-purple-900 capitalize">{selectedInvestment.liquidity}</div>
            </div>
          </div>
        </div>
      )}

      {/* Dr. Sigmund's Investment Guidance */}
      <DrSigmundAdviceCard
        variant="insights"
        title="Investment Therapy"
        badgeText="Psychology Guide"
        mood="analytical"
        expandableContent={
          <div className="space-y-3">
            <div className="bg-white rounded-xl p-4 border border-violet-200">
              <h3 className="font-medium text-violet-900 mb-2">🎯 Personalized Recommendations</h3>
              <p className="text-sm text-violet-700">Based on your {riskTolerance} risk profile, focus on {riskTolerance === 'conservative' ? 'capital preservation and steady income' : riskTolerance === 'moderate' ? 'balanced growth with managed risk' : 'long-term growth potential with higher volatility tolerance'}.</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-violet-200">
              <h3 className="font-medium text-violet-900 mb-2">⚖️ Balance & Diversification</h3>
              <p className="text-sm text-violet-700">Don't put all surplus cash into one investment. Consider a mix of instruments to spread risk while maintaining some liquidity for unexpected opportunities or needs.</p>
            </div>
          </div>
        }
      >
        <div>
          <h3 className="font-medium text-violet-900 mb-2">💭 Investment Psychology</h3>
          <p className="text-sm text-violet-800">Remember, investing surplus cash should reduce financial anxiety, not create it. Start with your emergency fund, then gradually explore investments that match your comfort level.</p>
        </div>
      </DrSigmundAdviceCard>
    </div>
  )
}