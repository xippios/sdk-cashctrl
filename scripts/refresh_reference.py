"""Packaged reference data for CashCtrl (``/refresh-reference-data``): none yet, by design.

Tenant data is never packaged. Accounts, currencies, tax codes, fiscal periods and every
other list an organisation keeps for itself are per-organisation data, served live by the
list tasks with ``org``. The only reference data this package may ship are value sets the
documentation fixes, enumerations such as journal or order types, generated with
provenance from ``docs/upstream/`` into ``reference/`` and ``enums.py`` (through
``xippios.core.reference.render_str_enums``), never from an organisation's API.

No task needs such an enum yet, so this script says so and exits with status 1. When the
first one is needed, it becomes a generator over the snapshot, as
``.claude/commands/refresh-reference-data.md`` describes::

    uv run scripts/refresh_reference.py
"""

import sys

MESSAGE = (
    "refresh_reference.py: nothing to refresh. CashCtrl's lists (accounts, currencies, "
    "tax codes, fiscal periods) are per-organisation data, served live by the list tasks "
    "and never packaged; the package ships only value sets docs/upstream/ fixes, and none "
    "is needed yet. See .claude/commands/refresh-reference-data.md."
)


def main() -> int:
    """Say why there is nothing to refresh; return a non-zero exit status."""
    print(MESSAGE, file=sys.stderr)  # noqa: T201
    return 1


if __name__ == "__main__":
    sys.exit(main())
