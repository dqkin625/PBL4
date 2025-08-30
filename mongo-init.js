// MongoDB initialization script
db = db.getSiblingDB('crypto_news');

// Create collections
db.createCollection('news');
db.createCollection('bulletin');

// Create indexes for news collection
db.news.createIndex({ "url": 1 }, { unique: true });
db.news.createIndex({ "source": 1 });
db.news.createIndex({ "published_time": -1 });
db.news.createIndex({ "source": 1, "published_time": -1 });

// Create indexes for bulletin collection
db.bulletin.createIndex({ "bulletin_id": 1 }, { unique: true });
db.bulletin.createIndex({ "created_at": -1 });

print('Database initialized successfully with news and bulletin collections!');
