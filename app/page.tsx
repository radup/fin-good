'use client'

import React from 'react'
import Link from 'next/link'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import { ArrowRight, BarChart3, Shield, Zap, Users, TrendingUp } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center gap-4">
              <DrSigmundSpendAvatar 
                size="md" 
                mood="encouraging"
                showMessage={false}
              />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">FinGood</h1>
                <p className="text-gray-600">AI-Powered Financial Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link 
                href="/login" 
                className="btn-primary flex items-center gap-2 therapeutic-hover"
              >
                Sign In
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <DrSigmundSpendAvatar 
            size="xl" 
            mood="inspiring"
            message="Welcome to the future of financial management! Let me help you understand your money better."
            className="mb-8"
          />
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Your AI-Powered Financial Companion
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            FinGood uses advanced AI to categorize transactions, provide insights, and help you achieve financial wellness. 
            Get personalized recommendations and understand your spending patterns like never before.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/login" 
              className="btn-primary text-lg px-8 py-4 therapeutic-hover"
            >
              Get Started
            </Link>
            <button 
              onClick={() => {
                // Demo login functionality
                window.location.href = '/login'
              }}
              className="btn-secondary text-lg px-8 py-4 therapeutic-hover"
            >
              Try Demo
            </button>
          </div>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 therapeutic-transition">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">AI-Powered Categorization</h3>
            <p className="text-gray-600">
              Automatically categorize your transactions with machine learning. 
              No more manual sorting - let AI do the heavy lifting.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 therapeutic-transition">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <BarChart3 className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Analytics</h3>
            <p className="text-gray-600">
              Get deep insights into your spending patterns, identify trends, 
              and discover opportunities to save money.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 therapeutic-transition">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Secure & Private</h3>
            <p className="text-gray-600">
              Your financial data is protected with enterprise-grade security. 
              We never share your information with third parties.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 therapeutic-transition">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Financial Wellness</h3>
            <p className="text-gray-600">
              Track your financial health with personalized wellness metrics 
              and get actionable recommendations for improvement.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 therapeutic-transition">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
              <Users className="w-6 h-6 text-red-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Personalized Support</h3>
            <p className="text-gray-600">
              Meet Dr. Sigmund Spend, your AI financial advisor. 
              Get personalized guidance and emotional support for your financial journey.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 therapeutic-transition">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <ArrowRight className="w-6 h-6 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Easy Import</h3>
            <p className="text-gray-600">
              Import your financial data from CSV files with just a few clicks. 
              No complex setup required - get started in minutes.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Financial Life?</h2>
          <p className="text-xl mb-6 opacity-90">
            Join thousands of users who are already using FinGood to achieve financial wellness.
          </p>
          <Link 
            href="/login" 
            className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center gap-2"
          >
            Start Your Journey
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center gap-4 mb-4">
              <DrSigmundSpendAvatar 
                size="sm" 
                mood="encouraging"
                showMessage={false}
              />
              <span className="text-lg font-semibold text-gray-900">FinGood</span>
            </div>
            <p className="text-gray-600">
              AI-Powered Financial Intelligence for a better financial future.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
