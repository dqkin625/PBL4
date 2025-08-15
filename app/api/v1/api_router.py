from fastapi import APIRouter
from app.api.v1.endpoints import coindesk, cryptonews

router = APIRouter()

router.include_router(coindesk.router, prefix="/v1", tags=["coindesk_news"])
router.include_router(cryptonews.router, prefix="/v1", tags=["cryptonews_news"])