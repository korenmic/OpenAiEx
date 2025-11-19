#!/usr/bin/env python3

import json
from functools import lru_cache, partial
from utils import slice_dict
from openai import OpenAI


PRICE_FILE = 'chat_models.json'
PRICE_KEY = 'price_per_1k_input'
DEFAUT_CONTEXT_WINDOW_MAX_SIZE = 2


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


def append_history(history, user_input, response, max_size=DEFAUT_CONTEXT_WINDOW_MAX_SIZE) -> None:
    ai_output = response.output[0].content[0].text
    history.append({'user': user_input, 'ai': ai_output})
    amount_of_pairs_to_be_cut_off = max(0, len(history) - max_size)
    for _ in range(amount_of_pairs_to_be_cut_off):
        history.pop(0)


def send_next_input(client, model_id, history, next_input) -> None:
    print(f'Sending {next_input=}')
    user_input = ((str(history) + ' ') if history else '') + next_input
    response = client.responses.create(
        model=model_id,
        input=user_input,
    )
    append_history(history, next_input, response)
    print("Model output:")
    print(response.output_text)
    print('\n')


def main() -> None:
    # Assumes OPENAI_API_KEY is set in the environment
    client = OpenAI()

    price_map = load_price_map()
    model_id, price = pick_cheapest_supported_model(client, price_map)

    print(f"Using model: {model_id} (input: ${price} per 1K tokens)")

    history = []
    sender = partial(send_next_input, client, model_id, history)
    sender('Hello World')                         # 1
    sender('Please tell me a joke')               # 2
    sender('Why was the joke funny?')             # 3 (1 is lost)
    sender('What is the weather like')            # 4 (2 is lost)
    sender('What is the time?')                   # 5 (3 is lost)
    sender('What joke did you tell me before?')   # 6 (4 is lost)

if __name__ == "__main__":
    main()
