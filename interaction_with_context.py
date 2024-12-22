import json

import requests
import streamlit as st

from context_manager import get_conversation_history, update_conversation_history


class LLMExplorer:
    def __init__(self, base_url='http://localhost:11434'):
        self.base_url = base_url
        self.models = self._fetch_models()

    def _fetch_models(self):
        """Fetch available Ollama models"""
        try:
            response = requests.get(f'{self.base_url}/api/tags')
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            st.error(f"Could not fetch models: {e}")
            return []

    def _call_ollama_api(self, endpoint, payload):
        """Make API call to Ollama with streaming response"""
        try:
            with requests.post(
                    f'{self.base_url}{endpoint}',
                    json=payload,
                    stream=True
            ) as response:
                response.raise_for_status()
                full_response = ""
                response_placeholder = st.empty()

                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line.decode('utf-8'))
                            if 'response' in json_response:
                                full_response += json_response['response']
                            elif 'message' in json_response:
                                full_response += json_response['message'].get('content', '')

                            response_placeholder.markdown(full_response)
                        except json.JSONDecodeError:
                            st.error("Error parsing API response")
                return full_response

        except Exception as e:
            st.error(f"API Call Error: {e}")
            return None


    def interact(self):
        """Main interaction interface"""
        st.title("🤖LLMExplorer")

        # Model Selection
        if not self.models:
            st.warning("No models available. Ensure Ollama is running.")
            return

        col1, col2 = st.columns(2)

        with col1:
            selected_model = st.selectbox(
                "Select Model",
                [model['name'] for model in self.models]
            )

        with col2:
            model_details = next(
                (model for model in self.models if model['name'] == selected_model),
                {}
            )
            st.metric("Model Size",
                      f"{model_details.get('size', 0) / (1024 ** 3):.2f} GB")

        # Advanced Model Controls
        with st.expander("🛠️ Model Generation Parameters"):
            col1, col2, col3 = st.columns(3)

            with col1:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.7,
                    step=0.1
                )

            with col2:
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=10,
                    max_value=4096,
                    value=512
                )

            with col3:
                top_p = st.slider(
                    "Top P",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.9,
                    step=0.1
                )

        # User Input
        user_input = st.text_area(
            "Enter your prompt",
            placeholder="Type your message here..."
        )

        # Initialize session state if not already initialized
        if 'user_id' not in st.session_state:
            st.session_state.user_id = "user_123"  # Unique user/session identifier

        # When the button is pressed
        if st.button(" 💬 Chat", type="secondary", key="API - chat", use_container_width=True):
            if user_input:
                # Get current conversation history
                conversation_history = get_conversation_history(st.session_state.user_id)

                # prepare the payload for the API call (conversation history plus user input)
                payload = {
                    "model": selected_model,
                    "messages": conversation_history + [{"role": "user", "content": user_input}],
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "num_predict": max_tokens
                    }
                }

                response = self._call_ollama_api("/api/chat", payload)

                # update conversation history with user input and assistant response
                update_conversation_history(st.session_state.user_id, user_input, response)



def main():
    explorer = LLMExplorer()
    explorer.interact()


if __name__ == "__main__":
    main()
