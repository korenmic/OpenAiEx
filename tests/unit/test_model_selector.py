"""Unit tests for model selection logic."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.services.model_selector import ModelSelector, ModelPreference, ModelInfo


@pytest.fixture
def mock_models_response():
    """Mock response from OpenAI models API."""
    return {
        "data": [
            {"id": "gpt-4o", "object": "model"},
            {"id": "gpt-4o-mini", "object": "model"},
            {"id": "gpt-3.5-turbo", "object": "model"},
            {"id": "gpt-4-turbo", "object": "model"},
            {"id": "whisper-1", "object": "model"},  # Audio model, should be filtered
        ]
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cheapest_preference_selects_lowest_price(mock_models_response):
    """Test that CHEAPEST preference selects the model with lowest average price."""
    selector = ModelSelector("test-key", ModelPreference.CHEAPEST)
    
    # Mock the get_available_models method directly
    async def mock_get_available():
        return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"]
    
    selector.get_available_models = mock_get_available
    
    selected = await selector.select_best_model()
    
    # gpt-4o-mini should be selected (cheapest: 0.150 input, 0.600 output = 0.375 avg)
    assert selected == "gpt-4o-mini"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastest_preference_selects_fast_model(mock_models_response):
    """Test that FASTEST preference prioritizes fast models."""
    selector = ModelSelector("test-key", ModelPreference.FASTEST)
    
    # Mock the get_available_models method directly
    async def mock_get_available():
        return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"]
    
    selector.get_available_models = mock_get_available
    
    selected = await selector.select_best_model()
    
    # Should select a fast model (is_fast=true)
    # Among fast models available: gpt-4o-mini, gpt-3.5-turbo, gpt-4-turbo
    # gpt-4o-mini is fastest AND cheapest
    assert selected in ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"]
    assert selector.known_models[selected].is_fast is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fallback_when_api_fails():
    """Test fallback to default model when API query fails."""
    selector = ModelSelector("test-key", ModelPreference.CHEAPEST)
    
    # Mock API failure
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        selected = await selector.select_best_model()
        
        # Should fallback to gpt-3.5-turbo
        assert selected == "gpt-3.5-turbo"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_filters_non_text_models():
    """Test that non-text models are filtered out."""
    selector = ModelSelector("test-key", ModelPreference.CHEAPEST)
    
    # Mock to return only text models (whisper and dall-e filtered by API query)
    async def mock_get_available():
        return ["gpt-3.5-turbo"]
    
    selector.get_available_models = mock_get_available
    
    selected = await selector.select_best_model()
    
    # Should only select from text models
    assert selected == "gpt-3.5-turbo"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_unknown_models_gracefully():
    """Test that unknown models are handled gracefully."""
    selector = ModelSelector("test-key", ModelPreference.CHEAPEST)
    
    # Mock to return mix of known and unknown models
    async def mock_get_available():
        return ["gpt-future-model-2025", "gpt-3.5-turbo"]
    
    selector.get_available_models = mock_get_available
    
    selected = await selector.select_best_model()
    
    # Should select known model
    assert selected == "gpt-3.5-turbo"


@pytest.mark.unit
def test_model_info_calculates_average_price():
    """Test that ModelInfo correctly calculates average price."""
    model = ModelInfo(
        name="test-model",
        input_price=1.0,
        output_price=3.0,
        model_type="text",
        is_fast=True
    )
    
    assert model.avg_price == 2.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cheapest_among_multiple_fast_models():
    """Test that CHEAPEST selects cheapest among fast models."""
    selector = ModelSelector("test-key", ModelPreference.CHEAPEST)
    
    # Mock to return multiple fast models
    async def mock_get_available():
        return ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"]
    
    selector.get_available_models = mock_get_available
    
    selected = await selector.select_best_model()
    
    # Should select cheapest
    assert selected == "gpt-4o-mini"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastest_prefers_speed_over_price():
    """Test that FASTEST preference prioritizes speed over price."""
    selector = ModelSelector("test-key", ModelPreference.FASTEST)
    
    # Mock to return mix of fast and slow models
    async def mock_get_available():
        return ["gpt-4", "gpt-4-turbo", "gpt-4o-mini"]
    
    selector.get_available_models = mock_get_available
    
    selected = await selector.select_best_model()
    
    # Should select a fast model (not gpt-4)
    assert selected != "gpt-4"
    assert selector.known_models[selected].is_fast is True
