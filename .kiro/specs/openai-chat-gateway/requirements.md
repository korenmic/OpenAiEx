# Requirements Document

## Introduction

This document specifies the requirements for an OpenAI Chat API Gateway - a cloud-native RESTful API server that acts as a proxy to OpenAI's Chat API with built-in user management and content moderation capabilities. The system manages artificial users (not actual OpenAI accounts), handles asynchronous requests to a single OpenAI API key, and enforces content moderation rules to prevent users from mentioning other users in their chat requests. The system is designed for horizontal scalability in Kubernetes environments with enterprise-grade reliability and observability.

## Glossary

- **API Gateway**: The RESTful API server system being developed
- **Artificial User**: A user entity managed by the API Gateway, not an actual OpenAI account
- **OpenAI Client**: The component that communicates with OpenAI's API using a single API key
- **Content Moderator**: The service component that detects and enforces user mention violations
- **Block Count**: An integer counter tracking how many times a user has violated the mention policy
- **Blocked User**: A user whose block count has reached or exceeded 3, preventing further chat requests
- **User Mention**: The occurrence of one user's username appearing in another user's chat request content
- **Chat Request**: An HTTP request to send a message to OpenAI's Chat API on behalf of a user
- **Admin API Key**: A secret key required to access internal administrative endpoints
- **Username Cache**: An in-memory cache of all usernames for efficient content moderation
- **Distributed Lock**: A Redis-based locking mechanism ensuring per-user request serialization across multiple pods
- **Auto-Creation**: Automatic creation of users on their first chat request when enabled via configuration

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to manage artificial users within the API Gateway through secure administrative endpoints, so that I can control access to the OpenAI Chat API without requiring actual OpenAI accounts for each user.

#### Acceptance Criteria

1. WHEN an authenticated admin requests to create a new user with a unique username, THEN the API Gateway SHALL create an artificial user with a block count initialized to zero and is_blocked set to false
2. WHEN an authenticated admin requests user information by username, THEN the API Gateway SHALL return the user's current block count and blocked status
3. WHEN an authenticated admin requests a list of all users, THEN the API Gateway SHALL return all artificial users with their usernames, block counts, and blocked status
4. THE API Gateway SHALL persist user data in PostgreSQL so that user information remains available across server restarts and pod replacements
5. WHEN an admin attempts to create a user with a duplicate username, THEN the API Gateway SHALL reject the request and return an error response
6. WHEN a request to an admin endpoint lacks a valid admin API key, THEN the API Gateway SHALL reject the request with HTTP 401 Unauthorized
7. THE API Gateway SHALL load the admin API key from the ADMIN_API_KEY environment variable at startup
8. WHEN the ADMIN_API_KEY environment variable is not set, THEN the API Gateway SHALL generate a random admin API key, write it to a file, and log the file path

### Requirement 2

**User Story:** As a user, I want to send chat requests to OpenAI through the API Gateway, so that I can interact with OpenAI's language models without managing my own API key.

#### Acceptance Criteria

1. WHEN a non-blocked user submits a chat request with a message, THEN the API Gateway SHALL forward the request to OpenAI's Chat API using the configured API key
2. WHEN the OpenAI Client receives a response from OpenAI, THEN the API Gateway SHALL return the response content to the requesting user along with the current block count and violation detection status
3. WHEN a blocked user attempts to submit a chat request, THEN the API Gateway SHALL reject the request and return HTTP 403 Forbidden with an error indicating the user is blocked
4. THE API Gateway SHALL handle chat requests asynchronously to support concurrent requests from different users without blocking
5. WHEN the OpenAI API returns an error, THEN the API Gateway SHALL propagate the error information to the requesting user with HTTP 502 Bad Gateway
6. WHEN a user does not exist and auto-creation is enabled, THEN the API Gateway SHALL automatically create the user by calling the internal user creation endpoint with the admin API key
7. WHEN a user does not exist and auto-creation is disabled, THEN the API Gateway SHALL reject the request with HTTP 404 Not Found
8. THE API Gateway SHALL load the auto-creation setting from the AUTO_CREATE_USERS environment variable at startup

### Requirement 3

**User Story:** As a system administrator, I want the Content Moderator to efficiently detect when users mention other users in their chat requests, so that I can enforce community guidelines and prevent harassment.

#### Acceptance Criteria

1. WHEN a user submits a chat request, THEN the Content Moderator SHALL retrieve all usernames except the requesting user's username and scan the message content for mentions
2. WHEN the Content Moderator detects one or more user mentions in a chat request, THEN the API Gateway SHALL increment the requesting user's block count by one
3. WHEN a user mention is detected, THEN the API Gateway SHALL process the chat request normally after incrementing the block count
4. THE Content Moderator SHALL perform case-insensitive username matching when detecting mentions
5. THE Content Moderator SHALL only detect exact username matches as complete words, not partial or substring matches
6. THE API Gateway SHALL maintain a username cache in Redis to minimize database queries during content moderation
7. WHEN a new user is created, THEN the API Gateway SHALL invalidate the username cache to ensure fresh data on next access
8. WHEN retrieving usernames for moderation, THEN the API Gateway SHALL query only the username column from the database, not block counts or other fields

### Requirement 4

**User Story:** As a system administrator, I want users to be automatically blocked after exceeding the violation threshold, so that repeat offenders cannot continue to violate community guidelines.

#### Acceptance Criteria

