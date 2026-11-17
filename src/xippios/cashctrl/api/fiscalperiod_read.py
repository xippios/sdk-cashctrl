"""``GET /api/v1/fiscalperiod/read.json``: one fiscal period by its id, or the current one.

Reference: ``docs/upstream/meta.md``, "Read fiscal period" ("Returns a single fiscal
period by ID or the current fiscal period."), one parameter, ``id`` (optional, TEXT:
"Leave empty to read the current fiscal period"). Observed on 2026-11-17: the answer is
``{"success": true, "data": {...}}`` with the fields of a ``fiscalperiod/list.json``
entry, but ``current`` and ``isCurrent`` are ``false`` and ``lastEntryDate`` is ``null``
even for the current period, read without an id, which the list marks current and
dates. An unknown id is answered with HTTP 200 and ``"success": false`` ("This fiscal
period does not exist."), which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._params import present
from xippios.cashctrl.models import FiscalPeriod, ReadResponse

__all__ = ["fiscalperiod_read"]


async def fiscalperiod_read(org: str, id: int | None = None) -> FiscalPeriod:
    """Call ``fiscalperiod/read.json`` for organisation ``org`` and return the period.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the fiscal period's id; left out, upstream reads the API user's
            current fiscal period.

    Raises:
        NotFoundError: No fiscal period has this id.
    """
    raw = await client_for(org).get_json("/fiscalperiod/read.json", params=present({"id": id}))
    response = parse(
        ReadResponse[FiscalPeriod], raw, source=SOURCE, endpoint="fiscalperiod/read.json"
    )
    return response.data
