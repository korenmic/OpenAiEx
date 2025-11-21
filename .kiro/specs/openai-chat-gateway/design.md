# Design Document

## Overview

The OpenAI Chat API Gateway is a cloud-native Python-based RESTful API server that provides managed access to OpenAI's Chat API with built-in user management and content moderation. The system is designed for horizontal scalability in Kubernetes environments with enterprise-grade reliability, observability, and performance.

The architecture follows a layered approach with clear separation between API endpoints, business logic services, data access repositories, and external integrations. All components use abstraction layers (protocols) to enable flexible testing strategies from unit tests with mocks to end-to-end tests with real running servers.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (FastAPI Routes - Public Chat + Admin User Management)     │
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
│              (User Repository - PostgreSQL)                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                Infrastructure Components                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Redis      │  │  Distributed │  │   OpenAI     │      │
│  │   Cache      │  │    Locks     │  │   Client     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Web Framework**: FastAPI 0.104+ (async-native, automatic OpenAPI docs, Pydantic validation)
- **ORM**: SQLModel 0.0.14+ (combines SQLAlchemy + Pydantic for type-safe database models)
- **Database**: PostgreSQL 13+ with asyncpg driver (cloud-native, multi-pod safe)
- **Cache & Locks**: Redis 6+ with aioredis (distributed caching and locking)
- **Async HTTP Client**: httpx (for OpenAI API calls)
- **Data Validation**: Pydantic v2 (built into FastAPI and SQLModel)
- **Python Version**: 3.9+ (WSL compatibility)
- **Testing**: pytest with pytest-asyncio for async tests, Hypothesis for property-based testing

### Design Principles

1. **Cloud-Native**: Stateless application design, horizontal scalability, health checks, graceful shutdown
2. **Async-First**: All I/O operations (database, HTTP, cache, locks) are asynchronous
3. **Abstraction Layer**: Protocol-based interfaces enable flexible testing (mocks, real services, or hybrid)
4. **Dependency Injection**: FastAPI's dependency system for testability and flexibility
5. **Fail-Fast**: Validate configuration and dependencies at startup
6. **Explicit Error Handling**: Clear error types and HTTP status codes
7. **Twelve-Factor App**: All configuration via environment variables, structured logging, stateless processes

## Components and Interfaces

### 1. API Layer (FastAPI Routes)

**Public Endpoints:**

```python
POST /chat
  Request: {"username": str, "message": str}
  Response: {"response": str, "block_count": int, "violation_detected": bool}
  Status: 200 OK, 400 Bad Request, 403 Forbidden, 404 Not Found, 502 Bad Gateway
  Description: Public endpoint for chat requests, auto-creates users if enabled

GET /health
  Response: {"status": "healthy"}
  Status: 200 OK
  Description: Liveness probe for Kubernetes

GET /ready
  Response: {"status": "ready", "database": "connected", "redis": "connected"}
  Status: 200 OK (ready) or 503 Service Unavailable (not ready)
  Description: Readiness probe for Kubernetes
```

**Admin Endpoints (require X-Admin-Key header):**

```python
POST /admin/users
  Headers: {"X-Admin-Key": str}
  Request: {"username": str}
  Response: {"username": str, "block_count": int, "is_blocked": bool}
  Status: 201 Created, 400 Bad Request, 401 Unauthorized, 409 Conflict
  Description: Internal endpoint for user creation

GET /admin/users/{username}
  Headers: {"X-Admin-Key": str}
  Response: {"username": str, "block_count": int, "is_blocked": bool}
  Status: 200 OK, 401 Unauthorized, 404 Not Found
  Description: Retrieve user information

GET /admin/users
  Headers: {"X-Admin-Key": str}
  Response: {"users": [{"username": str, "block_count": int, "is_blocked": bool}]}
  Status: 200 OK, 401 Unauthorized
  Description: List all users
```

### 2. Service Layer

**UserService:**
```python
class UserService:
    async def create_user(username: str) -> User
    async def get_user(username: str) -> User | None
    async def get_all_users() -> list[User]
    async def get_all_usernames_except(exclude: str) -> set[str]
    async def increment_block_count(username: str) -> User
    async def is_user_blocked(username: str) -> bool
    async def get_or_create_user(username: str) -> User  # For auto-creation
```

