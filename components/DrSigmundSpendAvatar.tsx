'use client';

import React, { useState } from 'react';
import { 
  CpuChipIcon,
  HeartIcon,
  SparklesIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  LightBulbIcon,
  BoltIcon,
  StarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface DrSigmundSpendAvatarProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  message?: string;
  mood?: 'encouraging' | 'celebrating' | 'supportive' | 'thinking' | 'reassuring' | 'analytical' | 'inspiring' | 'protective';
  showMessage?: boolean;
  className?: string;
  animated?: boolean;
  showPulse?: boolean;
  variant?: 'default' | 'professional' | 'friendly' | 'expert';
  isTyping?: boolean;
  isListening?: boolean;
}

const DrSigmundSpendAvatar: React.FC<DrSigmundSpendAvatarProps> = ({
  size = 'md',
  message,
  mood = 'encouraging',
  showMessage = true,
  className = '',
  animated = true,
  showPulse = false,
  variant = 'default',
  isTyping = false,
  isListening = false
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-20 h-20',
    xl: 'w-24 h-24'
  };

  const sizeIconClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-7 h-7'
  };

  const sizeTextClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
    xl: 'text-lg'
  };
  
  const moodConfig = {
    encouraging: {
      bgGradient: 'dr-sigmund-gradient',
      message: "I'm here to help you understand your finances better!"
    },
    celebrating: {
      bgGradient: 'dr-sigmund-gradient',
      message: "Great job! You're making excellent progress!"
    },
    supportive: {
      bgGradient: 'dr-sigmund-gradient',
      message: "Remember, every step forward is progress."
    },
    thinking: {
      bgGradient: 'dr-sigmund-gradient',
      message: "Let me analyze this for you..."
    },
    reassuring: {
      bgGradient: 'dr-sigmund-gradient',
      message: "Your financial data is safe and secure with us."
    },
    analytical: {
      bgGradient: 'dr-sigmund-gradient',
      message: "Let me break down these patterns for you."
    },
    inspiring: {
      bgGradient: 'dr-sigmund-gradient',
      message: "You have the power to transform your financial future!"
    },
    protective: {
      bgGradient: 'dr-sigmund-gradient',
      message: "I'm here to protect your financial wellbeing."
    }
  };

  const currentMood = moodConfig[mood];
  const displayMessage = message || currentMood?.message || "I'm here to help you with your finances!";
  
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      {/* Dr. Sigmund Avatar (Variant18 Style) */}
      <div 
        className={`
          ${sizeClasses[size]} 
          relative group
          therapeutic-transition
          ${animated ? 'hover:scale-105' : ''}
          ${showPulse ? 'animate-pulse' : ''}
        `}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Main container with breathing animation */}
        <div className={`w-full h-full relative ${isTyping || isListening ? 'animate-pulse' : ''}`} style={{ animationDuration: '6s' }}>
          <svg viewBox="0 0 200 200" className="w-full h-full transform transition-transform duration-300 group-hover:scale-105">
            {/* Background circle */}
            <defs>
              <linearGradient id="drSigmundBg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#475569" />
                <stop offset="100%" stopColor="#334155" />
              </linearGradient>
              <linearGradient id="faceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f1c27d" />
                <stop offset="100%" stopColor="#e0a96d" />
              </linearGradient>
              <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="2" dy="4" stdDeviation="4" floodColor="#000" floodOpacity="0.3"/>
              </filter>
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge> 
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            {/* Main head circle */}
            <circle cx="100" cy="100" r="90" fill="url(#drSigmundBg)" filter="url(#shadow)" />
            
            {/* Face */}
            <circle cx="100" cy="95" r="65" fill="url(#faceGradient)" />
            
            {/* Hair */}
            <path d="M 45 80 Q 100 40 155 80 Q 150 70 100 65 Q 50 70 45 80" fill="#8b7355" />
            <path d="M 40 85 Q 45 75 55 82" fill="#8b7355" />
            <path d="M 145 82 Q 155 75 160 85" fill="#8b7355" />
            
            {/* Glasses */}
            <g>
              {/* Glasses frame */}
              <circle cx="85" cy="90" r="18" fill="none" stroke="#374151" strokeWidth="3" />
              <circle cx="115" cy="90" r="18" fill="none" stroke="#374151" strokeWidth="3" />
              <line x1="103" y1="90" x2="97" y2="90" stroke="#374151" strokeWidth="3" />
              
              {/* Glasses lenses with reflection */}
              <circle cx="85" cy="90" r="15" fill="#e5e7eb" opacity="0.8" />
              <circle cx="115" cy="90" r="15" fill="#e5e7eb" opacity="0.8" />
              <ellipse cx="82" cy="87" rx="4" ry="6" fill="#ffffff" opacity="0.9" />
              <ellipse cx="112" cy="87" rx="4" ry="6" fill="#ffffff" opacity="0.9" />
            </g>
            
            {/* Eyes */}
            <circle cx="85" cy="90" r="4" fill="#2c3e50" />
            <circle cx="115" cy="90" r="4" fill="#2c3e50" />
            <circle cx="86" cy="89" r="1" fill="#ffffff" />
            <circle cx="116" cy="89" r="1" fill="#ffffff" />
            
            {/* Eyebrows */}
            <path d="M 70 78 Q 85 75 100 78" fill="#8b7355" />
            <path d="M 100 78 Q 115 75 130 78" fill="#8b7355" />
            
            {/* Nose */}
            <ellipse cx="100" cy="100" rx="3" ry="8" fill="#d69e2e" opacity="0.6" />
            
            {/* Mouth - gentle smile */}
            <path d="M 88 115 Q 100 125 112 115" fill="none" stroke="#2c3e50" strokeWidth="2" strokeLinecap="round" />
            
            {/* Beard/facial hair */}
            <path d="M 80 125 Q 100 135 120 125 Q 110 140 100 142 Q 90 140 80 125" fill="#8b7355" opacity="0.8" />
            
            {/* Professional indicator - small brain icon */}
            <circle cx="160" cy="60" r="15" fill="#3b82f6" />
            <path d="M 153 55 Q 160 50 167 55 Q 165 60 160 62 Q 155 60 153 55" fill="#ffffff" />
            <circle cx="158" cy="58" r="2" fill="#ffffff" />
            <circle cx="162" cy="58" r="2" fill="#ffffff" />
            
            {/* Status indicator */}
            <circle cx="170" cy="40" r="8" fill="#10b981" />
            <circle cx="170" cy="40" r="3" fill="#ffffff" />
          </svg>
        </div>

        {/* CSS-based animations overlay */}
        
        {/* Blinking animation */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-[35%] left-[37%] w-[8%] h-[4%] bg-slate-800 rounded-full opacity-0 animate-blink"></div>
          <div className="absolute top-[35%] right-[37%] w-[8%] h-[4%] bg-slate-800 rounded-full opacity-0 animate-blink" style={{ animationDelay: '0.1s' }}></div>
        </div>

        {/* Listening animation */}
        {isListening && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-[15%] right-[10%] w-[20%] h-[20%] border-2 border-green-400 rounded-full animate-ping opacity-40" style={{ animationDuration: '3s' }}></div>
            <div className="absolute top-[15%] right-[10%] w-[20%] h-[20%] border border-green-400 rounded-full animate-ping opacity-25" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
          </div>
        )}

        {/* Typing animation */}
        {isTyping && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-[25%] right-[5%] flex gap-1">
              <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{ animationDuration: '1.5s' }}></div>
              <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s', animationDuration: '1.5s' }}></div>
              <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.6s', animationDuration: '1.5s' }}></div>
            </div>
          </div>
        )}

        {/* Enhanced status indicator */}
        <div className="absolute top-[15%] right-[15%] w-[16%] h-[16%] dr-sigmund-gradient rounded-full animate-pulse border-2 border-white" style={{ animationDuration: '4s' }}></div>

        {/* Brain glow effect */}
        <div className="absolute top-[25%] right-[25%] w-[15%] h-[15%] dr-sigmund-gradient rounded-full animate-pulse opacity-30" style={{ animationDuration: '5s' }}></div>

        {/* Hair sway animation */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[15%] left-[20%] w-[60%] h-[20%] bg-amber-700 rounded-full opacity-10 animate-pulse" style={{ animationDuration: '6s' }}></div>
        </div>

        {/* Mouth animation for typing */}
        {isTyping && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-[55%] left-[42%] w-[16%] h-[2%] bg-slate-800 rounded-full animate-pulse" style={{ animationDuration: '1s' }}></div>
          </div>
        )}

        {/* Hover effect glow */}
        <div className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" style={{background: 'linear-gradient(to bottom right, rgba(19, 137, 169, 0.1), rgba(98, 211, 242, 0.1))'}}></div>
      </div>

      {/* Message Bubble */}
      {showMessage && displayMessage && (
        <div className={`
          relative
          bg-white 
          rounded-2xl 
          p-4 
          shadow-lg
          border border-gray-200
          max-w-xs
          therapeutic-transition
          ${animated ? 'hover:shadow-xl' : ''}
        `}>
          {/* Speech Bubble Tail */}
          <div className={`
            absolute left-0 top-4 -ml-2
            w-0 h-0 
            border-t-4 border-t-transparent
            border-b-4 border-b-transparent
            border-r-4 border-r-white
          `}></div>

          {/* Message Header */}
          <div className="flex items-center gap-2 mb-3">
            <div className={`
              w-3 h-3 rounded-full ${currentMood?.bgGradient || 'dr-sigmund-gradient'}
              ${animated ? 'animate-pulse' : ''}
            `}></div>
            <p className={`${sizeTextClasses[size]} font-semibold text-gray-800`}>Dr. Sigmund Spend</p>
          </div>

          {/* Message Content */}
          <p className="text-sm text-gray-700 leading-relaxed text-left">{displayMessage}</p>

          {/* Mood Indicator */}
          <div className="flex items-center gap-2 mt-3">
            <div className={`
              w-2 h-2 rounded-full ${currentMood?.bgGradient || 'dr-sigmund-gradient'}
              ${animated ? 'animate-pulse' : ''}
            `}></div>
            <span className="text-xs text-gray-500 capitalize font-medium">{mood}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DrSigmundSpendAvatar;
