from pymongo import ASCENDING, DESCENDING, TEXT
from .client import get_news_collection, get_bulletin_collection

def ensure_news_indexes():
    """Tạo indexes cho collection news"""
    
    try:
        col = get_news_collection()
        
        # unique theo URL (tránh lưu trùng 1 bài)
        col.create_index([("url", ASCENDING)], name="uniq_url", unique=True)
        
        # thời gian xuất bản để sort/filter
        col.create_index([("published_time", DESCENDING)], name="idx_published_time_desc")
        
        # tìm kiếm full-text theo title & content
        col.create_index([("title", TEXT), ("content", TEXT)], name="text_title_content")
        
        # filter theo author
        col.create_index([("author", ASCENDING)], name="idx_author")
        
        # filter theo source - QUAN TRỌNG để phân biệt các nguồn tin
        col.create_index([("source", ASCENDING)], name="idx_source")
        
        # compound index cho source + published_time
        col.create_index([("source", ASCENDING), ("published_time", DESCENDING)], name="idx_source_pubtime")
        
        print(f"Indexes ensured for news collection")
        
    except Exception as e:
        print(f"Error creating indexes for news collection: {e}")


def ensure_bulletin_indexes():
    """Tạo indexes cho collection bulletin"""
    
    try:
        col = get_bulletin_collection()
        
        # Index cho created_at để sort theo thời gian tạo
        col.create_index([("created_at", DESCENDING)], name="idx_created_at_desc")
        
        # Index unique cho bulletin_id
        col.create_index([("bulletin_id", ASCENDING)], name="uniq_bulletin_id", unique=True)
        
        # Index cho type để phân loại bulletin
        col.create_index([("type", ASCENDING)], name="idx_type")
        
        # Compound index cho type + created_at
        col.create_index([("type", ASCENDING), ("created_at", DESCENDING)], name="idx_type_created")
        
        # Index cho metadata.articles_processed để query theo số bài viết
        col.create_index([("metadata.articles_processed", DESCENDING)], name="idx_articles_processed")
        
        # Text search cho content bulletin
        col.create_index([("content", TEXT)], name="text_bulletin_content")
        
        print(f"Indexes ensured for bulletin collection")
        
    except Exception as e:
        print(f"Error creating indexes for bulletin collection: {e}")


def ensure_indexes():
    """Tạo indexes cho tất cả collections"""
    ensure_news_indexes()
    ensure_bulletin_indexes()


if __name__ == "__main__":
    ensure_indexes()
    print("All indexes ensured.")
