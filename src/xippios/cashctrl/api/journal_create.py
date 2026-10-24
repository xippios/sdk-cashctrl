"""``POST /api/v1/journal/create.json``: a new manual journal entry.

Reference: ``docs/upstream/journal.md``, "Create journal entry" ("Creates a new manual
journal entry. Returns either a success or multiple error messages (for each issue).").
Its documented parameters: ``amount``, ``creditId`` and ``debitId`` (mandatory, "ignored
if ``items`` is set"), and optionally ``allocations``, ``associateId``, ``attachments``,
``currencyId``, ``currencyRate``, ``custom``, ``dateAdded``, ``daysBefore``, ``endDate``,
``items``, ``notes``, ``notifyEmail``, ``notifyPersonId``, ``notifyType``,
``notifyUserId``, ``recurrence``, ``reference``, ``sequenceNumberId``, ``startDate``,
``taxId`` and ``title``. ``journal/update.json`` documents the same ones and ``id``, so
``journal_fields`` encodes both.

Observed on 2026-10-23 (``docs/demo-org.md``): the answer is ``{"success": true,
"insertId": <int>, "message": ...}``, and an ``amount`` with a ``taxId`` is the gross
amount, VAT included, although the tax codes' ``calcType`` is ``NET``.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import form_fields, post_form
from xippios.cashctrl.models import (
    AllocationInput,
    AttachmentInput,
    JournalItemInput,
    NotifyType,
    Recurrence,
    WriteAnswer,
)

__all__ = ["journal_create", "journal_fields"]


def journal_fields(
    *,
    id: int | None = None,
    amount: Decimal | None = None,
    credit_id: int | None = None,
    debit_id: int | None = None,
    allocations: Sequence[AllocationInput] | None = None,
    associate_id: int | str | None = None,
    attachments: Sequence[AttachmentInput] | None = None,
    currency_id: int | None = None,
    currency_rate: Decimal | None = None,
    custom: str | None = None,
    date_added: date | None = None,
    days_before: int | None = None,
    end_date: date | None = None,
    items: Sequence[JournalItemInput] | None = None,
    notes: str | None = None,
    notify_email: str | None = None,
    notify_person_id: int | None = None,
    notify_type: NotifyType | None = None,
    notify_user_id: int | None = None,
    recurrence: Recurrence | None = None,
    reference: str | None = None,
    sequence_number_id: int | None = None,
    start_date: date | None = None,
    tax_id: int | None = None,
    title: str | None = None,
) -> dict[str, str]:
    """The form fields of ``journal/create.json`` (``id`` unset) or ``update.json`` (set).

    Upstream's names, in the order of its table, ``id`` first; a value left at ``None``
    or an empty list is not sent (``api/_form.py``). ``custom`` is the XML text upstream
    stores (``<values><customField1>...</customField1></values>``).
    """
    return form_fields(
        {
            "id": id,
            "amount": amount,
            "creditId": credit_id,
            "debitId": debit_id,
            "allocations": allocations,
            "associateId": associate_id,
            "attachments": attachments,
            "currencyId": currency_id,
            "currencyRate": currency_rate,
            "custom": custom,
            "dateAdded": date_added,
            "daysBefore": days_before,
            "endDate": end_date,
            "items": items,
            "notes": notes,
            "notifyEmail": notify_email,
            "notifyPersonId": notify_person_id,
            "notifyType": notify_type,
            "notifyUserId": notify_user_id,
            "recurrence": recurrence,
            "reference": reference,
            "sequenceNumberId": sequence_number_id,
            "startDate": start_date,
            "taxId": tax_id,
            "title": title,
        }
    )


async def journal_create(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``journal/create.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: The form fields, from ``journal_fields`` without ``id``.

    Raises:
        RequestRejected: Upstream refused the entry, naming the fields (``debitId``).
    """
    raw = await post_form(org, "/journal/create.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="journal/create.json")
