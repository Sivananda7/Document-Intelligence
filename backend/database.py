import os
from motor.motor_asyncio import AsyncIOMotorClient

# Get the MongoDB URI from the environment variable (default for local development)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "document_intelligence")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    """Create MongoDB connection."""
    print(f"Connecting to MongoDB at {MONGODB_URL}...")
    db.client = AsyncIOMotorClient(MONGODB_URL)
    db.db = db.client[DATABASE_NAME]
    print("Connected to MongoDB.")

async def close_mongo_connection():
    """Close MongoDB connection."""
    print("Closing MongoDB connection...")
    if db.client is not None:
        db.client.close()
    print("MongoDB connection closed.")

def get_db():
    """Return database instance."""
    return db.db
