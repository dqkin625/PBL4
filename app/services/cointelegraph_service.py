import re
from typing import Dict, Optional
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LISTING_URL = "https://cointelegraph.com/category/latest-news"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0 Safari/537.36"
    )
}

HOURS_OR_MINUTES_RE = re.compile(r'\b(\d+)\s+(HOUR|HOURS|MINUTE|MINUTES)\s+AGO\b', re.I)
DATE_STAMP_RE = re.compile(r'^[A-Z]{3}\s+\d{1,2},\s+\d{4}$')  # e.g. AUG 16, 2025

def get_article_links(url: str):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=opts)

    try:
        driver.get(url)
        # Đợi danh sách render xong (có ảnh + tiêu đề)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    results = []
    seen = set()

    main = soup.find("main") or soup

    # Tìm mọi block có text thời gian
    for time_block in main.find_all(string=True):
        text = time_block.strip().upper()
        if not text:
            continue

        # Nếu chạm tới mốc là ngày tháng -> dừng (đã sang các bài cũ hơn)
        if DATE_STAMP_RE.match(text):
            break

        # Chỉ quan tâm block có "HOURS AGO / MINUTES AGO"
        if not HOURS_OR_MINUTES_RE.search(text):
            continue

        # Từ block thời gian, tìm phần tử bao ngoài (card)
        card = None
        node = getattr(time_block, "parent", None)
        # leo lên vài cấp để tìm card chứa link bài
        for _ in range(6):
            if node is None:
                break
            # trong card phải có link /news/
            a = node.find("a", href=True)
            if a and a["href"].startswith("/news/"):
                card = node
                break
            node = node.parent

        if not card:
            continue

        # Lấy link tiêu đề trong card
        a = card.find("a", href=True)
        if not a or not a["href"].startswith("/news/"):
            continue

        full = urljoin(url, a["href"])
        if full not in seen:
            seen.add(full)
            results.append(full)

    return results

def scrape_article(url: str) -> Dict:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # --- title ---
    title: Optional[str] = None
    h1 = soup.find("h1", class_="post__title") or soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # --- published_time từ <time datetime="..."> ---
    pub_dt = None
    t = soup.find("time", attrs={"datetime": True})
    if t and t.get("datetime"):
        dt_str = t["datetime"]
        try:
            pub_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pub_dt = dt_str

    # --- author ---
    author: Optional[str] = None
    author_block = soup.find("div", class_="post-meta__author") or soup.find("span", class_="post-meta__author-name")
    if author_block:
        a = author_block.find("a")
        author = (a.get_text(strip=True) if a else author_block.get_text(strip=True)) or None

    # --- description ---
    desc: Optional[str] = None
    meta_desc = soup.find("meta", {"property": "og:description"})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"]

    # --- media (ảnh đầu tiên trong <picture>) ---
    media: Optional[str] = None
    picture = soup.find("picture")
    if picture:
        # Ưu tiên lấy <img src>
        img = picture.find("img")
        if img and img.get("src"):
            media = img["src"]
        else:
            # fallback: lấy source đầu tiên
            source = picture.find("source")
            if source and source.get("srcset"):
                media = source["srcset"].split()[0]  # lấy url đầu tiên

    # --- content ---
    content: Optional[str] = None
    article_container = soup.select_one(
        "div.post-content, div.post__content, div.post_content, "
        "div.post-content-wrapper, div.post_content-wrapper"
    )
    paragraphs = []
    if article_container:
        p_tags = article_container.find_all("p")
    else:
        main = soup.find("main") or soup
        p_tags = main.find_all("p")

    for p in p_tags:
        txt = p.get_text(" ", strip=True)
        if txt:
            paragraphs.append(txt)

    if paragraphs:
        content = "\n\n".join(paragraphs)

    return {
        "url": url,
        "title": title,
        "media": media,
        "published_time": pub_dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")) if isinstance(pub_dt, datetime) else pub_dt,
        "author": author,
        "content": content,
    }


# if __name__ == "__main__":
#     from pprint import pprint
#     links = get_latest_news_until_date(LISTING_URL)
#     result = [scrape_article(link) for link in links]
#     pprint (result)
