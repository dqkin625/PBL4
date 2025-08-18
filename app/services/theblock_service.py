from typing import Optional
from fastapi import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0 Safari/537.36"
    )
}

def get_article_links(url: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "articleCard"))
        )
    except:
        driver.quit()
        return []

    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'lxml')

    tz_hcm = pytz.timezone('Asia/Ho_Chi_Minh')
    today_hcm = datetime.now(tz_hcm).date()

    links = []

    for article in soup.find_all('article', class_='articleCard'):
        meta = article.find('div', class_='meta__wrapper')
        if not meta:
            continue

        time_text = meta.get_text(strip=True)
        try:
            cleaned_time_text = time_text.split('•')[0].strip()
            dt_naive = datetime.strptime(cleaned_time_text, '%B %d, %Y, %I:%M%p EDT')
            dt_edt = pytz.timezone('US/Eastern').localize(dt_naive)
            dt_hcm = dt_edt.astimezone(tz_hcm)
            if dt_hcm.date() != today_hcm:
                continue
            a_tag = article.find('a', href=True)
            if a_tag:
                links.append("https://www.theblock.co" + a_tag['href'])
        except:
            continue

    return links

def scrape_article(url: str) -> dict:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
    except:
        driver.quit()
        return {
            "url": url,
            "title": None
        }

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    #title
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else None

    #author
    a = soup.find("a", href=lambda x: x and "/author/" in x)
    author = a.get_text(strip=True) if a else None
    
    #media
    img = soup.find("img")
    media = img["src"] if img else None

    #published time
    date_iso = None
    div = soup.find("div", class_="categoryLink")
    if div and "•" in div.text:
        date_str = div.text.split("•")[-1].strip()
        # Bỏ "EDT" đi, tự gắn US/Eastern
        date_str = date_str.replace("EDT", "").strip()
        dt_naive = datetime.strptime(date_str, "%B %d, %Y, %I:%M%p")

        eastern = pytz.timezone("US/Eastern")
        dt_est = eastern.localize(dt_naive)

        hcm = pytz.timezone("Asia/Ho_Chi_Minh")
        dt_hcm = dt_est.astimezone(hcm)

        date_iso = dt_hcm.isoformat(timespec="seconds")

    #content
    quick_take = soup.find("div", class_="quickTake")
    content = ""

    if quick_take:
        # Lấy text trong span
        spans = quick_take.find_all("span")
        texts = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]

        # Nếu không có span, fallback lấy text trong li
        if not texts:
            lis = quick_take.find_all("li")
            texts = [li.get_text(strip=True) for li in lis if li.get_text(strip=True)]

        content = "\n".join(texts)

    return {
        "url": url,
        "title": title,
        "media": media,
        "published_time": date_iso,
        "author": author,
        "content": content
    }


# if __name__ == "__main__":
#     from pprint import pprint
#     links = get_today_links()
#     for link in links:
#         print(link)
#         article = scrape_article(link)
#         pprint(article)
        
