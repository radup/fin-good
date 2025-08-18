# Categorization Rules Management API

This document describes the comprehensive categorization rules management API endpoints implemented for the FinGood application.

## Overview

The categorization rules API provides advanced functionality for managing transaction categorization rules, including CRUD operations, rule testing, performance analytics, bulk operations, and more.

## Base URL

All endpoints are prefixed with `/api/v1/categorization-rules`

## Authentication

All endpoints require user authentication via cookie-based session authentication.

## Endpoints

### 1. List Rules

**GET** `/`

Get paginated list of categorization rules with filtering and sorting.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Number of rules per page
- `active_only` (bool, default: true): Show only active rules
- `category` (string, optional): Filter by category
- `pattern_type` (string, optional): Filter by pattern type
- `search` (string, optional): Search in pattern or category
- `sort_by` (string, default: "priority"): Sort field (priority, created_at, category, pattern)
- `sort_desc` (bool, default: true): Sort in descending order

**Response:** `RuleListResponse`
```json
{
  "rules": [...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

### 2. Create Rule

**POST** `/`

Create a new categorization rule with validation.

**Request Body:** `RuleCreate`
```json
{
  "pattern": "starbucks|coffee",
  "pattern_type": "regex",
  "category": "Meals & Entertainment",
  "subcategory": "Coffee",
  "priority": 5,
  "is_active": true
}
```

**Response:** `RuleResponse`

### 3. Get Specific Rule

**GET** `/{rule_id}`

Get details of a specific categorization rule.

**Response:** `RuleResponse`

### 4. Update Rule

**PUT** `/{rule_id}`

Update an existing categorization rule.

**Request Body:** `RuleUpdate` (all fields optional)
```json
{
  "pattern": "starbucks|coffee|cafe",
  "priority": 7,
  "is_active": false
}
```

**Response:** `RuleResponse`

### 5. Delete Rule

**DELETE** `/{rule_id}`

Delete a categorization rule.

**Response:** Success message

### 6. Test Rule

**POST** `/test`

Test a rule pattern against existing transactions to see potential matches.

**Request Body:** `RuleTestRequest`
```json
{
  "pattern": "uber|lyft",
  "pattern_type": "regex",
  "test_description": "uber ride",
  "test_vendor": null,
  "limit": 10
}
```

**Response:** `RuleTestResponse`
```json
{
  "pattern": "uber|lyft",
  "pattern_type": "regex",
  "matches_found": 15,
  "total_transactions": 1000,
  "match_rate": 0.015,
  "sample_matches": [...],
  "potential_conflicts": [...]
}
```

### 7. Validate Rule

**POST** `/validate`

Validate a rule before creation or update.

**Query Parameters:**
- `pattern` (string): Rule pattern
- `pattern_type` (string): Pattern type
- `category` (string): Target category
- `subcategory` (string, optional): Target subcategory
- `rule_id` (int, optional): Exclude this rule ID from conflict detection

**Response:** `RuleValidationResult`
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Category 'New Category' does not exist"],
  "conflicts": [],
  "estimated_matches": 25
}
```

### 8. Bulk Create Rules

**POST** `/bulk`

Create multiple categorization rules in one operation.

**Request Body:** `BulkRuleCreate`
```json
{
  "rules": [
    {
      "pattern": "restaurant",
      "pattern_type": "keyword",
      "category": "Meals & Entertainment",
      "priority": 5
    },
    {
      "pattern": "gas|fuel",
      "pattern_type": "regex", 
      "category": "Transportation",
      "subcategory": "Fuel",
      "priority": 6
    }
  ]
}
```

**Response:** `BulkOperationResponse`

### 9. Performance Analytics

**GET** `/performance/analytics`

Get comprehensive rule performance analytics.

**Response:** `PerformanceAnalytics`
```json
{
  "total_rules": 25,
  "active_rules": 20,
  "inactive_rules": 5,
  "total_matches": 1500,
  "average_accuracy": 0.85,
  "top_performing_rules": [...],
  "underperforming_rules": [...],
  "category_distribution": {
    "Transportation": 450,
    "Meals & Entertainment": 300
  }
}
```

### 10. Detect Duplicates

