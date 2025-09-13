from asyncio import as_completed
from fastapi import APIRouter, Query, HTTPException, Depends
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.crypto_news_service import scrape_rss_feed_articles
# from app.services.crypto_news_service import get_theblock_article_links, scrape_theblock_article
from app.services.db_service import save_news_by_source, get_news_from_db, save_bulletin_to_db, get_bulletins_from_db, get_bulletin_stats, get_bulletins_paginated
from app.services.gemini_service import create_news_bulletin
from app.utils.response import response_data, StatusMessage
from app.utils.auth import require_admin, create_admin_token
from datetime import datetime, timedelta, timezone


router = APIRouter()

COINDESK_RSS_FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss"
COINGAPE_RSS_FEED_URL = "https://coingape.com/feed/"
COINTELEGRAPH_URL = "https://cointelegraph.com/rss"
CRYPTONEWS_RSS_FEED_URL = "https://cryptonews.com/news/feed/"
THEBLOCK_URL = "https://www.theblock.co/category/policy"
UTODAY_URL = "https://u.today/rss.php"

# Cấu hình các nguồn RSS
RSS_SOURCES = {
    "coindesk": COINDESK_RSS_FEED_URL,
    # "coingape": COINGAPE_RSS_FEED_URL,
    # "cointelegraph": COINTELEGRAPH_URL,
    "cryptonews": CRYPTONEWS_RSS_FEED_URL,
    # "utoday": UTODAY_URL
}

def scrape_rss_source(source_name: str, url: str):
    """
    Hàm chung để scrape một nguồn RSS
    """
    try:
        data = scrape_rss_feed_articles(url)
        db_result = save_news_by_source(source_name, data)
        return {
            "source": source_name,
            "count": len(data),
            "data": data,
            "db_stats": db_result,
            "status": "success"
        }
    except Exception as e:
        return {
            "source": source_name,
            "status": "error",
            "error": str(e)
        }

# def scrape_theblock():
#     try:
#         links_raw = get_theblock_article_links(THEBLOCK_URL)
#         links = list(dict.fromkeys(links_raw))
        
#         results_by_url = {}
#         errors = []
        
#         with ThreadPoolExecutor(max_workers=5, thread_name_prefix="scraper") as executor:
#             future_to_url = {executor.submit(scrape_theblock_article, link): link for link in links}
            
#             for future in as_completed(future_to_url):
#                 url = future_to_url[future]
#                 try:
#                     article = future.result()
#                     results_by_url[url] = article
#                 except Exception as e:
#                     errors.append({"url": url, "error": str(e)})
        
#         articles = [results_by_url[u] for u in links if u in results_by_url]
#         db_result = save_news_by_source("theblock", articles)
        
#         return {
#             "source": "theblock",
#             "count": len(articles),
#             "data": articles,
#             "db_stats": db_result,
#             "status": "success"
#         }
#     except Exception as e:
#         return {
#             "source": "theblock",
#             "status": "error",
#             "error": str(e)
#         }

@router.get("/get_all_news")
def get_all_news():
    try:
        start_time = datetime.now()
        
        results = []
        total_articles = 0
        successful_sources = 0
        failed_sources = 0
        
        with ThreadPoolExecutor(max_workers=6, thread_name_prefix="news_scraper") as executor:
            # Tạo future cho mỗi nguồn RSS
            future_to_source = {
                executor.submit(scrape_rss_source, source_name, url): source_name 
                for source_name, url in RSS_SOURCES.items()
            }
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.get("status") == "success":
                        successful_sources += 1
                        total_articles += result.get("count", 0)
                    else:
                        failed_sources += 1
                        
                except Exception as e:
                    failed_sources += 1
                    results.append({
                        "source": source_name,
                        "status": "error",
                        "error": str(e)
                    })
        
        end_time = datetime.now()
        execution_time = round((end_time - start_time).total_seconds(), 2)
        
        total_db_stats = {
            "total_matched": 0,
            "total_upserted": 0, 
            "total_modified": 0,
            "total_processed": 0,
            "total_skipped": 0,
            "sources_with_errors": []
        }
        
        for result in results:
            if result.get("status") == "success" and "db_stats" in result:
                db_stats = result["db_stats"]
                total_db_stats["total_matched"] += db_stats.get("matched", 0)
                total_db_stats["total_upserted"] += db_stats.get("upserted", 0)
                total_db_stats["total_modified"] += db_stats.get("modified", 0)
                total_db_stats["total_processed"] += db_stats.get("processed_items", 0)
                total_db_stats["total_skipped"] += len(db_stats.get("skipped_items", []))
                
                if (db_stats.get("bulk_write_errors") or 
                    db_stats.get("individual_errors") or 
                    db_stats.get("skipped_items")):
                    total_db_stats["sources_with_errors"].append({
                        "source": result["source"],
                        "skipped_items": len(db_stats.get("skipped_items", [])),
                        "bulk_errors": len(db_stats.get("bulk_write_errors", [])),
                        "individual_errors": len(db_stats.get("individual_errors", []))
                    })
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "message": f"Successfully scraped all {len(RSS_SOURCES)} crypto news sources",
                "execution_time_seconds": execution_time,
                "summary": {
                    "total_sources": len(RSS_SOURCES),
                    "successful_sources": successful_sources,
                    "failed_sources": failed_sources,
                    "total_articles": total_articles
                },
                "database_summary": total_db_stats,
                "results": results
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi scrape tin tức: {str(e)}"
        )


