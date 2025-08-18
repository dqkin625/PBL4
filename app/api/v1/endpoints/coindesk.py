from datetime import datetime
from zoneinfo import ZoneInfo
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
        
        dt_str = entry.get("published","")
        dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %z")

        news_items.append(
            {
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "media": entry.get("media_content", [{}])[0].get("url",""),
                "published_time": dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")),
                # "description": entry.get("title_detail", {}).get("value",""),
                "author": entry.get("authors", ""),
                "content": content_text
            }
        )
    
    return {"data": news_items}

    #Sửa lại coindesk và cryptonews chỉ lấy bài ngày hôm nay