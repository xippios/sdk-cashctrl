"""Write tasks for CashCtrl: journal entries, persons and orders, order statuses and payments.

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
   the categories and their statuses, the ids ``create_order`` and ``update_order``
   take.
5. **Live tests mark, delete and sweep** (``tests/test_live.py``).
6. **Deletes** preview the record they would delete. A journal delete reads the entry,
   confirmed or not, and refuses one an order or a salary run booked (2026-10-24).
7. Core's form bodies (``data=``) carry the fields (``api/_form.py``).
8. **Order statuses and payments** (G5 (8) of 2026-10-28): ``update_order_status`` and
   ``create_order_payment`` send the fields they are given, nothing read first, so a
   preview sends no request. A payment creates no book entry, and upstream documents
   no way to delete it.

``meta.endpoint`` is the write operation (``journal/create.json``) and ``meta.tenant``
the organisation. ``meta.request`` is ``org`` plus the form fields as sent when the
write was performed, and ``org`` alone for a preview, whose ``payload`` holds them:
the payload never appears twice. ``tests/test_tasks.py`` checks every name in
``__all__``.

Personal identifiers (ADR-0017): ``create_person`` and ``update_person`` take ``ssn``
and, in ``bank_accounts``, each account's ``iban``, and send them as given, but no
result echoes them: a preview's ``payload`` and ``changes`` and a performed write's
``meta.request`` show ``REDACTED`` instead (``_shown``), and the record a preview shows
as ``before`` is the read tasks' projection, without ``ssn`` and ``iban``.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from decimal import Decimal
from typing import Any, TypeGuard, get_args

from pydantic import BaseModel, JsonValue, ValidationError
from xippios.core import InvalidRequestError, Result, sync
from xippios.core.models import REDACTED

from xippios.cashctrl import api
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import json_text
from xippios.cashctrl.models import (
    AllocationInput,
    AttachmentInput,
    BankAccountInput,
    ChildInput,
    Color,
    InsuranceContractInput,
    JournalEntryDetail,
    JournalEntryDetailProjection,
    JournalItemInput,
    Language,
    NotifyType,
    OrderDetail,
    OrderItemInput,
    PaymentType,
    PersonAddressInput,
    PersonContactInput,
    PersonDetail,
    PersonDetailProjection,
    Recurrence,
    ServicePeriodInput,
    WriteAnswer,
    WritePreview,
    WriteResult,
)
from xippios.cashctrl.tasks import _journal_entry_detail, _meta, _person_detail

__all__ = [
    "create_journal_entry",
    "create_order",
    "create_order_payment",
    "create_person",
    "delete_journal_entry",
    "delete_order",
    "delete_person",
    "update_journal_entry",
    "update_order",
    "update_order_status",
    "update_person",
]

JournalOutcome = WritePreview[JournalEntryDetailProjection] | WriteResult
"""A journal write's result: a preview (``performed`` false) or what was written (true)."""
PersonOutcome = WritePreview[PersonDetailProjection] | WriteResult
"""A person write's result: a preview (``performed`` false) or what was written (true)."""
OrderOutcome = WritePreview[OrderDetail] | WriteResult
"""An order write's result: a preview (``performed`` false) or what was written (true)."""

NOTIFY_TYPES: tuple[str, ...] = get_args(NotifyType)
RECURRENCES: tuple[str, ...] = get_args(Recurrence)
LANGUAGES: tuple[str, ...] = get_args(Language)
COLORS: tuple[str, ...] = get_args(Color)
PAYMENT_TYPES: tuple[str, ...] = get_args(PaymentType)


IDENTIFIERS = frozenset({"ssn"})
"""Form fields that hold a documented personal identifier (ADR-0017), by upstream name."""
IDENTIFIERS_IN_LISTS = {"bankAccounts": "iban"}
"""JSON list fields whose items hold one, by upstream name: the list and the item's key.

The item's key is matched in any case, as the projections and the recorder match it.
"""


def _redacted_items(text: str, key: str) -> str:
    """A JSON list field with ``key`` (in any case) of each item ``REDACTED`` where it is set."""
    try:
        items = json.loads(text)
    except ValueError:
        return REDACTED
    if not isinstance(items, list):
        return REDACTED
    shown = [
        {
            name: REDACTED if name.lower() == key.lower() and value not in (None, "") else value
            for name, value in item.items()
        }
        if isinstance(item, dict)
        else item
        for item in items
    ]
    return json_text(shown)


def _shown(fields: Mapping[str, str]) -> dict[str, str]:
    """``fields`` as a result may show them: no personal identifier's value (ADR-0017).

    ``ssn`` and the ``iban`` of each item of ``bankAccounts`` become ``REDACTED``; every
    other field, and an identifier sent empty (a cleared ``ssn``, which reveals nothing),
    is kept. Only what a result shows changes: upstream receives the values.
    """
    shown = dict(fields)
    for name, value in fields.items():
        if name in IDENTIFIERS and value:
            shown[name] = REDACTED
        elif name in IDENTIFIERS_IN_LISTS and value:
            shown[name] = _redacted_items(value, IDENTIFIERS_IN_LISTS[name])
    return shown


def _preview[T](
    org: str,
    endpoint: str,
    payload: dict[str, str],
    *,
    before: T | None = None,
    changes: dict[str, str] | None = None,
) -> Result[WritePreview[T] | WriteResult]:
    preview = WritePreview[T](
        endpoint=endpoint,
        payload=_shown(payload),
        before=before,
        changes=None if changes is None else _shown(changes),
    )
    return Result[WritePreview[T] | WriteResult](data=preview, meta=_meta(org, endpoint, {}))


def _performed[T](
    org: str, endpoint: str, payload: dict[str, str], answer: WriteAnswer
) -> Result[WritePreview[T] | WriteResult]:
    result = WriteResult(insert_id=answer.insert_id, message=answer.message)
    meta = _meta(org, endpoint, _shown(payload))
    return Result[WritePreview[T] | WriteResult](data=result, meta=meta)


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


def _ids(name: str, values: object, problems: list[str]) -> list[int]:
    """``values`` as a list of at least one order id; problems collected.

    Every id is a whole number of at least 1, as ``_check_id`` takes one: a list of
    them, not one id on its own nor a text such as ``"20,21"``, which the task joins.
    """
    if isinstance(values, str | bytes | Mapping) or not isinstance(values, Sequence) or not values:
        problems.append(f"{name} takes a list of at least one order id, e.g. [20], not {values!r}")
        return []
    wrong = [value for value in values if not _whole(value) or value < 1]
    if wrong:
        listed = ", ".join(repr(value) for value in wrong)
        problems.append(f"{name}: an id is a whole number of at least 1, not {listed}")
        return []
    return list(values)