**ChatService:**
```python
class ChatService:
    async def process_chat_request(username: str, message: str) -> ChatResponse
    # Orchestrates:
    # 1. Acquire per-user distributed lock
    # 2. Get or create user (if auto-creation enabled)
    # 3. Check if blocked
    # 4. Content moderation check
    # 5. Increment block count if violations found
    # 6. Forward to OpenAI
    # 7. Return response
    # 8. Release lock
```

**ContentModerator:**
```python
class ContentModerator:
    async def check_for_violations(message: str, requesting_username: str) -> list[str]
    # Returns list of mentioned usernames found in message
    # Uses cached username list for efficiency
```

### 3. Abstraction Layer (Protocols)

All components use protocol-based interfaces to enable flexible testing:

**DatabaseRepository (Protocol):**
```python
class DatabaseRepository(Protocol):
    async def create_user(username: str) -> User
    async def get_user(username: str) -> User | None
    async def get_all_users() -> list[User]
    async def get_all_usernames() -> list[str]  # Optimized query
    async def update_user(user: User) -> User
    async def initialize() -> None
```

**CacheClient (Protocol):**
```python
class CacheClient(Protocol):
    async def get(key: str) -> str | None
    async def set(key: str, value: str, ttl: int | None = None) -> None
    async def delete(key: str) -> None
    async def exists(key: str) -> bool
```

**LockManager (Protocol):**
```python
class LockManager(Protocol):
    async def acquire_lock(key: str, timeout: float = 30.0) -> AsyncContextManager
    # Returns async context manager for use with 'async with'
```

**OpenAIClient (Protocol):**
```python
class OpenAIClient(Protocol):
    async def send_chat_request(message: str) -> str
```

### 4. Real Implementations (Production)

**PostgresRepository:**
```python
class PostgresRepository(DatabaseRepository):
    # Uses SQLModel + asyncpg for PostgreSQL
    # Implements all protocol methods with real database queries
```

**RedisCache:**
```python
class RedisCache(CacheClient):
    # Uses aioredis for distributed caching
```

**RedisLockManager:**
```python
class RedisLockManager(LockManager):
    # Uses aioredis with Redlock algorithm for distributed locks
```

**OpenAIHttpClient:**
```python
class OpenAIHttpClient(OpenAIClient):
    # Uses httpx for real OpenAI API calls
```

### 5. Test Implementations (Mocks)

**InMemoryRepository:**
```python
class InMemoryRepository(DatabaseRepository):
    # Dictionary-based in-memory implementation for fast unit tests
```

**InMemoryCache:**
```python
class InMemoryCache(CacheClient):
    # Dictionary-based cache for testing
```

**LocalLockManager:**
```python
class LocalLockManager(LockManager):
    # asyncio.Lock-based implementation for single-process tests
```

**MockOpenAIClient:**
```python
class MockOpenAIClient(OpenAIClient):
    # Returns predefined responses for testing
```

## Data Models

### User Model (SQLModel)

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    username: str = Field(primary_key=True, max_length=50)
    block_count: int = Field(default=0, ge=0, le=3)
    is_blocked: bool = Field(default=False)
