#!/usr/bin/env python3
"""
Simple demonstration of export functionality concepts.
This script shows the core ideas without requiring full application setup.
"""

import json
import csv
import tempfile
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from pathlib import Path

def demo_export_concepts():
    """Demonstrate the core export concepts."""
    print("🚀 FinGood Export Functionality Concepts Demo")
    print("=" * 60)
    
    # Sample transaction data
    transactions = [
        {
            "id": 1,
            "date": "2024-01-15",
            "amount": -50.00,
            "description": "Coffee shop purchase",
            "vendor": "Starbucks",
            "category": "Food & Dining",
            "subcategory": "Coffee",
            "is_income": False,
            "is_categorized": True,
            "confidence_score": 0.95
        },
        {
            "id": 2,
            "date": "2024-01-14",
            "amount": -120.50,
            "description": "Grocery shopping",
            "vendor": "Whole Foods",
            "category": "Food & Dining",
            "subcategory": "Groceries",
            "is_income": False,
            "is_categorized": True,
            "confidence_score": 0.88
        },
        {
            "id": 3,
            "date": "2024-01-13",
            "amount": 2500.00,
            "description": "Monthly salary",
            "vendor": "Company Inc",
            "category": "Income",
            "subcategory": "Salary",
            "is_income": True,
            "is_categorized": True,
            "confidence_score": 1.0
        },
        {
            "id": 4,
            "date": "2024-01-12",
            "amount": -45.00,
            "description": "Gas station",
            "vendor": "Shell",
            "category": "Transportation",
            "subcategory": "Gas",
            "is_income": False,
            "is_categorized": True,
            "confidence_score": 0.92
        },
        {
            "id": 5,
            "date": "2024-01-11",
            "amount": -1200.00,
            "description": "Monthly rent",
            "vendor": "Property Management Co",
            "category": "Housing",
            "subcategory": "Rent",
            "is_income": False,
            "is_categorized": True,
            "confidence_score": 0.99
        }
    ]
    
    print(f"Sample data: {len(transactions)} transactions")
    print()
    
    # Demo 1: CSV Export
    demo_csv_export(transactions)
    
    # Demo 2: JSON Export with metadata
    demo_json_export(transactions)
    
    # Demo 3: Filtering concepts
    demo_filtering_concepts(transactions)
    
    # Demo 4: Security validation concepts
    demo_security_concepts()
    
    # Demo 5: Rate limiting concepts
    demo_rate_limiting_concepts()
    
    print("\n" + "=" * 60)
    print("✅ Export concepts demonstration completed!")