def _check_status(status_id: object, problems: list[str], *, required: bool) -> None:
    """``status_id`` is a status's id from ``list_order_categories``, or ``None`` if allowed."""
    if status_id is None and not required:
        return
    if not _whole(status_id) or status_id < 1:
        problems.append(
            f"status_id must be a status id from list_order_categories, a whole number of "
            f"at least 1, not {status_id!r}"
        )


def _check_associate(associate_id: object, problems: list[str]) -> None:
    """``associate_id`` is a person's id: upstream would create a person from a name."""
    if associate_id is not None and not _whole(associate_id):
        problems.append(
            f"associate_id must be a person's id, a whole number, not {associate_id!r}; "
            "create a new person with create_person first"
        )


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


def _clear_names(
    clear: object,
    documented: Mapping[str, str],
    given: Mapping[str, Any],
    custom: Mapping[str, str] | None,
    problems: list[str],
) -> list[str]:
    """The parameters ``clear`` names, checked against ``update.json``; problems collected.

    Every name must be a documented update parameter of the resource, by its task name
    (``tax_id``, ``notes``), not one in ``_UNSENT`` (``sequence_number_id``, sent only
    when given, so clearing it would change nothing), and must not be changed by the
    same call.
    """
    if clear is None:
        return []
    if isinstance(clear, str | bytes) or not isinstance(clear, Sequence):
        problems.append(f"clear takes a list of parameter names, not {type(clear).__name__}")
        return []
    names: list[str] = []
    for name in clear:
        if not isinstance(name, str) or name not in documented:
            problems.append(
                f"clear: {name!r} is not an update.json parameter here; one of "
                + ", ".join(documented)
            )
        elif name in _UNSENT:
            problems.append(f"clear: {name!r} {_UNSENT[name]}")
        elif name in given or (name == "custom" and custom):
            problems.append(f"clear: {name!r} is both changed and cleared")
        elif name not in names:
            names.append(name)
    return names


def _changes(
    encode: Any,
    documented: Mapping[str, str],
    given: Mapping[str, Any],
    cleared: Sequence[str],
    custom: Mapping[str, str] | None,
) -> dict[str, str]:
    """What an update changes, upstream name to encoded text, for the preview.

    The values given, encoded as sent; a list or map given empty as ``[]`` or ``{}``,
    which the payload leaves out (upstream empties what is left out); a cleared
    parameter as ``""``, ``[]`` or ``{}``, by its kind, and a cleared flag as ``false``,
    the value the payload sends for it.
    """
    changes: dict[str, str] = encode(**given, custom=api.custom_xml(custom) if custom else None)
    for name, value in given.items():
        if isinstance(value, list | tuple | Mapping) and not value:
            changes[documented[name]] = "{}" if isinstance(value, Mapping) else "[]"
    for name in cleared:
        changes[documented[name]] = "false" if name in _FLAGS else _EMPTY.get(name, "")
    return changes


def _cleared(cleared: Sequence[str]) -> dict[str, Any]:
    """The values the cleared parameters are sent with: ``False`` for a flag, else ``None``.

    ``None`` and an empty list are left out of the form, which upstream reads as empty
    ("omitted parameters are treated as empty values"). A flag has no empty value:
    clearing it means ``false``, so it is sent as ``false`` (decided by Johannes on
    2026-10-24, after the wave 2 review).
    """
    return {name: False if name in _FLAGS else None for name in cleared}


_EMPTY = {
    "items": "[]",
    "allocations": "[]",
    "attachments": "[]",
    "addresses": "[]",
    "contacts": "[]",
    "bank_accounts": "[]",
    "children": "[]",
    "insurance_contracts": "[]",
    "service_periods": "[]",
    "certificate_values": "{}",
}
"""How ``changes`` shows a cleared list or map parameter; a flag is ``false``, others ``""``."""

_FLAGS = frozenset(
    {
        "is_auto_fill_responsible_person",
        "is_customer",
        "is_display_item_gross",
        "is_employee",
        "is_family",
        "is_inactive",
        "is_insurance",
        "is_vendor",
    }
)
"""The boolean update parameters ("Possible values: true, false"): a person's and an order's.

``journal/update.json`` documents none; ``order/update.json`` one,
``isDisplayItemGross``. A flag named in ``clear`` is sent as ``false``.
"""

_UNSENT = {
    "sequence_number_id": (
        "is not stored, and an update sends it only when it is given; left out, upstream "
        "already reads it as empty, so clearing it would change nothing: drop it from clear"
    ),
}
"""Update parameters an update never takes from the record, and why ``clear`` refuses them.

``sequenceNumberId`` is not stored ("If this is empty, the sequence number will not
update when ``reference`` is set"; for a person, ``nr``): the update leaves it out unless
the call gives it, so a cleared one would be sent exactly as an omitted one.
"""


def _blocked(stored: Mapping[str, str | None], decided: Iterable[str]) -> dict[str, str]:
    """What an update cannot carry over and the call neither replaced nor cleared, why."""
    settled = set(decided)
    return {name: why for name, why in stored.items() if why and name not in settled}


def _cannot_carry(resource: str, blocked: Mapping[str, str]) -> InvalidRequestError:
    listed = ", ".join(blocked)
    return InvalidRequestError(
        f"the {resource} holds {'; '.join(blocked.values())}, which the update cannot send "
        f"back as stored, and upstream would empty it; pass {listed} to replace it, or "
        "clear it, or change the record in CashCtrl. Nothing was sent",
        source=SOURCE,
    )


def _never_seen(name: str, stored: object) -> str | None:
    return f"{name}, never observed filled" if stored else None


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


def _journal_values(entry: JournalEntryDetail) -> tuple[dict[str, Any], dict[str, str | None]]:
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
        "allocations": _never_seen("allocations", entry.allocations),
        "attachments": _never_seen("attachments", entry.attachments),
        "items": "items, a line with allocations, never observed filled" if items_blocked else None,
    }
    return values, stored


JOURNAL_UPDATE: dict[str, str] = {
    "amount": "amount",
    "credit_id": "creditId",
    "debit_id": "debitId",
    "allocations": "allocations",
    "associate_id": "associateId",
    "attachments": "attachments",
    "currency_id": "currencyId",
    "currency_rate": "currencyRate",
    "custom": "custom",
    "date_added": "dateAdded",
    "days_before": "daysBefore",
    "end_date": "endDate",
    "items": "items",
    "notes": "notes",
    "notify_email": "notifyEmail",
    "notify_person_id": "notifyPersonId",
    "notify_type": "notifyType",
    "notify_user_id": "notifyUserId",
    "recurrence": "recurrence",
    "reference": "reference",
    "sequence_number_id": "sequenceNumberId",
    "start_date": "startDate",
    "tax_id": "taxId",
    "title": "title",
}
"""Every parameter ``journal/update.json`` documents but ``id``: task name to upstream name."""

