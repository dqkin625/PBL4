# Crypto News API with Gemini AI

## Mô tả dự án

API scrape tin tức crypto từ các nguồn uy tín và sử dụng Gemini AI để tạo bản tin tóm tắt. Dự án được xây dựng bằng FastAPI và MongoDB.

### Tính năng chính:
- **Scrape tin tức** từ 6 nguồn: CoinDesk, CoinGape, CoinTelegraph, CryptoNews, TheBlock, UToday
- **Tạo bản tin AI** bằng Gemini AI từ các tin tức đã scrape
- **API RESTful** để quản lý và truy xuất tin tức
- **Database MongoDB** để lưu trữ tin tức
- **Docker support** cho deployment dễ dàng

## Cài đặt và chạy dự án

### Yêu cầu hệ thống:
- Docker và Docker Compose
- Hoặc Python 3.11+ và MongoDB (nếu chạy local)

---

## Phương pháp 1: Chạy với Docker (Khuyến nghị)

### Bước 1: Clone và chuẩn bị project
```bash
git clone <repository-url>
cd Crypto_NEWS
```

### Bước 2: Tạo file .env
```bash
# Tạo file .env trong thư mục gốc
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://mongodb:27017
MONGO_DB_NAME=crypto_news
MONGO_COLLECTION_NEWS=news
```

### Bước 3: Chạy với Docker Compose
```bash
# Chạy tất cả services (MongoDB + API + Mongo Express)
docker-compose up -d

# Hoặc chỉ chạy MongoDB và API
docker-compose up -d mongodb app

# Xem logs
docker-compose logs -f app
```

### Bước 4: Kiểm tra services
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **MongoDB**: localhost:27017
- **Mongo Express** (Web UI): http://localhost:8081 (admin/admin123)

---

## Phương pháp 2: Chạy Local (Development)

### Bước 1: Cài đặt dependencies
```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt packages
pip install -r requirements.txt
```

### Bước 2: Chuẩn bị MongoDB
```bash
# Cài đặt MongoDB local hoặc sử dụng MongoDB Atlas
# Hoặc chạy MongoDB bằng Docker:
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

### Bước 3: Tạo file .env
```bash
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=crypto_news
MONGO_COLLECTION_NEWS=news
```

### Bước 4: Setup Database
```bash
# Chạy script setup database và tạo indexes
python setup_db.py
```

### Bước 5: Chạy API server
```bash
# Chạy development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Hoặc
python -m uvicorn main:app --reload
```

---

##  API Endpoints

### News Endpoints

#### 1. Scrape tất cả tin tức
```http
GET /v1/get_all_news
```
- Scrape tin tức từ tất cả 6 nguồn
- Lưu vào database
- Trả về kết quả scraping

#### 2. Lấy tin tức cho bulletin
```http
GET /v1/get_news_for_bulletin?hours=24&sources=coindesk,coingape&limit=50
```
**Parameters:**
- `hours` (int): Lấy tin trong X giờ qua (default: 24)
- `sources` (string): Các nguồn cách nhau bởi dấu phẩy (optional)
- `limit` (int): Số lượng bài viết tối đa (default: 50)

#### 3. Tạo bản tin AI
```http
POST /v1/create_bulletin?hours=8&limit=20
```
**Parameters:**
- `hours` (int): Lấy tin trong X giờ qua (default: 8)
- `sources` (string): Các nguồn tin (optional)
- `limit` (int): Số bài viết để tóm tắt (default: 20)

### Stats Endpoints

#### 4. Thống kê database
```http
GET /v1/db_stats
```

#### 5. Kiểm tra duplicate
```http
GET /v1/check_duplicates
```

#### 6. Xóa duplicate
```http
POST /v1/clean_duplicates
```

---

## Ví dụ sử dụng API

### Scrape tin tức và tạo bulletin:
```bash
# 1. Scrape tin tức mới
curl -X GET "http://localhost:8000/v1/get_all_news"

# 2. Tạo bản tin từ tin trong 12 giờ qua
curl -X POST "http://localhost:8000/v1/create_bulletin?hours=12&limit=15"

# 3. Lấy tin tức từ nguồn cụ thể
curl -X GET "http://localhost:8000/v1/get_news_for_bulletin?hours=24&sources=coindesk,cointelegraph&limit=30"

# 4. Kiểm tra thống kê database
curl -X GET "http://localhost:8000/v1/db_stats"
```

### Với Python requests:
```python
import requests

base_url = "http://localhost:8000"

# Scrape tin tức
response = requests.get(f"{base_url}/v1/get_all_news")
print(response.json())

# Tạo bulletin
response = requests.post(f"{base_url}/v1/create_bulletin?hours=8&limit=20")
bulletin = response.json()
print(bulletin['data']['bulletin'])
```

---

## Database Schema

### Collection: `news`
```json
{
  "_id": "ObjectId",
  "title": "Tiêu đề bài viết",
  "media": "Link tới ảnh bài viết",
  "content": "Nội dung bài viết",
  "url": "https://example.com/article",
  "source": "coindesk|coingape|cointelegraph|cryptonews|theblock|utoday",
  "author": "Tác giả",
  "published_time": "ISO Date",
}
```

### Indexes:
- `url`: Unique index
- `source`: Index cho query theo nguồn
- `published_time`: Index cho query theo thời gian
- `source + published_time`: Compound index

---

## Commands

### Docker Commands:
```bash
# Xem logs
docker-compose logs -f app
docker-compose logs -f mongodb

# Restart services
docker-compose restart app
docker-compose restart mongodb

# Stop và remove containers
docker-compose down

# Rebuild và restart
docker-compose up -d --build
```

### Database Commands:
```bash
# Setup lại database
python setup_db.py

# Kết nối MongoDB CLI (nếu chạy local)
mongosh crypto_news

# Backup database
mongodump --db crypto_news --out backup/

# Restore database
mongorestore --db crypto_news backup/crypto_news/
```

---

## Troubleshooting

### 1. Lỗi kết nối MongoDB:
```bash
# Kiểm tra MongoDB đã chạy chưa
docker-compose ps
# Hoặc
systemctl status mongod
```

### 2. Lỗi Selenium/ChromeDriver:
- Đảm bảo Chrome và ChromeDriver compatible
- Trong Docker đã được setup sẵn

### 3. Lỗi Gemini API:
- Kiểm tra `GEMINI_API_KEY` trong file `.env`
- Đảm bảo API key hợp lệ và có credit

### 4. Lỗi port đã được sử dụng:
```bash
# Thay đổi port trong docker-compose.yml
ports:
  - "8001:8000"  # Thay vì 8000:8000
```

---

## Environment Variables

|       Variable            |       Description             |           Default             |
|---------------------------|-------------------------------|-------------------------------|
| `GEMINI_API_KEY`          | API key cho Google Gemini AI  | Required                      |
| `MONGO_URI`               | MongoDB connection string     | `mongodb://localhost:27017`   |
| `MONGO_DB_NAME`           | Tên database                  | `crypto_news`                 |
| `MONGO_COLLECTION_NEWS`   | Tên collection tin tức        | `news`                        |

