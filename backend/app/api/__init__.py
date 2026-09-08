"""API Router exports for FastAPI backend."""

from fastapi import APIRouter
from backend.app.api.routes_videos import router as videos_router
from backend.app.api.routes_activity import router as activity_router
from backend.app.api.routes_analytics import router as analytics_router
from backend.app.api.routes_calendar import router as calendar_router
from backend.app.api.routes_providers import router as providers_router
from backend.app.api.routes_autopilot import router as autopilot_router
from backend.app.api.routes_settings import router as settings_router
from backend.app.api.routes_youtube_auth import router as youtube_auth_router
from backend.app.api.routes_style import router as style_router
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_vault import router as vault_router
from backend.app.api.routes_admin import router as admin_router
from backend.app.api.routes_tenant_youtube import router as tenant_youtube_router

api_router = APIRouter(prefix="/api")

api_router.include_router(videos_router)
api_router.include_router(activity_router)
api_router.include_router(analytics_router)
api_router.include_router(calendar_router)
api_router.include_router(providers_router)
api_router.include_router(autopilot_router)
api_router.include_router(settings_router)
api_router.include_router(youtube_auth_router)
api_router.include_router(style_router)
api_router.include_router(auth_router)
api_router.include_router(vault_router)
api_router.include_router(admin_router)
api_router.include_router(tenant_youtube_router)

__all__ = ["api_router"]
