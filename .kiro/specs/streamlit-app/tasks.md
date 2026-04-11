# Implementation Plan: Streamlit Travel Planner App

## Overview

Build a two-file Streamlit chat app (`streamlit_app/app.py` + `streamlit_app/agent_client.py`) that sends prompts to the TravelAgent runtime on AgentCore via HTTP POST with OAuth2 client_credentials authentication. Tests go in `tests/test_agent_client.py` using pytest and Hypothesis.

## Tasks

- [x] 1. Create project structure and agent_client module
  - [x] 1.1 Create `streamlit_app/requirements.txt` with `streamlit`, `httpx`, and `boto3`
    - _Requirements: 1.2_
  - [x] 1.2 Create `streamlit_app/agent_client.py` with environment variable reading, `get_config_errors()`, `_get_token()`, and `invoke()` functions
    - Read `TRAVEL_AGENT_URL`, `TRAVEL_AGENT_CLIENT_ID`, `TRAVEL_AGENT_CLIENT_SECRET`, `TRAVEL_AGENT_TOKEN_ENDPOINT`, `TRAVEL_AGENT_SCOPE` from environment
    - Implement `get_config_errors()` returning names of missing required vars
    - Implement `_get_token()` with OAuth2 client_credentials flow and 5-minute-early refresh using module-level `_token_cache`
    - Implement `invoke(prompt)` sending POST with Bearer token, returning `response` field or raising `RuntimeError`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  - [ ]* 1.3 Write property test: missing env vars correctly identified
    - **Property 1: Missing environment variables are correctly identified**
    - Generate random subsets of the four required env var names, verify `get_config_errors()` returns the complement
    - **Validates: Requirements 2.6**
  - [ ]* 1.4 Write property test: token cache hit/miss behavior
    - **Property 2: Token cache returns cached token when valid, refreshes when expired**
    - Generate random `expires_in` values and call times, verify cache hit when before `expires_at` and miss when at or after
    - **Validates: Requirements 3.2, 3.3**
  - [ ]* 1.5 Write property test: token endpoint errors include status and body
    - **Property 3: Token endpoint errors include status code and response body**
    - Generate random non-200 status codes (400–599) and response body strings, verify raised error contains both
    - **Validates: Requirements 3.4**
  - [ ]* 1.6 Write property test: invoke sends prompt in correct format
    - **Property 5: Invoke sends prompt in correct request format**
    - Generate random non-empty prompt strings, mock HTTP, verify POST body `prompt` field matches input exactly
    - **Validates: Requirements 5.1**
  - [ ]* 1.7 Write property test: invoke extracts response field
    - **Property 6: Invoke extracts response field from successful agent reply**
    - Generate random response strings, mock 200 response, verify return value matches
    - **Validates: Requirements 5.4**
  - [ ]* 1.8 Write property test: agent runtime errors include status and body
    - **Property 7: Agent runtime errors include status code and response text**
    - Generate random non-200 status codes and body strings, verify raised error contains both
    - **Validates: Requirements 5.5**

- [x] 2. Checkpoint - Verify agent_client module
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create Streamlit UI
  - [x] 3.1 Create `streamlit_app/app.py` with page config, title, sidebar, chat history, and input handling
    - Set page title to "Travel Planner Agent" via `st.set_page_config`
    - Display `st.title("Travel Planner Agent")`
    - Call `get_config_errors()` on startup; if errors, display with `st.error()` and `st.stop()`
    - Sidebar with "Clear Chat" button (resets `st.session_state.messages` to `[]` and calls `st.rerun()`) and description text
    - Initialize `st.session_state.messages` as `[]` if not present
    - Render chat history using `st.chat_message` with role-based rendering
    - Handle `st.chat_input("Ask the travel planner...")`: append user message, call `invoke()` inside `st.spinner("Thinking...")`, append assistant response or display error via `st.error()`
    - _Requirements: 1.1, 1.3, 1.4, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 6.1, 6.2, 6.3_
  - [ ]* 3.2 Write property test: messages correctly appended to chat history
    - **Property 4: Messages are correctly appended to chat history**
    - Generate random role/content pairs, verify append increases list length by one and last element matches
    - **Validates: Requirements 4.4, 4.6**

- [x] 4. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- All tests go in `tests/test_agent_client.py` using pytest + Hypothesis
- The app uses the same OAuth2 `client_credentials` pattern as `travel_agent/agent.py`
