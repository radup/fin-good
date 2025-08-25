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
import { 
  cardClasses, 
  buttonClasses, 
  badgeClasses, 
  cn, 
  gradientClasses, 
  textClasses,
  semantic
} from '../lib/design-utils'
import DrSigmundAdviceCard from './DrSigmundAdviceCard'

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
      <div className={cn(
        gradientClasses('hero'),
        cardClasses('elevated'),
        'p-6 text-white'
      )}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={cn(
              textClasses.size('2xl'),
              textClasses.weight('bold'),
              'mb-2 text-white'
            )}>
              Multi-Jurisdiction Tax Optimization
            </h1>
            <p className="text-brand-accent/80">
              Benelux-focused tax planning with EU expansion strategies
            </p>
          </div>
          <div className="text-right">
            <div className={cn(
              textClasses.size('sm'),
              'text-brand-accent/80 mb-1'
            )}>
              Potential Annual Savings
            </div>
            <div className={cn(
              textClasses.size('3xl'),
              textClasses.weight('bold'),
              'text-white'
            )}>
              €{totalPotentialSavings.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Jurisdiction Selector */}
      <div className={cardClasses('elevated', 'p-6')}>
        <h2 className={cn(
          textClasses.size('lg'),
          textClasses.weight('semibold'),
          semantic.text.primary,
          'mb-6 flex items-center gap-3'
        )}>
          <MapPin className="h-5 w-5 text-brand-primary" />
          Tax Jurisdiction Focus
        </h2>
        <div className="grid grid-cols-3 gap-6">
          {(['BE', 'LU', 'EU'] as const).map((jurisdiction) => (
            <button
              key={jurisdiction}
              onClick={() => setSelectedJurisdiction(jurisdiction)}
              className={cn(
                'p-5 rounded-2xl border-2 transition-all duration-200',
                selectedJurisdiction === jurisdiction
                  ? 'border-brand-primary bg-gradient-to-r from-brand-primary/5 to-brand-accent/10 text-brand-primary-dark shadow-brand'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-brand-primary/30 hover:shadow-md'
              )}
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
                <span className={cn(
                  textClasses.weight('semibold'),
                  selectedJurisdiction === jurisdiction ? 'text-brand-primary' : semantic.text.primary
                )}>
                  {jurisdiction === 'BE' ? 'Belgium' : jurisdiction === 'LU' ? 'Luxembourg' : 'EU-Wide'}
                </span>
              </div>
              <div className={cn(
                textClasses.size('sm'),
                selectedJurisdiction === jurisdiction ? 'text-brand-primary-dark' : semantic.text.muted
              )}>
                {jurisdiction === 'BE' && 'BVBA/SRL, VAT optimization'}
                {jurisdiction === 'LU' && 'Holding structures, cross-border'}
                {jurisdiction === 'EU' && 'Digital nomad, mobility planning'}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Business Type Selector */}
      <div className={cardClasses('elevated', 'p-6')}>
        <h2 className={cn(
          textClasses.size('lg'),
          textClasses.weight('semibold'),
          semantic.text.primary,
          'mb-6 flex items-center gap-3'
        )}>
          <Briefcase className="h-5 w-5 text-brand-primary" />
          Business Structure
        </h2>
        <div className="grid grid-cols-2 gap-6">
          {(['individual', 'company'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setBusinessType(type)}
              className={cn(
                'p-5 rounded-2xl border-2 transition-all duration-200',
                businessType === type
                  ? 'border-brand-primary bg-gradient-to-r from-brand-primary/5 to-brand-accent/10 text-brand-primary-dark shadow-brand'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-brand-primary/30 hover:shadow-md'
              )}
            >
              <div className="flex items-center justify-center gap-3 mb-3">
                {type === 'individual' ? (
                  <Users className={cn(
                    'h-5 w-5',
                    businessType === type ? 'text-brand-primary' : 'text-gray-500'
                  )} />
                ) : (
                  <Building2 className={cn(
                    'h-5 w-5',
                    businessType === type ? 'text-brand-primary' : 'text-gray-500'
                  )} />
                )}
                <span className={cn(
                  textClasses.weight('semibold'),
                  businessType === type ? 'text-brand-primary' : semantic.text.primary
                )}>
                  {type === 'individual' ? 'Independent Professional' : 'Company (BVBA/SRL)'}
                </span>
              </div>
              <div className={cn(
                textClasses.size('sm'),
                businessType === type ? 'text-brand-primary-dark' : semantic.text.muted
              )}>
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
        <div className={cardClasses('elevated', 'p-6')}>
          <h2 className={cn(
            textClasses.size('lg'),
            textClasses.weight('semibold'),
            semantic.text.primary,
            'mb-6 flex items-center gap-3'
          )}>
            <Calculator className="h-5 w-5 text-brand-primary" />
            VAT Rate Calculator - {selectedJurisdiction === 'BE' ? 'Belgium' : 'Luxembourg'}
          </h2>
          <div className="grid grid-cols-2 gap-8">
            <div>
              <h3 className={cn(
                textClasses.weight('semibold'),
                semantic.text.secondary,
                'mb-4'
              )}>
                Available VAT Rates
              </h3>
              <div className="space-y-4">
                <div className={cn(
                  'flex items-center justify-between p-4 rounded-xl',
                  'bg-gradient-to-r from-red-50 to-red-100 border border-red-200'
                )}>
                  <span className={cn(textClasses.weight('medium'), 'text-red-800')}>
                    Standard Rate
                  </span>
                  <span className={cn(
                    textClasses.size('lg'),
                    textClasses.weight('bold'),
                    'text-red-600'
                  )}>
                    {vatRates[selectedJurisdiction].standard}%
                  </span>
                </div>
                <div className={cn(
                  'flex items-center justify-between p-4 rounded-xl',
                  'bg-gradient-to-r from-yellow-50 to-yellow-100 border border-yellow-200'
                )}>
                  <span className={cn(textClasses.weight('medium'), 'text-yellow-800')}>
                    Reduced Rate 1
                  </span>
                  <span className={cn(
                    textClasses.size('lg'),
                    textClasses.weight('bold'),
                    'text-yellow-600'
                  )}>
                    {vatRates[selectedJurisdiction].reduced1}%
                  </span>
                </div>
                <div className={cn(
                  'flex items-center justify-between p-4 rounded-xl',
                  'bg-gradient-to-r from-green-50 to-green-100 border border-green-200'
                )}>
                  <span className={cn(textClasses.weight('medium'), 'text-green-800')}>
                    Reduced Rate 2
                  </span>
                  <span className={cn(
                    textClasses.size('lg'),
                    textClasses.weight('bold'),
                    'text-green-600'
                  )}>
                    {vatRates[selectedJurisdiction].reduced2}%
                  </span>
                </div>
                {selectedJurisdiction === 'LU' && (
                  <div className={cn(
                    'flex items-center justify-between p-4 rounded-xl',
                    'bg-gradient-to-r from-brand-primary/10 to-brand-accent/20 border border-brand-primary/30'
                  )}>
                    <span className={cn(textClasses.weight('medium'), 'text-brand-primary-dark')}>
                      Super Reduced
                    </span>
                    <span className={cn(
                      textClasses.size('lg'),
                      textClasses.weight('bold'),
                      'text-brand-primary'
                    )}>
                      {vatRates[selectedJurisdiction].super_reduced}%
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div>
              <h3 className={cn(
                textClasses.weight('semibold'),
                semantic.text.secondary,
                'mb-4'
              )}>
                Service Examples
              </h3>
              <div className="space-y-4">
                <div className={cn(
                  'p-4 rounded-xl',
                  'bg-gradient-to-r from-red-50 to-red-100 border border-red-200'
                )}>
                  <div className={cn(
                    textClasses.weight('semibold'),
                    'text-red-800 mb-2'
                  )}>
                    Standard ({vatRates[selectedJurisdiction].standard}%)
                  </div>
                  <div className={cn(
                    textClasses.size('sm'),
                    'text-red-600'
                  )}>
                    {vatRates[selectedJurisdiction].examples.standard.join(', ')}
                  </div>
                </div>
                <div className={cn(
                  'p-4 rounded-xl',
                  'bg-gradient-to-r from-yellow-50 to-yellow-100 border border-yellow-200'
                )}>
                  <div className={cn(
                    textClasses.weight('semibold'),
                    'text-yellow-800 mb-2'
                  )}>
                    Reduced 1 ({vatRates[selectedJurisdiction].reduced1}%)
                  </div>
                  <div className={cn(
                    textClasses.size('sm'),
                    'text-yellow-600'
                  )}>
                    {vatRates[selectedJurisdiction].examples.reduced1.join(', ')}
                  </div>
                </div>
                <div className={cn(
                  'p-4 rounded-xl',
                  'bg-gradient-to-r from-green-50 to-green-100 border border-green-200'
                )}>
                  <div className={cn(
                    textClasses.weight('semibold'),
                    'text-green-800 mb-2'
                  )}>
                    Reduced 2 ({vatRates[selectedJurisdiction].reduced2}%)
                  </div>
                  <div className={cn(
                    textClasses.size('sm'),
                    'text-green-600'
                  )}>
                    {vatRates[selectedJurisdiction].examples.reduced2.join(', ')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tax Strategies */}
      <div className={cardClasses('elevated', 'p-6')}>
        <h2 className={cn(
          textClasses.size('lg'),
          textClasses.weight('semibold'),
          semantic.text.primary,
          'mb-6 flex items-center gap-3'
        )}>
          <TrendingUp className="h-5 w-5 text-brand-primary" />
          Available Tax Strategies
        </h2>
        <div className="grid gap-6">
          {currentStrategies.map((strategy) => (
            <div
              key={strategy.id}
              className={cn(
                'border-2 rounded-2xl p-5 cursor-pointer transition-all duration-200',
                selectedStrategy?.id === strategy.id
                  ? 'border-brand-primary bg-gradient-to-r from-brand-primary/5 to-brand-accent/10 shadow-brand'
                  : 'border-gray-200 hover:border-brand-primary/30 hover:shadow-md'
              )}
              onClick={() => setSelectedStrategy(strategy)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className={cn(
                      textClasses.weight('semibold'),
                      selectedStrategy?.id === strategy.id ? 'text-brand-primary' : semantic.text.primary
                    )}>
                      {strategy.name}
                    </h3>
                    <span className={
                      strategy.complexity === 'low' 
                        ? badgeClasses('success')
                        : strategy.complexity === 'medium'
                        ? badgeClasses('warning')
                        : badgeClasses('error')
                    }>
                      {strategy.complexity} complexity
                    </span>
                    <span className={badgeClasses('neutral')}>
                      {strategy.jurisdiction}
                    </span>
                  </div>
                  <p className={cn(
                    textClasses.size('sm'),
                    selectedStrategy?.id === strategy.id ? 'text-brand-primary-dark' : semantic.text.muted,
                    'mb-4'
                  )}>
                    {strategy.description}
                  </p>
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 text-green-600">
                      <Euro className="h-4 w-4" />
                      <span className={cn(
                        textClasses.size('sm'),
                        textClasses.weight('semibold')
                      )}>
                        €{strategy.estimatedSavings.toLocaleString()}/year
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-brand-primary">
                      <FileText className="h-4 w-4" />
                      <span className={textClasses.size('sm')}>
                        {strategy.timeframe}
                      </span>
                    </div>
                  </div>
                </div>
                <ArrowRight className={cn(
                  'h-5 w-5 mt-2 transition-colors',
                  selectedStrategy?.id === strategy.id ? 'text-brand-primary' : 'text-gray-400'
                )} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Details */}
      {selectedStrategy && (
        <div className={cardClasses('elevated', 'p-6')}>
          <h2 className={cn(
            textClasses.size('lg'),
            textClasses.weight('semibold'),
            semantic.text.primary,
            'mb-6 flex items-center gap-3'
          )}>
            <Info className="h-5 w-5 text-brand-primary" />
            Strategy Details: {selectedStrategy.name}
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className={cn(
                textClasses.weight('semibold'),
                semantic.text.secondary,
                'mb-4'
              )}>
                Requirements
              </h3>
              <div className="space-y-3">
                {selectedStrategy.requirements.map((requirement, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className={cn(
                      textClasses.size('sm'),
                      semantic.text.primary
                    )}>
                      {requirement}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className={cn(
                textClasses.weight('semibold'),
                semantic.text.secondary,
                'mb-4'
              )}>
                Implementation Timeline
              </h3>
              <div className={cn(
                'bg-gradient-to-r from-brand-primary/5 to-brand-accent/10',
                'border border-brand-primary/20 rounded-2xl p-6'
              )}>
                <div className="flex items-center gap-3 mb-3">
                  <BarChart3 className="h-5 w-5 text-brand-primary" />
                  <span className={cn(
                    textClasses.weight('semibold'),
                    'text-brand-primary-dark'
                  )}>
                    Expected Timeline
                  </span>
                </div>
                <div className={cn(
                  textClasses.size('2xl'),
                  textClasses.weight('bold'),
                  'text-brand-primary mb-2'
                )}>
                  {selectedStrategy.timeframe}
                </div>
                <div className={cn(
                  textClasses.size('sm'),
                  'text-brand-primary-dark'
                )}>
                  Estimated annual savings: €{selectedStrategy.estimatedSavings.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
          
          <div className={cn(
            'mt-8 p-5 rounded-2xl',
            'bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200'
          )}>
            <div className="flex items-start gap-4">
              <AlertCircle className="h-6 w-6 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div>
                <div className={cn(
                  textClasses.weight('semibold'),
                  'text-yellow-900 mb-2'
                )}>
                  Professional Consultation Recommended
                </div>
                <div className={cn(
                  textClasses.size('sm'),
                  'text-yellow-800 leading-relaxed'
                )}>
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
      <DrSigmundAdviceCard
        variant="business"
        title="Tax Therapy Corner"
        badgeText="Stress Relief"
        mood="thinking"
        className="mt-12"
      >
        <div>
          <h3 className="font-medium text-emerald-900 mb-3">Tax Anxiety Relief Tips</h3>
          <ul className="space-y-2 text-sm text-emerald-800">
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 mt-1">•</span>
              <span>Remember: tax optimization is about making informed, legal choices to minimize your burden</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 mt-1">•</span>
              <span>Start with simple strategies (expense optimization) before considering complex structures</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 mt-1">•</span>
              <span>Always consult with a qualified tax professional for high-complexity strategies</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 mt-1">•</span>
              <span>Focus on long-term financial health, not just immediate tax savings</span>
            </li>
          </ul>
        </div>
      </DrSigmundAdviceCard>

      {/* Disclaimer */}
      <div className={cn(cardClasses('default'), 'mt-8 bg-amber-50 border-amber-200 p-6')}>
        <div className="flex items-start gap-3">
          <AlertCircle className="h-6 w-6 text-amber-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className={cn(textClasses.weight('medium'), 'text-amber-900 mb-2')}>Important Disclaimer</h3>
            <p className={cn(textClasses.size('sm'), 'text-amber-800 leading-relaxed')}>
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