**GET** `/duplicates`

Detect duplicate or similar rules.

**Response:** Array of duplicate rule information
```json
[
  {
    "original_rule_id": 1,
    "original_pattern": "starbucks",
    "duplicate_rule_id": 5,
    "duplicate_pattern": "starbucks",
    "type": "exact_duplicate",
    "same_category": true
  }
]
```

### 11. Optimize Priorities

**POST** `/optimize-priorities`

Automatically optimize rule priorities based on effectiveness.

**Response:**
```json
{
  "optimized_count": 8,
  "changes": [
    {
      "rule_id": 3,
      "pattern": "uber",
      "old_priority": 2,
      "new_priority": 8
    }
  ],
  "total_rules": 20
}
```

### 12. Export Rules

**GET** `/export`

Export user's categorization rules.

**Query Parameters:**
- `format` (string, default: "json"): Export format
- `active_only` (bool, default: false): Export only active rules

**Response:** `RuleExportResponse`

### 13. Import Rules

**POST** `/import`

Import categorization rules from exported data.

**Request Body:** `RuleImportRequest`
```json
{
  "rules": [...],
  "overwrite_existing": false,
  "validate_only": false
}
```

**Response:** `RuleImportResponse`

### 14. Get Templates

**GET** `/templates`

Get predefined rule templates for common categories.

**Query Parameters:**
- `category` (string, optional): Filter templates by category

**Response:** `RuleTemplateResponse`

### 15. Apply Template

**POST** `/apply-template`

Apply a predefined rule template to user's account.

**Query Parameters:**
- `template_name` (string): Name of the template to apply

**Response:** Success message with creation results

### 16. Apply Rule to Transactions

**POST** `/{rule_id}/apply`

Apply a specific rule to existing transactions.

**Query Parameters:**
- `force_recategorize` (bool, default: false): Force recategorization of already categorized transactions

**Response:** Background task confirmation

## Pattern Types

The API supports the following pattern types:

1. **keyword**: Simple case-insensitive substring matching
2. **regex**: Regular expression matching (case-insensitive)
3. **vendor**: Match against vendor field specifically
4. **exact**: Exact string matching (case-insensitive)
5. **contains**: Same as keyword (case-insensitive substring)

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Validation errors or invalid input
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Schema validation errors
- `500 Internal Server Error`: Server-side errors

Error responses include detailed error messages and, where applicable, validation error details.

## Usage Examples

### Create a Simple Keyword Rule
```bash
curl -X POST "/api/v1/categorization-rules/" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "starbucks",
    "pattern_type": "keyword",
    "category": "Meals & Entertainment",
    "subcategory": "Coffee",
    "priority": 5
  }'
```

### Test a Regex Rule
```bash
curl -X POST "/api/v1/categorization-rules/test" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "uber|lyft|taxi",
    "pattern_type": "regex",
    "limit": 5
  }'
```

### Get Performance Analytics
```bash
curl -X GET "/api/v1/categorization-rules/performance/analytics"
```

### Apply Restaurant Template
```bash
curl -X POST "/api/v1/categorization-rules/apply-template?template_name=Restaurant%20%26%20Dining"
```

## Security Features

- **User Isolation**: Users can only access their own rules
- **Input Validation**: Comprehensive validation of all inputs
- **Pattern Validation**: Regex patterns are validated before compilation
- **Rate Limiting**: Background tasks prevent system overload
- **Audit Logging**: All rule changes are logged for security

## Performance Considerations

- **Caching**: Compiled regex patterns are cached for performance
- **Pagination**: Large result sets are paginated
- **Background Processing**: Heavy operations like rule application run in background
- **Batch Operations**: Bulk operations are optimized for performance
- **Index Optimization**: Database queries are optimized with proper indexing

## Integration with Existing System

The new API endpoints integrate seamlessly with the existing FinGood system:

- **Authentication**: Uses existing cookie-based authentication
- **Database**: Works with existing PostgreSQL schema
- **Categorization Service**: Extends existing categorization functionality
- **Transaction Processing**: Integrates with transaction categorization workflow
- **Analytics**: Connects with existing analytics endpoints for comprehensive insights