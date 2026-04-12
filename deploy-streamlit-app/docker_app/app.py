"""Streamlit chat UI for the Travel Planner Agent with Cognito authentication.

Provides a chat-style interface behind Cognito login that sends user prompts
to the TravelAgent runtime on AgentCore via the agent_client module and
displays responses.

Run with: streamlit run app.py
"""

import streamlit as st
import cognito_client
import agent_client
from config_file import Config

st.set_page_config(page_title="Travel Planner Agent")
st.title("Travel Planner Agent")

# Initialise CognitoAuthenticator
authenticator = cognito_client.get_authenticator(
    Config.SECRETS_MANAGER_ID, Config.DEPLOYMENT_REGION
)

# Authenticate user, and stop here if not logged in
is_logged_in = authenticator.login()
if not is_logged_in:
    st.stop()

# Validate config on startup
errors = agent_client.get_config_errors()
if errors:
    st.error(f"Missing environment variables: {', '.join(errors)}")
    st.stop()


def logout():
    authenticator.logout()


# Sidebar
with st.sidebar:
    st.text(f"Welcome,\n{authenticator.get_username()}")
    st.button("Logout", "logout_btn", on_click=logout)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Init chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle input
if prompt := st.chat_input("Ask the travel planner..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = agent_client.invoke(prompt)
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                st.error(str(e))
