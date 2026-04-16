#!/usr/bin/env python3
"""Script to check which ports are listening on localhost using `ss -tlnp`."""

import subprocess
import sys


def main():
    print("Checking listening ports on localhost ...\n")
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print("Error: 'ss' command not found. Install iproute2.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running ss command: {e}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout
    print(output)

    lines = output.strip().splitlines()
    if len(lines) <= 1:
        print("No listening TCP ports found.")
        return

    print("Summary of listening ports:")
    for line in lines[1:]:
        parts = line.split()
        if len(parts) <= 3:
            continue
        local_addr = parts[3]
        process = parts[5] if len(parts) > 5 else "n/a"
        print(f"  {local_addr}  {process}")


if __name__ == "__main__":
    main()
