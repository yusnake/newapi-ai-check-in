#!/usr/bin/env python3
"""Simple script to test the httpbin.org GET endpoint and print response headers."""

import sys

import requests


def main():
    url = "https://httpbin.org/get"
    print(f"Making GET request to {url} ...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch {url}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nStatus code: {response.status_code}\n")
    print("Response headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")

    print(f"\nResponse body (JSON):\n{response.json()}")


if __name__ == "__main__":
    main()
