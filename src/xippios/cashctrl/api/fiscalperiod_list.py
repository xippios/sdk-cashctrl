"""``GET /api/v1/fiscalperiod/list.json``: every fiscal period of an organisation.

Reference: ``docs/upstream/meta.md``, "List fiscal periods" ("Returns a list of all
fiscal periods."). The operation documents no parameters.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import FiscalPeriod, ListResponse

__all__ = ["fiscalperiod_list"]


async def fiscalperiod_list(org: str) -> Answer[ListResponse[FiscalPeriod]]:
    """Call ``fiscalperiod/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    return await client_for(org).get_answer(
        "/fiscalperiod/list.json",
        parse=ListResponse[FiscalPeriod],
        endpoint="fiscalperiod/list.json",
    )
