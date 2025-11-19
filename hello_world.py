#!/usr/bin/env python3

import json
from functools import lru_cache
from utils import slice_dict
from openai import OpenAI


PRICE_FILE = 'chat_models.json'
PRICE_KEY = 'price_per_1k_input'


@lru_cache()
def load_price_map() -> dict[str, float]:
    """
    Based on https://openai.com/api/pricing/
    Load a mapping of model_id -> price_per_1k_input from chat_models.json
    which contains only the chat type models for filtering
    """
    with open(PRICE_FILE, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    price_map: dict[str, float] = {key: value.get(PRICE_KEY) for (key, value) in raw.items()}

    if not price_map:
        raise RuntimeError(f'No usable prices found in {path}')

    return price_map


def pick_cheapest_supported_model(client: OpenAI, price_map: dict[str, float]) -> tuple[str, float]:
    """
    Intersect the models supported by this API key with the models
    listed in chat_models.json, then pick the cheapest by input price.
    """
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


def append_history(history, user_input, response) -> None:
    ai_output = response.output[0].content[0].text
    history.append({'user': user_input, 'ai': ai_output})


def main() -> None:
    # Assumes OPENAI_API_KEY is set in the environment
    client = OpenAI()

    price_map = load_price_map()
    model_id, price = pick_cheapest_supported_model(client, price_map)

    print(f"Using model: {model_id} (input: ${price} per 1K tokens)")

    history = []
    user_input = 'Hello World'
    print(f'Sending {user_input=}')
    response = client.responses.create(
        model=model_id,
        input=user_input,
    )
    append_history(history, user_input, response)

    print("Model output:")
    print(response.output_text)

    user_input = 'Please tell me a joke'
    print(f'Sending {user_input=}')
    response = client.responses.create(
        model=model_id,
        input=str(history) + user_input,
    )
    append_history(history, user_input, response)
    print("Model output:")
    print(response.output_text)

    user_input = 'Why was the joke funny?'
    print(f'Sending {user_input=}')
    response = client.responses.create(
        model=model_id,
        input=str(history) + user_input,
    )
    #append_history(history, user_input, response)
    print("Model output:")
    print(response.output_text)


if __name__ == "__main__":
    main()
