"""``GET /api/v1/order/bookentry/list.json``: the book entries of one order.

Reference: ``docs/upstream/order.md``, Book entry, "List book entries" ("Returns a list
of book entries for an order."), one parameter, ``id`` (mandatory, NUMBER), the order's
id. It documents no ``start`` or ``limit``: one answer carries the order's entries.
Observed on 2026-10-27 for a seeded purchase order in a status that books: ``{"total":
1, "data": [...]}``, the one entry its items booked (``type`` ``GENERATED``).
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import ListResponse, OrderBookEntry

__all__ = ["order_bookentry_list"]


async def order_bookentry_list(org: str, id: int) -> ListResponse[OrderBookEntry]:
    """Call ``order/bookentry/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the order's id (not its number ``nr``), e.g. ``5``.
    """
    raw = await client_for(org).get_json("/order/bookentry/list.json", params={"id": id})
    return parse(
        ListResponse[OrderBookEntry], raw, source=SOURCE, endpoint="order/bookentry/list.json"
    )
