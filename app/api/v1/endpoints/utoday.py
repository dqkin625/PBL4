from fastapi import APIRouter, FastAPI
from app.services.utoday_service import get_article_links, scrape_article

router = APIRouter()

UTODAY_URL = "https://u.today/rss.php"

@router.get('/utoday_news')
def crawl_articles():
    try:
        links = get_article_links(UTODAY_URL)
        articles = [scrape_article(link) for link in links]
        return {
            "data": articles
        }
    except Exception as e:
        return {
            "error": str(e)
        }
            