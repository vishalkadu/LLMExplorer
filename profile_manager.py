import json
import redis
from typing import Dict, Optional
from datetime import datetime


class UserManager:
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=db,
            decode_responses=True
        )

    @staticmethod
    def _get_user_key(username: str) -> str:
        """Generate Redis key for user profile."""
        return f"profile:{username}"

    def create_user(self, username: str, password: str, display_name: str) -> bool:
        """Create a new user profile."""
        user_key = self._get_user_key(username)

        # Check if user already exists
        if self.redis_client.exists(user_key):
            return False

        user_data = {
            "username": username,
            "password": password,  # In production, use proper password hashing
            "display_name": display_name,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }

        self.redis_client.set(user_key, json.dumps(user_data))
        return True

    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials."""
        user_key = self._get_user_key(username)
        user_data = self.redis_client.get(user_key)

        if not user_data:
            return False

        user_data = json.loads(user_data)
        return user_data["password"] == password  # In production, use proper password verification

    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user profile data."""
        user_key = self._get_user_key(username)
        user_data = self.redis_client.get(user_key)
        return json.loads(user_data) if user_data else None

    def update_last_login(self, username: str):
        """Update user's last login time."""
        user_key = self._get_user_key(username)
        user_data = json.loads(self.redis_client.get(user_key))
        user_data["last_login"] = datetime.now().isoformat()
        self.redis_client.set(user_key, json.dumps(user_data))