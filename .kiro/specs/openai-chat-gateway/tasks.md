# Implementation Plan

- [x] 1. Set up project structure and dependencies


  - Create directory structure: app/, app/models/, app/services/, app/repositories/, app/api/, app/core/, tests/
  - Create requirements.txt with FastAPI, SQLModel, asyncpg, aioredis, httpx, pytest, pytest-asyncio, Hypothesis
  - Create .env.example with all required environment variables
  - Set up Python 3.9 compatibility
  - _Requirements: 8.4_

- [x] 2. Implement configuration and settings management


  - Create app/core/config.py with Settings class using pydantic-settings
  - Implement get_or_generate_admin_key() method for admin key management
  - Add validation for required environment variables (OPENAI_API_KEY)
  - _Requirements: 7.1, 7.5, 1.7, 1.8_

- [x] 3. Define data models using SQLModel


  - Create app/models/user.py with User model (username, block_count, is_blocked)
  - Add Pydantic models for requests/responses (CreateUserRequest, UserResponse, ChatRequest, ChatResponse)
  - _Requirements: 1.1, 1.4_

- [x] 4. Create abstraction layer protocols


  - Create app/core/protocols.py with DatabaseRepository, CacheClient, LockManager, OpenAIClient protocols
  - Define all interface methods with type hints
  - _Requirements: 9.1, 9.4_

- [x] 5. Implement PostgreSQL repository


  - Create app/repositories/postgres_repository.py implementing DatabaseRepository protocol
  - Implement create_user, get_user, get_all_users, get_all_usernames, update_user methods
  - Add initialize() method to create tables
  - Use SQLModel with asyncpg for async PostgreSQL operations
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.5_

- [x] 5.1 Write property test for user creation


  - **Property 1: User creation initializes block count to zero**
  - **Validates: Requirements 1.1**

- [x] 5.2 Write property test for user data retrieval

  - **Property 2: User data retrieval accuracy**
  - **Validates: Requirements 1.2**

- [x] 5.3 Write property test for list all users

  - **Property 3: List all users completeness**
  - **Validates: Requirements 1.3**

- [x] 5.4 Write property test for persistence

  - **Property 4: User data persistence across restarts**
  - **Validates: Requirements 1.4**

- [x] 5.5 Write property test for duplicate rejection

  - **Property 5: Duplicate username rejection**
  - **Validates: Requirements 1.5**

- [x] 6. Implement Redis cache client


  - Create app/repositories/redis_cache.py implementing CacheClient protocol
  - Implement get, set, delete, exists methods using aioredis
  - Add health_check() method
  - _Requirements: 3.6, 8.6_

- [x] 7. Implement Redis distributed lock manager


  - Create app/repositories/redis_lock_manager.py implementing LockManager protocol
  - Implement acquire_lock() with async context manager using Redlock algorithm
  - Handle lock timeout and release
  - _Requirements: 4.6, 4.7, 8.6_

- [x] 7.1 Write property test for per-user serialization


  - **Property 8: Concurrent chat requests complete successfully (different users)**
  - **Validates: Requirements 2.4, 4.8**

- [x] 8. Implement username caching service


  - Create app/services/username_cache.py with UsernameCache class
  - Implement get_usernames_except() method with Redis caching
  - Implement invalidate() method for cache invalidation on user creation
  - _Requirements: 3.6, 3.7, 3.8_

- [x] 9. Implement content moderator service


  - Create app/services/content_moderator.py with ContentModerator class
  - Implement check_for_violations() method using word boundary regex
  - Use username cache for efficient lookups
  - Implement case-insensitive, exact word matching
  - _Requirements: 3.1, 3.4, 3.5_

- [x] 9.1 Write property test for mention detection


  - **Property 10: Username mention detection**
  - **Validates: Requirements 3.1**

- [x] 9.2 Write property test for case-insensitive matching

  - **Property 13: Case-insensitive username matching**
  - **Validates: Requirements 3.4**

- [x] 9.3 Write property test for exact matching

  - **Property 14: Exact match only (no substring matching)**
  - **Validates: Requirements 3.5**

