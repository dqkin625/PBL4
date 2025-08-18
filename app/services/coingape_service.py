from typing import Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pytz

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0 Safari/537.36"
    )
}

def get_news_links(url: str) -> list[str]:
    """
    Lấy toàn bộ link bài trong:
      - cột trái:  div.col-md-7.col-50.mb-4
      - danh sách phải: .NewsPre .Newslists
    Trả về list URL tuyệt đối, bỏ trùng và lọc link phụ (author/category/tag).
    """
    # --- Selenium (headless) ---
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(url)
        # Chờ khi các <a> ở 2 khu vực xuất hiện
        selector = "div.col-md-7.col-50.mb-4 a[href], .NewsPre .Newslists a[href]"
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
        )
        html = driver.page_source
    finally:
        driver.quit()

    # --- Parse & lấy link ---
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("div.col-md-7.col-50.mb-4 a[href], .NewsPre .Newslists a[href]")

    banlist = ("/author/", "/category/", "/tag/", "/companies.")
    links = [
        urljoin(url, a["href"])
        for a in anchors
        if a.get("href") and not any(x in a["href"] for x in banlist)
    ]

    # Bỏ trùng nhưng giữ thứ tự
    return list(dict.fromkeys(links))

def scrape_article(url: str) -> Dict:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    #title
    title: Optional[str] = None
    h1 = soup.find("h1", class_="c-title entry-title tittle")
    title = h1.get_text(strip=True) if h1 else None
    
    #media
    img_div = soup.find("div", class_="imgthum")
    img_tag = img_div.find("img") if img_div else None
    media = img_tag["src"] if img_tag else None

    #published_time
    time_tag = soup.find("time", class_="arcg-timeago")
    time = time_tag["datetime"]
    time_utc = datetime.fromisoformat(time)
    time_utc = time_utc.astimezone(pytz.UTC)
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    dt_vn = time_utc.astimezone(vn_tz)
    published_time = dt_vn.isoformat()

    #author
    author_tag = soup.find("span", class_="auth-name")
    a_tag = author_tag.find("a")
    author = a_tag.get_text(strip=True)

    #content
    content_tag = soup.find("div", class_="keyfeatures")
    hightlights = content_tag.find_all("li")
    content = ""
    for hightlight in hightlights:
        content += hightlight.get_text(strip=True)

    return {
        "url": url,
        "title": title,
        "media": media,
        "published_time": published_time,
        "author": author,
        "content": content
    } 


# if __name__ == "__main__":
#     from pprint import pprint
#     links = get_news_links("https://coingape.com/category/news/")
#     pprint (links)

#     for link in links:
#         pprint(scrape_article(link))
