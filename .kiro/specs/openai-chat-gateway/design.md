# Design Document

## Overview

The OpenAI Chat API Gateway is a Python-based RESTful API server that provides managed access to OpenAI's Chat API with built-in user management and content moderation. The system uses FastAPI for async request handling, SQLite for persistent storage, and httpx for async HTTP communication with OpenAI's API.

The architecture follows a layered approach with clear separation between API endpoints, business logic services, data access repositories, and external integrations. This design ensures maintainability, testability, and scalability.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (FastAPI Routes - User Management & Chat Endpoints)         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ User Service │  │ Chat Service │  │   Content    │      │
│  │              │  │              │  │  Moderator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────┬───────────────────────┬───────────────┘
                      │                       │
┌─────────────────────▼───────────────────────▼───────────────┐
│                  Repository Layer                            │
│              (User Repository - SQLite)                      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  External Integration                         │
│              (OpenAI Client - httpx async)                   │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Web Framework**: FastAPI 0.104+ (async-native, automatic OpenAPI docs, Pydantic validation)
- **Async HTTP Client**: httpx (for OpenAI API calls)
- **Database**: SQLite with aiosqlite (async SQLite driver)
- **Data Validation**: Pydantic v2 (built into FastAPI)
- **Python Version**: 3.11+
- **Testing**: pytest with pytest-asyncio for async tests

### Design Principles

1. **Async-First**: All I/O operations (database, HTTP) are asynchronous
2. **Separation of Concerns**: Clear boundaries between API, business logic, and data access
3. **Dependency Injection**: FastAPI's dependency system for testability
4. **Fail-Fast**: Validate configuration and dependencies at startup
5. **Explicit Error Handling**: Clear error types and HTTP status codes

## Components and Interfaces

### 1. API Layer (FastAPI Routes)

**User Management Endpoints:**

```python
POST /users
  Request: {"username": str}
  Response: {"username": str, "block_count": int, "is_blocked": bool}
  Status: 201 Created, 400 Bad Request, 409 Conflict

GET /users/{username}
  Response: {"username": str, "block_count": int, "is_blocked": bool}
  Status: 200 OK, 404 Not Found

GET /users
  Response: {"users": [{"username": str, "block_count": int, "is_blocked": bool}]}
  Status: 200 OK
```

**Chat Endpoints:**

```python
POST /chat
  Request: {"username": str, "message": str}
  Response: {"response": str, "block_count": int, "violation_detected": bool}
  Status: 200 OK, 400 Bad Request, 403 Forbidden, 404 Not Found, 502 Bad Gateway
```

### 2. Service Layer

**UserService:**
```python
class UserService:
    async def create_user(username: str) -> User
    async def get_user(username: str) -> User | None
    async def get_all_users() -> list[User]
    async def increment_block_count(username: str) -> User
    async def is_user_blocked(username: str) -> bool
```

**ChatService:**
```python
class ChatService:
    async def process_chat_request(username: str, message: str) -> ChatResponse
    # Orchestrates: moderation check -> OpenAI call -> response
```

**ContentModerator:**
```python
class ContentModerator:
    async def check_for_violations(message: str, requesting_username: str) -> list[str]
    # Returns list of mentioned usernames found in message
```

### 3. Repository Layer

**UserRepository:**
```python
class UserRepository:
    async def create(username: str) -> User
    async def get_by_username(username: str) -> User | None
    async def get_all() -> list[User]
    async def update_block_count(username: str, new_count: int) -> User
    async def initialize_db() -> None
```

### 4. External Integration

**OpenAIClient:**
```python
class OpenAIClient:
    async def send_chat_request(message: str) -> str
    # Sends request to OpenAI API, returns response text
```

## Data Models

### User Model

```python
class User(BaseModel):
    username: str  # Unique identifier, 3-50 characters, alphanumeric + underscore
    block_count: int  # 0-3, increments on violations
    is_blocked: bool  # True when block_count >= 3
    created_at: datetime
    updated_at: datetime
```

**Database Schema:**
```sql
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    block_count INTEGER NOT NULL DEFAULT 0,
    is_blocked BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_is_blocked ON users(is_blocked);
```

### Request/Response Models

