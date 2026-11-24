"""``GET /api/v1/order/read.json``: one order by its id.

Reference: ``docs/upstream/order.md``, "Read order" ("Returns a single order by ID."),
one parameter, ``id`` (mandatory, NUMBER). An unknown id is assumed to be answered with
HTTP 200 and ``"success": false``, which ``_client.classify`` raises as
``NotFoundError``: recorded for ``account`` and ``journal`` reads
(``docs/upstream/OBSERVED.md``), not for ``order``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import OrderDetail, ReadResponse

__all__ = ["order_read"]


async def order_read(org: str, id: int) -> Answer[OrderDetail]:
    """Call ``order/read.json`` for organisation ``org`` and return the order.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the order's id (not its number ``nr``).

    Raises:
        NotFoundError: No order has this id.
    """
    answer = await client_for(org).get_answer(
        "/order/read.json",
        params={"id": id},
        parse=ReadResponse[OrderDetail],
        endpoint="order/read.json",
    )
    return Answer(answer.payload.data, answer.retrieved_at)
