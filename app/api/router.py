from fastapi import APIRouter
from app.api.endpoints import files, health

api_router = APIRouter()

# Include files router under /api/files
api_router.include_router(files.router, prefix="/files", tags=["Files & Measurements"])

# Include health endpoint
api_router.include_router(health.router, tags=["Health"])
