#!/usr/bin/env python3

import json
from functools import lru_cache, partial
from utils.dict_utils import slice_dict
from openai import OpenAI

from utils.model_negotiator import pick_cheapest_supported_model


DEFAUT_CONTEXT_WINDOW_MAX_SIZE = 2


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

    model_id, price = pick_cheapest_supported_model(client)

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
