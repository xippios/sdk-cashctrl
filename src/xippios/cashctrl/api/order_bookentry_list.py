"""``GET /api/v1/order/bookentry/list.json``: the book entries of one order.

Reference: ``docs/upstream/order.md``, Book entry, "List book entries" ("Returns a list
of book entries for an order."), one parameter, ``id`` (mandatory, NUMBER), the order's
id. It documents no ``start`` or ``limit``: one answer carries the order's entries.
Its answer for a seeded purchase order in a status that books, as
``docs/upstream/OBSERVED.md`` notes: ``{"total":
1, "data": [...]}``, the one entry its items booked (``type`` ``GENERATED``).
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import ListResponse, OrderBookEntry

__all__ = ["order_bookentry_list"]


async def order_bookentry_list(org: str, id: int) -> Answer[ListResponse[OrderBookEntry]]:
    """Call ``order/bookentry/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the order's id (not its number ``nr``), e.g. ``5``.
    """
    return await client_for(org).get_answer(
        "/order/bookentry/list.json",
        params={"id": id},
        parse=ListResponse[OrderBookEntry],
        endpoint="order/bookentry/list.json",
    )
