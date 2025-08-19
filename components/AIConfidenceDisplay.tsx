'use client';

import React, { useState, useEffect } from 'react';
import { transactionAPI } from '@/lib/api';
import type { ConfidenceAnalysis, FeedbackResult } from '@/lib/api';

interface AIConfidenceDisplayProps {
  transactionId: number;
  confidence?: number; // Optional now since we'll fetch from API
  category?: string; // Optional now since we'll fetch from API
  reasoning?: string;
  onCorrect?: () => void;
  onIncorrect?: () => void;
  showFeedback?: boolean;
  className?: string;
  onFeedbackSubmitted?: (response: FeedbackResult) => void;
}

const AIConfidenceDisplay: React.FC<AIConfidenceDisplayProps> = ({
  transactionId,
  confidence: propConfidence,
  category: propCategory,
  reasoning: propReasoning,
  onCorrect,
  onIncorrect,
  showFeedback = true,
  className = '',
  onFeedbackSubmitted
}) => {
  const [confidenceData, setConfidenceData] = useState<ConfidenceAnalysis | null>(null);
  const [isLoadingConfidence, setIsLoadingConfidence] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [showSuggestionForm, setShowSuggestionForm] = useState(false);
  const [suggestedCategory, setSuggestedCategory] = useState('');
  const [suggestedSubcategory, setSuggestedSubcategory] = useState('');
  const [feedbackComment, setFeedbackComment] = useState('');

  // Use prop values as fallback if API data not available
  const confidence = confidenceData?.confidence_score || propConfidence || 0;
  const category = confidenceData?.current_category || propCategory || 'Unknown';
  const reasoning = confidenceData?.alternatives?.[0]?.reasoning || propReasoning;

  // Fetch confidence data from API
  useEffect(() => {
    const fetchConfidenceData = async () => {
      setIsLoadingConfidence(true);
      try {
        const response = await transactionAPI.getConfidence(transactionId);
        setConfidenceData(response.data);
      } catch (error) {
        console.error('Failed to fetch confidence data:', error);
        // Continue with prop values as fallback
      } finally {
        setIsLoadingConfidence(false);
      }
    };

    if (transactionId) {
      fetchConfidenceData();
    }
  }, [transactionId]);

  const getConfidenceLevel = (score: number): { level: 'high' | 'medium' | 'low'; color: string; text: string } => {
    if (score >= 80) return { level: 'high', color: 'green', text: 'Very Confident' };
    if (score >= 60) return { level: 'medium', color: 'yellow', text: 'Somewhat Confident' };
    return { level: 'low', color: 'orange', text: 'Less Confident' };
  };

  const confidenceInfo = getConfidenceLevel(confidence);

  // Submit feedback to backend API
  const submitFeedback = async (feedbackType: 'correct' | 'incorrect' | 'suggest_alternative') => {
    setIsSubmittingFeedback(true);
    setFeedbackMessage(null);
    
    try {
      const params: any = {
        feedback_type: feedbackType
      };

      if (feedbackType === 'suggest_alternative') {
        if (!suggestedCategory.trim()) {
          setFeedbackMessage('Please provide a suggested category');
          return;
        }
        params.suggested_category = suggestedCategory;
        if (suggestedSubcategory.trim()) {
          params.suggested_subcategory = suggestedSubcategory;
        }
      }

      if (feedbackComment.trim()) {
        params.feedback_comment = feedbackComment;
      }

      const response = await transactionAPI.submitFeedback(transactionId, params);
      const result = response.data;
      
      // Show success message
      setFeedbackMessage(`Feedback submitted! ${result.ml_learning ? 'AI is learning from your feedback.' : 'Thank you for your feedback.'}`);
      
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

      // Reset form
      setShowSuggestionForm(false);
      setSuggestedCategory('');
      setSuggestedSubcategory('');
      setFeedbackComment('');
      
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

  if (isLoadingConfidence) {
    return (
      <div className={`bg-gray-50 rounded-lg p-4 border border-gray-200 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
          <div className="h-2 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-50 rounded-lg p-4 border border-gray-200 therapeutic-transition ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">AI Suggestion:</span>
          <span className="font-semibold text-blue-600">{category}</span>
          {confidenceData?.current_subcategory && (
            <span className="text-sm text-gray-600">› {confidenceData.current_subcategory}</span>
          )}
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${confidenceColorClasses[confidenceInfo.level]}`}>
          {Math.round(confidence * 100)}% confident
        </span>
      </div>

      {/* Categorization Method */}
      {confidenceData?.categorization_method && (
        <div className="mb-3 text-xs text-gray-600">
          <span>Method: </span>
          <span className="font-medium capitalize">{confidenceData.categorization_method}</span>
        </div>
      )}
      
      {reasoning && (
        <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-xs font-medium text-blue-800 mb-1">Why this category?</p>
          <p className="text-sm text-blue-700">{reasoning}</p>
        </div>
      )}

      {/* Alternative Categories */}
      {confidenceData?.alternatives && confidenceData.alternatives.length > 0 && (
        <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs font-medium text-gray-700 mb-2">Alternative Categories:</p>
          <div className="space-y-1">
            {confidenceData.alternatives.slice(0, 3).map((alt, index) => (
              <div key={index} className="flex justify-between items-center text-sm">
                <span className="text-gray-600">
                  {alt.category}
                  {alt.subcategory && <span className="text-gray-500"> › {alt.subcategory}</span>}
                </span>
                <span className="text-xs text-gray-500">
                  {Math.round(alt.confidence * 100)}% confidence
                </span>
              </div>
            ))}
          </div>
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
            style={{ width: `${Math.round(confidence * 100)}%` }}
          />
        </div>
      </div>
      
      {showFeedback && (
        <div className="space-y-3">
          {/* Basic Feedback Buttons */}
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

          {/* Suggest Alternative Button */}
          <button
            onClick={() => setShowSuggestionForm(!showSuggestionForm)}
            disabled={isSubmittingFeedback}
            className="w-full py-2 px-3 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors therapeutic-transition therapeutic-hover disabled:opacity-50"
          >
            <span className="mr-1">💡</span>
            {showSuggestionForm ? 'Cancel Suggestion' : 'Suggest Alternative'}
          </button>

          {/* Suggestion Form */}
          {showSuggestionForm && (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 space-y-3">
              <div>
                <label className="block text-xs font-medium text-blue-800 mb-1">
                  Suggested Category *
                </label>
                <input
                  type="text"
                  value={suggestedCategory}
                  onChange={(e) => setSuggestedCategory(e.target.value)}
                  placeholder="e.g., Food & Dining"
                  className="w-full px-3 py-2 text-sm border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-blue-800 mb-1">
                  Suggested Subcategory (Optional)
                </label>
                <input
                  type="text"
                  value={suggestedSubcategory}
                  onChange={(e) => setSuggestedSubcategory(e.target.value)}
                  placeholder="e.g., Restaurants"
                  className="w-full px-3 py-2 text-sm border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-blue-800 mb-1">
                  Additional Comment (Optional)
                </label>
                <textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Any additional context or explanation..."
                  rows={2}
                  className="w-full px-3 py-2 text-sm border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={() => submitFeedback('suggest_alternative')}
                disabled={isSubmittingFeedback || !suggestedCategory.trim()}
                className="w-full py-2 px-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors therapeutic-transition therapeutic-hover disabled:opacity-50"
              >
                {isSubmittingFeedback ? 'Submitting...' : 'Submit Suggestion'}
              </button>
            </div>
          )}
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
