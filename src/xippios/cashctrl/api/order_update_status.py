"""``POST /api/v1/order/update_status.json``: set the status of orders.

Reference: ``docs/upstream/order.md``, "Update status" ("Updates the status of an existing
order by order ID. Returns either a success or multiple error messages (for each
issue)."). Its documented parameters, both mandatory: ``ids`` (CSV, "The IDs of one or
multiple orders, comma-separated.") and ``statusId`` (NUMBER, "The ID of the new
status."). A status is one of the order's category's ``status`` list
(``order/category/list.json``).
"""

from collections.abc import Mapping, Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import form_fields, ids_csv, post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["order_update_status", "order_update_status_fields"]


def order_update_status_fields(*, ids: Sequence[int], status_id: int) -> dict[str, str]:
    """The form fields of ``order/update_status.json``: ``{"ids": "20,21", "statusId": "16"}``.

    Upstream's names, in the order of its table; ``ids`` comma-separated. Checking the
    values is the task's.
    """
    return form_fields({"ids": ids_csv(ids), "statusId": status_id})


async def order_update_status(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``order/update_status.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: ``ids`` and ``statusId``, from ``order_update_status_fields``.

    Raises:
        RequestRejected: Upstream refused the change of status.
    """
    raw = await post_form(org, "/order/update_status.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/update_status.json")
