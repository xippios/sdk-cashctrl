"""Write tasks for CashCtrl: create, update and delete journal entries, persons and orders.

Served only by ``xippios-cashctrl-mcp-write``, never by the read-only server and never
on the HTTP router (conventions §8). List the sync names in ``__all__``.

``org: str`` is the first, required parameter of every write task, and ``confirm: bool =
False`` its last. The gate is ``confirm is True``: from Python, anything but ``True``
(``"false"``, ``1``, ``[0]``) previews; over MCP the tool schema turns ``"true"``,
``"yes"``, ``"1"`` and ``1`` into ``True`` and ``"false"``, ``"no"``, ``"0"`` and ``0``
into ``False``, and refuses anything else. The decisions taken for these tools on
2026-10-23 (the wave 2 interview):

1. **Preview.** While ``confirm`` is false a task writes nothing and returns a
   ``WritePreview``: the exact form ``payload`` upstream would receive (upstream names,
   encoded values) and, for an update or a delete, the record as it is now (``before``),
   for an update next to the ``changes``. A create's preview sends no request; an
   update's or a delete's sends one read, never a write. With ``confirm`` true the
   result is a ``WriteResult`` (``performed``, ``insert_id``, ``message``).
2. **Updates fail closed.** Upstream treats every parameter an update leaves out as
   empty. An ``update_*`` task therefore reads the record (``read.json``), applies the
   caller's changes, and sends every parameter the ``update.json`` table documents,
   derived from the record. A mandatory parameter that neither the record nor the call
   gives, or a stored list it cannot carry over (a shape never observed, such as
   attachments or allocations), stops it with ``InvalidRequestError`` before anything
   is written; it never sends a partial record.
3. **Custom fields.** Every create and update task takes ``custom``, a mapping from
   upstream's custom field names (``customField<ID>``) to text, sent as the XML upstream
   documents, every value escaped. An update keeps every stored custom value it is not
   given.
4. **Ids for orders.** ``list_order_categories`` (``tasks.py``, the read server) lists
   the categories and their statuses, the ids ``create_order`` takes.
5. **Live tests mark, delete and sweep** (``tests/test_live.py``).
6. **Deletes** preview the record they would delete.
7. Core's form bodies (``data=``) carry the fields (``api/_form.py``).

``meta.endpoint`` is the write operation (``journal/create.json``) and ``meta.tenant``
the organisation. ``meta.request`` is ``org`` plus the form fields as sent when the
write was performed, and ``org`` alone for a preview, whose ``payload`` holds them:
the payload never appears twice. ``tests/test_tasks.py`` checks every name in
``__all__``.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from typing import Any, TypeGuard, get_args

from pydantic import BaseModel, JsonValue, ValidationError
from xippios.core import InvalidRequestError, Result, sync

from xippios.cashctrl import api
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.models import (
    AllocationInput,
    AttachmentInput,
    BankAccountInput,
    ChildInput,
    Color,
    InsuranceContractInput,
    JournalEntryDetail,
    JournalItemInput,
    Language,
    NotifyType,
    OrderDetail,
    OrderItemInput,
    PersonAddressInput,
    PersonContactInput,
    PersonDetail,
    Recurrence,
    ServicePeriodInput,
    WriteAnswer,
    WritePreview,
    WriteResult,
)
from xippios.cashctrl.tasks import _meta

__all__ = [
    "create_journal_entry",
    "create_order",
    "create_person",
    "delete_journal_entry",
    "delete_order",
    "delete_person",
    "update_journal_entry",
    "update_person",
]

JournalOutcome = WritePreview[JournalEntryDetail] | WriteResult
"""A journal write's result: a preview (``performed`` false) or what was written (true)."""
PersonOutcome = WritePreview[PersonDetail] | WriteResult
"""A person write's result: a preview (``performed`` false) or what was written (true)."""
OrderOutcome = WritePreview[OrderDetail] | WriteResult
"""An order write's result: a preview (``performed`` false) or what was written (true)."""

NOTIFY_TYPES: tuple[str, ...] = get_args(NotifyType)
RECURRENCES: tuple[str, ...] = get_args(Recurrence)
LANGUAGES: tuple[str, ...] = get_args(Language)
COLORS: tuple[str, ...] = get_args(Color)


def _preview[T](
    org: str,
    endpoint: str,
    payload: dict[str, str],
    *,
    before: T | None = None,
    changes: dict[str, str] | None = None,
) -> Result[WritePreview[T] | WriteResult]:
    preview = WritePreview[T](endpoint=endpoint, payload=payload, before=before, changes=changes)
    return Result[WritePreview[T] | WriteResult](data=preview, meta=_meta(org, endpoint, {}))


def _performed[T](
    org: str, endpoint: str, payload: dict[str, str], answer: WriteAnswer
) -> Result[WritePreview[T] | WriteResult]:
    result = WriteResult(insert_id=answer.insert_id, message=answer.message)
    return Result[WritePreview[T] | WriteResult](data=result, meta=_meta(org, endpoint, payload))