1. WHEN a user's block count reaches three, THEN the API Gateway SHALL set the is_blocked field to true
2. WHEN a user is marked as blocked, THEN the API Gateway SHALL reject all subsequent chat requests from that user
3. WHEN a blocked user attempts a chat request, THEN the API Gateway SHALL return HTTP 403 Forbidden indicating the user is blocked and cannot make further requests
4. THE API Gateway SHALL persist block count and is_blocked updates immediately after each violation using database transactions
5. WHEN a user's block count is incremented to three during a chat request, THEN the API Gateway SHALL complete the current request before blocking future requests
6. THE API Gateway SHALL use distributed locks to ensure only one chat request from the same user is processed at a time across all pods
7. WHEN multiple chat requests from the same user arrive concurrently, THEN the API Gateway SHALL serialize them using per-user distributed locks
8. WHEN chat requests from different users arrive concurrently, THEN the API Gateway SHALL process them in parallel without blocking each other

### Requirement 5

**User Story:** As a developer integrating with the API Gateway, I want clear RESTful API endpoints with proper HTTP methods and status codes, so that I can easily build client applications.

#### Acceptance Criteria

1. THE API Gateway SHALL expose a POST endpoint for creating new users that returns HTTP 201 on success
2. THE API Gateway SHALL expose a GET endpoint for retrieving user information that returns HTTP 200 on success
3. THE API Gateway SHALL expose a POST endpoint for submitting chat requests that returns HTTP 200 on success
4. WHEN a requested resource does not exist, THEN the API Gateway SHALL return HTTP 404 with an appropriate error message
5. WHEN a client submits invalid request data, THEN the API Gateway SHALL return HTTP 400 with validation error details

### Requirement 6

**User Story:** As a system operator, I want the API Gateway to handle errors gracefully, so that the system remains stable and provides useful feedback when issues occur.

#### Acceptance Criteria

1. WHEN the OpenAI API is unavailable or returns an error, THEN the API Gateway SHALL return HTTP 502 with an error message indicating the upstream service failure
2. WHEN an internal server error occurs, THEN the API Gateway SHALL return HTTP 500 and log the error details for debugging
3. WHEN the configured OpenAI API key is invalid or missing, THEN the API Gateway SHALL fail to start and log a clear error message
4. THE API Gateway SHALL validate all incoming request payloads and reject malformed requests before processing
5. WHEN concurrent requests cause resource contention, THEN the API Gateway SHALL handle the situation without crashing or corrupting user data

### Requirement 7

**User Story:** As a system administrator, I want the API Gateway to use a single OpenAI API key for all users, so that I can centrally manage API costs and access control.

#### Acceptance Criteria

1. THE API Gateway SHALL load the OpenAI API key from the OPENAI_API_KEY environment variable at startup
2. THE OpenAI Client SHALL use the same API key for all chat requests regardless of which artificial user initiated the request
3. WHEN making requests to OpenAI, THEN the OpenAI Client SHALL include proper authentication headers with the configured API key
4. THE API Gateway SHALL not expose the OpenAI API key in any API responses or logs
5. WHEN the OPENAI_API_KEY environment variable is not set, THEN the API Gateway SHALL refuse to start and log a clear error message

### Requirement 8

**User Story:** As a platform engineer, I want the API Gateway to be cloud-native and Kubernetes-ready, so that I can deploy it in a horizontally scalable, highly available configuration.

#### Acceptance Criteria

1. THE API Gateway SHALL expose a GET /health endpoint that returns HTTP 200 when the application is running
2. THE API Gateway SHALL expose a GET /ready endpoint that returns HTTP 200 when the application is ready to serve traffic and returns HTTP 503 when dependencies are unavailable
3. WHEN the API Gateway receives a SIGTERM signal, THEN it SHALL gracefully shutdown by finishing in-flight requests and closing database connections
4. THE API Gateway SHALL load all configuration from environment variables following the twelve-factor app methodology
5. THE API Gateway SHALL use PostgreSQL as the persistent data store to support multi-pod deployments
6. THE API Gateway SHALL use Redis for distributed caching and locking to maintain consistency across multiple pods
7. THE API Gateway SHALL emit structured JSON logs with request IDs, timestamps, and contextual information for log aggregation systems
8. THE API Gateway SHALL support running multiple replicas concurrently without data corruption or race conditions

### Requirement 9

**User Story:** As a developer, I want comprehensive test coverage at multiple levels, so that I can confidently deploy changes and catch bugs early.

#### Acceptance Criteria

1. THE test suite SHALL include unit tests that use mocked dependencies via the abstraction layer and run in-process with TestClient
2. THE test suite SHALL include integration tests that use real PostgreSQL and Redis instances running locally with TestClient
3. THE test suite SHALL include end-to-end tests that start the API Gateway as a real process on localhost and make actual HTTP requests
4. WHEN running unit tests, THEN all external dependencies SHALL be mocked using in-memory implementations
5. WHEN running integration tests, THEN the tests SHALL use real database and cache instances but mock external APIs like OpenAI
6. WHEN running end-to-end tests, THEN the tests SHALL start PostgreSQL, Redis, and the FastAPI server as separate processes and verify the complete system behavior
7. THE test suite SHALL verify admin API key authentication for administrative endpoints
8. THE test suite SHALL verify auto-creation behavior when enabled and disabled via environment variable
9. THE test suite SHALL verify per-user request serialization by sending concurrent requests from the same user with artificial delays
10. THE test suite SHALL verify concurrent requests from different users are processed in parallel without blocking
