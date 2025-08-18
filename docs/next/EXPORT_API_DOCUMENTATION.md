# FinGood Export API Documentation

## Overview

The FinGood Export API provides comprehensive data export functionality for financial transactions with multiple formats, advanced filtering, security validation, and rate limiting. This API supports CSV, Excel, and JSON exports with customizable column selection and formatting options.

## Features

### Export Formats
- **CSV**: Standard comma-separated values with customizable delimiters
- **Excel**: Multi-sheet workbooks with formatting, summaries, and charts
- **JSON**: Structured data with metadata and comprehensive transaction details

### Security Features
- **Rate Limiting**: 5 exports per hour for free tier, scalable by user tier
- **Data Validation**: Comprehensive input sanitization and validation
- **File Security**: Secure filename generation and temporary file handling
- **Access Control**: User-specific exports with proper authentication
- **Audit Logging**: Complete activity logging for compliance

### Filtering Options
- **Date Range**: From/to date filtering with validation
- **Categories**: Filter by transaction categories and subcategories  
- **Amount Range**: Min/max amount filtering with decimal precision
- **Transaction Type**: Income vs expense filtering
- **Text Search**: Vendor and description partial matching
- **Batch Filtering**: Filter by import batch ID

## API Endpoints

### 1. Quick CSV Export
```http
GET /api/v1/transactions/export/csv
```

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD format)
- `to_date` (optional): End date (YYYY-MM-DD format)
- `category` (optional): Filter by category
- `subcategory` (optional): Filter by subcategory
- `is_income` (optional): Filter by income/expense type
- `min_amount` (optional): Minimum amount filter
- `max_amount` (optional): Maximum amount filter

**Response:**
- Returns CSV file directly for small datasets
- Returns job ID for large exports requiring background processing

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/export/csv?from_date=2024-01-01&to_date=2024-12-31&category=Food%20%26%20Dining" \
  -H "Authorization: Bearer your-token" \
  -H "Accept: text/csv"
```

### 2. Excel Export
```http
GET /api/v1/transactions/export/excel
```

**Query Parameters:**
- All CSV parameters plus:
- `include_summary` (optional, default: true): Include summary sheet

**Features:**
- Multiple sheets (Transactions, Summary, Category Breakdown)
- Professional formatting with headers and styling
- Auto-sized columns and data validation
- Charts and visualizations (category breakdown pie chart)

**Response:**
Returns job ID for background processing due to Excel complexity.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/export/excel?from_date=2024-01-01&include_summary=true" \
  -H "Authorization: Bearer your-token"
```

### 3. JSON Export
```http
GET /api/v1/transactions/export/json
```

**Query Parameters:**
- All CSV parameters plus:
- `include_metadata` (optional, default: true): Include export metadata and raw data

**Features:**
- Structured JSON with metadata
- Complete transaction details including confidence scores
- Export summary statistics
- Category breakdowns and analysis

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/export/json?include_metadata=true" \
  -H "Authorization: Bearer your-token" \
  -H "Accept: application/json"
