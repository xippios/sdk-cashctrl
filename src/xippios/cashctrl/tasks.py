"""Task-shaped functions for CashCtrl.

The public API (ADR-0001, layer 2). A task composes endpoint wrappers from ``api/``,
resolves pagination and reference lookups, and returns ``Result[T]`` with full
``ResultMeta``. Write the async version, derive the sync one with ``xippios.core.sync``,
and list the sync name in ``__all__``: the MCP server and the HTTP router register
exactly what is named there.

``org: str`` is the first, required parameter of every task: the name of a declared
organisation (``demo``, ``acme``), handed to the endpoint wrappers, which reach CashCtrl
through ``client_for(org)``. No task spans organisations. ``tests/test_tasks.py`` checks
every name in ``__all__``.

Docstrings are read by agents: one sentence first, then ``Args:`` with examples of
valid values for every parameter. ``/add-endpoint`` walks through the whole recipe.

``meta.endpoint`` is the upstream path after ``/api/v1/`` (``account/list.json``) and
``meta.request`` holds ``org`` plus the query parameters sent, under upstream's names.
CashCtrl publishes no release time or identifier, so ``published_at`` and ``vintage``
stay empty. The lists served here document no ``start`` or ``limit`` and come back whole
in one answer (upstream's ``total`` equals the number of records), so ``total`` is not
carried separately.
"""

from collections.abc import Mapping, Sequence
from typing import Any, get_args

from pydantic import ValidationError
from pydantic_core import ErrorDetails
from xippios.core import InvalidRequestError, Result, ResultMeta, sync

from xippios.cashctrl import api
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.models import (
    Account,
    AccountDetail,
    Comparison,
    Currency,
    Direction,
    Filter,
    FiscalPeriod,
    TaxCode,
)

__all__ = [
    "get_account",
    "list_accounts",
    "list_currencies",
    "list_fiscal_periods",
    "list_tax_codes",
]

DIRECTIONS: tuple[str, ...] = get_args(Direction)
"""The values of ``dir`` on every list that documents it: ``ASC``, ``DESC``."""
COMPARISONS: tuple[str, ...] = get_args(Comparison)
"""The values of ``comparison`` in a ``filter`` item: ``eq``, ``like``, ``gt``, ``lt``."""


def _meta(endpoint: str, request: dict[str, Any]) -> ResultMeta:
    return ResultMeta(source=SOURCE, endpoint=endpoint, request=request)


def _wrong_comparison(where: str, value: object) -> str:
    return f"{where}.comparison must be one of eq, like, gt, lt, not {value!r}"


def _problem(where: str, detail: ErrorDetails) -> str:
    """One validation error of a ``filter`` item, in the words of the other refusals."""
    if detail["loc"] == ("comparison",):
        return _wrong_comparison(where, detail["input"])
    field = ".".join(str(part) for part in detail["loc"])
    return f"{where}.{field}: {detail['msg']}"


def _filter_item(where: str, item: object) -> tuple[Filter | None, list[str]]:
    """One ``filter`` item as a ``Filter``, or the problems that keep it from being one."""
    if isinstance(item, Mapping):
        try:
            item = Filter.model_validate(dict(item))
        except ValidationError as error:
            return None, [_problem(where, detail) for detail in error.errors()]
    if not isinstance(item, Filter):
        return None, [f"{where} must be a Filter or a mapping, not {type(item).__name__}"]
    if item.comparison not in COMPARISONS:  # a Filter built without validation
        return None, [_wrong_comparison(where, item.comparison)]
    return item, []


def _check_list_arguments(
    *,
    dir: object = None,
    filter: object = None,
    texts: dict[str, object] | None = None,
) -> list[Filter] | None:
    """Refuse what upstream would silently ignore, before anything is sent (ADR-0007).

    Only what the documentation fixes is checked: ``dir`` is ``ASC`` or ``DESC``, every
    ``filter`` item is a ``Filter``, or a mapping that validates as one, whose
    ``comparison`` is ``eq``, ``like``, ``gt`` or ``lt``, and the text parameters
    (``query``, ``sort``) are strings. Column names in ``sort`` and ``Filter.field`` are
    not documented, so they are not checked. The parameter types say the same, so the
    MCP and HTTP adapters refuse a wrong value before the task runs; this check is for
    Python callers, whose arguments nothing else validates.

    Returns:
        ``filter`` as ``Filter`` objects, or ``None`` when it was not given.

    Raises:
        InvalidRequestError: Naming every problem found.
    """
    problems: list[str] = []
    if dir is not None and dir not in DIRECTIONS:
        problems.append(f"dir must be ASC or DESC, not {dir!r}")
    filters: list[Filter] | None = None
    if filter is not None:
        if isinstance(filter, str | bytes) or not isinstance(filter, Sequence):
            problems.append(
                "filter takes a list of filters such as "
                '[{"comparison": "eq", "field": "number", "value": "1020"}], '
                f"not {type(filter).__name__}"
            )
        else:
            filters = []
            for index, item in enumerate(filter):
                parsed, found = _filter_item(f"filter[{index}]", item)
                problems += found
                if parsed is not None:
                    filters.append(parsed)
    for name, value in (texts or {}).items():
        if value is not None and not isinstance(value, str):
            problems.append(f"{name} must be a string, not {type(value).__name__}")
    if problems:
        raise InvalidRequestError("; ".join(problems), source=SOURCE)
    return filters


