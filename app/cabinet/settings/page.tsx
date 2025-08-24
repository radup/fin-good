'use client'

import React, { useState } from 'react'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { User, Bell, Shield, Palette, Database, Globe } from 'lucide-react'

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    weekly: true,
    monthly: true
  })

  const [theme, setTheme] = useState('light')

  return (
    <CabinetPageLayout title="Settings" description="Manage your account preferences and settings">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your account preferences and settings
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Profile Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center mb-6">
              <User className="w-5 h-5 text-blue-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">Profile</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  defaultValue="demo@spendsanalysis.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  defaultValue="Demo User"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Update Profile
              </button>
            </div>
          </div>
          
          {/* Notification Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center mb-6">
              <Bell className="w-5 h-5 text-green-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">Email Notifications</p>
                  <p className="text-xs text-gray-500">Receive updates via email</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.email}
                  onChange={(e) => setNotifications(prev => ({ ...prev, email: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">Push Notifications</p>
                  <p className="text-xs text-gray-500">Browser push notifications</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.push}
                  onChange={(e) => setNotifications(prev => ({ ...prev, push: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">Weekly Reports</p>
                  <p className="text-xs text-gray-500">Weekly financial summaries</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.weekly}
                  onChange={(e) => setNotifications(prev => ({ ...prev, weekly: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          
          {/* Security Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center mb-6">
              <Shield className="w-5 h-5 text-red-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">Security</h2>
            </div>
            
            <div className="space-y-4">
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Change Password
              </button>
              
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Two-Factor Authentication
              </button>
              
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Session Management
              </button>
            </div>
          </div>
          
          {/* Appearance Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center mb-6">
              <Palette className="w-5 h-5 text-purple-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">Appearance</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Theme
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Currency
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>
          </div>
          
          {/* Data Management */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center mb-6">
              <Database className="w-5 h-5 text-indigo-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">Data Management</h2>
            </div>
            
            <div className="space-y-4">
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Export Data
              </button>
              
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Import Data
              </button>
              
              <button className="w-full px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 transition-colors">
                Delete Account
              </button>
            </div>
          </div>
          
          {/* API Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center mb-6">
              <Globe className="w-5 h-5 text-teal-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">API & Integrations</h2>
            </div>
            
            <div className="space-y-4">
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                API Keys
              </button>
              
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Webhooks
              </button>
              
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Third-party Integrations
              </button>
            </div>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}