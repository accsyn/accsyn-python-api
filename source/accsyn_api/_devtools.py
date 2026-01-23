from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Sequence


def run_pytest(argv: Optional[Sequence[str]] = None) -> int:
    """
    Run pytest from the repository root, regardless of current working directory.

    This makes `poetry run test` work even if invoked from e.g. `doc/`.
    """
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    args = list(sys.argv[1:] if argv is None else argv)
    # Ensure we always pick up the project's pytest settings.
    if "-c" not in args and "--config-file" not in args:
        args = ["-c", str(repo_root / "pyproject.toml"), *args]

    import pytest

    return pytest.main(args)


def test() -> None:
    """Poetry script entrypoint: `poetry run test [pytest-args...]`."""
    raise SystemExit(run_pytest())

