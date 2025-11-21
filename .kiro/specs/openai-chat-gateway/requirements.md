# Requirements Document

## Introduction

This document specifies the requirements for an OpenAI Chat API Gateway - a RESTful API server that acts as a proxy to OpenAI's Chat API with built-in user management and content moderation capabilities. The system manages artificial users (not actual OpenAI accounts), handles asynchronous requests to a single OpenAI API key, and enforces content moderation rules to prevent users from mentioning other users in their chat requests.

## Glossary

- **API Gateway**: The RESTful API server system being developed
- **Artificial User**: A user entity managed by the API Gateway, not an actual OpenAI account
- **OpenAI Client**: The component that communicates with OpenAI's API using a single API key
- **Content Moderator**: The service component that detects and enforces user mention violations
- **Block Count**: An integer counter tracking how many times a user has violated the mention policy
- **Blocked User**: A user whose block count has reached or exceeded 3, preventing further chat requests
- **User Mention**: The occurrence of one user's username appearing in another user's chat request content
- **Chat Request**: An HTTP request to send a message to OpenAI's Chat API on behalf of a user

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to manage artificial users within the API Gateway, so that I can control access to the OpenAI Chat API without requiring actual OpenAI accounts for each user.

#### Acceptance Criteria

1. WHEN a client requests to create a new user with a unique username, THEN the API Gateway SHALL create an artificial user with a block count initialized to zero
2. WHEN a client requests user information by username, THEN the API Gateway SHALL return the user's current block count and blocked status
3. WHEN a client requests a list of all users, THEN the API Gateway SHALL return all artificial users with their usernames, block counts, and blocked status
4. THE API Gateway SHALL persist user data so that user information remains available across server restarts
5. WHEN a client attempts to create a user with a duplicate username, THEN the API Gateway SHALL reject the request and return an error response

### Requirement 2

**User Story:** As a user, I want to send chat requests to OpenAI through the API Gateway, so that I can interact with OpenAI's language models without managing my own API key.

#### Acceptance Criteria

1. WHEN a non-blocked user submits a chat request with a message, THEN the API Gateway SHALL forward the request to OpenAI's Chat API using the configured API key
2. WHEN the OpenAI Client receives a response from OpenAI, THEN the API Gateway SHALL return the response content to the requesting user
3. WHEN a blocked user attempts to submit a chat request, THEN the API Gateway SHALL reject the request and return an error indicating the user is blocked
4. THE API Gateway SHALL handle chat requests asynchronously to support concurrent users without blocking
5. WHEN the OpenAI API returns an error, THEN the API Gateway SHALL propagate the error information to the requesting user

### Requirement 3

**User Story:** As a system administrator, I want the Content Moderator to detect when users mention other users in their chat requests, so that I can enforce community guidelines and prevent harassment.

#### Acceptance Criteria

1. WHEN a user submits a chat request, THEN the Content Moderator SHALL scan the message content for mentions of other existing usernames
2. WHEN the Content Moderator detects one or more user mentions in a chat request, THEN the API Gateway SHALL increment the requesting user's block count by one
3. WHEN a user mention is detected, THEN the API Gateway SHALL process the chat request normally after incrementing the block count
4. THE Content Moderator SHALL perform case-insensitive username matching when detecting mentions
5. THE Content Moderator SHALL only detect exact username matches, not partial or substring matches

### Requirement 4

**User Story:** As a system administrator, I want users to be automatically blocked after exceeding the violation threshold, so that repeat offenders cannot continue to violate community guidelines.

#### Acceptance Criteria

1. WHEN a user's block count reaches three, THEN the API Gateway SHALL mark the user as blocked
2. WHEN a user is marked as blocked, THEN the API Gateway SHALL reject all subsequent chat requests from that user
3. WHEN a blocked user attempts a chat request, THEN the API Gateway SHALL return an error response indicating the user is blocked and cannot make further requests
4. THE API Gateway SHALL persist block count updates immediately after each violation
5. WHEN a user's block count is incremented to three during a chat request, THEN the API Gateway SHALL complete the current request before blocking future requests

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

1. THE API Gateway SHALL load the OpenAI API key from environment variables or configuration at startup
2. THE OpenAI Client SHALL use the same API key for all chat requests regardless of which artificial user initiated the request
3. WHEN making requests to OpenAI, THEN the OpenAI Client SHALL include proper authentication headers with the configured API key
4. THE API Gateway SHALL not expose the OpenAI API key in any API responses or logs
5. WHEN the API key is not configured, THEN the API Gateway SHALL refuse to start and provide a clear error message
