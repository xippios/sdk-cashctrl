"""``GET /api/v1/account/costcenter/list.json``: the cost centers of an organisation.

Reference: ``docs/upstream/account.md``, "List cost centers" ("Returns a list of all cost
centers."). Its documented parameters, all optional: ``categoryId``, ``dir`` ("Defaults
to 'ASC'."), ``filter``, ``fiscalPeriodId`` ("The ID of the fiscal period, from which we
retrieve the balances."), ``onlyActive`` and ``onlyNotes`` ("Defaults to false."),
``query`` and ``sort`` ("Defaults to 'number'."). It documents no ``start`` or
``limit``: one answer holds every match. Observed on 2026-10-27: ``{"total": 0, "data":
[]}``, the demo organisation having no cost center.
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._params import flag, present
from xippios.cashctrl.models import CostCenter, Direction, Filter, ListResponse

__all__ = ["account_costcenter_list", "account_costcenter_list_params"]


def account_costcenter_list_params(
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    only_active: bool | None = None,
    only_notes: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``account/costcenter/list.json``, under upstream's names.

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
            "onlyActive": flag(only_active),
            "onlyNotes": flag(only_notes),
            "query": query,
            "sort": sort,
        }
    )


async def account_costcenter_list(
    org: str,
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    only_active: bool | None = None,
    only_notes: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
) -> ListResponse[CostCenter]:
    """Call ``account/costcenter/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        category_id: ``categoryId``, a cost center category.
        dir: ``dir``, ``ASC`` or ``DESC``; upstream's default is ``ASC``.
        filter: ``filter``, sent as a JSON array; all filters must match.
        fiscal_period_id: ``fiscalPeriodId``, the fiscal period of the balances.
        only_active: ``onlyActive``; upstream's default is false.
        only_notes: ``onlyNotes``; upstream's default is false.
        query: ``query``, a full-text search.
        sort: ``sort``, the column to sort by; upstream's default is ``number``.
    """
    params = account_costcenter_list_params(
        category_id=category_id,
        dir=dir,
        filter=filter,
        fiscal_period_id=fiscal_period_id,
        only_active=only_active,
        only_notes=only_notes,
        query=query,
        sort=sort,
    )
    raw = await client_for(org).get_json("/account/costcenter/list.json", params=params)
    return parse(
        ListResponse[CostCenter], raw, source=SOURCE, endpoint="account/costcenter/list.json"
    )
