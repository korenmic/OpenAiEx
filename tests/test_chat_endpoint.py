import json
import sys

import requests


def main() -> None:
    # Allow overriding the message from CLI, default to a simple test string
    message = "Hello from the client"
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])

    url = "http://localhost:8000/chat"
    payload = {"message": message}

    print(f"POST {url} with:", json.dumps(payload))

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    print("\n=== Response ===")
    print("Model:", data.get("model"))
    print("Reply:", data.get("reply"))


if __name__ == "__main__":
    main()
