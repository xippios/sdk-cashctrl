"""Task functions, the public API: the adapters serve ``__all__`` (conventions §2).

``/add-endpoint`` adds them.

``org: str`` is the first, required parameter of every task: the name of a declared
organisation (``demo``, ``acme``), handed to the endpoint wrappers, which reach CashCtrl
through ``client_for(org)``. No task spans organisations. ``tests/test_tasks.py`` checks
every name in ``__all__``. The one exception is ``list_organisations``, the package's
tenant list (``_tenants.list_task``, ADR-0024): no argument, the declared
organisations' names only, so an agent can form valid calls.

``meta.endpoint`` is the upstream path after ``/api/v1/`` (``account/list.json``),
``meta.tenant`` the organisation the data came from, by name (ADR-0014), and
``meta.request`` holds ``org`` plus the query parameters sent, under upstream's names.
CashCtrl publishes no release time or identifier, so ``published_at`` and ``vintage``
stay empty. Every list task sets ``meta.total`` to upstream's ``total``, its count of the
records matching the request (ADR-0012); it is never computed from ``len(data)``.

The persons a task returns are projections without the personal identifiers ``ssn`` and
``iban`` (ADR-0017, ``_person`` and its neighbours), the locations projections without
their bank account numbers ``iban`` and ``qr_iban`` (``_location``), and the rows of a
report, kept as upstream sends them, lose every key named ``ssn``, ``iban`` or
``qrIban`` in any letter case and at any depth (``_report``); the endpoint wrappers' read
models keep them.

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
from datetime import date, datetime
from typing import Any, TypeGuard, get_args

from pydantic import JsonValue, ValidationError
from pydantic_core import ErrorDetails
from xippios.core import (
    InvalidRequestError,
    Result,
    ResultCap,
    ResultMeta,
    collect,
    paginate_offset,
    sync,
)

from xippios.cashctrl import api
from xippios.cashctrl._client import SOURCE, TENANTS
from xippios.cashctrl._tenants import list_task
from xippios.cashctrl.models import (
    Account,
    AccountCategory,
    AccountDetail,
    Comparison,
    CostCenter,
    Currency,
    CustomField,
    CustomFieldType,
    Direction,
    Filter,
    FiscalPeriod,
    HistoryEntry,
    JournalEntry,
    JournalEntryDetail,
    JournalEntryDetailProjection,
    ListResponse,
    Location,
    LocationProjection,
    Order,
    OrderBookEntry,
    OrderCategory,
    OrderDetail,
    OrderType,
    Person,
    PersonCategory,
    PersonDetail,
    PersonDetailProjection,
    PersonProjection,
    PersonTitle,
    ReportData,
    ReportTreeNode,
    TaxCode,
)

__all__ = [
    "get_account",
    "get_journal_entry",
    "get_order",
    "get_person",
    "get_report_data",
    "get_report_tree",
    "list_account_categories",
    "list_accounts",
    "list_cost_centers",
    "list_currencies",
    "list_custom_fields",
    "list_fiscal_periods",
    "list_history",
    "list_journal_entries",
    "list_locations",
    "list_order_book_entries",
    "list_order_categories",
    "list_orders",
    "list_organisations",
    "list_person_categories",
    "list_person_titles",
    "list_persons",
    "list_tax_codes",
]

# A task named here is Python-only: no tool, no route; the adapters skip it (ADR-0019 decision 4).
BULK_TASKS: frozenset[str] = frozenset()

MCP_CAPS: Mapping[str, ResultCap] = {
    "get_report_data": ResultCap(
        max_bytes=131_072,
        note=(
            "narrow the period (fiscal_period, or start_date and end_date) or read a "
            "smaller report of get_report_tree to see the rest"
        ),
    ),
    "list_cost_centers": ResultCap(
        note="narrow the list with query, filter, category_id or only_active to see the rest"
    ),
    "list_custom_fields": ResultCap(
        max_rows=500,
        max_bytes=131_072,
        note="the list is every custom field of the type and cannot be narrowed further",
    ),
    "list_history": ResultCap(
        note=(
            "narrow the history with order_id, person_id, statement_id, query or filter, "
            "or page it with limit"
        )
    ),
}
"""Per-tool MCP result caps (ADR-0016), which ``mcp.py`` passes to ``build_server``.

