"""Debug endpoints for testing infrastructure."""
import os
from fastapi import APIRouter
import redis.asyncio as redis_async
import redis as redis_sync

router = APIRouter()

@router.get("/debug/redis-test")
async def test_redis():
    """Test Redis connectivity."""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    results = {
        "config": {
            "host": redis_host,
            "port": redis_port,
            "env_vars": {
                "REDIS_HOST": os.getenv("REDIS_HOST"),
                "REDIS_PORT": os.getenv("REDIS_PORT"),
                "REDIS_URL": os.getenv("REDIS_URL")
            }
        },
        "async_test": None,
        "sync_test": None
    }
    
    # Test async connection
    try:
        client = redis_async.Redis(
            host=redis_host,
            port=redis_port,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        await client.ping()
        results["async_test"] = "SUCCESS: Async Redis connected"
        await client.close()
    except Exception as e:
        results["async_test"] = f"FAILED: {str(e)}"
    
    # Test sync connection
    try:
        client = redis_sync.Redis(
            host=redis_host,
            port=redis_port,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        client.ping()
        results["sync_test"] = "SUCCESS: Sync Redis connected"
        client.close()
    except Exception as e:
        results["sync_test"] = f"FAILED: {str(e)}"
    
    return results