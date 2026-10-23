"""``GET /api/v1/currency/list.json``: every currency of an organisation.

Reference: ``docs/upstream/common.md``, "List currencies" ("Returns a list of all
currencies."). The operation documents no parameters.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import Currency, ListResponse

__all__ = ["currency_list"]


async def currency_list(org: str) -> ListResponse[Currency]:
    """Call ``currency/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/currency/list.json")
    return parse(ListResponse[Currency], raw, source=SOURCE, endpoint="currency/list.json")
