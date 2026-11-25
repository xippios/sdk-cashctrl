"""``GET /api/v1/order/category/list.json``: the order categories of one type.

Reference: ``docs/upstream/order.md``, "List categories" in "Category" ("Returns a list
of categories per type (sales or purchase)."). Its documented parameters, both optional:
``fiscalPeriodId`` ("The ID of the fiscal period, from which we retrieve the counts
(number of orders). Leave empty to use the current fiscal period.") and ``type`` ("The
type of category (sales orders or purchase orders). Defaults to SALES. Possible values:
SALES, PURCHASE."). It documents no ``start`` or ``limit``: one answer carries every
category. Its answer without ``type``, as ``docs/upstream/OBSERVED.md`` notes:
``{"total": 6, "data": [...]}``, the
six default sales categories, ``total`` equal to the records.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.api._params import present
from xippios.cashctrl.models import ListResponse, OrderCategory, OrderType

__all__ = ["order_category_list", "order_category_list_params"]


def order_category_list_params(
    *, fiscal_period_id: int | None = None, type: OrderType | None = None
) -> dict[str, str | int]:
    """The query parameters of ``order/category/list.json``; ``None`` is not sent."""
    return present({"fiscalPeriodId": fiscal_period_id, "type": type})


async def order_category_list(
    org: str, *, fiscal_period_id: int | None = None, type: OrderType | None = None
) -> Answer[ListResponse[OrderCategory]]:
    """Call ``order/category/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fiscal_period_id: ``fiscalPeriodId``, the period the order counts come from; the
            current fiscal period when not sent.
        type: ``type``, ``SALES`` or ``PURCHASE``; upstream's default is ``SALES``.
    """
    params = order_category_list_params(fiscal_period_id=fiscal_period_id, type=type)
    return await client_for(org).get_answer(
        "/order/category/list.json",
        params=params,
        parse=ListResponse[OrderCategory],
        endpoint="order/category/list.json",
    )