```

### 4. Custom Export (Advanced)
```http
POST /api/v1/transactions/export/custom
```

**Request Body:**
```json
{
  "export_format": "excel",
  "export_name": "Q4_Financial_Report",
  "filters": {
    "from_date": "2024-10-01",
    "to_date": "2024-12-31",
    "categories": ["Food & Dining", "Transportation", "Housing"],
    "min_amount": -5000.00,
    "max_amount": 0.00,
    "is_income": false
  },
  "columns": {
    "include_id": true,
    "include_date": true,
    "include_amount": true,
    "include_description": true,
    "include_vendor": true,
    "include_category": true,
    "include_subcategory": true,
    "include_is_income": true,
    "include_confidence_score": true,
    "include_created_at": false,
    "include_raw_data": false
  },
  "options": {
    "csv_delimiter": ",",
    "date_format": "MM/DD/YYYY",
    "currency_symbol": "$",
    "include_summary_sheet": true,
    "include_category_breakdown": true,
    "anonymize_vendor_names": false,
    "compress_output": false
  }
}
```

**Response:**
```json
{
  "job_id": "export_12345678-1234-5678-9abc-123456789abc",
  "status": "processing",
  "estimated_records": 1250,
  "estimated_completion_time": "2024-01-15T10:35:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "message": "Custom excel export created. Use /export/status/{job_id} to monitor progress."
}
```

### 5. Export Status Check
```http
GET /api/v1/transactions/export/status/{job_id}
```

**Response:**
```json
{
  "job_id": "export_12345678-1234-5678-9abc-123456789abc",
  "status": "completed",
  "progress_percentage": 100.0,
  "records_processed": 1250,
  "total_records": 1250,
  "current_operation": "Processing excel export",
  "started_at": "2024-01-15T10:30:15Z",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "error_message": null
}
```

**Status Values:**
- `pending`: Export job created but not started
- `processing`: Export is currently being processed
- `completed`: Export completed successfully
- `failed`: Export failed with error
- `cancelled`: Export was cancelled

### 6. Download Export
```http
GET /api/v1/transactions/export/download/{job_id}
```

**Response:**
Returns the export file with appropriate content-type headers and secure filename.

**Headers:**
- `Content-Type`: Appropriate MIME type (text/csv, application/json, etc.)
- `Content-Disposition`: Attachment with secure filename
- `Cache-Control`: No-cache headers for security

## Column Configuration Options

### Core Transaction Fields
- `include_id`: Transaction ID
- `include_date`: Transaction date
- `include_amount`: Transaction amount
- `include_description`: Transaction description
- `include_vendor`: Vendor/merchant name

### Categorization Fields
- `include_category`: Main category
- `include_subcategory`: Subcategory
- `include_is_income`: Income flag

### Processing Fields
- `include_source`: Data source (csv, api, etc.)
- `include_import_batch`: Import batch ID
- `include_is_categorized`: Categorization status
- `include_confidence_score`: AI confidence score

### Timestamps
- `include_created_at`: Record creation time
- `include_updated_at`: Last update time

### Additional Data
- `include_raw_data`: Original import data
- `include_meta_data`: Additional metadata

## Export Options Configuration

### File Options
- `compress_output`: Compress large files (.gz)
- `include_summary_sheet`: Excel summary sheet
- `include_category_breakdown`: Excel category analysis

### CSV Options
- `csv_delimiter`: Field delimiter (",", ";", "\t")
- `csv_quote_char`: Quote character ('"', "'")
- `csv_include_bom`: UTF-8 BOM for Excel compatibility

### Data Formatting
- `date_format`: Date format (YYYY-MM-DD, MM/DD/YYYY, etc.)
- `currency_symbol`: Currency symbol to include
- `decimal_places`: Number of decimal places (2, 3, 4)

### Security Options
- `anonymize_vendor_names`: Replace vendor names with generic labels
- `mask_amounts`: Partially mask transaction amounts

## Rate Limiting

### Rate Limits by User Tier
- **Free Tier**: 5 exports per hour, 10,000 records max
- **Premium Tier**: 25 exports per hour, 100,000 records max  
- **Enterprise Tier**: 100 exports per hour, 1,000,000 records max
- **Admin Tier**: 200 exports per hour, 10,000,000 records max

### Rate Limit Headers
When rate limited, the API returns:
```json
{
  "message": "Export rate limit exceeded",
  "retry_after": 3600,
  "limit": 5,
  "reset_time": "2024-01-15T11:00:00Z"
}
```

## Error Handling

### Common Error Codes
- `400 Bad Request`: Invalid parameters or filters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `413 Payload Too Large`: Export size exceeds tier limits
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server processing error

### Error Response Format
```json
{
  "error": "EXPORT_SIZE_LIMIT_EXCEEDED",
  "message": "Export size (50,000 records) exceeds limit for free tier (10,000 records)",
  "correlation_id": "err_12345678-1234-5678-9abc-123456789abc",
  "suggested_action": "Reduce date range or upgrade to premium tier"
}
```

## Security Considerations

### Data Protection
- All exports are user-specific with proper access control
- Sensitive data sanitization and PII removal
- Secure temporary file handling
- Automatic file cleanup after 24 hours

### Input Validation
- Comprehensive parameter validation
- SQL injection prevention
- XSS protection in exported data
- File path traversal protection

### Audit Logging
- All export requests logged with user context
- Security violations tracked and monitored
- Export download activity audited
- Failed attempts recorded for analysis

## Usage Examples

### Python Client Example
```python
import requests
import time
import json

