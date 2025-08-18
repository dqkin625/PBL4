from fastapi import APIRouter, FastAPI
from app.services.theblock_service import get_article_links, scrape_article
from concurrent.futures import ThreadPoolExecutor, as_completed

THEBLOCK_URL = "https://www.theblock.co/category/policy"
router = APIRouter()

@router.get('/theblock_news')
def crawl_articles():
    try:
        # Lấy và khử trùng lặp link (giữ nguyên thứ tự xuất hiện)
        links_raw = get_article_links(THEBLOCK_URL)
        links = list(dict.fromkeys(links_raw))

        results_by_url = {}
        errors = []

        # Tối đa 5 luồng
        with ThreadPoolExecutor(max_workers=5, thread_name_prefix="scraper") as executor:
            future_to_url = {executor.submit(scrape_article, link): link for link in links}

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    article = future.result()  # future đã hoàn thành nên không cần timeout ở đây
                    results_by_url[url] = article
                except Exception as e:
                    # Không để văng cả job chỉ vì 1 link hỏng
                    errors.append({"url": url, "error": str(e)})

        # Giữ thứ tự kết quả theo thứ tự links ban đầu
        articles = [results_by_url[u] for u in links if u in results_by_url]

        return {
            "data": articles,
        }

    except Exception as e:
        return {"error": str(e)}
            