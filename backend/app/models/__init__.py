"""
Models package for FinGood Financial Platform

This module imports all SQLAlchemy models to ensure proper initialization
and relationship resolution.
"""

# Import models in the correct order to resolve relationships
from app.models.user import User, RevokedToken, PasswordResetToken
from app.models.transaction import Transaction, Category, CategorizationRule
from app.models.export_job import ExportJob, ExportTemplate
from app.models.budget import (
    Budget, BudgetItem, BudgetActual, BudgetVarianceReport, 
    BudgetTemplate, BudgetGoal
)

# Export all models for easy importing
__all__ = [
    "User", "RevokedToken", "PasswordResetToken",
    "Transaction", "Category", "CategorizationRule", 
    "ExportJob", "ExportTemplate",
    "Budget", "BudgetItem", "BudgetActual", "BudgetVarianceReport",
    "BudgetTemplate", "BudgetGoal"
]