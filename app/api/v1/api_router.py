from fastapi import APIRouter
from app.api.v1.endpoints import coindesk

router = APIRouter()

router.include_router(coindesk.router, prefix="/v1", tags=["coindesk_news"])