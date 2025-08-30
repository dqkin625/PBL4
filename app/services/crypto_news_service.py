from datetime import datetime
from time import timezone
from zoneinfo import ZoneInfo
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import pytz

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def scrape_rss_feed_articles(url: str) -> List[dict]:
    """
    Hàm chung để xử lý tất cả các RSS feed
    Hỗ trợ: CoinDesk, CryptoNews, CoinTelegraph, U.Today, CoinGape
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"Requests failed for {url}, using feedparser: {e}")
        import urllib.request
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', HEADERS['User-Agent'])]
        urllib.request.install_opener(opener)
        feed = feedparser.parse(url)
    
    news_items = []
    
    for entry in feed.entries:
        # --- URL ---
        article_url = entry.get("link", "")
        
        # --- Title ---
        title = entry.get("title", "")
        
        # --- Content (ưu tiên content:encoded > description > title) ---
        content = ""
        
        # Thử lấy content:encoded trước
        content_encoded = entry.get("content", [{}])
        if content_encoded and len(content_encoded) > 0:
            content_html = content_encoded[0].get("value", "")
            if content_html:
                content = BeautifulSoup(content_html, "html.parser").get_text(strip=True)
        
        # Nếu không có content:encoded, lấy description
        if not content:
            description = entry.get("description", "") or entry.get("summary", "")
            if description:
                content = BeautifulSoup(description, "html.parser").get_text(strip=True)
        
        # Nếu không có description, lấy title
        if not content:
            content = title
        
        # --- Published Time ---
        published_time = None
        dt_str = entry.get("published", "") or entry.get("pubDate", "")
        if dt_str:
            try:
                dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %z")
                dt_vn = dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
                published_time = dt_vn.isoformat()
            except ValueError:
                # Thử format khác nếu cần
                try:
                    dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %Z")
                    dt = dt.replace(tzinfo=pytz.UTC)
                    dt_vn = dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
                    published_time = dt_vn.isoformat()
                except ValueError:
                    published_time = dt_str
        
        # --- Author ---
        author = ""
        
        # Thử lấy từ authors array
        authors_arr = entry.get("authors", [])
        if authors_arr:
            if isinstance(authors_arr, list):
                author = ", ".join([auth.get("name", "") for auth in authors_arr if auth.get("name")])
            else:
                author = str(authors_arr)
        
        # Nếu không có authors, thử dc:creator
        if not author:
            creator = entry.get("dc:creator", "") or entry.get("author", "")
            if creator:
                # Xử lý trường hợp "Cointelegraph by Amin Haqshanas"
                if "by " in creator:
                    author = creator.split("by ")[-1].strip()
                else:
                    author = creator
        
        # --- Media ---
        media = ""
        
        # Thử lấy từ media:content
        media_content = entry.get("media_content", [])
        if media_content:
            media = media_content[0].get("url", "")
        
        # Nếu không có media_content, thử từ links
        if not media:
            links = entry.get("links", [])
            if len(links) > 1:
                media = links[1].get("href", "")
        
        # Nếu không có links, thử từ enclosure
        if not media:
            enclosures = entry.get("enclosures", [])
            if enclosures:
                for enc in enclosures:
                    if enc.get("type", "").startswith("image"):
                        media = enc.get("href", "")
                        break
        
        # Tạo dict kết quả
        news_item = {
            "url": article_url,
            "title": title,
            "media": media,
            "published_time": published_time,
            "author": author,
            "content": content
        }
        
        news_items.append(news_item)
    
    return news_items

# def get_theblock_article_links(url: str):
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
#     driver = webdriver.Chrome(options=options)

#     driver.get(url)

#     try:
#         WebDriverWait(driver, 15).until(
#             EC.presence_of_element_located((By.CLASS_NAME, "articleCard"))
#         )
#     except:
#         driver.quit()
#         return []

#     html = driver.page_source
#     driver.quit()
#     soup = BeautifulSoup(html, 'lxml')

#     tz_hcm = pytz.timezone('Asia/Ho_Chi_Minh')
#     today_hcm = datetime.now(tz_hcm).date()

#     links = []

#     for article in soup.find_all('article', class_='articleCard'):
#         meta = article.find('div', class_='meta__wrapper')
#         if not meta:
#             continue

#         time_text = meta.get_text(strip=True)
#         try:
#             cleaned_time_text = time_text.split('•')[0].strip()
#             dt_naive = datetime.strptime(cleaned_time_text, '%B %d, %Y, %I:%M%p EDT')
#             dt_edt = pytz.timezone('US/Eastern').localize(dt_naive)
#             dt_hcm = dt_edt.astimezone(tz_hcm)
#             if dt_hcm.date() != today_hcm:
#                 continue
#             a_tag = article.find('a', href=True)
#             if a_tag:
#                 links.append("https://www.theblock.co" + a_tag['href'])
#         except:
#             continue

#     return links

# def scrape_theblock_article(url: str) -> dict:
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
#     driver = webdriver.Chrome(options=options)

#     driver.get(url)

#     try:
#         WebDriverWait(driver, 15).until(
#             EC.presence_of_element_located((By.TAG_NAME, "h1"))
#         )
#     except:
#         driver.quit()
#         return {
#             "url": url,
#             "title": None
#         }

#     html = driver.page_source
#     driver.quit()

#     soup = BeautifulSoup(html, "html.parser")

#     #title
#     h1 = soup.find("h1")
#     title = h1.get_text(strip=True) if h1 else None

#     #author
#     a = soup.find("a", href=lambda x: x and "/author/" in x)
#     author = a.get_text(strip=True) if a else None
    
#     #media
#     img = soup.find("img")
#     media = img["src"] if img else None

#     #published time
#     date_iso = None
#     div = soup.find("div", class_="categoryLink")
#     if div and "•" in div.text:
#         date_str = div.text.split("•")[-1].strip()
#         date_str = date_str.replace("EDT", "").strip()
#         dt_naive = datetime.strptime(date_str, "%B %d, %Y, %I:%M%p")

#         eastern = pytz.timezone("US/Eastern")
#         dt_est = eastern.localize(dt_naive)

#         hcm = pytz.timezone("Asia/Ho_Chi_Minh")
#         dt_hcm = dt_est.astimezone(hcm)

#         date_iso = dt_hcm.isoformat(timespec="seconds")

#     #content
#     quick_take = soup.find("div", class_="quickTake")
#     content = ""

#     if quick_take:
#         # Lấy text trong span
#         spans = quick_take.find_all("span")
#         texts = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]

#         # Nếu không có span, fallback lấy text trong li
#         if not texts:
#             lis = quick_take.find_all("li")
#             texts = [li.get_text(strip=True) for li in lis if li.get_text(strip=True)]

#         content = "\n".join(texts)

#     return {
#         "url": url,
#         "title": title,
#         "media": media,
#         "published_time": date_iso,
#         "author": author,
#         "content": content
#     }

