'use client';

import React, { useState } from 'react';
import { transactionAPI } from '@/lib/api';
import type { ConfidenceAnalysisResponse, FeedbackSubmissionResponse } from '@/types/api';

interface AIConfidenceDisplayProps {
  transactionId: number; // Required for API integration
  confidence: number; // 0-100
  category: string;
  reasoning?: string;
  onCorrect?: () => void;
  onIncorrect?: () => void;
  showFeedback?: boolean;
  className?: string;
  onFeedbackSubmitted?: (response: FeedbackSubmissionResponse) => void;
}

const AIConfidenceDisplay: React.FC<AIConfidenceDisplayProps> = ({
  transactionId,
  confidence,
  category,
  reasoning,
  onCorrect,
  onIncorrect,
  showFeedback = true,
  className = '',
  onFeedbackSubmitted
}) => {
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const getConfidenceLevel = (score: number): { level: 'high' | 'medium' | 'low'; color: string; text: string } => {
    if (score >= 80) return { level: 'high', color: 'green', text: 'Very Confident' };
    if (score >= 60) return { level: 'medium', color: 'yellow', text: 'Somewhat Confident' };
    return { level: 'low', color: 'orange', text: 'Less Confident' };
  };

  const confidenceInfo = getConfidenceLevel(confidence);

  // Submit feedback to backend API
  const submitFeedback = async (feedbackType: 'correct' | 'incorrect' | 'suggest_alternative', suggestedCategory?: string) => {
    setIsSubmittingFeedback(true);
    setFeedbackMessage(null);
    
    try {
      const response = await transactionAPI.submitFeedback(
        transactionId,
        feedbackType,
        suggestedCategory
      );
      
      const result = response.data;
      
      // Show success message
      setFeedbackMessage(`Feedback submitted! ${result.impact === 'ml_learning' ? 'AI is learning from your feedback.' : 'Thank you for your feedback.'}`);
      
      // Call callback if provided
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(result);
      }
      
      // Call original callbacks if provided
      if (feedbackType === 'correct' && onCorrect) {
        onCorrect();
      } else if (feedbackType === 'incorrect' && onIncorrect) {
        onIncorrect();
      }
      
    } catch (error: any) {
      console.error('Feedback submission failed:', error);
      
      if (error.response?.status === 429) {
        // Rate limit exceeded
        const retryAfter = error.response.data?.retry_after || 60;
        setFeedbackMessage(`Rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`);
      } else {
        // Generic error
        setFeedbackMessage('Failed to submit feedback. Please try again.');
      }
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  
  const confidenceColorClasses = {
    high: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-orange-100 text-orange-800 border-orange-200'
  };

  return (
    <div className={`bg-gray-50 rounded-lg p-4 border border-gray-200 therapeutic-transition ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">AI Suggestion:</span>
          <span className="font-semibold text-blue-600">{category}</span>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${confidenceColorClasses[confidenceInfo.level]}`}>
          {confidence}% confident
        </span>
      </div>
      
      {reasoning && (
        <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-xs font-medium text-blue-800 mb-1">Why this category?</p>
          <p className="text-sm text-blue-700">{reasoning}</p>
        </div>
      )}
      
      <div className="mb-3">
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <span>Confidence Level:</span>
          <span className={`font-medium ${confidenceColorClasses[confidenceInfo.level].replace('bg-', 'text-').replace(' border-', '')}`}>
            {confidenceInfo.text}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
          <div 
            className={`h-1.5 rounded-full therapeutic-transition ${
              confidenceInfo.level === 'high' ? 'bg-green-500' :
              confidenceInfo.level === 'medium' ? 'bg-yellow-500' : 'bg-orange-500'
            }`}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>
      
      {showFeedback && (
        <div className="flex gap-2">
          <button
            onClick={() => submitFeedback('correct')}
            disabled={isSubmittingFeedback}
            className="flex-1 py-2 px-3 bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors therapeutic-transition therapeutic-hover disabled:opacity-50"
          >
            <span className="mr-1">👍</span>
            {isSubmittingFeedback ? 'Submitting...' : 'Correct'}
          </button>
          <button
            onClick={() => submitFeedback('incorrect')}
            disabled={isSubmittingFeedback}
            className="flex-1 py-2 px-3 bg-orange-100 text-orange-800 rounded-lg hover:bg-orange-200 transition-colors therapeutic-transition therapeutic-hover disabled:opacity-50"
          >
            <span className="mr-1">👎</span>
            {isSubmittingFeedback ? 'Submitting...' : 'Incorrect'}
          </button>
        </div>
      )}
      
      {/* Feedback message */}
      {feedbackMessage && (
        <div className={`mt-3 p-2 rounded-lg text-sm ${
          feedbackMessage.includes('Rate limit') || feedbackMessage.includes('Failed') 
            ? 'bg-red-50 text-red-700 border border-red-200' 
            : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {feedbackMessage}
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-500 text-center">
        <p>Your feedback helps our AI learn and improve!</p>
      </div>
    </div>
  );
};

export default AIConfidenceDisplay;
