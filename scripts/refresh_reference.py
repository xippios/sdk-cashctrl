"""Packaged reference data for CashCtrl (``/refresh-reference-data``): none yet, by design.

Tenant data is never packaged: a multi-tenant source packages no tenant data (ADR-0014).
Accounts, currencies, tax codes, fiscal periods and every other list an organisation
keeps for itself are per-organisation data, served live by the list tasks with ``org``.
The only reference data this package may ship are value sets the documentation fixes,
enumerations such as journal or order types, generated with provenance from
``docs/upstream/`` into ``reference/`` and ``enums.py`` (through one
``xippios.core.reference.render_enums`` call, then ``ruff format`` and ``ruff check --fix``),
never from an organisation's API, so the generator needs no key and no request.

No task needs such an enum yet, so this script, run without options, says so and exits
with status 1. When the first one is needed, it becomes a generator over the snapshot,
as ``.claude/commands/refresh-reference-data.md`` describes, filling ``LISTS``::

    uv run python scripts/refresh_reference.py

``--render-only`` regenerates ``enums.py`` from the packaged ``reference/*.json`` alone,
without a request and without a key: after a core release changes the renderer
(conventions §15, item 6), it changes ``enums.py`` and nothing else, committed as
formatted. With nothing packaged it renders a module without an enum::

    uv run python scripts/refresh_reference.py --render-only
"""

import argparse
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from xippios.core.reference import render_enums

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/xippios/cashctrl"
REFERENCE = PACKAGE_DIR / "reference"
ENUMS = PACKAGE_DIR / "enums.py"
GENERATOR = "scripts/refresh_reference.py"

LISTS: dict[str, tuple[str, str, str]] = {}
"""Value sets, one ``StrEnum`` each: name to (snapshot file, operation, parameter); none yet.

Keep ``params.PACKAGED_LISTS`` in step with the keys.
"""

MESSAGE = (
    "refresh_reference.py: nothing to refresh. CashCtrl's lists (accounts, currencies, "
    "tax codes, fiscal periods) are per-organisation data, served live by the list tasks "
    "and never packaged; the package ships only value sets docs/upstream/ fixes, and none "
    "is needed yet. See .claude/commands/refresh-reference-data.md."
)


def read(name: str) -> dict[str, Any]:
    """The packaged ``reference/<name>.json``: ``param``, ``fetched`` and ``values``."""
    path = REFERENCE / f"{name}.json"
    if not path.is_file():
        raise SystemExit(f"{path.name} is not packaged yet: run the generator first")
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return payload


def render(values: Mapping[str, Sequence[str]], fetched: Mapping[str, str]) -> str:
    """``enums.py`` as core renders it: one ``StrEnum`` per value set, ASCII-only.

    ``fetched`` holds each set's fetch date, so sets fetched on different days render
    together.
    """
    return render_enums(values, fetched=fetched, generator=GENERATOR)


def format_enums() -> None:
    """``ruff format`` and ``ruff check --fix`` on ``enums.py``, with this repository's config.

    Core's renderer leaves the layout to ruff (ADR-0008, amendment 2026-10-27): the
    module is committed as formatted.
    """
    config = ["--config", str(ROOT / "pyproject.toml")]
    for command in (["format"], ["check", "--fix", "--quiet"]):
        subprocess.run([sys.executable, "-m", "ruff", *command, *config, str(ENUMS)], check=True)


def render_only() -> None:
    """Regenerate ``enums.py`` from the packaged files, without a request, and format it."""
    values: dict[str, list[str]] = {}
    fetched: dict[str, str] = {}
    for name in LISTS:
        payload = read(name)
        values[name] = payload["values"]
        fetched[name] = payload["fetched"]
    ENUMS.write_text(render(values, fetched), encoding="utf-8")
    format_enums()
    print(f"{ENUMS.name}: {len(values)} enums, from the packaged files")  # noqa: T201


def main(argv: Sequence[str] | None = None) -> int:
    """With ``--render-only`` regenerate ``enums.py``; otherwise say why there is nothing to do.

    Returns:
        ``0`` after ``--render-only``; ``1`` otherwise, the stub's refusal.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="regenerate enums.py from the packaged reference/*.json, without a request or a key",
    )
    args = parser.parse_args(argv)
    if args.render_only:
        render_only()
        return 0
    print(MESSAGE, file=sys.stderr)  # noqa: T201
    return 1


if __name__ == "__main__":
    sys.exit(main())
