import json
import redis
from typing import List, Dict
from datetime import datetime


class ChatContextManager:
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=db,
            decode_responses=True
        )

    @staticmethod
    def _get_chat_key(username: str, chat_id: str) -> str:
        """Generate a unique Redis key for a specific chat."""
        return f"chat:{username}:{chat_id}"

    @staticmethod
    def _get_user_chats_key(username: str) -> str:
        """Generate a Redis key for storing chat metadata."""
        return f"chats:{username}"

    def create_new_chat(self, username: str, chat_name: str, context: str = "") -> str:
        """Create a new chat with optional context."""
        chat_id = str(self.redis_client.incr(f"chat_counter:{username}"))

        chat_metadata = {
            "id": chat_id,
            "name": chat_name,
            "context": context,
            "created_at": datetime.now().isoformat(),
            "messages_count": 0,
            "last_updated": datetime.now().isoformat()
        }

        chats_key = self._get_user_chats_key(username)
        self.redis_client.hset(chats_key, chat_id, json.dumps(chat_metadata))

        chat_key = self._get_chat_key(username, chat_id)
        self.redis_client.set(chat_key, json.dumps([]))

        return chat_id

    def get_user_chats(self, username: str) -> List[Dict]:
        """Get all chats for a user."""
        chats_key = self._get_user_chats_key(username)
        chats_data = self.redis_client.hgetall(chats_key)
        return [json.loads(chat_data) for chat_data in chats_data.values()]

    def get_conversation_history(self, username: str, chat_id: str) -> List[Dict]:
        """Retrieve conversation history for a specific chat."""
        chat_key = self._get_chat_key(username, chat_id)
        conversation = self.redis_client.get(chat_key)
        return json.loads(conversation) if conversation else []

    def update_conversation_history(
            self,
            username: str,
            chat_id: str,
            user_input: str,
            assistant_response: str
    ) -> List[Dict]:
        """Update the conversation history for a specific chat."""
        chat_key = self._get_chat_key(username, chat_id)
        conversation_history = self.get_conversation_history(username, chat_id)

        conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant_response}
        ])

        self.redis_client.set(chat_key, json.dumps(conversation_history))

        # Update chat metadata
        chats_key = self._get_user_chats_key(username)
        chat_metadata = json.loads(self.redis_client.hget(chats_key, chat_id))
        chat_metadata["messages_count"] += 2
        chat_metadata["last_updated"] = datetime.now().isoformat()
        self.redis_client.hset(chats_key, chat_id, json.dumps(chat_metadata))

        return conversation_history

    def delete_chat(self, username: str, chat_id: str) -> bool:
        """Delete a specific chat and its history."""
        chat_key = self._get_chat_key(username, chat_id)
        self.redis_client.delete(chat_key)

        chats_key = self._get_user_chats_key(username)
        return bool(self.redis_client.hdel(chats_key, chat_id))

    def update_chat_name(self, username: str, chat_id: str, new_name: str) -> bool:
        """Update chat name."""
        chats_key = self._get_user_chats_key(username)
        chat_metadata = self.redis_client.hget(chats_key, chat_id)

        if not chat_metadata:
            return False

        chat_metadata = json.loads(chat_metadata)
        chat_metadata["name"] = new_name
        chat_metadata["last_updated"] = datetime.now().isoformat()

        self.redis_client.hset(chats_key, chat_id, json.dumps(chat_metadata))
        return True