_BOOKED_BY = {
    "order_id": "orderId",
    "order_book_entry_id": "orderBookEntryId",
    "salary_book_entry_id": "salaryBookEntryId",
}
"""The read fields that mark an entry an order or a salary run booked."""


def _booked(entry: JournalEntryDetail, write: str) -> InvalidRequestError | None:
    """A refusal for an entry another module booked, ``write`` ``updated`` or ``deleted``.

    ``journal/update.json``: "you cannot update automatically created entries this way";
    ``journal/delete.json``: "you cannot delete automatically created entries here".
    """
    marks = [upstream for name, upstream in _BOOKED_BY.items() if getattr(entry, name) is not None]
    if not marks:
        return None
    return InvalidRequestError(
        f"journal entry {entry.id} was booked by an order or a salary run ({', '.join(marks)} "
        f"set); upstream documents that such entries cannot be {write} here, only through "
        "that module. Nothing was sent",
        source=SOURCE,
    )


async def create_journal_entry_async(
    org: str,
    *,
    date_added: date | None = None,
    amount: Decimal | None = None,
    debit_id: int | None = None,
    credit_id: int | None = None,
    title: str | None = None,
    tax_id: int | None = None,
    associate_id: int | None = None,
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
    number; ``list_account_categories`` gives the ``category_id`` that narrows it), tax
    codes from ``list_tax_codes``, persons from ``list_persons``, currencies from
    ``list_currencies``, cost centers from ``list_cost_centers`` and custom field names
    from ``list_custom_fields`` with ``type`` ``JOURNAL``. CashCtrl
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
            a new person is created with ``create_person`` first.
        reference: A reference or receipt number, at most 100 characters, e.g. ``"RE-1"``.
        notes: Notes, limited HTML allowed, e.g. ``"<p>paid in cash</p>"``.
        items: The lines of a collective entry, each with ``account_id`` and ``debit`` or
            ``credit``, and optionally ``description``, ``tax_id``, ``associate_id`` and
            ``allocations``, e.g. ``[{"account_id": 3, "debit": 500},
            {"account_id": 42, "credit": 500}]``.
        allocations: Allocations to cost centers, each a ``share`` and a
            ``to_cost_center_id`` from ``list_cost_centers``, e.g.
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
        custom: Custom field values by upstream's name, ``customField<id>`` with an
            ``id`` from ``list_custom_fields`` (``type`` ``JOURNAL``), e.g.
            ``{"customField1": "Projekt A"}``.
        confirm: ``true`` books the entry; ``false`` (the default) only previews it.
    """
    problems: list[str] = []
    _check_associate(associate_id, problems)
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
    associate_id: int | None = None,
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
    clear: list[str] | None = None,
    confirm: bool = False,
) -> Result[JournalOutcome]:
    """Change a manual journal entry; without confirm=true it only previews the change.

    The entry is read first (``journal/read.json``), the parameters given are applied,
    and every parameter ``journal/update.json`` documents is sent, taken from the entry
    where not given: upstream empties every parameter an update leaves out. A parameter
    left out here keeps its stored value; one named in ``clear`` is sent empty. Without
    ``confirm`` nothing is written: the preview (``performed`` false) shows the
    ``payload`` that would be sent, the entry as it is (``before``) and the
    ``changes``, at the cost of that one read. ``confirm=true`` reads the entry again
    and recomputes the payload, so it can differ from the preview if the entry changed
    in between. Refused before anything is written: an entry an order or a salary run
    booked (``order_id``, ``order_book_entry_id`` or ``salary_book_entry_id`` set); a
    simple entry that gives no ``amount``, ``debit_id`` or ``credit_id``; an entry
    holding attachments or allocations, which cannot be carried over, unless the call
    replaces or clears them. ``amount`` with a ``tax_id`` is gross. The ids come from
    the lists ``create_journal_entry`` names: ``list_accounts``, ``list_tax_codes``,
    ``list_persons``, ``list_currencies``, ``list_cost_centers`` and
    ``list_custom_fields`` (``JOURNAL``).

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
            a new person is created with ``create_person`` first.
        reference: A reference or receipt number, at most 100 characters, e.g. ``"RE-1"``.
        notes: Notes, limited HTML allowed, e.g. ``"<p>paid in cash</p>"``.
        items: The lines of a collective entry, replacing the stored ones, each with
            ``account_id`` and ``debit`` or ``credit``, e.g.
            ``[{"account_id": 3, "debit": 500}, {"account_id": 42, "credit": 500}]``.
        allocations: Allocations to cost centers, replacing the stored ones, each a
            ``share`` and a ``to_cost_center_id`` from ``list_cost_centers``, e.g.
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
        custom: Custom field values to set by upstream's name, ``customField<id>`` with
            an ``id`` from ``list_custom_fields`` (``type`` ``JOURNAL``), e.g.
            ``{"customField1": "Projekt B"}``; the other stored values are kept.
        clear: Parameters to send empty, by these names, e.g. ``["tax_id", "notes"]``;
            ``["custom"]`` empties every custom field. A parameter cannot be both given
            and cleared, and ``sequence_number_id``, not stored and sent only when
            given, cannot be cleared.
        confirm: ``true`` writes the change; ``false`` (the default) only previews it.
    """
    _check_id(id)
    problems: list[str] = []
    _check_associate(associate_id, problems)
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
    cleared = _clear_names(clear, JOURNAL_UPDATE, given, custom, problems)
    _refuse(problems)
    if custom:
        api.custom_xml(custom)  # refuse a wrong name before the read
    entry = await api.journal_read(org, id)
    booked = _booked(entry, "updated")
    if booked is not None:
        raise booked
    values, stored = _journal_values(entry)
    blocked = _blocked(stored, [*given, *cleared])
    if blocked:
        raise _cannot_carry("journal entry", blocked)
    merged = {**values, **given, "custom": api.merge_custom(entry.custom, custom or {})}
    merged.update(_cleared(cleared))
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
    changes = _changes(api.journal_fields, JOURNAL_UPDATE, given, cleared, custom)
    endpoint = "journal/update.json"
    if confirm is not True:
        before = _journal_entry_detail(entry)
        return _preview(org, endpoint, fields, before=before, changes=changes)
    answer = await api.journal_update(org, fields)
    return _performed(org, endpoint, fields, answer)


async def delete_journal_entry_async(
    org: str, id: int, *, confirm: bool = False
) -> Result[JournalOutcome]:
    """Delete one manual journal entry; without confirm=true it only shows the entry.

    The entry is read first (``journal/read.json``), with ``confirm`` as well, and one
    that an order or a salary run booked (``order_id``, ``order_book_entry_id`` or
    ``salary_book_entry_id`` set) is refused with ``InvalidRequestError`` before
    anything is deleted, as ``update_journal_entry`` refuses it: upstream documents that
    such entries cannot be deleted here, but how it answers such a delete was never
    observed, so the check is made here, and a confirmed delete reads again so that it
    holds for the entry as it is when deleted, not as the preview saw it. Without
    ``confirm`` nothing is deleted: the preview (``performed`` false) shows the entry
    that would be deleted (``before``) and the ``payload``, ``ids`` with this one id.
    ``confirm=true`` deletes it after that read. An unknown id raises
    ``NotFoundError`` at the read; an entry deleted between the read and the delete is
    refused by upstream with ``RequestRejected`` ("This book entry does not exist.",
    observed).

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The entry's ``id`` from ``list_journal_entries``, e.g. ``52``.
        confirm: ``true`` deletes the entry; ``false`` (the default) only shows it.
    """
    _check_id(id)
    fields = api.delete_fields([id])
    endpoint = "journal/delete.json"
    entry = await api.journal_read(org, id)
    booked = _booked(entry, "deleted")
    if booked is not None:
        raise booked
    if confirm is not True:
        return _preview(org, endpoint, fields, before=_journal_entry_detail(entry))
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


def _person_values(
    person: PersonDetail,
) -> tuple[dict[str, Any], dict[str, str | None], list[str]]:
    """Every ``update.json`` parameter of ``person``, what it cannot carry or cannot know.

    Observed on 2026-10-24 (a person created with every documented scalar field set, read
    back, deleted): ``person/read.json`` returns every stored documented field under its
    own name and leaves out the empty ones, so a field the read lacks is empty, and the
    mapping takes each by name. Three fields were not seen come back: ``insuranceNr`` and
    ``insuranceMemberNr`` (not stored for a person who is no insurance, as documented;
    for an insurance, unverified) and ``userId`` (not sent: it links a CashCtrl login).
    For an insurance or an employee, a lack of them is therefore unknown, not empty, and
    the update needs them given or cleared.

    ``sequenceNumberId`` is not stored: an update leaves it out, so ``nr`` stays as it
    is. ``attachments``, ``bankAccounts``, ``children``, ``insuranceContracts``,
    ``servicePeriods`` and ``certificateValues`` were only ever seen empty; a record
    holding one of them cannot be carried over. Addresses and contacts are carried with
    the keys their tables document; one outside upstream's value sets cannot be carried,
    nor an address with a ``titleId`` (stored and read back, observed, but not in the
    addresses table) nor a contact with a ``purpose`` (not in the contacts table; sent,
    it was not stored).
    """
    stored: dict[str, str | None] = {
        "attachments": _never_seen("attachments", person.attachments),
        "bank_accounts": _never_seen("bank_accounts", person.bank_accounts),
        "children": _never_seen("children", person.children),
        "insurance_contracts": _never_seen("insurance_contracts", person.insurance_contracts),
        "service_periods": _never_seen("service_periods", person.service_periods),
        "certificate_values": _never_seen(
            "certificate_values", person.certificate_values or person.certificate_values_map
        ),
    }
    addresses: list[PersonAddressInput] | None = None
    contacts: list[PersonContactInput] | None = None
    try:
        addresses = _addresses(person)
    except ValidationError:
        stored["addresses"] = "addresses, one outside the documented value sets"
    if any(address.title_id is not None for address in person.addresses):
        stored["addresses"] = "addresses, one with a titleId the addresses table does not document"
    try:
        contacts = _contacts(person)
    except ValidationError:
        stored["contacts"] = "contacts, one outside the documented value sets"
    if any(contact.purpose is not None for contact in person.contacts):
        stored["contacts"] = "contacts, one with a purpose the contacts table does not document"
    unknown = [
        name
        for name, applies in (
            ("insurance_nr", person.is_insurance),
            ("insurance_member_nr", person.is_insurance),
            ("user_id", person.is_employee),
        )
        if applies and getattr(person, name) is None
    ]
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
    return values, stored, unknown


PERSON_UPDATE: dict[str, str] = {
    "company": "company",
    "first_name": "firstName",
    "last_name": "lastName",
    "addresses": "addresses",
    "alt_name": "altName",
    "attachments": "attachments",
    "bank_accounts": "bankAccounts",
    "bank_data": "bankData",
    "category_id": "categoryId",
    "certificate_template_id": "certificateTemplateId",
    "certificate_values": "certificateValues",
    "children": "children",
    "color": "color",
    "contacts": "contacts",
    "custom": "custom",
    "date_birth": "dateBirth",
    "department": "department",
    "discount_percentage": "discountPercentage",
    "industry": "industry",
    "insurance_contracts": "insuranceContracts",
    "insurance_member_nr": "insuranceMemberNr",
    "insurance_nr": "insuranceNr",
    "is_auto_fill_responsible_person": "isAutoFillResponsiblePerson",
    "is_customer": "isCustomer",
    "is_employee": "isEmployee",
    "is_family": "isFamily",
    "is_inactive": "isInactive",
    "is_insurance": "isInsurance",
    "is_vendor": "isVendor",
    "language": "language",
    "location_id": "locationId",
    "notes": "notes",
    "nr": "nr",
    "position": "position",
    "sequence_number_id": "sequenceNumberId",
    "service_periods": "servicePeriods",
    "ssn": "ssn",
    "superior_id": "superiorId",
    "title_id": "titleId",
    "user_id": "userId",
    "vat_uid": "vatUid",
}
"""Every parameter ``person/update.json`` documents but ``id``: task name to upstream name."""


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
    ``sequence_number_id`` upstream may number the person from a sequence itself. Ids:
    ``category_id`` from ``list_person_categories``, ``title_id`` from
    ``list_person_titles``, an employee's ``location_id`` from ``list_locations``,
    ``superior_id`` from ``list_persons`` and custom field names from
    ``list_custom_fields`` with ``type`` ``PERSON``.

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
        category_id: A person category, an ``id`` from ``list_person_categories``,
            e.g. ``1``.
        is_customer: ``true`` for a customer.
        is_vendor: ``true`` for a vendor.
        is_employee: ``true`` for an employee.
        is_insurance: ``true`` for an insurance company.
        is_family: ``true`` for a family.
        is_inactive: ``true`` marks the person inactive; upstream's default is false.
        nr: The person number, at most 50 characters, e.g. ``"K-1001"``.
        sequence_number_id: The sequence number that generates ``nr``, e.g. ``3``.
        language: ``DE``, ``EN``, ``FR`` or ``IT``, e.g. for documents.
        title_id: A title (Mr., Mrs., Dr.), an ``id`` from ``list_person_titles``,
            e.g. ``1``.
        alt_name: An alternative name for the organisational chart.
        position: The job title, at most 100 characters.
        department: The department, at most 100 characters.
        industry: The industry or trade, at most 100 characters.
        vat_uid: The VAT number (UID), at most 32 characters, e.g. ``"CHE-123.456.789"``.
        bank_data: Unstructured bank information when no IBAN is known.
        bank_accounts: Bank accounts, each with ``iban`` and ``type`` (``DEFAULT``,
            ``ORDER``, ``SALARY``, ``HISTORICAL``, ``OTHER``), optionally ``bic``,
            ``notes``; each ``iban`` is sent as given and shown as ``REDACTED`` in the
            preview and in ``meta.request``.
        discount_percentage: A discount for orders, 0 to 100, e.g. ``5``.
        date_birth: The date of birth, e.g. ``1980-05-17``.
        color: The colour in the organisational chart: ``BLUE``, ``GREEN``, ``RED``,
            ``YELLOW``, ``ORANGE``, ``BLACK``, ``GRAY``, ``BROWN``, ``VIOLET``, ``PINK``.
        superior_id: The superior, an ``id`` from ``list_persons``.
        notes: Notes, limited HTML allowed.
        attachments: Files to attach, e.g. ``[{"file_id": 24}]``.
        user_id: The CashCtrl user linked to an employee.
        is_auto_fill_responsible_person: ``true`` fills this person in as responsible
            person on order documents (with ``user_id``).
        location_id: The employee's workplace, an ``id`` from ``list_locations``.
        ssn: The employee's social security number; sent as given, shown as
            ``REDACTED`` in the preview and in ``meta.request``.
        children: Children of an employee or family, each with ``name``.
        service_periods: Service periods of an employee, each with ``date_entry``.
        certificate_template_id: The salary certificate template of an employee.
        certificate_values: Values printed on the salary certificate, e.g.
            ``{"F": true, "2.3a": "Bonus"}``.
        insurance_nr: The insurance number of an insurance.
        insurance_member_nr: The member number at an insurance.
        insurance_contracts: Insurance contracts, each with ``type_id``.
        custom: Custom field values by upstream's name, ``customField<id>`` with an
            ``id`` from ``list_custom_fields`` (``type`` ``PERSON``), e.g.
            ``{"customField2": "Gold"}``.
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
    clear: list[str] | None = None,
    confirm: bool = False,
) -> Result[PersonOutcome]:
    """Change a person; without confirm=true it only previews the change.

    The person is read first (``person/read.json``), the parameters given are applied,
    and every parameter ``person/update.json`` documents is sent, taken from the person
    where not given: upstream empties every parameter an update leaves out. A parameter
    left out here keeps its stored value; one named in ``clear`` is sent empty, a flag
    (``is_customer``, ``is_inactive``, ...) as ``false``;
    ``addresses`` and ``contacts`` given replace the stored lists whole. Without
    ``confirm`` nothing is written: the preview (``performed`` false) shows the
    ``payload`` that would be sent, the person as it is (``before``) and the
    ``changes``, at the cost of that one read. ``confirm=true`` reads the person again
    and recomputes the payload, so it can differ from the preview if the person changed
    in between. Refused before anything is written, unless the call gives or clears
    what is missing: a person with neither company nor name; one holding attachments,
    bank accounts, children, service periods, insurance contracts, certificate values,
    an address with a title or a contact with a purpose, which cannot be carried over;
    an insurance whose read shows no ``insurance_nr`` or ``insurance_member_nr``, or an
    employee whose read shows no ``user_id`` (the read leaves empty fields out, and these
    were never seen come back, so their absence is unknown, not empty). The ids come
    from the lists ``create_person`` names: ``list_person_categories``,
    ``list_person_titles``, ``list_locations``, ``list_persons`` and
    ``list_custom_fields`` (``PERSON``).

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
        category_id: A person category, an ``id`` from ``list_person_categories``,
            e.g. ``1``.
        is_customer: ``true`` for a customer, ``false`` to drop the role.
        is_vendor: ``true`` for a vendor, ``false`` to drop the role.
        is_employee: ``true`` for an employee.
        is_insurance: ``true`` for an insurance company.
        is_family: ``true`` for a family.
        is_inactive: ``true`` marks the person inactive.
        nr: The person number, at most 50 characters, e.g. ``"K-1001"``.
        sequence_number_id: The sequence number that generates ``nr``, e.g. ``3``.
        language: ``DE``, ``EN``, ``FR`` or ``IT``.
        title_id: A title (Mr., Mrs., Dr.), an ``id`` from ``list_person_titles``,
            e.g. ``1``.
        alt_name: An alternative name for the organisational chart.
        position: The job title, at most 100 characters.
        department: The department, at most 100 characters.
        industry: The industry or trade, at most 100 characters.
        vat_uid: The VAT number (UID), e.g. ``"CHE-123.456.789"``.
        bank_data: Unstructured bank information when no IBAN is known.
        bank_accounts: Bank accounts replacing the stored ones, each with ``iban`` and
            ``type``; each ``iban`` is shown as ``REDACTED`` in the preview and in
            ``meta.request``.
        discount_percentage: A discount for orders, 0 to 100, e.g. ``5``.
        date_birth: The date of birth, e.g. ``1980-05-17``.
        color: ``BLUE``, ``GREEN``, ``RED``, ``YELLOW``, ``ORANGE``, ``BLACK``, ``GRAY``,
            ``BROWN``, ``VIOLET`` or ``PINK``.
        superior_id: The superior, an ``id`` from ``list_persons``.
        notes: Notes, limited HTML allowed.
        attachments: Files to attach, replacing the stored ones, e.g. ``[{"file_id": 24}]``.
        user_id: The CashCtrl user linked to an employee.
        is_auto_fill_responsible_person: ``true`` fills this person in as responsible
            person on order documents.
        location_id: The employee's workplace, an ``id`` from ``list_locations``.
        ssn: The employee's social security number; sent as given, shown as
            ``REDACTED`` in the preview and in ``meta.request``.
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
        custom: Custom field values to set by upstream's name, ``customField<id>`` with
            an ``id`` from ``list_custom_fields`` (``type`` ``PERSON``), e.g.
            ``{"customField2": "Silber"}``; the other stored values are kept.
        clear: Parameters to send empty, by these names, e.g. ``["department", "notes"]``
            or ``["user_id"]``; ``["custom"]`` empties every custom field, and a flag
            such as ``["is_vendor"]`` is sent ``false``. A parameter cannot be both
            given and cleared, and ``sequence_number_id``, not stored and sent only
            when given, cannot be cleared.
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
    cleared = _clear_names(clear, PERSON_UPDATE, given, custom, problems)
    _refuse(problems)
    if custom:
        api.custom_xml(custom)  # refuse a wrong name before the read
    person = await api.person_read(org, id)
    values, stored, unknown = _person_values(person)
    decided = [*given, *cleared]
    blocked = _blocked(stored, decided)
    if blocked:
        raise _cannot_carry("person", blocked)
    undecided = [name for name in unknown if name not in decided]
    if undecided:
        raise InvalidRequestError(
            f"the person's read shows no {', '.join(undecided)}; person/read.json leaves "
            "empty fields out, and these were never seen come back, so whether one is "
            f"stored is unknown and the update could empty it; pass {', '.join(undecided)} "
            "or name them in clear. Nothing was sent",
            source=SOURCE,
        )
    merged = {**values, **given, "custom": api.merge_custom(person.custom, custom or {})}
    merged.update(_cleared(cleared))
    if not any(merged[name] for name in ("company", "first_name", "last_name")):
        raise _missing(
            "person",
            ["company", "firstName", "lastName"],
            "upstream needs one of them; pass company, first_name or last_name",
        )
    fields = api.person_fields(id=person.id, **merged)
    changes = _changes(api.person_fields, PERSON_UPDATE, given, cleared, custom)
    endpoint = "person/update.json"
    if confirm is not True:
        before = _person_detail(person)
        return _preview(org, endpoint, fields, before=before, changes=changes)
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
        return _preview(org, endpoint, fields, before=_person_detail(person))
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
    accounts from ``list_accounts``, tax codes from ``list_tax_codes``, currencies from
    ``list_currencies``, cost centers from ``list_cost_centers`` and custom field names
    from ``list_custom_fields`` with ``type`` ``ORDER``. The items'
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
        items: The items, each with ``account_id`` (an ``id`` from ``list_accounts``:
            revenue for sales, expense for purchase), ``name`` and ``unit_price``,
            optionally ``quantity`` (default 1), ``tax_id`` (from ``list_tax_codes``),
            ``description``, ``article_nr``, ``discount_percentage``, ``unit_id``,
            ``inventory_id``, ``type`` (``ARTICLE``, ``TEXT``, ``PAGEBREAK``,
            ``SUBTOTAL``, ``TITLE``, ``OPTIONTOTAL``) and ``allocations`` (each a
            ``share`` and a ``to_cost_center_id`` from ``list_cost_centers``), e.g.
            ``[{"account_id": 42, "name": "Beratung", "unit_price": 150, "quantity": 2,
            "tax_id": 9}]``.
        nr: The order number, at most 50 characters, e.g. ``"RE-2026-201"``.
        description: A description of the document, at most 200 characters.
        status_id: A status of the category, an id from its ``status`` in
            ``list_order_categories``, e.g. ``12``.
        account_id: The account, e.g. the debtors account, an ``id`` from
            ``list_accounts``; the category's when left out.
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
        responsible_person_id: The responsible person, an ``id`` from ``list_persons``.
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
        custom: Custom field values by upstream's name, ``customField<id>`` with an
            ``id`` from ``list_custom_fields`` (``type`` ``ORDER``), e.g.
            ``{"customField3": "A-17"}``.
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