- [x] 10. Implement OpenAI client



  - Create app/services/openai_client.py implementing OpenAIClient protocol
  - Implement send_chat_request() using httpx with proper authentication headers
  - Handle errors and timeouts
  - _Requirements: 2.1, 7.2, 7.3_

- [x] 10.1 Write property test for API key usage


  - **Property 22: Single API key for all users**
  - **Validates: Requirements 7.2**

- [x] 10.2 Write property test for API key in headers

  - **Property 23: API key in request headers**
  - **Validates: Requirements 7.3**

- [x] 10.3 Write property test for API key not exposed

  - **Property 24: API key not exposed**
  - **Validates: Requirements 7.4**

- [x] 11. Implement user service



  - Create app/services/user_service.py with UserService class
  - Implement create_user, get_user, get_all_users, get_all_usernames_except methods
  - Implement increment_block_count with atomic transaction and is_blocked update
  - Implement get_or_create_user for auto-creation support
  - _Requirements: 1.1, 1.2, 1.3, 2.6, 4.1, 4.4_



- [x] 11.1 Write property test for block count increment

  - **Property 11: Block count increments by one per request**
  - **Validates: Requirements 3.2, 4.4**



- [x] 11.2 Write property test for blocking trigger


  - **Property 15: Block count of three triggers blocked status**
  - **Validates: Requirements 4.1**

- [x] 12. Implement chat service

  - Create app/services/chat_service.py with ChatService class
  - Implement process_chat_request() orchestrating: lock acquisition, user check, moderation, OpenAI call
  - Handle auto-creation when enabled

  - Ensure violations don't prevent request processing
  - _Requirements: 2.1, 2.2, 2.6, 2.7, 3.2, 3.3_



- [ ] 12.1 Write property test for non-blocked users
  - **Property 6: Non-blocked users can make chat requests**
  - **Validates: Requirements 2.1, 2.2**



- [ ] 12.2 Write property test for blocked users
  - **Property 7: Blocked users are rejected**


  - **Validates: Requirements 2.3, 4.2, 4.3**


- [ ] 12.3 Write property test for violations don't prevent processing
  - **Property 12: Violations don't prevent request processing**

  - **Validates: Requirements 3.3**



- [x] 12.4 Write property test for third violation behavior

  - **Property 16: Third violation request completes before blocking**
  - **Validates: Requirements 4.5**



- [ ] 12.5 Write property test for OpenAI error propagation
  - **Property 9: OpenAI errors are propagated**
  - **Validates: Requirements 2.5, 6.1**

- [x] 13. Implement test mock implementations

  - Create app/tests/mocks.py with InMemoryRepository, InMemoryCache, LocalLockManager, MockOpenAIClient
  - Implement all protocol methods with in-memory data structures
  - _Requirements: 9.1, 9.4_


- [x] 14. Set up dependency injection


  - Create app/core/dependencies.py with FastAPI dependency functions
  - Implement get_db, get_cache, get_lock_manager, get_openai_client
  - Support environment-based configuration (production vs test)
  - _Requirements: 8.4_

- [x] 15. Implement admin authentication middleware




  - Create app/api/auth.py with verify_admin_key dependency
  - Check X-Admin-Key header against configured admin key
  - Return 401 Unauthorized if invalid
  - _Requirements: 1.6_

- [x] 15.1 Write unit test for admin authentication

  - Test valid admin key returns success
  - Test invalid admin key returns 401
  - Test missing admin key returns 401
  - _Requirements: 1.6, 9.7_



- [ ] 16. Implement admin user management endpoints
  - Create app/api/admin.py with admin router
  - Implement POST /admin/users (create user)
  - Implement GET /admin/users/{username} (get user)
  - Implement GET /admin/users (list all users)
  - All endpoints require admin authentication


  - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_


- [ ] 16.1 Write property test for correct status codes
  - **Property 17: Correct HTTP status codes for success**
  - **Validates: Requirements 5.1, 5.2, 5.3**


- [x] 16.2 Write property test for 404 errors


  - **Property 18: 404 for non-existent resources**
  - **Validates: Requirements 5.4**

- [ ] 16.3 Write property test for 400 errors
  - **Property 19: 400 for invalid input**
  - **Validates: Requirements 5.5, 6.4**