@router.get("/get_news_for_bulletin")
def get_news_for_bulletin(
    hours: int = Query(default=24, description="Lấy tin tức trong X giờ qua"),
    sources: str = Query(default=None, description="Các nguồn tin cách nhau bởi dấu phẩy (coindesk,coingape,...)"), 
    limit: int = Query(default=50, description="Giới hạn số bài viết tối đa")
):
    try:
        # Validate parameters
        if hours <= 0:
            raise HTTPException(status_code=400, detail="Hours phải là số dương")
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Limit phải là số dương")
        
        source_list = None
        if sources:
            source_list = [s.strip() for s in sources.split(",") if s.strip()]
        
        from_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        news_data = get_news_from_db(
            from_time=from_time,
            sources=source_list,
            limit=limit
        )
        
        if not news_data:
            return response_data(
                status_code=404,
                message=StatusMessage.NOT_FOUND,
                data={
                    "message": "Không tìm thấy tin tức nào trong khoảng thời gian đã chọn",
                    "total_articles": 0,
                    "articles": [],
                    "filter_info": {
                        "hours": hours,
                        "sources": source_list,
                        "limit": limit,
                        "from_time": from_time.isoformat()
                    }
                }
            )
        
        articles_for_gemini = []
        for article in news_data:
            if article.get("content") and article.get("title"):
                article_summary = {
                    "title": article["title"],
                    "content": article["content"],
                    "source": article.get("source", "unknown"),
                    "url": article.get("url", ""),
                    "published_time": article.get("published_time", ""),
                    "author": article.get("author", "")
                }
                articles_for_gemini.append(article_summary)
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "message": f"Lấy thành công {len(articles_for_gemini)} bài viết có nội dung đầy đủ",
                "total_articles": len(articles_for_gemini),
                "articles": articles_for_gemini,
                "filter_info": {
                    "hours": hours,
                    "sources": source_list,
                    "limit": limit,
                    "from_time": from_time.isoformat()
                },
                "statistics": {
                    "sources_found": list(set([article.get("source") for article in articles_for_gemini])),
                    "articles_with_content": len(articles_for_gemini),
                    "total_found_in_db": len(news_data)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy tin tức cho bulletin: {str(e)}"
        )


