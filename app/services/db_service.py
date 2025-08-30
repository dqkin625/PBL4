from datetime import timezone, datetime, timedelta
from typing import List, Dict, Optional
import random
from pymongo import UpdateOne
from app.db.client import get_news_collection, get_bulletin_collection

def _normalize_doc(doc: Dict, source: str = None) -> Dict:
        
    normalized = {}
    
    # URL (bắt buộc) - clean URL
    if "url" in doc and doc["url"]:
        url = str(doc["url"]).strip()
        if url:
            normalized["url"] = url
    
    # Title - clean title
    if "title" in doc and doc["title"]:
        title = str(doc["title"]).strip()
        if title:
            normalized["title"] = title
        
    # Media - có thể null
    if "media" in doc:
        media = doc["media"]
        if media and str(media).strip():
            normalized["media"] = str(media).strip()
        else:
            normalized["media"] = None
    
    # Published time - chuyển về datetime object để lưu vào MongoDB
    if "published_time" in doc and doc["published_time"] is not None:
        try:
            if isinstance(doc["published_time"], datetime):
                # Nếu là datetime object, giữ nguyên múi giờ, chỉ bỏ tzinfo để lưu vào MongoDB
                normalized["published_time"] = doc["published_time"].replace(tzinfo=None)
            elif isinstance(doc["published_time"], str):
                # Nếu là string, thử parse thành datetime
                pub_time_str = doc["published_time"].strip()
                if pub_time_str:
                    try:
                        # Parse ISO string với timezone thành datetime
                        if "T" in pub_time_str and ("+" in pub_time_str or pub_time_str.endswith("Z")):
                            # ISO format với timezone: "2025-08-21T10:30:00+07:00"
                            dt_parsed = datetime.fromisoformat(pub_time_str.replace("Z", "+00:00"))
                            # Giữ nguyên thời gian (không convert timezone), chỉ bỏ tzinfo
                            normalized["published_time"] = dt_parsed.replace(tzinfo=None)
                        else:
                            normalized["published_time"] = None
                    except Exception as e:
                        print(f"Error parsing published_time '{pub_time_str}': {e}")
                        normalized["published_time"] = None
                else:
                    normalized["published_time"] = None
            else:
                normalized["published_time"] = None
        except Exception:
            normalized["published_time"] = None
    else:
        normalized["published_time"] = None
    
    # Author - có thể null
    if "author" in doc:
        author = doc["author"]
        if author and str(author).strip():
            normalized["author"] = str(author).strip()
        else:
            normalized["author"] = None
        
    # Content - có thể null nhưng nên có
    if "content" in doc:
        content = doc["content"]
        if content and str(content).strip():
            normalized["content"] = str(content).strip()
        else:
            normalized["content"] = None
    
    # Source (thêm nếu chưa có)
    if source:
        normalized["source"] = source
    elif "source" in doc and doc["source"]:
        normalized["source"] = str(doc["source"]).strip()
    else:
        normalized["source"] = "unknown"
    
    return normalized