class FinGoodExporter:
    def __init__(self, base_url, auth_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    def export_csv(self, from_date=None, to_date=None, **filters):
        """Quick CSV export with optional filters."""
        params = {k: v for k, v in filters.items() if v is not None}
        if from_date:
            params['from_date'] = from_date
        if to_date:
            params['to_date'] = to_date
        
        response = requests.get(
            f"{self.base_url}/api/v1/transactions/export/csv",
            params=params,
            headers=self.headers
        )
        
        if response.headers.get('content-type') == 'text/csv':
            return response.content  # Direct CSV content
        else:
            return response.json()   # Job ID for large exports
    
    def create_custom_export(self, export_config):
        """Create custom export with full configuration."""
        response = requests.post(
            f"{self.base_url}/api/v1/transactions/export/custom",
            json=export_config,
            headers=self.headers
        )
        return response.json()
    
    def wait_for_export(self, job_id, timeout=300):
        """Wait for export completion and download."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = requests.get(
                f"{self.base_url}/api/v1/transactions/export/status/{job_id}",
                headers=self.headers
            ).json()
            
            if status['status'] == 'completed':
                # Download the file
                response = requests.get(
                    f"{self.base_url}/api/v1/transactions/export/download/{job_id}",
                    headers=self.headers
                )
                return response.content
            elif status['status'] == 'failed':
                raise Exception(f"Export failed: {status.get('error_message')}")
            
            time.sleep(2)  # Poll every 2 seconds
        
        raise TimeoutError(f"Export did not complete within {timeout} seconds")

# Usage
exporter = FinGoodExporter("http://localhost:8000", "your-auth-token")

# Quick CSV export
csv_data = exporter.export_csv(
    from_date="2024-01-01",
    to_date="2024-12-31",
    category="Food & Dining"
)

# Custom Excel export
export_config = {
    "export_format": "excel",
    "export_name": "Monthly_Report",
    "filters": {
        "from_date": "2024-01-01",
        "to_date": "2024-01-31",
        "is_income": False
    },
    "options": {
        "include_summary_sheet": True,
        "date_format": "MM/DD/YYYY",
        "currency_symbol": "$"
    }
}

job = exporter.create_custom_export(export_config)
excel_data = exporter.wait_for_export(job['job_id'])

with open("monthly_report.xlsx", "wb") as f:
    f.write(excel_data)
```

### JavaScript/Node.js Example
```javascript
class FinGoodExporter {
    constructor(baseUrl, authToken) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        };
    }

    async exportCSV(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(
            `${this.baseUrl}/api/v1/transactions/export/csv?${params}`,
            { headers: this.headers }
        );
        
        if (response.headers.get('content-type').includes('text/csv')) {
            return await response.blob();
        } else {
            return await response.json();
        }
    }

    async createCustomExport(exportConfig) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/transactions/export/custom`,
            {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(exportConfig)
            }
        );
        return await response.json();
    }

    async waitForExport(jobId, timeout = 300000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const statusResponse = await fetch(
                `${this.baseUrl}/api/v1/transactions/export/status/${jobId}`,
                { headers: this.headers }
            );
            const status = await statusResponse.json();
            
            if (status.status === 'completed') {
                const downloadResponse = await fetch(
                    `${this.baseUrl}/api/v1/transactions/export/download/${jobId}`,
                    { headers: this.headers }
                );
                return await downloadResponse.blob();
            } else if (status.status === 'failed') {
                throw new Error(`Export failed: ${status.error_message}`);
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        throw new Error('Export timeout');
    }
}
```

## Best Practices

### Performance Optimization
1. **Use appropriate filters** to limit export size
2. **Choose minimal column sets** for faster processing
3. **Use CSV for large datasets** (faster than Excel)
4. **Consider compression** for large exports
5. **Poll status efficiently** (2-5 second intervals)

### Security Best Practices
1. **Validate all inputs** before sending requests
2. **Use HTTPS** for all API calls
3. **Store auth tokens securely** (not in code)
4. **Handle rate limits gracefully** with exponential backoff
5. **Clean up downloaded files** after processing

### Error Handling
1. **Implement retry logic** for transient errors
2. **Check rate limit headers** before requests
3. **Validate export size** before submission
4. **Handle job failures gracefully** with user feedback
5. **Log errors** for debugging and monitoring

## Troubleshooting

### Common Issues

**Export Size Too Large**
- Solution: Reduce date range or add more specific filters
- Alternative: Upgrade to higher tier for increased limits

**Rate Limit Exceeded**
- Solution: Implement exponential backoff retry logic
- Alternative: Upgrade tier for higher rate limits

**Export Job Stuck in Processing**
- Check job status endpoint for error messages
- Jobs auto-timeout after 10 minutes for safety

**Download Link Expired**
- Export files expire after 24 hours
- Re-run export if needed

**CSV Opening Incorrectly in Excel**
- Use `csv_include_bom: true` for better Excel compatibility
- Consider Excel export format instead

### Support
For additional support or feature requests, please contact the development team or refer to the API documentation at `/docs`.