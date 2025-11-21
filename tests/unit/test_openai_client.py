"""Property-based tests for OpenAI client."""
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import AsyncMock, patch

from app.services.openai_client import OpenAIHttpClient


# Feature: openai-chat-gateway, Property 22: Single API key for all users
@given(
    messages=st.lists(
        st.text(min_size=1, max_size=100),
        min_size=2,
        max_size=5,
    )
)
@settings(max_examples=50)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_single_api_key_for_all_users(messages: list[str]) -> None:
    """For any set of chat requests, all should use the same configured API key."""
    api_key = "test-api-key-12345"
    client = OpenAIHttpClient(api_key=api_key)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Mock response"}}]
        })
        mock_response.raise_for_status = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Send multiple requests
        for message in messages:
            await client.send_chat_request(message)

        # Verify all requests used the same API key
        assert mock_client.post.call_count == len(messages)
        for call in mock_client.post.call_args_list:
            headers = call.kwargs["headers"]
            assert headers["Authorization"] == f"Bearer {api_key}"


# Feature: openai-chat-gateway, Property 23: API key in request headers
@given(
    message=st.text(min_size=1, max_size=100),
    api_key=st.text(min_size=10, max_size=50),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_api_key_in_request_headers(message: str, api_key: str) -> None:
    """For any request to OpenAI, headers should include Authorization with Bearer token."""
    client = OpenAIHttpClient(api_key=api_key)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Mock response"}}]
        })
        mock_response.raise_for_status = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        await client.send_chat_request(message)

        # Verify Authorization header format
        call_kwargs = mock_client.post.call_args.kwargs
        headers = call_kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {api_key}"
        assert headers["Content-Type"] == "application/json"


# Feature: openai-chat-gateway, Property 24: API key not exposed
@pytest.mark.asyncio
@pytest.mark.unit
async def test_api_key_not_exposed_in_response() -> None:
    """API key should not appear in any response or error message."""
    api_key = "sk-secret-key-12345"
    client = OpenAIHttpClient(api_key=api_key)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "This is a response"}}]
        })
        mock_response.raise_for_status = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        response = await client.send_chat_request("Hello")

        # Verify API key not in response
        assert api_key not in response
        assert "sk-" not in response  # No API key prefix


@pytest.mark.asyncio
@pytest.mark.unit
async def test_api_key_not_exposed_in_error() -> None:
    """API key should not appear in error messages."""
    api_key = "sk-secret-key-12345"
    client = OpenAIHttpClient(api_key=api_key)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("HTTP 401")
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        try:
            await client.send_chat_request("Hello")
        except Exception as e:
            error_message = str(e)
            # Verify API key not in error message
            assert api_key not in error_message
