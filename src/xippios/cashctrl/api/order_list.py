"""``GET /api/v1/order/list.json``: orders (sales or purchase), one page at a time.

Reference: ``docs/upstream/order.md``, "List orders" ("Returns a list of orders per type
(sales or purchase)."). Its documented parameters, all optional: ``categoryId``,
``dir`` (default ``DESC``), ``filter``, ``fiscalPeriodId``, ``groupId``, ``limit`` ("The
number of entries to retrieve. Defaults to 100."), ``onlyCostCenters``, ``onlyNotes``,
``onlyOpen``, ``onlyOverdue``, ``personId``, ``query``, ``sort`` (default ``date``),
``start`` ("The starting entry. Defaults to 0."), ``statusId`` and ``type`` ("Possible
values: SALES, PURCHASE", no default documented).

Observed on 2026-10-23 against the demo organisation: without ``type`` the list holds
both types (the 4 sales and 2 purchase orders of 2026); without ``fiscalPeriodId`` it
answers for the API user's current fiscal period, which held no order. Pages are the
task's business.
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._params import flag, present
from xippios.cashctrl.models import Direction, Filter, ListResponse, Order, OrderType

__all__ = ["order_list", "order_list_params"]


def order_list_params(
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    group_id: int | None = None,
    limit: int | None = None,
    only_cost_centers: bool | None = None,
    only_notes: bool | None = None,
    only_open: bool | None = None,
    only_overdue: bool | None = None,
    person_id: int | None = None,
    query: str | None = None,
    sort: str | None = None,
    start: int | None = None,
    status_id: int | None = None,
    type: OrderType | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``order/list.json``, under upstream's names.

    A parameter left at ``None`` is not sent, so upstream applies its own default; an
    empty ``filter`` is not sent either. Booleans are sent as ``true``/``false`` and
    ``filter`` as its JSON array.
    """
    return present(
        {
            "categoryId": category_id,
            "dir": dir,
            "filter": encode_filter(filter) if filter else None,
            "fiscalPeriodId": fiscal_period_id,
            "groupId": group_id,
            "onlyCostCenters": flag(only_cost_centers),
            "onlyNotes": flag(only_notes),
            "onlyOpen": flag(only_open),
            "onlyOverdue": flag(only_overdue),
            "personId": person_id,
            "query": query,
            "sort": sort,
            "statusId": status_id,
            "type": type,
            "start": start,
            "limit": limit,
        }
    )


async def order_list(
    org: str,
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    group_id: int | None = None,
    limit: int | None = None,
    only_cost_centers: bool | None = None,
    only_notes: bool | None = None,
    only_open: bool | None = None,
    only_overdue: bool | None = None,
    person_id: int | None = None,
    query: str | None = None,
    sort: str | None = None,
    start: int | None = None,
    status_id: int | None = None,
    type: OrderType | None = None,
) -> ListResponse[Order]:
    """Call ``order/list.json`` for organisation ``org``: one page and upstream's total.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        category_id: ``categoryId``, an order category.
        dir: ``dir``, ``ASC`` or ``DESC``; upstream's default is ``DESC``.
        filter: ``filter``, sent as a JSON array; all filters must match.
        fiscal_period_id: ``fiscalPeriodId``; the current fiscal period when not sent.
        group_id: ``groupId``, an order group (dossier).
        limit: ``limit``, the number of entries; upstream's default is 100.
        only_cost_centers: ``onlyCostCenters``; upstream's default is false.
        only_notes: ``onlyNotes``; upstream's default is false.
        only_open: ``onlyOpen``; upstream's default is false.
        only_overdue: ``onlyOverdue``; upstream's default is false.
        person_id: ``personId``, the orders of one person.
        query: ``query``, a full-text search.
        sort: ``sort``, the column to sort by; upstream's default is ``date``.
        start: ``start``, the offset of the first entry; upstream's default is 0.
        status_id: ``statusId``, an order status.
        type: ``type``, ``SALES`` or ``PURCHASE``; both when not sent (observed).
    """
    params = order_list_params(
        category_id=category_id,
        dir=dir,
        filter=filter,
        fiscal_period_id=fiscal_period_id,
        group_id=group_id,
        limit=limit,
        only_cost_centers=only_cost_centers,
        only_notes=only_notes,
        only_open=only_open,
        only_overdue=only_overdue,
        person_id=person_id,
        query=query,
        sort=sort,
        start=start,
        status_id=status_id,
        type=type,
    )
    raw = await client_for(org).get_json("/order/list.json", params=params)
    return parse(ListResponse[Order], raw, source=SOURCE, endpoint="order/list.json")
