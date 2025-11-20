import json
from functools import lru_cache
from typing import Optional

from openai import OpenAI

from utils.dict_utils import slice_dict


PRICE_FILE = 'chat_models.json'
PRICE_KEY = 'price_per_1k_input'


@lru_cache()
def load_price_map() -> dict[str, float]:
    """
    Based on https://openai.com/api/pricing/
    Load a mapping of model_id -> price_per_1k_input from chat_models.json
    which contains only the chat type models for filtering
    """
    with open(f'./utils/{PRICE_FILE}', 'r', encoding='utf-8') as f:
        raw = json.load(f)

    price_map: dict[str, float] = {
        key: value.get(PRICE_KEY) for (key, value) in raw.items() if value.get(PRICE_KEY) is not None}

    if not price_map:
        raise RuntimeError(f'No usable prices found in {PRICE_FILE}')

    return price_map


def pick_cheapest_supported_model(client: OpenAI, price_map: Optional[dict[str, float]] = None) -> tuple[str, float]:
    """
    Intersect the models supported by this API key with the models
    listed in chat_models.json, then pick the cheapest by input price.
    """
    if price_map is None:
        price_map = load_price_map()
    models = client.models.list()

    # Set of model IDs your key is allowed to use
    supported_ids = {m.id for m in models.data}

    # Only keep models that are both priced AND supported
    candidates = slice_dict(price_map, supported_ids)

    if not candidates:
        raise RuntimeError(
            "No overlap between chat_models.json and models.list(). "
            "Either your key doesn't have access to any of those chat models, "
            "or the IDs in chat_models.json don't match the live model IDs."
        )

    # Pick the model with the lowest input price
    cheapest_id, cheapest_price = min(candidates.items(), key=lambda x: x[1])
    return cheapest_id, cheapest_price
