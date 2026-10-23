"""Query parameters of CashCtrl's list operations, encoded once.

Upstream reads booleans as ``true``/``false`` ("Possible values: true, false" in every
table of ``docs/upstream/``) and applies its own default to a parameter that is not
sent.
"""

from collections.abc import Mapping

__all__ = ["flag", "present"]


def flag(value: bool | None) -> str | None:
    """``True`` → ``"true"``, ``False`` → ``"false"``, ``None`` stays ``None`` (not sent)."""
    return None if value is None else str(value).lower()


def present(named: Mapping[str, str | int | None]) -> dict[str, str | int]:
    """The parameters of ``named`` that are not ``None``, in their order: what is sent."""
    return {name: value for name, value in named.items() if value is not None}