- [ ] 17. Implement public chat endpoint
  - Create app/api/chat.py with chat router
  - Implement POST /chat endpoint


  - Integrate with chat service for request processing
  - Handle auto-creation when enabled
  - Return response with block_count and violation_detected
  - _Requirements: 2.1, 2.2, 2.3, 2.6, 2.7_

- [x] 18. Implement health and readiness endpoints


  - Create app/api/health.py with health router
  - Implement GET /health (liveness probe - always returns 200)
  - Implement GET /ready (readiness probe - checks DB and Redis connectivity)
  - _Requirements: 8.1, 8.2_




- [x] 19. Implement application lifecycle management


  - Create app/main.py with FastAPI app initialization
  - Implement lifespan context manager for startup/shutdown
  - Validate configuration on startup
  - Initialize database and test connections
  - Handle SIGTERM for graceful shutdown
  - _Requirements: 7.5, 8.3, 8.4_

- [ ] 20. Implement structured JSON logging
  - Create app/core/logging.py with JSONFormatter
  - Configure logging with request IDs and context
  - Ensure API keys are never logged (redaction)
  - _Requirements: 7.4, 8.7_

- [ ] 20.1 Write property test for internal errors
  - **Property 20: Internal errors return 500**
  - **Validates: Requirements 6.2**

- [ ] 21. Implement exception handlers
  - Create app/core/exceptions.py with custom exception classes
  - Add FastAPI exception handlers for custom exceptions
  - Map exceptions to appropriate HTTP status codes
  - _Requirements: 5.4, 5.5, 6.1, 6.2_

- [ ] 22. Create unit test fixtures and configuration
  - Create tests/unit/conftest.py with test app fixture using mocks
  - Override all dependencies with in-memory implementations
  - _Requirements: 9.1, 9.4_

- [ ] 23. Create integration test fixtures and configuration
  - Create tests/integration/conftest.py with PostgreSQL and Redis setup
  - Start services if not running
  - Create test database
  - Override only OpenAI client with mock
  - _Requirements: 9.2, 9.5_

- [ ] 24. Create end-to-end test fixtures and configuration
  - Create tests/e2e/conftest.py with real server startup
  - Start PostgreSQL, Redis, and FastAPI server as subprocesses
  - Provide httpx.AsyncClient for HTTP requests
  - Handle cleanup on teardown
  - _Requirements: 9.3, 9.6_



- [ ] 24.1 Write E2E test for auto-creation
  - Test with AUTO_CREATE_USERS=true creates user on first chat
  - Test with AUTO_CREATE_USERS=false returns 404 for non-existent user
  - _Requirements: 2.6, 2.7, 9.8_




- [ ] 24.2 Write E2E test for per-user serialization with delays
  - Send 2 concurrent requests from same user with artificial delays
  - Verify requests are processed serially (second waits for first)
  - Send concurrent requests from different users
  - Verify they process in parallel
  - _Requirements: 4.6, 4.7, 4.8, 9.9, 9.10_

- [ ] 25. Create Dockerfile for containerization
  - Create Dockerfile with Python 3.9 base image
  - Multi-stage build for smaller image size
  - Run as non-root user
  - Add health check
  - _Requirements: 8.4_

- [ ] 26. Create Kubernetes deployment manifests
  - Create k8s/deployment.yaml with deployment configuration
  - Configure replicas, resource limits, health probes
  - Create k8s/service.yaml for load balancing
  - Create k8s/secrets.yaml.example for secrets
  - _Requirements: 8.1, 8.2, 8.3, 8.8_

- [ ] 27. Create documentation
  - Create README.md with project overview, setup instructions, API documentation
  - Document environment variables
  - Document local development setup (WSL)
  - Document Kubernetes deployment
  - Document testing strategy (unit, integration, E2E)
  - _Requirements: 8.4_

- [ ] 28. Final checkpoint - Ensure all tests pass
  - Run all unit tests: pytest tests/unit/
  - Run all integration tests: pytest tests/integration/
  - Run all E2E tests: pytest tests/e2e/
  - Verify test coverage
  - Ensure all tests pass, ask the user if questions arise