Every other tool keeps the family default, 200 rows or 64 KB. ``list_custom_fields`` has
no filter or paging beyond its ``type`` and a write needs a type's custom fields whole
(``customField<id>``), so its bound is raised to 500 rows or 128 KB. A report is read
whole: ``get_report_data``'s result is no list, so the cap replaces one over its bound
with a note and a preview. The demo organisation's balance sheet of 2025, 25 rows with
its totals, is about 17 KB, some 650 bytes a row, so 64 KB holds a report of about 100
rows and 128 KB one of about 200; the note names the period parameters (a raised bound
for a tool that is no reference list: row 127). ``list_cost_centers`` keeps the default
bound and names its filters, and so does ``list_history``, whose whole log may hold far
more than the bound: a cut is resumed at ``start`` (ADR-0016, amended 2026-10-27), or
narrowed to one record's history.
"""

DIRECTIONS: tuple[str, ...] = get_args(Direction)
"""The values of ``dir`` on every list that documents it: ``ASC``, ``DESC``."""
COMPARISONS: tuple[str, ...] = get_args(Comparison)
"""The values of ``comparison`` in a ``filter`` item: ``eq``, ``like``, ``gt``, ``lt``."""
ORDER_TYPES: tuple[str, ...] = get_args(OrderType)
"""The values of ``type`` on ``order/list.json`` and ``order/category/list.json``."""
CUSTOM_FIELD_TYPES: tuple[str, ...] = get_args(CustomFieldType)
"""The values of ``type`` on ``customfield/list.json``, the modules: ``JOURNAL``, ``PERSON``, ..."""
PAGE_SIZE = 100
"""Records per request when a list task collects every page.

Upstream's documented default for ``limit`` on the journal, person and order lists
("Defaults to 100."), sent explicitly so the page size never depends on that default.
"""


def _meta(
    org: str, endpoint: str, params: dict[str, Any], *, total: int | None = None
) -> ResultMeta:
    """``meta`` of a task's result: ``org`` as the tenant and first in ``request``."""
    return ResultMeta(
        source=SOURCE,
        endpoint=endpoint,
        request={"org": org, **params},
        total=total,
        tenant=org,
    )


def _person(person: Person) -> PersonProjection:
    """A ``person/list.json`` entry without ``ssn`` and ``iban`` (ADR-0017)."""
    return PersonProjection.project(person)


def _person_detail(person: PersonDetail) -> PersonDetailProjection:
    """A ``person/read.json`` record without ``ssn`` and its bank accounts' ``iban`` (ADR-0017).

    The projection drops each ``iban`` itself (its validator), so nothing is overridden.
    """
    return PersonDetailProjection.project(person)


def _journal_entry_detail(entry: JournalEntryDetail) -> JournalEntryDetailProjection:
    """A ``journal/read.json`` record whose ``associates`` are projected (ADR-0017)."""
    associates = [_person_detail(person) for person in entry.associates]
    return JournalEntryDetailProjection.project(entry, associates=associates)


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

    Pages are cut by offset at request time: if the list changes while every page is
    collected, a record added or removed before the next offset shifts it by one, and a
    record is repeated or skipped. Upstream offers no cursor.

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
    meta = _meta(org, "fiscalperiod/list.json", {}, total=response.total)
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
    meta = _meta(org, "currency/list.json", {}, total=response.total)
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
    return Result(data=response.data, meta=_meta(org, "tax/list.json", {}, total=response.total))


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
    currency. Without parameters every account is listed; narrow a large chart of
    accounts with ``query``, ``filter`` or ``only_active``.
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
    meta = _meta(org, "account/list.json", sent, total=response.total)
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
    return Result(data=account, meta=_meta(org, "account/read.json", {"id": id}))


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
    (``tax_code``, ``tax_rate``) and its ``type`` (``MANUAL``, ``COLLECTIVE``, or
    ``ORDER`` with ``order_id`` for one an order booked, which only that order changes).
    A collective entry has ``items_count`` lines, which ``get_journal_entry`` returns.
    Pass ``fiscal_period_id`` (an id from ``list_fiscal_periods``) for a reproducible
    answer; without it upstream uses the API user's current period, server-side state
    that ``fiscalperiod/switch.json`` changes, and ``meta.request`` does not show which
    period answered.

    Paging: with ``limit``, one page of at most ``limit`` entries from ``start``; without
    it, every matching entry from ``start`` on. ``meta.total`` is upstream's count of all
    matching entries. The next page starts at ``start`` plus the number of records
    received, which can be fewer than ``limit``: never advance by ``limit``. MCP agents
    should always pass ``limit`` (about 20): collecting a large journal costs about 1 s
    per 100 entries. Offset pages over a list that changes meanwhile can repeat or skip
    entries: an entry added or removed shifts every later page by one.

    Upstream ignores values it does not understand, so ``dir`` and the filters'
    ``comparison`` are checked first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        fiscal_period_id: The fiscal period, an ``id`` from ``list_fiscal_periods``,
            e.g. ``2``. When left out, upstream uses the API user's current period,
            which ``meta.request`` does not show.
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
        start: The offset of the first entry, ``0`` (the default) for the first page;
            for the next, ``start`` plus the number of entries received, e.g. ``20``.
        limit: One page of at most this many entries, e.g. ``20``; every entry when
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
    meta = _meta(org, "journal/list.json", sent, total=total)
    return Result(data=entries, meta=meta)


