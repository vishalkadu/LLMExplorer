import json

import redis

# Initialize Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


def get_conversation_history(user_id):
    """Retrieve conversation history from Redis."""
    conversation = redis_client.get(user_id)
    if conversation:
        return json.loads(conversation)
    return []


def save_conversation_history(user_id, conversation_history):
    """Save conversation history to Redis."""
    redis_client.set(user_id, json.dumps(conversation_history))


def update_conversation_history(user_id, user_input, assistant_response):
    """Update the conversation history with user and assistant messages."""
    # Get current conversation history
    conversation_history = get_conversation_history(user_id)

    # Add user message and assistant response to the conversation
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": assistant_response})

    # Save the updated conversation back to Redis
    save_conversation_history(user_id, conversation_history)

    return conversation_history

############################################################################################################

# WIP - Embedding history
def get_embedding_history(user_id):
    """Retrieve embedding history from Redis."""
    embeddings = redis_client.get(f"{user_id}_embeddings")
    if embeddings:
        return json.loads(embeddings)
    return []


def save_embedding_history(user_id, embedding_history):
    """Save embedding history to Redis."""
    redis_client.set(f"{user_id}_embeddings", json.dumps(embedding_history))


def update_embedding_history(user_id, prompt, embedding_response):
    """Update the embedding history with the prompt and generated embedding."""
    # Get current embedding history
    embedding_history = get_embedding_history(user_id)

    # Add prompt and embedding response to the history
    embedding_history.append({"prompt": prompt, "embedding": embedding_response})

    # Save the updated embedding history back to Redis
    save_embedding_history(user_id, embedding_history)

    return embedding_history
