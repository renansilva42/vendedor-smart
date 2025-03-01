from typing import Dict, Any, Optional, Union
import logging
import json
import time
from functools import wraps
from threading import Lock
from .interfaces import CacheServiceInterface

logger = logging.getLogger(__name__)

class CacheEntry:
    """Represents a cached item with TTL support."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl  # TTL in seconds
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

class MemoryCacheService(CacheServiceInterface):
    """In-memory implementation of cache service with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            with self._lock:
                entry = self._cache.get(key)
                if entry is None:
                    return None
                
                if entry.is_expired():
                    del self._cache[key]
                    return None
                
                return entry.value
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        try:
            with self._lock:
                self._cache[key] = CacheEntry(value, ttl)
                return True
                
        except Exception as e:
            logger.error(f"Error setting cache value: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                return True
                
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear all cached values."""
        try:
            with self._lock:
                self._cache.clear()
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        try:
            removed = 0
            with self._lock:
                expired_keys = [
                    key for key, entry in self._cache.items()
                    if entry.is_expired()
                ]
                for key in expired_keys:
                    del self._cache[key]
                    removed += 1
                return removed
                
        except Exception as e:
            logger.error(f"Error cleaning up expired entries: {str(e)}")
            return 0

def cached(ttl: Optional[int] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Get cache instance (assuming it's available globally or through context)
            cache = MemoryCacheService()  # In practice, this should be injected
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached new value for key: {cache_key}")
            
            return result
        return wrapper
    return decorator

class JSONSerializableCacheService(MemoryCacheService):
    """Cache service that handles JSON serialization for complex objects."""
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with JSON serialization."""
        try:
            serialized_value = json.dumps(value)
            return super().set(key, serialized_value, ttl)
        except Exception as e:
            logger.error(f"Error serializing cache value: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache with JSON deserialization."""
        try:
            value = super().get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error deserializing cache value: {str(e)}")
            return None
