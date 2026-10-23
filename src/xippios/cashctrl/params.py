"""Packaged value sets for CashCtrl (conventions §3): none yet.

Tenant data is never packaged: accounts, currencies, tax codes, fiscal periods and every
other list an organisation keeps for itself are per-organisation data, served live by the
list tasks with ``org``. The only lists this package may ship are value sets that
``docs/upstream/`` fixes (enumerations such as journal or order types), generated from the
snapshot with provenance into ``reference/`` and the matching ``StrEnum`` classes in
``enums.py`` by ``scripts/refresh_reference.py``, never by hand. ``reference/README.md``
carries the provenance of every file.
"""

from datetime import date

from xippios.core import UpstreamModel, load_json

__all__ = ["PACKAGED_LISTS", "PackagedValues", "packaged_values"]

PACKAGE = "xippios.cashctrl"

PACKAGED_LISTS: tuple[str, ...] = ()
"""Names of the value sets that ship inside the package; keep in step with the script."""


class PackagedValues(UpstreamModel):
    """One packaged value set: ``reference/<name>.json``.

    Attributes:
        param: The upstream parameter the values belong to, as ``docs/upstream/`` names it.
        fetched: Day the documentation snapshot the values come from was fetched.
        values: The values, as the documentation lists them.
    """

    param: str
    fetched: date
    values: list[str]


def packaged_values(name: str) -> PackagedValues | None:
    """The packaged value set ``name``, or ``None`` when it is not packaged."""
    if name not in PACKAGED_LISTS:
        return None
    return PackagedValues.model_validate(load_json(PACKAGE, f"{name}.json"))
