"""
Simple in-memory cache for user data to speed up authentication.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class UserCache:
    def __init__(self, ttl_minutes: int = 5):
        self._cache: Optional[List[Dict]] = None
        self._cache_time: Optional[datetime] = None
        self._ttl = timedelta(minutes=ttl_minutes)
    
    def get(self) -> Optional[List[Dict]]:
        """Get cached users if still valid."""
        if self._cache is None or self._cache_time is None:
            return None
        
        if datetime.now() - self._cache_time > self._ttl:
            # Cache expired
            self._cache = None
            self._cache_time = None
            return None
        
        return self._cache
    
    def set(self, users: List[Dict]):
        """Cache users data."""
        self._cache = users
        self._cache_time = datetime.now()
    
    def clear(self):
        """Clear the cache."""
        self._cache = None
        self._cache_time = None

# Global cache instance
user_cache = UserCache(ttl_minutes=5)
