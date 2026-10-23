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
stay empty. Every list task sets ``meta.total`` to upstream's ``total``, its count of the
records matching the request (ADR-0012); it is never computed from ``len(data)``.

The journal, person and order lists page by offset (``start``, ``limit``), resolved once
in ``_offset_pages`` (conventions §4). With ``limit`` the task sends one request,
``start`` (default 0) and ``limit``, and returns that page; ``meta.total`` tells the
caller how many there are in all. Without ``limit`` it collects every page from
``start`` on through core's ``paginate_offset``, ``PAGE_SIZE`` (100, upstream's
documented default for ``limit``, sent explicitly) at a time, and stops after a short
page or, without a further request, once the next offset reaches the ``total``
upstream reported; ``meta.total`` is the ``total`` of the last page fetched. A page past
the end is answered with an empty ``data`` and the same ``total`` (observed on
2026-10-23). ``meta.request`` holds the parameters as the first request sent them; when
every page is collected it leaves out ``limit``, the page size, so the same arguments
collect the same records again.
"""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, TypeGuard, get_args

from pydantic import ValidationError
from pydantic_core import ErrorDetails
from xippios.core import (
    InvalidRequestError,
    Result,
    ResultMeta,
    collect,
    paginate_offset,
    sync,
)

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
    JournalEntry,
    JournalEntryDetail,
    ListResponse,
    Order,
    OrderDetail,
    OrderType,
    Person,
    PersonDetail,
    TaxCode,
)

__all__ = [
    "get_account",
    "get_journal_entry",
    "get_order",
    "get_person",
    "list_accounts",
    "list_currencies",
    "list_fiscal_periods",
    "list_journal_entries",
    "list_orders",
    "list_persons",
    "list_tax_codes",
]

DIRECTIONS: tuple[str, ...] = get_args(Direction)
"""The values of ``dir`` on every list that documents it: ``ASC``, ``DESC``."""
COMPARISONS: tuple[str, ...] = get_args(Comparison)
"""The values of ``comparison`` in a ``filter`` item: ``eq``, ``like``, ``gt``, ``lt``."""
ORDER_TYPES: tuple[str, ...] = get_args(OrderType)
"""The values of ``type`` on ``order/list.json``: ``SALES``, ``PURCHASE``."""
PAGE_SIZE = 100
"""Records per request when a list task collects every page.

