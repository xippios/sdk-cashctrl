"""``POST /api/v1/order/delete.json``: delete orders.

Reference: ``docs/upstream/order.md``, "Delete orders" ("Deletes one or multiple orders.
Returns either a success or error message."), one parameter, ``ids`` (mandatory, CSV):
"The IDs of the selected entries, comma-separated."
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import delete_fields, post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["order_delete"]


async def order_delete(org: str, ids: Sequence[int]) -> WriteAnswer:
    """Call ``order/delete.json`` for organisation ``org``: delete the orders ``ids``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        ids: ``ids``, the orders' ids, e.g. ``[7]``.

    Raises:
        RequestRejected: Upstream refused the delete.
    """
    raw = await post_form(org, "/order/delete.json", delete_fields(ids))
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/delete.json")
