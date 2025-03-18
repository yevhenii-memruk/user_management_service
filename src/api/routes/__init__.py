from fastapi import APIRouter

from src.api.routes.auth import router as auth_router
from src.api.routes.health import router as health_router
from src.api.routes.root import router as root_router
from src.api.routes.user import router as user_router

router = APIRouter()

router.include_router(user_router, tags=["users"])
router.include_router(auth_router, prefix="/auth", tags=["authentication"])
router.include_router(health_router, tags=["healthcheck"])
router.include_router(root_router, tags=["root"])