def _order_items(order: OrderDetail) -> tuple[list[OrderItemInput] | None, str | None]:
    """The record's items as inputs, in their position, or why they cannot be carried.

    Each item is taken under the keys the ``items`` table of ``order/update.json``
    documents: ``accountId``, ``name``, ``unitPrice``, ``articleNr``, ``description``,
    ``discountPercentage``, ``inventoryId``, ``quantity``, ``taxId``, ``type`` and
    ``unitId``; what upstream computes from them (the totals, ``netUnitPrice``, the tax
    code's text) is not sent. An item's ``allocations`` were only ever seen empty, and
    its ``attachments`` and ``isOptional`` are not in the table: an item holding one of
    them cannot be carried over, nor one outside the documented value sets or without
    the mandatory ``accountId``, ``name`` or ``unitPrice``. The items are sent in the
    order of their ``pos``.
    """
    if not order.items:
        return None, None
    if any(item.allocations for item in order.items):
        return None, "items, one with allocations, never observed filled"
    if any(item.attachments for item in order.items):
        return None, "items, one with attachments, a key the items table does not document"
    if any(item.is_optional or item.optional for item in order.items):
        return None, "items, one marked optional, a key the items table does not document"
    ordered = sorted(order.items, key=lambda item: (item.pos is None, item.pos or 0))
    try:
        inputs = [
            OrderItemInput.model_validate(
                {
                    "account_id": item.account_id,
                    "name": item.name,
                    "unit_price": item.unit_price,
                    "article_nr": item.article_nr,
                    "description": item.description,
                    "discount_percentage": item.discount_percentage,
                    "inventory_id": item.inventory_id,
                    "quantity": item.quantity,
                    "tax_id": item.tax_id,
                    "type": item.type,
                    "unit_id": item.unit_id,
                }
            )
            for item in ordered
        ]
    except ValidationError:
        return None, (
            "items, one outside the documented value sets or without its account, name "
            "or unit price"
        )
    return inputs, None


