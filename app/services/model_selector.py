"""OpenAI model selection based on availability and preferences."""
import json
import httpx
from pathlib import Path
from enum import Enum
from typing import Optional


class ModelPreference(str, Enum):
    """Model selection preference."""
    FASTEST = "FASTEST"
    CHEAPEST = "CHEAPEST"


class ModelInfo:
    """Information about an OpenAI model."""
    
    def __init__(self, name: str, input_price: float, output_price: float, 
                 model_type: str, is_fast: bool):
        self.name = name
        self.input_price = input_price
        self.output_price = output_price
        self.model_type = model_type
        self.is_fast = is_fast
        # Average price for sorting
        self.avg_price = (input_price + output_price) / 2


class ModelSelector:
    """Select the best OpenAI model based on availability and preferences."""
    
    def __init__(self, api_key: str, preference: ModelPreference = ModelPreference.CHEAPEST):
        self.api_key = api_key
        self.preference = preference
        self.known_models = self._load_known_models()
    
    def _load_known_models(self) -> dict[str, ModelInfo]:
        """Load known models from JSON file."""
        json_path = Path(__file__).parent.parent / "data" / "openai_models.json"
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        models = {}
        for name, info in data["models"].items():
            models[name] = ModelInfo(
                name=name,
                input_price=info["input_price_per_1m"],
                output_price=info["output_price_per_1m"],
                model_type=info["model_type"],
                is_fast=info["is_fast"]
            )
        
        return models
    
    async def get_available_models(self) -> list[str]:
        """Query OpenAI API for available models."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract model IDs that are chat models
                available = []
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    # Filter for chat/text models
                    if any(prefix in model_id for prefix in ["gpt-", "o1-", "o3-", "chatgpt-"]):
                        available.append(model_id)
                
                return available
            except Exception as e:
                # If we can't query, return empty list (will use default)
                print(f"Warning: Could not query available models: {e}")
                return []
    
    async def select_best_model(self) -> str:
        """Select the best model based on availability and preference."""
        # Get available models from API
        available_models = await self.get_available_models()
        
        if not available_models:
            # Fallback to default if API query fails
            return "gpt-3.5-turbo"
        
        # Intersect with known models
        available_known = [
            self.known_models[name] 
            for name in available_models 
            if name in self.known_models
        ]
        
        if not available_known:
            # No known models available, use first available
            return available_models[0]
        
        # Filter for text models only
        text_models = [m for m in available_known if m.model_type == "text"]
        
        if not text_models:
            # No text models, use first available
            return available_known[0].name
        
        # Sort based on preference
        if self.preference == ModelPreference.FASTEST:
            # Sort by speed (fast first), then by price (cheap first)
            sorted_models = sorted(
                text_models,
                key=lambda m: (not m.is_fast, m.avg_price)
            )
        else:  # CHEAPEST
            # Sort by price (cheap first), then by speed (fast first)
            sorted_models = sorted(
                text_models,
                key=lambda m: (m.avg_price, not m.is_fast)
            )
        
        return sorted_models[0].name
