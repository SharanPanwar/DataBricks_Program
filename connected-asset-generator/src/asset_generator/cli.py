"""CLI entrypoint — expanded in Step 9."""

from __future__ import annotations

import argparse
import sys

from asset_generator import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asset-generator",
        description="Synthetic connected-asset operational data source.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Apply schema and seed master data (Step 4+).")
    init_parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="Skip DDL; only seed data.",
    )

    sub.add_parser(
        "generate-history",
        help="Backfill historical telemetry/events/maintenance (Step 9+).",
    )
    sub.add_parser(
        "generate-daily",
        help="Generate one day of incremental data (Step 9+).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        print("init: schema + master data seeding will be implemented in Steps 3–4.")
        return 0
    if args.command in ("generate-history", "generate-daily"):
        print(f"{args.command}: generation engine will be implemented in Step 9.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
