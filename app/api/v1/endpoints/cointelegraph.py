from fastapi import APIRouter, FastAPI
from app.services.cointelegraph_service import get_article_links, scrape_article

router = APIRouter()

COINTELEGRAPH_URL = "https://cointelegraph.com/category/latest-news"

@router.get('/cointelegraph_news')
def crawl_articles():
    try:
        links = get_article_links(COINTELEGRAPH_URL)
        articles = [scrape_article(link) for link in links]
        return {
            "data": articles
        }
    except Exception as e:
        return {
            "error": str(e)
        }
            