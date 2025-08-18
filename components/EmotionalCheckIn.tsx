'use client'

import React, { useState, useEffect } from 'react'
import { Smile, Frown, Meh, Heart, TrendingUp, Target, AlertCircle, CheckCircle, Coffee, BookOpen } from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

interface MoodData {
  mood: 'great' | 'good' | 'okay' | 'stressed' | 'overwhelmed'
  timestamp: Date
  financialContext?: string
  stressLevel?: number // 1-10
}

interface Achievement {
  id: string
  type: 'savings' | 'categorization' | 'consistency' | 'goal' | 'budget'
  title: string
  description: string
  timestamp: Date
  value?: number
}

interface Nudge {
  id: string
  type: 'gentle' | 'encouraging' | 'celebratory' | 'supportive'
  message: string
  action?: string
  icon: React.ReactNode
  priority: 'low' | 'medium' | 'high'
}

interface EmotionalCheckInProps {
  userId?: string
  onMoodSubmit?: (mood: MoodData) => void
  achievements?: Achievement[]
  showNudges?: boolean
  className?: string
}

const MOOD_OPTIONS = [
  { value: 'great', label: 'Great!', icon: <Smile className="w-6 h-6" />, color: 'text-green-600' },
  { value: 'good', label: 'Good', icon: <Heart className="w-6 h-6" />, color: 'text-blue-600' },
  { value: 'okay', label: 'Okay', icon: <Meh className="w-6 h-6" />, color: 'text-yellow-600' },
  { value: 'stressed', label: 'Stressed', icon: <AlertCircle className="w-6 h-6" />, color: 'text-orange-600' },
  { value: 'overwhelmed', label: 'Overwhelmed', icon: <Frown className="w-6 h-6" />, color: 'text-red-600' }
]

const STRESS_LEVELS = [
  { value: 1, label: 'Very Low', color: 'bg-green-100 text-green-800' },
  { value: 2, label: 'Low', color: 'bg-green-100 text-green-800' },
  { value: 3, label: 'Low-Medium', color: 'bg-blue-100 text-blue-800' },
  { value: 4, label: 'Medium', color: 'bg-yellow-100 text-yellow-800' },
  { value: 5, label: 'Medium-High', color: 'bg-orange-100 text-orange-800' },
  { value: 6, label: 'High', color: 'bg-orange-100 text-orange-800' },
  { value: 7, label: 'Very High', color: 'bg-red-100 text-red-800' },
  { value: 8, label: 'Extremely High', color: 'bg-red-100 text-red-800' },
  { value: 9, label: 'Critical', color: 'bg-red-100 text-red-800' },
  { value: 10, label: 'Emergency', color: 'bg-red-100 text-red-800' }
]

