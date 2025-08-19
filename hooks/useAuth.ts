'use client'

import { useState, useEffect } from 'react'
import { authAPI } from '@/lib/api'

interface User {
  id: number
  email: string
  full_name?: string
  company_name?: string
  business_type?: string
}

interface AuthResponse {
  message: string
  user: User
  csrf_token: string
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [csrfToken, setCsrfToken] = useState<string | null>(null)

  useEffect(() => {
    // Check authentication status using secure /me endpoint
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await authAPI.me()
      const userData = response.data
      setUser(userData)
      setIsAuthenticated(true)
      
      // Extract CSRF token from cookie if available
      const csrfCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('fingood_auth_csrf='))
      
      if (csrfCookie) {
        const token = csrfCookie.split('=')[1]
        setCsrfToken(token)
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        // 401 is expected when user is not authenticated - this is normal behavior
        setUser(null)
        setIsAuthenticated(false)
        setCsrfToken(null)
      } else {
        // Only log warnings for unexpected error statuses
        console.warn('Auth check failed with unexpected status:', error.response?.status)
        setUser(null)
        setIsAuthenticated(false)
        setCsrfToken(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password)
      const data: AuthResponse = response.data
      
      // Store user data and CSRF token from response
      setUser(data.user)
      setIsAuthenticated(true)
      setCsrfToken(data.csrf_token)
      
      return data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()

      // Clear state regardless of response status
      setUser(null)
      setIsAuthenticated(false)
      setCsrfToken(null)
    } catch (error) {
      console.error('Logout error:', error)
      // Clear state even if logout request fails
      setUser(null)
      setIsAuthenticated(false)
      setCsrfToken(null)
    }
  }

  const refreshCsrfToken = async () => {
    try {
      const response = await authAPI.refreshCsrf()
      const data = response.data
      setCsrfToken(data.csrf_token)
      return data.csrf_token
    } catch (error) {
      console.error('CSRF refresh error:', error)
    }
    return null
  }

  return {
    user,
    isLoading,
    isAuthenticated,
    csrfToken,
    login,
    logout,
    refreshCsrfToken,
    checkAuthStatus,
  }
}