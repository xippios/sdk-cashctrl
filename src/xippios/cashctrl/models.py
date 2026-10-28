"""Pydantic models mirroring CashCtrl payloads.

One model per upstream object, subclassing ``xippios.core.UpstreamModel``, with fields
named as upstream names them in snake_case. Where upstream spells a field differently
(``isCurrent``), ``Field(validation_alias=...)`` accepts that spelling on input; never
``alias=``, which the adapters would serialise, handing agents the upstream spelling. So
results serialise under the snake_case names in Python, over MCP and over HTTP alike
(``is_current``, ``end_amount``), the same names the tool arguments use. Within-source
hygiene only: dates become ``datetime.date``/``datetime``, numbers become ``int`` or
``Decimal`` (ADR-0008: JSON numbers on the wire). Documented value sets are ``Literal``
types here (``Direction``, ``Language``), so the tool schemas list them; an enumeration
generated into ``enums.py`` would be a ``StrEnum``, and one of integer ids an ``IntEnum``
(conventions §3). No cross-source normalisation (ADR-0003): an upstream concept stays an
upstream concept, and nothing is renamed or computed.

These read models stay faithful, documented personal identifiers included: ``ssn`` and
``iban`` (``Person``, ``PersonDetail``, and ``JournalEntryDetail.associates``), and a
location's ``iban`` and ``qrIban`` (``Location``, row 123). The projections tasks return
leave those out (``PersonProjection``, ``PersonDetailProjection``,
``JournalEntryDetailProjection``, ``LocationProjection``), as ``get_report_data`` drops
them from its raw rows (``ReportData`` itself keeps what upstream sends), a write task
does not echo one in ``meta.request`` and its preview shows one as ``REDACTED``, and
fixtures never carry their values (ADR-0017).

``created_by`` and ``last_updated_by`` are ``AuditUser`` on every model that has them:
CashCtrl writes an API user there as ``API:`` and the first four characters of its key,
which every model masks to ``API:REDACTED``, the value the fixture recorder writes, so
a live answer and a fixture have one shape (G5 (2) of 2026-10-28, queue row 129).
``SYSTEM`` and a user's name pass as sent. ``HistoryEntry.message`` is upstream's text
as sent: no recorded message carries a tag.

``docs/upstream/`` shows no response bodies. Field types come from the create and update
parameter tables where they describe the field, and from the answers recorded against the
demo organisation where they do not: on 2026-10-23 and 2026-10-24 for the ledger,
journal, person and order models, on 2026-10-27 for the custom field, category, title,
cost center, location and report models. The latter fields are named in each model's
docstring as typed from observation. Two demo organisations answered on 2026-10-23: the
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
- A ``read.json`` record differs from its ``list.json`` entry (``Account`` and
  ``AccountDetail``, ``JournalEntry`` and ``JournalEntryDetail``, ``Person`` and
  ``PersonDetail``, ``Order`` and ``OrderDetail``); ``person/read.json`` leaves out
  every field whose value is ``null``.
- An id the create tables document as TEXT (``associateId`` of a journal entry or one of
  its lines, ``responsiblePersonId``, ``unitId``) is kept as the number it is; the lines
  of a collective journal entry send ``associateId`` as a string (``"3"``), parsed to
  ``3``.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AliasChoices, BeforeValidator, ConfigDict, Field, JsonValue, field_validator
from xippios.core import UpstreamModel

__all__ = [
    "Account",
    "AccountCategory",
    "AccountDetail",
    "AddressType",
    "AllocationInput",
    "AttachmentInput",
    "BankAccountInput",
    "BankAccountType",
    "Canton",
    "ChildInput",
    "Color",
    "Comparison",
    "ContactType",
    "CostCenter",
    "Currency",
    "CustomField",
    "CustomFieldType",
    "Direction",
    "Filter",
    "FiscalPeriod",
    "HistoryEntry",
    "InsuranceContractInput",
    "JournalEntry",
    "JournalEntryDetail",
    "JournalEntryDetailProjection",
    "JournalItem",
    "JournalItemInput",
    "JournalRow",
    "Language",
    "ListResponse",
    "Location",
    "LocationProjection",
    "NotifyType",
    "Order",
    "OrderBookEntry",
    "OrderBookTemplate",
    "OrderCategory",
    "OrderCategoryStatus",
    "OrderDetail",
    "OrderItem",
    "OrderItemInput",
    "OrderItemType",
    "OrderType",
    "Person",
    "PersonAddress",
    "PersonAddressInput",
    "PersonCategory",
    "PersonContact",
    "PersonContactInput",
    "PersonDetail",
    "PersonDetailProjection",
    "PersonProjection",
    "PersonTitle",
    "ReadResponse",
    "Recurrence",
    "ReportData",
    "ReportTreeNode",
    "ServicePeriodInput",
    "TaxCode",
    "TaxComponent",
    "TaxRate",
    "WriteAnswer",
    "WritePreview",
    "WriteResult",
]


def _date_part(value: object) -> object:
    """``"2024-12-31 23:59:59.0"`` → ``"2024-12-31"``: upstream sends dates as timestamps."""
    if isinstance(value, str) and len(value) > 10 and value[10] in " T":
        return value[:10]
    return value


UpstreamDate = Annotated[date, BeforeValidator(_date_part)]
"""A date upstream sends with a time of day; the date part is kept."""

API_USER_MASK = "API:REDACTED"
"""What an API user tag in ``created_by`` or ``last_updated_by`` becomes (``AuditUser``)."""


def _mask_api_user(value: object) -> object:
    """``"API:<four key characters>"`` → ``"API:REDACTED"``; any other value as sent.

    CashCtrl names the API user that wrote a record as ``API:`` and the first four
    characters of its key (observed on 2026-10-23), and the fixture recorder writes
    ``API:REDACTED`` instead. A text that starts with ``API:``, the marker in any letter
    case, is masked whole, whatever follows; ``SYSTEM``, a user's name or e-mail address
    and ``None`` pass.
    """
    if isinstance(value, str) and value[:4].upper() == "API:":
        return API_USER_MASK
    return value


AuditUser = Annotated[str | None, BeforeValidator(_mask_api_user)]
"""``created_by`` and ``last_updated_by`` of every model: who wrote the record, an API user's
tag masked (G5 (2) of 2026-10-28, queue row 129), so a live answer has a fixture's shape
and no key prefix reaches a result."""

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
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


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
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


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
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


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
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


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


OrderType = Literal["SALES", "PURCHASE"]
"""The values of ``type`` on ``order/list.json``: "Possible values: SALES, PURCHASE"."""


class JournalItem(UpstreamModel):
    """One line of a collective journal entry, an item of ``JournalEntryDetail.items``.

    Typed from the ``items`` table of ``journal/create.json`` (``docs/upstream/journal.md``):
    ``account_id``, ``debit`` and ``credit`` (one of the two is set), ``description``,
    ``tax_id``, and ``associate_id``, documented as TEXT (an id, or a name that creates a
    person) and sent as a string (``"3"``) in the read, parsed as the person's id.
    ``allocations`` were only seen empty and are kept as sent. Typed from observation:
    ``id``, ``journal_id``, ``pos``, ``amount``, ``tax_rate``, ``tax_code``,
    ``associate_name`` and ``account_name`` (the account's localised name, without its
    number).
    """

    id: int
    journal_id: int | None = Field(default=None, validation_alias="journalId")
    account_id: int = Field(validation_alias="accountId")
    account_name: str | None = Field(default=None, validation_alias="accountName")
    associate_id: int | None = Field(default=None, validation_alias="associateId")
    associate_name: str | None = Field(default=None, validation_alias="associateName")
    description: str | None = None
    debit: Decimal | None = None
    credit: Decimal | None = None
    amount: Decimal | None = None
    tax_id: int | None = Field(default=None, validation_alias="taxId")
    tax_code: str | None = Field(default=None, validation_alias="taxCode")
    tax_rate: Decimal | None = Field(default=None, validation_alias="taxRate")
    pos: int | None = None
    allocations: list[JsonValue] = Field(default_factory=list)


class JournalRow(UpstreamModel):
    """One booking row of a journal entry, an item of ``JournalEntryDetail.rows``.

    Not documented; typed from observation. A row per account the entry books to, with
    its debit, credit and tax amounts in three variants, ``fc_*``, ``ac_*`` and ``dc_*``,
    which upstream does not explain (equal in every observed row, all in CHF). An entry
    with a tax code shows the taxed account's row net of tax, ``is_taxed``, and a separate
    row on the tax account, ``is_tax``: for an invoice of 3'600.00 with 8.1 %, 3'330.25 on
    3200 and 269.75 on 2200. ``tax_percentage`` is the rate of the taxed and the tax row.
    """

    account_id: int = Field(validation_alias="accountId")
    account_name: str | None = Field(default=None, validation_alias="accountName")
    fc_debit: Decimal = Field(validation_alias="fcDebit")
    fc_credit: Decimal = Field(validation_alias="fcCredit")
    ac_debit: Decimal = Field(validation_alias="acDebit")
    ac_credit: Decimal = Field(validation_alias="acCredit")
    dc_debit: Decimal = Field(validation_alias="dcDebit")
    dc_credit: Decimal = Field(validation_alias="dcCredit")
    fc_tax: Decimal = Field(validation_alias="fcTax")
    ac_tax: Decimal = Field(validation_alias="acTax")
    dc_tax: Decimal = Field(validation_alias="dcTax")
    tax_percentage: Decimal | None = Field(default=None, validation_alias="taxPercentage")
    is_taxed: bool = Field(validation_alias="isTaxed")
    is_tax: bool = Field(validation_alias="isTax")


class _JournalEntryFields(UpstreamModel):
    """The fields ``journal/list.json`` and ``journal/read.json`` both send.

    ``attachment_count`` may be ``None``. ``docs/upstream/journal.md`` documents no
    ``attachmentCount``: Read journal entry (line 7) and List journal entries (line 23)
    give parameters only, no response body, and ``attachments`` is an input of create and
    update (lines 199 and 263). It was typed from the manual entries, which send a number;
    the entries an order booked (``type`` ``ORDER``, ``orderId`` set) send ``null`` in the
    list and the read, seen in the demo organisation on 2026-10-26
    (``tests/fixtures/journal_list/order_booked.json``,
    ``tests/fixtures/journal_read/order_booked.json``).
    """

    id: int
    type: str
    date_added: UpstreamDate = Field(validation_alias="dateAdded")
    title: str | None = None
    reference: str | None = None
    amount: Decimal
    debit_id: int | None = Field(default=None, validation_alias="debitId")
    credit_id: int | None = Field(default=None, validation_alias="creditId")
    associate_id: int | None = Field(default=None, validation_alias="associateId")
    associate_name: str | None = Field(default=None, validation_alias="associateName")
    tax_id: int | None = Field(default=None, validation_alias="taxId")
    tax_code: str | None = Field(default=None, validation_alias="taxCode")
    tax_rate: Decimal | None = Field(default=None, validation_alias="taxRate")
    currency_id: int | None = Field(default=None, validation_alias="currencyId")
    currency_code: str | None = Field(default=None, validation_alias="currencyCode")
    currency_rate: Decimal | None = Field(default=None, validation_alias="currencyRate")
    custom: str | None = None
    notes: str | None = None
    items_count: int = Field(validation_alias="itemsCount")
    attachment_count: int | None = Field(default=None, validation_alias="attachmentCount")
    allocation_count: int | None = Field(default=None, validation_alias="allocationCount")
    cost_center_ids: JsonValue = Field(default=None, validation_alias="costCenterIds")
    cost_center_numbers: JsonValue = Field(default=None, validation_alias="costCenterNumbers")
    order_id: JsonValue = Field(default=None, validation_alias="orderId")
    order_book_entry_id: JsonValue = Field(default=None, validation_alias="orderBookEntryId")
    salary_book_entry_id: JsonValue = Field(default=None, validation_alias="salaryBookEntryId")
    statement_id: JsonValue = Field(default=None, validation_alias="statementId")
    inventory_id: JsonValue = Field(default=None, validation_alias="inventoryId")
    import_entry_id: JsonValue = Field(default=None, validation_alias="importEntryId")
    imported: JsonValue = None
    imported_by: JsonValue = Field(default=None, validation_alias="importedBy")
    recurrence: str | None = None
    start_date: UpstreamDate | None = Field(default=None, validation_alias="startDate")
    end_date: UpstreamDate | None = Field(default=None, validation_alias="endDate")
    days_before: int | None = Field(default=None, validation_alias="daysBefore")
    notify_type: str | None = Field(default=None, validation_alias="notifyType")
    notify_person_id: int | None = Field(default=None, validation_alias="notifyPersonId")
    notify_user_id: int | None = Field(default=None, validation_alias="notifyUserId")
    notify_email: str | None = Field(default=None, validation_alias="notifyEmail")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class JournalEntry(_JournalEntryFields):
    """One journal entry, an entry of ``journal/list.json`` (``docs/upstream/journal.md``).

    A book entry, manual or made by another module (orders, salary, imports). Typed from
    the tables of ``journal/create.json`` and ``update.json``: ``date_added`` (the date of
    the entry, ``YYYY-MM-DD``), ``title``, ``reference``, ``amount``, ``debit_id``,
    ``credit_id``, ``associate_id`` (documented as TEXT, an id or a name; seen as a
    number), ``tax_id``, ``currency_id``, ``currency_rate``, ``custom`` (XML), ``notes``
    (HTML), ``recurrence``, ``start_date``, ``end_date``, ``days_before`` and the
    ``notify_*`` fields.

    Typed from observation: ``type`` (seen: ``MANUAL``, ``COLLECTIVE``, and ``ORDER`` for
    an entry an order booked), ``debit_name`` and ``credit_name`` (the account's number
    and localised name), ``associate_name``, ``tax_code``, ``tax_rate``,
    ``currency_code``, ``items_count`` (the lines of a collective entry, ``0``
    otherwise), ``attachment_count`` (``None`` for an entry an order booked),
    ``allocation_count``, ``recurring`` with its ``is_*`` twin, and the
    ``created*``/``last_updated*`` bookkeeping fields. A collective entry has no
    ``debit_id`` and one ``credit_id`` in the list; its lines are in
    ``get_journal_entry``'s ``items``. Kept as sent: ``order_id``, the order's id on an
    entry an order booked, and the list's ``name_singular`` (a localised name) and
    ``order_type`` (``PURCHASE``); ``order_id``, ``name_singular`` and ``order_type`` are
    filled on such an entry (seen on 2026-10-26) and ``null`` on a manual one; only seen
    as ``null``: ``order_book_entry_id``, ``salary_book_entry_id``, ``statement_id``,
    ``inventory_id``, ``import_entry_id``, ``imported``, ``imported_by``,
    ``cost_center_ids``, ``cost_center_numbers``, and the list's ``account_id``,
    ``account_currency_id``, ``account_class`` and ``balance``.
    """

    debit_name: str | None = Field(default=None, validation_alias="debitName")
    credit_name: str | None = Field(default=None, validation_alias="creditName")
    account_id: JsonValue = Field(default=None, validation_alias="accountId")
    account_currency_id: JsonValue = Field(default=None, validation_alias="accountCurrencyId")
    account_class: JsonValue = Field(default=None, validation_alias="accountClass")
    balance: JsonValue = None
    name_singular: JsonValue = Field(default=None, validation_alias="nameSingular")
    order_type: JsonValue = Field(default=None, validation_alias="orderType")
    recurring: bool
    is_recurring: bool = Field(validation_alias="isRecurring")


class PersonAddress(UpstreamModel):
    """One address of a person, an item of ``PersonDetail.addresses``.

    Typed from the ``addresses`` table of ``person/create.json``
    (``docs/upstream/person.md``): ``type`` (``MAIN``, ``INVOICE``, ``DELIVERY``,
    ``SALARY``, ``HISTORICAL``, ``OTHER``), ``address`` (street and number, may span
    lines), ``zip``, ``city``, ``canton`` (Swiss cantons only), ``country`` (ISO 3166
    alpha-3, ``CHE``), ``company``, ``first_name``, ``last_name``, ``is_hide_company`` and
    ``is_hide_name``. Typed from observation: ``id``, ``person_id``, ``pos``, the twins
    ``hide_company`` and ``hide_name``, ``company_for_address``,
    ``first_name_for_address``, ``last_name_for_address``, ``street_name`` and
    ``street_number`` (``address`` split), ``title_name``, ``canton_code``,
    ``country_code2`` and ``country_code3``. ``title_id``: an address ``titleId`` sent
    with a create was stored and read back, with ``title_name``, in the live
    verification of 2026-10-24 (``docs/demo-org.md``, Person reads); it is in neither
    ``addresses`` table (``person/create.json``, ``person/update.json``), but reads
    return it, so ``update_person`` refuses to carry it over. Typed as the id of a title,
    an integer, as the person's own ``titleId`` is: "optional, NUMBER", a "Person title"
    (``docs/upstream/person.md`` line 314), whose ``id`` is "mandatory, NUMBER" (line
    683, Read title).
    """

    id: int
    person_id: int | None = Field(default=None, validation_alias="personId")
    type: str
    address: str | None = None
    zip: str | None = None
    city: str | None = None
    canton: str | None = None
    country: str | None = None
    company: str | None = None
    first_name: str | None = Field(default=None, validation_alias="firstName")
    last_name: str | None = Field(default=None, validation_alias="lastName")
    title_id: int | None = Field(default=None, validation_alias="titleId")
    title_name: str | None = Field(default=None, validation_alias="titleName")
    company_for_address: str | None = Field(default=None, validation_alias="companyForAddress")
    first_name_for_address: str | None = Field(default=None, validation_alias="firstNameForAddress")
    last_name_for_address: str | None = Field(default=None, validation_alias="lastNameForAddress")
    street_name: str | None = Field(default=None, validation_alias="streetName")
    street_number: str | None = Field(default=None, validation_alias="streetNumber")
    canton_code: str | None = Field(default=None, validation_alias="cantonCode")
    country_code2: str | None = Field(default=None, validation_alias="countryCode2")
    country_code3: str | None = Field(default=None, validation_alias="countryCode3")
    pos: int | None = None
    hide_company: bool | None = Field(default=None, validation_alias="hideCompany")
    is_hide_company: bool | None = Field(default=None, validation_alias="isHideCompany")
    hide_name: bool | None = Field(default=None, validation_alias="hideName")
    is_hide_name: bool | None = Field(default=None, validation_alias="isHideName")


class PersonContact(UpstreamModel):
    """One piece of contact information of a person, an item of ``PersonDetail.contacts``.

    Typed from the ``contacts`` table of ``person/create.json``: ``type`` (``EMAIL_WORK``,
    ``EMAIL_INVOICE``, ``PHONE_WORK``, ``WEBSITE`` and the rest), ``address`` (the e-mail
    address, phone number or URL itself) and ``notes``. Typed from observation: ``id``,
    ``person_id`` and ``pos``; ``purpose`` was only seen as ``null``.
    """

    id: int
    person_id: int | None = Field(default=None, validation_alias="personId")
    type: str
    address: str
    notes: str | None = None
    purpose: JsonValue = None
    pos: int | None = None


class _PersonFields(UpstreamModel):
    """The fields ``person/list.json`` and ``person/read.json`` share, but ``ssn``.

    ``read.json`` leaves out every field whose value is ``null`` (observed on 2026-10-23;
    the list sends them as ``null``), so everything that may be empty defaults to ``None``.
    ``ssn``, which both send, is declared on the read models (``Person``,
    ``PersonDetail``) alone, so that the projections tasks return can leave it out
    (ADR-0017).
    """

    id: int
    nr: str | None = None
    name: str | None = None
    company: str | None = None
    first_name: str | None = Field(default=None, validation_alias="firstName")
    last_name: str | None = Field(default=None, validation_alias="lastName")
    alt_name: str | None = Field(default=None, validation_alias="altName")
    category_id: int | None = Field(default=None, validation_alias="categoryId")
    category_name: str | None = Field(default=None, validation_alias="categoryName")
    title_id: int | None = Field(default=None, validation_alias="titleId")
    position: str | None = None
    department: str | None = None
    industry: str | None = None
    language: str | None = None
    language_name: str | None = Field(default=None, validation_alias="languageName")
    address: str | None = None
    zip: str | None = None
    city: str | None = None
    canton: str | None = None
    country: str | None = None
    email_work: str | None = Field(default=None, validation_alias="emailWork")
    vat_uid: str | None = Field(default=None, validation_alias="vatUid")
    bank_data: str | None = Field(default=None, validation_alias="bankData")
    discount_percentage: Decimal | None = Field(default=None, validation_alias="discountPercentage")
    date_birth: UpstreamDate | None = Field(default=None, validation_alias="dateBirth")
    color: str | None = None
    superior_id: int | None = Field(default=None, validation_alias="superiorId")
    user_id: int | None = Field(default=None, validation_alias="userId")
    location_id: int | None = Field(default=None, validation_alias="locationId")
    certificate_template_id: int | None = Field(
        default=None, validation_alias="certificateTemplateId"
    )
    insurance_nr: str | None = Field(default=None, validation_alias="insuranceNr")
    insurance_member_nr: str | None = Field(default=None, validation_alias="insuranceMemberNr")
    custom: str | None = None
    notes: str | None = None
    attachment_count: int = Field(validation_alias="attachmentCount")
    customer: bool
    is_customer: bool = Field(validation_alias="isCustomer")
    vendor: bool
    is_vendor: bool = Field(validation_alias="isVendor")
    employee: bool
    is_employee: bool = Field(validation_alias="isEmployee")
    insurance: bool
    is_insurance: bool = Field(validation_alias="isInsurance")
    family: bool
    is_family: bool = Field(validation_alias="isFamily")
    inactive: bool
    is_inactive: bool = Field(validation_alias="isInactive")
    is_auto_fill_responsible_person: bool = Field(validation_alias="isAutoFillResponsiblePerson")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class _PersonEntryFields(_PersonFields):
    """The fields only ``person/list.json`` sends, but ``iban`` (see ``Person``)."""

    category_display: str | None = Field(default=None, validation_alias="categoryDisplay")
    country_name: str | None = Field(default=None, validation_alias="countryName")
    children_count: int | None = Field(default=None, validation_alias="childrenCount")
    auto_fill_responsible_person: bool = Field(validation_alias="autoFillResponsiblePerson")
    title: JsonValue = None
    title_sentence: JsonValue = Field(default=None, validation_alias="titleSentence")
    gender: JsonValue = None
    gender_name: JsonValue = Field(default=None, validation_alias="genderName")
    thumbnail_file_id: JsonValue = Field(default=None, validation_alias="thumbnailFileId")
    certificate_values: JsonValue = Field(default=None, validation_alias="certificateValues")
    discount_inherited: JsonValue = Field(default=None, validation_alias="discountInherited")
    discount_effective: JsonValue = Field(default=None, validation_alias="discountEffective")
    bic: JsonValue = None
    email_private: JsonValue = Field(default=None, validation_alias="emailPrivate")
    email_invoice: JsonValue = Field(default=None, validation_alias="emailInvoice")
    phone_work: JsonValue = Field(default=None, validation_alias="phoneWork")
    phone_private: JsonValue = Field(default=None, validation_alias="phonePrivate")
    mobile_work: JsonValue = Field(default=None, validation_alias="mobileWork")
    mobile_private: JsonValue = Field(default=None, validation_alias="mobilePrivate")
    url: JsonValue = None
    superior_name: JsonValue = Field(default=None, validation_alias="superiorName")
    location_name: JsonValue = Field(default=None, validation_alias="locationName")


class Person(_PersonEntryFields):
    """One person, an entry of ``person/list.json`` (``docs/upstream/person.md``).

    A customer, vendor, employee, insurance or family, company or natural person. Typed
    from the tables of ``person/create.json`` and ``update.json``: ``nr``, ``company``,
    ``first_name``, ``last_name``, ``alt_name``, ``category_id``, ``title_id``,
    ``position``, ``department``, ``industry``, ``language`` (``DE``, ``EN``, ``FR``,
    ``IT``), ``vat_uid``, ``bank_data``, ``discount_percentage``, ``date_birth``,
    ``color``, ``superior_id``, ``user_id``, ``location_id``,
    ``certificate_template_id``, ``ssn``, ``insurance_nr``, ``insurance_member_nr``,
    ``custom`` (XML), ``notes`` (HTML), the role flags ``is_customer``, ``is_vendor``,
    ``is_employee``, ``is_insurance``, ``is_family`` and ``is_inactive``, and
    ``is_auto_fill_responsible_person``.

    Typed from observation: ``name`` (the company, or the person's name),
    ``category_name`` and ``category_display`` (localised), ``language_name``, the main
    address flattened into ``address``, ``zip``, ``city``, ``canton``, ``country`` and
    ``country_name``, ``email_work``, ``attachment_count``, ``children_count``, the twins
    without ``is_`` and ``auto_fill_responsible_person``, and the
    ``created*``/``last_updated*`` bookkeeping fields. CashCtrl creates two insurance
    persons itself (``created_by`` ``SYSTEM``). Only seen as ``null`` and kept as sent:
    ``title``, ``title_sentence``, ``gender``, ``gender_name``, ``thumbnail_file_id``,
    ``certificate_values``, ``discount_inherited``, ``discount_effective``, ``iban``,
    ``bic``, ``email_private``, ``email_invoice``, ``phone_work``, ``phone_private``,
    ``mobile_work``, ``mobile_private``, ``url``, ``superior_name`` and
    ``location_name``.

    The endpoint wrapper's read model, faithful to upstream (ADR-0003): it carries
    ``ssn`` and ``iban``, which ``PersonProjection``, what ``list_persons`` returns,
    leaves out (ADR-0017).
    """

    ssn: str | None = None
    iban: JsonValue = None


class PersonProjection(_PersonEntryFields):
    """One person as ``list_persons`` returns it: ``Person`` without ``ssn`` and ``iban``.

    Documented personal identifiers stay out of the projections tasks return (ADR-0017,
    conventions §3): ``ssn``, "Social security number of the employee", and ``iban``, an
    IBAN (documented for each of a person's ``bankAccounts``; on the list only seen
    ``null``). Every other field is ``Person``'s, under the same name and type; built
    with ``UpstreamModel.project``.
    """


class _PersonDetailFields(_PersonFields):
    """The fields only ``person/read.json`` sends, but ``bank_accounts`` (see ``PersonDetail``)."""

    addresses: list[PersonAddress] = Field(default_factory=list)
    contacts: list[PersonContact] = Field(default_factory=list)
    children: list[JsonValue] = Field(default_factory=list)
    service_periods: list[JsonValue] = Field(
        default_factory=list, validation_alias="servicePeriods"
    )
    insurance_contracts: list[JsonValue] = Field(
        default_factory=list, validation_alias="insuranceContracts"
    )
    attachments: list[JsonValue] = Field(default_factory=list)
    certificate_values_map: JsonValue = Field(default=None, validation_alias="certificateValuesMap")
    certificate_values: JsonValue = Field(default=None, validation_alias="certificateValues")
    full_name: str | None = Field(default=None, validation_alias="fullName")
    company_or_full_name: str | None = Field(default=None, validation_alias="companyOrFullName")
    abbreviated_name: str | None = Field(default=None, validation_alias="abbreviatedName")
    title_name: str | None = Field(default=None, validation_alias="titleName")
    language_code: str | None = Field(default=None, validation_alias="languageCode")
    canton_code: str | None = Field(default=None, validation_alias="cantonCode")
    country_code2: str | None = Field(default=None, validation_alias="countryCode2")
    country_code3: str | None = Field(default=None, validation_alias="countryCode3")
    number_of_children: int | None = Field(default=None, validation_alias="numberOfChildren")
    icon_cls: str | None = Field(default=None, validation_alias="iconCls")


class PersonDetail(_PersonDetailFields):
    """One person as ``person/read.json`` returns it (``docs/upstream/person.md``).

    Observed on 2026-10-23 against the demo organisation: the read leaves out every field
    whose value is ``null``, and sends a different set than the list. It adds the
    structured lists below and some derived names, and has no ``category_display``,
    ``country_name``, ``children_count`` nor the list's ``null``-only fields. The fields
    both send are typed as on ``Person``. ``journal/read.json`` embeds the same record for
    each person an entry names (``JournalEntryDetail.associates``).

    ``addresses`` and ``contacts`` are typed from the create tables (``PersonAddress``,
    ``PersonContact``). ``bank_accounts``, ``children``, ``service_periods``,
    ``insurance_contracts`` and ``attachments`` are documented as inputs but were only
    seen empty, so their items are kept as sent; so is ``certificate_values_map``, only
    seen as ``{}``, and ``certificate_values``, documented as an input and never seen in
    a read (which leaves out ``null``), kept should it come. Typed from observation:
    ``full_name`` (empty for a company), ``company_or_full_name``, ``abbreviated_name``,
    ``title_name``, ``language_code`` (``de``), ``canton_code``, ``country_code2``
    (``CH``), ``country_code3`` (``CHE``), ``number_of_children`` and ``icon_cls``.

    The endpoint wrapper's read model, faithful to upstream (ADR-0003): it carries
    ``ssn`` and, in each of ``bank_accounts``, ``iban``, which
    ``PersonDetailProjection``, what the tasks return, leaves out (ADR-0017).
    """

    ssn: str | None = None
    bank_accounts: list[JsonValue] = Field(default_factory=list, validation_alias="bankAccounts")


def _without_iban(account: JsonValue) -> JsonValue:
    """One item of ``bankAccounts`` without its ``iban``, the key in any case; others kept."""
    if isinstance(account, dict):
        return {key: value for key, value in account.items() if key.lower() != "iban"}
    return account


class PersonDetailProjection(_PersonDetailFields):
    """One person as ``get_person`` returns it: ``PersonDetail`` without ``ssn`` and ``iban``.

    Documented personal identifiers stay out of the projections tasks return (ADR-0017,
    conventions §3): ``ssn`` is left out, and so is the ``iban`` of each of
    ``bank_accounts``, whose other keys are kept as sent. The type enforces both: it has
    no ``ssn`` field, and its validator drops each bank account's ``iban`` (the key in
    any case) however it is validated, so ``PersonDetailProjection.project`` needs no
    help from the caller. Every other field is ``PersonDetail``'s, under the
    same name and type; built with ``UpstreamModel.project``. Write previews show the
    record before an update or a delete as this projection, and
    ``JournalEntryDetailProjection.associates`` holds it.
    """

    bank_accounts: list[JsonValue] = Field(default_factory=list, validation_alias="bankAccounts")

    @field_validator("bank_accounts")
    @classmethod
    def _drop_iban(cls, accounts: list[JsonValue]) -> list[JsonValue]:
        """Each bank account without its ``iban`` (ADR-0017); its other keys as sent."""
        return [_without_iban(account) for account in accounts]


class _JournalEntryDetailFields(_JournalEntryFields):
    """The fields only ``journal/read.json`` sends, but ``associates`` (``JournalEntryDetail``)."""

    nr: str | None = None
    items: list[JournalItem] = Field(default_factory=list)
    rows: list[JournalRow] = Field(default_factory=list)
    attachments: list[JsonValue] = Field(default_factory=list)
    allocations: list[JsonValue] = Field(default_factory=list)
    taxed_items: list[JsonValue] = Field(default_factory=list, validation_alias="taxedItems")
    taxed: bool
    default_currency_amount: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyAmount"
    )
    account_ids: str | None = Field(default=None, validation_alias="accountIds")
    items_index: str | None = Field(default=None, validation_alias="itemsIndex")
    recurrence_id: JsonValue = Field(default=None, validation_alias="recurrenceId")


class JournalEntryDetail(_JournalEntryDetailFields):
    """One journal entry as ``journal/read.json`` returns it (``docs/upstream/journal.md``).

    Observed on 2026-10-23 against the demo organisation: the read sends a different set
    of fields than the list. It has no ``debit_name``, ``credit_name``, ``recurring`` nor
    the list's ``null``-only account fields, and adds the fields below. The fields both
    send are typed as on ``JournalEntry``; ``currency_code`` was ``null`` in the read of
    an entry whose list entry says ``CHF``.

    ``items`` are the lines of a collective entry (``JournalItem``), empty for a simple
    one. ``rows`` are the bookings per account (``JournalRow``), tax rows included.
    ``associates`` are the full records of the persons the entry or its lines name, as
    ``person/read.json`` returns them. ``attachments`` and ``allocations`` are documented
    as inputs but were only seen empty, so their items are kept as sent, as are
    ``taxed_items`` (only seen empty) and ``recurrence_id`` (only seen ``null``). Typed
    from observation: ``nr`` (seen equal to ``reference``), ``taxed``,
    ``default_currency_amount``, ``account_ids`` (a JSON array of account ids as text,
    ``["33","4","42"]``, kept as sent) and ``items_index`` (the lines' texts as one
    search string).

    The endpoint wrapper's read model, faithful to upstream (ADR-0003): ``associates``
    are ``PersonDetail`` records, ``ssn`` and ``iban`` included; what
    ``get_journal_entry`` returns is ``JournalEntryDetailProjection`` (ADR-0017).
    """

    associates: list[PersonDetail] = Field(default_factory=list)


class JournalEntryDetailProjection(_JournalEntryDetailFields):
    """One journal entry as ``get_journal_entry`` returns it, its persons projected.

    ``JournalEntryDetail`` with ``associates`` as ``PersonDetailProjection`` records,
    without ``ssn`` and ``iban`` (ADR-0017, conventions §3). Every other field is
    ``JournalEntryDetail``'s, under the same name and type; built with
    ``UpstreamModel.project``.
    """

    associates: list[PersonDetailProjection] = Field(default_factory=list)


class OrderItem(UpstreamModel):
    """One item of an order, an entry of ``OrderDetail.items``.

    Typed from the ``items`` table of ``order/create.json`` (``docs/upstream/order.md``):
    ``account_id`` (revenue account for sales, expense account for purchase), ``name``,
    ``unit_price``, ``article_nr``, ``description``, ``discount_percentage``,
    ``inventory_id``, ``quantity``, ``tax_id``, ``type`` (``ARTICLE``, ``TEXT``,
    ``PAGEBREAK``, ``SUBTOTAL``, ``TITLE``, ``OPTIONTOTAL``) and ``unit_id`` (documented
    as TEXT, the id of a unit; only seen ``null``). ``allocations`` and ``attachments``
    were only seen empty and are kept as sent.

    Typed from observation: ``id``, ``order_id``, ``pos``, ``tax_code``, ``tax_rate``,
    ``tax_calc_type`` (``NET``), ``base_value`` (``GROSS``), the amounts
    ``net_unit_price``, ``tax_amount`` (per unit), ``gross_total``, ``net_total``,
    ``tax_total`` and their ``default_currency_*`` twins, ``optional`` with its ``is_*``
    twin, ``is_inventory_article`` and ``is_included_in_stats``. ``unit_name``,
    ``discount_inherited`` and ``discount_effective`` were only seen as ``null``.
    """

    id: int
    order_id: int | None = Field(default=None, validation_alias="orderId")
    pos: int | None = None
    type: str | None = None
    account_id: int | None = Field(default=None, validation_alias="accountId")
    inventory_id: int | None = Field(default=None, validation_alias="inventoryId")
    article_nr: str | None = Field(default=None, validation_alias="articleNr")
    name: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_id: int | None = Field(default=None, validation_alias="unitId")
    unit_name: JsonValue = Field(default=None, validation_alias="unitName")
    unit_price: Decimal | None = Field(default=None, validation_alias="unitPrice")
    net_unit_price: Decimal | None = Field(default=None, validation_alias="netUnitPrice")
    default_currency_unit_price: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyUnitPrice"
    )
    default_currency_net_unit_price: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyNetUnitPrice"
    )
    discount_percentage: Decimal | None = Field(default=None, validation_alias="discountPercentage")
    discount_inherited: JsonValue = Field(default=None, validation_alias="discountInherited")
    discount_effective: JsonValue = Field(default=None, validation_alias="discountEffective")
    tax_id: int | None = Field(default=None, validation_alias="taxId")
    tax_code: str | None = Field(default=None, validation_alias="taxCode")
    tax_rate: Decimal | None = Field(default=None, validation_alias="taxRate")
    tax_calc_type: str | None = Field(default=None, validation_alias="taxCalcType")
    base_value: str | None = Field(default=None, validation_alias="baseValue")
    tax_amount: Decimal | None = Field(default=None, validation_alias="taxAmount")
    gross_total: Decimal | None = Field(default=None, validation_alias="grossTotal")
    net_total: Decimal | None = Field(default=None, validation_alias="netTotal")
    tax_total: Decimal | None = Field(default=None, validation_alias="taxTotal")
    default_currency_gross_total: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyGrossTotal"
    )
    default_currency_net_total: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyNetTotal"
    )
    optional: bool | None = None
    is_optional: bool | None = Field(default=None, validation_alias="isOptional")
    is_inventory_article: bool | None = Field(default=None, validation_alias="isInventoryArticle")
    is_included_in_stats: bool | None = Field(default=None, validation_alias="isIncludedInStats")
    allocations: list[JsonValue] = Field(default_factory=list)
    attachments: list[JsonValue] = Field(default_factory=list)


class _OrderFields(UpstreamModel):
    """The fields ``order/list.json`` and ``order/read.json`` both send."""

    id: int
    type: str
    nr: str | None = None
    date: UpstreamDate
    description: str | None = None
    associate_id: int | None = Field(default=None, validation_alias="associateId")
    associate_name: str | None = Field(default=None, validation_alias="associateName")
    category_id: int = Field(validation_alias="categoryId")
    account_id: int | None = Field(default=None, validation_alias="accountId")
    status_id: int | None = Field(default=None, validation_alias="statusId")
    status_name: str | None = Field(default=None, validation_alias="statusName")
    sent_status_id: int | None = Field(default=None, validation_alias="sentStatusId")
    book_type: str | None = Field(default=None, validation_alias="bookType")
    group_id: int | None = Field(default=None, validation_alias="groupId")
    previous_id: int | None = Field(default=None, validation_alias="previousId")
    responsible_person_id: int | None = Field(default=None, validation_alias="responsiblePersonId")
    responsible_person_name: JsonValue = Field(
        default=None, validation_alias="responsiblePersonName"
    )
    rounding_id: int | None = Field(default=None, validation_alias="roundingId")
    action_id: str | None = Field(default=None, validation_alias="actionId")
    icon: str | None = None
    name_singular: str | None = Field(default=None, validation_alias="nameSingular")
    name_plural: str | None = Field(default=None, validation_alias="namePlural")
    language: str | None = None
    due_days: int | None = Field(default=None, validation_alias="dueDays")
    has_due_days: bool = Field(validation_alias="hasDueDays")
    currency_id: int | None = Field(default=None, validation_alias="currencyId")
    currency_code: str | None = Field(default=None, validation_alias="currencyCode")
    currency_rate: Decimal | None = Field(default=None, validation_alias="currencyRate")
    discount_percentage: Decimal | None = Field(default=None, validation_alias="discountPercentage")
    sub_total: Decimal = Field(validation_alias="subTotal")
    tax: Decimal
    total: Decimal
    open: Decimal | None = None
    group_open: Decimal | None = Field(default=None, validation_alias="groupOpen")
    date_last_booked: datetime | None = Field(default=None, validation_alias="dateLastBooked")
    qr_reference: str | None = Field(default=None, validation_alias="qrReference")
    iso11649_reference: str | None = Field(default=None, validation_alias="iso11649Reference")
    custom_reference: JsonValue = Field(default=None, validation_alias="customReference")
    custom: str | None = None
    notes: str | None = None
    attachment_count: int = Field(validation_alias="attachmentCount")
    allocation_count: int | None = Field(default=None, validation_alias="allocationCount")
    cost_center_ids: JsonValue = Field(default=None, validation_alias="costCenterIds")
    cost_center_numbers: JsonValue = Field(default=None, validation_alias="costCenterNumbers")
    sent: JsonValue = None
    sent_by: JsonValue = Field(default=None, validation_alias="sentBy")
    downloaded: JsonValue = None
    downloaded_by: JsonValue = Field(default=None, validation_alias="downloadedBy")
    recurrence: str | None = None
    start_date: UpstreamDate | None = Field(default=None, validation_alias="startDate")
    end_date: UpstreamDate | None = Field(default=None, validation_alias="endDate")
    days_before: int | None = Field(default=None, validation_alias="daysBefore")
    notify_type: str | None = Field(default=None, validation_alias="notifyType")
    notify_person_id: int | None = Field(default=None, validation_alias="notifyPersonId")
    notify_user_id: int | None = Field(default=None, validation_alias="notifyUserId")
    notify_email: str | None = Field(default=None, validation_alias="notifyEmail")
    book: bool
    is_book: bool = Field(validation_alias="isBook")
    closed: bool
    is_closed: bool = Field(validation_alias="isClosed")
    display_item_gross: bool = Field(validation_alias="displayItemGross")
    is_display_item_gross: bool = Field(validation_alias="isDisplayItemGross")
    add_stock: bool = Field(validation_alias="addStock")
    is_add_stock: bool = Field(validation_alias="isAddStock")
    remove_stock: bool = Field(validation_alias="removeStock")
    is_remove_stock: bool = Field(validation_alias="isRemoveStock")
    is_credit_note: bool = Field(validation_alias="isCreditNote")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class Order(_OrderFields):
    """One order, an entry of ``order/list.json`` (``docs/upstream/order.md``).

    An offer, invoice, delivery note or other order document, sales or purchase. Typed
    from the tables of ``order/create.json`` and ``update.json``: ``associate_id``
    (documented as the comma-separated ids of the business partners; one id per order
    here), ``category_id``, ``date`` (``YYYY-MM-DD``), ``account_id``, ``nr``,
    ``description``, ``status_id``, ``group_id``, ``previous_id``,
    ``responsible_person_id`` (documented as TEXT, an id; only seen ``null``),
    ``rounding_id``, ``language`` (``DE``, ``EN``, ``FR``, ``IT``), ``due_days``,
    ``currency_id``, ``currency_rate``, ``discount_percentage``, ``custom`` (XML),
    ``notes`` (HTML), ``is_display_item_gross``, ``recurrence``, ``start_date``,
    ``end_date``, ``days_before`` and the ``notify_*`` fields.

    Typed from observation: ``type`` (``SALES``, ``PURCHASE``), ``book_type`` (``DEBIT``
    for the sales, ``CREDIT`` for the purchase orders seen), ``associate_name``,
    ``account`` (the account's localised name), ``status_name``, ``name_singular`` and
    ``name_plural`` (localised, from the category), ``sent_status_id``, ``action_id``
    (seen empty), ``icon``, the amounts ``sub_total`` (net), ``tax`` and ``total``
    (gross), ``open`` and ``group_open`` (the amount still open, ``null`` for a draft),
    ``date_last_booked`` (a timestamp), ``qr_reference``, ``iso11649_reference``,
    ``currency_code``, ``attachment_count``, ``allocation_count``, the flags ``book``,
    ``closed``, ``received``, ``recurring``, ``add_stock``, ``remove_stock`` and
    ``display_item_gross`` with their ``is_*`` twins, ``has_due_days``,
    ``is_credit_note``, and the ``created*``/``last_updated*`` bookkeeping fields. Only
    seen as ``null`` and kept as sent: ``responsible_person_name``, ``custom_reference``,
    ``sent``, ``sent_by``, ``downloaded``, ``downloaded_by``, ``cost_center_ids``,
    ``cost_center_numbers``, ``date_due`` and ``date_received``.
    """

    account: str | None = None
    date_due: JsonValue = Field(default=None, validation_alias="dateDue")
    date_received: JsonValue = Field(default=None, validation_alias="dateReceived")
    received: bool
    is_received: bool = Field(validation_alias="isReceived")
    recurring: bool
    is_recurring: bool = Field(validation_alias="isRecurring")


class OrderDetail(_OrderFields):
    """One order as ``order/read.json`` returns it (``docs/upstream/order.md``).

    Observed on 2026-10-23 against the demo organisation: the read sends a different set
    of fields than the list. It has no ``account``, ``date_due``, ``date_received``,
    ``received`` nor ``recurring``, and adds the fields below. The fields both send are
    typed as on ``Order``; ``currency_code`` was ``null`` in the read of an order whose
    list entry says ``CHF``.

    ``items`` are typed from the create table (``OrderItem``). ``attachments`` are
    documented as an input but were only seen empty, so their items are kept as sent, as
    are ``file_id`` and ``recurrence_id`` (only seen ``null``). Typed from observation:
    ``category_name`` (localised), ``tax_type`` (``AGREED``), ``total_to_pay``,
    ``paid``, ``default_currency_total`` and ``rounding_difference`` (amounts), the
    flags ``due``, ``foreign_currency``, ``has_recurrence`` and ``file_replacement`` with
    its ``is_*`` twin, and ``hash``, an undocumented 32-character text that may be the
    token of a public link to the order document (not verified); the fixture recorder
    writes it as ``REDACTED``.
    """

    items: list[OrderItem] = Field(default_factory=list)
    attachments: list[JsonValue] = Field(default_factory=list)
    category_name: str | None = Field(default=None, validation_alias="categoryName")
    tax_type: str | None = Field(default=None, validation_alias="taxType")
    total_to_pay: Decimal | None = Field(default=None, validation_alias="totalToPay")
    paid: Decimal | None = None
    default_currency_total: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyTotal"
    )
    rounding_difference: Decimal | None = Field(default=None, validation_alias="roundingDifference")
    due: bool
    foreign_currency: bool = Field(validation_alias="foreignCurrency")
    has_recurrence: bool = Field(validation_alias="hasRecurrence")
    file_replacement: bool = Field(validation_alias="fileReplacement")
    is_file_replacement: bool = Field(validation_alias="isFileReplacement")
    hash: str | None = None
    file_id: JsonValue = Field(default=None, validation_alias="fileId")
    recurrence_id: JsonValue = Field(default=None, validation_alias="recurrenceId")


class OrderBookEntry(UpstreamModel):
    """One book entry of an order, an entry of ``order/bookentry/list.json``.

    "All the journal book entries that are created for an order (e.g. an invoice or a
    credit note), either automatically from items or manually by the user, like payments
    for example" (``docs/upstream/order.md``, Book entry). Typed from the tables of
    ``order/bookentry/create.json`` and ``update.json``: ``account_id`` (the contra
    account to the category's), ``amount``, ``currency_id``, ``currency_rate``, ``date``
    (``YYYY-MM-DD``), ``description``, ``reference``, ``tax_id`` and ``template_id``.

    Typed from observation on 2026-10-27, the entry a seeded purchase order booked
    (``tests/fixtures/order_bookentry_list/booked.json``): ``id``, ``order_id``,
    ``type`` (``GENERATED`` for one booked from the items), ``debit_id`` and
    ``debit_name``, ``credit_id`` and ``credit_name`` (the account's number and
    localised name), the amounts ``default_currency_amount``, ``net_amount`` and
    ``tax_amount``, ``rows`` (the bookings per account, tax rows apart, as a journal
    entry's ``JournalRow``), the flags ``is_allow_tax``, ``original`` and ``separate``,
    ``name`` (seen empty) and the ``created*``/``last_updated*`` bookkeeping fields.
    Kept as sent: ``allocations`` (only seen empty), ``cost_center_numbers`` (seen
    empty) and ``import_entry_id`` (only seen ``null``).
    """

    id: int
    order_id: int | None = Field(default=None, validation_alias="orderId")
    type: str | None = None
    date: UpstreamDate | None = None
    description: str | None = None
    reference: str | None = None
    name: str | None = None
    amount: Decimal | None = None
    default_currency_amount: Decimal | None = Field(
        default=None, validation_alias="defaultCurrencyAmount"
    )
    net_amount: Decimal | None = Field(default=None, validation_alias="netAmount")
    tax_amount: Decimal | None = Field(default=None, validation_alias="taxAmount")
    account_id: int | None = Field(default=None, validation_alias="accountId")
    debit_id: int | None = Field(default=None, validation_alias="debitId")
    debit_name: str | None = Field(default=None, validation_alias="debitName")
    credit_id: int | None = Field(default=None, validation_alias="creditId")
    credit_name: str | None = Field(default=None, validation_alias="creditName")
    tax_id: int | None = Field(default=None, validation_alias="taxId")
    template_id: int | None = Field(default=None, validation_alias="templateId")
    currency_id: int | None = Field(default=None, validation_alias="currencyId")
    currency_rate: Decimal | None = Field(default=None, validation_alias="currencyRate")
    is_allow_tax: bool | None = Field(default=None, validation_alias="isAllowTax")
    original: bool | None = None
    separate: bool | None = None
    rows: list[JournalRow] = Field(default_factory=list)
    allocations: list[JsonValue] = Field(default_factory=list)
    cost_center_numbers: JsonValue = Field(default=None, validation_alias="costCenterNumbers")
    import_entry_id: JsonValue = Field(default=None, validation_alias="importEntryId")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class OrderCategoryStatus(UpstreamModel):
    """One status of an order category, an item of ``OrderCategory.status``.

    Typed from the ``status`` table of ``order/category/create.json``
    (``docs/upstream/order.md``): ``icon`` (``BLUE``, ``GREEN``, ``RED``, ...), ``name``
    (localised, ``<values><de>Entwurf</de>...</values>``), ``action_id`` (what follows
    the status, ``CATEGORY_9`` or ``BOOK_TEMPLATE_3``; empty for none), ``is_add_stock``,
    ``is_book`` (whether orders in this status book journal entries), ``is_closed`` and
    ``is_remove_stock``. Typed from observation on 2026-10-24: ``id`` (the id
    ``create_order`` takes as ``status_id``), ``category_id``, ``pos``, the twins without
    ``is_`` and the ``created*``/``last_updated*`` bookkeeping fields; the first status of
    the invoice category came without ``created`` and with an empty ``createdBy``.
    """

    id: int
    category_id: int | None = Field(default=None, validation_alias="categoryId")
    name: str | None = None
    icon: str | None = None
    action_id: str | None = Field(default=None, validation_alias="actionId")
    pos: int | None = None
    book: bool
    is_book: bool = Field(validation_alias="isBook")
    add_stock: bool = Field(validation_alias="addStock")
    is_add_stock: bool = Field(validation_alias="isAddStock")
    remove_stock: bool = Field(validation_alias="removeStock")
    is_remove_stock: bool = Field(validation_alias="isRemoveStock")
    closed: bool
    is_closed: bool = Field(validation_alias="isClosed")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class OrderBookTemplate(UpstreamModel):
    """One book template of an order category, an item of ``OrderCategory.book_templates``.

    Typed from the ``bookTemplates`` table of ``order/category/create.json``:
    ``account_id`` (typically a bank account for a payment template), ``name``
    (localised), ``is_allow_tax`` and ``tax_id``. Typed from observation on 2026-10-24:
    ``id``, ``category_id``, ``pos``, the twin ``allow_tax``, ``text`` and ``value`` (only
    seen ``null``) and the ``created*``/``last_updated*`` bookkeeping fields.
    """

    id: int
    category_id: int | None = Field(default=None, validation_alias="categoryId")
    account_id: int | None = Field(default=None, validation_alias="accountId")
    tax_id: int | None = Field(default=None, validation_alias="taxId")
    name: str | None = None
    pos: int | None = None
    text: JsonValue = None
    value: JsonValue = None
    allow_tax: bool | None = Field(default=None, validation_alias="allowTax")
    is_allow_tax: bool | None = Field(default=None, validation_alias="isAllowTax")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class OrderCategory(UpstreamModel):
    """One order category, an entry of ``order/category/list.json`` (``docs/upstream/order.md``).

    "An order category is for example 'Offers', 'Invoices', 'Delivery notes', etc. A
    category contains the configuration for the order document and how it behaves." Its
    ``id`` is what ``create_order`` takes as ``category_id``, and one of its ``status``
    ids what it takes as ``status_id``.

    Typed from the tables of ``order/category/create.json`` and ``update.json``:
    ``account_id`` (typically the debtors account for sales), ``name_plural`` and
    ``name_singular`` (localised), ``status``, ``address_type``, ``book_templates``,
    ``book_type`` (``DEBIT``, ``CREDIT``), ``currency_id``, ``due_days``, ``file_id``,
    ``footer_template_id``, ``has_due_days``, ``header_template_id``,
    ``is_display_item_gross``, ``is_display_prices``, ``is_inactive``,
    ``is_switch_recipient``, ``layout_id``, ``mail_subject``, ``mail_template_id``,
    ``message``, ``responsible_person_id`` (documented as TEXT, an id; only seen
    ``null``), ``rounding_id``, ``sent_status_id``, ``sequence_nr_id`` and ``type``
    (``SALES``, ``PURCHASE``).

    Typed from observation on 2026-10-24 against the demo organisation (CashCtrl's six
    default sales categories): the answer is ``{"total": ..., "data": [...]}``; ``id``,
    ``name`` (seen equal to ``name_singular``), ``pos``, ``default_status_id``,
    ``sequence_nr_id_inherited``, ``template_id``, ``layout_name`` (localised),
    ``value`` (the id as text), the twins without ``is_`` and ``is_free`` with its twin,
    and the ``created*``/``last_updated*`` bookkeeping fields. ``attachments`` were only
    seen empty and are kept as sent; ``responsible_person_name``, ``text`` and
    ``type_name`` were only seen ``null``.
    """

    id: int
    type: str
    name: str | None = None
    name_singular: str | None = Field(default=None, validation_alias="nameSingular")
    name_plural: str | None = Field(default=None, validation_alias="namePlural")
    pos: int | None = None
    account_id: int | None = Field(default=None, validation_alias="accountId")
    address_type: str | None = Field(default=None, validation_alias="addressType")
    book_type: str | None = Field(default=None, validation_alias="bookType")
    currency_id: int | None = Field(default=None, validation_alias="currencyId")
    due_days: int | None = Field(default=None, validation_alias="dueDays")
    has_due_days: bool | None = Field(default=None, validation_alias="hasDueDays")
    default_status_id: int | None = Field(default=None, validation_alias="defaultStatusId")
    sent_status_id: int | None = Field(default=None, validation_alias="sentStatusId")
    sequence_nr_id: int | None = Field(default=None, validation_alias="sequenceNrId")
    sequence_nr_id_inherited: int | None = Field(
        default=None, validation_alias="sequenceNrIdInherited"
    )
    rounding_id: int | None = Field(default=None, validation_alias="roundingId")
    responsible_person_id: int | None = Field(default=None, validation_alias="responsiblePersonId")
    responsible_person_name: JsonValue = Field(
        default=None, validation_alias="responsiblePersonName"
    )
    file_id: int | None = Field(default=None, validation_alias="fileId")
    footer_template_id: int | None = Field(default=None, validation_alias="footerTemplateId")
    header_template_id: int | None = Field(default=None, validation_alias="headerTemplateId")
    mail_template_id: int | None = Field(default=None, validation_alias="mailTemplateId")
    template_id: int | None = Field(default=None, validation_alias="templateId")
    layout_id: int | None = Field(default=None, validation_alias="layoutId")
    layout_name: str | None = Field(default=None, validation_alias="layoutName")
    mail_subject: str | None = Field(default=None, validation_alias="mailSubject")
    message: str | None = None
    status: list[OrderCategoryStatus] = Field(default_factory=list)
    book_templates: list[OrderBookTemplate] = Field(
        default_factory=list, validation_alias="bookTemplates"
    )
    attachments: list[JsonValue] = Field(default_factory=list)
    display_item_gross: bool | None = Field(default=None, validation_alias="displayItemGross")
    is_display_item_gross: bool | None = Field(default=None, validation_alias="isDisplayItemGross")
    display_prices: bool | None = Field(default=None, validation_alias="displayPrices")
    is_display_prices: bool | None = Field(default=None, validation_alias="isDisplayPrices")
    free: bool | None = None
    is_free: bool | None = Field(default=None, validation_alias="isFree")
    inactive: bool | None = None
    is_inactive: bool | None = Field(default=None, validation_alias="isInactive")
    switch_recipient: bool | None = Field(default=None, validation_alias="switchRecipient")
    is_switch_recipient: bool | None = Field(default=None, validation_alias="isSwitchRecipient")
    text: JsonValue = None
    type_name: JsonValue = Field(default=None, validation_alias="typeName")
    value: str | None = None
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


CustomFieldType = Literal[
    "JOURNAL", "ACCOUNT", "INVENTORY_ARTICLE", "INVENTORY_ASSET", "ORDER", "PERSON", "FILE",
    "SALARY_STATEMENT",
]  # fmt: skip
"""``type`` of ``customfield/list.json``, the module: "Possible values: JOURNAL, ACCOUNT, ..."."""


class CustomField(UpstreamModel):
    """One custom field, an entry of ``customfield/list.json`` (``docs/upstream/common.md``).

    A field of the organisation's own on the records of one module (``type``); a write
    task sets its value as ``customField<id>`` in ``custom``. Typed from the tables of
    ``customfield/create.json`` and ``update.json`` alone: the demo organisation has no
    custom field, and ``customfield/list.json`` for ``PERSON`` answered ``{"total": 0,
    "data": []}`` on 2026-10-27, so no record was observed. Every field but ``id`` is
    therefore optional, and the two whose wire type the tables leave open are kept as
    upstream sends them: ``group_id`` (TEXT, "The ID of the custom field group") and
    ``values`` (TEXT holding a JSON array, ``["red","green","blue"]``, the choices of a
    ``COMBOBOX``). ``type`` and ``data_type`` (``TEXT``, ``TEXTAREA``, ``CHECKBOX``,
    ``DATE``, ``COMBOBOX``, ``NUMBER``, ``ACCOUNT``, ``PERSON``) stay strings;
    ``row_label``, ``field_label``, ``field_info`` and ``field_text_right`` may hold
    localised text as ``<values><de>...</de></values>``; ``variable_name`` is the
    optional ``$name`` used instead of ``$customField<ID>``. The ``created*`` and
    ``last_updated*`` bookkeeping fields every other list sends are assumed here, not
    observed.
    """

    id: int
    type: str | None = None
    data_type: str | None = Field(default=None, validation_alias="dataType")
    row_label: str | None = Field(default=None, validation_alias="rowLabel")
    field_label: str | None = Field(default=None, validation_alias="fieldLabel")
    field_info: str | None = Field(default=None, validation_alias="fieldInfo")
    field_text_right: str | None = Field(default=None, validation_alias="fieldTextRight")
    group_id: JsonValue = Field(default=None, validation_alias="groupId")
    is_inactive: bool | None = Field(default=None, validation_alias="isInactive")
    is_multi: bool | None = Field(default=None, validation_alias="isMulti")
    max_width: Decimal | None = Field(default=None, validation_alias="maxWidth")
    values: JsonValue = None
    variable_name: str | None = Field(default=None, validation_alias="variableName")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class PersonCategory(UpstreamModel):
    """One person category, an entry of ``person/category/list.json`` (``docs/upstream/person.md``).

    A group persons are filed in, possibly below a parent category. Its ``id`` is what
    ``list_persons``, ``create_person`` and ``update_person`` take as ``category_id``.
    Typed from the tables of ``person/category/create.json`` and ``update.json``:
    ``name`` (localised, ``<values><de>Kunden</de><en>Customers</en>...</values>``),
    ``discount_percentage`` (for orders), ``parent_id`` and ``sequence_nr_id`` (the
    sequence that numbers its persons, inherited from the parent when empty). Typed from
    observation on 2026-10-27 (CashCtrl's four default categories, all at the top level):
    ``id`` and the ``created*``/``last_updated*`` bookkeeping fields;
    ``sequence_nr_id_inherited``, ``discount_inherited`` and ``discount_effective`` were
    only seen ``null`` and are kept as sent.
    """

    id: int
    name: str
    parent_id: int | None = Field(default=None, validation_alias="parentId")
    sequence_nr_id: int | None = Field(default=None, validation_alias="sequenceNrId")
    sequence_nr_id_inherited: JsonValue = Field(
        default=None, validation_alias="sequenceNrIdInherited"
    )
    discount_percentage: Decimal | None = Field(default=None, validation_alias="discountPercentage")
    discount_inherited: JsonValue = Field(default=None, validation_alias="discountInherited")
    discount_effective: JsonValue = Field(default=None, validation_alias="discountEffective")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class PersonTitle(UpstreamModel):
    """One title, an entry of ``person/title/list.json`` (``docs/upstream/person.md``).

    A form of address with its letter salutation. Its ``id`` is what ``create_person``
    and ``update_person`` take as ``title_id``. Typed from the tables of
    ``person/title/create.json`` and ``update.json``: ``name`` (the title itself,
    localised, ``<values><de>Herr</de><en>Mr.</en>...</values>``), ``gender`` (``MALE``
    or ``FEMALE``, a string) and ``sentence`` (the letter salutation, localised). Typed
    from observation on 2026-10-27 (CashCtrl's three default titles): ``id``, ``value``
    (the id as text), the ``created*``/``last_updated*`` bookkeeping fields, and
    ``text``, only seen ``null`` and kept as sent. The title without a ``gender`` had no
    ``sentence``.
    """

    id: int
    name: str
    gender: str | None = None
    sentence: str | None = None
    text: JsonValue = None
    value: str | None = None
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class AccountCategory(UpstreamModel):
    """One account category, an entry of ``account/category/list.json`` (``account.md``).

    A group of the chart of accounts; the groups nest by ``parent_id``. Its ``id`` is the
    ``category_id`` an account carries and ``list_accounts`` takes. Typed from the tables
    of ``account/category/create.json`` and ``update.json``: ``name`` (localised as
    ``<values><de>...</de></values>``; the five top-level categories' plain,
    ``Assets``), ``number`` (optional text, "Must be numeric", used for sorting: ``"1"``,
    ``"10"``, ``"100"``; every recorded category has one) and ``parent_id`` (``None`` at
    the top level). Typed from
    observation on 2026-10-27 (CashCtrl's default chart, 38 categories): ``id``,
    ``account_class`` (seen: ``ASSET``, ``LIABILITY``, ``EXPENSE``, ``REVENUE``,
    ``BALANCE``, one per top-level category and inherited below it), ``full_name`` (the
    number and the name, ``"1 Assets"``), ``system`` with its ``is_system`` twin (true
    for the five top-level categories only) and the ``created*``/``last_updated*``
    bookkeeping fields.

    ``account/category/tree.json`` answers the same 38 categories nested, each child list
    under ``data``, and its ``total`` counts the five top-level ones; it adds only
    display fields (``text``, the name in one language; ``cls``; ``leaf``) and lacks
    ``account_class`` and ``full_name`` (compared on 2026-10-27), so the flat list is
    the one wrapped.
    """

    id: int
    number: str | None = None
    name: str
    parent_id: int | None = Field(default=None, validation_alias="parentId")
    account_class: str | None = Field(default=None, validation_alias="accountClass")
    full_name: str | None = Field(default=None, validation_alias="fullName")
    system: bool
    is_system: bool = Field(validation_alias="isSystem")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class CostCenter(UpstreamModel):
    """One cost center, an entry of ``account/costcenter/list.json`` (``docs/upstream/account.md``).

    A cost center or cost unit amounts are allocated to: its ``id`` is the
    ``to_cost_center_id`` of an allocation (``create_journal_entry``,
    ``update_journal_entry``, the items of ``create_order``). Typed from the tables of
    ``account/costcenter/create.json`` and ``update.json`` alone: the demo organisation
    has no cost center, and ``account/costcenter/list.json`` answered ``{"total": 0,
    "data": []}`` on 2026-10-27, so no record was observed. Every field but ``id`` is
    therefore optional: ``name`` (localised), ``category_id``, ``notes`` (HTML),
    ``is_inactive``, ``target_min`` and ``target_max``, and ``attachments``, documented
    as a list of ``{fileId}`` and kept as sent, as ``Location``'s are. ``number`` is
    documented as the account number is ("NUMBER", "Must be numeric but can contain a
    decimal point"), which comes as text, and is kept as sent. The list documents
    ``fiscalPeriodId``, "from which we retrieve the balances", so its records presumably
    carry balances; never observed, they are not modelled. The ``created*`` and
    ``last_updated*`` bookkeeping fields every other list sends are assumed here, not
    observed.
    """

    id: int
    number: JsonValue = None
    name: str | None = None
    category_id: int | None = Field(default=None, validation_alias="categoryId")
    notes: str | None = None
    is_inactive: bool | None = Field(default=None, validation_alias="isInactive")
    target_min: Decimal | None = Field(default=None, validation_alias="targetMin")
    target_max: Decimal | None = Field(default=None, validation_alias="targetMax")
    attachments: list[JsonValue] = Field(default_factory=list)
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class _LocationFields(UpstreamModel):
    """The fields of a ``location/list.json`` entry that ``LocationProjection`` keeps."""

    id: int
    name: str
    type: str | None = None
    org_name: str | None = Field(default=None, validation_alias="orgName")
    address: str | None = None
    street_name: str | None = Field(default=None, validation_alias="streetName")
    street_number: str | None = Field(default=None, validation_alias="streetNumber")
    zip: str | None = None
    city: str | None = None
    canton: str | None = None
    country: str | None = None
    full_address: str | None = Field(default=None, validation_alias="fullAddress")
    full_address_csv: JsonValue = Field(default=None, validation_alias="fullAddressCsv")
    email: str | None = None
    phone_main: str | None = Field(default=None, validation_alias="phoneMain")
    phone_salary_cert: str | None = Field(default=None, validation_alias="phoneSalaryCert")
    url: str | None = None
    vat_uid: str | None = Field(default=None, validation_alias="vatUid")
    bur_nr: str | None = Field(default=None, validation_alias="burNr")
    footer: str | None = None
    logo_file_id: int | None = Field(default=None, validation_alias="logoFileId")
    bank_account_id: int | None = Field(default=None, validation_alias="bankAccountId")
    bic: JsonValue = None
    qr_first_digits: JsonValue = Field(default=None, validation_alias="qrFirstDigits")
    attachments: list[JsonValue] = Field(default_factory=list)
    text: str | None = None
    value: str | None = None
    list_cls: str | None = Field(default=None, validation_alias="listCls")
    inactive: bool
    is_inactive: bool = Field(validation_alias="isInactive")
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    last_updated_by: AuditUser = Field(default=None, validation_alias="lastUpdatedBy")


class Location(_LocationFields):
    """One location, an entry of ``location/list.json`` (``docs/upstream/meta.md``).

    A site of the organisation: its headquarters (``type`` ``MAIN``), a branch, a
    storage site or another. Its ``id`` is what ``create_person`` and ``update_person``
    take as ``location_id``, an employee's workplace. Typed from the tables of
    ``location/create.json`` and ``update.json``: ``name`` (for identification only, not
    used in an address), ``type`` (``MAIN``, ``BRANCH``, ``STORAGE``, ``OTHER``; a
    string), ``org_name`` (the company name), ``address``, ``zip``, ``city``, ``canton``,
    ``country`` (ISO 3166 alpha-3, ``CHE``), ``email``, ``phone_main``,
    ``phone_salary_cert``, ``url``, ``vat_uid``, ``bur_nr``, ``footer`` (HTML),
    ``logo_file_id``, ``bank_account_id`` and ``is_inactive``. Typed from observation on
    2026-10-27 (the demo organisation's one location, created by hand with placeholder
    data, ``docs/demo-org.md``): ``id``, ``street_name`` and ``street_number``
    (``address`` split), ``full_address`` (the company name and the address as printed,
    a line each), ``text`` (the name) and ``value`` (the id as text),
    ``list_cls``, ``attachments`` (only seen empty, kept as sent), the twin ``inactive``
    and the ``created*``/``last_updated*`` bookkeeping fields. Only seen ``null`` and
    kept as sent: ``full_address_csv``, ``qr_first_digits``, ``bic``, ``iban`` and
    ``qr_iban``. No table documents the last three: the documented link to the bank is
    ``bank_account_id``.

    This read model stays faithful; ``list_locations`` returns ``LocationProjection``,
    which leaves out ``iban`` and ``qr_iban`` (ADR-0017).
    """

    iban: JsonValue = None
    qr_iban: JsonValue = Field(default=None, validation_alias="qrIban")


class LocationProjection(_LocationFields):
    """A ``location/list.json`` entry without ``iban`` and ``qr_iban``, the bank account numbers.

    What ``list_locations`` returns (ADR-0017): every field of ``Location`` but those two,
    under the same names; ``bank_account_id`` names the bank account instead.
    """


class HistoryEntry(UpstreamModel):
    """One entry of the history, the audit log, an entry of ``history/list.json``.

    ``docs/upstream/common.md``, History, documents the list's parameters only
    (``orderId``, ``personId``, ``statementId`` among them). Typed from observation on
    2026-10-27 (``tests/fixtures/history_list/order.json``, a seeded order's): ``id``,
    ``created`` (when the change was made) and ``created_by`` (who made it: an API user,
    which upstream names as ``API:`` and the first four characters of its key, shows as
    ``API:REDACTED``, as on every record), ``type`` (the module, ``ORDER`` seen),
    ``change_type`` (``CREATE`` and ``STATUS`` in the fixture; ``UPDATE`` seen on
    2026-10-27, not in a fixture, since the recording that showed it was overwritten),
    the record it concerns (``order_id``, ``person_id`` the order's partner,
    ``statement_id`` only seen ``null``) and ``message``, upstream's text of the change,
    kept as sent (G5 (12) of 2026-10-28): it names the record (``Rechnung 'EK-2026-001'
    created.``) and may name a person; no recorded message carries an API user tag, so
    it is not masked.
    """

    id: int
    created: datetime | None = None
    created_by: AuditUser = Field(default=None, validation_alias="createdBy")
    type: str | None = None
    change_type: str | None = Field(default=None, validation_alias="changeType")
    order_id: int | None = Field(default=None, validation_alias="orderId")
    person_id: int | None = Field(default=None, validation_alias="personId")
    statement_id: int | None = Field(default=None, validation_alias="statementId")
    message: str | None = None


class ReportTreeNode(UpstreamModel):
    """One node of ``report/tree.json``, a report collection or a report element.

    ``docs/upstream/report.md``: "A report collection is a collection of report elements
    which are grouped together and form one document"; "A report element is the actual
    report, for example the balance sheet or profit and loss statement." The answer is
    ``{"total": ..., "data": [...]}``, ``total`` counting the top-level nodes. The
    documentation describes no field; typed from observation on 2026-10-27 (CashCtrl's
    default reports: six collections and two elements at the top level, 44 nodes, every
    field but ``data`` on every node).

    ``id`` is the tree's own text key (``collection-1``, ``element-1``), which no other
    operation takes. An element is a ``leaf`` with ``element_id``, the ``element_id`` of
    ``get_report_data``, and its report ``type`` (``BALANCE``, ``PLS``,
    ``OPEN_DEBTORS``, ...: the types of ``report/element/create.json``, a string),
    ``type_name`` and ``xclass``; a collection has ``element_id``, ``type``,
    ``type_name`` and ``xclass`` ``None`` and its elements in ``data``. Both carry
    ``collection_id`` (``None`` for an element outside a collection), ``text`` (the name,
    seen in German and in English), ``set_id``, ``expanded``, ``cls``, ``qtip`` and the
    flags ``system``, ``pro`` and ``beta`` with their ``is_*`` twins.
    """

    id: str
    text: str | None = None
    type: str | None = None
    type_name: str | None = Field(default=None, validation_alias="typeName")
    element_id: int | None = Field(default=None, validation_alias="elementId")
    collection_id: int | None = Field(default=None, validation_alias="collectionId")
    set_id: int | None = Field(default=None, validation_alias="setId")
    xclass: str | None = None
    qtip: str | None = None
    cls: str | None = None
    leaf: bool
    expanded: bool
    system: bool
    is_system: bool = Field(validation_alias="isSystem")
    pro: bool
    is_pro: bool = Field(validation_alias="isPro")
    beta: bool
    is_beta: bool = Field(validation_alias="isBeta")
    data: list["ReportTreeNode"] = Field(default_factory=list)


class ReportData(UpstreamModel):
    """The answer of ``report/element/data.json``: one report's data for a period.

    ``docs/upstream/report.md``, "Read JSON data": "Returns the JSON data of a single
    element by ID for the given time period." The documentation gives no schema, and
    the rows differ by report type (``report/element/create.json`` lists 41), so ``data``
    and ``properties`` are kept as upstream sends them (``JsonValue``; decided by
    Johannes on 2026-10-27, ADR-0003): rows under upstream's camelCase names
    (``endAmount``), amounts as JSON numbers, not ``Decimal``.

    Observed on 2026-10-27 for the balance sheet (``BALANCE``) of fiscal period 2025:
    ``{"total": 2, "data": [...], "properties": {"columns": [...]}}``. ``total`` counts
    the top-level rows (assets, liabilities and equity). Each row is a node with its
    child rows in ``data``: ``text`` (the label, ``1020 Bank account``), ``level``,
    ``leaf``, ``accountId`` (an account's id, ``null`` on a category or a total),
    ``cls`` (``category level-0``, ``account level-3``, ``total level-3``), the amounts
    (``openingAmount``, ``endAmount``, ``previousAmount``, ``changeAmount``, ... and
    their ``dc*`` twins) and the flags ``isTotal`` and ``isForeignCurrency``; a
    category's total is a row of its own. ``properties.columns`` lists the columns the
    report shows, each with its ``title`` (``01/01/2025``) and ``dataIndex``, the row
    field it shows (``dcOpeningAmount``).

    The envelope, ``total`` a number and ``data`` a list, was observed for ``BALANCE``
    alone and is assumed for every report type: an answer of another shape (a chart
    without a ``total``, ``data`` as an object) fails to parse with ``ValidationError``
    instead of being returned misread. Neither the answer nor the request names the
    report's type.
    """

    total: int
    data: list[JsonValue]
    properties: JsonValue = None


# The write tools' payloads (``tasks_write.py``) and their outcomes.
#
# Input models mirror the JSON arrays the create and update tables document (``items``,
# ``addresses``, ``contacts``, ...): snake_case fields, typed from those tables, with the
# documented value sets as ``Literal``. ``validation_alias=AliasChoices(snake, camel)``
# accepts both spellings and shows the snake_case name in the tool schema, as the tool
# arguments are snake_case; ``serialization_alias`` is the upstream name, which
# ``api/_form.py`` writes into the form's JSON. These models only ever go upstream: no
# result carries them (a preview shows the encoded form fields). Unknown keys are
# refused, so a misspelt key never goes missing silently.

NotifyType = Literal["NONE", "USER", "PERSON", "RESPONSIBLE_PERSON", "EMAIL"]
"""``notifyType`` of journal entries and orders: "Possible values: NONE, USER, PERSON, ..."."""

Recurrence = Literal[
    "MONTHLY", "WEEKLY", "DAILY", "YEARLY", "SEMESTRAL", "QUARTERLY", "BI_MONTHLY", "BI_WEEKLY"
]
"""``recurrence`` of journal entries and orders: "Possible values: MONTHLY, WEEKLY, ..."."""

Language = Literal["DE", "EN", "FR", "IT"]
"""``language`` of persons and orders: "Possible values: DE, EN, FR, IT"."""

Color = Literal[
    "BLUE", "GREEN", "RED", "YELLOW", "ORANGE", "BLACK", "GRAY", "BROWN", "VIOLET", "PINK"
]
"""``color`` of a person: "Possible values: BLUE, GREEN, RED, ..."; white when not set."""

AddressType = Literal["MAIN", "INVOICE", "DELIVERY", "SALARY", "HISTORICAL", "OTHER"]
"""``type`` of an address: "Possible values: MAIN, INVOICE, DELIVERY, SALARY, ..."."""

Canton = Literal[
    "AG", "AI", "AR", "BE", "BL", "BS", "FR", "GE", "GL", "GR", "JU", "LU", "NE",
    "NW", "OW", "SG", "SH", "SO", "SZ", "TG", "TI", "UR", "VD", "VS", "ZG", "ZH",
]  # fmt: skip
"""``canton`` of an address, Switzerland only: "Possible values: AG, AI, AR, ..."."""

ContactType = Literal[
    "EMAIL_INVOICE", "EMAIL_WORK", "EMAIL_PRIVATE", "PHONE_RECEPTION", "PHONE_WORK",
    "PHONE_PRIVATE", "MOBILE_WORK", "MOBILE_PRIVATE", "FAX", "WEBSITE", "MESSENGER", "OTHER",
]  # fmt: skip
"""``type`` of a contact: "Possible values: EMAIL_INVOICE, EMAIL_WORK, ..."."""

BankAccountType = Literal["DEFAULT", "ORDER", "SALARY", "HISTORICAL", "OTHER"]
"""``type`` of a bank account: "Possible values: DEFAULT, ORDER, SALARY, HISTORICAL, OTHER"."""

OrderItemType = Literal["ARTICLE", "TEXT", "PAGEBREAK", "SUBTOTAL", "TITLE", "OPTIONTOTAL"]
"""``type`` of an order item: "Defaults to ARTICLE. Possible values: ARTICLE, TEXT, ..."."""


class _Input(UpstreamModel):
    """An object of a JSON array a write takes; unknown keys are refused."""

    model_config = ConfigDict(extra="forbid")


class AllocationInput(_Input):
    """One allocation to a cost center, an item of ``allocations`` (journal, order items).

    Attributes:
        share: ``share``, the allocation share; shares 3 and 1 split the amount 3:1.
        to_cost_center_id: ``toCostCenterId``, the cost center to allocate to.
    """

    share: Decimal
    to_cost_center_id: int = Field(
        validation_alias=AliasChoices("to_cost_center_id", "toCostCenterId"),
        serialization_alias="toCostCenterId",
    )


class AttachmentInput(_Input):
    """One file to attach, an item of ``attachments`` (journal entries, persons, orders).

    Attributes:
        file_id: ``fileId``, the id of a file uploaded through the File API.
    """

    file_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("file_id", "fileId"),
        serialization_alias="fileId",
    )


class JournalItemInput(_Input):
    """One line of a collective journal entry, an item of ``items`` (``journal/create.json``).

    Attributes:
        account_id: ``accountId``, the account of the line (an id from ``list_accounts``).
        allocations: ``allocations``, the line's allocations to cost centers.
        associate_id: ``associateId``, a person's id from ``list_persons``. Upstream also
            takes a name, which creates a new person; this package takes ids only, and a
            new person is created with ``create_person``.
        credit: ``credit``, the amount on the credit side; ``debit`` or ``credit`` is set.
        debit: ``debit``, the amount on the debit side.
        description: ``description``, the text of the line.
        tax_id: ``taxId``, a tax code's id from ``list_tax_codes``.
    """

    account_id: int = Field(
        validation_alias=AliasChoices("account_id", "accountId"), serialization_alias="accountId"
    )
    allocations: list[AllocationInput] | None = None
    associate_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("associate_id", "associateId"),
        serialization_alias="associateId",
    )
    credit: Decimal | None = None
    debit: Decimal | None = None
    description: str | None = None
    tax_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("tax_id", "taxId"),
        serialization_alias="taxId",
    )


class OrderItemInput(_Input):
    """One item of an order, an item of ``items`` (``order/create.json``).

    Attributes:
        account_id: ``accountId``, the revenue account for sales, the expense account for
            purchase (an id from ``list_accounts``).
        name: ``name``, the item's name.
        unit_price: ``unitPrice``, the price of one unit. Observed on the demo
            organisation: CashCtrl read the seeded unit prices as gross, VAT included
            (``baseValue`` ``GROSS``, ``docs/demo-org.md``).
        allocations: ``allocations``, the item's allocations to cost centers.
        article_nr: ``articleNr``, the article number.
        description: ``description``, a description of the item.
        discount_percentage: ``discountPercentage``, a discount on the item price.
        inventory_id: ``inventoryId``, an inventory article.
        quantity: ``quantity``, the number of units; upstream's default is 1.
        tax_id: ``taxId``, a tax code's id from ``list_tax_codes``.
        type: ``type``; upstream's default is ``ARTICLE``.
        unit_id: ``unitId``, the unit (pcs., hours); documented as TEXT holding an id.
    """

    account_id: int = Field(
        validation_alias=AliasChoices("account_id", "accountId"), serialization_alias="accountId"
    )
    name: str
    unit_price: Decimal = Field(
        validation_alias=AliasChoices("unit_price", "unitPrice"), serialization_alias="unitPrice"
    )
    allocations: list[AllocationInput] | None = None
    article_nr: str | None = Field(
        default=None,
        validation_alias=AliasChoices("article_nr", "articleNr"),
        serialization_alias="articleNr",
    )
    description: str | None = None
    discount_percentage: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("discount_percentage", "discountPercentage"),
        serialization_alias="discountPercentage",
    )
    inventory_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("inventory_id", "inventoryId"),
        serialization_alias="inventoryId",
    )
    quantity: Decimal | None = None
    tax_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("tax_id", "taxId"),
        serialization_alias="taxId",
    )
    type: OrderItemType | None = None
    unit_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("unit_id", "unitId"),
        serialization_alias="unitId",
    )


class PersonAddressInput(_Input):
    """One address of a person, an item of ``addresses`` (``person/create.json``).

    Attributes:
        type: ``type``, e.g. ``MAIN`` or ``INVOICE``.
        address: ``address``, street, house number and more; may span lines.
        canton: ``canton``, Switzerland only, e.g. ``ZH``.
        city: ``city``.
        company: ``company``, the recipient's company name.
        country: ``country``, ISO 3166 alpha-3, e.g. ``CHE`` (upstream lists the codes).
        first_name: ``firstName``, the recipient's first name.
        is_hide_company: ``isHideCompany``, no company name in the address window.
        is_hide_name: ``isHideName``, no title and name in the address window.
        last_name: ``lastName``, the recipient's last name.
        zip: ``zip``, the postal code.
    """

    type: AddressType
    address: str | None = None
    canton: Canton | None = None
    city: str | None = None
    company: str | None = None
    country: str | None = None
    first_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("first_name", "firstName"),
        serialization_alias="firstName",
    )
    is_hide_company: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("is_hide_company", "isHideCompany"),
        serialization_alias="isHideCompany",
    )
    is_hide_name: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("is_hide_name", "isHideName"),
        serialization_alias="isHideName",
    )
    last_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("last_name", "lastName"),
        serialization_alias="lastName",
    )
    zip: str | None = None


class PersonContactInput(_Input):
    """One piece of contact information, an item of ``contacts`` (``person/create.json``).

    Attributes:
        address: ``address``, the e-mail address, phone number or URL itself.
        type: ``type``, e.g. ``EMAIL_WORK`` or ``PHONE_WORK``.
        notes: ``notes``, a short note (at most 255 characters).
    """

    address: str
    type: ContactType
    notes: str | None = None


class BankAccountInput(_Input):
    """One bank account of a person, an item of ``bankAccounts`` (``person/create.json``).

    Attributes:
        iban: ``iban``, at most 32 characters.
        type: ``type``, what the account is used for, e.g. ``DEFAULT``.
        bic: ``bic``, at most 11 characters.
        notes: ``notes``, at most 255 characters.
    """

    iban: str
    type: BankAccountType
    bic: str | None = None
    notes: str | None = None


class ChildInput(_Input):
    """One child of an employee or family, an item of ``children`` (``person/create.json``).

    Attributes:
        name: ``name``, first and last name.
        date_benefit_begin: ``dateBenefitBegin``, child benefit start.
        date_benefit_end: ``dateBenefitEnd``, child benefit end.
        date_birth: ``dateBirth``.
        date_in_education: ``dateInEducation``, in education since.
        notes: ``notes``, at most 255 characters.
    """

    name: str
    date_benefit_begin: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_benefit_begin", "dateBenefitBegin"),
        serialization_alias="dateBenefitBegin",
    )
    date_benefit_end: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_benefit_end", "dateBenefitEnd"),
        serialization_alias="dateBenefitEnd",
    )
    date_birth: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_birth", "dateBirth"),
        serialization_alias="dateBirth",
    )
    date_in_education: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_in_education", "dateInEducation"),
        serialization_alias="dateInEducation",
    )
    notes: str | None = None


class InsuranceContractInput(_Input):
    """One insurance contract, an item of ``insuranceContracts`` (``person/create.json``).

    Attributes:
        type_id: ``typeId``, the insurance type (AHV, BVG, ...).
        contract_nr: ``contractNr``, the contract number.
        sub_nr: ``subNr``, a sub-contract number.
    """

    type_id: int = Field(
        validation_alias=AliasChoices("type_id", "typeId"), serialization_alias="typeId"
    )
    contract_nr: str | None = Field(
        default=None,
        validation_alias=AliasChoices("contract_nr", "contractNr"),
        serialization_alias="contractNr",
    )
    sub_nr: str | None = Field(
        default=None,
        validation_alias=AliasChoices("sub_nr", "subNr"),
        serialization_alias="subNr",
    )


class ServicePeriodInput(_Input):
    """One service period of an employee, an item of ``servicePeriods`` (``person/create.json``).

    Attributes:
        date_entry: ``dateEntry``, the entry date.
        date_exit: ``dateExit``, the exit date; none for the current period.
        notes: ``notes``, at most 255 characters.
    """

    date_entry: date = Field(
        validation_alias=AliasChoices("date_entry", "dateEntry"), serialization_alias="dateEntry"
    )
    date_exit: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_exit", "dateExit"),
        serialization_alias="dateExit",
    )
    notes: str | None = None


class WriteAnswer(UpstreamModel):
    """The answer of a create, update or delete: ``{"success": true, "message": ...}``.

    ``docs/upstream/`` says only "Returns either a success or multiple error messages"
    (or "a success or error message" for a delete). Observed on 2026-10-23 when
    ``scripts/seed_demo.py`` seeded the demo organisation: ``person/create.json``,
    ``journal/create.json`` and ``order/create.json`` answer with ``success``,
    ``message`` and ``insertId``, a JSON integer, the new record's id. A refusal
    (``"success": false``) never gets here: ``_client.classify`` raises it.

    Attributes:
        success: ``True``.
        insert_id: ``insertId``, the id of the record created; ``None`` when absent.
        message: Upstream's message, in the language of the request.
    """

    success: bool
    insert_id: int | None = Field(default=None, validation_alias="insertId")
    message: str | None = None


class WritePreview[T](UpstreamModel):
    """What a write tool would send, returned while ``confirm`` is false; nothing was written.

    Attributes:
        performed: ``False``: no write was sent. The tag that tells a preview from a
            ``WriteResult``.
        endpoint: The operation that would be called, e.g. ``journal/create.json``.
        payload: The exact form fields upstream would receive, upstream name to encoded
            text, e.g. ``{"debitId": "3", "amount": "100.00"}``: booleans ``true`` or
            ``false``, dates ``YYYY-MM-DD``, lists as JSON, ``custom`` as XML. A personal
            identifier, ``ssn`` or the ``iban`` of an item of ``bankAccounts``, shows as
            ``REDACTED``; upstream receives the value (ADR-0017).
        before: For an update or a delete, the record as upstream holds it now, read with
            ``read.json``, as the task's projection, without ``ssn`` and ``iban``
            (ADR-0017); ``None`` for a create.
        changes: For an update, the fields the call changes, upstream name to encoded
            text, a personal identifier as ``REDACTED``; ``None`` otherwise.
    """

    performed: Literal[False] = False
    endpoint: str
    payload: dict[str, str]
    before: T | None = None
    changes: dict[str, str] | None = None


class WriteResult(UpstreamModel):
    """What a write tool did, returned when ``confirm`` is true: upstream accepted the write.

    Attributes:
        performed: ``True``: the write was sent and upstream answered ``success: true``.
        insert_id: The new record's id upstream answered (``insertId``); ``None`` when
            the answer carries none.
        message: Upstream's message, e.g. that the record was saved.
    """

    performed: Literal[True] = True
    insert_id: int | None = None
    message: str | None = None
