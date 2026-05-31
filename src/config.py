from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    vault_dir: Path | None
    paper_subdir: str | None
    recursive: bool
    debug: bool

    @property
    def paper_dir(self) -> Path | None:
        if self.vault_dir is None:
            return None
        if self.paper_subdir:
            return self.vault_dir / self.paper_subdir
        return self.vault_dir


def parse_args(argv: list[str] | None = None) -> AppConfig:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--vault_dir")
    parser.add_argument("--paper_subdir")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args, _ = parser.parse_known_args(argv)

    return AppConfig(
        vault_dir=Path(args.vault_dir).expanduser() if args.vault_dir else None,
        paper_subdir=args.paper_subdir,
        recursive=args.recursive,
        debug=args.debug,
    )
