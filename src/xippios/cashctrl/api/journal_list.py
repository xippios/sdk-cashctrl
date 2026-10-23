"""``GET /api/v1/journal/list.json``: journal entries, one page at a time.

Reference: ``docs/upstream/journal.md``, "List journal entries" ("Returns a list of
journal entries."). Its documented parameters, all optional: ``accountId``,
``associateId``, ``dir`` (default ``DESC``), ``filter``, ``fiscalPeriodId``, ``limit``
("The number of entries to retrieve. Defaults to 100."), ``onlyCollective``,
``onlyCostCenters``, ``onlyImported``, ``onlyManual``, ``onlyNotes``, ``onlyPurchase``,
``onlySalary``, ``onlySales``, ``onlyUntaxed``, ``query``, ``sort`` (default
``dateAdded``) and ``start`` ("The starting entry. Defaults to 0."). Without
``fiscalPeriodId`` upstream answers for the API user's current fiscal period
(``docs/upstream/meta.md``, "Switch fiscal period"). Pages are the task's business.
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._params import flag, present
from xippios.cashctrl.models import Direction, Filter, JournalEntry, ListResponse

__all__ = ["journal_list", "journal_list_params"]


def journal_list_params(
    *,
    account_id: int | None = None,
    associate_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    limit: int | None = None,
    only_collective: bool | None = None,
    only_cost_centers: bool | None = None,
    only_imported: bool | None = None,
    only_manual: bool | None = None,
    only_notes: bool | None = None,
    only_purchase: bool | None = None,
    only_salary: bool | None = None,
    only_sales: bool | None = None,
    only_untaxed: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
    start: int | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``journal/list.json``, under upstream's names.

    A parameter left at ``None`` is not sent, so upstream applies its own default; an
    empty ``filter`` is not sent either. Booleans are sent as ``true``/``false`` and
    ``filter`` as its JSON array.
    """
    return present(
        {
            "accountId": account_id,
            "associateId": associate_id,
            "dir": dir,
            "filter": encode_filter(filter) if filter else None,
            "fiscalPeriodId": fiscal_period_id,
            "onlyCollective": flag(only_collective),
            "onlyCostCenters": flag(only_cost_centers),
            "onlyImported": flag(only_imported),
            "onlyManual": flag(only_manual),
            "onlyNotes": flag(only_notes),
            "onlyPurchase": flag(only_purchase),
            "onlySalary": flag(only_salary),
            "onlySales": flag(only_sales),
            "onlyUntaxed": flag(only_untaxed),
            "query": query,
            "sort": sort,
            "start": start,
            "limit": limit,
        }
    )


async def journal_list(
    org: str,
    *,
    account_id: int | None = None,
    associate_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    fiscal_period_id: int | None = None,
    limit: int | None = None,
    only_collective: bool | None = None,
    only_cost_centers: bool | None = None,
    only_imported: bool | None = None,
    only_manual: bool | None = None,
    only_notes: bool | None = None,
    only_purchase: bool | None = None,
    only_salary: bool | None = None,
    only_sales: bool | None = None,
    only_untaxed: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
    start: int | None = None,
) -> ListResponse[JournalEntry]:
    """Call ``journal/list.json`` for organisation ``org``: one page and upstream's total.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        account_id: ``accountId``, the journal of one account.
        associate_id: ``associateId``, the journal of one person.
        dir: ``dir``, ``ASC`` or ``DESC``; upstream's default is ``DESC``.
        filter: ``filter``, sent as a JSON array; all filters must match.
        fiscal_period_id: ``fiscalPeriodId``; the current fiscal period when not sent.
        limit: ``limit``, the number of entries; upstream's default is 100.
        only_collective: ``onlyCollective``; upstream's default is false.
        only_cost_centers: ``onlyCostCenters``; upstream's default is false.
        only_imported: ``onlyImported``; upstream's default is false.
        only_manual: ``onlyManual``; upstream's default is false.
        only_notes: ``onlyNotes``; upstream's default is false.
        only_purchase: ``onlyPurchase``; upstream's default is false.
        only_salary: ``onlySalary``; upstream's default is false.
        only_sales: ``onlySales``; upstream's default is false.
        only_untaxed: ``onlyUntaxed``; upstream's default is false.
        query: ``query``, a full-text search.
        sort: ``sort``, the column to sort by; upstream's default is ``dateAdded``.
        start: ``start``, the offset of the first entry; upstream's default is 0.
    """
    params = journal_list_params(
        account_id=account_id,
        associate_id=associate_id,
        dir=dir,
        filter=filter,
        fiscal_period_id=fiscal_period_id,
        limit=limit,
        only_collective=only_collective,
        only_cost_centers=only_cost_centers,
        only_imported=only_imported,
        only_manual=only_manual,
        only_notes=only_notes,
        only_purchase=only_purchase,
        only_salary=only_salary,
        only_sales=only_sales,
        only_untaxed=only_untaxed,
        query=query,
        sort=sort,
        start=start,
    )
    raw = await client_for(org).get_json("/journal/list.json", params=params)
    return parse(ListResponse[JournalEntry], raw, source=SOURCE, endpoint="journal/list.json")
