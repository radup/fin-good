'use client'

import { useState } from 'react'
import { 
  Calculator,
  TrendingUp,
  DollarSign,
  Building2,
  Users,
  MapPin,
  AlertCircle,
  CheckCircle,
  Euro,
  FileText,
  BarChart3,
  PieChart,
  ArrowRight,
  Info,
  Globe,
  Briefcase
} from 'lucide-react'

interface TaxStrategy {
  id: string
  name: string
  jurisdiction: 'BE' | 'LU' | 'EU'
  category: 'structure' | 'timing' | 'deduction' | 'cross_border'
  estimatedSavings: number
  complexity: 'low' | 'medium' | 'high'
  description: string
  requirements: string[]
  timeframe: string
}

export default function TaxOptimizationDashboard() {
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<'BE' | 'LU' | 'EU'>('BE')
  const [selectedStrategy, setSelectedStrategy] = useState<TaxStrategy | null>(null)
  const [businessType, setBusinessType] = useState<'individual' | 'company'>('individual')

  const beneluxStrategies: TaxStrategy[] = [
    {
      id: 'be-professional-vs-company',
      name: 'Independent Professional vs BVBA/SRL',
      jurisdiction: 'BE',
      category: 'structure',
      estimatedSavings: 8500,
      complexity: 'high',
      description: 'Compare tax efficiency between independent professional status and incorporating as BVBA/SRL',
      requirements: ['Annual revenue > €25,000', 'Professional activity', 'Belgian tax residency'],
      timeframe: '2-3 months'
    },
    {
      id: 'be-expense-optimization',
      name: 'Business Expense Optimization',
      jurisdiction: 'BE',
      category: 'deduction',
      estimatedSavings: 3200,
      complexity: 'medium',
      description: 'Maximize deductions for home office, training, car, and meal expenses under Belgian tax law',
      requirements: ['Proper documentation', 'Business justification', 'Expense tracking'],
      timeframe: 'Immediate'
    },
    {
      id: 'be-vat-optimization',
      name: 'VAT Rate Optimization',
      jurisdiction: 'BE',
      category: 'timing',
      estimatedSavings: 2800,
      complexity: 'medium',
      description: 'Optimize between 21% standard rate and 6%/12% reduced rates for eligible services',
      requirements: ['Service classification review', 'Customer base analysis'],
      timeframe: '1-2 weeks'
    },
    {
      id: 'lu-cross-border',
      name: 'Cross-Border Tax Optimization',
      jurisdiction: 'LU',
      category: 'cross_border',
      estimatedSavings: 12000,
      complexity: 'high',
      description: 'Optimize tax efficiency across Belgium, Luxembourg, France, and Germany borders',
      requirements: ['Multi-country income', 'EU citizenship/residency', 'Professional mobility'],
      timeframe: '3-6 months'
    },
    {
      id: 'lu-holding-benefits',
      name: 'Luxembourg Holding Company',
      jurisdiction: 'LU',
      category: 'structure',
      estimatedSavings: 25000,
      complexity: 'high',
      description: 'Leverage EU directive advantages for investment income and capital gains',
      requirements: ['Investment portfolio > €100,000', 'Substance requirements', 'Professional advice'],
      timeframe: '4-6 months'
    },
    {
      id: 'eu-mobility-planning',
      name: 'EU Digital Nomad Tax Planning',
      jurisdiction: 'EU',
      category: 'cross_border',
      estimatedSavings: 15000,
      complexity: 'high',
      description: 'Tax-efficient residency and work location strategies within the EU',
      requirements: ['Digital work capability', 'EU citizenship', 'Flexible business structure'],
      timeframe: '6-12 months'
    }
  ]

  const vatRates = {
    BE: {
      standard: 21,
      reduced1: 12,
      reduced2: 6,
      examples: {
        standard: ['Professional services', 'Consulting', 'Software development'],
        reduced1: ['Social housing', 'Restaurant services'],
        reduced2: ['Books', 'Newspapers', 'Medicine']
      }
    },
    LU: {
      standard: 17,
      reduced1: 14,
      reduced2: 8,
      super_reduced: 3,
      examples: {
        standard: ['General services', 'Digital products'],
        reduced1: ['Energy', 'Heating'],
        reduced2: ['Tourism', 'Cultural services'],
        super_reduced: ['Food', 'Books', 'Medicine']
      }
    }
  }

  const currentStrategies = beneluxStrategies.filter(s => 
    selectedJurisdiction === 'EU' ? true : s.jurisdiction === selectedJurisdiction
  )

  const totalPotentialSavings = currentStrategies.reduce((sum, strategy) => sum + strategy.estimatedSavings, 0)

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-medium mb-2">Multi-Jurisdiction Tax Optimization</h1>
            <p className="text-purple-100">Benelux-focused tax planning with EU expansion strategies</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-purple-100">Potential Annual Savings</div>
            <div className="text-3xl font-medium">€{totalPotentialSavings.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Jurisdiction Selector */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <MapPin className="h-5 w-5 text-purple-600" />
          Tax Jurisdiction Focus
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {(['BE', 'LU', 'EU'] as const).map((jurisdiction) => (
            <button
              key={jurisdiction}
              onClick={() => setSelectedJurisdiction(jurisdiction)}
              className={`p-4 rounded-2xl border-2 transition-all ${
                selectedJurisdiction === jurisdiction
                  ? 'border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50 text-purple-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                {jurisdiction === 'BE' && (
                  <div className="w-6 h-4 rounded-sm overflow-hidden border border-gray-300">
                    <div className="flex h-full">
                      <div className="w-1/3 bg-black"></div>
                      <div className="w-1/3 bg-yellow-400"></div>
                      <div className="w-1/3 bg-red-600"></div>
                    </div>
                  </div>
                )}
                {jurisdiction === 'LU' && (
                  <div className="w-6 h-4 rounded-sm overflow-hidden border border-gray-300">
                    <div className="flex flex-col h-full">
                      <div className="h-1/3 bg-red-600"></div>
                      <div className="h-1/3 bg-white"></div>
                      <div className="h-1/3 bg-cyan-400"></div>
                    </div>
                  </div>
                )}
                {jurisdiction === 'EU' && (
                  <div className="w-6 h-4 rounded-sm overflow-hidden border border-gray-300 bg-blue-600 relative flex items-center justify-center">
                    <div className="text-yellow-400 text-xs font-medium">★</div>
                  </div>
                )}
                <span className="font-medium">
                  {jurisdiction === 'BE' ? 'Belgium' : jurisdiction === 'LU' ? 'Luxembourg' : 'EU-Wide'}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {jurisdiction === 'BE' && 'BVBA/SRL, VAT optimization'}
                {jurisdiction === 'LU' && 'Holding structures, cross-border'}
                {jurisdiction === 'EU' && 'Digital nomad, mobility planning'}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Business Type Selector */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-purple-600" />
          Business Structure
        </h2>
        <div className="grid grid-cols-2 gap-4">
          {(['individual', 'company'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setBusinessType(type)}
              className={`p-4 rounded-2xl border-2 transition-all ${
                businessType === type
                  ? 'border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50 text-purple-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                {type === 'individual' ? <Users className="h-5 w-5" /> : <Building2 className="h-5 w-5" />}
                <span className="font-medium">
                  {type === 'individual' ? 'Independent Professional' : 'Company (BVBA/SRL)'}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {type === 'individual' 
                  ? 'Freelancer, consultant, sole proprietor'
                  : 'BVBA, SRL, SARL corporate structure'
                }
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* VAT Calculator */}
      {(selectedJurisdiction === 'BE' || selectedJurisdiction === 'LU') && (
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Calculator className="h-5 w-5 text-purple-600" />
            VAT Rate Calculator - {selectedJurisdiction === 'BE' ? 'Belgium' : 'Luxembourg'}
          </h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Available VAT Rates</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                  <span className="font-medium">Standard Rate</span>
                  <span className="text-lg font-medium text-red-600">
                    {vatRates[selectedJurisdiction].standard}%
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                  <span className="font-medium">Reduced Rate 1</span>
                  <span className="text-lg font-medium text-orange-600">
                    {vatRates[selectedJurisdiction].reduced1}%
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                  <span className="font-medium">Reduced Rate 2</span>
                  <span className="text-lg font-medium text-green-600">
                    {vatRates[selectedJurisdiction].reduced2}%
                  </span>
                </div>
                {selectedJurisdiction === 'LU' && (
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                    <span className="font-medium">Super Reduced</span>
                    <span className="text-lg font-medium text-blue-600">
                      {vatRates[selectedJurisdiction].super_reduced}%
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Service Examples</h3>
              <div className="space-y-3 text-sm">
                <div className="p-4 bg-gradient-to-r from-red-50 to-red-100 border border-red-200 rounded-xl">
                  <div className="font-medium text-red-800">Standard ({vatRates[selectedJurisdiction].standard}%)</div>
                  <div className="text-red-600 text-sm">
                    {vatRates[selectedJurisdiction].examples.standard.join(', ')}
                  </div>
                </div>
                <div className="p-4 bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200 rounded-xl">
                  <div className="font-medium text-orange-800">Reduced 1 ({vatRates[selectedJurisdiction].reduced1}%)</div>
                  <div className="text-orange-600 text-sm">
                    {vatRates[selectedJurisdiction].examples.reduced1.join(', ')}
                  </div>
                </div>
                <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 border border-green-200 rounded-xl">
                  <div className="font-medium text-green-800">Reduced 2 ({vatRates[selectedJurisdiction].reduced2}%)</div>
                  <div className="text-green-600 text-sm">
                    {vatRates[selectedJurisdiction].examples.reduced2.join(', ')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tax Strategies */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-purple-600" />
          Available Tax Strategies
        </h2>
        <div className="grid gap-4">
          {currentStrategies.map((strategy) => (
            <div
              key={strategy.id}
              className={`border-2 rounded-2xl p-4 cursor-pointer transition-all shadow-sm hover:shadow-md ${
                selectedStrategy?.id === strategy.id
                  ? 'border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedStrategy(strategy)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium text-gray-900">{strategy.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      strategy.complexity === 'low' 
                        ? 'bg-green-100 text-green-800'
                        : strategy.complexity === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {strategy.complexity} complexity
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {strategy.jurisdiction}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{strategy.description}</p>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1 text-green-600">
                      <Euro className="h-4 w-4" />
                      <span className="font-medium">€{strategy.estimatedSavings.toLocaleString()}/year</span>
                    </div>
                    <div className="flex items-center gap-1 text-blue-600">
                      <FileText className="h-4 w-4" />
                      <span>{strategy.timeframe}</span>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-gray-400 mt-2" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Details */}
      {selectedStrategy && (
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Info className="h-5 w-5 text-purple-600" />
            Strategy Details: {selectedStrategy.name}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Requirements</h3>
              <div className="space-y-2">
                {selectedStrategy.requirements.map((requirement, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{requirement}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Implementation Timeline</h3>
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="h-4 w-4 text-purple-600" />
                  <span className="font-medium text-purple-800">Expected Timeline</span>
                </div>
                <div className="text-2xl font-medium text-purple-900 mb-1">{selectedStrategy.timeframe}</div>
                <div className="text-sm text-purple-700">
                  Estimated annual savings: €{selectedStrategy.estimatedSavings.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-2xl">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <div className="font-medium text-yellow-800">Professional Consultation Recommended</div>
                <div className="text-sm text-yellow-700 mt-1">
                  This strategy involves complex tax regulations. Consider consulting with a qualified tax professional 
                  in {selectedStrategy.jurisdiction === 'BE' ? 'Belgium' : selectedStrategy.jurisdiction === 'LU' ? 'Luxembourg' : 'your target jurisdiction'} 
                  before implementation.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dr. Sigmund Tax Therapy Section */}
      <div className="mt-12 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
        <div className="flex items-start gap-6">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <Calculator className="h-8 w-8 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Dr. Sigmund's Tax Therapy Corner</h2>
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-6">
              <h3 className="font-medium text-purple-900 mb-3">Tax Anxiety Relief Tips</h3>
              <ul className="space-y-2 text-sm text-purple-800">
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Remember: tax optimization is about making informed, legal choices to minimize your burden</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Start with simple strategies (expense optimization) before considering complex structures</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Always consult with a qualified tax professional for high-complexity strategies</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Focus on long-term financial health, not just immediate tax savings</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-medium text-yellow-900 mb-2">Important Disclaimer</h3>
            <p className="text-sm text-yellow-800 leading-relaxed">
              This tool provides general information and estimates for educational purposes only. Tax laws are complex and change frequently. 
              Always consult with qualified tax professionals in Belgium, Luxembourg, or your target jurisdiction before implementing any tax strategy. 
              Spend's Analysis and Dr. Sigmund Spend do not provide professional tax advice.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}