```

**Database Schema (PostgreSQL):**
```sql
CREATE TABLE users (
    username VARCHAR(50) PRIMARY KEY,
    block_count INTEGER NOT NULL DEFAULT 0 CHECK (block_count >= 0 AND block_count <= 3),
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_is_blocked ON users(is_blocked);
CREATE INDEX idx_block_count ON users(block_count);
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

The testing strategy follows a three-tier pyramid approach, leveraging the abstraction layer for flexible test configurations.

### Test Tier 1: Unit Tests (Fast - All Mocked)

**Purpose**: Verify individual components in isolation with maximum speed

**Configuration**:
- Use FastAPI's TestClient (in-process, no real HTTP server)
- All dependencies mocked via abstraction layer
- InMemoryRepository, InMemoryCache, LocalLockManager, MockOpenAIClient
- No external services required (PostgreSQL, Redis, OpenAI)

**Coverage**:
- User Service logic (creation, retrieval, blocking)
- Content Moderator logic (mention detection, word boundaries)
- Chat Service orchestration
- API endpoint request/response handling
- Admin authentication

**Example**:
```python
# tests/unit/test_user_service.py
@pytest.fixture
def test_app():
    app.dependency_overrides[get_db] = lambda: InMemoryRepository()
    app.dependency_overrides[get_cache] = lambda: InMemoryCache()
    yield app
    app.dependency_overrides.clear()

def test_create_user(test_app):
    client = TestClient(test_app)
    response = client.post("/admin/users", 
                          json={"username": "alice"},
                          headers={"X-Admin-Key": "test-key"})
    assert response.status_code == 201
```

**Execution**: `pytest tests/unit/` (runs in seconds)

### Test Tier 2: Integration Tests (Medium - Real Services, TestClient)

**Purpose**: Verify component interactions with real infrastructure

**Configuration**:
- Use FastAPI's TestClient (in-process, no real HTTP server)
- Real PostgreSQL and Redis running on localhost
- Mock only external APIs (OpenAI)
- PostgresRepository, RedisCache, RedisLockManager, MockOpenAIClient

**Coverage**:
- Database queries and transactions
- Redis caching behavior
- Distributed lock functionality
- Username cache invalidation
- Full request flow with real persistence

**Setup**:
```python
# tests/integration/conftest.py
@pytest.fixture(scope="session")
def postgres_db():
    # Start PostgreSQL if not running
    subprocess.run(["sudo", "service", "postgresql", "start"])
    # Create test database
    yield "postgresql://localhost:5432/gateway_test"
    # Cleanup

@pytest.fixture(scope="session")
def redis_server():
    subprocess.run(["sudo", "service", "redis-server", "start"])
    yield "redis://localhost:6379"

@pytest.fixture
def integration_app(postgres_db, redis_server):
    # Use real DB and Redis, mock OpenAI
    app.dependency_overrides[get_openai] = lambda: MockOpenAIClient()
    yield app
    app.dependency_overrides.clear()
```

**Execution**: `pytest tests/integration/` (runs in seconds to minutes)

### Test Tier 3: End-to-End Tests (Slow - Real Running Server)

**Purpose**: Verify complete system behavior exactly as in production

**Configuration**:
- Real FastAPI server running as subprocess (uvicorn on 127.0.0.1:8000)
- Real PostgreSQL (127.0.0.1:5432)
- Real Redis (127.0.0.1:6379)
- Tests use httpx.AsyncClient to make actual HTTP requests
- Mock only OpenAI (or use real API with test key)

**Coverage**:
- Full HTTP request/response cycle
- Multi-process behavior
- Graceful shutdown
- Health/readiness endpoints
- Admin authentication over HTTP
- Auto-creation flow
- Per-user request serialization with real delays

**Setup**:
```python
# tests/e2e/conftest.py
@pytest.fixture(scope="session")
def running_server():
    # Start PostgreSQL and Redis
    subprocess.run(["sudo", "service", "postgresql", "start"])
    subprocess.run(["sudo", "service", "redis-server", "start"])
    
    # Start FastAPI server as subprocess
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env={
            "DATABASE_URL": "postgresql://localhost:5432/gateway_test",
            "REDIS_URL": "redis://localhost:6379",
            "OPENAI_API_KEY": "test-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AUTO_CREATE_USERS": "true"
        }
    )
    
    # Wait for server to be ready
    time.sleep(3)
    
    yield "http://127.0.0.1:8000"
    
    # Cleanup
    process.terminate()
    process.wait()

@pytest.fixture
async def e2e_client(running_server):
    async with httpx.AsyncClient(base_url=running_server, timeout=30.0) as client:
        yield client
```

**Example**:
```python
# tests/e2e/test_chat_flow.py
async def test_concurrent_same_user_serialization(e2e_client):
    """Verify same-user requests are serialized"""
    # Send 2 requests from same user concurrently
    responses = await asyncio.gather(
        e2e_client.post("/chat", json={"username": "alice", "message": "hi"}),
        e2e_client.post("/chat", json={"username": "alice", "message": "hello"})
    )
    # Both should succeed, but processed serially
    assert all(r.status_code == 200 for r in responses)
```

**Execution**: `pytest tests/e2e/` (runs in minutes)

### Property-Based Testing

Property-based tests will be integrated across all tiers:

- **Library**: Hypothesis (Python's leading property-based testing library)
- **Configuration**: Minimum 100 iterations per property test
- **Tagging**: Each property test must include a comment with format: `# Feature: openai-chat-gateway, Property {number}: {property_text}`
- **Data Generation**: Use Hypothesis strategies, but avoid generating usernames that might trigger blocking in tests that don't expect it

**Example**:
```python
from hypothesis import given, strategies as st, settings

# Feature: openai-chat-gateway, Property 1: User creation initializes block count to zero
@given(username=st.text(min_size=3, max_size=50, 
                       alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), 
                                            whitelist_characters='_')))
@settings(max_examples=100)
async def test_user_creation_initializes_block_count(username):
    user = await user_service.create_user(username)
    assert user.block_count == 0
    assert user.is_blocked == False
```

### Test Organization

```
tests/
├── unit/                          # Tier 1: All mocked, TestClient
│   ├── conftest.py
│   ├── test_user_service.py
│   ├── test_content_moderator.py
│   ├── test_chat_service.py
│   └── test_api_endpoints.py
│
├── integration/                   # Tier 2: Real DB/Redis, TestClient
│   ├── conftest.py
│   ├── test_user_repository.py
│   ├── test_cache_integration.py
│   ├── test_lock_manager.py
│   └── test_full_flow.py
│
└── e2e/                          # Tier 3: Real running server
    ├── conftest.py
    ├── test_chat_flow.py
    ├── test_user_blocking.py
    ├── test_concurrent_requests.py
    ├── test_admin_endpoints.py
    └── test_health_endpoints.py
```

### Running Tests

```bash
# Fast unit tests only (seconds)
pytest tests/unit/ -v

# Integration tests (requires PostgreSQL/Redis)
pytest tests/integration/ -v

# Full E2E tests (starts real server)
pytest tests/e2e/ -v

# All tests
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

## Implementation Notes

### Configuration Management

```python
from pydantic_settings import BaseSettings
import secrets
import hashlib
from pathlib import Path

class Settings(BaseSettings):
    # Required
    openai_api_key: str  # OPENAI_API_KEY env var
    
    # Optional with defaults
    openai_model: str = "gpt-3.5-turbo"
    database_url: str = "postgresql+asyncpg://localhost:5432/gateway"
    redis_url: str = "redis://localhost:6379"
    auto_create_users: bool = True
    admin_api_key: str | None = None  # ADMIN_API_KEY env var
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
    
    def get_or_generate_admin_key(self) -> str:
        """Get admin key from env or generate and save to file"""
        if self.admin_api_key:
            return self.admin_api_key
        
        # Generate random admin key
        key = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        
        # Save to file
        key_file = Path.home() / ".gateway_admin_key"
        key_file.write_text(key)
        key_file.chmod(0o600)  # Read/write for owner only
        
        print(f"Generated admin API key and saved to: {key_file}")
        return key
```

### Application Lifecycle Management

```python
from contextlib import asynccontextmanager
import signal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    
    # Validate required config
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize admin key
    admin_key = settings.get_or_generate_admin_key()
    app.state.admin_key = admin_key
    
    # Initialize database
    await db_repository.initialize()
    
    # Test connections
    await db_repository.health_check()
    await redis_cache.health_check()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down gracefully...")
    await db_repository.close()
    await redis_cache.close()
    logger.info("Shutdown complete")

app = FastAPI(lifespan=lifespan)

# Handle SIGTERM for graceful shutdown
def handle_sigterm(signum, frame):
    logger.info("Received SIGTERM, initiating graceful shutdown")
    raise KeyboardInterrupt()

signal.signal(signal.SIGTERM, handle_sigterm)
```

### Content Moderation Algorithm

```python
import re

def detect_mentions(message: str, all_usernames: set[str], requesting_user: str) -> list[str]:
    """
    Detect username mentions in message using word boundary matching.
    Case-insensitive, exact word matches only.
    """
    # Tokenize into words (alphanumeric + underscore)
    words = re.findall(r'\b\w+\b', message.lower())
    
    # Check each word against usernames (case-insensitive)
    mentioned = []
    usernames_lower = {u.lower(): u for u in all_usernames if u.lower() != requesting_user.lower()}
    
    for word in words:
        if word in usernames_lower:
            mentioned.append(usernames_lower[word])
    
    return list(set(mentioned))  # Remove duplicates
```

### Username Caching Strategy

```python
class UsernameCache:
    """Redis-backed username cache with simple invalidation"""
    
    CACHE_KEY = "usernames:all"
    
    def __init__(self, redis: CacheClient, db: DatabaseRepository):
        self.redis = redis
        self.db = db
    
    async def get_usernames_except(self, exclude: str) -> set[str]:
        """Get all usernames except one, using cache"""
        # Try cache first
        cached = await self.redis.get(self.CACHE_KEY)
        if cached:
            usernames = set(cached.split(","))
        else:
            # Cache miss - query database and populate cache
            usernames = set(await self.db.get_all_usernames())
            if usernames:
                await self.redis.set(self.CACHE_KEY, ",".join(usernames))
        
        # Remove excluded username
        usernames.discard(exclude)
        return usernames
    
    async def invalidate(self):
        """Invalidate cache when users are created - simple deletion"""
        await self.redis.delete(self.CACHE_KEY)
```

### Distributed Locking Implementation

```python
from aioredis import Redis
from contextlib import asynccontextmanager

class RedisLockManager:
    """Distributed locks using Redis"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    @asynccontextmanager
    async def acquire_lock(self, key: str, timeout: float = 30.0):
        """Acquire distributed lock with timeout"""
        lock_key = f"lock:{key}"
        lock_value = secrets.token_hex(16)
        
        # Try to acquire lock
        acquired = await self.redis.set(
            lock_key, 
            lock_value, 
            ex=int(timeout),
            nx=True  # Only set if not exists
        )
        
        if not acquired:
            # Wait for lock to be released
            for _ in range(int(timeout * 10)):
                await asyncio.sleep(0.1)
                acquired = await self.redis.set(lock_key, lock_value, ex=int(timeout), nx=True)
                if acquired:
                    break
            else:
                raise TimeoutError(f"Could not acquire lock for {key}")
        
        try:
            yield
        finally:
            # Release lock only if we still own it
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.redis.eval(script, 1, lock_key, lock_value)
```

### Concurrency Considerations

**Per-User Request Serialization:**
```python
async def process_chat_with_lock(username: str, message: str):
    """Process chat request with per-user locking"""
    async with lock_manager.acquire_lock(f"user:{username}"):
        # Only one request per user at a time
        # Multiple users can be processed concurrently
        return await chat_service.process_chat_request(username, message)
```

**Database Transactions:**
```python
async def increment_block_count_atomic(username: str):
    """Atomically increment block count and update is_blocked"""
    async with db.transaction():
        user = await db.get_user(username)
        user.block_count += 1
        if user.block_count >= 3:
            user.is_blocked = True
        await db.update_user(user)
        return user
```

### OpenAI API Integration

```python
class OpenAIHttpClient:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    async def send_chat_request(self, message: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": message}]
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                raise OpenAIServiceError(f"OpenAI API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise OpenAIServiceError(f"OpenAI API request failed: {str(e)}")
```

### Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for log aggregation"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "username"):
            log_data["username"] = record.username
        
        # Never log sensitive data
        if "api_key" in str(log_data).lower():
            log_data["message"] = "[REDACTED - contains API key]"
        
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("gateway")
logger.addHandler(handler)
```

## Cloud-Native Deployment

### Environment Variables (Production)

```bash
# Required
OPENAI_API_KEY=sk-...
ADMIN_API_KEY=<generated-or-provided>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres-service:5432/gateway

# Redis
REDIS_URL=redis://redis-service:6379

# Configuration
AUTO_CREATE_USERS=true
OPENAI_MODEL=gpt-3.5-turbo
LOG_LEVEL=INFO
```

### Kubernetes Deployment

**Deployment YAML:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
spec:
  replicas: 3  # Horizontal scaling
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gateway-secrets
              key: openai-api-key
        - name: ADMIN_API_KEY
          valueFrom:
            secretKeyRef:
              name: gateway-secrets
              key: admin-api-key
        - name: DATABASE_URL
          value: "postgresql+asyncpg://user:pass@postgres:5432/gateway"
        - name: REDIS_URL
          value: "redis://redis:6379"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Local Development (WSL)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Start services
sudo service postgresql start
sudo service redis-server start

# Create database
sudo -u postgres createdb gateway_dev

# Install Python dependencies
pip install -r requirements.txt

# Run application
export OPENAI_API_KEY=sk-...
export DATABASE_URL=postgresql+asyncpg://localhost:5432/gateway_dev
export REDIS_URL=redis://localhost:6379
python -m uvicorn app.main:app --reload
```

### Performance Considerations

- **PostgreSQL**: Connection pooling via SQLAlchemy (default 5-20 connections)
- **Redis**: Connection pooling via aioredis
- **Horizontal Scaling**: Stateless design allows unlimited replicas
- **Lock Contention**: Per-user locks minimize contention, different users don't block each other
- **Cache Hit Rate**: Username cache reduces DB queries by ~99% after warmup
- **OpenAI Rate Limits**: Consider implementing rate limiting per user or globally
