"""``GET /api/v1/order/bookentry/read.json``: one book entry of an order by its id.

Reference: ``docs/upstream/order.md``, Book entry, "Read book entry" ("Returns a single
book entry by ID."), one parameter, ``id`` (mandatory, NUMBER). Observed on 2026-11-17
for the seeded purchase order 5's entry: ``{"success": true, "data": {...}}``, the entry
as ``order/bookentry/list.json`` lists it, ``orderId`` naming its order and ``type``
``GENERATED`` for an entry booked from the order's items. The book entry writes read
it first (``tasks_write``); no read tool serves it.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import OrderBookEntry, ReadResponse

__all__ = ["order_bookentry_read"]


async def order_bookentry_read(org: str, id: int) -> OrderBookEntry:
    """Call ``order/bookentry/read.json`` for organisation ``org`` and return the entry.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the book entry's id, e.g. ``5``.

    Raises:
        NotFoundError: No book entry has this id.
    """
    raw = await client_for(org).get_json("/order/bookentry/read.json", params={"id": id})
    response = parse(
        ReadResponse[OrderBookEntry], raw, source=SOURCE, endpoint="order/bookentry/read.json"
    )
    return response.data
