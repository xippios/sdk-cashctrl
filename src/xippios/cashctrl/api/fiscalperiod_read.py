"""``GET /api/v1/fiscalperiod/read.json``: one fiscal period by its id, or the current one.

Reference: ``docs/upstream/meta.md``, "Read fiscal period" ("Returns a single fiscal
period by ID or the current fiscal period."), one parameter, ``id`` (optional, TEXT:
"Leave empty to read the current fiscal period"). Its answer, as
``docs/upstream/OBSERVED.md`` notes, is
``{"success": true, "data": {...}}`` with the fields of a ``fiscalperiod/list.json``
entry, but ``current`` and ``isCurrent`` are ``false`` and ``lastEntryDate`` is ``null``
even for the current period, read without an id, which the list marks current and
dates. An unknown id is answered with HTTP 200 and ``"success": false`` ("This fiscal
period does not exist."), which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.api._params import present
from xippios.cashctrl.models import FiscalPeriod, ReadResponse

__all__ = ["fiscalperiod_read"]


async def fiscalperiod_read(org: str, id: int | None = None) -> Answer[FiscalPeriod]:
    """Call ``fiscalperiod/read.json`` for organisation ``org`` and return the period.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the fiscal period's id; left out, upstream reads the API user's
            current fiscal period.

    Raises:
        NotFoundError: No fiscal period has this id.
    """
    answer = await client_for(org).get_answer(
        "/fiscalperiod/read.json",
        params=present({"id": id}),
        parse=ReadResponse[FiscalPeriod],
        endpoint="fiscalperiod/read.json",
    )
    return Answer(answer.payload.data, answer.retrieved_at)
