import feedparser
from bs4 import BeautifulSoup
from fastapi import APIRouter

router = APIRouter()

COINDESK_RSS_FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss"

@router.get("/coindesk_news")
def get_news():
    feed = feedparser.parse(COINDESK_RSS_FEED_URL)
    news_items = []
    
    for entry in feed.entries:

        # from pprint import pprint
        # print("\n==== ENTRY ====")
        # pprint(entry)

        content_html = entry.get("content", [{}])[0].get("value", "")
        content_text = BeautifulSoup(content_html, "html.parser").getText()
        
        news_items.append(
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "media": entry.get("media_content", [{}])[0].get("url",""),
                "published": entry.get("published",""),
                # "description": entry.get("title_detail", {}).get("value",""),
                "author": entry.get("authors", ""),
                "content": content_text
            }
        )
    
    return {"coindesk_new": news_items}