def _order_values(order: OrderDetail) -> tuple[dict[str, Any], dict[str, str | None]]:
    """Every ``update.json`` parameter of ``order`` by task name, and what it cannot carry.

    ``sequenceNumberId`` is not stored (the read sends none): an update leaves it out,
    so ``nr`` stays as it is ("Leave empty to generate the number with
    ``sequenceNumberId``"). ``statusId`` is sent as stored: left out, upstream would set
    "the first status in the list". ``attachments`` were only ever seen empty; an order
    holding attachments, or items ``_order_items`` cannot carry, cannot be carried over.
    """
    items, items_blocked = _order_items(order)
    values: dict[str, Any] = {
        "associate_id": order.associate_id,
        "category_id": order.category_id,
        "date": order.date,
        "account_id": order.account_id,
        "currency_id": order.currency_id,
        "currency_rate": order.currency_rate,
        "custom": order.custom,
        "days_before": order.days_before,
        "description": order.description,
        "discount_percentage": order.discount_percentage,
        "due_days": order.due_days,
        "end_date": order.end_date,
        "group_id": order.group_id,
        "is_display_item_gross": order.is_display_item_gross,
        "items": items,
        "language": order.language,
        "notes": order.notes,
        "notify_email": order.notify_email,
        "notify_person_id": order.notify_person_id,
        "notify_type": order.notify_type,
        "notify_user_id": order.notify_user_id,
        "nr": order.nr,
        "previous_id": order.previous_id,
        "recurrence": order.recurrence,
        "responsible_person_id": order.responsible_person_id,
        "rounding_id": order.rounding_id,
        "start_date": order.start_date,
        "status_id": order.status_id,
    }
    stored = {
        "attachments": _never_seen("attachments", order.attachments),
        "items": items_blocked,
    }
    return values, stored


