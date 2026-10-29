"""``GET /api/v1/order/document/read.json``: the document of one order, by the order's id.

Reference: ``docs/upstream/order.md``, "Read document" ("Returns a single document by
order ID."), one parameter, ``id`` (mandatory, NUMBER, "The ID of the order."). The
document is the order's sender and recipient, layout and language, not the order itself
("Here you only manage the sender / recipient of the document, which layout to use, and
the document language"). An unknown id is assumed to be refused as ``order/read.json``
refuses one, which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import OrderDocument, ReadResponse

__all__ = ["order_document_read"]


async def order_document_read(org: str, id: int) -> OrderDocument:
    """Call ``order/document/read.json`` for organisation ``org`` and return the document.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the order's id (not its number ``nr``).

    Raises:
        NotFoundError: No order has this id (assumed, as for ``order/read.json``).
    """
    raw = await client_for(org).get_json("/order/document/read.json", params={"id": id})
    response = parse(
        ReadResponse[OrderDocument], raw, source=SOURCE, endpoint="order/document/read.json"
    )
    return response.data
