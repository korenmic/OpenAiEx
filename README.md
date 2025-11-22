# OpenAI Chat API Gateway

Cloud-native Python-based RESTful API gateway that provides managed access to OpenAI's Chat API with built-in user management and content moderation.

## Features

- **User Management**: Admin endpoints for creating and managing users
- **Content Moderation**: Automatic detection of username mentions with blocking after 3 violations
- **Auto-Creation**: Optional automatic user creation on first chat request
- **Cloud-Native**: Horizontal scalability with PostgreSQL and Redis
- **Health Probes**: Kubernetes-ready liveness and readiness endpoints
- **Structured Logging**: JSON logging with sensitive data redaction

## Architecture

- **FastAPI**: Async-native web framework
- **PostgreSQL**: User data persistence
- **Redis**: Distributed caching and locking
- **SQLModel**: Type-safe ORM
- **Hypothesis**: Property-based testing

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- OpenAI API key

### Installation

```bash
# Clone repository
git clone <repository-url>
cd OpenAiEx

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (with defaults)
DATABASE_URL=postgresql+asyncpg://localhost:5432/gateway
REDIS_URL=redis://localhost:6379
AUTO_CREATE_USERS=true
OPENAI_MODEL=gpt-3.5-turbo
ADMIN_API_KEY=your-admin-key  # Auto-generated if not provided
LOG_LEVEL=INFO
```

### Running Locally

```bash
# Start PostgreSQL and Redis (if not running)
# On WSL/Linux:
sudo service postgresql start
sudo service redis-server start

# Run the application
python -m uvicorn app.main:app --reload

# Application will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## API Endpoints

### Public Endpoints

#### POST /chat
Process a chat request with content moderation.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "message": "Hello!"}'
```

Response:
```json
{
  "response": "Hi! How can I help you?",
  "block_count": 0,
  "violation_detected": false
}
```

#### GET /health
Liveness probe (always returns 200).

#### GET /ready
Readiness probe (checks database and Redis connectivity).

### Admin Endpoints

All admin endpoints require the `X-Admin-Key` header.

#### POST /admin/users
Create a new user.

```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-key" \
  -d '{"username": "alice"}'
```

#### GET /admin/users/{username}
Get user information.

```bash
curl http://localhost:8000/admin/users/alice \
  -H "X-Admin-Key: your-admin-key"
```

#### GET /admin/users
List all users.

```bash
curl http://localhost:8000/admin/users \
  -H "X-Admin-Key: your-admin-key"
```

## Testing

### Run Unit Tests

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=html
```

### Test Strategy

- **Unit Tests**: Fast tests with mocked dependencies (32 tests, 56% coverage)
- **Property-Based Tests**: Using Hypothesis for comprehensive input validation
- **Integration Tests**: Real PostgreSQL and Redis (not yet implemented)
- **E2E Tests**: Full running server tests (not yet implemented)

## Content Moderation Rules

1. Messages are scanned for mentions of other usernames
2. Mentions are detected using word boundaries (case-insensitive)
3. Each violation increments the user's `block_count`
4. After 3 violations, the user is blocked (`is_blocked = true`)
5. Blocked users receive 403 Forbidden on chat requests
6. Violations don't prevent the current request from being processed

## Development

### Project Structure

```
app/
├── api/           # FastAPI route handlers
├── core/          # Configuration, protocols, dependencies
├── models/        # Data models (SQLModel)
├── repositories/  # Data access layer
├── services/      # Business logic
└── tests/         # Test mocks

tests/
└── unit/          # Unit tests with mocks
```

### Adding New Features

1. Update requirements in `.kiro/specs/openai-chat-gateway/requirements.md`
2. Update design in `.kiro/specs/openai-chat-gateway/design.md`
3. Add tasks to `.kiro/specs/openai-chat-gateway/tasks.md`
4. Implement with tests
5. Run full test suite

## Deployment

### Docker

```bash
# Build image
docker build -t openai-gateway:latest .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e DATABASE_URL=postgresql+asyncpg://host:5432/db \
  -e REDIS_URL=redis://host:6379 \
  openai-gateway:latest
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `DATABASE_URL` | No | `postgresql+asyncpg://localhost:5432/gateway` | PostgreSQL connection string |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection string |
| `AUTO_CREATE_USERS` | No | `true` | Auto-create users on first chat |
| `OPENAI_MODEL` | No | `gpt-3.5-turbo` | OpenAI model to use |
| `ADMIN_API_KEY` | No | Auto-generated | Admin API key |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## License

[Your License Here]

## Contributing

[Contributing guidelines]
