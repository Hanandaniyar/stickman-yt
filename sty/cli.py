"""CLI `sty`. Setiap modul menambah subcommand lewat register(subparsers)."""
import argparse
import sys

MODULES: list[str] = []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sty", description="Pipeline video stickman")
    sub = parser.add_subparsers(dest="command")
    import importlib

    for name in MODULES:
        importlib.import_module(f"sty.{name}").register(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
