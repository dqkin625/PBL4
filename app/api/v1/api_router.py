from fastapi import APIRouter
from app.api.v1.endpoints import news, stats, get_db

router = APIRouter()

router.include_router(news.router, prefix="/v1", tags=["news"])
router.include_router(stats.router, prefix="/v1", tags=["stats"])
router.include_router(get_db.router, prefix="/v1", tags=["get from database"])