async def get_journal_entry_async(org: str, id: int) -> Result[JournalEntryDetailProjection]:
    """Read one journal entry by its id, with its lines, bookings and partners.

    The entry comes back as upstream's read returns it: ``date_added``, ``title``,
    ``reference``, ``amount``, ``debit_id``, ``credit_id``, the tax code, and three
    lists: ``items``, the lines of a collective entry (each with ``account_id``,
    ``debit`` or ``credit``, ``description`` and ``associate_id``; empty for a simple
    entry), ``rows``, the bookings per account with tax rows apart (``is_tax``), and
    ``associates``, the records of the persons the entry names, as ``get_person`` returns
    them, without ``ssn`` and ``iban``. An id no entry has raises ``NotFoundError``.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The entry's ``id`` as ``list_journal_entries`` gives it, e.g. ``11``.
    """
    entry = _journal_entry_detail(await api.journal_read(org, id))
    return Result(data=entry, meta=_meta(org, "journal/read.json", {"id": id}))


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
) -> Result[list[PersonProjection]]:
    """List an organisation's persons, its customers, vendors and other contacts, by name.

    Every person comes back with its ``name``, ``nr`` (e.g. ``P-00001``), ``company``,
    ``first_name`` and ``last_name``, its roles (``is_customer``, ``is_vendor``,
    ``is_employee``, ``is_insurance``, ``is_family``), ``category_id`` and
    ``category_name``, ``is_inactive``, the main address flattened (``address``,
    ``zip``, ``city``, ``country``) and ``email_work``. CashCtrl creates insurance
    records of its own (``is_insurance``). Addresses and contacts in full come from
    ``get_person``. The personal identifiers ``ssn`` and ``iban`` are left out.

    Paging: with ``limit``, one page of at most ``limit`` persons from ``start``; without
    it, every matching person from ``start`` on. ``meta.total`` is upstream's count of
    all matching persons. The next page starts at ``start`` plus the number of records
    received, which can be fewer than ``limit``: never advance by ``limit``. MCP agents
    should always pass ``limit`` (about 20): collecting many persons costs about 1 s per
    100. Offset pages over a list that changes meanwhile can repeat or skip persons: a
    person added or removed shifts every later page by one.

    Upstream ignores values it does not understand, so ``dir`` and the filters'
    ``comparison`` are checked first and a wrong one is refused.

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
        start: The offset of the first person, ``0`` (the default) for the first page;
            for the next, ``start`` plus the number of persons received, e.g. ``20``.
        limit: One page of at most this many persons, e.g. ``20``; every person when
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
    meta = _meta(org, "person/list.json", sent, total=total)
    return Result(data=[_person(person) for person in persons], meta=meta)


async def get_person_async(org: str, id: int) -> Result[PersonDetailProjection]:
    """Read one person by its id, with its addresses and contacts.

    The person comes back as upstream's read returns it: ``name``, ``nr``, ``company``,
    ``first_name``, ``last_name``, the roles (``is_customer``, ``is_vendor``, ...),
    ``category_id`` and ``category_name``, ``language``, and the lists ``addresses``
    (each with ``type`` such as ``MAIN``, ``address``, ``zip``, ``city``, ``country``)
    and ``contacts`` (each with ``type`` such as ``EMAIL_WORK`` and ``address``, the
    e-mail address, phone number or URL itself). Fields without a value are left out by
    upstream and come back empty. The personal identifiers ``ssn`` and each bank
    account's ``iban`` are left out. An id no person has raises ``NotFoundError``; that
    answer is assumed for persons, observed for accounts, currencies and the journal.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The person's ``id`` as ``list_persons`` gives it, e.g. ``3``; not its
            number ``nr``.
    """
    person = _person_detail(await api.person_read(org, id))
    return Result(data=person, meta=_meta(org, "person/read.json", {"id": id}))


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
    ``get_order``. Without ``type`` upstream lists both types. Pass
    ``fiscal_period_id`` (an id from ``list_fiscal_periods``) for a reproducible answer;
    without it upstream uses the API user's current period, server-side state that
    ``fiscalperiod/switch.json`` changes, and ``meta.request`` does not show which period
    answered.

    Paging: with ``limit``, one page of at most ``limit`` orders from ``start``; without
    it, every matching order from ``start`` on. ``meta.total`` is upstream's count of all
    matching orders. The next page starts at ``start`` plus the number of records
    received, which can be fewer than ``limit``: never advance by ``limit``. MCP agents
    should always pass ``limit`` (about 20): collecting many orders costs about 1 s per
    100. Offset pages over a list that changes meanwhile can repeat or skip orders: an
    order added or removed shifts every later page by one.

    Upstream ignores values it does not understand, so ``type``, ``dir`` and the
    filters' ``comparison`` are checked first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        type: ``SALES`` or ``PURCHASE``; both when left out.
        fiscal_period_id: The fiscal period, an ``id`` from ``list_fiscal_periods``,
            e.g. ``1``. When left out, upstream uses the API user's current period,
            which ``meta.request`` does not show.
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
        start: The offset of the first order, ``0`` (the default) for the first page;
            for the next, ``start`` plus the number of orders received, e.g. ``20``.
        limit: One page of at most this many orders, e.g. ``20``; every order when
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
    meta = _meta(org, "order/list.json", sent, total=total)
    return Result(data=orders, meta=meta)


async def get_order_async(org: str, id: int) -> Result[OrderDetail]:
    """Read one order by its id, with its items.

    The order comes back as upstream's read returns it: ``type``, ``nr``, ``date``,
    ``associate_id`` and ``associate_name``, ``description``, ``status_name``, the
    amounts ``sub_total``, ``tax``, ``total``, ``total_to_pay`` and ``paid``, and its
    ``items``, each with ``name``, ``description``, ``quantity``, ``unit_price``,
    ``account_id``, ``tax_code``, and the computed ``net_total``, ``tax_total`` and
    ``gross_total``. An id no order has raises ``NotFoundError``; that answer is assumed
    for orders, observed for accounts, currencies and the journal.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The order's ``id`` as ``list_orders`` gives it, e.g. ``3``; not its number
            ``nr``.
    """
    order = await api.order_read(org, id)
    return Result(data=order, meta=_meta(org, "order/read.json", {"id": id}))


async def list_order_book_entries_async(org: str, order_id: int) -> Result[list[OrderBookEntry]]:
    """List the book entries of one order: the journal entries it booked, and its payments.

    These are "all the journal book entries that are created for an order (e.g. an
    invoice or a credit note), either automatically from items or manually by the user,
    like payments for example". Every entry comes back with its ``type`` (``GENERATED``
    for one booked from the items), ``date``, ``description``, ``reference``, ``amount``
    (gross) with ``net_amount`` and ``tax_amount``, the accounts it books
    (``debit_id`` and ``debit_name``, ``credit_id`` and ``credit_name``), ``tax_id``,
    and ``rows``, the bookings per account with the tax rows apart (``is_tax``), as
    ``get_journal_entry`` returns them. An order in a status that books nothing (a
    draft) has none; ``is_book`` in ``get_order`` says whether its status books.
    ``meta.total`` is upstream's count. What an id no order has answers was not observed.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        order_id: The order's ``id`` as ``list_orders`` gives it, e.g. ``5``; not its
            number ``nr``. Sent as upstream's ``id``.
    """
    response = await api.order_bookentry_list(org, order_id)
    meta = _meta(org, "order/bookentry/list.json", {"id": order_id}, total=response.total)
    return Result(data=response.data, meta=meta)


async def list_history_async(
    org: str,
    *,
    order_id: int | None = None,
    person_id: int | None = None,
    statement_id: int | None = None,
    query: str | None = None,
    filter: list[Filter] | None = None,
    dir: Direction | None = None,
    start: int = 0,
    limit: int | None = None,
) -> Result[list[HistoryEntry]]:
    """List an organisation's history, the audit log of its changes, newest first.

    Every entry comes back with ``created`` (when the change was made), ``created_by``
    (who made it; an API user shows as ``API:`` and the first four characters of its
    key), ``type`` (the module, e.g. ``ORDER``), ``change_type`` (``CREATE`` and
    ``STATUS`` were seen, ``UPDATE`` too on 2026-10-27, though in no fixture), the
    record it concerns (``order_id``, ``person_id``, ``statement_id``) and ``message``,
    upstream's text of the change (``Rechnung 'EK-2026-001' created.``). ``order_id``,
    ``person_id`` or ``statement_id`` narrow it to one record's history; the history of
    an order that was deleted is not listed (observed: none, a minute after the delete).

    Paging: with ``limit``, one page of at most ``limit`` entries from ``start``; without
    it, every matching entry from ``start`` on, which for a whole organisation is long:
    pass ``limit`` (about 20), or one record's id. ``meta.total`` is upstream's count of
    all matching entries. The next page starts at ``start`` plus the number of entries
    received, which can be fewer than ``limit``: never advance by ``limit``. Offset pages
    over a log that grows meanwhile can repeat entries: one added shifts every later page
    by one. Upstream ignores values it does not understand, so ``dir`` and the filters'
    ``comparison`` are checked first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        order_id: Only the history of one order, an ``id`` from ``list_orders``,
            e.g. ``5``.
        person_id: Only the history of one person, an ``id`` from ``list_persons``,
            e.g. ``3``.
        statement_id: Only the history of one salary statement, its id, e.g. ``4``.
        query: Full-text search, e.g. ``"EK-2026-001"``.
        filter: Filters that must all match, each with ``comparison`` (``eq``, ``like``,
            ``gt`` or ``lt``; ``like`` when left out), ``field`` (a column of the list,
            e.g. ``changeType``) and ``value`` (a text, or a list of texts of which any
            may match), e.g.
            ``[{"comparison": "eq", "field": "changeType", "value": "CREATE"}]``.
        dir: ``DESC`` (upstream's default, newest first) or ``ASC``.
        start: The offset of the first entry, ``0`` (the default) for the first page;
            for the next, ``start`` plus the number of entries received, e.g. ``20``.
        limit: One page of at most this many entries, e.g. ``20``; every entry when
            left out.
    """
    filters = _check_list_arguments(
        dir=dir, filter=filter, texts={"query": query}, start=start, limit=limit
    )
    arguments: dict[str, Any] = {
        "dir": dir,
        "filter": filters,
        "order_id": order_id,
        "person_id": person_id,
        "query": query,
        "statement_id": statement_id,
    }

    async def page(offset: int, size: int) -> ListResponse[HistoryEntry]:
        return await api.history_list(org, **arguments, start=offset, limit=size)

    entries, total = await _offset_pages(page, start=start, limit=limit)
    sent = api.history_list_params(**arguments, start=start, limit=limit)
    meta = _meta(org, "history/list.json", sent, total=total)
    return Result(data=entries, meta=meta)


async def list_order_categories_async(
    org: str, *, type: OrderType | None = None, fiscal_period_id: int | None = None
) -> Result[list[OrderCategory]]:
    """List an organisation's order categories of one type, with their statuses.

    An order category is a kind of document (offer, order confirmation, delivery note,
    invoice, reminder, credit note, purchase order) with its own statuses and settings.
    Every category comes back with its ``id`` (the ``category_id`` of ``create_order``),
    ``name_singular`` and ``name_plural`` (localised, ``<values><de>Rechnung</de>
    <en>Invoice</en>...</values>``), ``type``, ``account_id`` (the debtors or creditors
    account its orders book to), ``sequence_nr_id`` (the sequence that numbers its
    orders; without one, ``create_order`` needs ``nr``), ``due_days``, ``is_inactive``,
    and ``status``: each status's ``id`` (the ``status_id`` of ``create_order``),
    ``name`` (Draft, Open, Paid, ...), ``is_book`` (whether orders in it book journal
    entries) and ``is_closed``. Upstream lists ``SALES`` when ``type`` is left out.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        type: ``SALES`` (upstream's default) or ``PURCHASE``.
        fiscal_period_id: The fiscal period upstream counts the orders in, an ``id`` from
            ``list_fiscal_periods``, e.g. ``1``; the current period when left out.
    """
    _check_list_arguments(choices={"type": (type, ORDER_TYPES)})
    arguments: dict[str, Any] = {"fiscal_period_id": fiscal_period_id, "type": type}
    sent = api.order_category_list_params(**arguments)
    response = await api.order_category_list(org, **arguments)
    meta = _meta(org, "order/category/list.json", sent, total=response.total)
    return Result(data=response.data, meta=meta)


async def list_custom_fields_async(org: str, type: CustomFieldType) -> Result[list[CustomField]]:
    """List an organisation's custom fields of one module, the fields it added to its records.

    Every custom field of ``type`` comes back with its ``id``, its ``data_type``
    (``TEXT``, ``TEXTAREA``, ``CHECKBOX``, ``DATE``, ``COMBOBOX``, ``NUMBER``, ``ACCOUNT``
    or ``PERSON``), the labels it is shown with (``row_label``, ``field_label``,
    localised as ``<values><de>...</de></values>``), ``is_inactive``, ``is_multi`` and,
    for a ``COMBOBOX``, the ``values`` to choose from. A write tool sets a custom field
    as ``customField<id>`` in its ``custom`` mapping, e.g. ``{"customField3": "Projekt
    A"}``: ``JOURNAL`` for ``create_journal_entry``, ``PERSON`` for ``create_person``,
    ``ORDER`` for ``create_order``. ``meta.total`` is upstream's count. ``type`` is
    checked first, and a value outside the documented set is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        type: The module whose custom fields to list: ``JOURNAL``, ``ACCOUNT``,
            ``INVENTORY_ARTICLE``, ``INVENTORY_ASSET``, ``ORDER``, ``PERSON``, ``FILE`` or
            ``SALARY_STATEMENT``, e.g. ``PERSON``.
    """
    if type not in CUSTOM_FIELD_TYPES:
        allowed = ", ".join(CUSTOM_FIELD_TYPES)
        raise InvalidRequestError(f"type must be one of {allowed}, not {type!r}", source=SOURCE)
    response = await api.customfield_list(org, type)
    sent = api.customfield_list_params(type)
    meta = _meta(org, "customfield/list.json", sent, total=response.total)
    return Result(data=response.data, meta=meta)


async def list_person_categories_async(org: str) -> Result[list[PersonCategory]]:
    """List an organisation's person categories, the groups its persons are filed in.

    Every category comes back with its ``id`` (the ``category_id`` of ``list_persons``,
    ``create_person`` and ``update_person``), its ``name`` (localised,
    ``<values><de>Kunden</de><en>Customers</en>...</values>``), ``parent_id`` (``None``
    at the top level), ``sequence_nr_id`` (the sequence that numbers its persons) and
    ``discount_percentage``. CashCtrl creates four in a new organisation: customers,
    vendors, employees and insurances.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.person_category_list(org)
    meta = _meta(org, "person/category/list.json", {}, total=response.total)
    return Result(data=response.data, meta=meta)


async def list_person_titles_async(org: str) -> Result[list[PersonTitle]]:
    """List an organisation's titles, the forms of address a person can be given.

    Every title comes back with its ``id`` (the ``title_id`` of ``create_person`` and
    ``update_person``), its ``name`` (localised, ``<values><de>Herr</de><en>Mr.</en>
    ...</values>``), ``gender`` (``MALE``, ``FEMALE`` or empty) and ``sentence``, the
    letter salutation (``<values><de>Sehr geehrter Herr</de>...</values>``).

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.person_title_list(org)
    meta = _meta(org, "person/title/list.json", {}, total=response.total)
    return Result(data=response.data, meta=meta)


async def list_account_categories_async(org: str) -> Result[list[AccountCategory]]:
    """List an organisation's account categories, the groups of its chart of accounts.

    Every category comes back flat, with its ``id`` (the ``category_id`` an account
    carries and ``list_accounts`` takes), ``number`` (``"1"``, ``"10"``, ``"100"``, as
    text), ``name`` (localised as ``<values><de>...</de></values>``, plain for the five
    top-level categories), ``full_name`` (number and name), ``account_class``
    (``ASSET``, ``LIABILITY``, ``EXPENSE``, ``REVENUE`` or ``BALANCE``) and
    ``parent_id``, the category it belongs to: ``None`` for the five top-level ones,
    which are ``is_system``. The ``parent_id`` links are the hierarchy.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.account_category_list(org)
    meta = _meta(org, "account/category/list.json", {}, total=response.total)
    return Result(data=response.data, meta=meta)


async def list_cost_centers_async(
    org: str,
    *,
    query: str | None = None,
    filter: list[Filter] | None = None,
    category_id: int | None = None,
    only_active: bool = False,
    only_notes: bool = False,
    sort: str | None = None,
    dir: Direction | None = None,
) -> Result[list[CostCenter]]:
    """List an organisation's cost centers, the units amounts can be allocated to.

    Every matching cost center comes back with its ``id`` (the ``to_cost_center_id`` of
    an allocation in ``create_journal_entry``, ``update_journal_entry`` and the items of
    ``create_order``), ``number``, ``name`` (localised), ``category_id``,
    ``is_inactive``, ``notes`` and its targets ``target_min`` and ``target_max``. No
    cost center has been observed yet (the demo organisation has none), so balances the
    list may carry are not returned. ``meta.total`` is upstream's count. Upstream ignores
    values it does not understand, so ``dir`` and the filters' ``comparison`` are checked
    first and a wrong one is refused.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        query: Full-text search, e.g. ``"Projekt"``.
        filter: Filters that must all match, each with ``comparison`` (``eq``, ``like``,
            ``gt`` or ``lt``; ``like`` when left out), ``field`` (a column of the list,
            e.g. ``number``) and ``value`` (a text, or a list of texts of which any may
            match), e.g. ``[{"comparison": "eq", "field": "number", "value": "100"}]``.
        category_id: Only the cost centers of one cost center category, e.g. ``1``.
        only_active: ``true`` to leave out inactive cost centers.
        only_notes: ``true`` to list only cost centers with notes.
        sort: The column to sort by, e.g. ``number`` (upstream's default) or ``name``.
        dir: ``ASC`` (upstream's default) or ``DESC``.
    """
    filters = _check_list_arguments(dir=dir, filter=filter, texts={"query": query, "sort": sort})
    arguments: dict[str, Any] = {
        "category_id": category_id,
        "dir": dir,
        "filter": filters,
        "only_active": only_active or None,
        "only_notes": only_notes or None,
        "query": query,
        "sort": sort,
    }
    sent = api.account_costcenter_list_params(**arguments)
    response = await api.account_costcenter_list(org, **arguments)
    meta = _meta(org, "account/costcenter/list.json", sent, total=response.total)
    return Result(data=response.data, meta=meta)


def _location(location: Location) -> LocationProjection:
    """A ``location/list.json`` entry without ``iban`` and ``qr_iban`` (ADR-0017)."""
    return LocationProjection.project(location)


async def list_locations_async(org: str) -> Result[list[LocationProjection]]:
    """List an organisation's locations: its headquarters, branches and other sites.

    Every location comes back with its ``id`` (the ``location_id`` of ``create_person``
    and ``update_person``, an employee's workplace), ``name``, ``type`` (``MAIN`` for
    the headquarters, ``BRANCH``, ``STORAGE`` or ``OTHER``), the company name
    ``org_name``, the address (``address``, ``zip``, ``city``, ``canton``, ``country``,
    and ``full_address`` as printed), the contacts (``email``, ``phone_main``, ``url``),
    ``vat_uid``, ``bur_nr``, ``bank_account_id`` and ``is_inactive``. The bank account
    numbers ``iban`` and ``qr_iban`` are left out.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.location_list(org)
    meta = _meta(org, "location/list.json", {}, total=response.total)
    return Result(data=[_location(location) for location in response.data], meta=meta)


async def get_report_tree_async(org: str) -> Result[list[ReportTreeNode]]:
    """Get an organisation's report tree: its report collections and the reports in them.

    Every top-level node comes back with its children in ``data``. A collection
    (``Jahresbericht``, ``Mehrwertsteuer``, ...) holds report elements; an element, a
    ``leaf``, is one report: its ``element_id`` is the ``element_id`` of
    ``get_report_data``, its ``type`` the kind of report (``BALANCE`` for the balance
    sheet, ``PLS`` for profit and loss, ``OPEN_DEBTORS``, ``VAT_SETTLEMENT``, ...) and
    its ``text`` its name. ``id`` is the tree's own key (``element-1``), not an id other
    tools take. ``meta.total`` is upstream's count of the top-level nodes, not of every
    report.

    Args:
        org: A declared organisation name, e.g. ``demo``.
    """
    response = await api.report_tree(org)
    meta = _meta(org, "report/tree.json", {}, total=response.total)
    return Result(data=response.data, meta=meta)


_IDENTIFIER_KEYS = frozenset({"ssn", "iban", "qriban"})
"""Keys dropped from a report's raw rows, compared in lower case (ADR-0017, row 123)."""


def _without_identifiers(value: JsonValue) -> JsonValue:
    """``value`` without a key named ``ssn``, ``iban`` or ``qrIban``, in any case, at any depth."""
    if isinstance(value, dict):
        return {
            key: _without_identifiers(item)
            for key, item in value.items()
            if key.lower() not in _IDENTIFIER_KEYS
        }
    if isinstance(value, list):
        return [_without_identifiers(item) for item in value]
    return value


def _report(report: ReportData) -> ReportData:
    """``report`` without the identifier keys in its rows and ``properties`` (ADR-0017).

    The rows stay upstream's JSON (``JsonValue``); dropping a nested identifier is the
    projection rule's parsing only (ADR-0003, amendment 2026-10-26).
    """
    return ReportData.project(
        report,
        data=[_without_identifiers(row) for row in report.data],
        properties=_without_identifiers(report.properties),
    )


def _check_report_arguments(
    *,
    element_id: object,
    fiscal_period: object,
    start_date: object,
    end_date: object,
    language: object,
    sort: object,
) -> None:
    """Refuse a ``get_report_data`` call upstream would answer for another period (ADR-0007).

    ``docs/upstream/report.md``, "Read JSON data": ``fiscalPeriod`` "overrides the
    ``startDate`` and ``endDate`` parameter, as these are derived from the fiscal
    period", so upstream would silently ignore dates given with it: the two forms are
    refused together. The rest is for Python callers, whose arguments nothing else
    validates (the MCP and HTTP adapters refuse a wrong type before the task runs): the
    ids are whole numbers, the dates ``date`` objects (not a ``datetime``, whose text
    would carry a time), ``language`` and ``sort`` strings. Whether one date may be
    given without the other, and what a start after the end answers, is not documented,
    so neither is checked.

    Raises:
        InvalidRequestError: Naming every problem found.
    """
    problems: list[str] = []
    if not _whole(element_id):
        problems.append(f"element_id must be a whole number, not {element_id!r}")
    if fiscal_period is not None and not _whole(fiscal_period):
        problems.append(f"fiscal_period must be a whole number, not {fiscal_period!r}")
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None and (not isinstance(value, date) or isinstance(value, datetime)):
            problems.append(f"{name} must be a date (YYYY-MM-DD), not {type(value).__name__}")
    for name, value in (("language", language), ("sort", sort)):
        if value is not None and not isinstance(value, str):
            problems.append(f"{name} must be a string, not {type(value).__name__}")
    if fiscal_period is not None and (start_date is not None or end_date is not None):
        problems.append(
            "give fiscal_period or start_date and end_date, not both: upstream derives "
            "the dates from the fiscal period and would ignore the ones given"
        )
    if problems:
        raise InvalidRequestError("; ".join(problems), source=SOURCE)


async def get_report_data_async(
    org: str,
    element_id: int,
    *,
    fiscal_period: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    language: str | None = None,
    sort: str | None = None,
) -> Result[ReportData]:
    """Read one report's data for a period, such as a balance sheet or a profit and loss.

    The report is the element ``element_id`` of ``get_report_tree``, for the fiscal
    period ``fiscal_period`` or for ``start_date`` to ``end_date``; passing the fiscal
    period and a date is refused before anything is sent, since upstream derives the
    dates from the period and would ignore the ones given. Pass one of the two for a
    reproducible answer: which period upstream uses without either is not documented.

    The data comes back as upstream sends it, since the documentation gives no schema
    and the rows differ by report type: ``data``, the rows, each with its child rows in
    ``data`` (a balance sheet's are categories and accounts, with ``text``,
    ``accountId`` and the amounts ``openingAmount``, ``endAmount`` and more; a total is
    a row of its own); ``properties``, among them the ``columns`` the report shows (each
    a ``title`` and the row field it shows, ``dataIndex``); and ``total``, upstream's
    count of the top-level rows, which ``meta.total`` repeats. Rows keep upstream's
    camelCase names, and amounts are JSON numbers.

    Payroll and people reports (``SALARY_LIST``, ``SETTLEMENT``,
    ``WITHHOLDING_TAX_SETTLEMENT``, ``REVENUE_BY_PERSON``, ``OPEN_DEBTORS``, ...) carry
    personal data under names the documentation does not give. Every key named ``ssn``,
    ``iban`` or ``qrIban``, in any letter case and at any depth, is dropped before the
    data comes back; nothing else is. The salary module is outside what this package
    covers, but its reports are not refused: the answer does not say which type of
    report it is.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        element_id: The report, an ``element_id`` from ``get_report_tree``, e.g. ``1``.
        fiscal_period: The fiscal period, an ``id`` from ``list_fiscal_periods``, e.g.
            ``2``; not together with ``start_date`` or ``end_date``.
        start_date: The first day of the report period, ``YYYY-MM-DD``, e.g.
            ``2025-01-01``.
        end_date: The last day of the report period, ``YYYY-MM-DD``, e.g.
            ``2025-12-31``.
        language: The language of the report, e.g. ``en``; upstream lists no values,
            and the language codes ``de``, ``fr``, ``it`` and ``en`` are assumed.
        sort: The column to sort the rows by, a ``dataIndex`` of
            ``properties.columns``, e.g. ``text``.
    """
    _check_report_arguments(
        element_id=element_id,
        fiscal_period=fiscal_period,
        start_date=start_date,
        end_date=end_date,
        language=language,
        sort=sort,
    )
    arguments: dict[str, Any] = {
        "end_date": end_date,
        "fiscal_period": fiscal_period,
        "language": language,
        "sort": sort,
        "start_date": start_date,
    }
    sent = api.report_element_data_params(element_id, **arguments)
    report = _report(await api.report_element_data(org, element_id, **arguments))
    meta = _meta(org, "report/element/data.json", sent, total=report.total)
    return Result(data=report, meta=meta)


LIST_ORGANISATIONS_DOC = """List the organisations this server can reach, by name.

On a server that serves every declared organisation, every other tool takes one of these
names as ``org`` to choose the organisation it works on, e.g. ``demo`` or ``acme``; on a
server started with ``--org`` the tools act on that one organisation and this list shows
it alone. Only names come back, never a subdomain, a key or another value; an empty list
means that no organisation is declared where the server runs.
"""

list_organisations = list_task(TENANTS, name="list_organisations", doc=LIST_ORGANISATIONS_DOC)
"""The declared organisations' names (ADR-0024); ``meta.tenant`` is ``None``."""

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
list_order_book_entries = sync(list_order_book_entries_async)
list_history = sync(list_history_async)
list_order_categories = sync(list_order_categories_async)
list_custom_fields = sync(list_custom_fields_async)
list_person_categories = sync(list_person_categories_async)
list_person_titles = sync(list_person_titles_async)
list_account_categories = sync(list_account_categories_async)
list_cost_centers = sync(list_cost_centers_async)
list_locations = sync(list_locations_async)
get_report_tree = sync(get_report_tree_async)
get_report_data = sync(get_report_data_async)
