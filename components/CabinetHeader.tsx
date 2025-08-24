'use client'

import React from 'react'
import Breadcrumbs from './Breadcrumbs'
import { useAuth } from '../hooks/useAuth'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'
import { LogOut } from 'lucide-react'

interface CabinetHeaderProps {
  title: string
  description?: string
  onUserProfileClick?: () => void
}

export default function CabinetHeader({ title, description, onUserProfileClick }: CabinetHeaderProps) {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
      // Redirect to home page after successful logout
      window.location.href = '/'
    } catch (error) {
      console.error('Logout failed:', error)
      // Still redirect to home even if logout API call fails
      window.location.href = '/'
    }
  }
  return (
    <div className="flex-shrink-0 bg-gradient-to-r from-gray-900 to-slate-800 border-b border-gray-700 shadow-sm">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Breadcrumbs */}
        <div className="flex items-center">
          <Breadcrumbs />
        </div>
        
        {/* Right side actions */}
        <div className="flex items-center space-x-4">
          {/* User Info */}
          <button
            onClick={onUserProfileClick}
            className="flex items-center space-x-3 group rounded-lg p-2 transition-colors hover:bg-gray-700/50"
          >
            <DrSigmundSpendAvatar 
              size="sm" 
              mood="analytical"
              showMessage={false}
              className="group-hover:scale-110 transition-transform duration-300"
            />
            <div className="text-left">
              <p className="text-sm font-medium text-white group-hover:text-brand-secondary-light transition-colors">
                {user?.full_name || user?.email?.split('@')[0] || 'User'}
              </p>
              <p className="text-xs text-gray-300 group-hover:text-brand-secondary-light/80 transition-colors">
                {user?.email || 'demo@fingood.com'}
              </p>
            </div>
          </button>
          
          {/* Logout */}
          <button
            onClick={handleLogout}
            className="p-2 text-gray-400 hover:text-brand-secondary-light hover:bg-gray-700 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
