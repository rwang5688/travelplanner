# Requirements Document

## Introduction

A locally executable Streamlit application that provides a chat-style user interface for conversing with the TravelAgent running on AgentCore. The app replaces the reference Docker-based Streamlit app by removing all Cognito user authentication and instead invoking the TravelAgent runtime directly via HTTP POST with OAuth2 client credentials. This is a local development tool for rapid UI iteration — no Docker, ECS, or CloudFront infrastructure is needed.

## Glossary

- **Streamlit_App**: The local Streamlit web application providing the chat UI, located in `streamlit_app/`.
- **TravelAgent_Runtime**: The deployed AgentCore runtime that orchestrates flights and hotels MCP servers via a gateway. Accepts `{"prompt": "..."}` and returns `{"response": "..."}`.
- **OAuth2_Client**: The HTTP client component within the Streamlit_App responsible for obtaining and caching OAuth2 access tokens using the client_credentials grant type.
- **Chat_History**: The list of user and assistant messages stored in Streamlit session state for the current browser session.
- **Token_Cache**: A module-level cache storing the current OAuth2 access token and its expiry timestamp to avoid redundant token requests.
- **Agent_Response**: The JSON object returned by TravelAgent_Runtime containing a `response` field with the assistant's text reply.

## Requirements

### Requirement 1: Project Structure and Local Execution

**User Story:** As a developer, I want to run the Streamlit app locally with a single command, so that I can iterate on the UI without any containerization or cloud deployment.

#### Acceptance Criteria

1. THE Streamlit_App SHALL be runnable with the command `streamlit run streamlit_app/app.py`
2. THE Streamlit_App SHALL have its Python dependencies listed in a `streamlit_app/requirements.txt` file containing `streamlit`, `httpx`, and `boto3`
3. THE Streamlit_App SHALL consist of a single `streamlit_app/app.py` entry point file and a `streamlit_app/agent_client.py` module for TravelAgent_Runtime communication
4. THE Streamlit_App SHALL contain no Cognito user authentication logic, no Docker configuration, and no ECS or CloudFront references

### Requirement 2: Environment-Based Configuration

**User Story:** As a developer, I want to configure the TravelAgent connection via environment variables, so that I can point the app at different AgentCore deployments without code changes.

#### Acceptance Criteria

1. THE Streamlit_App SHALL read the TravelAgent_Runtime invoke endpoint URL from the `TRAVEL_AGENT_URL` environment variable
2. THE Streamlit_App SHALL read the OAuth2 client ID from the `TRAVEL_AGENT_CLIENT_ID` environment variable
3. THE Streamlit_App SHALL read the OAuth2 client secret from the `TRAVEL_AGENT_CLIENT_SECRET` environment variable
4. THE Streamlit_App SHALL read the OAuth2 token endpoint from the `TRAVEL_AGENT_TOKEN_ENDPOINT` environment variable
5. THE Streamlit_App SHALL read the OAuth2 scope from the `TRAVEL_AGENT_SCOPE` environment variable
6. IF any required environment variable (`TRAVEL_AGENT_URL`, `TRAVEL_AGENT_CLIENT_ID`, `TRAVEL_AGENT_CLIENT_SECRET`, `TRAVEL_AGENT_TOKEN_ENDPOINT`) is missing, THEN THE Streamlit_App SHALL display an error message in the UI identifying the missing variable and halt further interaction

### Requirement 3: OAuth2 Token Management

**User Story:** As a developer, I want the app to handle OAuth2 authentication to the TravelAgent runtime automatically, so that I do not need to manage tokens manually.

#### Acceptance Criteria

1. THE OAuth2_Client SHALL obtain an access token from the configured token endpoint using the `client_credentials` grant type with the configured client ID, client secret, and scope
2. THE OAuth2_Client SHALL cache the obtained access token in Token_Cache and reuse the cached token for subsequent requests until 5 minutes before the token's expiry time
3. WHEN the cached token is within 5 minutes of expiry or absent, THE OAuth2_Client SHALL request a new token from the token endpoint before making the next TravelAgent_Runtime request
4. IF the token endpoint returns a non-200 HTTP status code, THEN THE OAuth2_Client SHALL raise an error that is displayed to the user in the chat UI with the HTTP status code and response body

### Requirement 4: Chat-Style User Interface

**User Story:** As a developer, I want a chat-style interface with message history, so that I can have multi-turn conversations with the TravelAgent.

#### Acceptance Criteria

1. THE Streamlit_App SHALL display a page title of "Travel Planner Agent"
2. THE Streamlit_App SHALL render all previous messages from Chat_History using `st.chat_message` with role "user" for user messages and role "assistant" for assistant messages
3. THE Streamlit_App SHALL provide a text input at the bottom of the page using `st.chat_input` with placeholder text "Ask the travel planner..."
4. WHEN the user submits a message via the chat input, THE Streamlit_App SHALL immediately append the user message to Chat_History and display it in the chat UI
5. WHEN the user submits a message, THE Streamlit_App SHALL display a spinner with the text "Thinking..." while waiting for the TravelAgent_Runtime response
6. WHEN the TravelAgent_Runtime returns a successful response, THE Streamlit_App SHALL append the assistant response text to Chat_History and display it in the chat UI
7. THE Streamlit_App SHALL store Chat_History in `st.session_state` so that messages persist across Streamlit reruns within the same browser session

### Requirement 5: TravelAgent Runtime Invocation

**User Story:** As a developer, I want the app to send my messages to the TravelAgent on AgentCore and display the responses, so that I can test the agent's travel planning capabilities through the UI.

#### Acceptance Criteria

1. WHEN the user submits a message, THE Streamlit_App SHALL send an HTTP POST request to the TravelAgent_Runtime invoke endpoint with a JSON body of `{"prompt": "<user_message>"}`
2. THE Streamlit_App SHALL include an `Authorization: Bearer <access_token>` header on every request to TravelAgent_Runtime, using the token obtained by OAuth2_Client
3. THE Streamlit_App SHALL set the `Content-Type` header to `application/json` on every request to TravelAgent_Runtime
4. WHEN TravelAgent_Runtime returns a 200 response, THE Streamlit_App SHALL extract the `response` field from the returned JSON and display the value as the assistant message
5. IF TravelAgent_Runtime returns a non-200 HTTP status code, THEN THE Streamlit_App SHALL display an error message in the chat UI containing the HTTP status code and response text
6. IF a network error occurs during the HTTP request to TravelAgent_Runtime, THEN THE Streamlit_App SHALL display an error message in the chat UI describing the connection failure

### Requirement 6: Sidebar Controls

**User Story:** As a developer, I want a sidebar with a button to clear the conversation, so that I can start fresh conversations without reloading the page.

#### Acceptance Criteria

1. THE Streamlit_App SHALL display a sidebar containing a "Clear Chat" button
2. WHEN the user clicks the "Clear Chat" button, THE Streamlit_App SHALL remove all messages from Chat_History and rerun the app to reflect the empty state
3. THE Streamlit_App SHALL display a brief description in the sidebar explaining that the app connects to the TravelAgent on AgentCore
