#!/usr/bin/env python3
"""
Database setup script for FinGood
Creates database tables and initial data
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import engine, Base
from app.models.user import User
from app.models.transaction import Transaction, Category, CategorizationRule
from app.core.config import settings
from passlib.context import CryptContext

def setup_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def create_default_categories():
    """Create default categories for new users"""
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    
    default_categories = [
        {"name": "Food & Dining", "color": "#ef4444"},
        {"name": "Transportation", "color": "#3b82f6"},
        {"name": "Shopping", "color": "#8b5cf6"},
        {"name": "Entertainment", "color": "#f59e0b"},
        {"name": "Healthcare", "color": "#10b981"},
        {"name": "Utilities", "color": "#6b7280"},
        {"name": "Insurance", "color": "#84cc16"},
        {"name": "Travel", "color": "#06b6d4"},
        {"name": "Business Expenses", "color": "#f97316"},
        {"name": "Income", "color": "#22c55e"},
    ]
    
    db = SessionLocal()
    try:
        # Get the demo user
        demo_user = db.query(User).filter(User.email == "demo@fingood.com").first()
        
        if demo_user:
            for cat_data in default_categories:
                # Check if category already exists for this user
                existing = db.query(Category).filter(
                    Category.name == cat_data["name"],
                    Category.user_id == demo_user.id
                ).first()
                
                if not existing:
                    category = Category(
                        user_id=demo_user.id,
                        name=cat_data["name"],
                        color=cat_data["color"],
                        is_default=True
                    )
                    db.add(category)
            
            db.commit()
            print("✅ Default categories created for demo user")
        else:
            print("⚠️  Demo user not found, skipping default categories")
    except Exception as e:
        print(f"❌ Error creating default categories: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_user():
    """Create a sample user for testing"""
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    db = SessionLocal()
    try:
        # Check if sample user already exists
        existing_user = db.query(User).filter(User.email == "demo@fingood.com").first()
        
        if not existing_user:
            hashed_password = pwd_context.hash("demo123")
            user = User(
                email="demo@fingood.com",
                hashed_password=hashed_password,
                full_name="Demo User",
                company_name="Demo Company",
                business_type="Consulting"
            )
            db.add(user)
            db.commit()
            print("✅ Sample user created (demo@fingood.com / demo123)")
        else:
            print("ℹ️  Sample user already exists")
    except Exception as e:
        print(f"❌ Error creating sample user: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🚀 Setting up FinGood database...")
    
    try:
        setup_database()
        create_default_categories()
        create_sample_user()
        
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend: cd backend && python main.py")
        print("2. Start the frontend: npm run dev")
        print("3. Visit http://localhost:3000")
        print("4. Login with demo@fingood.com / demo123")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
