import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def _get_mongo_uri() -> str:
    return os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")


def _get_mongo_db_name() -> str:
    return os.getenv("MONGO_DB_NAME", "student_db")


_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(_get_mongo_uri())
    return _mongo_client


def close_mongo_client() -> None:
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


async def get_mongo_db() -> AsyncIOMotorDatabase:
    client = get_mongo_client()
    return client[_get_mongo_db_name()]
