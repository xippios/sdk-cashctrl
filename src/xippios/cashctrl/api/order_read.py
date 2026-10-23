"""``GET /api/v1/order/read.json``: one order by its id.

Reference: ``docs/upstream/order.md``, "Read order" ("Returns a single order by ID."),
one parameter, ``id`` (mandatory, NUMBER). An unknown id is answered with HTTP 200 and
``"success": false``, which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import OrderDetail, ReadResponse

__all__ = ["order_read"]


async def order_read(org: str, id: int) -> OrderDetail:
    """Call ``order/read.json`` for organisation ``org`` and return the order.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the order's id (not its number ``nr``).

    Raises:
        NotFoundError: No order has this id.
    """
    raw = await client_for(org).get_json("/order/read.json", params={"id": id})
    response = parse(ReadResponse[OrderDetail], raw, source=SOURCE, endpoint="order/read.json")
    return response.data
