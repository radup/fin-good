#!/usr/bin/env python3
"""
Example of ML categorization integration in FinGood

This example demonstrates how to use the ML categorization service
integrated with the existing rule-based categorization system.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

# Example transaction data structure
class MockTransaction:
    def __init__(self, id: int, user_id: int, description: str, vendor: str = None, amount: float = 0.0):
        self.id = id
        self.user_id = user_id
        self.description = description
        self.vendor = vendor
        self.amount = amount
        self.date = datetime.now()
        self.category = None
        self.subcategory = None
        self.is_categorized = False
        self.confidence_score = None
        self.meta_data = {}

async def demonstrate_ml_categorization():
    """
    Demonstrates the ML categorization workflow:
    1. Rule-based categorization first (high priority)
    2. ML categorization fallback for uncategorized transactions
    3. User feedback integration for continuous improvement
    """
    
    print("=== FinGood ML Categorization Demo ===\n")
    
    # Sample transactions that would typically be processed
    sample_transactions = [
        MockTransaction(1, 1, "STARBUCKS STORE #1234 SEATTLE WA", "Starbucks", -4.50),
        MockTransaction(2, 1, "RENT PAYMENT - DOWNTOWN APARTMENTS", "Downtown Apartments", -1200.00),
        MockTransaction(3, 1, "DIRECT DEPOSIT PAYROLL ACME CORP", "Acme Corp", 2500.00),
        MockTransaction(4, 1, "AMAZON.COM AMZN.COM/BILL", "Amazon", -89.99),
        MockTransaction(5, 1, "SHELL GAS STATION #567", "Shell", -45.67),
    ]
    
    print("📊 Sample Transactions to Categorize:")
    for tx in sample_transactions:
        print(f"  {tx.id}. {tx.description} - ${tx.amount}")
    
    print("\n🔄 Categorization Process:")
    
    # Step 1: Rule-based categorization simulation
    print("\n1️⃣  Rule-based Categorization:")
    
    # Simulate rule matches
    rule_matches = {
        1: ("Food & Dining", "Coffee Shops", 0.9),  # Starbucks
        2: ("Housing", "Rent", 0.9),  # Rent
        3: ("Income", "Salary", 0.9),  # Payroll
        # Amazon and Shell would not match rules, go to ML
    }
    
    for tx in sample_transactions:
        if tx.id in rule_matches:
            category, subcategory, confidence = rule_matches[tx.id]
            tx.category = category
            tx.subcategory = subcategory
            tx.is_categorized = True
            tx.confidence_score = confidence
            print(f"  ✅ Transaction {tx.id}: {category} -> {subcategory} (confidence: {confidence:.2f})")
        else:
            print(f"  ❌ Transaction {tx.id}: No rule match")
    
    # Step 2: ML categorization for uncategorized transactions
    print("\n2️⃣  ML Categorization Fallback:")
    
    # Simulate ML predictions for uncategorized transactions
    ml_predictions = {
        4: {  # Amazon
            "category": "Shopping",
            "subcategory": "Online Retail",
            "confidence": 0.85,
            "reasoning": "Online retailer based on description and vendor",
            "alternatives": [{"category": "Entertainment", "confidence": 0.65}]
        },
        5: {  # Shell
            "category": "Transportation",
            "subcategory": "Gas Stations",
            "confidence": 0.92,
            "reasoning": "Gas station chain, typical fuel purchase amount",
            "alternatives": [{"category": "Auto & Transport", "confidence": 0.78}]
        }
    }
    
    for tx in sample_transactions:
        if not tx.is_categorized and tx.id in ml_predictions:
            pred = ml_predictions[tx.id]
            tx.category = pred["category"]
            tx.subcategory = pred["subcategory"]
            tx.is_categorized = True
            tx.confidence_score = pred["confidence"]
            
            # Store ML metadata
            tx.meta_data = {
                "categorization_method": "ml",
                "ml_reasoning": pred["reasoning"],
                "ml_alternatives": pred["alternatives"]
            }
            
            print(f"  🤖 Transaction {tx.id}: {pred['category']} -> {pred['subcategory']}")
            print(f"     Confidence: {pred['confidence']:.2f} | Reason: {pred['reasoning']}")
    
    # Step 3: Results summary
    print("\n📈 Categorization Results:")
    
    categorized_count = sum(1 for tx in sample_transactions if tx.is_categorized)
    rule_count = sum(1 for tx in sample_transactions if tx.is_categorized and tx.confidence_score >= 0.9)
    ml_count = sum(1 for tx in sample_transactions if tx.meta_data.get("categorization_method") == "ml")
    
    print(f"  Total transactions: {len(sample_transactions)}")
    print(f"  Successfully categorized: {categorized_count}")
    print(f"  Rule-based categorizations: {rule_count}")
    print(f"  ML categorizations: {ml_count}")
    print(f"  Success rate: {categorized_count/len(sample_transactions):.1%}")
    
    # Step 4: User feedback simulation
    print("\n👤 User Feedback Integration:")
    
    # Simulate user correcting an ML categorization
    amazon_tx = sample_transactions[3]  # Amazon transaction
    if amazon_tx.meta_data.get("categorization_method") == "ml":
        print(f"  📝 User corrects Amazon transaction:")
        print(f"     ML suggested: {amazon_tx.category} -> {amazon_tx.subcategory}")
        
        # User correction
        amazon_tx.category = "Entertainment"
        amazon_tx.subcategory = "Digital Media"
        amazon_tx.meta_data.update({
            "categorization_method": "manual",
            "manual_correction": True,
            "original_ml_category": "Shopping"
        })
        
        print(f"     User corrected to: {amazon_tx.category} -> {amazon_tx.subcategory}")
        print(f"     📊 This correction improves ML accuracy for future predictions")
    
    # Step 5: API endpoints demonstration
    print("\n🌐 Available API Endpoints:")
    
    api_examples = [
        {
            "method": "POST",
            "endpoint": "/api/v1/transactions/categorize",
            "description": "Bulk categorize with ML fallback",
            "params": "?use_ml_fallback=true&batch_id=upload_2024_01_15"
        },
        {
            "method": "POST",
            "endpoint": "/api/v1/ml/{transaction_id}/categorize",
            "description": "Real-time ML categorization",
            "params": ""
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/ml/{transaction_id}/suggestions",
            "description": "Get ML suggestions without applying",
            "params": ""
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/ml/performance-metrics",
            "description": "ML accuracy and performance metrics",
            "params": ""
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/ml/health-status",
            "description": "Check ML service and Ollama status",
            "params": ""
        }
    ]
    
    for api in api_examples:
        print(f"  {api['method']} {api['endpoint']}{api['params']}")
        print(f"      → {api['description']}")
    
    # Step 6: Performance characteristics
    print("\n⚡ Performance Characteristics:")
    
    performance_specs = [
        "🎯 Accuracy: >85% for trained categories",
        "⏱️  Response Time: <2s average, <100ms cached",
        "🔄 Cache Hit Rate: >60% for common transactions", 
        "📊 Throughput: >1000 predictions/minute",
        "🛡️  Security: Data sanitization, rate limiting",
        "🔧 Fallback: Graceful degradation to rule-based",
    ]
    
    for spec in performance_specs:
        print(f"  {spec}")
    
    print("\n✅ ML Categorization Integration Complete!")
    print("\n📖 For detailed documentation, see: backend/ML_CATEGORIZATION_README.md")
    print("🧪 To run tests: python backend/test_ml_categorization.py")
    
def main():
    """Run the demonstration"""
    asyncio.run(demonstrate_ml_categorization())

if __name__ == "__main__":
    main()