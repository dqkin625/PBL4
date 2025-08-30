from fastapi import APIRouter, HTTPException
from app.db.client import get_news_collection
from app.utils.response import response_data, StatusMessage

router = APIRouter()

@router.get("/db_stats")
def get_database_stats():
    try:
        collection = get_news_collection()
        
        # Đếm tổng số bài viết
        total_count = collection.count_documents({})
        
        # Đếm theo từng source
        source_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        sources_stats = list(collection.aggregate(source_pipeline))
        
        # Chuyển đổi format cho dễ đọc
        stats = {}
        for item in sources_stats:
            source = item["_id"] if item["_id"] else "unknown"
            stats[source] = item["count"]
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "database_stats": {
                    "total": total_count,
                    "by_source": stats
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy thống kê database: {str(e)}"
        )

@router.get("/check_duplicates")
def check_duplicates():
    try:
        collection = get_news_collection()
        
        # Pipeline để tìm URL trùng lặp
        pipeline = [
            {
                "$group": {
                    "_id": "$url",
                    "count": {"$sum": 1},
                    "sources": {"$addToSet": "$source"},
                    "ids": {"$push": "$_id"}
                }
            },
            {
                "$match": {"count": {"$gt": 1}}
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        duplicates = list(collection.aggregate(pipeline))
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "total_duplicates": len(duplicates),
                "duplicates": duplicates[:10],
                "message": f"Found {len(duplicates)} duplicate URLs"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi kiểm tra duplicate: {str(e)}"
        )

@router.post("/clean_duplicates")
def clean_duplicates():    
    try:
        collection = get_news_collection()
        
        # Tìm tất cả URL trùng lặp
        pipeline = [
            {
                "$group": {
                    "_id": "$url",
                    "count": {"$sum": 1},
                    "docs": {"$push": {"id": "$_id", "source": "$source", "published_time": "$published_time"}}
                }
            },
            {
                "$match": {"count": {"$gt": 1}}
            }
        ]
        
        duplicates = list(collection.aggregate(pipeline))
        deleted_count = 0
        
        for dup in duplicates:
            docs = dup["docs"]
            # Sắp xếp theo thời gian, giữ lại doc mới nhất
            docs.sort(key=lambda x: x.get("published_time") or "", reverse=True)
            
            # Xóa các doc cũ (giữ lại doc đầu tiên - mới nhất)
            ids_to_delete = [doc["id"] for doc in docs[1:]]
            
            if ids_to_delete:
                result = collection.delete_many({"_id": {"$in": ids_to_delete}})
                deleted_count += result.deleted_count
        
        return response_data(
            status_code=200,
            message=StatusMessage.SUCCESS,
            data={
                "message": f"Deleted {deleted_count} duplicate articles",
                "total_duplicates_found": len(duplicates),
                "total_deleted": deleted_count
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xóa duplicate: {str(e)}"
        )
