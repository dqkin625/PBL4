import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "crypto_news")
MONGO_COLLECTION_NEWS = os.getenv("MONGO_COLLECTION_NEWS", "news")
MONGO_COLLECTION_BULLETIN = os.getenv("MONGO_COLLECTION_BULLETIN", "bulletin")
