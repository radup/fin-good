'use client';

import React from 'react';
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar';

interface TherapeuticUploadProgressProps {
  progress: number;
  stage: 'uploading' | 'processing' | 'categorizing' | 'complete';
  filename: string;
  onComplete?: () => void;
  className?: string;
}

const TherapeuticUploadProgress: React.FC<TherapeuticUploadProgressProps> = ({
  progress,
  stage,
  filename,
  onComplete,
  className = ''
}) => {
  const stageMessages = {
    uploading: {
      message: "Securely receiving your financial data...",
      mood: 'reassuring' as const,
      icon: "🔒"
    },
    processing: {
      message: "Reading and organizing your transactions...",
      mood: 'thinking' as const,
      icon: "📊"
    },
    categorizing: {
      message: "AI is intelligently categorizing your expenses...",
      mood: 'thinking' as const,
      icon: "🧠"
    },
    complete: {
      message: "Your financial insights are ready!",
      mood: 'celebrating' as const,
      icon: "✨"
    }
  };

  const currentStage = stageMessages[stage];

  React.useEffect(() => {
    if (stage === 'complete' && onComplete) {
      const timer = setTimeout(onComplete, 2000);
      return () => clearTimeout(timer);
    }
  }, [stage, onComplete]);

  return (
    <div className={`bg-blue-50 rounded-lg p-6 border border-blue-200 therapeutic-transition ${className}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
          <span className="text-blue-600 text-lg">{currentStage.icon}</span>
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-blue-900">Processing {filename}</h3>
          <p className="text-sm text-blue-700">{currentStage.message}</p>
        </div>
      </div>
      
      <div className="w-full bg-blue-200 rounded-full h-2 mb-4">
        <div 
          className="bg-blue-600 h-2 rounded-full therapeutic-transition"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <div className="mb-4">
        <DrSigmundSpendAvatar 
          size="sm" 
          mood={currentStage.mood}
          message={currentStage.message}
          showMessage={false}
        />
      </div>
      
      <div className="text-xs text-blue-600 text-center space-y-1">
        <p>Your data is encrypted and secure throughout this process</p>
        {stage === 'complete' && (
          <p className="font-medium celebration-animation">
            🎉 All done! Your financial insights are ready to explore.
          </p>
        )}
      </div>
    </div>
  );
};

export default TherapeuticUploadProgress;
