'use client'

import { useState, useEffect } from 'react'

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
      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        method: 'GET',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const userData = await response.json()
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
      } else {
        setUser(null)
        setIsAuthenticated(false)
        setCsrfToken(null)
      }
    } catch (error) {
      console.error('Auth check error:', error)
      setUser(null)
      setIsAuthenticated(false)
      setCsrfToken(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        credentials: 'include', // Include cookies to receive secure auth cookies
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const data: AuthResponse = await response.json()
      
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
      const response = await fetch('http://localhost:8000/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include', // Include cookies for authentication
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRF-Token': csrfToken })
        },
      })

      // Clear state regardless of response status
      setUser(null)
      setIsAuthenticated(false)
      setCsrfToken(null)

      if (!response.ok) {
        console.warn('Logout request failed, but local state cleared')
      }
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
      const response = await fetch('http://localhost:8000/api/v1/auth/refresh-csrf', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setCsrfToken(data.csrf_token)
        return data.csrf_token
      }
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