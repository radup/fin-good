'use client'

import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'
import { 
  User, 
  Mail, 
  Building, 
  Briefcase, 
  Settings, 
  Shield, 
  Bell, 
  Palette,
  Save,
  Edit,
  X,
  Check
} from 'lucide-react'

export default function UserProfile() {
  const { user } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    company_name: user?.company_name || '',
    business_type: user?.business_type || ''
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSave = async () => {
    // TODO: Implement save functionality
    console.log('Saving user data:', formData)
    setIsEditing(false)
  }

  const handleCancel = () => {
    setFormData({
      full_name: user?.full_name || '',
      email: user?.email || '',
      company_name: user?.company_name || '',
      business_type: user?.business_type || ''
    })
    setIsEditing(false)
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <DrSigmundSpendAvatar 
              size="lg" 
              mood="analytical"
              showMessage={false}
            />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">User Profile</h1>
              <p className="text-gray-600">Manage your account settings and preferences</p>
            </div>
          </div>
          <div className="flex space-x-3">
            {isEditing ? (
              <>
                <button
                  onClick={handleSave}
                  className="bg-brand-gradient text-white px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 flex items-center space-x-2"
                >
                  <Save className="w-4 h-4" />
                  <span>Save</span>
                </button>
                <button
                  onClick={handleCancel}
                  className="bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-300 hover:border-brand-primary-light hover:text-brand-primary px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105 flex items-center space-x-2"
                >
                  <X className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="bg-brand-gradient text-white px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 flex items-center space-x-2"
              >
                <Edit className="w-4 h-4" />
                <span>Edit Profile</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Profile Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Personal Information */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <User className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-semibold text-gray-900">Personal Information</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              {isEditing ? (
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900">{user?.full_name || 'Not provided'}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              {isEditing ? (
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900">{user?.email || 'Not provided'}</p>
              )}
            </div>
          </div>
        </div>

        {/* Business Information */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Building className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-semibold text-gray-900">Business Information</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
              {isEditing ? (
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900">{user?.company_name || 'Not provided'}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Business Type</label>
              {isEditing ? (
                <select
                  name="business_type"
                  value={formData.business_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                >
                  <option value="">Select business type</option>
                  <option value="freelancer">Freelancer</option>
                  <option value="solopreneur">Solopreneur</option>
                  <option value="micro_sme">Micro SME</option>
                  <option value="contractor">Contractor</option>
                </select>
              ) : (
                <p className="text-gray-900">{user?.business_type || 'Not specified'}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Security Settings */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Shield className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-semibold text-gray-900">Security</h2>
          </div>
          
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Change Password</div>
              <div className="text-sm text-gray-500">Update your account password</div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Two-Factor Authentication</div>
              <div className="text-sm text-gray-500">Add an extra layer of security</div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Login History</div>
              <div className="text-sm text-gray-500">View recent login activity</div>
            </button>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Bell className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
          </div>
          
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Email Notifications</div>
              <div className="text-sm text-gray-500">Manage email preferences</div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Financial Alerts</div>
              <div className="text-sm text-gray-500">Set up spending alerts</div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Weekly Reports</div>
              <div className="text-sm text-gray-500">Configure report frequency</div>
            </button>
          </div>
        </div>

        {/* Appearance Settings */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Palette className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-semibold text-gray-900">Appearance</h2>
          </div>
          
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Theme</div>
              <div className="text-sm text-gray-500">Light, dark, or auto</div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Language</div>
              <div className="text-sm text-gray-500">English, German, etc.</div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="font-medium text-gray-900">Currency</div>
              <div className="text-sm text-gray-500">EUR, USD, GBP</div>
            </button>
          </div>
        </div>
      </div>

      {/* Account Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Actions</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button className="bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-300 hover:border-brand-primary-light hover:text-brand-primary px-4 py-3 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105">
            Export My Data
          </button>
          
          <button className="bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-300 hover:border-brand-primary-light hover:text-brand-primary px-4 py-3 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105">
            Download Reports
          </button>
          
          <button className="bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-300 hover:border-brand-primary-light hover:text-brand-primary px-4 py-3 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105">
            Privacy Settings
          </button>
          
          <button className="bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 px-4 py-3 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105">
            Delete Account
          </button>
        </div>
      </div>
    </div>
  )
}