export default function EmotionalCheckIn({
  userId,
  onMoodSubmit,
  achievements = [],
  showNudges = true,
  className = ''
}: EmotionalCheckInProps) {
  const [currentMood, setCurrentMood] = useState<MoodData | null>(null)
  const [showMoodCheck, setShowMoodCheck] = useState(false)
  const [stressLevel, setStressLevel] = useState<number>(5)
  const [financialContext, setFinancialContext] = useState('')
  const [recentMoods, setRecentMoods] = useState<MoodData[]>([])
  const [nudges, setNudges] = useState<Nudge[]>([])
  const [showAchievements, setShowAchievements] = useState(false)

  // Generate nudges based on mood and achievements
  useEffect(() => {
    const generateNudges = (): Nudge[] => {
      const newNudges: Nudge[] = []

      // Check if user hasn't logged mood recently
      const lastMood = recentMoods[0]
      const hoursSinceLastMood = lastMood 
        ? (Date.now() - lastMood.timestamp.getTime()) / (1000 * 60 * 60)
        : 24

      if (hoursSinceLastMood > 12) {
        newNudges.push({
          id: 'mood-check',
          type: 'gentle',
          message: "How are you feeling about your finances today? A quick check-in can help us provide better support.",
          action: 'Check in now',
          icon: <Heart className="w-5 h-5" />,
          priority: 'medium'
        })
      }

      // Stress-based nudges
      if (currentMood?.mood === 'stressed' || currentMood?.mood === 'overwhelmed') {
        newNudges.push({
          id: 'stress-support',
          type: 'supportive',
          message: "Financial stress is completely normal. Let's break this down into smaller, manageable steps.",
          action: 'Get support',
          icon: <Coffee className="w-5 h-5" />,
          priority: 'high'
        })
      }

      // Achievement-based nudges
      const recentAchievements = achievements.filter(a => 
        (Date.now() - a.timestamp.getTime()) < 7 * 24 * 60 * 60 * 1000 // Last 7 days
      )

      if (recentAchievements.length > 0) {
        newNudges.push({
          id: 'celebration',
          type: 'celebratory',
          message: `You've achieved ${recentAchievements.length} financial milestone${recentAchievements.length > 1 ? 's' : ''} this week!`,
          action: 'Celebrate',
          icon: <CheckCircle className="w-5 h-5" />,
          priority: 'medium'
        })
      }

      // Consistency nudges
      if (recentMoods.length >= 3) {
        const positiveMoods = recentMoods.slice(0, 3).filter(m => 
          m.mood === 'great' || m.mood === 'good'
        ).length

        if (positiveMoods >= 2) {
          newNudges.push({
            id: 'consistency',
            type: 'encouraging',
            message: "You're maintaining a positive financial mindset! Keep up the great work.",
            action: 'View progress',
            icon: <TrendingUp className="w-5 h-5" />,
            priority: 'low'
          })
        }
      }

      return newNudges
    }

    setNudges(generateNudges())
  }, [currentMood, recentMoods, achievements])

  const handleMoodSubmit = (mood: MoodData['mood']) => {
    const moodData: MoodData = {
      mood,
      timestamp: new Date(),
      financialContext: financialContext || undefined,
      stressLevel: stressLevel
    }

    setCurrentMood(moodData)
    setRecentMoods(prev => [moodData, ...prev.slice(0, 9)]) // Keep last 10 moods
    setShowMoodCheck(false)
    setFinancialContext('')
    setStressLevel(5)

    onMoodSubmit?.(moodData)
  }

  const getMoodMessage = (mood: MoodData['mood']) => {
    const messages = {
      great: "Fantastic! Your positive financial mindset is shining through. Keep up this amazing energy!",
      good: "That's wonderful! You're in a good place with your finances. Every positive step counts.",
      okay: "It's okay to feel neutral about finances. Let's work together to find what would make you feel better.",
      stressed: "Financial stress is completely normal and manageable. You're not alone in this journey.",
      overwhelmed: "I understand this feels overwhelming. Let's take it one step at a time. You've got this."
    }
    return messages[mood]
  }

  const getStressIntervention = (level: number) => {
    if (level <= 3) return null

    const interventions = {
      low: "Consider taking a short break and doing something you enjoy. Small steps forward are still progress.",
      medium: "Let's focus on one small financial task today. What's one thing you can do to feel more in control?",
      high: "Your feelings are valid. Consider reaching out to a friend or taking some time for self-care.",
      critical: "Please consider talking to someone you trust about how you're feeling. You don't have to handle this alone."
    }

    if (level <= 5) return interventions.low
    if (level <= 7) return interventions.medium
    if (level <= 9) return interventions.high
    return interventions.critical
  }

  const handleNudgeAction = (nudge: Nudge) => {
    switch (nudge.id) {
      case 'mood-check':
        setShowMoodCheck(true)
        break
      case 'celebration':
        setShowAchievements(true)
        break
      case 'stress-support':
        // Could open a support resources modal
        console.log('Opening stress support resources')
        break
      default:
        console.log('Nudge action:', nudge.action)
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Mood Check-in Section */}
      {showMoodCheck && (
        <div className="card therapeutic-transition">
          <div className="text-center mb-6">
            <DrSigmundSpendAvatar 
              mood={currentMood?.mood === 'stressed' || currentMood?.mood === 'overwhelmed' ? 'supportive' : 'encouraging'}
              message="How are you feeling about your finances today?"
              showMessage={true}
            />
          </div>

          <div className="space-y-6">
            {/* Mood Selection */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">How are you feeling?</h3>
              <div className="grid grid-cols-5 gap-3">
                {MOOD_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleMoodSubmit(option.value as MoodData['mood'])}
                    className={`p-4 rounded-lg border-2 border-gray-200 hover:border-primary-300 therapeutic-transition therapeutic-hover ${option.color}`}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      {option.icon}
                      <span className="text-sm font-medium">{option.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Stress Level */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Stress Level (1-10)</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Very Low</span>
                  <span>Very High</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={stressLevel}
                  onChange={(e) => setStressLevel(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="text-center">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    STRESS_LEVELS.find(s => s.value === stressLevel)?.color || 'bg-gray-100 text-gray-800'
                  }`}>
                    {STRESS_LEVELS.find(s => s.value === stressLevel)?.label} ({stressLevel}/10)
                  </span>
                </div>
                {getStressIntervention(stressLevel) && (
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">{getStressIntervention(stressLevel)}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Financial Context */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">What's on your mind? (Optional)</h3>
              <textarea
                value={financialContext}
                onChange={(e) => setFinancialContext(e.target.value)}
                placeholder="Share what's affecting your financial mood today..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
              />
            </div>
          </div>
        </div>
      )}

      {/* Current Mood Display */}
      {currentMood && !showMoodCheck && (
        <div className="card therapeutic-transition">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {MOOD_OPTIONS.find(m => m.value === currentMood.mood)?.icon}
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Feeling {MOOD_OPTIONS.find(m => m.value === currentMood.mood)?.label}
                </h3>
                <p className="text-sm text-gray-600">
                  {getMoodMessage(currentMood.mood)}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowMoodCheck(true)}
              className="btn-secondary"
            >
              Update Mood
            </button>
          </div>
        </div>
      )}

      {/* Nudges Section */}
      {showNudges && nudges.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-gray-900">Gentle Reminders</h3>
          {nudges.map((nudge) => (
            <div
              key={nudge.id}
              className={`card therapeutic-transition ${
                nudge.priority === 'high' ? 'border-l-4 border-l-orange-500' :
                nudge.priority === 'medium' ? 'border-l-4 border-l-blue-500' :
                'border-l-4 border-l-green-500'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {nudge.icon}
                </div>
                <div className="flex-1">
                  <p className="text-gray-900">{nudge.message}</p>
                  {nudge.action && (
                    <button
                      onClick={() => handleNudgeAction(nudge)}
                      className="mt-2 text-sm text-primary-600 hover:text-primary-800 therapeutic-transition"
                    >
                      {nudge.action} →
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Achievements Section */}
      {showAchievements && achievements.length > 0 && (
        <div className="card therapeutic-transition">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Achievements</h3>
            <button
              onClick={() => setShowAchievements(false)}
              className="text-gray-400 hover:text-gray-600 therapeutic-transition"
            >
              ×
            </button>
          </div>
          <div className="space-y-3">
            {achievements.slice(0, 5).map((achievement) => (
              <div key={achievement.id} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-green-900">{achievement.title}</h4>
                  <p className="text-sm text-green-700">{achievement.description}</p>
                  {achievement.value && (
                    <p className="text-xs text-green-600 mt-1">
                      Value: ${achievement.value.toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mood History */}
      {recentMoods.length > 0 && (
        <div className="card therapeutic-transition">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Mood History</h3>
          <div className="space-y-2">
            {recentMoods.slice(0, 5).map((mood, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  {MOOD_OPTIONS.find(m => m.value === mood.mood)?.icon}
                  <span className="text-sm text-gray-900">
                    {MOOD_OPTIONS.find(m => m.value === mood.mood)?.label}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {mood.timestamp.toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Mood Check Button */}
      {!showMoodCheck && !currentMood && (
        <div className="text-center">
          <button
            onClick={() => setShowMoodCheck(true)}
            className="btn-primary therapeutic-transition"
          >
            <Heart className="w-4 h-4 mr-2" />
            How are you feeling today?
          </button>
        </div>
      )}
    </div>
  )
}
