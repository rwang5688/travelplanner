"""Streamlit chat UI for the Travel Planner Agent.

Provides a chat-style interface that sends user prompts to the TravelAgent
runtime on AgentCore via the agent_client module and displays responses.

Run with: streamlit run streamlit_app/app.py
"""

import streamlit as st
from agent_client import invoke, get_config_errors

st.set_page_config(page_title="Travel Planner Agent")
st.title("Travel Planner Agent")

# Validate config on startup
errors = get_config_errors()
if errors:
    st.error(f"Missing environment variables: {', '.join(errors)}")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("Connects to the TravelAgent on AgentCore.")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("**Sample Prompts**")
    sample_prompts = [
        "Plan a 5-day trip to Tokyo from SFO, March 10-15 2026. Budget is $3000. I prefer direct flights.",
        "Find me the cheapest way to get to Tokyo from LAX next month. I'm on a tight budget.",
        "Plan a luxury trip to Paris from JFK, March 20-25 2026. Money is not an issue.",
        "I need to go to London from SFO, March 15-20 2026. Budget is $2500. I prefer direct flights and hotels with a gym.",
        "Search flights from SFO to TYO on 2026-03-10 with max price 900",
    ]
    for p in sample_prompts:
        st.code(p, language=None)

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
                response = invoke(prompt)
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                st.error(str(e))