ORDER_UPDATE: dict[str, str] = {
    "associate_id": "associateId",
    "category_id": "categoryId",
    "date": "date",
    "account_id": "accountId",
    "attachments": "attachments",
    "currency_id": "currencyId",
    "currency_rate": "currencyRate",
    "custom": "custom",
    "days_before": "daysBefore",
    "description": "description",
    "discount_percentage": "discountPercentage",
    "due_days": "dueDays",
    "end_date": "endDate",
    "group_id": "groupId",
    "is_display_item_gross": "isDisplayItemGross",
    "items": "items",
    "language": "language",
    "notes": "notes",
    "notify_email": "notifyEmail",
    "notify_person_id": "notifyPersonId",
    "notify_type": "notifyType",
    "notify_user_id": "notifyUserId",
    "nr": "nr",
    "previous_id": "previousId",
    "recurrence": "recurrence",
    "responsible_person_id": "responsiblePersonId",
    "rounding_id": "roundingId",
    "sequence_number_id": "sequenceNumberId",
    "start_date": "startDate",
    "status_id": "statusId",
}
"""Every parameter ``order/update.json`` documents but ``id``: task name to upstream name."""

_ORDER_MANDATORY = (
    ("associate_id", "associateId"),
    ("category_id", "categoryId"),
    ("date", "date"),
)
"""The parameters ``order/update.json`` marks mandatory, ``id`` aside: task and upstream name."""


