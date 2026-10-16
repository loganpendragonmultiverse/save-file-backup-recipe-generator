from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a reviewable game-save backup recipe.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--shell", choices=("powershell", "bash"), default="powershell")
    parser.add_argument("--mode", choices=("copy", "archive"), default="copy")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--verify", action="store_true", help="Verify copy file count and SHA-256 before success"
    )
    args = parser.parse_args(argv)
    try:
        recipe = generate(args.source, args.destination, args.shell, args.mode, args.verify)
        if args.output:
            if args.output.exists():
                raise ValueError(f"output already exists: {args.output}")
            args.output.write_text(recipe, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(recipe)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
