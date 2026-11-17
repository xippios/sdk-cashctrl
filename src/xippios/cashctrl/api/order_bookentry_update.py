"""``POST /api/v1/order/bookentry/update.json``: change a manual book entry of an order.

Reference: ``docs/upstream/order.md``, Book entry, "Update book entry": the parameters
of "Create book entry" but ``orderIds``, and ``id`` (mandatory). "Note that you cannot
update book entries that have been automatically created from order items, only
manually created book entries (e.g. payments). Note that all parameters must be
submitted, omitted parameters are treated as empty values." The form fields come from
``order_bookentry_fields`` with ``id`` set; ``tasks_write.update_order_book_entry``
derives every one of them from the entry before it changes any.
"""

from collections.abc import Mapping

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["order_bookentry_update"]


async def order_bookentry_update(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``order/bookentry/update.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: Every form field of the entry, ``id`` included, from
            ``order_bookentry_fields``.

    Raises:
        RequestRejected: Upstream refused the update.
    """
    raw = await post_form(org, "/order/bookentry/update.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/bookentry/update.json")
