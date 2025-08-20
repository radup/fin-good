'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Brain, Heart, TrendingUp, Shield, Sparkles, CheckCircle, Star, User, Lock } from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

export default function LandingPage() {
  const [isSignUp, setIsSignUp] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-green-50">
      {/* Header */}
      <header className="relative z-10 bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-3">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <h1 className="text-lg font-bold text-gray-900">Spend's Analysis</h1>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsSignUp(false)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  !isSignUp 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-600 hover:bg-blue-50'
                }`}
              >
                Check In
              </button>
              <button
                onClick={() => setIsSignUp(true)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  isSignUp 
                    ? 'bg-green-600 text-white' 
                    : 'text-green-600 hover:bg-green-50'
                }`}
              >
                New Patient
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 py-20">
          {/* Left Column - Marketing Content */}
          <div className="space-y-8">
            <div className="space-y-6">
              <div className="flex items-center space-x-2 text-blue-600">
                <Brain className="h-5 w-5" />
                <span className="text-sm font-semibold">AI-Powered Financial Therapy</span>
              </div>
              
              <h1 className="text-5xl font-bold text-gray-900 leading-tight">
                Heal Your Relationship with{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                  Money
                </span>
              </h1>
              
              <p className="text-xl text-gray-600 leading-relaxed">
                Dr. Sigmund Spend combines cutting-edge AI with therapeutic principles to help you understand, 
                categorize, and optimize your financial behaviors. Transform anxiety into clarity.
              </p>
            </div>

            {/* Key Benefits */}
            <div className="grid grid-cols-2 gap-6">
              <div className="flex items-start space-x-3">
                <Heart className="h-6 w-6 text-red-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Emotional Intelligence</h3>
                  <p className="text-sm text-gray-600">Understand the feelings behind your spending</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <TrendingUp className="h-6 w-6 text-green-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Smart Forecasting</h3>
                  <p className="text-sm text-gray-600">AI-powered cash flow predictions</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Shield className="h-6 w-6 text-blue-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Bank-Grade Security</h3>
                  <p className="text-sm text-gray-600">Your data is encrypted and protected</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Sparkles className="h-6 w-6 text-purple-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Automated Insights</h3>
                  <p className="text-sm text-gray-600">Discover patterns you never noticed</p>
                </div>
              </div>
            </div>

            {/* Social Proof */}
            <div className="bg-white/60 backdrop-blur-sm rounded-lg p-6 border border-gray-200">
              <div className="flex items-center space-x-2 mb-3">
                <div className="flex text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-current" />
                  ))}
                </div>
                <span className="text-sm font-semibold text-gray-900">4.9/5 Patient Satisfaction</span>
              </div>
              <p className="text-gray-600 text-sm italic">
                "Dr. Spend helped me understand my financial anxiety and gave me practical tools 
                to manage my spending habits. The AI insights are incredible!"
              </p>
              <p className="text-xs text-gray-500 mt-2">— Sarah M., Small Business Owner</p>
            </div>
          </div>

          {/* Right Column - Sign In/Up Form */}
          <div className="flex items-center justify-center">
            <div className="w-full max-w-md">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 p-8">
                <div className="text-center mb-8">
                  <DrSigmundSpendAvatar size="lg" className="mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-gray-900">
                    {isSignUp ? 'Welcome, New Patient!' : 'Welcome Back!'}
                  </h2>
                  <p className="text-gray-600 mt-2">
                    {isSignUp 
                      ? 'Ready to start your financial healing journey?' 
                      : 'How are you feeling about your finances today?'
                    }
                  </p>
                </div>

                <form className="space-y-6">
                  {isSignUp && (
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                        <input
                          type="text"
                          id="name"
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Enter your full name"
                        />
                      </div>
                    </div>
                  )}

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your email"
                      defaultValue="demo@spendsanalysis.com"
                    />
                  </div>

                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="password"
                        id="password"
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter your password"
                        defaultValue="demo123"
                      />
                    </div>
                  </div>

                  {isSignUp && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div className="text-sm text-blue-800">
                          <p className="font-medium">What you'll get:</p>
                          <ul className="mt-1 space-y-1">
                            <li>• Personalized financial therapy sessions</li>
                            <li>• AI-powered transaction categorization</li>
                            <li>• Advanced cash flow forecasting</li>
                            <li>• Emotional spending pattern analysis</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  <Link
                    href="/cabinet"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>{isSignUp ? 'Begin Therapy' : 'Enter Cabinet'}</span>
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                </form>

                <div className="mt-6 text-center">
                  <p className="text-sm text-gray-600">
                    {isSignUp ? 'Already a patient?' : 'New to financial therapy?'}{' '}
                    <button
                      onClick={() => setIsSignUp(!isSignUp)}
                      className="text-blue-600 hover:text-blue-700 font-medium"
                    >
                      {isSignUp ? 'Check In' : 'Start Journey'}
                    </button>
                  </p>
                </div>
              </div>

              {/* Demo Account Notice */}
              <div className="mt-4 text-center">
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-800">
                    <strong>Demo Account:</strong> demo@spendsanalysis.com / demo123
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Preview */}
        <div className="py-20 border-t border-gray-200">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Your Financial Therapy Toolkit
            </h2>
            <p className="text-xl text-gray-600">
              Powered by AI, guided by therapeutic principles
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white/60 backdrop-blur-sm rounded-lg p-6 border border-gray-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Brain className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">AI Chat Therapy</h3>
              <p className="text-gray-600">
                Have natural conversations about your finances. Dr. Spend understands context 
                and provides personalized insights.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg p-6 border border-gray-200">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Forecasting</h3>
              <p className="text-gray-600">
                Multi-model AI predicts your cash flow using Prophet, ARIMA, and ensemble methods 
                for accurate planning.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg p-6 border border-gray-200">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <Heart className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Emotional Intelligence</h3>
              <p className="text-gray-600">
                Understand the emotional triggers behind your spending patterns and develop 
                healthier financial behaviors.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm border-t border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm text-gray-600">
              © 2024 Spend's Analysis. AI-powered financial therapy for your wellness journey.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}