async def update_order_async(
    org: str,
    id: int,
    *,
    associate_id: int | None = None,
    category_id: int | None = None,
    date: date | None = None,
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
    clear: list[str] | None = None,
    confirm: bool = False,
) -> Result[OrderOutcome]:
    """Change an order, its items included; without confirm=true it only previews the change.

    The order is read first (``order/read.json``), the parameters given are applied,
    and every parameter ``order/update.json`` documents is sent, taken from the order
    where not given: upstream empties every parameter an update leaves out, the items
    included. A parameter left out here keeps its stored value. Without ``items`` the
    stored items are sent back unchanged, in their position, each with the keys the
    items table documents (``account_id``, ``name``, ``unit_price``, ``quantity``,
    ``tax_id``, ``description``, ...); ``items`` given replace them whole. One named in
    ``clear`` is sent empty, ``is_display_item_gross`` as ``false``. Without ``confirm``
    nothing is written: the preview (``performed`` false) shows the ``payload`` that
    would be sent, the order as it is (``before``, as ``get_order`` returns it) and the
    ``changes``, at the cost of that one read. ``confirm=true`` reads the order again and
    recomputes the payload, so it can differ from the preview if the order changed in
    between. Refused before anything is written, unless the call replaces or clears what
    is missing: an order holding attachments, or an item holding allocations or
    attachments or marked optional, which cannot be carried over; an item without its
    account, name or unit price; an order that gives no ``associate_id``,
    ``category_id`` or ``date``. Upstream changes the journal entries an order booked
    only through its items. Ids: ``category_id`` and ``status_id`` from
    ``list_order_categories``, the partner from ``list_persons``, accounts from
    ``list_accounts``, tax codes from ``list_tax_codes``, currencies from
    ``list_currencies``, cost centers from ``list_cost_centers`` and custom field names
    from ``list_custom_fields`` with ``type`` ``ORDER``. The items' ``unit_price`` was
    read as gross, VAT included, on the demo organisation.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        id: The order's ``id`` from ``list_orders``, e.g. ``7``; not its number ``nr``.
        associate_id: The business partner, one ``id`` from ``list_persons``, e.g.
            ``7``; a new person is created with ``create_person`` first.
        category_id: The order category, an ``id`` from ``list_order_categories``,
            e.g. ``4`` (the default invoice category).
        date: The date of the order, e.g. ``2026-10-24``.
        items: The items replacing the stored ones, each with ``account_id`` (an ``id``
            from ``list_accounts``: revenue for sales, expense for purchase), ``name``
            and ``unit_price``, optionally ``quantity`` (default 1), ``tax_id`` (from
            ``list_tax_codes``), ``description``, ``article_nr``,
            ``discount_percentage``, ``unit_id``, ``inventory_id``, ``type``
            (``ARTICLE``, ``TEXT``, ``PAGEBREAK``, ``SUBTOTAL``, ``TITLE``,
            ``OPTIONTOTAL``) and ``allocations`` (each a ``share`` and a
            ``to_cost_center_id`` from ``list_cost_centers``), e.g.
            ``[{"account_id": 42, "name": "Beratung", "unit_price": 150, "quantity": 2,
            "tax_id": 9}]``.
        nr: The order number, at most 50 characters, e.g. ``"RE-2026-201"``.
        description: A description of the document, at most 200 characters.
        status_id: A status of the category, an id from its ``status`` in
            ``list_order_categories``, e.g. ``12``.
        account_id: The account, e.g. the debtors account, an ``id`` from
            ``list_accounts``.
        language: The document's language: ``DE``, ``EN``, ``FR`` or ``IT``.
        due_days: Days until payment is due, e.g. ``30``.
        discount_percentage: A discount on the whole order, 0 to 100, e.g. ``2``.
        is_display_item_gross: ``true`` shows item totals gross, ``false`` net.
        currency_id: A currency, an ``id`` from ``list_currencies``.
        currency_rate: The exchange rate into the default currency, e.g. ``0.92``.
        sequence_number_id: The sequence number that generates ``nr``, e.g. ``3``.
        group_id: The order group (dossier) of the order, e.g. ``3``.
        previous_id: The order this one continues (offer to invoice), e.g. ``2``.
        responsible_person_id: The responsible person, an ``id`` from ``list_persons``.
        rounding_id: The rounding of the grand total, e.g. ``1``.
        notes: Notes, limited HTML allowed, e.g. ``"<p>Lieferung im November</p>"``.
        attachments: Files to attach, replacing the stored ones, e.g. ``[{"file_id": 24}]``.
        recurrence: How often the order repeats: ``MONTHLY``, ``WEEKLY``, ``DAILY``,
            ``YEARLY``, ``SEMESTRAL``, ``QUARTERLY``, ``BI_MONTHLY`` or ``BI_WEEKLY``.
        start_date: The next date the order repeats on, e.g. ``2026-11-01``.
        end_date: The date the recurrence stops, e.g. ``2027-12-31``.
        days_before: Create the next order this many days before ``start_date``.
        notify_type: ``NONE``, ``USER``, ``PERSON``, ``RESPONSIBLE_PERSON`` or ``EMAIL``.
        notify_email: The address notified with ``notify_type`` ``EMAIL``.
        notify_person_id: The person notified with ``notify_type`` ``PERSON``.
        notify_user_id: The user notified with ``notify_type`` ``USER``.
        custom: Custom field values to set by upstream's name, ``customField<id>`` with
            an ``id`` from ``list_custom_fields`` (``type`` ``ORDER``), e.g.
            ``{"customField3": "A-18"}``; the other stored values are kept.
        clear: Parameters to send empty, by these names, e.g. ``["notes", "due_days"]``;
            ``["items"]`` removes every item, ``["custom"]`` empties every custom field
            and ``["is_display_item_gross"]`` sends ``false``. A parameter cannot be
            both given and cleared, and ``sequence_number_id``, not stored and sent
            only when given, cannot be cleared.
        confirm: ``true`` writes the change; ``false`` (the default) only previews it.
    """
    _check_id(id)
    problems: list[str] = []
    _check_associate(associate_id, problems)
    given = _given(
        associate_id=associate_id,
        category_id=category_id,
        date=date,
        account_id=account_id,
        attachments=_inputs("attachments", attachments, AttachmentInput, problems),
        currency_id=currency_id,
        currency_rate=currency_rate,
        days_before=days_before,
        description=description,
        discount_percentage=discount_percentage,
        due_days=due_days,
        end_date=end_date,
        group_id=group_id,
        is_display_item_gross=is_display_item_gross,
        items=_inputs("items", items, OrderItemInput, problems),
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
    _choices(
        problems,
        language=(language, LANGUAGES),
        notify_type=(notify_type, NOTIFY_TYPES),
        recurrence=(recurrence, RECURRENCES),
    )
    cleared = _clear_names(clear, ORDER_UPDATE, given, custom, problems)
    _refuse(problems)
    if custom:
        api.custom_xml(custom)  # refuse a wrong name before the read
    order = await api.order_read(org, id)
    values, stored = _order_values(order)
    blocked = _blocked(stored, [*given, *cleared])
    if blocked:
        raise _cannot_carry("order", blocked)
    merged = {**values, **given, "custom": api.merge_custom(order.custom, custom or {})}
    merged.update(_cleared(cleared))
    absent = [upstream for name, upstream in _ORDER_MANDATORY if merged[name] is None]
    if absent:
        raise _missing("order", absent, "pass them (associate_id, category_id, date)")
    fields = api.order_fields(id=order.id, **merged)
    changes = _changes(api.order_fields, ORDER_UPDATE, given, cleared, custom)
    endpoint = "order/update.json"
    if confirm is not True:
        return _preview(org, endpoint, fields, before=order, changes=changes)
    answer = await api.order_update(org, fields)
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


async def update_order_status_async(
    org: str, ids: list[int], status_id: int, *, confirm: bool = False
) -> Result[OrderOutcome]:
    """Set the status of one or more orders; without confirm=true it only previews the change.

    Without ``confirm`` nothing is written and no request is sent: the preview
    (``performed`` false) holds the ``payload`` CashCtrl would receive, ``ids``
    comma-separated and ``statusId``, and shows no order (``before`` is empty; read one
    with ``get_order``). ``confirm=true`` sends it (``order/update_status.json``) without
    reading the orders first; the result is ``performed`` true with upstream's
    ``message``. A status belongs to an order category: take ``status_id`` from the
    ``status`` list of the orders' category in ``list_order_categories`` (``type``
    ``SALES`` or ``PURCHASE``), never a guess, and the order ids from ``list_orders``.
    That list says what a status does: ``is_book`` (the order books its journal entries
    in it), ``is_closed`` (it completes the order) and ``action_id`` (what follows it).
    Upstream checks the change and refuses it with its message.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        ids: The orders, their ``id`` from ``list_orders``, e.g. ``[20]`` or ``[20, 21]``;
            not their numbers ``nr``.
        status_id: The new status, an ``id`` from the ``status`` of the orders' category
            in ``list_order_categories``, e.g. ``16``.
        confirm: ``true`` sets the status; ``false`` (the default) only previews it.
    """
    problems: list[str] = []
    orders = _ids("ids", ids, problems)
    _check_status(status_id, problems, required=True)
    _refuse(problems)
    fields = api.order_update_status_fields(ids=orders, status_id=status_id)
    endpoint = "order/update_status.json"
    if confirm is not True:
        return _preview(org, endpoint, fields)
    answer = await api.order_update_status(org, fields)
    return _performed(org, endpoint, fields, answer)


async def create_order_payment_async(
    org: str,
    date: date,
    order_ids: list[int],
    *,
    amount: Decimal | None = None,
    is_combine: bool | None = None,
    status_id: int | None = None,
    type: PaymentType | None = None,
    confirm: bool = False,
) -> Result[OrderOutcome]:
    """Create the payment order (pain.001 or PDF) of orders; without confirm=true a preview.

    Without ``confirm`` nothing is written and no request is sent: the preview
    (``performed`` false) holds the ``payload`` CashCtrl would receive. ``confirm=true``
    creates the payment (``order/payment/create.json``); the result is ``performed`` true
    with upstream's ``message``. Upstream documents a payment as the payment order for
    e-banking, an ISO 20022 pain.001 file (``PAIN``, ``SEPA_PAIN``) or a PDF
    (``WIRE_PDF``, ``CASH_PDF``), which is downloaded afterwards with the same parameters
    through ``order/payment/download``, not wrapped by this package; created first, it
    lets upstream match the payments of a camt.052/053/054 file later. It creates no book
    entry (upstream: "for that see Book entries"), and upstream documents no way to read,
    list or delete it. The order ids come from ``list_orders``, ``status_id`` from the
    ``status`` of the orders' category in ``list_order_categories``. Upstream checks the
    payment and refuses it naming the fields.

    Args:
        org: A declared organisation name, e.g. ``demo``.
        date: The execution date of the payment, e.g. ``2026-10-30``.
        order_ids: The orders to pay, their ``id`` from ``list_orders``, e.g. ``[21]``;
            not their numbers ``nr``.
        amount: A partial amount per order, e.g. ``100.00``; every open amount when left
            out.
        is_combine: ``true`` merges several payments to the same payee into one
            transaction.
        status_id: The status the orders get, an ``id`` from the ``status`` of their
            category in ``list_order_categories``, e.g. ``51``; not sent when left out.
        type: The payment and its file: ``PAIN`` (pain.001, upstream's default),
            ``SEPA_PAIN``, ``WIRE_PDF`` or ``CASH_PDF``.
        confirm: ``true`` creates the payment; ``false`` (the default) only previews it.
    """
    problems: list[str] = []
    orders = _ids("order_ids", order_ids, problems)
    _check_status(status_id, problems, required=False)
    _choices(problems, type=(type, PAYMENT_TYPES))
    _refuse(problems)
    fields = api.order_payment_create_fields(
        date=date,
        order_ids=orders,
        amount=amount,
        is_combine=is_combine,
        status_id=status_id,
        type=type,
    )
    endpoint = "order/payment/create.json"
    if confirm is not True:
        return _preview(org, endpoint, fields)
    answer = await api.order_payment_create(org, fields)
    return _performed(org, endpoint, fields, answer)


create_journal_entry = sync(create_journal_entry_async)
update_journal_entry = sync(update_journal_entry_async)
delete_journal_entry = sync(delete_journal_entry_async)
create_person = sync(create_person_async)
update_person = sync(update_person_async)
delete_person = sync(delete_person_async)
create_order = sync(create_order_async)
update_order = sync(update_order_async)
delete_order = sync(delete_order_async)
update_order_status = sync(update_order_status_async)
create_order_payment = sync(create_order_payment_async)
