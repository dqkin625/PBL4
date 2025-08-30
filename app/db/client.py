from pymongo import MongoClient
from .config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NEWS, MONGO_COLLECTION_BULLETIN

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB_NAME]

def get_db():
    return _db

def get_news_collection():
    return _db[MONGO_COLLECTION_NEWS]

def get_bulletin_collection():
    return _db[MONGO_COLLECTION_BULLETIN]
