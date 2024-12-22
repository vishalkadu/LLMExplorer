import json
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
import streamlit as st

from context_manager import ChatContextManager
from profile_manager import UserManager


@dataclass
class ModelParameters:
    """Model generation parameters configuration."""
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9

    def to_dict(self) -> Dict:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "num_predict": self.max_tokens
        }


class ModelManager:
    """Handles model-related operations and configurations."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.models = self._fetch_models()

    def _fetch_models(self) -> List[Dict]:
        """Fetch available Ollama models."""
        try:
            response = requests.get(f'{self.base_url}/api/tags')
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            st.error(f"Could not fetch models: {e}")
            return []

    def get_model_size(self, model_name: str) -> float:
        """Get the size of a specific model in GB."""
        model_details = next(
            (model for model in self.models if model['name'] == model_name),
            {}
        )
        return model_details.get('size', 0) / (1024 ** 3)


class APIHandler:
    """Handles API communication with Ollama."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def call_api(self, endpoint: str, payload: Dict) -> Optional[str]:
        """Make API call to Ollama with streaming response."""
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


class UIComponents:
    """Handles UI component rendering."""

    @staticmethod
    def render_model_parameters() -> ModelParameters:
        """Render model parameter controls."""
        with st.expander("🛠️ Model Generation Parameters", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.7,
                    step=0.1,
                    help="Higher values make the output more random"
                )

            with col2:
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=10,
                    max_value=8192,
                    value=512,
                    help="Maximum number of tokens to generate"
                )

            with col3:
                top_p = st.slider(
                    "Top P",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.9,
                    step=0.1,
                    help="Controls diversity via nucleus sampling"
                )

            return ModelParameters(temperature, max_tokens, top_p)

    @staticmethod
    def render_chat_list(chats: List[Dict], context_manager: ChatContextManager):
        """Render chat list in sidebar."""
        st.subheader("Your Chats")
        for chat in sorted(chats, key=lambda x: x['last_updated'], reverse=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                        f"🗨️ {chat['name']}",
                        key=f"chat_{chat['id']}"
                ):
                    st.session_state.current_chat_id = chat['id']
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{chat['id']}"):
                    context_manager.delete_chat(st.session_state.username, chat['id'])
                    if st.session_state.current_chat_id == chat['id']:
                        st.session_state.current_chat_id = None
                    st.rerun()

    @staticmethod
    def render_new_chat_form(context_manager: ChatContextManager):
        """Render new chat creation form."""
        with st.form("new_chat_form"):
            chat_name = st.text_input("Chat Name", value="New Chat")
            chat_context = st.text_area("Initial Context (Optional)")
            if st.form_submit_button("Create Chat"):
                new_chat_id = context_manager.create_new_chat(
                    st.session_state.username,
                    chat_name,
                    chat_context
                )
                st.session_state.current_chat_id = new_chat_id
                st.rerun()


class AuthManager:
    """Handles authentication-related operations."""

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    def show_auth_page(self):
        """Show login/register page."""
        st.title("🤖 LLMExplorer - Login")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            self._render_login_form()

        with tab2:
            self._render_register_form()

    def _render_login_form(self):
        """Render login form."""
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted and username and password:
                if self.user_manager.verify_user(username, password):
                    st.session_state.username = username
                    self.user_manager.update_last_login(username)
                    st.success("Login successful!")
                else:
                    st.error("Invalid credentials")

    def _render_register_form(self):
        """Render registration form."""
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            display_name = st.text_input("Display Name")
            submitted = st.form_submit_button("Register")

            if submitted and new_username and new_password and display_name:
                if self.user_manager.create_user(new_username, new_password, display_name):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists")


class LLMExplorer:
    """Main application class."""

    def __init__(self, base_url='http://localhost:11434'):
        self.base_url = base_url
        self.model_manager = ModelManager(base_url)
        self.api_handler = APIHandler(base_url)
        self.user_manager = UserManager()
        self.context_manager = ChatContextManager()
        self.auth_manager = AuthManager(self.user_manager)
        self.ui = UIComponents()

    def _handle_auth(self) -> bool:
        """Handle user authentication."""
        if 'username' not in st.session_state:
            self.auth_manager.show_auth_page()
            return False
        return True

    def _render_sidebar(self):
        """Render sidebar with user profile and chat management."""
        with st.sidebar:
            # User Profile Section
            st.header("👤 Profile")
            user_profile = self.user_manager.get_user_profile(st.session_state.username)
            st.write(f"Welcome, {user_profile['display_name']}!")
            if st.button("Logout"):
                del st.session_state.username
                del st.session_state.current_chat_id
                st.rerun()

            # Chat Management Section
            st.header("💭 Chats")
            self.ui.render_new_chat_form(self.context_manager)
            chats = self.context_manager.get_user_chats(st.session_state.username)
            self.ui.render_chat_list(chats, self.context_manager)
            return chats

    def _render_chat_interface(self, chats: List[Dict]):
        """Render main chat interface."""
        current_chat = next(
            (c for c in chats if c['id'] == st.session_state.current_chat_id),
            None
        )
        if current_chat:
            st.subheader(f"Chat: {current_chat['name']}")
            if current_chat['context']:
                with st.expander("Chat Context", expanded=False):
                    st.write(current_chat['context'])

        # Chat History Display
        history = self.context_manager.get_conversation_history(
            st.session_state.username,
            st.session_state.current_chat_id
        )
        for message in history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        return history

    def interact(self):
        """Main interaction interface."""
        if not self._handle_auth():
            return

        st.title("🤖 LLMExplorer")

        # Initialize chat state
        if 'current_chat_id' not in st.session_state:
            st.session_state.current_chat_id = None

        # Render sidebar and get chats
        chats = self._render_sidebar()

        # Main Chat Interface
        if st.session_state.current_chat_id is None:
            st.info("👈 Create a new chat or select an existing one from the sidebar")
            return

        # Model Selection
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox(
                "Select Model",
                [model['name'] for model in self.model_manager.models]
            )
        with col2:
            st.metric("Model Size", f"{self.model_manager.get_model_size(selected_model):.2f} GB")

        # Get model parameters
        model_params = self.ui.render_model_parameters()

        st.divider()

        # Render chat interface and get history
        history = self._render_chat_interface(chats)

        # Handle user input
        user_input = st.chat_input("Type your message...")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)

            payload = {
                "model": selected_model,
                "messages": history + [{"role": "user", "content": user_input}],
                "stream": True,
                "options": model_params.to_dict()
            }

            with st.chat_message("assistant"):
                response = self.api_handler.call_api("/api/chat", payload)
                if response:
                    self.context_manager.update_conversation_history(
                        st.session_state.username,
                        st.session_state.current_chat_id,
                        user_input,
                        response
                    )


def main():
    explorer = LLMExplorer()
    explorer.interact()


if __name__ == "__main__":
    main()