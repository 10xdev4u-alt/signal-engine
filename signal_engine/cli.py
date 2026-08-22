import argparse
import sys

from signal_engine import __version__

IMPLEMENTED = {"status"}

SUBCOMMANDS = [
    "add-subreddit",
    "fetch",
    "analyze",
    "digest",
    "serve",
    "status",
    "report",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="signal-engine", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    for name in SUBCOMMANDS:
        sub.add_parser(name)
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "status":
        from pathlib import Path

        db = Path("data/engine.db")
        if not db.exists():
            print("no database yet — nothing collected so far")
            return 0
        print(f"database present at {db}")
        return 0

    print(f"'{args.command}' is not implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
import os