def demo_csv_export(transactions: List[Dict]):
    """Demonstrate CSV export functionality."""
    print("=== CSV Export Demo ===")
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        fieldnames = [
            'ID', 'Date', 'Amount', 'Description', 'Vendor', 
            'Category', 'Subcategory', 'Is Income', 'Confidence Score'
        ]
        
        writer = csv.DictWriter(tmp, fieldnames=fieldnames)
        writer.writeheader()
        
        for tx in transactions:
            writer.writerow({
                'ID': tx['id'],
                'Date': tx['date'],
                'Amount': f"${tx['amount']:.2f}",
                'Description': tx['description'],
                'Vendor': tx['vendor'],
                'Category': tx['category'],
                'Subcategory': tx['subcategory'],
                'Is Income': 'Yes' if tx['is_income'] else 'No',
                'Confidence Score': f"{tx['confidence_score']:.2f}"
            })
        
        csv_path = tmp.name
    
    # Read and display results
    with open(csv_path, 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
        
    print(f"✅ CSV export created: {len(lines)} lines (including header)")
    print("Sample CSV content:")
    for i, line in enumerate(lines[:3]):
        print(f"  {i+1}: {line}")
    if len(lines) > 3:
        print(f"  ... and {len(lines) - 3} more lines")
    
    # File size
    file_size = Path(csv_path).stat().st_size
    print(f"File size: {file_size} bytes")
    
    # Cleanup
    Path(csv_path).unlink()
    print()

def demo_json_export(transactions: List[Dict]):
    """Demonstrate JSON export with metadata."""
    print("=== JSON Export Demo ===")
    
    # Calculate summary statistics
    total_income = sum(tx['amount'] for tx in transactions if tx['is_income'])
    total_expenses = sum(abs(tx['amount']) for tx in transactions if not tx['is_income'])
    categories = list(set(tx['category'] for tx in transactions))
    
    # Create structured export data
    export_data = {
        "metadata": {
            "total_records": len(transactions),
            "export_date": datetime.now().isoformat(),
            "exported_by": "demo_user",
            "export_format": "json",
            "date_range": {
                "from": min(tx['date'] for tx in transactions),
                "to": max(tx['date'] for tx in transactions)
            },
            "summary": {
                "total_income": f"${total_income:.2f}",
                "total_expenses": f"${total_expenses:.2f}",
                "net_amount": f"${(total_income - total_expenses):.2f}",
                "unique_categories": len(categories),
                "categories_list": sorted(categories)
            }
        },
        "transactions": transactions
    }
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(export_data, tmp, indent=2, default=str)
        json_path = tmp.name
    
    # Display results
    file_size = Path(json_path).stat().st_size
    print(f"✅ JSON export created: {file_size} bytes")
    print("Export metadata:")
    print(f"  Total records: {export_data['metadata']['total_records']}")
    print(f"  Date range: {export_data['metadata']['date_range']['from']} to {export_data['metadata']['date_range']['to']}")
    print(f"  Total income: {export_data['metadata']['summary']['total_income']}")
    print(f"  Total expenses: {export_data['metadata']['summary']['total_expenses']}")
    print(f"  Net amount: {export_data['metadata']['summary']['net_amount']}")
    print(f"  Categories: {', '.join(export_data['metadata']['summary']['categories_list'])}")
    
    # Cleanup
    Path(json_path).unlink()
    print()

def demo_filtering_concepts(transactions: List[Dict]):
    """Demonstrate filtering concepts."""
    print("=== Filtering Concepts Demo ===")
    
    # Date range filtering
    target_date = "2024-01-13"
    date_filtered = [tx for tx in transactions if tx['date'] >= target_date]
    print(f"Date filter (>= {target_date}): {len(date_filtered)} transactions")
    
    # Category filtering
    target_categories = ['Food & Dining', 'Transportation']
    category_filtered = [tx for tx in transactions if tx['category'] in target_categories]
    print(f"Category filter ({', '.join(target_categories)}): {len(category_filtered)} transactions")
    
    # Amount range filtering
    min_amount, max_amount = -100.0, 0.0
    amount_filtered = [tx for tx in transactions 
                      if min_amount <= tx['amount'] <= max_amount]
    print(f"Amount filter (${min_amount} to ${max_amount}): {len(amount_filtered)} transactions")
    
    # Income vs expense filtering
    expense_filtered = [tx for tx in transactions if not tx['is_income']]
    income_filtered = [tx for tx in transactions if tx['is_income']]
    print(f"Expense transactions: {len(expense_filtered)}")
    print(f"Income transactions: {len(income_filtered)}")
    
    # Combined filtering example
    complex_filtered = [tx for tx in transactions 
                       if not tx['is_income'] 
                       and tx['category'] in ['Food & Dining', 'Transportation']
                       and tx['amount'] >= -100.0]
    print(f"Complex filter (expenses, food/transport, >= -$100): {len(complex_filtered)} transactions")
    print()

def demo_security_concepts():
    """Demonstrate security validation concepts."""
    print("=== Security Concepts Demo ===")
    
    # Export size validation by tier
    size_limits = {
        "free": 10000,
        "premium": 100000,
        "enterprise": 1000000
    }
    
    test_sizes = [5000, 50000, 500000]
    
    for size in test_sizes:
        print(f"Export size: {size:,} records")
        for tier, limit in size_limits.items():
            status = "✅ ALLOWED" if size <= limit else "❌ BLOCKED"
            print(f"  {tier.capitalize()} tier ({limit:,} limit): {status}")
        print()
    
    # Filename sanitization
    unsafe_filenames = [
        "../../etc/passwd.csv",
        "transactions<script>alert('xss')</script>.csv",
        "normal_file.csv",
        "transactions with spaces.csv"
    ]
    
    print("Filename sanitization:")
    for filename in unsafe_filenames:
        # Simple sanitization logic (mimics the real implementation)
        import re
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        if len(safe_filename) > 50:
            safe_filename = safe_filename[:40] + "_truncated.csv"
        
        safe_filename = f"{safe_filename.rsplit('.', 1)[0]}_20240115_103000.csv"
        
        print(f"  '{filename}' -> '{safe_filename}'")
    print()

def demo_rate_limiting_concepts():
    """Demonstrate rate limiting concepts."""
    print("=== Rate Limiting Concepts Demo ===")
    
    # Rate limits by tier
    rate_limits = {
        "free": {"per_hour": 5, "per_day": 20},
        "premium": {"per_hour": 25, "per_day": 100},
        "enterprise": {"per_hour": 100, "per_day": 500},
        "admin": {"per_hour": 200, "per_day": 1000}
    }
    
    print("Export rate limits by user tier:")
    for tier, limits in rate_limits.items():
        print(f"  {tier.capitalize()}: {limits['per_hour']} per hour, {limits['per_day']} per day")
    
    print()
    
    # Simulate rate limit checking
    user_requests = {"current_hour": 3, "current_day": 15}
    user_tier = "free"
    
    limits = rate_limits[user_tier]
    hour_remaining = limits["per_hour"] - user_requests["current_hour"]
    day_remaining = limits["per_day"] - user_requests["current_day"]
    
    print(f"Current user ({user_tier} tier) status:")
    print(f"  Requests this hour: {user_requests['current_hour']}/{limits['per_hour']} ({hour_remaining} remaining)")
    print(f"  Requests today: {user_requests['current_day']}/{limits['per_day']} ({day_remaining} remaining)")
    
    if hour_remaining > 0 and day_remaining > 0:
        print("  Status: ✅ REQUEST ALLOWED")
    else:
        print("  Status: ❌ RATE LIMITED")
        if hour_remaining <= 0:
            print("    Reason: Hourly limit exceeded")
        if day_remaining <= 0:
            print("    Reason: Daily limit exceeded")
    print()

if __name__ == "__main__":
    demo_export_concepts()