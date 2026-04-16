"""
setup_env.py — Generate a .env snapshot for onboarding new developers.

Reads the current environment and writes all variables whose names begin with
ANTHROPIC_, OPENAI_, LITELLM_, or TWILL_ to env_snapshot.txt in the format:

    VARNAME=<actual_value>

The resulting file shows both the expected variable names *and* their current
values so developers can verify their own setup against a known-good baseline.

Usage:
    python setup_env.py [--output PATH]

Options:
    --output PATH   Destination file (default: env_snapshot.txt)
"""

import os
import argparse

PREFIXES = ("ANTHROPIC_", "OPENAI_", "LITELLM_", "TWILL_")
DEFAULT_OUTPUT = "env_snapshot.txt"


def collect_vars(prefixes: tuple[str, ...]) -> dict[str, str]:
    """Return env vars whose names start with any of *prefixes*, sorted by name."""
    return {
        key: value
        for key, value in sorted(os.environ.items())
        if any(key.startswith(p) for p in prefixes)
    }


def write_snapshot(vars_: dict[str, str], output_path: str) -> None:
    """Write *vars_* to *output_path* in KEY=value format."""
    lines = [f"{key}={value}" for key, value in vars_.items()]
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Output file path (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    vars_ = collect_vars(PREFIXES)

    if not vars_:
        print("No matching environment variables found.")
        return

    write_snapshot(vars_, args.output)

    print(f"Wrote {len(vars_)} variable(s) to {args.output}:")
    for key in vars_:
        print(f"  {key}")


if __name__ == "__main__":
    main()
