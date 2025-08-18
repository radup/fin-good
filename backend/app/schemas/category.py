from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    parent_category: Optional[str] = None
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RuleBase(BaseModel):
    pattern: str
    pattern_type: str  # 'regex', 'keyword', 'vendor'
    category: str
    subcategory: Optional[str] = None
    priority: int = 1

class RuleCreate(RuleBase):
    pass

class RuleResponse(RuleBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