```python
class CreateUserRequest(BaseModel):
    username: str

class UserResponse(BaseModel):
    username: str
    block_count: int
    is_blocked: bool

class ChatRequest(BaseModel):
    username: str
    message: str

class ChatResponse(BaseModel):
    response: str
    block_count: int
    violation_detected: bool
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to reduce redundancy:

- Properties 5.1, 5.2, 5.3 (HTTP status codes for success) can be combined into one property about correct status codes
- Properties 2.3, 4.2, 4.3 (blocked user rejection) are redundant - one comprehensive property covers all
- Properties 3.2 and 4.4 (persistence of block count) can be verified by the same property
- Properties 6.3, 7.1, 7.5 (startup validation) are all examples of the same startup behavior

### User Management Properties

**Property 1: User creation initializes block count to zero**
*For any* valid username, creating a new user should result in a user with block_count = 0 and is_blocked = false
**Validates: Requirements 1.1**

**Property 2: User data retrieval accuracy**
*For any* user in the system, retrieving that user's information should return the exact block_count and is_blocked status that was stored
**Validates: Requirements 1.2**

**Property 3: List all users completeness**
*For any* set of users created in the system, the list users operation should return all users with their complete and accurate data
**Validates: Requirements 1.3**

**Property 4: User data persistence across restarts**
*For any* user created in the system, after simulating a database restart (close and reopen connection), the user should still exist with the same username, block_count, and is_blocked status
**Validates: Requirements 1.4**

**Property 5: Duplicate username rejection**
*For any* username that already exists in the system, attempting to create another user with the same username should be rejected with an error
**Validates: Requirements 1.5**

### Chat Request Properties

**Property 6: Non-blocked users can make chat requests**
*For any* non-blocked user and any message, the chat request should be forwarded to the OpenAI API and return a response
**Validates: Requirements 2.1, 2.2**

**Property 7: Blocked users are rejected**
*For any* user with is_blocked = true, attempting a chat request should be rejected with a 403 Forbidden error indicating the user is blocked
**Validates: Requirements 2.3, 4.2, 4.3**

**Property 8: Concurrent chat requests complete successfully**
*For any* set of non-blocked users, sending chat requests concurrently should result in all requests completing successfully without blocking each other
**Validates: Requirements 2.4**

**Property 9: OpenAI errors are propagated**
*For any* error response from the OpenAI API, the API Gateway should return an error response to the user with appropriate error information
**Validates: Requirements 2.5, 6.1**

### Content Moderation Properties

**Property 10: Username mention detection**
*For any* message containing an existing username as a complete word, the Content Moderator should detect it as a violation
**Validates: Requirements 3.1**

**Property 11: Block count increments by one per request**
*For any* chat request where violations are detected, the requesting user's block_count should increase by exactly one, regardless of how many usernames were mentioned
**Validates: Requirements 3.2, 4.4**

**Property 12: Violations don't prevent request processing**
*For any* chat request with detected violations, the request should still be forwarded to OpenAI and return a response, in addition to incrementing the block count
**Validates: Requirements 3.3**

**Property 13: Case-insensitive username matching**
*For any* username in the system, all case variations of that username (uppercase, lowercase, mixed case) appearing in a message should be detected as violations
**Validates: Requirements 3.4**

**Property 14: Exact match only (no substring matching)**
*For any* username, if it appears as a substring within another word (e.g., "alice" in "palace"), it should NOT be detected as a violation
**Validates: Requirements 3.5**

### Blocking Behavior Properties

**Property 15: Block count of three triggers blocked status**
*For any* user, when their block_count reaches 3, the is_blocked field should be set to true
**Validates: Requirements 4.1**

**Property 16: Third violation request completes before blocking**
*For any* user with block_count = 2, a chat request that causes a violation should complete successfully and return a response, but the next chat request should be rejected as blocked
**Validates: Requirements 4.5**

### HTTP API Properties

**Property 17: Correct HTTP status codes for success**
*For any* successful operation, the API should return the appropriate success status code: 201 for user creation, 200 for retrievals and chat requests
**Validates: Requirements 5.1, 5.2, 5.3**

**Property 18: 404 for non-existent resources**
*For any* username that does not exist in the system, GET requests for that user should return HTTP 404
**Validates: Requirements 5.4**

**Property 19: 400 for invalid input**
*For any* request with invalid data (empty username, missing required fields, invalid format), the API should return HTTP 400 with validation error details
**Validates: Requirements 5.5, 6.4**

### Error Handling and Security Properties

**Property 20: Internal errors return 500**
*For any* unexpected internal error during request processing, the API should return HTTP 500 and log error details
**Validates: Requirements 6.2**

**Property 21: Data integrity under concurrent modifications**
*For any* user, when multiple concurrent requests attempt to increment their block_count, the final block_count should equal the initial count plus the number of requests (no lost updates)
**Validates: Requirements 6.5**

**Property 22: Single API key for all users**
*For any* set of chat requests from different users, all requests to OpenAI should use the same configured API key
**Validates: Requirements 7.2**

**Property 23: API key in request headers**
*For any* request to OpenAI, the HTTP headers should include the Authorization header with the configured API key in the format "Bearer {api_key}"
**Validates: Requirements 7.3**

**Property 24: API key not exposed**
*For any* API response or log output, the OpenAI API key should not appear in the content
**Validates: Requirements 7.4**

## Error Handling

### Error Types and HTTP Status Codes

| Error Condition | HTTP Status | Error Response |
|----------------|-------------|----------------|
| User not found | 404 Not Found | `{"detail": "User not found: {username}"}` |
| User already exists | 409 Conflict | `{"detail": "User already exists: {username}"}` |
| User is blocked | 403 Forbidden | `{"detail": "User is blocked and cannot make requests"}` |
| Invalid request data | 400 Bad Request | `{"detail": "Validation error", "errors": [...]}` |
| OpenAI API error | 502 Bad Gateway | `{"detail": "Upstream service error: {error}"}` |
| Internal server error | 500 Internal Server Error | `{"detail": "Internal server error"}` |
| Missing API key | 500 Internal Server Error | Startup failure with log message |

### Error Handling Strategy

1. **Validation Errors**: FastAPI/Pydantic automatically handles request validation and returns 422/400
2. **Business Logic Errors**: Custom exceptions mapped to appropriate HTTP status codes
3. **External Service Errors**: Catch httpx exceptions, map to 502 Bad Gateway
4. **Database Errors**: Catch aiosqlite exceptions, log details, return 500
5. **Startup Validation**: Check for required configuration (API key) before starting server

### Custom Exception Classes

```python
class UserNotFoundError(Exception): pass
class UserAlreadyExistsError(Exception): pass
class UserBlockedError(Exception): pass
class OpenAIServiceError(Exception): pass
```

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases:

- **User Service**: Creating users with various usernames, handling duplicates
- **Content Moderator**: Detecting mentions in specific message examples
- **OpenAI Client**: Mocking API responses and error conditions
- **API Endpoints**: Testing specific request/response scenarios

**Testing Framework**: pytest with pytest-asyncio for async test support

### Property-Based Testing

Property-based tests will verify universal properties across many randomly generated inputs:

- **Library**: Hypothesis (Python's leading property-based testing library)
- **Configuration**: Minimum 100 iterations per property test
- **Tagging**: Each property test must include a comment with format: `# Feature: openai-chat-gateway, Property {number}: {property_text}`

