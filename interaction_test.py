import json

import requests
import streamlit as st


class LLMExplorerTest:
    def __init__(self, base_url='http://localhost:11434'):
        # subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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

    def _call_ollama_api(self, endpoint, payload, is_embedding=False):
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
                            if is_embedding:
                                response_placeholder.markdown(json_response)
                                continue
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

    @staticmethod
    def render_api_documentation():
        """Render comprehensive API documentation"""
        st.sidebar.title("🔍API Endpoints")

        api_docs = {
            "Chat": {
                "endpoint": "/api/chat",
                "description": "Start an interactive chat session",
                "method": "POST",
                "payload": {
                    "model": "Selected model name",
                    "messages": [
                        {"role": "user", "content": "Your message"}
                    ],
                    "stream": True
                }
            },
            "Generate": {
                "endpoint": "/api/generate",
                "description": "Generate text based on a prompt",
                "method": "POST",
                "payload": {
                    "model": "Selected model name",
                    "prompt": "Your input text",
                    "stream": True
                }
            },
            "Embeddings": {
                "endpoint": "/api/embeddings",
                "description": "Generate vector embeddings for text",
                "method": "POST",
                "payload": {
                    "model": "Selected model name",
                    "prompt": "Text to embed"
                }
            }
        }

        for name, details in api_docs.items():
            with st.sidebar.expander(f"🚀 {name} API"):
                st.json(details)

    def interact(self):
        """Main interaction interface"""
        st.title("🤖LLMExplorer")

        # Render API documentation
        self.render_api_documentation()

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

        if st.button(" 💬 Chat", type="secondary", key="API - chat", use_container_width=True):
            payload = {
                "model": selected_model,
                "messages": [{"role": "user", "content": user_input}],
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens
                }
            }
            self._call_ollama_api("/api/chat", payload)

        with st.expander("✍️Generate Text - API"):
            if st.button("Stateless No context, generate Text", type="secondary"):
                payload = {
                    "model": selected_model,
                    "prompt": user_input,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "num_predict": max_tokens
                    }
                }
                self._call_ollama_api("/api/generate", payload)

        with st.expander("🧬 Generate Embeddings - API"):
            if st.button("Generate Embeddings (check if model supports)", type="secondary"):
                payload = {
                    "model": selected_model,
                    "prompt": user_input
                }
                self._call_ollama_api("/api/embeddings", payload, is_embedding=True)


def main():
    explorer = LLMExplorerTest()
    explorer.interact()


if __name__ == "__main__":
    main()
