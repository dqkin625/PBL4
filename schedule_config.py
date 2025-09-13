API_CONFIG = {
    "base_url": "http://localhost:8000",
    
    # API endpoints
    "endpoints": {
        "get_all_news": "/v1/get_all_news",
        "create_bulletin": "/v1/create_bulletin"
    },
    
    # Request timeout (seconds)
    "timeout": 300,  # 5 minutes
    
    # Request headers
    "headers": {
        "Content-Type": "application/json",
        "User-Agent": "CrawlerWebBot-Scheduler/1.0"
    }
}

# Schedule Configuration
SCHEDULE_CONFIG = {
    # Thời gian giữa các lần chạy (phút)
    "interval_minutes": 2,  # 3 tiếng = 180 phút
    
    # Chạy ngay khi khởi động
    "run_on_startup": True,
    
    # Thời gian chờ giữa get_all_news và create_bulletin (giây)
    "delay_between_tasks": 1,
    
    # Số lần thử lại khi API lỗi
    "max_retries": 3,
    
    # Thời gian chờ giữa các lần retry (giây)
    "retry_delay": 60
}

# Bulletin Configuration
BULLETIN_CONFIG = {
    # Số giờ lấy tin tức (từ hiện tại trở về trước)
    "hours": 3,
    
    # Giới hạn số bài viết
    "limit": 30,
    
    # Các nguồn tin cụ thể (để trống sẽ lấy tất cả)
    # Ví dụ: "coindesk,coingape,cointelegraph"
    "sources": None
}
