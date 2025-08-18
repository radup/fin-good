# ML-Powered Transaction Categorization

This document describes the ML-based transaction categorization system implemented using Ollama for the FinGood financial platform.

## Overview

The ML categorization system provides intelligent transaction categorization using local LLMs via Ollama. It serves as a fallback to rule-based categorization and provides category suggestions with confidence scoring.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Transaction   │───▶│ Rule-based      │───▶│ ML Fallback     │
│   Processing    │    │ Categorization  │    │ (Ollama)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ High Confidence │    │ ML Prediction   │
                       │ Rule Match      │    │ with Confidence │
                       └─────────────────┘    └─────────────────┘
```

## Key Components

### 1. MLCategorizationService
- **Location**: `backend/app/services/ml_categorization.py`
- **Purpose**: Core ML categorization logic
- **Features**:
  - Single transaction categorization
  - Batch processing for efficiency
  - Few-shot learning with user context
  - Caching for performance
  - Performance monitoring

### 2. Enhanced CategorizationService
- **Location**: `backend/app/services/categorization.py`
- **Purpose**: Orchestrates rule-based and ML categorization
- **Features**:
  - ML fallback integration
  - User feedback tracking
  - Performance metrics
  - Category suggestions

### 3. OllamaClient
- **Location**: Within `ml_categorization.py`
- **Purpose**: Async communication with Ollama API
- **Features**:
  - Timeout handling
  - Error resilience
  - Connection pooling

## API Endpoints

### ML Categorization Endpoints
Base URL: `/api/v1/ml`

#### `POST /{transaction_id}/categorize`
Categorize a single transaction using ML in real-time.

**Response:**
```json
{
  "transaction_id": 123,
  "categorization_result": {
    "categorized": true,
    "method": "ml",
    "confidence": 0.85,
    "category": "Food & Dining",
    "subcategory": "Restaurants",
    "reasoning": "Coffee shop transaction based on description",
    "alternatives": [
      {"category": "Entertainment", "confidence": 0.65}
    ]
  }
}
```

#### `GET /{transaction_id}/suggestions`
Get ML category suggestions without applying them.

**Response:**
```json
{
  "transaction_id": 123,
  "transaction_details": {
    "description": "STARBUCKS STORE #1234",
    "vendor": "Starbucks",
    "amount": -4.50
  },
  "suggestions": {
    "has_suggestions": true,
    "primary_suggestion": {
      "category": "Food & Dining",
      "subcategory": "Coffee Shops",
      "confidence": 0.92,
      "reasoning": "Coffee shop chain, typical beverage purchase"
    },
    "alternatives": [
      {"category": "Business Meals", "confidence": 0.45}
    ]
  }
}
```

#### `GET /performance-metrics`
Get ML performance metrics for the current user.

**Response:**
```json
{
  "user_id": 1,
  "ml_performance": {
    "total_predictions": 156,
    "correct_predictions": 142,
    "accuracy": 0.910,
    "average_response_time": 1.250,
    "cache_size": 89,
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

#### `GET /health-status`
Check ML service health and Ollama connectivity.

#### `GET /training-data`
Generate training data from user's categorized transactions.

### Enhanced Transaction Endpoints

#### `POST /transactions/categorize`
Enhanced with ML fallback support.

**Query Parameters:**
- `use_ml_fallback` (bool): Enable ML categorization fallback (default: true)
- `batch_id` (str, optional): Process specific import batch

**Response:**
```json
{
  "message": "Categorized 45 of 50 transactions",
  "total_transactions": 50,
  "rule_categorized": 32,
  "ml_categorized": 13,
  "failed_categorizations": 5,
  "success_rate": 0.90,
  "failed_details": [...]
}
```

## Configuration

### Environment Variables
Add to your `.env` file:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### Ollama Setup
1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Verify: `curl http://localhost:11434/api/version`

## Usage Examples

### Basic ML Categorization
```python
from app.services.categorization import CategorizationService

categorization_service = CategorizationService(db)

# Categorize with ML fallback
result = await categorization_service.categorize_single_transaction(
    transaction, 
    use_ml_fallback=True
)
```

### Batch Processing with ML
```python
# Categorize all uncategorized transactions
result = await categorization_service.categorize_user_transactions(
    user_id=1,
    use_ml_fallback=True
)

print(f"ML categorized: {result['ml_categorized']} transactions")
```

### Get Category Suggestions
```python
# Get suggestions without applying
suggestions = await categorization_service.suggest_categories_for_transaction(transaction)

if suggestions['has_suggestions']:
    primary = suggestions['primary_suggestion']
    print(f"Suggested: {primary['category']} ({primary['confidence']:.2f})")
```

## ML Features

### Few-Shot Learning
The system uses the user's existing categorized transactions as examples:
- Recent categorized transactions (up to 20)
- User's categorization rules (up to 10)
- Category distribution patterns

### Prompt Engineering
The ML prompts include:
- Transaction details (sanitized)
- User-specific examples
- Common financial categories
- Structured JSON response format

### Confidence Scoring
- **0.9-1.0**: Rule-based categorization (high confidence)
- **0.8-0.9**: Strong ML prediction with clear patterns
- **0.6-0.8**: Good ML prediction, suitable for auto-categorization
- **0.4-0.6**: Uncertain prediction, suggest to user
- **0.0-0.4**: Low confidence, manual review needed

### Performance Optimizations

#### Caching
- In-memory caching of ML responses
- 1-hour TTL for cache entries
- Automatic cache cleanup (max 1000 entries)

#### Batch Processing
- Groups similar transactions
- Processes representative transaction
- Applies prediction to similar transactions
- Adjusts confidence based on similarity

#### Error Handling
- Graceful fallback to rule-based categorization
- Timeout handling (30-second limit)
- Rate limiting protection
- Secure error messages

## Security Measures

### Data Sanitization
- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- SSN patterns → `[SSN]`
- Credit card numbers → `[CARD]`
- Text length limit: 500 characters

### Rate Limiting
- ML API calls are rate limited
- Fallback to rule-based on quota exceeded
- User-specific quotas

### Logging
- All ML predictions logged
- Performance metrics tracked
- Error incidents recorded
- User corrections tracked for accuracy

## Monitoring & Analytics

### Performance Metrics
- Prediction accuracy tracking
- Response time monitoring
- Cache hit rates
- Error rate tracking

### User Feedback Loop
- Track manual corrections
- Update accuracy metrics
- Improve prediction quality
- Generate better training data

## Testing

### Run ML Tests
```bash
cd backend
python test_ml_categorization.py
```

### Test Prerequisites
1. Ollama running on localhost:11434
2. Model pulled (e.g., `ollama pull llama2`)
3. Database configured and accessible

### Test Coverage
- Ollama connectivity
- Single transaction categorization
- Batch processing
- Performance metrics
- Health checks

## Troubleshooting

### Common Issues

#### Ollama Not Running
```
Error: Failed to connect to Ollama
Solution: Start Ollama service and ensure port 11434 is accessible
```

#### Model Not Found
```
Error: Model 'llama2' not found
Solution: Run `ollama pull llama2` to download the model
```

#### Low Accuracy
```
Issue: ML predictions are frequently incorrect
Solutions:
- Review training data quality
- Check prompt engineering
- Increase confidence thresholds
- Verify user categorization patterns
```

#### Slow Performance
```
Issue: ML categorization takes too long
Solutions:
- Enable caching
- Use batch processing
- Consider lighter model
- Optimize prompt length
```

## Future Enhancements

### Planned Features
1. **Model Fine-tuning**: Train custom models on user data
2. **Advanced Caching**: Redis-based distributed caching
3. **Multiple Models**: Support for different LLM providers
4. **Real-time Learning**: Continuous model improvement
5. **Category Suggestions**: Proactive category recommendations
6. **Vendor Recognition**: Enhanced merchant identification
7. **Amount-based Rules**: Category suggestions based on amount patterns

### Integration Roadmap
1. **Frontend Integration**: ML suggestions in UI
2. **Mobile Support**: Offline ML categorization
3. **API Extensions**: Third-party ML integration
4. **Analytics Dashboard**: ML performance visualization

## Performance Targets

### Current Benchmarks
- **Accuracy**: >85% for well-trained categories
- **Response Time**: <2 seconds average
- **Cache Hit Rate**: >60% for common transactions
- **Uptime**: >99.5% availability

### Production Requirements
- **Latency**: <100ms for cached predictions
- **Throughput**: >1000 predictions/minute
- **Accuracy**: >90% with user feedback
- **Memory**: <512MB for ML service

## Contributing

When contributing to ML categorization:

1. **Test Coverage**: Add tests for new ML features
2. **Security**: Ensure data sanitization
3. **Performance**: Monitor response times
4. **Documentation**: Update API docs and examples
5. **Backwards Compatibility**: Maintain API contracts

## Support

For ML categorization issues:
1. Check Ollama connectivity
2. Review application logs
3. Verify model availability
4. Test with sample data
5. Monitor performance metrics