def save_news_by_source(source: str, items: List[Dict]) -> dict:
    collection = get_news_collection()
    
    ops = []
    skipped_items = []
    
    for i, item in enumerate(items):
        try:
            doc = _normalize_doc(item, source)
            url = doc.get("url")
            
            # Kiểm tra URL bắt buộc
            if not url or not url.strip():
                skipped_items.append(f"Item {i}: Missing URL")
                continue
                
            # Kiểm tra các field quan trọng khác
            if not doc.get("title"):
                skipped_items.append(f"Item {i}: Missing title")
                continue
                
            ops.append(
                UpdateOne(
                    {"url": url.strip()},
                    {"$set": doc},
                    upsert=True
                )
            )
        except Exception as e:
            skipped_items.append(f"Item {i}: Error processing - {str(e)}")
            continue

    if not ops:
        return {
            "matched": 0, 
            "upserted": 0, 
            "modified": 0, 
            "source": source,
            "total_items": len(items),
            "processed_items": 0,
            "skipped_items": skipped_items
        }

    try:
        res = collection.bulk_write(ops, ordered=False)
        return {
            "matched": res.matched_count,
            "upserted": len(res.upserted_ids),
            "modified": res.modified_count,
            "source": source,
            "total_items": len(items),
            "processed_items": len(ops),
            "skipped_items": skipped_items,
            "bulk_write_errors": []
        }
    except Exception as e:
        # Nếu có lỗi bulk_write, thử lưu từng item một
        print(f"Bulk write error for {source}: {str(e)}")
        
        individual_results = {"matched": 0, "upserted": 0, "modified": 0}
        individual_errors = []
        
        for op in ops:
            try:
                result = collection.replace_one(
                    op._filter,
                    op._doc["$set"],
                    upsert=True
                )
                if result.upserted_id:
                    individual_results["upserted"] += 1
                elif result.modified_count > 0:
                    individual_results["modified"] += 1
                else:
                    individual_results["matched"] += 1
            except Exception as individual_error:
                individual_errors.append(str(individual_error))
        
        return {
            **individual_results,
            "source": source,
            "total_items": len(items),
            "processed_items": len(ops),
            "skipped_items": skipped_items,
            "bulk_write_errors": [str(e)],
            "individual_errors": individual_errors
        }

def save_coindesk_news(items: List[Dict]) -> dict:
    return save_news_by_source("coindesk", items)


def get_news_from_db(
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    sources: Optional[List[str]] = None,
    limit: int = 100
) -> List[Dict]:
    
    collection = get_news_collection()
    
    # Xây dựng query filter
    query_filter = {}
    
    # Filter theo thời gian - chuyển from_time và to_time sang UTC+7 để so sánh
    if from_time or to_time:
        from zoneinfo import ZoneInfo
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        utc_tz = ZoneInfo("UTC")
        
        time_filter = {}
        if from_time:
            # Nếu from_time không có timezone, giả định là UTC
            if from_time.tzinfo is None:
                from_time_utc = from_time.replace(tzinfo=utc_tz)
            else:
                from_time_utc = from_time.astimezone(utc_tz)
            # Convert từ UTC sang UTC+7 (cộng 7 tiếng)
            from_time_vn = from_time_utc.astimezone(vn_tz).replace(tzinfo=None)
            time_filter["$gte"] = from_time_vn
            
        if to_time:
            # Nếu to_time không có timezone, giả định là UTC
            if to_time.tzinfo is None:
                to_time_utc = to_time.replace(tzinfo=utc_tz)
            else:
                to_time_utc = to_time.astimezone(utc_tz)
            # Convert từ UTC sang UTC+7 (cộng 7 tiếng)
            to_time_vn = to_time_utc.astimezone(vn_tz).replace(tzinfo=None)
            time_filter["$lte"] = to_time_vn
            
        query_filter["published_time"] = time_filter
    
    # Filter theo nguồn tin
    if sources and len(sources) > 0:
        query_filter["source"] = {"$in": sources}
    
    try:
        # Query database với sort theo thời gian mới nhất
        cursor = collection.find(query_filter).sort("published_time", -1).limit(limit)
        
        # Convert cursor to list và xử lý ObjectId
        results = []
        for doc in cursor:
            # Convert ObjectId to string
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            # Chuyển datetime thành string nếu cần (để trả về JSON)
            if "published_time" in doc and isinstance(doc["published_time"], datetime):
                doc["published_time"] = doc["published_time"].isoformat()
                
            results.append(doc)
        
        return results
        
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []


def get_random_image_from_news() -> Optional[str]:
    """
    Lấy một hình ảnh ngẫu nhiên từ bảng news
    
    Returns:
        str: URL của hình ảnh hoặc None nếu không tìm thấy
    """
    try:
        collection = get_news_collection()
        
        # Tìm các bài viết có media (hình ảnh) không null
        pipeline = [
            {"$match": {"media": {"$ne": None}}},
            {"$sample": {"size": 1}},  # Lấy ngẫu nhiên 1 bài
            {"$project": {"media": 1}}
        ]
        
        result = list(collection.aggregate(pipeline))
        
        if result and len(result) > 0:
            return result[0].get("media")
        
        return None
        
    except Exception as e:
        print(f"Error getting random image from news: {str(e)}")
        return None