Upstream's documented default for ``limit`` on the journal, person and order lists
("Defaults to 100."), sent explicitly so the page size never depends on that default.
"""


def _meta(endpoint: str, request: dict[str, Any], *, total: int | None = None) -> ResultMeta:
    return ResultMeta(source=SOURCE, endpoint=endpoint, request=request, total=total)


async def _offset_pages[T](
    fetch_page: Callable[[int, int], Awaitable[ListResponse[T]]],
    *,
    start: int,
    limit: int | None,
) -> tuple[list[T], int]:
    """One page, or every page from ``start`` on, with upstream's ``total`` (ADR-0012).

    Args:
        fetch_page: Fetches the page at an offset with a page size, e.g. a wrapper call
            with ``start`` and ``limit``.
        start: The offset of the first record, ``0`` for the first.
        limit: ``None`` collects every page through ``paginate_offset``, ``PAGE_SIZE``
            records a request; a number fetches that one page.

    Returns:
        The records and the ``total`` upstream reported, on the last page fetched.
    """
    if limit is not None:
        page = await fetch_page(start, limit)
        return page.data, page.total
    totals: list[int] = []

    async def fetch(offset: int) -> list[T]:
        if totals and offset >= totals[-1]:
            return []  # upstream counts nothing past this offset: no further request
        page = await fetch_page(offset, PAGE_SIZE)
        totals.append(page.total)
        return page.data

    records = await collect(paginate_offset(fetch, page_size=PAGE_SIZE, start=start))
    return records, totals[-1]


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


def _whole(value: object) -> TypeGuard[int]:
    """An ``int`` that is not a ``bool``: a count or an offset."""
    return isinstance(value, int) and not isinstance(value, bool)


def _check_list_arguments(
    *,
    dir: object = None,
    filter: object = None,
    texts: dict[str, object] | None = None,
    choices: dict[str, tuple[object, tuple[str, ...]]] | None = None,
    start: object = 0,
    limit: object = None,
) -> list[Filter] | None:
    """Refuse what upstream would silently ignore, before anything is sent (ADR-0007).

    Only what the documentation fixes is checked: ``dir`` is ``ASC`` or ``DESC``, every
    ``filter`` item is a ``Filter``, or a mapping that validates as one, whose
    ``comparison`` is ``eq``, ``like``, ``gt`` or ``lt``, the text parameters
    (``query``, ``sort``) are strings, and a documented value set (``choices``, such as
    the orders' ``type``) holds the value given. Paging is the task's own: ``start`` is a
    whole number of at least 0, ``limit`` one of at least 1. Column names in ``sort`` and
    ``Filter.field`` are not documented, so they are not checked. The parameter types say
    the same, so the MCP and HTTP adapters refuse a wrong value before the task runs;
    this check is for Python callers, whose arguments nothing else validates.

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
    for name, (value, allowed) in (choices or {}).items():
        if value is not None and value not in allowed:
            problems.append(f"{name} must be {' or '.join(allowed)}, not {value!r}")
    if not _whole(start) or start < 0:
        problems.append(f"start must be a whole number of at least 0, not {start!r}")
    if limit is not None and (not _whole(limit) or limit < 1):
        problems.append(f"limit must be a whole number of at least 1, not {limit!r}")
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
    meta = _meta("fiscalperiod/list.json", {"org": org}, total=response.total)
    return Result(data=response.data, meta=meta)


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
    meta = _meta("currency/list.json", {"org": org}, total=response.total)
    return Result(data=response.data, meta=meta)


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
    return Result(
        data=response.data, meta=_meta("tax/list.json", {"org": org}, total=response.total)
    )


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
    meta = _meta("account/list.json", {"org": org, **sent}, total=response.total)
    return Result(data=response.data, meta=meta)


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


async def list_journal_entries_async(
    org: str,
    *,
    fiscal_period_id: int | None = None,
    account_id: int | None = None,
    associate_id: int | None = None,
    query: str | None = None,
    filter: list[Filter] | None = None,
    only_collective: bool = False,
    only_cost_centers: bool = False,
    only_imported: bool = False,
    only_manual: bool = False,
    only_notes: bool = False,
    only_purchase: bool = False,
    only_salary: bool = False,
    only_sales: bool = False,
    only_untaxed: bool = False,
    sort: str | None = None,
    dir: Direction | None = None,
    start: int = 0,
    limit: int | None = None,
) -> Result[list[JournalEntry]]:
    """List an organisation's journal entries, newest first: every page, or one.

    Every entry comes back with its date ``date_added``, ``title``, ``reference``,
    ``amount``, the accounts it books (``debit_id`` and ``debit_name``, ``credit_id`` and
    ``credit_name``), the partner (``associate_id``, ``associate_name``), the tax code
    (``tax_code``, ``tax_rate``) and its ``type`` (``MANUAL``, ``COLLECTIVE``). A
    collective entry has ``items_count`` lines, which ``get_journal_entry`` returns.
    Without ``fiscal_period_id`` upstream lists the API user's current fiscal period
    only. Without ``limit`` every matching entry from ``start`` on is returned; with
    ``limit``, one page of at most ``limit`` entries from ``start``. ``meta.total`` is
    upstream's count of all matching entries, so there is more while
    ``start + limit < meta.total``. A long journal exceeds the MCP result cap (200 rows
    or 64 KB) and is truncated with a note: page with ``limit`` and ``start``, or narrow
    the list. Upstream ignores values it does not understand, so ``dir`` and the
    filters' ``comparison`` are checked first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        fiscal_period_id: The fiscal period, an ``id`` from ``list_fiscal_periods``,
            e.g. ``2``; the current fiscal period when left out.
        account_id: Only the entries that book to one account, an ``id`` from
            ``list_accounts`` (not the account number), e.g. ``3``.
        associate_id: Only the entries that name one person, an ``id`` from
            ``list_persons``, e.g. ``8``.
        query: Full-text search, e.g. ``"Miete"``.
        filter: Filters that must all match, each with ``comparison`` (``eq``, ``like``,
            ``gt`` or ``lt``; ``like`` when left out), ``field`` (a column of the list,
            e.g. ``reference``) and ``value`` (a text, or a list of texts of which any
            may match), e.g.
            ``[{"comparison": "eq", "field": "reference", "value": "RE-2025-003"}]``.
        only_collective: ``true`` for collective entries only.
        only_cost_centers: ``true`` for entries with cost centers only.
        only_imported: ``true`` for imported entries only.
        only_manual: ``true`` for manual entries only.
        only_notes: ``true`` for entries with notes only.
        only_purchase: ``true`` for entries booked by purchase orders only.
        only_salary: ``true`` for salary entries only.
        only_sales: ``true`` for entries booked by sales orders only.
        only_untaxed: ``true`` for untaxed entries only.
        sort: The column to sort by, e.g. ``dateAdded`` (upstream's default).
        dir: ``DESC`` (upstream's default) or ``ASC``.
        start: The offset of the first entry, e.g. ``0`` (the default) or ``50``.
        limit: One page of at most this many entries, e.g. ``50``; every entry when
            left out.
    """
    filters = _check_list_arguments(
        dir=dir, filter=filter, texts={"query": query, "sort": sort}, start=start, limit=limit
    )
    arguments: dict[str, Any] = {
        "account_id": account_id,
        "associate_id": associate_id,
        "dir": dir,
        "filter": filters,
        "fiscal_period_id": fiscal_period_id,
        "only_collective": only_collective or None,
        "only_cost_centers": only_cost_centers or None,
        "only_imported": only_imported or None,
        "only_manual": only_manual or None,
        "only_notes": only_notes or None,
        "only_purchase": only_purchase or None,
        "only_salary": only_salary or None,
        "only_sales": only_sales or None,
        "only_untaxed": only_untaxed or None,
        "query": query,
        "sort": sort,
    }

    async def page(offset: int, size: int) -> ListResponse[JournalEntry]:
        return await api.journal_list(org, **arguments, start=offset, limit=size)

    entries, total = await _offset_pages(page, start=start, limit=limit)
    sent = api.journal_list_params(**arguments, start=start, limit=limit)
    meta = _meta("journal/list.json", {"org": org, **sent}, total=total)
    return Result(data=entries, meta=meta)


async def get_journal_entry_async(org: str, id: int) -> Result[JournalEntryDetail]:
    """Read one journal entry by its id, with its lines, bookings and partners.

    The entry comes back as upstream's read returns it: ``date_added``, ``title``,
    ``reference``, ``amount``, ``debit_id``, ``credit_id``, the tax code, and three
    lists: ``items``, the lines of a collective entry (each with ``account_id``,
    ``debit`` or ``credit``, ``description`` and ``associate_id``; empty for a simple
    entry), ``rows``, the bookings per account with tax rows apart (``is_tax``), and
    ``associates``, the full records of the persons the entry names. An id no entry has
    raises ``NotFoundError``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The entry's ``id`` as ``list_journal_entries`` gives it, e.g. ``11``.
    """
    entry = await api.journal_read(org, id)
    return Result(data=entry, meta=_meta("journal/read.json", {"org": org, "id": id}))


async def list_persons_async(
    org: str,
    *,
    query: str | None = None,
    filter: list[Filter] | None = None,
    category_id: int | None = None,
    only_active: bool = False,
    only_customers: bool = False,
    only_vendors: bool = False,
    only_employees: bool = False,
    only_insurances: bool = False,
    only_families: bool = False,
    only_notes: bool = False,
    only_with_images: bool = False,
    only_without_category: bool = False,
    only_without_role: bool = False,
    sort: str | None = None,
    dir: Direction | None = None,
    start: int = 0,
    limit: int | None = None,
) -> Result[list[Person]]:
    """List an organisation's persons, its customers, vendors and other contacts, by name.

    Every person comes back with its ``name``, ``nr`` (e.g. ``P-00001``), ``company``,
    ``first_name`` and ``last_name``, its roles (``is_customer``, ``is_vendor``,
    ``is_employee``, ``is_insurance``, ``is_family``), ``category_id`` and
    ``category_name``, ``is_inactive``, the main address flattened (``address``,
    ``zip``, ``city``, ``country``) and ``email_work``. CashCtrl creates insurance
    records of its own (``is_insurance``). Addresses and contacts in full come from
    ``get_person``. Without ``limit`` every matching person from ``start`` on is
    returned; with ``limit``, one page of at most ``limit`` persons from ``start``.
    ``meta.total`` is upstream's count of all matching persons, so there is more while
    ``start + limit < meta.total``. Upstream ignores values it does not understand, so
    ``dir`` and the filters' ``comparison`` are checked first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        query: Full-text search, e.g. ``"Muster"``.
        filter: Filters that must all match, each with ``comparison`` (``eq``, ``like``,
            ``gt`` or ``lt``; ``like`` when left out), ``field`` (a column of the list,
            e.g. ``city``) and ``value`` (a text, or a list of texts of which any may
            match), e.g. ``[{"comparison": "eq", "field": "city", "value": "Basel"}]``.
        category_id: Only the persons of one person category, e.g. ``1``.
        only_active: ``true`` to leave out inactive persons.
        only_customers: ``true`` for customers only.
        only_vendors: ``true`` for vendors only.
        only_employees: ``true`` for employees only.
        only_insurances: ``true`` for insurances only.
        only_families: ``true`` for families only.
        only_notes: ``true`` for persons with notes only.
        only_with_images: ``true`` for persons with images only.
        only_without_category: ``true`` for persons without a category only.
        only_without_role: ``true`` for persons without a role only.
        sort: The column to sort by, e.g. ``name`` (upstream's default) or ``nr``.
        dir: ``ASC`` (upstream's default) or ``DESC``.
        start: The offset of the first person, e.g. ``0`` (the default) or ``50``.
        limit: One page of at most this many persons, e.g. ``50``; every person when
            left out.
    """
    filters = _check_list_arguments(
        dir=dir, filter=filter, texts={"query": query, "sort": sort}, start=start, limit=limit
    )
    arguments: dict[str, Any] = {
        "category_id": category_id,
        "dir": dir,
        "filter": filters,
        "only_active": only_active or None,
        "only_customers": only_customers or None,
        "only_employees": only_employees or None,
        "only_families": only_families or None,
        "only_insurances": only_insurances or None,
        "only_notes": only_notes or None,
        "only_vendors": only_vendors or None,
        "only_with_images": only_with_images or None,
        "only_without_category": only_without_category or None,
        "only_without_role": only_without_role or None,
        "query": query,
        "sort": sort,
    }

    async def page(offset: int, size: int) -> ListResponse[Person]:
        return await api.person_list(org, **arguments, start=offset, limit=size)

    persons, total = await _offset_pages(page, start=start, limit=limit)
    sent = api.person_list_params(**arguments, start=start, limit=limit)
    meta = _meta("person/list.json", {"org": org, **sent}, total=total)
    return Result(data=persons, meta=meta)


async def get_person_async(org: str, id: int) -> Result[PersonDetail]:
    """Read one person by its id, with its addresses and contacts.

    The person comes back as upstream's read returns it: ``name``, ``nr``, ``company``,
    ``first_name``, ``last_name``, the roles (``is_customer``, ``is_vendor``, ...),
    ``category_id`` and ``category_name``, ``language``, and the lists ``addresses``
    (each with ``type`` such as ``MAIN``, ``address``, ``zip``, ``city``, ``country``)
    and ``contacts`` (each with ``type`` such as ``EMAIL_WORK`` and ``address``, the
    e-mail address, phone number or URL itself). Fields without a value are left out by
    upstream and come back empty. An id no person has raises ``NotFoundError``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The person's ``id`` as ``list_persons`` gives it, e.g. ``3``; not its
            number ``nr``.
    """
    person = await api.person_read(org, id)
    return Result(data=person, meta=_meta("person/read.json", {"org": org, "id": id}))


async def list_orders_async(
    org: str,
    *,
    type: OrderType | None = None,
    fiscal_period_id: int | None = None,
    query: str | None = None,
    filter: list[Filter] | None = None,
    category_id: int | None = None,
    status_id: int | None = None,
    person_id: int | None = None,
    group_id: int | None = None,
    only_open: bool = False,
    only_overdue: bool = False,
    only_cost_centers: bool = False,
    only_notes: bool = False,
    sort: str | None = None,
    dir: Direction | None = None,
    start: int = 0,
    limit: int | None = None,
) -> Result[list[Order]]:
    """List an organisation's orders (offers, invoices and the like), newest first.

    Every order comes back with its ``type`` (``SALES`` or ``PURCHASE``), ``nr``
    (e.g. ``RE-2026-101``), ``date``, the partner (``associate_id``,
    ``associate_name``), ``description``, the amounts ``sub_total`` (net), ``tax`` and
    ``total`` (gross), ``open`` (still to be paid), ``status_id`` and ``status_name``,
    and ``is_book`` (whether its status books it to the journal). The items come from
    ``get_order``. Without ``type`` upstream lists both types. Without
    ``fiscal_period_id`` upstream lists the API user's current fiscal period only.
    Without ``limit`` every matching order from ``start`` on is returned; with
    ``limit``, one page of at most ``limit`` orders from ``start``. ``meta.total`` is
    upstream's count of all matching orders, so there is more while
    ``start + limit < meta.total``. Upstream ignores values it does not understand, so
    ``type``, ``dir`` and the filters' ``comparison`` are checked first and a wrong one
    is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        type: ``SALES`` or ``PURCHASE``; both when left out.
        fiscal_period_id: The fiscal period, an ``id`` from ``list_fiscal_periods``,
            e.g. ``1``; the current fiscal period when left out.
        query: Full-text search, e.g. ``"Büromöbel"``.
        filter: Filters that must all match, each with ``comparison`` (``eq``, ``like``,
            ``gt`` or ``lt``; ``like`` when left out), ``field`` (a column of the list,
            e.g. ``nr``) and ``value`` (a text, or a list of texts of which any may
            match), e.g. ``[{"comparison": "eq", "field": "nr", "value": "RE-2026-101"}]``.
        category_id: Only the orders of one order category, e.g. ``4``.
        status_id: Only the orders in one status, e.g. ``12``.
        person_id: Only the orders of one person, an ``id`` from ``list_persons``,
            e.g. ``10``.
        group_id: Only the orders of one order group (dossier), e.g. ``3``.
        only_open: ``true`` for open orders only (a status like Open, not Paid).
        only_overdue: ``true`` for orders past their due date only.
        only_cost_centers: ``true`` for orders with cost centers only.
        only_notes: ``true`` for orders with notes only.
        sort: The column to sort by, e.g. ``date`` (upstream's default) or ``nr``.
        dir: ``DESC`` (upstream's default) or ``ASC``.
        start: The offset of the first order, e.g. ``0`` (the default) or ``50``.
        limit: One page of at most this many orders, e.g. ``50``; every order when
            left out.
    """
    filters = _check_list_arguments(
        dir=dir,
        filter=filter,
        texts={"query": query, "sort": sort},
        choices={"type": (type, ORDER_TYPES)},
        start=start,
        limit=limit,
    )
    arguments: dict[str, Any] = {
        "category_id": category_id,
        "dir": dir,
        "filter": filters,
        "fiscal_period_id": fiscal_period_id,
        "group_id": group_id,
        "only_cost_centers": only_cost_centers or None,
        "only_notes": only_notes or None,
        "only_open": only_open or None,
        "only_overdue": only_overdue or None,
        "person_id": person_id,
        "query": query,
        "sort": sort,
        "status_id": status_id,
        "type": type,
    }

    async def page(offset: int, size: int) -> ListResponse[Order]:
        return await api.order_list(org, **arguments, start=offset, limit=size)

    orders, total = await _offset_pages(page, start=start, limit=limit)
    sent = api.order_list_params(**arguments, start=start, limit=limit)
    meta = _meta("order/list.json", {"org": org, **sent}, total=total)
    return Result(data=orders, meta=meta)


async def get_order_async(org: str, id: int) -> Result[OrderDetail]:
    """Read one order by its id, with its items.

    The order comes back as upstream's read returns it: ``type``, ``nr``, ``date``,
    ``associate_id`` and ``associate_name``, ``description``, ``status_name``, the
    amounts ``sub_total``, ``tax``, ``total``, ``total_to_pay`` and ``paid``, and its
    ``items``, each with ``name``, ``description``, ``quantity``, ``unit_price``,
    ``account_id``, ``tax_code``, and the computed ``net_total``, ``tax_total`` and
    ``gross_total``. An id no order has raises ``NotFoundError``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The order's ``id`` as ``list_orders`` gives it, e.g. ``3``; not its number
            ``nr``.
    """
    order = await api.order_read(org, id)
    return Result(data=order, meta=_meta("order/read.json", {"org": org, "id": id}))


list_fiscal_periods = sync(list_fiscal_periods_async)
list_currencies = sync(list_currencies_async)
list_tax_codes = sync(list_tax_codes_async)
list_accounts = sync(list_accounts_async)
get_account = sync(get_account_async)
list_journal_entries = sync(list_journal_entries_async)
get_journal_entry = sync(get_journal_entry_async)
list_persons = sync(list_persons_async)
get_person = sync(get_person_async)
list_orders = sync(list_orders_async)
get_order = sync(get_order_async)
