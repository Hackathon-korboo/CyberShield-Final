"""Extended API router aggregator including Phase 03 AI routes."""

from fastapi import APIRouter

from backend.app.api.routes.ai_analysis import router as ai_analysis_router

ai_api_router = APIRouter()
ai_api_router.include_router(ai_analysis_router)
