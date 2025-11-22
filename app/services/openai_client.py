"""OpenAI API client implementation."""
import httpx


class OpenAIServiceError(Exception):
    """Exception raised when OpenAI API fails."""

    pass


class OpenAIHttpClient:
    """OpenAI HTTP client implementation."""

    def __init__(self, api_key: str, model: str):
        """Initialize OpenAI client."""
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def send_chat_request(self, message: str) -> str:
        """Send chat request to OpenAI and return response.
        
        Uses the Responses API for future-proof implementation.
        API Documentation: https://platform.openai.com/docs/api-reference/chat/create
        """
        async with httpx.AsyncClient() as client:
            try:
                # Using responses.create endpoint (future-proof)
                # https://platform.openai.com/docs/api-reference/chat/create
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": message}]
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                raise OpenAIServiceError(
                    f"OpenAI API error: {e.response.status_code}"
                ) from e
            except httpx.RequestError as e:
                raise OpenAIServiceError(f"OpenAI API request failed: {str(e)}") from e
