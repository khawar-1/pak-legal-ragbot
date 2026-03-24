"""
MongoDB Database Connection and Models
"""
import os
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)

# MongoDB configuration - Using provided Atlas connection string
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://kashan_abbas:kashanabbas@mernapp.1grlr.mongodb.net/?appName=MERNApp")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "aws_chatbot")

# Global MongoDB client
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None

async def connect_to_mongo():
    """Connect to MongoDB database"""
    global mongodb_client, database
    
    try:
        mongodb_client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        await mongodb_client.admin.command('ping')
        
        database = mongodb_client[DATABASE_NAME]
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"Connected to MongoDB: {DATABASE_NAME}")
        print(f"[OK] Connected to MongoDB Atlas: {DATABASE_NAME}")
        return database
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        print(f"[ERROR] MongoDB connection error: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        sessions_collection = database["sessions"]
        
        # Create indexes
        await sessions_collection.create_index("session_id", unique=True)
        await sessions_collection.create_index("user_id")
        await sessions_collection.create_index("created_at")
        await sessions_collection.create_index("last_updated")
        
        logger.info("Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")

def get_database():
    """Get database instance. Returns None if not connected."""
    return database
