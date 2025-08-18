from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from decimal import Decimal

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Core transaction data
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    vendor = Column(String(255), nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    is_income = Column(Boolean, default=False)
    
    # Source tracking
    source = Column(String(50), nullable=False)  # 'csv', 'quickbooks', 'xero'
    source_id = Column(String(255), nullable=True)  # Original ID from source
    import_batch = Column(String(100), nullable=True)  # Batch ID for grouping imports
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    is_categorized = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)  # ML confidence for categorization
    
    # Additional data (flexible JSON field for different formats)
    raw_data = Column(JSON, nullable=True)  # Original CSV row data
    meta_data = Column(JSON, nullable=True)  # Additional processing metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, description='{self.description[:50]}...')>"

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    parent_category = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class CategorizationRule(Base):
    __tablename__ = "categorization_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    pattern = Column(String(255), nullable=False)  # Regex pattern or keyword
    pattern_type = Column(String(50), nullable=False)  # 'regex', 'keyword', 'vendor'
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    priority = Column(Integer, default=1)  # Higher priority rules applied first
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CategorizationRule(id={self.id}, pattern='{self.pattern}', category='{self.category}')>"
