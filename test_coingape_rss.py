#!/usr/bin/env python3
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import pytz
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def test_coingape_rss():
    url = "https://coingape.com/feed/"
    print(f"Testing RSS feed: {url}")
    
    try:
        # Sử dụng requests để lấy RSS content
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        print(f"Feed title: {feed.feed.get('title', 'N/A')}")
        print(f"Feed description: {feed.feed.get('description', 'N/A')}")
        print(f"Number of entries: {len(feed.entries)}")
        print("-" * 50)
        
        if len(feed.entries) > 0:
            entry = feed.entries[0]
            print("First entry details:")
            print(f"Title: {entry.get('title', 'N/A')}")
            print(f"Link: {entry.get('link', 'N/A')}")
            print(f"Published: {entry.get('published', 'N/A')}")
            print(f"Author: {entry.get('author', 'N/A')}")
            print(f"DC Creator: {entry.get('dc:creator', 'N/A')}")
            print(f"Description: {entry.get('description', 'N/A')[:100]}...")
            print(f"Content: {entry.get('content', 'N/A')}")
            print(f"Media content: {entry.get('media_content', 'N/A')}")
            print(f"Links: {entry.get('links', 'N/A')}")
            print(f"Enclosures: {entry.get('enclosures', 'N/A')}")
            
            # Test processing like the main function
            print("\n--- Processing test ---")
            
            # Content
            content = ""
            content_encoded = entry.get("content", [{}])
            if content_encoded and len(content_encoded) > 0:
                content_html = content_encoded[0].get("value", "")
                if content_html:
                    content = BeautifulSoup(content_html, "html.parser").get_text(strip=True)
            
            if not content:
                description = entry.get("description", "")
                if description:
                    content = BeautifulSoup(description, "html.parser").get_text(strip=True)
            
            if not content:
                content = entry.get("title", "")
                
            print(f"Processed content: {content[:200]}...")
            
            # Media
            media = ""
            media_content = entry.get("media_content", [])
            if media_content:
                media = media_content[0].get("url", "")
            
            if not media:
                links = entry.get("links", [])
                if len(links) > 1:
                    media = links[1].get("href", "")
            
            if not media:
                enclosures = entry.get("enclosures", [])
                if enclosures:
                    for enc in enclosures:
                        if enc.get("type", "").startswith("image"):
                            media = enc.get("href", "")
                            break
                            
            print(f"Processed media: {media}")
            
        else:
            print("No entries found in RSS feed")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_coingape_rss()
