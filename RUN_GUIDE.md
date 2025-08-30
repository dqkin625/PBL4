# Crypto News Crawler & Bulletin Generator - Run Guide

## Prerequisites

1. **Python 3.8+** installed on your system
2. **MongoDB** installed and running locally or have access to a MongoDB instance
3. **Gemini API Key** for AI bulletin generation

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd CrawlerWebBot
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017/
MONGO_DB_NAME=crypto_news_db

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Admin Credentials (default: admin/admin123)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 5. Initialize Database

Run the database setup script to create indexes:
```bash
python setup_db.py
```

## Running the Application

### Option 1: Run Directly (Development)
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python run.py
```

This will start:
- API Server on `http://localhost:8000`
- Scheduler that runs every 3 hours

### Option 2: Run API Server Only
```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Run with Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run the Docker helper script
python run-docker.py
```

## API Endpoints

### Public Endpoints

#### 1. Fetch All News from Sources
```bash
curl http://localhost:8000/v1/get_all_news
```
Scrapes news from all configured sources (CoinDesk, CoinGape, CoinTelegraph, CryptoNews, The Block, U.Today)

#### 2. Create News Bulletin
```bash
curl -X POST "http://localhost:8000/v1/create_bulletin?hours=24&limit=10"
```
Parameters:
- `hours`: Get news from last X hours (default: 8)
- `limit`: Maximum articles to process (default: 20)
- `sources`: Comma-separated source names (optional)

#### 3. Get Bulletins
```bash
curl "http://localhost:8000/v1/get_bulletins?hours=24&limit=20"
```

#### 4. Get Bulletin Statistics
```bash
curl http://localhost:8000/v1/bulletin_stats
```

### Admin Endpoints (Requires Authentication)

#### 5. Admin Get Bulletins with Pagination
```bash
curl -u admin:admin123 "http://localhost:8000/v1/admin/bulletins?page=1&page_size=10"
```
Parameters:
- `page`: Page number (starts from 1)
- `page_size`: Items per page (1-100)
- `sort_by`: Field to sort by (default: created_at)
- `sort_order`: asc or desc
- `from_date`: Start date (YYYY-MM-DD)
- `to_date`: End date (YYYY-MM-DD)

## Features

### 1. News Aggregation
- Automatically scrapes crypto news from 6 major sources
- Stores news articles with metadata (title, content, URL, media, author, published time)
- Prevents duplicate articles using URL as unique identifier

### 2. AI-Powered Bulletin Generation
- Uses Google Gemini AI to create comprehensive news summaries
- Generates Vietnamese language bulletins with key points
- Includes random image from news articles
- Provides 5 reference URLs for further reading

### 3. Scheduled Updates
- Automatic news fetching every 3 hours
- Configurable schedule in `schedule_config.py`

### 4. Database Features
- MongoDB for data persistence
- Automatic indexing for optimal performance
- Pagination support for large datasets

## Testing the API

### Test News Fetching
```bash
# Fetch all news
curl http://localhost:8000/v1/get_all_news | python3 -m json.tool
```

### Test Bulletin Creation
```bash
# Create a bulletin from last 24 hours of news
curl -X POST "http://localhost:8000/v1/create_bulletin?hours=24&limit=10" | python3 -m json.tool
```

### Test Admin Access
```bash
# Get paginated bulletins (requires auth)
curl -u admin:admin123 "http://localhost:8000/v1/admin/bulletins?page=1&page_size=5" | python3 -m json.tool
```

## Project Structure
```
CrawlerWebBot/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── news.py         # News API endpoints
│   │   │   └── stats.py        # Statistics endpoints
│   │   └── api_router.py       # API router configuration
│   ├── db/
│   │   ├── client.py           # MongoDB client
│   │   └── config.py           # Database configuration
│   ├── services/
│   │   ├── crypto_news_service.py  # News scraping logic
│   │   ├── db_service.py          # Database operations
│   │   └── gemini_service.py      # AI bulletin generation
│   └── utils/
│       ├── exception_handlers.py  # Error handling
│       └── response.py            # Response formatting
├── main.py                     # FastAPI application
├── run.py                      # Main runner script
├── scheduler.py                # Scheduled tasks
├── schedule_config.py          # Schedule configuration
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker configuration
└── .env                        # Environment variables
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill <PID>
```

### MongoDB Connection Issues
- Ensure MongoDB is running: `mongod`
- Check MongoDB URL in `.env` file
- Verify database permissions

### Missing Dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Gemini API Issues
- Verify your API key is correct in `.env`
- Check API quota limits
- Ensure internet connectivity

## Additional Notes

- The bulletin content is generated in Vietnamese
- Images are randomly selected from news articles
- References provide 5 random article URLs from the database
- Admin endpoints use Basic HTTP authentication
- All timestamps are stored in UTC

## Support

For issues or questions, please refer to the repository's issue tracker or documentation.