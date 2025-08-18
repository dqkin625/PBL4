from typing import Dict, Optional, List
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import feedparser

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0 Safari/537.36"
    )
}

UTODAY_RSS = "https://u.today/rss.php"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def get_article_links(url: str = UTODAY_RSS) -> List[str]:
    """
    Lấy link bài viết U.Today đăng trong ngày hôm nay (giờ VN).
    """
    feed = feedparser.parse(url)
    today_links: List[str] = []

    # Ngày hôm nay (UTC+7)
    now_vn = datetime.now(VN_TZ).date()

    for entry in feed.entries:
        pub_str = entry.get("published") or entry.get("pubDate")
        if not pub_str:
            continue

        try:
            # vd: Mon, 18 Aug 2025 07:31:09 +0000
            pub_dt = datetime.strptime(pub_str, "%a, %d %b %Y %H:%M:%S %z")
            pub_dt_vn = pub_dt.astimezone(VN_TZ)
            if pub_dt_vn.date() == now_vn:
                link = entry.get("link", "")
                if link:
                    today_links.append(link)
        except Exception as e:
            print("Lỗi parse pubDate:", e, pub_str)

    return today_links


def _parse_meta_datetime(soup: BeautifulSoup) -> Optional[datetime]:
    """
    U.Today thường để thời gian ở các meta:
      - <meta property="article:published_time" content="2025-08-18T07:31:09+00:00">
      - JSON-LD trong <script type="application/ld+json">
    Trả về datetime timezone-aware (UTC) nếu parse được.
    """
    # 1) Open Graph article:published_time
    og_pub = soup.find("meta", {"property": "article:published_time"}) or soup.find(
        "meta", {"name": "article:published_time"}
    )
    if og_pub and og_pub.get("content"):
        try:
            return datetime.fromisoformat(og_pub["content"].replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pass

    # 2) Thử JSON-LD
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            # Có thể là 1 object hoặc list
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if isinstance(obj, dict):
                    # Bài viết thường có "@type": "NewsArticle" | "Article"
                    if obj.get("@type") in ("NewsArticle", "Article", "ReportageNewsArticle", "BlogPosting"):
                        dt_str = obj.get("datePublished") or obj.get("dateCreated")
                        if dt_str:
                            return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue

    # 3) Fallback: <time datetime="...">
    t = soup.find("time", attrs={"datetime": True})
    if t and t.get("datetime"):
        dt_str = t["datetime"]
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pass

    # 4) Cuối cùng: parse chuỗi ngày dạng "Mon, 18/08/2025 - 7:31" nếu có trong trang (ít gặp trong meta)
    # Lấy toàn bộ text rồi regex tìm mẫu d/m/Y - H:M
    body_text = soup.get_text(" ", strip=True)
    m = re.search(r"\b(\w{3}),\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*(\d{1,2}):(\d{2})\b", body_text)
    if m:
        try:
            # Không có timezone -> giả định UTC (rồi convert về UTC-aware)
            dt = datetime(
                year=int(m.group(4)),
                month=int(m.group(3)),
                day=int(m.group(2)),
                hour=int(m.group(5)),
                minute=int(m.group(6)),
            ).replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

    return None


def scrape_article(url: str) -> Dict:
    """
    Scrape bài U.Today:
    - title
    - media (ảnh cover)
    - published_time (UTC+7)
    - author
    - content (p, li trong thân bài)
    """
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # --- title ---
    # U.Today đặt tiêu đề trong <h1>
    title: Optional[str] = None
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # --- published_time ---
    pub_dt_utc = _parse_meta_datetime(soup)

    # --- author ---
    author: Optional[str] = None
    meta_author = soup.find("meta", {"name": "author"})
    if meta_author and meta_author.get("content"):
        author = meta_author["content"].strip()

    if not author:
        # U.Today: div.author-brief__name a
        a_tag = soup.select_one("div.author-brief__name a")
        if a_tag:
            author = a_tag.get_text(strip=True)

    if not author:
        # fallback các vị trí phổ biến khác
        author_block = soup.select_one(".author, .post-author, .article__author, .post-meta__author")
        if author_block:
            a = author_block.find("a")
            author = (a.get_text(strip=True) if a else author_block.get_text(strip=True)) or None


    # --- description (không bắt buộc, nhưng hữu ích nếu bạn muốn lưu thêm) ---
    desc: Optional[str] = None
    meta_desc = soup.find("meta", {"property": "og:description"}) or soup.find("meta", {"name": "description"})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"].strip()

    # --- media (ảnh cover) ---
    media: Optional[str] = None
    og_img = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "og:image"})
    if og_img and og_img.get("content"):
        media = og_img["content"].strip()
    if not media:
        # Fallback: thẻ img đầu tiên gần tiêu đề hoặc trong header
        header_img = soup.select_one("header img, .post-header img, .article__header img")
        if header_img and header_img.get("src"):
            media = header_img["src"]

    # --- content ---
    # U.Today body thường nằm trong các container dưới; ta gom p/li lại:
    container = (
        soup.select_one(
            "div.article__text, div.article__body, div.post-content, article .content, article"
        )
        or soup.find("article")
        or soup.find("main")
        or soup.body
    )

    paragraphs: List[str] = []
    if container:
        # Lọc đoạn văn bản: p + li (nếu có bullet)
        for p in container.find_all(["p", "li"]):
            # Bỏ các đoạn có thể là quảng cáo/điều khoản
            txt = p.get_text(" ", strip=True)
            if not txt:
                continue
            if any(
                bad in txt.lower()
                for bad in [
                    "subscribe to daily newsletter",
                    "advertisement",
                    "ad ",
                    "disclaimer:",
                    "read u.today on google news",
                ]
            ):
                continue
            paragraphs.append(txt)

    content: Optional[str] = "\n\n".join(paragraphs) if paragraphs else None

    return {
        "url": url,
        "title": title,
        "media": media,
        "published_time": (
            pub_dt_utc.astimezone(VN_TZ) if isinstance(pub_dt_utc, datetime) else None
        ),
        "author": author,
        "description": desc,
        "content": content,
    }


if __name__ == "__main__":
    from pprint import pprint
    links = get_article_links(UTODAY_RSS)
    result = [scrape_article(link) for link in links]
    pprint(result)
