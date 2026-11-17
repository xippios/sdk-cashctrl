"""``POST /api/v1/order/bookentry/delete.json``: delete book entries of orders.

Reference: ``docs/upstream/order.md``, Book entry, "Delete book entries" ("Deletes one or
multiple book entries. Returns either a success or error message."), one parameter,
``ids`` (mandatory, CSV): "The IDs of the selected entries, comma-separated." The
section's opening says that automatically created entries "cannot be manipulated
directly, only by changing items".
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import delete_fields, post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["order_bookentry_delete"]


async def order_bookentry_delete(org: str, ids: Sequence[int]) -> WriteAnswer:
    """Call ``order/bookentry/delete.json`` for organisation ``org``: delete the entries ``ids``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        ids: ``ids``, the book entries' ids, e.g. ``[31]``.

    Raises:
        RequestRejected: Upstream refused the delete.
    """
    raw = await post_form(org, "/order/bookentry/delete.json", delete_fields(ids))
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/bookentry/delete.json")
