"""``GET /api/v1/history/list.json``: the history, the audit log, one page at a time.

Reference: ``docs/upstream/common.md``, History, "List history" ("Returns the history
list."). Its documented parameters, all optional: ``dir`` (default ``DESC``),
``filter``, ``limit`` ("The number of entries to retrieve. Defaults to 100."),
``orderId``, ``personId`` and ``statementId`` (the history of one order, person or
salary statement), ``query`` and ``start`` ("The starting entry. Defaults to 0."); no
``sort``. Observed on 2026-10-27: ``{"total": 2, "data": [...]}`` for a seeded order,
newest first, and ``{"total": 0, "data": []}`` for an order deleted a minute before,
whose create and update the history had listed. Pages are the task's business.
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._params import present
from xippios.cashctrl.models import Direction, Filter, HistoryEntry, ListResponse

__all__ = ["history_list", "history_list_params"]


def history_list_params(
    *,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    limit: int | None = None,
    order_id: int | None = None,
    person_id: int | None = None,
    query: str | None = None,
    start: int | None = None,
    statement_id: int | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``history/list.json``, under upstream's names.

    A parameter left at ``None`` is not sent, so upstream applies its own default; an
    empty ``filter`` is not sent either, and ``filter`` goes as its JSON array.
    """
    return present(
        {
            "dir": dir,
            "filter": encode_filter(filter) if filter else None,
            "orderId": order_id,
            "personId": person_id,
            "query": query,
            "statementId": statement_id,
            "start": start,
            "limit": limit,
        }
    )


async def history_list(
    org: str,
    *,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    limit: int | None = None,
    order_id: int | None = None,
    person_id: int | None = None,
    query: str | None = None,
    start: int | None = None,
    statement_id: int | None = None,
) -> ListResponse[HistoryEntry]:
    """Call ``history/list.json`` for organisation ``org``: one page and upstream's total.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        dir: ``dir``, ``ASC`` or ``DESC``; upstream's default is ``DESC``.
        filter: ``filter``, sent as a JSON array; all filters must match.
        limit: ``limit``, the number of entries; upstream's default is 100.
        order_id: ``orderId``, the history of one order.
        person_id: ``personId``, the history of one person.
        query: ``query``, a full-text search.
        start: ``start``, the offset of the first entry; upstream's default is 0.
        statement_id: ``statementId``, the history of one salary statement.
    """
    params = history_list_params(
        dir=dir,
        filter=filter,
        limit=limit,
        order_id=order_id,
        person_id=person_id,
        query=query,
        start=start,
        statement_id=statement_id,
    )
    raw = await client_for(org).get_json("/history/list.json", params=params)
    return parse(ListResponse[HistoryEntry], raw, source=SOURCE, endpoint="history/list.json")
