#!/usr/bin/env python3
"""
Create Sigmund user for FinGood login
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

def create_sigmund_user():
    """Create the sigmund user for login"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    db = SessionLocal()
    try:
        # Check if sigmund user already exists
        existing_user = db.query(User).filter(User.email == "sigmund@spendsanalysis.com").first()
        
        if not existing_user:
            hashed_password = pwd_context.hash("sigmund123_")
            user = User(
                email="sigmund@spendsanalysis.com",
                hashed_password=hashed_password,
                full_name="Dr. Sigmund Spend",
                company_name="Spend's Analysis",
                business_type="Financial Therapy",
                is_active=True
            )
            db.add(user)
            db.commit()
            print("✅ Sigmund user created successfully!")
            print("   Email: sigmund@spendsanalysis.com")
            print("   Password: sigmund123_")
        else:
            # Update password if user exists
            existing_user.hashed_password = pwd_context.hash("sigmund123_")
            existing_user.is_active = True
            db.commit()
            print("✅ Sigmund user updated successfully!")
            print("   Email: sigmund@spendsanalysis.com")
            print("   Password: sigmund123_")
    except Exception as e:
        print(f"❌ Error creating/updating sigmund user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔐 Creating Sigmund user...")
    create_sigmund_user()