**Property Test Coverage**:
- User management operations (creation, retrieval, persistence)
- Content moderation (mention detection with various message formats)
- Block count increments and blocking behavior
- Concurrent request handling
- HTTP status code correctness
- Error propagation and handling

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

# Feature: openai-chat-gateway, Property 1: User creation initializes block count to zero
@given(username=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')))
async def test_user_creation_initializes_block_count(username):
    user = await user_service.create_user(username)
    assert user.block_count == 0
    assert user.is_blocked == False
```

### Integration Testing

Integration tests will verify component interactions:
- API endpoints → Services → Repository → Database
- Full request flow including moderation and OpenAI calls (with mocked OpenAI)
- Database persistence and transaction handling

### Test Data Strategy

- **Unit Tests**: Hand-crafted examples covering edge cases
- **Property Tests**: Hypothesis-generated random data within valid constraints
- **Integration Tests**: Realistic scenarios with multiple users and requests

## Implementation Notes

### Configuration Management

```python
class Settings(BaseSettings):
    openai_api_key: str  # Required, loaded from env var OPENAI_API_KEY
    openai_model: str = "gpt-3.5-turbo"  # Default model
    database_url: str = "sqlite+aiosqlite:///./gateway.db"
    
    class Config:
        env_file = ".env"
```

### Async Database Connection Management

Use FastAPI's lifespan events to manage database initialization and cleanup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database
    await user_repository.initialize_db()
    yield
    # Shutdown: cleanup if needed
```

### Content Moderation Algorithm

```python
def detect_mentions(message: str, all_usernames: set[str], requesting_user: str) -> list[str]:
    # Tokenize message into words
    # For each word, check case-insensitive match against usernames
    # Exclude the requesting user's own username
    # Return list of detected usernames
```

### Concurrency Considerations

- **Database**: SQLite with WAL mode for better concurrent write performance
- **Block Count Updates**: Use database transactions to ensure atomic increments
- **Race Conditions**: The "check if blocked then process" pattern needs careful handling to avoid TOCTOU issues

### OpenAI API Integration

```python
async def send_chat_request(self, message: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": message}]
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

## Deployment Considerations

### Environment Variables

```
OPENAI_API_KEY=sk-...  # Required
OPENAI_MODEL=gpt-3.5-turbo  # Optional, defaults to gpt-3.5-turbo
DATABASE_URL=sqlite+aiosqlite:///./gateway.db  # Optional
```

### Database Initialization

The application will automatically create the SQLite database and tables on first startup.

### Logging

- Use Python's `logging` module with structured logging
- Log levels: INFO for normal operations, ERROR for failures
- Never log the OpenAI API key

### Performance Considerations

- SQLite is suitable for moderate load (hundreds of users)
- For higher scale, consider PostgreSQL with asyncpg
- Connection pooling handled by aiosqlite
- OpenAI rate limits should be monitored and handled gracefully
