"""``GET /api/v1/fiscalperiod/list.json``: every fiscal period of an organisation.

Reference: ``docs/upstream/meta.md``, "List fiscal periods" ("Returns a list of all
fiscal periods."). The operation documents no parameters.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import FiscalPeriod, ListResponse

__all__ = ["fiscalperiod_list"]


async def fiscalperiod_list(org: str) -> ListResponse[FiscalPeriod]:
    """Call ``fiscalperiod/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/fiscalperiod/list.json")
    return parse(ListResponse[FiscalPeriod], raw, source=SOURCE, endpoint="fiscalperiod/list.json")
