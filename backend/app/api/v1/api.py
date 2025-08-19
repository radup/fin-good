from fastapi import APIRouter
from app.api.v1.endpoints import auth, transactions, categories, categorization_rules, upload, analytics, monitoring, rate_limit_admin, cache, reports

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(categorization_rules.router, prefix="/categorization-rules", tags=["categorization rules"])
api_router.include_router(upload.router, prefix="/upload", tags=["file upload"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache management"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(rate_limit_admin.router, prefix="/admin/rate-limits", tags=["rate limiting admin"])
