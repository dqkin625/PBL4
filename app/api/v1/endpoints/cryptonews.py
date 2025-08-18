from datetime import datetime
from zoneinfo import ZoneInfo
import feedparser
from bs4 import BeautifulSoup
from fastapi import APIRouter

router = APIRouter()

CRYPTONEWS_RSS_FEED_URL = "https://cryptonews.com/news/feed/"

@router.get("/cryptonews_news")
def get_news():
    feed = feedparser.parse(CRYPTONEWS_RSS_FEED_URL)
    news_items = []
    
    for entry in feed.entries:

        content_html = entry.get("content", [{}])[0].get("value", "")
        content_text = BeautifulSoup(content_html, "html.parser").getText()

        dt_str = entry.get("published","")
        dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %z")

        news_items.append(
            {
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "media": entry.get("links", [{}])[1].get("href",""),
                "published_time": dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")),
                # "description": entry.get("title_detail", {}).get("value",""),
                "author": entry.get("authors", ""),
                "content": content_text
            }
        )
    
    return {"data": news_items}