def _whole(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_id(id: object) -> int:
    """``id`` when it is a record id, a whole number of at least 1; refused otherwise."""
    if not _whole(id) or id < 1:
        raise InvalidRequestError(
            f"id must be a whole number of at least 1, not {id!r}", source=SOURCE
        )
    return id


def _inputs[M: BaseModel](
    name: str, values: Sequence[Any] | None, model: type[M], problems: list[str]
) -> list[M] | None:
    """``values`` as ``model`` objects (a mapping is validated as one); problems collected.

    The adapters validate a tool's arguments before the task runs; this is for Python
    callers, who may pass mappings, as ``list_accounts`` takes its filters.
    """
    if values is None:
        return None
    if isinstance(values, str | bytes | Mapping) or not isinstance(values, Sequence):
        problems.append(f"{name} takes a list, not {type(values).__name__}")
        return None
    parsed: list[M] = []
    for index, value in enumerate(values):
        if isinstance(value, model):
            parsed.append(value)
            continue
        if not isinstance(value, Mapping):
            problems.append(
                f"{name}[{index}] must be a {model.__name__} or a mapping, "
                f"not {type(value).__name__}"
            )
            continue
        try:
            parsed.append(model.model_validate(dict(value)))
        except ValidationError as error:
            for detail in error.errors():
                where = ".".join(str(part) for part in detail["loc"])
                problems.append(f"{name}[{index}].{where}: {detail['msg']}")
    return parsed


def _choices(problems: list[str], **named: tuple[object, tuple[str, ...]]) -> None:
    """Refuse a value outside a documented value set (``notify_type``, ``language``)."""
    for name, (value, allowed) in named.items():
        if value is not None and value not in allowed:
            problems.append(f"{name} must be one of {', '.join(allowed)}, not {value!r}")


def _refuse(problems: list[str]) -> None:
    if problems:
        raise InvalidRequestError("; ".join(problems), source=SOURCE)


def _custom(custom: Mapping[str, str] | None) -> str | None:
    """A create's ``custom``: upstream's XML, or ``None`` (not sent) when none is given."""
    return api.custom_xml(custom) if custom else None


def _given(**values: Any) -> dict[str, Any]:
    """The arguments an update was given: every one that is not ``None``."""
    return {name: value for name, value in values.items() if value is not None}


def _blocked(stored: Mapping[str, object], given: Mapping[str, Any]) -> list[str]:
    """The stored lists an update can neither carry over nor was given a replacement for."""
    return [name for name, value in stored.items() if value and name not in given]


_HELD = {"items": "items with allocations"}
"""What a stored list that cannot be carried holds, where its name alone does not say."""


def _cannot_carry(resource: str, names: Sequence[str]) -> InvalidRequestError:
    held = ", ".join(_HELD.get(name, name) for name in names)
    listed = ", ".join(names)
    return InvalidRequestError(
        f"the {resource} holds {held}, whose stored shape was never observed, so the "
        f"update cannot send it back and upstream would empty it; pass {listed} to "
        "replace it, or change the record in CashCtrl. Nothing was sent",
        source=SOURCE,
    )


def _missing(resource: str, names: Sequence[str], hint: str) -> InvalidRequestError:
    return InvalidRequestError(
        f"the {resource} gives no {', '.join(names)}, which update.json requires; {hint}. "
        "Nothing was sent",
        source=SOURCE,
    )


# Journal entries ---------------------------------------------------------------------


def _journal_items(entry: JournalEntryDetail) -> tuple[list[JournalItemInput] | None, bool]:
    """The record's lines as inputs, and whether one holds allocations it cannot carry."""
    if not entry.items:
        return None, False
    lines = [
        JournalItemInput(
            account_id=item.account_id,
            associate_id=item.associate_id,
            credit=item.credit,
            debit=item.debit,
            description=item.description,
            tax_id=item.tax_id,
        )
        for item in entry.items
    ]
    return lines, any(item.allocations for item in entry.items)


def _journal_values(entry: JournalEntryDetail) -> tuple[dict[str, Any], dict[str, object]]:
    """Every ``update.json`` parameter of ``entry`` by task name, and what it cannot carry.

    ``sequenceNumberId`` is not stored: an update leaves it out, so the reference stays
    as it is ("If this is empty, the sequence number will not update when ``reference``
    is set"). ``allocations`` and ``attachments`` were only ever seen empty; a record
    holding either, or a line holding allocations, cannot be carried over.
    """
    items, items_blocked = _journal_items(entry)
    values: dict[str, Any] = {
        "amount": entry.amount,
        "credit_id": entry.credit_id,
        "debit_id": entry.debit_id,
        "associate_id": entry.associate_id,
        "currency_id": entry.currency_id,
        "currency_rate": entry.currency_rate,
        "custom": entry.custom,
        "date_added": entry.date_added,
        "days_before": entry.days_before,
        "end_date": entry.end_date,
        "items": items,
        "notes": entry.notes,
        "notify_email": entry.notify_email,
        "notify_person_id": entry.notify_person_id,
        "notify_type": entry.notify_type,
        "notify_user_id": entry.notify_user_id,
        "recurrence": entry.recurrence,
        "reference": entry.reference,
        "start_date": entry.start_date,
        "tax_id": entry.tax_id,
        "title": entry.title,
    }
    stored = {
        "allocations": entry.allocations,
        "attachments": entry.attachments,
        "items": items_blocked,
    }
    return values, stored


async def create_journal_entry_async(
    org: str,
    *,
    date_added: date | None = None,
    amount: Decimal | None = None,
    debit_id: int | None = None,
    credit_id: int | None = None,
    title: str | None = None,
    tax_id: int | None = None,
    associate_id: int | str | None = None,
    reference: str | None = None,
    notes: str | None = None,
    items: list[JournalItemInput] | None = None,
    allocations: list[AllocationInput] | None = None,
    attachments: list[AttachmentInput] | None = None,
    currency_id: int | None = None,
    currency_rate: Decimal | None = None,
    sequence_number_id: int | None = None,
    recurrence: Recurrence | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    days_before: int | None = None,
    notify_type: NotifyType | None = None,
    notify_email: str | None = None,
    notify_person_id: int | None = None,
    notify_user_id: int | None = None,
    custom: Mapping[str, str] | None = None,
    confirm: bool = False,
) -> Result[JournalOutcome]:
    """Book a manual journal entry; without confirm=true it only previews the entry.

    Without ``confirm`` nothing is written and no request is sent: the result is a
    preview, ``performed`` false, whose ``payload`` holds the exact form fields CashCtrl
    would receive. Show it, then call again with ``confirm=true`` to book; the result is
    then ``performed`` true with ``insert_id``, the new entry's id. A simple entry takes
    ``amount``, ``debit_id`` and ``credit_id``; a collective entry takes ``items``, and
    upstream then ignores those three. ``amount`` with a ``tax_id`` is the gross amount,
    VAT included (observed on the demo organisation, although the tax codes' calculation
    type reads NET). Account ids come from ``list_accounts`` (the ``id``, not the account
    number), tax codes from ``list_tax_codes``, persons from ``list_persons``. CashCtrl
    checks the entry and refuses it naming the fields, e.g. ``debitId: This field cannot
    be empty.``; nothing is checked here that upstream checks itself.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        date_added: The date of the entry, e.g. ``2026-10-24``.
        amount: The amount, e.g. ``125.50``; gross when ``tax_id`` is set.
        debit_id: The account on the debit side, an ``id`` from ``list_accounts``, e.g. ``3``.
        credit_id: The account on the credit side, an ``id`` from ``list_accounts``, e.g. ``42``.
        title: The description of the entry, at most 250 characters, e.g. ``"Miete Oktober"``.
        tax_id: A tax code, an ``id`` from ``list_tax_codes``, e.g. ``9`` (``UN1``).
        associate_id: The business partner, an ``id`` from ``list_persons``, e.g. ``7``;
            upstream also takes a name, which creates a new person.
        reference: A reference or receipt number, at most 100 characters, e.g. ``"RE-1"``.
        notes: Notes, limited HTML allowed, e.g. ``"<p>paid in cash</p>"``.
        items: The lines of a collective entry, each with ``account_id`` and ``debit`` or
            ``credit``, and optionally ``description``, ``tax_id``, ``associate_id`` and
            ``allocations``, e.g. ``[{"account_id": 3, "debit": 500},
            {"account_id": 42, "credit": 500}]``.
        allocations: Allocations to cost centers, e.g.
            ``[{"share": 1, "to_cost_center_id": 2}]``.
        attachments: Files to attach, e.g. ``[{"file_id": 24}]``.
        currency_id: A currency, an ``id`` from ``list_currencies``; the default currency
            when left out.
        currency_rate: The exchange rate into the default currency, e.g. ``0.92``.
        sequence_number_id: The sequence number that generates ``reference``, e.g. ``6``.
        recurrence: How often the entry repeats: ``MONTHLY``, ``WEEKLY``, ``DAILY``,
            ``YEARLY``, ``SEMESTRAL``, ``QUARTERLY``, ``BI_MONTHLY`` or ``BI_WEEKLY``.
        start_date: The next date the entry repeats on, e.g. ``2026-11-01``.
        end_date: The date the recurrence stops, e.g. ``2027-12-31``.
        days_before: Create the next entry this many days before ``start_date``, e.g. ``5``.
        notify_type: Who is notified of a repeated entry: ``NONE``, ``USER``, ``PERSON``,
            ``RESPONSIBLE_PERSON`` or ``EMAIL``.
        notify_email: The address notified with ``notify_type`` ``EMAIL``.
        notify_person_id: The person notified with ``notify_type`` ``PERSON``.
        notify_user_id: The user notified with ``notify_type`` ``USER``.
        custom: Custom field values by upstream's name, e.g.
            ``{"customField1": "Projekt A"}``.
        confirm: ``true`` books the entry; ``false`` (the default) only previews it.
    """
    problems: list[str] = []
    item_inputs = _inputs("items", items, JournalItemInput, problems)
    allocation_inputs = _inputs("allocations", allocations, AllocationInput, problems)
    attachment_inputs = _inputs("attachments", attachments, AttachmentInput, problems)
    _choices(
        problems, notify_type=(notify_type, NOTIFY_TYPES), recurrence=(recurrence, RECURRENCES)
    )
    _refuse(problems)
    fields = api.journal_fields(
        amount=amount,
        credit_id=credit_id,
        debit_id=debit_id,
        allocations=allocation_inputs,
        associate_id=associate_id,
        attachments=attachment_inputs,
        currency_id=currency_id,
        currency_rate=currency_rate,
        custom=_custom(custom),
        date_added=date_added,
        days_before=days_before,
        end_date=end_date,
        items=item_inputs,
        notes=notes,
        notify_email=notify_email,
        notify_person_id=notify_person_id,
        notify_type=notify_type,
        notify_user_id=notify_user_id,
        recurrence=recurrence,
        reference=reference,
        sequence_number_id=sequence_number_id,
        start_date=start_date,
        tax_id=tax_id,
        title=title,
    )
    endpoint = "journal/create.json"
    if confirm is not True:
        return _preview(org, endpoint, fields)
    answer = await api.journal_create(org, fields)
    return _performed(org, endpoint, fields, answer)


async def update_journal_entry_async(
    org: str,
    id: int,
    *,
    date_added: date | None = None,
    amount: Decimal | None = None,
    debit_id: int | None = None,
    credit_id: int | None = None,
    title: str | None = None,
    tax_id: int | None = None,
    associate_id: int | str | None = None,
    reference: str | None = None,
    notes: str | None = None,
    items: list[JournalItemInput] | None = None,
    allocations: list[AllocationInput] | None = None,
    attachments: list[AttachmentInput] | None = None,
    currency_id: int | None = None,
    currency_rate: Decimal | None = None,
    sequence_number_id: int | None = None,
    recurrence: Recurrence | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    days_before: int | None = None,
    notify_type: NotifyType | None = None,
    notify_email: str | None = None,
    notify_person_id: int | None = None,
    notify_user_id: int | None = None,
    custom: Mapping[str, str] | None = None,
    confirm: bool = False,
) -> Result[JournalOutcome]:
    """Change a manual journal entry; without confirm=true it only previews the change.

    The entry is read first (``journal/read.json``), the parameters given are applied,
    and every parameter ``journal/update.json`` documents is sent, taken from the entry
    where not given: upstream empties every parameter an update leaves out. A parameter
    left out here keeps its stored value; an empty text (``""``) empties a text field.
    Without ``confirm`` nothing is written: the preview (``performed`` false) shows the
    ``payload`` that would be sent, the entry as it is (``before``) and the
    ``changes``, at the cost of that one read. ``confirm=true`` reads and writes. An
    entry that gives no ``amount``, ``debit_id`` or ``credit_id`` (a simple entry needs
    all three) or holds attachments or allocations, which cannot be carried over, is
    refused before anything is written, unless the call gives them. Entries that orders
    or salary booked are refused by upstream. ``amount`` with a ``tax_id`` is gross.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The entry's ``id`` from ``list_journal_entries``, e.g. ``52``.
        date_added: The date of the entry, e.g. ``2026-10-24``.
        amount: The amount, e.g. ``125.50``; gross when ``tax_id`` is set.
        debit_id: The account on the debit side, an ``id`` from ``list_accounts``, e.g. ``3``.
        credit_id: The account on the credit side, an ``id`` from ``list_accounts``, e.g. ``42``.
        title: The description of the entry, at most 250 characters, e.g. ``"Miete Oktober"``.
        tax_id: A tax code, an ``id`` from ``list_tax_codes``, e.g. ``9`` (``UN1``).
        associate_id: The business partner, an ``id`` from ``list_persons``, e.g. ``7``;
            upstream also takes a name, which creates a new person.
        reference: A reference or receipt number, at most 100 characters, e.g. ``"RE-1"``.
        notes: Notes, limited HTML allowed, e.g. ``"<p>paid in cash</p>"``.
        items: The lines of a collective entry, replacing the stored ones, each with
            ``account_id`` and ``debit`` or ``credit``, e.g.
            ``[{"account_id": 3, "debit": 500}, {"account_id": 42, "credit": 500}]``.
        allocations: Allocations to cost centers, replacing the stored ones, e.g.
            ``[{"share": 1, "to_cost_center_id": 2}]``.
        attachments: Files to attach, replacing the stored ones, e.g. ``[{"file_id": 24}]``.
        currency_id: A currency, an ``id`` from ``list_currencies``.
        currency_rate: The exchange rate into the default currency, e.g. ``0.92``.
        sequence_number_id: The sequence number that generates ``reference``, e.g. ``6``.
        recurrence: How often the entry repeats: ``MONTHLY``, ``WEEKLY``, ``DAILY``,
            ``YEARLY``, ``SEMESTRAL``, ``QUARTERLY``, ``BI_MONTHLY`` or ``BI_WEEKLY``.
        start_date: The next date the entry repeats on, e.g. ``2026-11-01``.
        end_date: The date the recurrence stops, e.g. ``2027-12-31``.
        days_before: Create the next entry this many days before ``start_date``, e.g. ``5``.
        notify_type: ``NONE``, ``USER``, ``PERSON``, ``RESPONSIBLE_PERSON`` or ``EMAIL``.
        notify_email: The address notified with ``notify_type`` ``EMAIL``.
        notify_person_id: The person notified with ``notify_type`` ``PERSON``.
        notify_user_id: The user notified with ``notify_type`` ``USER``.
        custom: Custom field values to set by upstream's name, e.g.
            ``{"customField1": "Projekt B"}``; the other stored values are kept.
        confirm: ``true`` writes the change; ``false`` (the default) only previews it.
    """
    _check_id(id)
    problems: list[str] = []
    given = _given(
        date_added=date_added,
        amount=amount,
        debit_id=debit_id,
        credit_id=credit_id,
        title=title,
        tax_id=tax_id,
        associate_id=associate_id,
        reference=reference,
        notes=notes,
        items=_inputs("items", items, JournalItemInput, problems),
        allocations=_inputs("allocations", allocations, AllocationInput, problems),
        attachments=_inputs("attachments", attachments, AttachmentInput, problems),
        currency_id=currency_id,
        currency_rate=currency_rate,
        sequence_number_id=sequence_number_id,
        recurrence=recurrence,
        start_date=start_date,
        end_date=end_date,
        days_before=days_before,
        notify_type=notify_type,
        notify_email=notify_email,
        notify_person_id=notify_person_id,
        notify_user_id=notify_user_id,
    )
    _choices(
        problems, notify_type=(notify_type, NOTIFY_TYPES), recurrence=(recurrence, RECURRENCES)
    )
    _refuse(problems)
    if custom:
        api.custom_xml(custom)  # refuse a wrong name before the read
    entry = await api.journal_read(org, id)
    values, stored = _journal_values(entry)
    blocked = _blocked(stored, given)
    if blocked:
        raise _cannot_carry("journal entry", blocked)
    merged = {**values, **given, "custom": api.merge_custom(entry.custom, custom or {})}
    if not merged["items"]:
        absent = [
            upstream
            for name, upstream in (
                ("amount", "amount"),
                ("credit_id", "creditId"),
                ("debit_id", "debitId"),
            )
            if merged[name] is None
        ]
        if absent:
            raise _missing(
                "journal entry", absent, "pass them (amount, credit_id, debit_id) or items"
            )
    fields = api.journal_fields(id=entry.id, **merged)
    changes = api.journal_fields(**given, custom=api.custom_xml(custom) if custom else None)
    endpoint = "journal/update.json"
    if confirm is not True:
        return _preview(org, endpoint, fields, before=entry, changes=changes)
    answer = await api.journal_update(org, fields)
    return _performed(org, endpoint, fields, answer)


async def delete_journal_entry_async(
    org: str, id: int, *, confirm: bool = False
) -> Result[JournalOutcome]:
    """Delete one manual journal entry; without confirm=true it only shows the entry.

    Without ``confirm`` nothing is deleted: the preview (``performed`` false) shows the
    entry that would be deleted (``before``, read with ``journal/read.json``) and the
    ``payload``, ``ids`` with this one id. ``confirm=true`` deletes it, without reading
    it first. Entries that orders or salary booked cannot be deleted here; upstream
    refuses them. An unknown id raises ``NotFoundError`` in the preview, and
    ``RequestRejected`` ("This book entry does not exist.", observed) when confirmed.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The entry's ``id`` from ``list_journal_entries``, e.g. ``52``.
        confirm: ``true`` deletes the entry; ``false`` (the default) only shows it.
    """
    _check_id(id)
    fields = api.delete_fields([id])
    endpoint = "journal/delete.json"
    if confirm is not True:
        entry = await api.journal_read(org, id)
        return _preview(org, endpoint, fields, before=entry)
    answer = await api.journal_delete(org, [id])
    return _performed(org, endpoint, fields, answer)


# Persons -----------------------------------------------------------------------------


def _addresses(person: PersonDetail) -> list[PersonAddressInput]:
    """The record's addresses under the keys the ``addresses`` table documents."""
    return [
        PersonAddressInput.model_validate(
            {
                "type": address.type,
                "address": address.address,
                "canton": address.canton,
                "city": address.city,
                "company": address.company,
                "country": address.country,
                "first_name": address.first_name,
                "is_hide_company": address.is_hide_company,
                "is_hide_name": address.is_hide_name,
                "last_name": address.last_name,
                "zip": address.zip,
            }
        )
        for address in person.addresses
    ]


def _contacts(person: PersonDetail) -> list[PersonContactInput]:
    """The record's contacts under the keys the ``contacts`` table documents."""
    return [
        PersonContactInput.model_validate(
            {"address": contact.address, "type": contact.type, "notes": contact.notes}
        )
        for contact in person.contacts
    ]


def _person_values(person: PersonDetail) -> tuple[dict[str, Any], dict[str, object]]:
    """Every ``update.json`` parameter of ``person`` by task name, and what it cannot carry.

    ``sequenceNumberId`` is not stored: an update leaves it out, so ``nr`` stays as it
    is. ``attachments``, ``bankAccounts``, ``children``, ``insuranceContracts``,
    ``servicePeriods`` and ``certificateValues`` were only ever seen empty; a record
    holding one of them cannot be carried over. Addresses and contacts are carried with
    the keys their tables document; one whose stored value upstream's value sets do not
    hold cannot be carried either.
    """
    stored: dict[str, object] = {
        "attachments": person.attachments,
        "bank_accounts": person.bank_accounts,
        "children": person.children,
        "insurance_contracts": person.insurance_contracts,
        "service_periods": person.service_periods,
        "certificate_values": person.certificate_values or person.certificate_values_map,
    }
    addresses: list[PersonAddressInput] | None = None
    contacts: list[PersonContactInput] | None = None
    try:
        addresses = _addresses(person)
    except ValidationError:
        stored["addresses"] = True
    try:
        contacts = _contacts(person)
    except ValidationError:
        stored["contacts"] = True
    values: dict[str, Any] = {
        "company": person.company,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "addresses": addresses,
        "alt_name": person.alt_name,
        "bank_data": person.bank_data,
        "category_id": person.category_id,
        "certificate_template_id": person.certificate_template_id,
        "color": person.color,
        "contacts": contacts,
        "custom": person.custom,
        "date_birth": person.date_birth,
        "department": person.department,
        "discount_percentage": person.discount_percentage,
        "industry": person.industry,
        "insurance_member_nr": person.insurance_member_nr,
        "insurance_nr": person.insurance_nr,
        "is_auto_fill_responsible_person": person.is_auto_fill_responsible_person,
        "is_customer": person.is_customer,
        "is_employee": person.is_employee,
        "is_family": person.is_family,
        "is_inactive": person.is_inactive,
        "is_insurance": person.is_insurance,
        "is_vendor": person.is_vendor,
        "language": person.language,
        "location_id": person.location_id,
        "notes": person.notes,
        "nr": person.nr,
        "position": person.position,
        "ssn": person.ssn,
        "superior_id": person.superior_id,
        "title_id": person.title_id,
        "user_id": person.user_id,
        "vat_uid": person.vat_uid,
    }
    return values, stored


def _person_inputs(
    problems: list[str],
    *,
    addresses: Sequence[Any] | None,
    attachments: Sequence[Any] | None,
    bank_accounts: Sequence[Any] | None,
    children: Sequence[Any] | None,
    contacts: Sequence[Any] | None,
    insurance_contracts: Sequence[Any] | None,
    service_periods: Sequence[Any] | None,
) -> dict[str, Any]:
    return {
        "addresses": _inputs("addresses", addresses, PersonAddressInput, problems),
        "attachments": _inputs("attachments", attachments, AttachmentInput, problems),
        "bank_accounts": _inputs("bank_accounts", bank_accounts, BankAccountInput, problems),
        "children": _inputs("children", children, ChildInput, problems),
        "contacts": _inputs("contacts", contacts, PersonContactInput, problems),
        "insurance_contracts": _inputs(
            "insurance_contracts", insurance_contracts, InsuranceContractInput, problems
        ),
        "service_periods": _inputs(
            "service_periods", service_periods, ServicePeriodInput, problems
        ),
    }


async def create_person_async(
    org: str,
    *,
    company: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    addresses: list[PersonAddressInput] | None = None,
    contacts: list[PersonContactInput] | None = None,
    category_id: int | None = None,
    is_customer: bool | None = None,
    is_vendor: bool | None = None,
    is_employee: bool | None = None,
    is_insurance: bool | None = None,
    is_family: bool | None = None,
    is_inactive: bool | None = None,
    nr: str | None = None,
    sequence_number_id: int | None = None,
    language: Language | None = None,
    title_id: int | None = None,
    alt_name: str | None = None,
    position: str | None = None,
    department: str | None = None,
    industry: str | None = None,
    vat_uid: str | None = None,
    bank_data: str | None = None,
    bank_accounts: list[BankAccountInput] | None = None,
    discount_percentage: Decimal | None = None,
    date_birth: date | None = None,
    color: Color | None = None,
    superior_id: int | None = None,
    notes: str | None = None,
    attachments: list[AttachmentInput] | None = None,
    user_id: int | None = None,
    is_auto_fill_responsible_person: bool | None = None,
    location_id: int | None = None,
    ssn: str | None = None,
    children: list[ChildInput] | None = None,
    service_periods: list[ServicePeriodInput] | None = None,
    certificate_template_id: int | None = None,
    certificate_values: dict[str, JsonValue] | None = None,
    insurance_nr: str | None = None,
    insurance_member_nr: str | None = None,
    insurance_contracts: list[InsuranceContractInput] | None = None,
    custom: Mapping[str, str] | None = None,
    confirm: bool = False,
) -> Result[PersonOutcome]:
    """Create a person (customer, vendor, employee, ...); without confirm=true only a preview.

    Without ``confirm`` nothing is written and no request is sent: the result is a
    preview, ``performed`` false, whose ``payload`` holds the exact form fields CashCtrl
    would receive. Call again with ``confirm=true`` to create; the result is then
    ``performed`` true with ``insert_id``, the new person's id. Upstream needs at least
    one of ``company``, ``first_name`` or ``last_name`` and refuses a person without,
    naming the fields. The roles are flags (``is_customer``, ``is_vendor``, ...); a flag
    left out is not sent, so upstream applies its default. Without ``nr`` and
    ``sequence_number_id`` upstream may number the person from a sequence itself.
    Person categories are ids from CashCtrl's person categories.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        company: The company name, at most 100 characters, e.g. ``"Muster AG"``.
        first_name: The first name, at most 50 characters, e.g. ``"Anna"``.
        last_name: The last name, at most 50 characters, e.g. ``"Muster"``.
        addresses: Addresses, each with ``type`` (``MAIN``, ``INVOICE``, ``DELIVERY``,
            ``SALARY``, ``HISTORICAL``, ``OTHER``) and optionally ``address``, ``zip``,
            ``city``, ``canton`` (``ZH``), ``country`` (ISO 3166 alpha-3, ``CHE``),
            ``company``, ``first_name``, ``last_name``, ``is_hide_company``,
            ``is_hide_name``, e.g. ``[{"type": "MAIN", "address": "Musterstrasse 1",
            "zip": "8001", "city": "Zürich", "country": "CHE"}]``.
        contacts: Contact information, each with ``type`` (``EMAIL_WORK``,
            ``EMAIL_INVOICE``, ``PHONE_WORK``, ``MOBILE_WORK``, ``WEBSITE``, ...) and
            ``address``, optionally ``notes``, e.g.
            ``[{"type": "EMAIL_WORK", "address": "info@muster.example"}]``.
        category_id: A person category's id, e.g. ``1``.
        is_customer: ``true`` for a customer.
        is_vendor: ``true`` for a vendor.
        is_employee: ``true`` for an employee.
        is_insurance: ``true`` for an insurance company.
        is_family: ``true`` for a family.
        is_inactive: ``true`` marks the person inactive; upstream's default is false.
        nr: The person number, at most 50 characters, e.g. ``"K-1001"``.
        sequence_number_id: The sequence number that generates ``nr``, e.g. ``3``.
        language: ``DE``, ``EN``, ``FR`` or ``IT``, e.g. for documents.
        title_id: A person title's id (Mr., Mrs., Dr.), e.g. ``1``.
        alt_name: An alternative name for the organisational chart.
        position: The job title, at most 100 characters.
        department: The department, at most 100 characters.
        industry: The industry or trade, at most 100 characters.
        vat_uid: The VAT number (UID), at most 32 characters, e.g. ``"CHE-123.456.789"``.
        bank_data: Unstructured bank information when no IBAN is known.
        bank_accounts: Bank accounts, each with ``iban`` and ``type`` (``DEFAULT``,
            ``ORDER``, ``SALARY``, ``HISTORICAL``, ``OTHER``), optionally ``bic``,
            ``notes``.
        discount_percentage: A discount for orders, 0 to 100, e.g. ``5``.
        date_birth: The date of birth, e.g. ``1980-05-17``.
        color: The colour in the organisational chart: ``BLUE``, ``GREEN``, ``RED``,
            ``YELLOW``, ``ORANGE``, ``BLACK``, ``GRAY``, ``BROWN``, ``VIOLET``, ``PINK``.
        superior_id: The superior, a person's id.
        notes: Notes, limited HTML allowed.
        attachments: Files to attach, e.g. ``[{"file_id": 24}]``.
        user_id: The CashCtrl user linked to an employee.
        is_auto_fill_responsible_person: ``true`` fills this person in as responsible
            person on order documents (with ``user_id``).
        location_id: The employee's workplace, a location's id.
        ssn: The employee's social security number.
        children: Children of an employee or family, each with ``name``.
        service_periods: Service periods of an employee, each with ``date_entry``.
        certificate_template_id: The salary certificate template of an employee.
        certificate_values: Values printed on the salary certificate, e.g.
            ``{"F": true, "2.3a": "Bonus"}``.
        insurance_nr: The insurance number of an insurance.
        insurance_member_nr: The member number at an insurance.
        insurance_contracts: Insurance contracts, each with ``type_id``.
        custom: Custom field values by upstream's name, e.g. ``{"customField2": "Gold"}``.
        confirm: ``true`` creates the person; ``false`` (the default) only previews it.
    """
    problems: list[str] = []
    lists = _person_inputs(
        problems,
        addresses=addresses,
        attachments=attachments,
        bank_accounts=bank_accounts,
        children=children,
        contacts=contacts,
        insurance_contracts=insurance_contracts,
        service_periods=service_periods,
    )
    _choices(problems, language=(language, LANGUAGES), color=(color, COLORS))
    _refuse(problems)
    fields = api.person_fields(
        company=company,
        first_name=first_name,
        last_name=last_name,
        alt_name=alt_name,
        bank_data=bank_data,
        category_id=category_id,
        certificate_template_id=certificate_template_id,
        certificate_values=certificate_values,
        color=color,
        custom=_custom(custom),
        date_birth=date_birth,
        department=department,
        discount_percentage=discount_percentage,
        industry=industry,
        insurance_member_nr=insurance_member_nr,
        insurance_nr=insurance_nr,
        is_auto_fill_responsible_person=is_auto_fill_responsible_person,
        is_customer=is_customer,
        is_employee=is_employee,
        is_family=is_family,
        is_inactive=is_inactive,
        is_insurance=is_insurance,
        is_vendor=is_vendor,
        language=language,
        location_id=location_id,
        notes=notes,
        nr=nr,
        position=position,
        sequence_number_id=sequence_number_id,
        ssn=ssn,
        superior_id=superior_id,
        title_id=title_id,
        user_id=user_id,
        vat_uid=vat_uid,
        **lists,
    )
    endpoint = "person/create.json"
    if confirm is not True:
        return _preview(org, endpoint, fields)
    answer = await api.person_create(org, fields)
    return _performed(org, endpoint, fields, answer)


async def update_person_async(
    org: str,
    id: int,
    *,
    company: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    addresses: list[PersonAddressInput] | None = None,
    contacts: list[PersonContactInput] | None = None,
    category_id: int | None = None,
    is_customer: bool | None = None,
    is_vendor: bool | None = None,
    is_employee: bool | None = None,
    is_insurance: bool | None = None,
    is_family: bool | None = None,
    is_inactive: bool | None = None,
    nr: str | None = None,
    sequence_number_id: int | None = None,
    language: Language | None = None,
    title_id: int | None = None,
    alt_name: str | None = None,
    position: str | None = None,
    department: str | None = None,
    industry: str | None = None,
    vat_uid: str | None = None,
    bank_data: str | None = None,
    bank_accounts: list[BankAccountInput] | None = None,
    discount_percentage: Decimal | None = None,
    date_birth: date | None = None,
    color: Color | None = None,
    superior_id: int | None = None,
    notes: str | None = None,
    attachments: list[AttachmentInput] | None = None,
    user_id: int | None = None,
    is_auto_fill_responsible_person: bool | None = None,
    location_id: int | None = None,
    ssn: str | None = None,
    children: list[ChildInput] | None = None,
    service_periods: list[ServicePeriodInput] | None = None,
    certificate_template_id: int | None = None,
    certificate_values: dict[str, JsonValue] | None = None,
    insurance_nr: str | None = None,
    insurance_member_nr: str | None = None,
    insurance_contracts: list[InsuranceContractInput] | None = None,
    custom: Mapping[str, str] | None = None,
    confirm: bool = False,
) -> Result[PersonOutcome]:
    """Change a person; without confirm=true it only previews the change.

    The person is read first (``person/read.json``), the parameters given are applied,
    and every parameter ``person/update.json`` documents is sent, taken from the person
    where not given: upstream empties every parameter an update leaves out. A parameter
    left out here keeps its stored value; an empty text (``""``) empties a text field;
    ``addresses`` and ``contacts`` given replace the stored lists whole. Without
    ``confirm`` nothing is written: the preview (``performed`` false) shows the
    ``payload`` that would be sent, the person as it is (``before``) and the
    ``changes``, at the cost of that one read. ``confirm=true`` reads and writes. A
    person with neither company nor name, or holding attachments, bank accounts,
    children, service periods, insurance contracts or certificate values, which cannot
    be carried over, is refused before anything is written, unless the call gives them.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The person's ``id`` from ``list_persons``, e.g. ``13``; not its number ``nr``.
        company: The company name, at most 100 characters, e.g. ``"Muster AG"``.
        first_name: The first name, at most 50 characters, e.g. ``"Anna"``.
        last_name: The last name, at most 50 characters, e.g. ``"Muster"``.
        addresses: Addresses replacing the stored ones, each with ``type`` (``MAIN``,
            ``INVOICE``, ...) and optionally ``address``, ``zip``, ``city``, ``canton``,
            ``country`` (``CHE``), e.g. ``[{"type": "MAIN", "city": "Bern"}]``.
        contacts: Contact information replacing the stored ones, each with ``type``
            (``EMAIL_WORK``, ``PHONE_WORK``, ...) and ``address``.
        category_id: A person category's id, e.g. ``1``.
        is_customer: ``true`` for a customer, ``false`` to drop the role.
        is_vendor: ``true`` for a vendor, ``false`` to drop the role.
        is_employee: ``true`` for an employee.
        is_insurance: ``true`` for an insurance company.
        is_family: ``true`` for a family.
        is_inactive: ``true`` marks the person inactive.
        nr: The person number, at most 50 characters, e.g. ``"K-1001"``.
        sequence_number_id: The sequence number that generates ``nr``, e.g. ``3``.
        language: ``DE``, ``EN``, ``FR`` or ``IT``.
        title_id: A person title's id (Mr., Mrs., Dr.), e.g. ``1``.
        alt_name: An alternative name for the organisational chart.
        position: The job title, at most 100 characters.
        department: The department, at most 100 characters.
        industry: The industry or trade, at most 100 characters.
        vat_uid: The VAT number (UID), e.g. ``"CHE-123.456.789"``.
        bank_data: Unstructured bank information when no IBAN is known.
        bank_accounts: Bank accounts replacing the stored ones, each with ``iban`` and
            ``type``.
        discount_percentage: A discount for orders, 0 to 100, e.g. ``5``.
        date_birth: The date of birth, e.g. ``1980-05-17``.
        color: ``BLUE``, ``GREEN``, ``RED``, ``YELLOW``, ``ORANGE``, ``BLACK``, ``GRAY``,
            ``BROWN``, ``VIOLET`` or ``PINK``.
        superior_id: The superior, a person's id.
        notes: Notes, limited HTML allowed.
        attachments: Files to attach, replacing the stored ones, e.g. ``[{"file_id": 24}]``.
        user_id: The CashCtrl user linked to an employee.
        is_auto_fill_responsible_person: ``true`` fills this person in as responsible
            person on order documents.
        location_id: The employee's workplace, a location's id.
        ssn: The employee's social security number.
        children: Children replacing the stored ones, each with ``name``.
        service_periods: Service periods replacing the stored ones, each with
            ``date_entry``.
        certificate_template_id: The salary certificate template of an employee.
        certificate_values: Values printed on the salary certificate, replacing the
            stored ones, e.g. ``{"F": true}``.
        insurance_nr: The insurance number of an insurance.
        insurance_member_nr: The member number at an insurance.
        insurance_contracts: Insurance contracts replacing the stored ones, each with
            ``type_id``.
        custom: Custom field values to set by upstream's name, e.g.
            ``{"customField2": "Silber"}``; the other stored values are kept.
        confirm: ``true`` writes the change; ``false`` (the default) only previews it.
    """
    _check_id(id)
    problems: list[str] = []
    lists = _person_inputs(
        problems,
        addresses=addresses,
        attachments=attachments,
        bank_accounts=bank_accounts,
        children=children,
        contacts=contacts,
        insurance_contracts=insurance_contracts,
        service_periods=service_periods,
    )
    given = _given(
        company=company,
        first_name=first_name,
        last_name=last_name,
        alt_name=alt_name,
        bank_data=bank_data,
        category_id=category_id,
        certificate_template_id=certificate_template_id,
        certificate_values=certificate_values,
        color=color,
        date_birth=date_birth,
        department=department,
        discount_percentage=discount_percentage,
        industry=industry,
        insurance_member_nr=insurance_member_nr,
        insurance_nr=insurance_nr,
        is_auto_fill_responsible_person=is_auto_fill_responsible_person,
        is_customer=is_customer,
        is_employee=is_employee,
        is_family=is_family,
        is_inactive=is_inactive,
        is_insurance=is_insurance,
        is_vendor=is_vendor,
        language=language,
        location_id=location_id,
        notes=notes,
        nr=nr,
        position=position,
        sequence_number_id=sequence_number_id,
        ssn=ssn,
        superior_id=superior_id,
        title_id=title_id,
        user_id=user_id,
        vat_uid=vat_uid,
        **lists,
    )
    _choices(problems, language=(language, LANGUAGES), color=(color, COLORS))
    _refuse(problems)
    if custom:
        api.custom_xml(custom)  # refuse a wrong name before the read
    person = await api.person_read(org, id)
    values, stored = _person_values(person)
    blocked = _blocked(stored, given)
    if blocked:
        raise _cannot_carry("person", blocked)
    merged = {**values, **given, "custom": api.merge_custom(person.custom, custom or {})}
    if not any(merged[name] for name in ("company", "first_name", "last_name")):
        raise _missing(
            "person",
            ["company", "firstName", "lastName"],
            "upstream needs one of them; pass company, first_name or last_name",
        )
    fields = api.person_fields(id=person.id, **merged)
    changes = api.person_fields(**given, custom=api.custom_xml(custom) if custom else None)
    endpoint = "person/update.json"
    if confirm is not True:
        return _preview(org, endpoint, fields, before=person, changes=changes)
    answer = await api.person_update(org, fields)
    return _performed(org, endpoint, fields, answer)


async def delete_person_async(org: str, id: int, *, confirm: bool = False) -> Result[PersonOutcome]:
    """Delete one person; without confirm=true it only shows the person.

    Without ``confirm`` nothing is deleted: the preview (``performed`` false) shows the
    person that would be deleted (``before``, read with ``person/read.json``) and the
    ``payload``, ``ids`` with this one id. ``confirm=true`` deletes the person, without
    reading it first; upstream decides whether a person with bookings or orders may go.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The person's ``id`` from ``list_persons``, e.g. ``13``; not its number ``nr``.
        confirm: ``true`` deletes the person; ``false`` (the default) only shows it.
    """
    _check_id(id)
    fields = api.delete_fields([id])
    endpoint = "person/delete.json"
    if confirm is not True:
        person = await api.person_read(org, id)
        return _preview(org, endpoint, fields, before=person)
    answer = await api.person_delete(org, [id])
    return _performed(org, endpoint, fields, answer)


# Orders ------------------------------------------------------------------------------


async def create_order_async(
    org: str,
    *,
    associate_id: int | list[int],
    category_id: int,
    date: date,
    items: list[OrderItemInput] | None = None,
    nr: str | None = None,
    description: str | None = None,
    status_id: int | None = None,
    account_id: int | None = None,
    language: Language | None = None,
    due_days: int | None = None,
    discount_percentage: Decimal | None = None,
    is_display_item_gross: bool | None = None,
    currency_id: int | None = None,
    currency_rate: Decimal | None = None,
    sequence_number_id: int | None = None,
    group_id: int | None = None,
    previous_id: int | None = None,
    responsible_person_id: int | None = None,
    rounding_id: int | None = None,
    notes: str | None = None,
    attachments: list[AttachmentInput] | None = None,
    recurrence: Recurrence | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    days_before: int | None = None,
    notify_type: NotifyType | None = None,
    notify_email: str | None = None,
    notify_person_id: int | None = None,
    notify_user_id: int | None = None,
    custom: Mapping[str, str] | None = None,
    confirm: bool = False,
) -> Result[OrderOutcome]:
    """Create an order (offer, invoice, purchase order, ...); without confirm=true a preview.

    Without ``confirm`` nothing is written and no request is sent: the result is a
    preview, ``performed`` false, whose ``payload`` holds the exact form fields CashCtrl
    would receive. Call again with ``confirm=true`` to create; the result is then
    ``performed`` true with ``insert_id``, the new order's id. The category decides the
    kind of document and its statuses: take ``category_id`` and ``status_id`` from
    ``list_order_categories`` (``type`` ``SALES`` or ``PURCHASE``); without
    ``status_id`` the order gets the category's first status (Draft for the default
    invoice category, which books nothing). The partner comes from ``list_persons``,
    accounts from ``list_accounts``, tax codes from ``list_tax_codes``. The items'
    ``unit_price`` was read as gross, VAT included, on the demo organisation. Without
    ``nr`` upstream numbers the order from the category's sequence, if it has one, and
    refuses it otherwise.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        associate_id: The business partner, an ``id`` from ``list_persons``, e.g. ``7``;
            several ids, e.g. ``[7, 8]``, create one document per partner.
        category_id: The order category, an ``id`` from ``list_order_categories``,
            e.g. ``4`` (the default invoice category).
        date: The date of the order, e.g. ``2026-10-24``.
        items: The items, each with ``account_id`` (revenue account for sales, expense
            account for purchase), ``name`` and ``unit_price``, optionally ``quantity``
            (default 1), ``tax_id``, ``description``, ``article_nr``,
            ``discount_percentage``, ``unit_id``, ``inventory_id``, ``type`` (``ARTICLE``,
            ``TEXT``, ``PAGEBREAK``, ``SUBTOTAL``, ``TITLE``, ``OPTIONTOTAL``) and
            ``allocations``, e.g. ``[{"account_id": 42, "name": "Beratung",
            "unit_price": 150, "quantity": 2, "tax_id": 9}]``.
        nr: The order number, at most 50 characters, e.g. ``"RE-2026-201"``.
        description: A description of the document, at most 200 characters.
        status_id: A status of the category, an id from its ``status`` in
            ``list_order_categories``, e.g. ``12``.
        account_id: The account, e.g. the debtors account; the category's when left out.
        language: The document's language: ``DE``, ``EN``, ``FR`` or ``IT``.
        due_days: Days until payment is due, e.g. ``30``.
        discount_percentage: A discount on the whole order, 0 to 100, e.g. ``2``.
        is_display_item_gross: ``true`` shows item totals gross; upstream's default is net.
        currency_id: A currency, an ``id`` from ``list_currencies``.
        currency_rate: The exchange rate into the default currency, e.g. ``0.92``.
        sequence_number_id: The sequence number that generates ``nr``; the category's
            when left out.
        group_id: The order group (dossier) to put the order in, e.g. ``3``.
        previous_id: The order this one continues (offer to invoice), e.g. ``2``.
        responsible_person_id: The responsible person, a person's id.
        rounding_id: The rounding of the grand total, e.g. ``1``.
        notes: Notes, limited HTML allowed.
        attachments: Files to attach, e.g. ``[{"file_id": 24}]``.
        recurrence: How often the order repeats: ``MONTHLY``, ``WEEKLY``, ``DAILY``,
            ``YEARLY``, ``SEMESTRAL``, ``QUARTERLY``, ``BI_MONTHLY`` or ``BI_WEEKLY``.
        start_date: The next date the order repeats on, e.g. ``2026-11-01``.
        end_date: The date the recurrence stops, e.g. ``2027-12-31``.
        days_before: Create the next order this many days before ``start_date``.
        notify_type: ``NONE``, ``USER``, ``PERSON``, ``RESPONSIBLE_PERSON`` or ``EMAIL``.
        notify_email: The address notified with ``notify_type`` ``EMAIL``.
        notify_person_id: The person notified with ``notify_type`` ``PERSON``.
        notify_user_id: The user notified with ``notify_type`` ``USER``.
        custom: Custom field values by upstream's name, e.g. ``{"customField3": "A-17"}``.
        confirm: ``true`` creates the order; ``false`` (the default) only previews it.
    """
    problems: list[str] = []
    associates = [associate_id] if _whole(associate_id) else associate_id
    if not isinstance(associates, list) or not associates or not all(map(_whole, associates)):
        problems.append(f"associate_id takes a person's id or a list of them, not {associate_id!r}")
    item_inputs = _inputs("items", items, OrderItemInput, problems)
    attachment_inputs = _inputs("attachments", attachments, AttachmentInput, problems)
    _choices(
        problems,
        language=(language, LANGUAGES),
        notify_type=(notify_type, NOTIFY_TYPES),
        recurrence=(recurrence, RECURRENCES),
    )
    _refuse(problems)
    fields = api.order_fields(
        associate_id=associate_id,
        category_id=category_id,
        date=date,
        account_id=account_id,
        attachments=attachment_inputs,
        currency_id=currency_id,
        currency_rate=currency_rate,
        custom=_custom(custom),
        days_before=days_before,
        description=description,
        discount_percentage=discount_percentage,
        due_days=due_days,
        end_date=end_date,
        group_id=group_id,
        is_display_item_gross=is_display_item_gross,
        items=item_inputs,
        language=language,
        notes=notes,
        notify_email=notify_email,
        notify_person_id=notify_person_id,
        notify_type=notify_type,
        notify_user_id=notify_user_id,
        nr=nr,
        previous_id=previous_id,
        recurrence=recurrence,
        responsible_person_id=responsible_person_id,
        rounding_id=rounding_id,
        sequence_number_id=sequence_number_id,
        start_date=start_date,
        status_id=status_id,
    )
    endpoint = "order/create.json"
    if confirm is not True:
        return _preview(org, endpoint, fields)
    answer = await api.order_create(org, fields)
    return _performed(org, endpoint, fields, answer)


async def delete_order_async(org: str, id: int, *, confirm: bool = False) -> Result[OrderOutcome]:
    """Delete one order; without confirm=true it only shows the order.

    Without ``confirm`` nothing is deleted: the preview (``performed`` false) shows the
    order that would be deleted (``before``, read with ``order/read.json``, items
    included) and the ``payload``, ``ids`` with this one id. ``confirm=true`` deletes
    the order, without reading it first; upstream decides what happens to the journal
    entries a booked order made.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The order's ``id`` from ``list_orders``, e.g. ``7``; not its number ``nr``.
        confirm: ``true`` deletes the order; ``false`` (the default) only shows it.
    """
    _check_id(id)
    fields = api.delete_fields([id])
    endpoint = "order/delete.json"
    if confirm is not True:
        order = await api.order_read(org, id)
        return _preview(org, endpoint, fields, before=order)
    answer = await api.order_delete(org, [id])
    return _performed(org, endpoint, fields, answer)


create_journal_entry = sync(create_journal_entry_async)
update_journal_entry = sync(update_journal_entry_async)
delete_journal_entry = sync(delete_journal_entry_async)
create_person = sync(create_person_async)
update_person = sync(update_person_async)
delete_person = sync(delete_person_async)
create_order = sync(create_order_async)
delete_order = sync(delete_order_async)
