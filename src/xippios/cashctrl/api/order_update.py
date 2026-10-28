"""``POST /api/v1/order/update.json``: change an existing order.

Reference: ``docs/upstream/order.md``, "Update order" ("Updates an existing order. Note
that all parameters must be submitted, omitted parameters are treated as empty values.
Returns either a success or multiple error messages (for each issue)."): the parameters
of "Create order", ``associateId`` a NUMBER (one business partner) where the create
takes a CSV, and ``id`` (mandatory), "The ID of the order to update". The form fields
come from ``order_fields`` with ``id`` set; ``tasks_write.update_order`` derives every
one of them from the record before it changes any, the ``items`` included, which
upstream would otherwise empty.
"""

from collections.abc import Mapping

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["order_update"]


async def order_update(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``order/update.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: Every form field of the order, ``id`` included, from ``order_fields``.

    Raises:
        RequestRejected: Upstream refused the update.
    """
    raw = await post_form(org, "/order/update.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/update.json")
