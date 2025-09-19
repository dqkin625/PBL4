from fastapi import APIRouter, HTTPException
from app.services.db_service import get_news_from_db, get_bulletins_from_db
from app.utils.response import StatusMessage, response_data

router = APIRouter()

@router.get("/get_news_db")
def get_news_db():
    """
    Lấy toàn bộ bài viết có trong database (giới hạn 1000 bài viết).
    """
    try:
        news = get_news_from_db(limit=1000)
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data=news
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy bài viết từ database: {str(e)}")

@router.get("/get_bulletin_db")
def get_bulletin_db():
    """
    Lấy bulletin mới nhất có trong database.
    """
    try:
        bulletins = get_bulletins_from_db(limit=1, sort_order=-1)
        latest_bulletin = bulletins[0] if bulletins else None
        if not latest_bulletin:
            return response_data(
                status_code=404,
                message=StatusMessage.NOT_FOUND,
                data=None
            )
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data=latest_bulletin
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy bulletin mới nhất: {str(e)}")
