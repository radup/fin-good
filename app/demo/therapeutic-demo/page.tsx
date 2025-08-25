'use client';

import React, { useState } from 'react';
import DrSigmundSpendAvatar from '../../components/DrSigmundSpendAvatar';
import TherapeuticUploadProgress from '../../components/TherapeuticUploadProgress';
import AIConfidenceDisplay from '../../components/AIConfidenceDisplay';
import { TherapeuticUploadModal } from '../../components/TherapeuticUploadModal';
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

export default function TherapeuticDemo() {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDemoUpload = () => {
    setUploadProgress(0);
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Therapeutic UX Components Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience the enhanced user interface designed to reduce financial anxiety and build trust through therapeutic design principles.
          </p>
        </div>

        {/* Dr. Sigmund Spend Avatar Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Dr. Sigmund Spend Avatar</h2>
          
          {/* All Moods Display */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Encouraging</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="encouraging"
                message="I'm here to help you understand your finances better!"
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Celebrating</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="celebrating"
                message="Great job! You're making excellent progress!"
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Supportive</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="supportive"
                message="Remember, every step forward is progress."
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Thinking</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="thinking"
                message="Let me analyze this for you..."
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Reassuring</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="reassuring"
                message="Your financial data is safe and secure with us."
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Analytical</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="analytical"
                message="Let me break down these patterns for you."
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Inspiring</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="inspiring"
                message="You have the power to transform your financial future!"
              />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-800 mb-3">Protective</h3>
              <DrSigmundSpendAvatar 
                size="lg" 
                mood="protective"
                message="I'm here to protect your financial wellbeing."
              />
            </div>
          </div>

          {/* Size Variations */}
          <div className="mb-8">
            <h3 className="font-medium text-gray-900 mb-4">Size Variations</h3>
            <div className="flex items-center justify-center gap-8">
              <div className="text-center">
                <span className="text-sm text-gray-600 mb-2 block">Small</span>
                <DrSigmundSpendAvatar size="sm" showMessage={false} />
              </div>
              <div className="text-center">
                <span className="text-sm text-gray-600 mb-2 block">Medium</span>
                <DrSigmundSpendAvatar size="md" showMessage={false} />
              </div>
              <div className="text-center">
                <span className="text-sm text-gray-600 mb-2 block">Large</span>
                <DrSigmundSpendAvatar size="lg" showMessage={false} />
              </div>
              <div className="text-center">
                <span className="text-sm text-gray-600 mb-2 block">Extra Large</span>
                <DrSigmundSpendAvatar size="xl" showMessage={false} />
              </div>
            </div>
          </div>

          {/* Interactive Features */}
          <div className="mb-8">
            <h3 className="font-medium text-gray-900 mb-4">Interactive Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <h4 className="font-medium text-gray-800 mb-2">Hover Effect</h4>
                <p className="text-sm text-gray-600 mb-3">Hover over the avatar to see the glow effect</p>
                <DrSigmundSpendAvatar 
                  size="lg" 
                  mood="encouraging"
                  showMessage={false}
                />
              </div>
              <div className="text-center">
                <h4 className="font-medium text-gray-800 mb-2">Pulse Animation</h4>
                <p className="text-sm text-gray-600 mb-3">Continuous pulse animation for attention</p>
                <DrSigmundSpendAvatar 
                  size="lg" 
                  mood="thinking"
                  showPulse={true}
                  showMessage={false}
                />
              </div>
              <div className="text-center">
                <h4 className="font-medium text-gray-800 mb-2">Typing State</h4>
                <p className="text-sm text-gray-600 mb-3">Shows when Dr. Sigmund is typing</p>
                <DrSigmundSpendAvatar 
                  size="lg" 
                  mood="analytical"
                  isTyping={true}
                  showMessage={false}
                />
              </div>
            </div>
          </div>

          {/* Modern Heroicons Showcase */}
          <div className="mb-8">
            <h3 className="font-medium text-gray-900 mb-4">Modern Heroicons</h3>
            <p className="text-sm text-gray-600 mb-4">Clean, simple icons by the Tailwind team</p>
            <div className="grid grid-cols-5 gap-4 p-6 bg-white rounded-xl shadow-sm">
              <div className="text-center">
                <CpuChipIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Brain</span>
              </div>
              <div className="text-center">
                <HeartIcon className="w-8 h-8 text-red-500 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Heart</span>
              </div>
              <div className="text-center">
                <SparklesIcon className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Sparkles</span>
              </div>
              <div className="text-center">
                <ShieldCheckIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Shield</span>
              </div>
              <div className="text-center">
                <ChartBarIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Chart</span>
              </div>
              <div className="text-center">
                <LightBulbIcon className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Lightbulb</span>
              </div>
              <div className="text-center">
                <BoltIcon className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Bolt</span>
              </div>
              <div className="text-center">
                <StarIcon className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Star</span>
              </div>
              <div className="text-center">
                <CheckCircleIcon className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Check</span>
              </div>
              <div className="text-center">
                <ExclamationTriangleIcon className="w-8 h-8 text-red-500 mx-auto mb-2" />
                <span className="text-xs text-gray-600">Warning</span>
              </div>
            </div>
          </div>
        </section>

        {/* AI Confidence Display Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">AI Confidence Display</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="font-medium text-gray-800 mb-3">High Confidence</h3>
              <AIConfidenceDisplay 
                transactionId={1}
                confidence={95}
                category="Restaurants"
                reasoning="This transaction clearly matches the 'Restaurants' category based on the merchant name and transaction pattern."
                onCorrect={() => console.log('Correct clicked')}
                onIncorrect={() => console.log('Incorrect clicked')}
              />
            </div>
            <div>
              <h3 className="font-medium text-gray-800 mb-3">Medium Confidence</h3>
              <AIConfidenceDisplay 
                transactionId={2}
                confidence={65}
                category="Entertainment"
                reasoning="This could be either 'Entertainment' or 'Shopping' based on the merchant type, but I'm not entirely certain."
                onCorrect={() => console.log('Correct clicked')}
                onIncorrect={() => console.log('Incorrect clicked')}
              />
            </div>
            <div>
              <h3 className="font-medium text-gray-800 mb-3">Low Confidence</h3>
              <AIConfidenceDisplay 
                transactionId={3}
                confidence={25}
                category="Uncategorized"
                reasoning="This transaction is unclear and may need manual categorization. The merchant name doesn't provide enough context."
                onCorrect={() => console.log('Correct clicked')}
                onIncorrect={() => console.log('Incorrect clicked')}
              />
            </div>
          </div>
        </section>

        {/* Therapeutic Upload Progress Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Therapeutic Upload Progress</h2>
          <div className="max-w-2xl mx-auto">
            <TherapeuticUploadProgress 
              progress={uploadProgress}
              stage={uploadProgress < 25 ? 'uploading' : uploadProgress < 50 ? 'processing' : uploadProgress < 75 ? 'categorizing' : 'complete'}
              filename="sample-transactions.csv"
            />
            <div className="text-center mt-6">
              <button 
                onClick={handleDemoUpload}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
              >
                Demo Upload Progress
              </button>
            </div>
          </div>
        </section>

        {/* Complete Upload Experience Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Complete Upload Experience</h2>
          <div className="text-center">
            <button 
              onClick={() => setShowUploadModal(true)}
              className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-8 py-4 rounded-xl font-medium hover:from-green-700 hover:to-blue-700 transition-all duration-200 text-lg"
            >
              Open Therapeutic Upload Modal
            </button>
          </div>
        </section>

        {/* Therapeutic Color Palette Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Therapeutic Color Palette</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="w-20 h-20 bg-blue-600 rounded-lg mx-auto mb-2"></div>
              <span className="text-sm font-medium text-gray-800">Trust Blue</span>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 bg-green-600 rounded-lg mx-auto mb-2"></div>
              <span className="text-sm font-medium text-gray-800">Calm Green</span>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 bg-yellow-500 rounded-lg mx-auto mb-2"></div>
              <span className="text-sm font-medium text-gray-800">Warm Gold</span>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-lg mx-auto mb-2"></div>
              <span className="text-sm font-medium text-gray-800">Soft Background</span>
            </div>
          </div>
        </section>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <TherapeuticUploadModal 
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
        />
      )}
    </div>
  );
}
