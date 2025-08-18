'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authAPI, setGlobalCsrfToken } from '@/lib/api'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const response = await authAPI.login(email, password)
      
      // Store CSRF token globally for API requests
      if (response.data.csrf_token) {
        setGlobalCsrfToken(response.data.csrf_token)
      }
      
      // Authentication is now handled by secure HttpOnly cookies
      // No need to store tokens in localStorage
      
      router.push('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <DrSigmundSpendAvatar 
            size="xl" 
            mood="reassuring"
            message="Welcome back! Your financial data is safe and secure with us."
            className="mb-6"
          />
          <h2 className="text-3xl font-extrabold text-gray-900">
            Sign in to FinGood
          </h2>
          <p className="mt-2 text-gray-600">
            AI-Powered Financial Intelligence
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="input-field rounded-t-md therapeutic-transition"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="input-field rounded-b-md therapeutic-transition"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="bg-danger-50 border border-danger-200 rounded-md p-4 therapeutic-transition">
              <p className="text-sm text-danger-800">{error}</p>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full therapeutic-hover"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Demo account: demo@fingood.com / demo123
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}