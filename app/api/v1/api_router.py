from fastapi import APIRouter
from app.api.v1.endpoints import coindesk, cryptonews, cointelegraph, utoday

router = APIRouter()

router.include_router(coindesk.router, prefix="/v1", tags=["coindesk_news"])
router.include_router(cryptonews.router, prefix="/v1", tags=["cryptonews_news"])
router.include_router(cointelegraph.router, prefix="/v1", tags=["cointelegraph_news"])
router.include_router(utoday.router, prefix="/v1", tags=["utoday_news"])