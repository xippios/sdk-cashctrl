"""``GET /api/v1/account/list.json``: the accounts of an organisation, with balances.

Reference: ``docs/upstream/account.md``, "List accounts" ("Returns a list of all
accounts."). Its documented parameters, all optional: ``categoryId``, ``dir``, ``filter``,
``fiscalPeriodId``, ``onlyActive``, ``onlyCostCenters``, ``onlyNotes``, ``query``,
``sort``. It documents no ``start`` or ``limit``: one answer holds every match.
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._params import flag, present
from xippios.cashctrl.models import Account, Direction, Filter, ListResponse

__all__ = ["account_list", "account_list_params"]


def account_list_params(
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    only_active: bool | None = None,
    only_cost_centers: bool | None = None,
    only_notes: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``account/list.json``, under upstream's names.

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
            "onlyCostCenters": flag(only_cost_centers),
            "onlyNotes": flag(only_notes),
            "query": query,
            "sort": sort,
        }
    )


async def account_list(
    org: str,
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    only_active: bool | None = None,
    only_cost_centers: bool | None = None,
    only_notes: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
) -> ListResponse[Account]:
    """Call ``account/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        category_id: ``categoryId``, an account category.
        dir: ``dir``, ``ASC`` or ``DESC``; upstream's default is ``ASC``.
        filter: ``filter``, sent as a JSON array; all filters must match.
        fiscal_period_id: ``fiscalPeriodId``, the fiscal period of the balances.
        only_active: ``onlyActive``; upstream's default is false.
        only_cost_centers: ``onlyCostCenters``; upstream's default is false.
        only_notes: ``onlyNotes``; upstream's default is false.
        query: ``query``, a full-text search.
        sort: ``sort``, the column to sort by; upstream's default is ``number``.
    """
    params = account_list_params(
        category_id=category_id,
        dir=dir,
        filter=filter,
        fiscal_period_id=fiscal_period_id,
        only_active=only_active,
        only_cost_centers=only_cost_centers,
        only_notes=only_notes,
        query=query,
        sort=sort,
    )
    raw = await client_for(org).get_json("/account/list.json", params=params)
    return parse(ListResponse[Account], raw, source=SOURCE, endpoint="account/list.json")