async def list_fiscal_periods_async(org: str) -> Result[list[FiscalPeriod]]:
    """List an organisation's fiscal periods, with their dates and which one is current.

    Every fiscal period comes back in upstream's order, with ``start`` and ``end`` as
    dates, whether it is closed, the months still open or closed
    (``open_month_ids``, ``closed_month_ids``, as ``YYYY-MM``), and ``is_current`` for the
    period upstream uses by default, e.g. for account balances. Use an ``id`` from here as
    ``fiscal_period_id`` in ``list_accounts``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.fiscalperiod_list(org)
    return Result(data=response.data, meta=_meta("fiscalperiod/list.json", {"org": org}))


async def list_currencies_async(org: str) -> Result[list[Currency]]:
    """List an organisation's currencies with their exchange rates into the default currency.

    Every currency comes back with its three-letter ``code`` (``CHF``, ``EUR``), its
    ``rate`` into the organisation's default currency (``1`` for the default currency
    itself, marked ``is_default``) and its ``description``, which may hold localised text
    as ``<values><de>...</de></values>``. Use an ``id`` from here where a call asks for a
    ``currency_id``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.currency_list(org)
    return Result(data=response.data, meta=_meta("currency/list.json", {"org": org}))


async def list_tax_codes_async(org: str) -> Result[list[TaxCode]]:
    """List an organisation's tax codes with their rates and the accounts they book to.

    Every tax code comes back with its short ``code`` (``UN1``), its ``rates`` (each a
    ``percentage`` such as ``8.1``, valid from ``date_valid``; the rate without a date is
    the fallback), ``current_percentage``, and its ``components``: the ``account_id`` the
    tax is collected on, ``calc_type`` (``NET`` or ``GROSS``) and ``apply_rule``.
    ``is_inactive`` marks codes no longer suggested. Use an ``id`` from here where a call
    asks for a ``tax_id``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.tax_list(org)
    return Result(data=response.data, meta=_meta("tax/list.json", {"org": org}))


async def list_accounts_async(
    org: str,
    *,
    query: str | None = None,
    filter: list[Filter] | None = None,
    category_id: int | None = None,
    fiscal_period_id: int | None = None,
    only_active: bool = False,
    only_cost_centers: bool = False,
    only_notes: bool = False,
    sort: str | None = None,
    dir: Direction | None = None,
) -> Result[list[Account]]:
    """List an organisation's accounts, its chart of accounts, with their balances.

    Every matching account comes back with its ``number`` (``"1020"``), ``name``,
    ``category_id``, ``currency_code``, ``is_inactive`` and its balances for one fiscal
    period: ``opening_amount`` and ``end_amount`` in the account's currency,
    ``default_currency_opening_amount`` and ``default_currency_end_amount`` in the default
    currency. Without parameters every account is listed, and a large chart of accounts
    exceeds the MCP result cap (200 rows or 64 KB): the tool result is then truncated
    with a note, so narrow the list with ``query``, ``filter`` or ``only_active``.
    Upstream ignores values it does not understand, so ``dir`` and the filters'
    ``comparison`` are checked first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        query: Full-text search, e.g. ``"Finanz"``.
        filter: Filters that must all match, each with ``comparison`` (``eq``, ``like``,
            ``gt`` or ``lt``; ``like`` when left out), ``field`` (a column of the list,
            e.g. ``number``) and ``value`` (a text, or a list of texts of which any may
            match), e.g. ``[{"comparison": "eq", "field": "number", "value": "1020"}]``.
            From Python, these mappings or ``Filter`` objects, e.g.
            ``[Filter(comparison="eq", field="number", value="1020")]``.
        category_id: Only the accounts of one account category, e.g. ``1``.
        fiscal_period_id: The fiscal period whose balances are returned, an ``id`` from
            ``list_fiscal_periods``, e.g. ``2``; the current fiscal period when left out.
        only_active: ``true`` to leave out inactive accounts.
        only_cost_centers: ``true`` to list only accounts with cost centers.
        only_notes: ``true`` to list only accounts with notes.
        sort: The column to sort by, e.g. ``number`` (upstream's default) or ``name``.
        dir: ``ASC`` (upstream's default) or ``DESC``.
    """
    filters = _check_list_arguments(dir=dir, filter=filter, texts={"query": query, "sort": sort})
    arguments: dict[str, Any] = {
        "category_id": category_id,
        "dir": dir,
        "filter": filters,
        "fiscal_period_id": fiscal_period_id,
        "only_active": only_active or None,
        "only_cost_centers": only_cost_centers or None,
        "only_notes": only_notes or None,
        "query": query,
        "sort": sort,
    }
    sent = api.account_list_params(**arguments)
    response = await api.account_list(org, **arguments)
    return Result(data=response.data, meta=_meta("account/list.json", {"org": org, **sent}))


async def get_account_async(org: str, id: int) -> Result[AccountDetail]:
    """Read one account of an organisation by its id.

    The account comes back as upstream's read returns it: ``number``, ``name``,
    ``category_id``, ``currency_id`` and ``currency_code``, ``tax_id``, ``is_inactive``,
    ``notes``, the custom fields in ``custom``, ``attachments`` and ``allocations``. It
    carries no balances; ``list_accounts`` has them. An id no account has raises
    ``NotFoundError``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The account's ``id`` as ``list_accounts`` gives it, e.g. ``100``; not the
            account number.
    """
    account = await api.account_read(org, id)
    return Result(data=account, meta=_meta("account/read.json", {"org": org, "id": id}))


list_fiscal_periods = sync(list_fiscal_periods_async)
list_currencies = sync(list_currencies_async)
list_tax_codes = sync(list_tax_codes_async)
list_accounts = sync(list_accounts_async)
get_account = sync(get_account_async)