@router.post("/create_bulletin")
def create_bulletin(
    hours: int = Query(default=8, description="Lấy tin tức trong X giờ qua"),
    sources: str = Query(default=None, description="Các nguồn tin cách nhau bởi dấu phẩy"), 
    limit: int = Query(default=20, description="Giới hạn số bài viết tối đa để tổng hợp")
):
    try:
        # Validate parameters
        if hours <= 0:
            raise HTTPException(status_code=400, detail="Hours phải là số dương")
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Limit phải là số dương")
        
        source_list = None
        if sources:
            source_list = [s.strip() for s in sources.split(",") if s.strip()]
        
        from_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        news_data = get_news_from_db(
            from_time=from_time,
            sources=source_list,
            limit=limit
        )
        
        if not news_data:
            return response_data(
                status_code=404,
                message=StatusMessage.NOT_FOUND,
                data={
                    "success": False,
                    "message": "Không tìm thấy tin tức nào để tổng hợp",
                    "bulletin": None,
                    "filter_info": {
                        "hours": hours,
                        "sources": source_list,
                        "limit": limit
                    }
                }
            )
        
        articles_with_content = []
        for article in news_data:
            if article.get("content") and article.get("title"):
                articles_with_content.append(article)
        
        if not articles_with_content:
            return response_data(
                status_code=400,
                message=StatusMessage.BAD_REQUEST,
                data={
                    "success": False,
                    "message": "Không có bài viết nào có nội dung đầy đủ để tổng hợp",
                    "bulletin": None,
                    "total_found": len(news_data),
                    "with_content": 0
                }
            )
        
        bulletin_result = create_news_bulletin(articles_with_content)
        
        if bulletin_result["success"]:
            metadata = {
                "articles_processed": len(articles_with_content),
                "total_found_in_db": len(news_data),
                "sources_used": bulletin_result.get("sources_used", []),
                "generated_at": bulletin_result.get("generated_at"),
                "filter_info": {
                    "hours": hours,
                    "sources": source_list,
                    "limit": limit,
                    "from_time": from_time.isoformat()
                }
            }
            
            db_save_result = save_bulletin_to_db(bulletin_result, metadata, articles_with_content)
            
            return response_data(
                status_code=200,
                message=StatusMessage.SUCCESS,
                data={
                    "success": True,
                    "message": f"Tạo bản tin thành công từ {len(articles_with_content)} bài viết",
                    "bulletin": bulletin_result["bulletin"],
                    "metadata": metadata,
                    "database": {
                        "saved": db_save_result["success"],
                        "bulletin_id": db_save_result.get("bulletin_id"),
                        "inserted_id": db_save_result.get("inserted_id"),
                        "error": db_save_result.get("error") if not db_save_result["success"] else None
                    },
                    "image_url": db_save_result.get("image_url"),
                    "references": db_save_result.get("references", [])
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi khi tạo bản tin với Gemini: {bulletin_result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi hệ thống khi tạo bulletin: {str(e)}"
        )


@router.get("/get_bulletins")
def get_bulletins(
    hours: int = Query(default=24, description="Lấy bulletin trong X giờ qua"),
    limit: int = Query(default=20, description="Giới hạn số lượng bulletin")
):
    """Lấy danh sách bulletin đã tạo"""
    try:
        if hours <= 0:
            raise HTTPException(status_code=400, detail="Hours phải là số dương")
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit phải từ 1-100")
        
        from_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        bulletins = get_bulletins_from_db(
            from_time=from_time,
            limit=limit
        )
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "message": f"Lấy thành công {len(bulletins)} bulletin",
                "total_bulletins": len(bulletins),
                "bulletins": bulletins,
                "filter_info": {
                    "hours": hours,
                    "limit": limit,
                    "from_time": from_time.isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy bulletin: {str(e)}"
        )


@router.get("/bulletin_stats")
def bulletin_stats():
    """Lấy thống kê về bulletin"""
    try:
        stats = get_bulletin_stats()
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "message": "Thống kê bulletin thành công",
                "statistics": stats
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy thống kê bulletin: {str(e)}"
        )


@router.post("/admin/login")
def admin_login(
    username: str = Query(..., description="Admin username"),
    password: str = Query(..., description="Admin password")
):
    """
    Login endpoint to get JWT token for admin access
    
    Default credentials (can be changed in environment):
    - username: admin
    - password: admin123
    
    Returns:
        JWT token for authentication
    """
    import os
    
    # Get credentials from environment or use defaults
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Verify credentials
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Generate JWT token
    token = create_admin_token(username)
    
    return response_data(
        status_code=200,
        message=StatusMessage.SUCCESS,
        data={
            "access_token": token,
            "token_type": "bearer",
            "message": "Login successful. Use this token in Authorization header as: Bearer <token>"
        }
    )



# --- Thêm 2 endpoint mới ---

@router.get("/get_news_db")
def get_news_db():
    """
    Lấy toàn bộ bài viết có trong database (giới hạn 1000 bài viết).
    """
    try:
        news = get_news_from_db(limit=1000)
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data=news
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy bài viết từ database: {str(e)}")

@router.get("/get_bulletin_db")
def get_bulletin_db():
    """
    Lấy bulletin mới nhất có trong database.
    """
    try:
        bulletins = get_bulletins_from_db(limit=1, sort_order=-1)
        latest_bulletin = bulletins[0] if bulletins else None
        if not latest_bulletin:
            return response_data(
                status_code=404,
                message=StatusMessage.NOT_FOUND,
                data=None
            )
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data=latest_bulletin
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy bulletin mới nhất: {str(e)}")