def get_random_news_urls(count: int = 5) -> List[str]:
    """
    Lấy danh sách URL ngẫu nhiên từ bảng news
    
    Args:
        count: Số lượng URL cần lấy (mặc định là 5)
    
    Returns:
        List[str]: Danh sách các URL ngẫu nhiên
    """
    try:
        collection = get_news_collection()
        
        # Lấy ngẫu nhiên các bài viết có URL
        pipeline = [
            {"$match": {"url": {"$ne": None}}},
            {"$sample": {"size": count}},
            {"$project": {"url": 1}}
        ]
        
        result = list(collection.aggregate(pipeline))
        
        # Trích xuất URLs từ kết quả
        urls = [doc.get("url") for doc in result if doc.get("url")]
        
        return urls
        
    except Exception as e:
        print(f"Error getting random URLs from news: {str(e)}")
        return []


def save_bulletin_to_db(bulletin_data: Dict, metadata: Dict = None, articles: List[Dict] = None) -> Dict:
    try:
        collection = get_bulletin_collection()
        
        # CHỈ lấy hình ảnh từ các bài viết đang được tổng hợp, không fallback
        image_url = None
        
        if articles:
            # Lấy tất cả media URLs từ các bài viết hiện tại
            media_urls = [article.get("media") for article in articles if article.get("media")]
            if media_urls:
                # Chọn ngẫu nhiên một hình ảnh từ các bài viết đang tổng hợp
                image_url = random.choice(media_urls)
        
        # CHỈ lấy URLs của các bài viết đang được tổng hợp làm references, không thêm random
        references = []
        if articles:
            references = [article.get("url") for article in articles if article.get("url")]
        
        # Chuẩn bị document để lưu
        bulletin_doc = {
            "content": bulletin_data.get("bulletin", ""),
            "image_url": image_url,  # Chỉ từ bài viết đang tổng hợp hoặc None
            "references": references,  # Chỉ URLs từ bài viết đang tổng hợp
            "created_at": datetime.now(),
            "metadata": {
                "articles_processed": metadata.get("articles_processed", 0) if metadata else 0,
                "total_found_in_db": metadata.get("total_found_in_db", 0) if metadata else 0,
                "sources_used": metadata.get("sources_used", []) if metadata else [],
                "generated_at": metadata.get("generated_at") if metadata else None,
                "filter_info": metadata.get("filter_info", {}) if metadata else {},
                "success": bulletin_data.get("success", False),
                "sources_count": len(metadata.get("sources_used", [])) if metadata else 0
            },
            "bulletin_id": f"bulletin_{int(datetime.now().timestamp())}"
        }
        
        # Lưu vào database
        result = collection.insert_one(bulletin_doc)
        
        return {
            "success": True,
            "bulletin_id": bulletin_doc["bulletin_id"],
            "inserted_id": str(result.inserted_id),
            "created_at": bulletin_doc["created_at"].isoformat(),
            "image_url": bulletin_doc["image_url"],
            "references": bulletin_doc["references"],
            "articles_processed": bulletin_doc["metadata"]["articles_processed"],
            "sources_count": bulletin_doc["metadata"]["sources_count"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "bulletin_id": None,
            "inserted_id": None
        }


def get_bulletins_from_db(
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 50,
    sort_order: int = -1  # -1 = mới nhất trước, 1 = cũ nhất trước
) -> List[Dict]:
 
    try:
        collection = get_bulletin_collection()
        
        # Xây dựng query filter
        query_filter = {}
        
        if from_time or to_time:
            time_filter = {}
            if from_time:
                time_filter["$gte"] = from_time
            if to_time:
                time_filter["$lte"] = to_time
            query_filter["created_at"] = time_filter
        
        # Query database
        cursor = collection.find(query_filter).sort("created_at", sort_order).limit(limit)
        
        # Convert cursor to list và xử lý ObjectId
        results = []
        for doc in cursor:
            # Convert ObjectId to string
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            # Chuyển datetime thành string để trả về JSON
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            
            results.append(doc)
        
        return results
        
    except Exception as e:
        print(f"Error querying bulletin database: {str(e)}")
        return []


def get_bulletins_paginated(
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: int = -1,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None
) -> Dict:
    """
    Lấy danh sách bulletin với phân trang
    
    Args:
        page: Số trang (bắt đầu từ 1)
        page_size: Số lượng bulletin mỗi trang
        sort_by: Trường để sắp xếp
        sort_order: Thứ tự sắp xếp (-1 = giảm dần, 1 = tăng dần)
        from_time: Thời gian bắt đầu filter
        to_time: Thời gian kết thúc filter
    
    Returns:
        Dict chứa bulletins và thông tin phân trang
    """
    try:
        collection = get_bulletin_collection()
        
        # Xây dựng query filter
        query_filter = {}
        
        if from_time or to_time:
            time_filter = {}
            if from_time:
                time_filter["$gte"] = from_time
            if to_time:
                time_filter["$lte"] = to_time
            query_filter["created_at"] = time_filter
        
        # Tính toán skip value
        skip_value = (page - 1) * page_size
        
        # Đếm tổng số documents
        total_documents = collection.count_documents(query_filter)
        
        # Tính tổng số trang
        total_pages = (total_documents + page_size - 1) // page_size
        
        # Query với pagination
        cursor = collection.find(query_filter).sort(sort_by, sort_order).skip(skip_value).limit(page_size)
        
        # Convert cursor to list và xử lý ObjectId
        bulletins = []
        for doc in cursor:
            # Convert ObjectId to string
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            # Chuyển datetime thành string để trả về JSON
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            
            # Chuyển metadata.generated_at nếu có
            if "metadata" in doc and "generated_at" in doc["metadata"]:
                if isinstance(doc["metadata"]["generated_at"], str):
                    # Đã là string, giữ nguyên
                    pass
                elif doc["metadata"]["generated_at"]:
                    doc["metadata"]["generated_at"] = str(doc["metadata"]["generated_at"])
            
            bulletins.append(doc)
        
        return {
            "success": True,
            "data": bulletins,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_documents": total_documents,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
    except Exception as e:
        print(f"Error getting paginated bulletins: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_documents": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False
            }
        }


def get_bulletin_stats() -> Dict:
    try:
        collection = get_bulletin_collection()
        
        # Đếm tổng số bulletin
        total_bulletins = collection.count_documents({})
        
        # Lấy bulletin mới nhất
        latest_bulletin = collection.find().sort("created_at", -1).limit(1)
        latest_bulletin_doc = next(latest_bulletin, None)
        
        # Lấy bulletin cũ nhất  
        oldest_bulletin = collection.find().sort("created_at", 1).limit(1)
        oldest_bulletin_doc = next(oldest_bulletin, None)
        
        # Thống kê theo ngày gần nhất (7 ngày)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_bulletins = collection.count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        return {
            "total_bulletins": total_bulletins,
            "recent_bulletins_7days": recent_bulletins,
            "latest_bulletin": {
                "created_at": latest_bulletin_doc["created_at"].isoformat() if latest_bulletin_doc else None,
                "bulletin_id": latest_bulletin_doc.get("bulletin_id") if latest_bulletin_doc else None,
                "articles_processed": latest_bulletin_doc.get("metadata", {}).get("articles_processed", 0) if latest_bulletin_doc else 0
            },
            "oldest_bulletin": {
                "created_at": oldest_bulletin_doc["created_at"].isoformat() if oldest_bulletin_doc else None,
                "bulletin_id": oldest_bulletin_doc.get("bulletin_id") if oldest_bulletin_doc else None
            }
        }
        
    except Exception as e:
        print(f"Error getting bulletin stats: {str(e)}")
        return {
            "total_bulletins": 0,
            "recent_bulletins_7days": 0,
            "latest_bulletin": {"created_at": None, "bulletin_id": None, "articles_processed": 0},
            "oldest_bulletin": {"created_at": None, "bulletin_id": None},
            "error": str(e)
        }
