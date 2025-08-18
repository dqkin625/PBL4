from fastapi import APIRouter

from app.services.coingape_service import get_news_links, scrape_article

router = APIRouter()

COINGAPE_RSS_FEED_URL = "https://coingape.com/category/news/"

@router.get("/coingape_news")
def get_news():
    news = []
    links = get_news_links(COINGAPE_RSS_FEED_URL)
    for link in links:
        news.append(scrape_article(link))
    return {"data": news}