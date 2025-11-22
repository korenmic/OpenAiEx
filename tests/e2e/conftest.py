"""End-to-end test configuration with real running server."""
import os
import time
import pytest
import subprocess
import httpx
from typing import AsyncGenerator

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost:5432/gateway_e2e_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/2")  # Use DB 2 for E2E tests
os.environ.setdefault("AUTO_CREATE_USERS", "true")


@pytest.fixture(scope="session")
def ensure_services():
    """Ensure PostgreSQL and Redis are running."""
    # Try to start services if not running (WSL/Linux)
    try:
        subprocess.run(["sudo", "service", "postgresql", "start"], 
                      capture_output=True, check=False)
        subprocess.run(["sudo", "service", "redis-server", "start"], 
                      capture_output=True, check=False)
    except FileNotFoundError:
        # Not on Linux/WSL, assume services are managed externally
        pass
    
    # Give services time to start
    time.sleep(2)
    
    yield


@pytest.fixture(scope="session")
def running_server(ensure_services):
    """Start a real FastAPI server as subprocess."""
    # Start the server
    env = os.environ.copy()
    env.update({
        "DATABASE_URL": "postgresql+asyncpg://localhost:5432/gateway_e2e_test",
        "REDIS_URL": "redis://localhost:6379/2",
        "OPENAI_API_KEY": "test-openai-key",
        "ADMIN_API_KEY": "test-admin-key",
        "AUTO_CREATE_USERS": "true",
    })
    
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get("http://127.0.0.1:8001/health", timeout=1.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.5)
    else:
        process.terminate()
        pytest.fail("Server failed to start within timeout")
    
    yield "http://127.0.0.1:8001"
    
    # Cleanup: Stop the server
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
async def e2e_client(running_server) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for E2E tests."""
    async with httpx.AsyncClient(base_url=running_server, timeout=30.0) as client:
        yield client


@pytest.fixture(autouse=True)
async def cleanup_test_data(running_server):
    """Clean up test data before each test."""
    # This runs before each test
    yield
    
    # Cleanup after test
    # Note: In a real scenario, you'd want to clean the database
    # For now, we rely on test isolation through unique usernames
