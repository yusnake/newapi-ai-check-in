#!/usr/bin/env python3
"""API test script for Anthropic endpoints."""

import json
import os
import sys

import httpx

BASE_URL = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("WARNING: ANTHROPIC_API_KEY is not set", file=sys.stderr)
    return key


def format_curl(method: str, url: str, headers: dict, body: dict | None = None) -> str:
    """Return a curl command string, replacing the API key value with its env var reference."""
    parts = ["curl", "-s", "-X", method]
    for k, v in headers.items():
        # Show env-var placeholder instead of the literal key value
        display_v = "$ANTHROPIC_API_KEY" if k == "x-api-key" else v
        parts += ["-H", f'"{k}: {display_v}"']
    if body is not None:
        parts += ["-d", f"'{json.dumps(body)}'"]
    parts.append(f'"{url}"')
    return " ".join(parts)


def test_models(api_key: str) -> None:
    print("=" * 60)
    print("TEST: GET /v1/models")
    print("=" * 60)

    url = f"{BASE_URL}/v1/models"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }

    print("\nCurl equivalent:")
    print(format_curl("GET", url, headers))
    print()

    resp = httpx.get(url, headers=headers)

    print(f"Status: {resp.status_code}")
    print("Response body:")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    print()


def test_messages(api_key: str) -> None:
    print("=" * 60)
    print("TEST: POST /v1/messages")
    print("=" * 60)

    url = f"{BASE_URL}/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 5,
        "messages": [{"role": "user", "content": "hi"}],
    }

    print("\nCurl equivalent:")
    print(format_curl("POST", url, headers, body))
    print()

    resp = httpx.post(url, headers=headers, json=body)

    print(f"Status: {resp.status_code}")
    print("Response body:")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    print()


def main() -> None:
    api_key = get_api_key()
    test_models(api_key)
    test_messages(api_key)


if __name__ == "__main__":
    main()
