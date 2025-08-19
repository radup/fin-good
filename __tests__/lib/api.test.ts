import { 
  bulkOperationsAPI, 
  duplicateDetectionAPI, 
  patternRecognitionAPI, 
  enhancedAnalyticsAPI, 
  reportBuilderAPI 
} from '@/lib/api'

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  }))
}))

describe('API Client Integration', () => {
  describe('Bulk Operations API', () => {
    it('should have categorize method', () => {
      expect(bulkOperationsAPI.categorize).toBeDefined()
      expect(typeof bulkOperationsAPI.categorize).toBe('function')
    })

    it('should have update method', () => {
      expect(bulkOperationsAPI.update).toBeDefined()
      expect(typeof bulkOperationsAPI.update).toBe('function')
    })

    it('should have delete method', () => {
      expect(bulkOperationsAPI.delete).toBeDefined()
      expect(typeof bulkOperationsAPI.delete).toBe('function')
    })

    it('should have undo method', () => {
      expect(bulkOperationsAPI.undo).toBeDefined()
      expect(typeof bulkOperationsAPI.undo).toBe('function')
    })

    it('should have redo method', () => {
      expect(bulkOperationsAPI.redo).toBeDefined()
      expect(typeof bulkOperationsAPI.redo).toBe('function')
    })

    it('should have getHistory method', () => {
      expect(bulkOperationsAPI.getHistory).toBeDefined()
      expect(typeof bulkOperationsAPI.getHistory).toBe('function')
    })
  })

  describe('Duplicate Detection API', () => {
    it('should have scan method', () => {
      expect(duplicateDetectionAPI.scan).toBeDefined()
      expect(typeof duplicateDetectionAPI.scan).toBe('function')
    })

    it('should have getGroups method', () => {
      expect(duplicateDetectionAPI.getGroups).toBeDefined()
      expect(typeof duplicateDetectionAPI.getGroups).toBe('function')
    })

    it('should have getGroup method', () => {
      expect(duplicateDetectionAPI.getGroup).toBeDefined()
      expect(typeof duplicateDetectionAPI.getGroup).toBe('function')
    })

    it('should have merge method', () => {
      expect(duplicateDetectionAPI.merge).toBeDefined()
      expect(typeof duplicateDetectionAPI.merge).toBe('function')
    })

    it('should have dismiss method', () => {
      expect(duplicateDetectionAPI.dismiss).toBeDefined()
      expect(typeof duplicateDetectionAPI.dismiss).toBe('function')
    })

    it('should have getStats method', () => {
      expect(duplicateDetectionAPI.getStats).toBeDefined()
      expect(typeof duplicateDetectionAPI.getStats).toBe('function')
    })

    it('should have getScanHistory method', () => {
      expect(duplicateDetectionAPI.getScanHistory).toBeDefined()
      expect(typeof duplicateDetectionAPI.getScanHistory).toBe('function')
    })
  })

  describe('Pattern Recognition API', () => {
    it('should have analyze method', () => {
      expect(patternRecognitionAPI.analyze).toBeDefined()
      expect(typeof patternRecognitionAPI.analyze).toBe('function')
    })

    it('should have getRecognized method', () => {
      expect(patternRecognitionAPI.getRecognized).toBeDefined()
      expect(typeof patternRecognitionAPI.getRecognized).toBe('function')
    })

    it('should have getPattern method', () => {
      expect(patternRecognitionAPI.getPattern).toBeDefined()
      expect(typeof patternRecognitionAPI.getPattern).toBe('function')
    })

    it('should have generateRules method', () => {
      expect(patternRecognitionAPI.generateRules).toBeDefined()
      expect(typeof patternRecognitionAPI.generateRules).toBe('function')
    })

    it('should have getStats method', () => {
      expect(patternRecognitionAPI.getStats).toBeDefined()
      expect(typeof patternRecognitionAPI.getStats).toBe('function')
    })

    it('should have getUserProfile method', () => {
      expect(patternRecognitionAPI.getUserProfile).toBeDefined()
      expect(typeof patternRecognitionAPI.getUserProfile).toBe('function')
    })

    it('should have updateAccuracy method', () => {
      expect(patternRecognitionAPI.updateAccuracy).toBeDefined()
      expect(typeof patternRecognitionAPI.updateAccuracy).toBe('function')
    })
  })

  describe('Enhanced Analytics API', () => {
    it('should have getPerformanceMetrics method', () => {
      expect(enhancedAnalyticsAPI.getPerformanceMetrics).toBeDefined()
      expect(typeof enhancedAnalyticsAPI.getPerformanceMetrics).toBe('function')
    })

    it('should have getPredictiveInsights method', () => {
      expect(enhancedAnalyticsAPI.getPredictiveInsights).toBeDefined()
      expect(typeof enhancedAnalyticsAPI.getPredictiveInsights).toBe('function')
    })

    it('should have getEnhancedVendorAnalysis method', () => {
      expect(enhancedAnalyticsAPI.getEnhancedVendorAnalysis).toBeDefined()
      expect(typeof enhancedAnalyticsAPI.getEnhancedVendorAnalysis).toBe('function')
    })

    it('should have clearEnhancedCache method', () => {
      expect(enhancedAnalyticsAPI.clearEnhancedCache).toBeDefined()
      expect(typeof enhancedAnalyticsAPI.clearEnhancedCache).toBe('function')
    })

    it('should have getAnalyticsSummary method', () => {
      expect(enhancedAnalyticsAPI.getAnalyticsSummary).toBeDefined()
      expect(typeof enhancedAnalyticsAPI.getAnalyticsSummary).toBe('function')
    })
  })

  describe('Report Builder API', () => {
    it('should have createReport method', () => {
      expect(reportBuilderAPI.createReport).toBeDefined()
      expect(typeof reportBuilderAPI.createReport).toBe('function')
    })

    it('should have getTemplates method', () => {
      expect(reportBuilderAPI.getTemplates).toBeDefined()
      expect(typeof reportBuilderAPI.getTemplates).toBe('function')
    })

    it('should have getTemplate method', () => {
      expect(reportBuilderAPI.getTemplate).toBeDefined()
      expect(typeof reportBuilderAPI.getTemplate).toBe('function')
    })

    it('should have getProgress method', () => {
      expect(reportBuilderAPI.getProgress).toBeDefined()
      expect(typeof reportBuilderAPI.getProgress).toBe('function')
    })

    it('should have download method', () => {
      expect(reportBuilderAPI.download).toBeDefined()
      expect(typeof reportBuilderAPI.download).toBe('function')
    })

    it('should have getHistory method', () => {
      expect(reportBuilderAPI.getHistory).toBeDefined()
      expect(typeof reportBuilderAPI.getHistory).toBe('function')
    })

    it('should have scheduleReport method', () => {
      expect(reportBuilderAPI.scheduleReport).toBeDefined()
      expect(typeof reportBuilderAPI.scheduleReport).toBe('function')
    })

    it('should have getScheduledReports method', () => {
      expect(reportBuilderAPI.getScheduledReports).toBeDefined()
      expect(typeof reportBuilderAPI.getScheduledReports).toBe('function')
    })

    it('should have updateScheduledReport method', () => {
      expect(reportBuilderAPI.updateScheduledReport).toBeDefined()
      expect(typeof reportBuilderAPI.updateScheduledReport).toBe('function')
    })

    it('should have deleteScheduledReport method', () => {
      expect(reportBuilderAPI.deleteScheduledReport).toBeDefined()
      expect(typeof reportBuilderAPI.deleteScheduledReport).toBe('function')
    })

    it('should have cancelJob method', () => {
      expect(reportBuilderAPI.cancelJob).toBeDefined()
      expect(typeof reportBuilderAPI.cancelJob).toBe('function')
    })
  })
})
