#!/usr/bin/env python3

import sys
import os

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.init_indexes import ensure_indexes
from app.db.client import get_db

def setup_database():
    try:
        print("Đang kết nối tới MongoDB...")
        db = get_db()
        
        # Test connection
        db.command("ping")
        print("Kết nối MongoDB thành công!")
        
        print("\nĐang tạo indexes...")
        ensure_indexes()
        
        print("\nSetup database hoàn thành!")
        print("\nCollection đã được tạo:")
        for collection_name in db.list_collection_names():
            print(f"  - {collection_name}")
        
        print("\nTất cả tin tức sẽ được lưu vào collection 'news' với field 'source' để phân biệt nguồn tin.")
            
    except Exception as e:
        print(f"Lỗi setup database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
