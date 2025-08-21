'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Brain, Heart, TrendingUp, Shield, Sparkles, CheckCircle, Star, User, Lock, Eye, EyeOff } from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

export default function LandingPage() {
  const [isSignUp, setIsSignUp] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-green-50" style={{height: '100vh', overflowY: 'scroll', scrollSnapType: 'y mandatory'}}>
      
      {/* Screen 1: Header + Hero Section */}
      <div style={{minHeight: '100vh', scrollSnapAlign: 'start'}} className="bg-gradient-to-br from-blue-50 via-purple-50 to-green-50">
        {/* Header */}
        <header className="relative z-10 bg-gradient-to-r from-gray-900 to-slate-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-3">
              <div className="flex items-center ml-4">
                <img 
                  src="/logo.png" 
                  alt="Spend's Analysis - AI Financial Therapy" 
                  className="h-24 w-auto rounded-lg"
                  onError={(e) => {
                    // Fallback to original design if logo doesn't load
                    e.currentTarget.style.display = 'none';
                    const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                    if (fallback) fallback.style.display = 'flex';
                  }}
                />
                <div className="flex items-center space-x-3 hidden">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg items-center justify-center">
                    <span className="text-white font-bold text-sm">S</span>
                  </div>
                  <h1 className="text-lg font-bold text-gray-900">Spend's Analysis</h1>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsSignUp(false)}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    !isSignUp 
                      ? 'bg-brand-secondary text-white bg-brand-secondary-hover' 
                      : 'bg-gray-700 text-brand-secondary-light border-brand-secondary-light hover:bg-gray-600'
                  }`}
                >
                  Check In
                </button>
                <button
                  onClick={() => setIsSignUp(true)}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    isSignUp 
                      ? 'bg-brand-secondary text-white bg-brand-secondary-hover' 
                      : 'bg-gray-700 text-brand-secondary-light border-brand-secondary-light hover:bg-gray-600'
                  }`}
                >
                  New Patient
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <main className="flex-1 flex items-center" style={{minHeight: 'calc(100vh - 80px)'}}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="grid lg:grid-cols-2 gap-12 xl:gap-16 items-center">
          {/* Left Column - Marketing Content */}
          <div className="space-y-8">
            <div className="space-y-6">
              <div className="flex items-center space-x-2 text-brand-secondary">
                <Brain className="h-5 w-5" />
                <span className="text-sm font-semibold">AI-Powered Financial Therapy</span>
              </div>
              
              <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 leading-tight">
                Heal Your Relationship with{' '}
                <span className="text-brand-secondary font-bold">
                  Money
                </span>
              </h1>
              
              <p className="text-lg lg:text-xl text-gray-600 leading-relaxed">
                Dr. Sigmund Spend combines cutting-edge AI with therapeutic principles to help you understand, 
                categorize, and optimize your financial behaviors. Transform anxiety into clarity.
              </p>
            </div>

            {/* Key Benefits */}
            <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 transition-all duration-700 ${
              isSignUp ? 'scale-105 border-2 bg-brand-secondary-lightest rounded-xl p-4 shadow-lg' : ''
            }`} style={isSignUp ? {borderColor: 'var(--brand-secondary-lighter)'} : {}}>
              <div className={`flex items-start space-x-3 transition-all duration-500 ${
                isSignUp ? 'transform translate-x-2' : ''
              }`}>
                <Heart className="h-6 w-6 text-red-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Emotional Intelligence</h3>
                  <p className="text-sm text-gray-600">Understand the feelings behind your spending</p>
                </div>
              </div>
              
              <div className={`flex items-start space-x-3 transition-all duration-500 delay-100 ${
                isSignUp ? 'transform translate-x-2' : ''
              }`}>
                <TrendingUp className="h-6 w-6 text-green-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Smart Forecasting</h3>
                  <p className="text-sm text-gray-600">AI-powered cash flow predictions</p>
                </div>
              </div>
              
              <div className={`flex items-start space-x-3 transition-all duration-500 delay-200 ${
                isSignUp ? 'transform translate-x-2' : ''
              }`}>
                <Shield className="h-6 w-6 text-brand-secondary mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Bank-Grade Security</h3>
                  <p className="text-sm text-gray-600">Your data is encrypted and protected</p>
                </div>
              </div>
              
              <div className={`flex items-start space-x-3 transition-all duration-500 delay-300 ${
                isSignUp ? 'transform translate-x-2' : ''
              }`}>
                <Sparkles className="h-6 w-6 text-purple-500 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Automated Insights</h3>
                  <p className="text-sm text-gray-600">Discover patterns you never noticed</p>
                </div>
              </div>
            </div>

            {/* Social Proof */}
            <div className="bg-white/60 backdrop-blur-sm rounded-lg p-5 border border-gray-200">
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
          <div className="flex items-start justify-center pt-0">
            <div className="w-full max-w-lg">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 p-6">
                <div className="text-center mb-6">
                  <DrSigmundSpendAvatar 
                    size="lg" 
                    className="mx-auto mb-4" 
                    message={isSignUp ? "Welcome New Patient! Ready to face your financial fears?" : "Welcome back! How are you feeling about your finances today?"}
                    showMessage={true}
                  />
                  <h2 className="text-xl font-bold text-gray-900">
                    {isSignUp ? 'Start Your Journey' : 'Check In'}
                  </h2>
                </div>

                <form className="space-y-5">
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
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:border-transparent"
                          style={{'--tw-ring-color': 'var(--brand-secondary)'} as React.CSSProperties}
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
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:border-transparent"
                      style={{'--tw-ring-color': 'var(--brand-secondary)'} as React.CSSProperties}
                      placeholder="Enter your email"
                      defaultValue="sigmund@spendsanalysis.com"
                    />
                  </div>

                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type={showPassword ? "text" : "password"}
                        id="password"
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:border-transparent"
                        style={{'--tw-ring-color': 'var(--brand-secondary)'} as React.CSSProperties}
                        placeholder="Enter your password"
                        defaultValue="sigmund123_"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-3 h-5 w-5 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>

                  {isSignUp && (
                    <div>
                      <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                        Confirm Password
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          id="confirmPassword"
                          className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:border-transparent"
                          style={{'--tw-ring-color': 'var(--brand-secondary)'} as React.CSSProperties}
                          placeholder="Re-enter your password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-3 top-3 h-5 w-5 text-gray-400 hover:text-gray-600"
                        >
                          {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                      </div>
                    </div>
                  )}


                  <Link
                    href="/cabinet"
                    className="w-full bg-brand-secondary text-white py-3 px-6 rounded-lg font-semibold bg-brand-secondary-hover transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>{isSignUp ? 'Begin Therapy' : 'Enter Cabinet'}</span>
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                </form>

                <div className="mt-5 text-center">
                  <p className="text-sm text-gray-600">
                    {isSignUp ? 'Already a patient?' : 'New to financial therapy?'}{' '}
                    <button
                      onClick={() => setIsSignUp(!isSignUp)}
                      className="text-brand-secondary text-brand-secondary-hover font-medium"
                    >
                      {isSignUp ? 'Check In' : 'Start Journey'}
                    </button>
                  </p>
                </div>
              </div>

              {/* Demo Account Notice - Only show for login */}
              {!isSignUp && (
                <div className="mt-4 text-center">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800">
                      <strong>Demo Account:</strong> sigmund@spendsanalysis.com / sigmund123_
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
          </div>
        </div>
        </main>
      </div>

      {/* Screen 2: Features Preview */}
        <section className="min-h-screen flex items-center justify-center py-20 bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100" style={{scrollSnapAlign: 'start'}}>
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Section Header */}
            <div className="text-center mb-20">
              <div className="inline-flex items-center px-4 py-2 bg-white/80 rounded-full border border-gray-200 mb-6">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700">Advanced Financial Intelligence</span>
              </div>
              <h2 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
                Your Complete{' '}
                <span className="text-brand-secondary font-bold">
                  Financial Therapy
                </span>{' '}
                Toolkit
              </h2>
              <p className="text-xl text-gray-600 leading-relaxed max-w-3xl mx-auto">
                Powered by cutting-edge AI and guided by therapeutic principles, our platform transforms 
                the way you understand, manage, and optimize your financial life.
              </p>
            </div>

            {/* Main Features Grid */}
            <div className="grid lg:grid-cols-3 gap-8 mb-16">
              {/* AI Chat Therapy */}
              <div className="group bg-white/90 backdrop-blur-sm rounded-3xl p-8 border border-gray-200/50 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-2">
                <div className="relative mb-6">
                  <div className="w-16 h-16 bg-brand-secondary rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-400 rounded-full flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">AI Chat Therapy</h3>
                <p className="text-gray-600 leading-relaxed mb-6">
                  Have natural, therapeutic conversations about your finances. Dr. Sigmund Spend 
                  understands context, remembers your journey, and provides personalized insights 
                  that evolve with your financial growth.
                </p>
                <div className="flex items-center text-sm text-brand-secondary font-medium">
                  <span>Start Conversation</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>

              {/* Smart Forecasting */}
              <div className="group bg-white/90 backdrop-blur-sm rounded-3xl p-8 border border-gray-200/50 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-2">
                <div className="relative mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">Smart Forecasting</h3>
                <p className="text-gray-600 leading-relaxed mb-6">
                  Multi-model AI predicts your cash flow using Prophet, ARIMA, and ensemble methods. 
                  Get accurate financial projections with confidence intervals and scenario modeling 
                  for strategic planning.
                </p>
                <div className="flex items-center text-sm text-green-600 font-medium">
                  <span>View Forecasts</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>

              {/* Emotional Intelligence */}
              <div className="group bg-white/90 backdrop-blur-sm rounded-3xl p-8 border border-gray-200/50 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-2">
                <div className="relative mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </div>
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-pink-400 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">Emotional Intelligence</h3>
                <p className="text-gray-600 leading-relaxed mb-6">
                  Understand the emotional triggers behind your spending patterns. Our therapeutic 
                  approach helps you develop healthier financial behaviors and build a positive 
                  relationship with money.
                </p>
                <div className="flex items-center text-sm text-purple-600 font-medium">
                  <span>Explore Insights</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
          </div>
        </section>

      {/* Screen 3: Additional Features + Footer */}
      <div style={{minHeight: '100vh', scrollSnapAlign: 'start'}} className="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        {/* Additional Features */}
        <section className="py-20">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Complete Financial Toolkit</h3>
              <p className="text-lg text-gray-600">Everything you need for financial wellness in one platform</p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-200/50">
                <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Bank-Grade Security</h4>
                <p className="text-sm text-gray-600">256-bit encryption, SOC 2 compliance, and zero-knowledge architecture.</p>
              </div>

              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-200/50">
                <div className="w-12 h-12 bg-cyan-100 rounded-xl flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Real-Time Insights</h4>
                <p className="text-sm text-gray-600">Instant transaction categorization and pattern recognition.</p>
              </div>

              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-200/50">
                <div className="w-12 h-12 bg-violet-100 rounded-xl flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4h4a2 2 0 002-2V5z" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Multi-Currency</h4>
                <p className="text-sm text-gray-600">Support for 150+ currencies with real-time exchange rates.</p>
              </div>

              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-200/50">
                <div className="w-12 h-12 bg-rose-100 rounded-xl flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Smart Analytics</h4>
                <p className="text-sm text-gray-600">Advanced pattern recognition and predictive modeling.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gradient-to-r from-gray-900 to-slate-800 text-white py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand Section */}
            <div className="md:col-span-2">
              <div className="flex items-center mb-6">
                <img 
                  src="/logo.png" 
                  alt="Spend's Analysis - AI Financial Therapy" 
                  className="h-28 w-auto rounded-lg"
                  onError={(e) => {
                    // Fallback to original design if logo doesn't load
                    e.currentTarget.style.display = 'none';
                    const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                    if (fallback) fallback.style.display = 'flex';
                  }}
                />
                <div className="flex items-center space-x-3 hidden">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl items-center justify-center">
                    <span className="text-white font-bold text-lg">S</span>
                  </div>
                  <h3 className="text-2xl font-bold">Spend's Analysis</h3>
                </div>
              </div>
              <p className="text-gray-300 leading-relaxed mb-6 max-w-md">
                Transform your relationship with money through AI-powered financial therapy. 
                Join thousands who have discovered financial wellness with Dr. Sigmund Spend.
              </p>
              <div className="flex space-x-4">
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-white/20 transition-colors cursor-pointer">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                  </svg>
                </div>
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-white/20 transition-colors cursor-pointer">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M22.46 6c-.77.35-1.6.58-2.46.69.88-.53 1.56-1.37 1.88-2.38-.83.5-1.75.85-2.72 1.05C18.37 4.5 17.26 4 16 4c-2.35 0-4.27 1.92-4.27 4.29 0 .34.04.67.11.98C8.28 9.09 5.11 7.38 3 4.79c-.37.63-.58 1.37-.58 2.15 0 1.49.75 2.81 1.91 3.56-.71 0-1.37-.2-1.95-.5v.03c0 2.08 1.48 3.82 3.44 4.21a4.22 4.22 0 0 1-1.93.07 4.28 4.28 0 0 0 4 2.98 8.521 8.521 0 0 1-5.33 1.84c-.34 0-.68-.02-1.02-.06C3.44 20.29 5.7 21 8.12 21 16 21 20.33 14.46 20.33 8.79c0-.19 0-.37-.01-.56.84-.6 1.56-1.36 2.14-2.23z"/>
                  </svg>
                </div>
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-white/20 transition-colors cursor-pointer">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </div>
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h4 className="text-lg font-semibold mb-4">Platform</h4>
              <ul className="space-y-3 text-gray-300">
                <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API</a></li>
              </ul>
            </div>

            {/* Support */}
            <div>
              <h4 className="text-lg font-semibold mb-4">Support</h4>
              <ul className="space-y-3 text-gray-300">
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-700 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">
              © 2025 Spend's Analysis. AI-powered financial therapy for your wellness journey.
            </p>
            <div className="flex items-center space-x-6 mt-4 md:mt-0">
              <span className="text-sm text-gray-400">Trusted by 10,000+ users</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-400">All systems operational</span>
              </div>
            </div>
          </div>
        </div>
        </footer>
      </div>
    </div>
  )
}