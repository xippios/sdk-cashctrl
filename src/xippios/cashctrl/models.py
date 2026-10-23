"""Pydantic models mirroring CashCtrl payloads.

One model per upstream object, subclassing ``xippios.core.UpstreamModel``, with fields
named as upstream names them in snake_case. Where upstream spells a field differently
(``isCurrent``), ``Field(validation_alias=...)`` accepts that spelling on input; never
``alias=``, which the adapters would serialise, handing agents the upstream spelling. So
results serialise under the snake_case names in Python, over MCP and over HTTP alike
(``is_current``, ``end_amount``), the same names the tool arguments use. Within-source
hygiene only: dates become ``datetime.date``/``datetime``, numbers become ``int`` or
``Decimal`` (ADR-0008: JSON numbers on the wire). No cross-source normalisation
(ADR-0003): an upstream concept stays an upstream concept, and nothing is renamed or
computed.

``docs/upstream/`` shows no response bodies. Field types come from the create and update
parameter tables where they describe the field, and from the answers recorded against the
demo organisation on 2026-10-23 where they do not; the latter are named in each model's
docstring as typed from observation. Two demo organisations answered that day: the
first, a copy of real books, since retired, and the synthetic one seeded by
``scripts/seed_demo.py``; the committed fixtures come from the synthetic one only. What
those answers showed:

- Timestamps come as ``YYYY-MM-DD HH:MM:SS.f`` (``2026-10-23 07:06:39.0``) without a zone;
  they are kept as naive ``datetime``.
- Dates come in the same form (``2025-12-31 23:59:59.0`` for the end of a fiscal period);
  the date part is kept (``2025-12-31``), the documented ``YYYY-MM-DD`` of the parameters.
  ``lastEntryDate``, which no table describes, stays a ``datetime``: the first demo
  organisation sent it with a time of day (``00:00:02``), the synthetic one at midnight
  (``2025-12-15 00:00:00.0``).
- Localised texts (``name``, ``description``) arrive as upstream stores them, plain or as
  ``<values><de>...</de><en>...</en></values>``, and are kept verbatim.
- A field that may be absent or ``null`` is ``X | None`` and defaults to ``None``. A
  field only ever seen as ``null`` or ``[]`` whose shape no table describes is kept as
  the JSON upstream sends (``JsonValue``) rather than guessed.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BeforeValidator, ConfigDict, Field, JsonValue
from xippios.core import UpstreamModel

__all__ = [
    "Account",
    "AccountDetail",
    "Comparison",
    "Currency",
    "Direction",
    "Filter",
    "FiscalPeriod",
    "ListResponse",
    "ReadResponse",
    "TaxCode",
    "TaxComponent",
    "TaxRate",
]


def _date_part(value: object) -> object:
    """``"2024-12-31 23:59:59.0"`` → ``"2024-12-31"``: upstream sends dates as timestamps."""
    if isinstance(value, str) and len(value) > 10 and value[10] in " T":
        return value[:10]
    return value


UpstreamDate = Annotated[date, BeforeValidator(_date_part)]
"""A date upstream sends with a time of day; the date part is kept."""

Comparison = Literal["eq", "like", "gt", "lt"]
"""The values of ``comparison`` in a ``filter`` item: "Possible values: eq, like, gt, lt"."""

Direction = Literal["ASC", "DESC"]
"""The values of ``dir`` on every list that documents it: "Possible values: ASC, DESC"."""


class ListResponse[T](UpstreamModel):
    """The answer of a ``list.json`` operation: ``{"total": 3, "data": [...]}``.

    Observed on 2026-10-23 against the demo organisation (``docs/upstream/`` shows no list
    response): there is no ``success`` key. For ``fiscalperiod``, ``currency``, ``tax`` and
    ``account``, which document no ``start`` or ``limit``, one answer carries the whole
    collection: ``total`` equalled ``len(data)`` for each.

    Attributes:
        total: Upstream's count of the matching records.
        data: The records.
    """

    total: int
    data: list[T]


class ReadResponse[T](UpstreamModel):
    """The answer of a ``read.json`` operation: ``{"success": true, "data": {...}}``.

    Observed on 2026-10-23 against the demo organisation. A refusal (``"success": false``)
    never gets here: ``_client.classify`` raises it.

    Attributes:
        success: ``True``.
        data: The record.
    """

    success: bool
    data: T


class FiscalPeriod(UpstreamModel):
    """One fiscal period, an entry of ``fiscalperiod/list.json`` (``docs/upstream/meta.md``).

    ``name``, ``start``, ``end``, ``salary_start`` and ``salary_end`` are typed from the
    create and update tables. Typed from observation: ``short_name`` (only ``null`` seen),
    ``last_entry_date`` (a ``datetime``: it is undocumented and was seen with a time of
    day), the ``*_month_ids`` lists of months as ``YYYY-MM`` strings, the
    flags ``closed``, ``current``, ``salary_closed``, ``transient`` and their ``is_*``
    twins (both spellings come in every record), and the ``created*``/``last_updated*``
    bookkeeping fields. ``is_current`` marks the API user's current fiscal period, which
    upstream uses for balances when no ``fiscalPeriodId`` is given. On the synthetic demo
    organisation that is 2025, the period ``scripts/seed_demo.py`` created, not 2026, the
    one the organisation was created with.
    """

    id: int
    name: str | None = None
    short_name: str | None = Field(default=None, validation_alias="shortName")
    start: UpstreamDate
    end: UpstreamDate
    salary_start: UpstreamDate | None = Field(default=None, validation_alias="salaryStart")
    salary_end: UpstreamDate | None = Field(default=None, validation_alias="salaryEnd")
    last_entry_date: datetime | None = Field(default=None, validation_alias="lastEntryDate")
    closed: bool
    current: bool
    salary_closed: bool = Field(validation_alias="salaryClosed")
    transient: bool
    is_closed: bool = Field(validation_alias="isClosed")
    is_current: bool = Field(validation_alias="isCurrent")
    is_salary_closed: bool = Field(validation_alias="isSalaryClosed")
    is_transient: bool = Field(validation_alias="isTransient")
    available_month_ids: list[str] = Field(validation_alias="availableMonthIds")
    available_salary_month_ids: list[str] = Field(validation_alias="availableSalaryMonthIds")
    closed_month_ids: list[str] = Field(validation_alias="closedMonthIds")
    closed_salary_month_ids: list[str] = Field(validation_alias="closedSalaryMonthIds")
    open_month_ids: list[str] = Field(validation_alias="openMonthIds")
    open_salary_month_ids: list[str] = Field(validation_alias="openSalaryMonthIds")
    created: datetime | None = None
    created_by: str | None = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: str | None = Field(default=None, validation_alias="lastUpdatedBy")


class Currency(UpstreamModel):
    """One currency, an entry of ``currency/list.json`` (``docs/upstream/common.md``).

    ``code`` (three letters, ``CHF``), ``description``, ``is_default`` and ``rate`` are
    typed from the create and update tables: ``rate`` is the exchange rate of this
    currency into the default currency, ``1`` for the default currency itself. Typed from
    observation: ``default`` and ``auto`` with their ``is_*`` twins (both spellings come
    in every record), ``index``, ``text`` and ``value`` (seen as the code with the
    description, the code, and the id as a string), and the ``created*``/``last_updated*``
    bookkeeping fields.
    """

    id: int
    code: str
    description: str | None = None
    rate: Decimal | None = None
    default: bool
    is_default: bool = Field(validation_alias="isDefault")
    auto: bool
    is_auto: bool = Field(validation_alias="isAuto")
    index: str | None = None
    text: str | None = None
    value: str | None = None
    created: datetime | None = None
    created_by: str | None = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: str | None = Field(default=None, validation_alias="lastUpdatedBy")


class TaxComponent(UpstreamModel):
    """One component of a tax code, an item of ``TaxCode.components`` (up to two).

    Typed from the create and update tables of ``tax`` (``docs/upstream/common.md``):
    ``account_id`` is the account the tax is collected on; ``apply_rule`` is one of
    ``CREDIT``, ``DEBIT``, ``REVENUE``, ``EXPENSE``, ``LEGACY_REV``, ``LEGACY_EXP``;
    ``calc_type`` is ``NET`` or ``GROSS``; ``code`` holds the ESTV tax-form codes,
    comma-separated (``200,303``), or is empty. Both value sets stay strings. Typed from
    observation: ``id``, ``pos`` and ``is_input_tax``.
    """

    id: int
    account_id: int = Field(validation_alias="accountId")
    apply_rule: str = Field(validation_alias="applyRule")
    calc_type: str = Field(validation_alias="calcType")
    code: str | None = None
    pos: int | None = None
    is_input_tax: bool = Field(validation_alias="isInputTax")


class TaxRate(UpstreamModel):
    """One rate of a tax code, an item of ``TaxCode.rates``.

    Typed from the create and update tables of ``tax``: ``percentage`` is the rate
    (``8.1``), valid from ``date_valid``; the one rate without ``date_valid`` is the
    fallback. ``percentage_flat`` is the net or flat rate, when that method is used.
    Typed from observation: ``id``. Only rates without ``date_valid`` were seen.
    """

    id: int
    percentage: Decimal
    date_valid: UpstreamDate | None = Field(default=None, validation_alias="dateValid")
    percentage_flat: Decimal | None = Field(default=None, validation_alias="percentageFlat")


class TaxCode(UpstreamModel):
    """One tax code, an entry of ``tax/list.json`` (``docs/upstream/common.md``).

    ``code``, ``components``, ``rates``, ``description``, ``document_name``,
    ``is_display_tax_rate`` and ``is_inactive`` are typed from the create and update
    tables; ``description`` and ``document_name`` may hold localised text as
    ``<values><de>...</de></values>``. Typed from observation: ``account_display`` (seen
    as the numbers of the components' accounts, ``"2200"`` or ``"2200, 1170"``),
    ``current_percentage`` and ``current_percentage_flat`` (the rate in force, typed like
    ``TaxRate``; the flat one was only seen as ``null``), ``form_codes`` (seen as
    ``"200, 303"``, ``"400"`` or empty),
    ``is_flat``, the twins ``display_tax_rate`` and ``inactive``, and the
    ``created*``/``last_updated*`` bookkeeping fields.
    """

    id: int
    code: str
    description: str | None = None
    document_name: str | None = Field(default=None, validation_alias="documentName")
    components: list[TaxComponent]
    rates: list[TaxRate]
    account_display: str | None = Field(default=None, validation_alias="accountDisplay")
    current_percentage: Decimal | None = Field(default=None, validation_alias="currentPercentage")
    current_percentage_flat: Decimal | None = Field(
        default=None, validation_alias="currentPercentageFlat"
    )
    form_codes: str | None = Field(default=None, validation_alias="formCodes")
    display_tax_rate: bool = Field(validation_alias="displayTaxRate")
    is_display_tax_rate: bool = Field(validation_alias="isDisplayTaxRate")
    inactive: bool
    is_inactive: bool = Field(validation_alias="isInactive")
    is_flat: bool = Field(validation_alias="isFlat")
    created: datetime | None = None
    created_by: str | None = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: str | None = Field(default=None, validation_alias="lastUpdatedBy")


class Filter(UpstreamModel):
    """One item of the ``filter`` parameter of a ``list.json`` operation.

    ``docs/upstream/account.md``, "List accounts": "An array of filters to filter the list.
    All filters must match (AND)." Sent as the JSON array upstream asks for, e.g.
    ``[{"comparison":"eq","field":"number","value":"1020"}]``. Unknown keys are refused.

    Attributes:
        comparison: ``eq``, ``like``, ``gt`` or ``lt`` (``Comparison``); upstream's default
            is ``like``. Upstream would ignore an unknown one, so the type refuses it, and
            the tasks check it again before anything is sent.
        field: The name of the column to filter by, as the list names it (``number``).
        value: Text to filter by, or a list of texts of which any may match (OR).
    """

    model_config = ConfigDict(extra="forbid")

    comparison: Comparison = "like"
    field: str
    value: str | list[str]


class _AccountFields(UpstreamModel):
    """The fields ``account/list.json`` and ``account/read.json`` both send."""

    id: int
    number: str
    name: str
    category_id: int = Field(validation_alias="categoryId")
    currency_id: int | None = Field(default=None, validation_alias="currencyId")
    currency_code: str | None = Field(default=None, validation_alias="currencyCode")
    tax_id: int | None = Field(default=None, validation_alias="taxId")
    account_class: str | None = Field(default=None, validation_alias="accountClass")
    custom: str | None = None
    notes: str | None = None
    target_min: Decimal | None = Field(default=None, validation_alias="targetMin")
    target_max: Decimal | None = Field(default=None, validation_alias="targetMax")
    inactive: bool
    is_inactive: bool = Field(validation_alias="isInactive")
    attachment_count: int = Field(validation_alias="attachmentCount")
    allocation_count: int = Field(validation_alias="allocationCount")
    cost_center_ids: JsonValue = Field(default=None, validation_alias="costCenterIds")
    cost_center_numbers: JsonValue = Field(default=None, validation_alias="costCenterNumbers")
    created: datetime | None = None
    created_by: str | None = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: str | None = Field(default=None, validation_alias="lastUpdatedBy")


class Account(_AccountFields):
    """One account, an entry of ``account/list.json`` (``docs/upstream/account.md``).

    A financial account of the chart of accounts. ``category_id``, ``name``, ``number``,
    ``currency_id``, ``custom`` (XML), ``notes`` (HTML), ``target_min``, ``target_max``,
    ``tax_id`` and ``is_inactive`` are typed from the create and update tables.
    ``number`` stays the string upstream sends (``"1020"``): it is the account's
    identifier, "numeric but can contain a decimal point". ``currency_id`` is ``null`` in
    the committed fixtures, list and read alike (their accounts are in the default
    currency); the first demo organisation sent it as a number in the read and as a
    string (``"2"``) in the list, in recordings never committed, so a model test feeds
    ``Account`` a string, a number and ``null``: all parse (``2``, ``2``, ``None``).

    Typed from observation: the balances of the fiscal period asked for (``fiscalPeriodId``,
    else the current one) as ``opening_amount`` and ``end_amount`` in the account's
    currency and ``default_currency_opening_amount`` and ``default_currency_end_amount``
    in the default currency; ``account_class`` (seen: ``ASSET``, ``LIABILITY``,
    ``REVENUE``, ``EXPENSE``, ``BALANCE``), ``category_display``, ``currency_code``,
    ``attachment_count``, ``allocation_count``, the flags ``bank_account`` and
    ``in_salary_type`` with their ``is_*`` twins and ``inactive``, the
    ``created*``/``last_updated*`` bookkeeping fields, and ``tax_code`` and
    ``target_display``, only seen as ``null`` and kept as strings. ``cost_center_ids`` and
    ``cost_center_numbers`` were only seen as ``null`` and are kept as sent.
    """

    category_display: str | None = Field(default=None, validation_alias="categoryDisplay")
    tax_code: str | None = Field(default=None, validation_alias="taxCode")
    opening_amount: Decimal | None = Field(default=None, validation_alias="openingAmount")
    end_amount: Decimal | None = Field(default=None, validation_alias="endAmount")
    default_currency_opening_amount: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyOpeningAmount"
    )
    default_currency_end_amount: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyEndAmount"
    )
    target_display: str | None = Field(default=None, validation_alias="targetDisplay")
    bank_account: bool = Field(validation_alias="bankAccount")
    is_bank_account: bool = Field(validation_alias="isBankAccount")
    in_salary_type: bool = Field(validation_alias="inSalaryType")
    is_in_salary_type: bool = Field(validation_alias="isInSalaryType")


class AccountDetail(_AccountFields):
    """One account as ``account/read.json`` returns it (``docs/upstream/account.md``).

    Observed on 2026-10-23 against the demo organisation: ``read.json`` sends a different
    set of fields than ``list.json``. It has no balances, no ``category_display``,
    ``tax_code`` or ``target_display``, and no ``bank_account`` or ``in_salary_type``
    flags; it adds the fields below. The fields both send are typed as on ``Account``.

    Typed from observation: ``full_name`` (seen as the number and the name),
    ``is_default_currency`` and ``is_foreign_currency``. ``currency_code`` was ``null`` in
    the read of an account in the default currency whose list entry says ``CHF``.
    ``attachments`` and ``allocations`` are documented as inputs of create and update
    (``fileId``; ``share``, ``toCostCenterId``) but were only seen empty in a response, so
    their items are kept as sent.
    """

    full_name: str | None = Field(default=None, validation_alias="fullName")
    attachments: list[JsonValue]
    allocations: list[JsonValue]
    is_default_currency: bool = Field(validation_alias="isDefaultCurrency")
    is_foreign_currency: bool = Field(validation_alias="isForeignCurrency")
