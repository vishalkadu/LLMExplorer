import subprocess
import time

import redis
import requests
import streamlit as st


class ServiceManager:
    def __init__(self):
        self.redis_port = 6379
        self.ollama_port = 11434
        self.streamlit_script = "app.py"

    def start_redis(self):
        """Start Redis server if not already running."""
        try:
            client = redis.StrictRedis(host="localhost", port=self.redis_port)
            client.ping()
            st.info("Redis is already running ✅")
        except redis.ConnectionError:
            st.info("Starting Redis server...")
            subprocess.Popen(["redis-server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(3)  # Allow some time for Redis to start
            try:
                client.ping()
                st.success("Redis started successfully ✅")
            except redis.ConnectionError:
                st.error("Failed to start Redis. Check logs for details.")

    def is_ollama_running(self):
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"http://localhost:{self.ollama_port}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def start_ollama(self):
        """Start Ollama server if not already running."""
        if self.is_ollama_running():
            st.info("Ollama is already running ✅")
        else:
            st.info("Starting Ollama server...")
            subprocess.Popen(["ollama", "start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)  # Allow some time for Ollama to start
            if self.is_ollama_running():
                st.success("Ollama started successfully ✅")
            else:
                st.error("Failed to start Ollama. Check logs for details.")

    def start_streamlit(self):
        """Start Streamlit app."""
        st.info("Starting Streamlit app...")
        subprocess.Popen(["streamlit", "run", self.streamlit_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def start_all_services(self):
        """Start all services: Redis, Ollama, and Streamlit."""
        with st.spinner("Starting services..."):
            self.start_redis()
            self.start_ollama()
            self.start_streamlit()
            st.success("All services started successfully ✅")


# Streamlit UI
def main():
    st.set_page_config(page_title="Service Manager", page_icon="⚙️")
    st.title("⚙️ Service Manager")

    service_manager = ServiceManager()

    if st.button("Start All Services"):
        service_manager.start_all_services()


if __name__ == "__main__":
    main()
