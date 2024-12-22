#!/bin/bash

# Function to check if Redis is running
is_redis_running() {
    for i in {1..10}; do
        if redis-cli ping | grep -q PONG; then
            echo "Redis is running and accessible."
            return 0
        fi
        sleep 1
    done
    return 1
}

# Function to check if Ollama is running
is_ollama_running() {
    for i in {1..30}; do
        if curl --silent --fail http://localhost:11434/api/tags > /dev/null; then
            echo "Ollama server is running and accessible."
            return 0
        fi
        sleep 1
    done
    return 1
}

# Start Redis server if not running
if ! is_redis_running; then
    echo "Starting Redis server..."
    redis-server > redis.log 2>&1 &
    sleep 2  # Give Redis a moment to start
    if ! is_redis_running; then
        echo "Failed to start Redis server. Check redis.log for details."
        exit 1
    fi
else
    echo "Redis is already running."
fi

# Start the Ollama server
echo "Starting the Ollama server..."
ollama start > ollama.log 2>&1 &
if is_ollama_running; then
    echo "Ollama server started successfully."
else
    echo "Failed to start Ollama server. Check ollama.log for details."
    exit 1
fi

# Start the Streamlit server
echo "Starting the Streamlit app..."
streamlit run app.py
