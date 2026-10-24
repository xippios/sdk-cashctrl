"""Write tasks for CashCtrl: create, update and delete journal entries, persons and orders.

Served only by ``xippios-cashctrl-mcp-write``, never by the read-only server and never
on the HTTP router (conventions §8). List the sync names in ``__all__``.

``org: str`` is the first, required parameter of every write task, and ``confirm: bool =
False`` its last. The decisions taken for these tools on 2026-10-23 (the PR 6 interview):

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

from pydantic import BaseModel, ValidationError
from xippios.core import InvalidRequestError, Result, sync

from xippios.cashctrl import api
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.models import (
    AllocationInput,
    AttachmentInput,
    JournalEntryDetail,
    JournalItemInput,
    NotifyType,
    Recurrence,
    WriteAnswer,
    WritePreview,
    WriteResult,
)
from xippios.cashctrl.tasks import _meta

__all__ = [
    "create_journal_entry",
    "delete_journal_entry",
    "update_journal_entry",
]

JournalOutcome = WritePreview[JournalEntryDetail] | WriteResult
"""A journal write's result: a preview (``performed`` false) or what was written (true)."""

NOTIFY_TYPES: tuple[str, ...] = get_args(NotifyType)
RECURRENCES: tuple[str, ...] = get_args(Recurrence)


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
    if not confirm:
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
    if not confirm:
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
    if not confirm:
        entry = await api.journal_read(org, id)
        return _preview(org, endpoint, fields, before=entry)
    answer = await api.journal_delete(org, [id])
    return _performed(org, endpoint, fields, answer)


create_journal_entry = sync(create_journal_entry_async)
update_journal_entry = sync(update_journal_entry_async)
delete_journal_entry = sync(delete_journal_entry_async)
