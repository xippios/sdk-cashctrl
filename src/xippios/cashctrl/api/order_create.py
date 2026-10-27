"""``POST /api/v1/order/create.json``: a new order (offer, invoice, purchase order, ...).

Reference: ``docs/upstream/order.md``, "Create order" ("Creates a new order. Returns
either a success or multiple error messages (for each issue)."). Its documented
parameters: ``associateId`` (mandatory, CSV: "If you enter multiple IDs it will create a
separate document for each business partner"), ``categoryId`` and ``date`` (mandatory),
and optionally ``accountId``, ``attachments``, ``currencyId``, ``currencyRate``,
``custom``, ``daysBefore``, ``description``, ``discountPercentage``, ``dueDays``,
``endDate``, ``groupId``, ``isDisplayItemGross``, ``items``, ``language``, ``notes``,
``notifyEmail``, ``notifyPersonId``, ``notifyType``, ``notifyUserId``, ``nr`` (mandatory
when neither the request nor the category sets a sequence number), ``previousId``,
``recurrence``, ``responsiblePersonId``, ``roundingId``, ``sequenceNumberId``,
``startDate`` and ``statusId``.

Observed on 2026-10-23 (``docs/demo-org.md``): the answer is ``{"success": true,
"insertId": <int>, "message": ...}``, and CashCtrl read the items' ``unitPrice`` as gross,
VAT included (``baseValue`` ``GROSS`` on every item read back).
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import form_fields, ids_csv, post_form
from xippios.cashctrl.models import (
    AttachmentInput,
    Language,
    NotifyType,
    OrderItemInput,
    Recurrence,
    WriteAnswer,
)

__all__ = ["order_create", "order_fields"]


def order_fields(
    *,
    id: int | None = None,
    associate_id: int | Sequence[int] | None = None,
    category_id: int | None = None,
    date: date | None = None,
    account_id: int | None = None,
    attachments: Sequence[AttachmentInput] | None = None,
    currency_id: int | None = None,
    currency_rate: Decimal | None = None,
    custom: str | None = None,
    days_before: int | None = None,
    description: str | None = None,
    discount_percentage: Decimal | None = None,
    due_days: int | None = None,
    end_date: date | None = None,
    group_id: int | None = None,
    is_display_item_gross: bool | None = None,
    items: Sequence[OrderItemInput] | None = None,
    language: Language | None = None,
    notes: str | None = None,
    notify_email: str | None = None,
    notify_person_id: int | None = None,
    notify_type: NotifyType | None = None,
    notify_user_id: int | None = None,
    nr: str | None = None,
    previous_id: int | None = None,
    recurrence: Recurrence | None = None,
    responsible_person_id: int | None = None,
    rounding_id: int | None = None,
    sequence_number_id: int | None = None,
    start_date: date | None = None,
    status_id: int | None = None,
) -> dict[str, str]:
    """The form fields of ``order/create.json`` (``id`` unset) or ``update.json`` (set).

    Upstream's names, in the order of the create table, ``id`` first. ``associate_id`` is
    one id or, for a create, several, sent comma-separated (``7`` or ``7,8``;
    ``update.json`` takes one, a NUMBER); a value left at ``None`` or an empty list is
    not sent (``api/_form.py``), and ``custom`` is the XML text upstream stores. The
    mandatory ``associateId``, ``categoryId`` and ``date`` are the tasks' to require.
    """
    associates = [associate_id] if isinstance(associate_id, int) else associate_id
    return form_fields(
        {
            "id": id,
            "associateId": None if associates is None else ids_csv(list(associates)),
            "categoryId": category_id,
            "date": date,
            "accountId": account_id,
            "attachments": attachments,
            "currencyId": currency_id,
            "currencyRate": currency_rate,
            "custom": custom,
            "daysBefore": days_before,
            "description": description,
            "discountPercentage": discount_percentage,
            "dueDays": due_days,
            "endDate": end_date,
            "groupId": group_id,
            "isDisplayItemGross": is_display_item_gross,
            "items": items,
            "language": language,
            "notes": notes,
            "notifyEmail": notify_email,
            "notifyPersonId": notify_person_id,
            "notifyType": notify_type,
            "notifyUserId": notify_user_id,
            "nr": nr,
            "previousId": previous_id,
            "recurrence": recurrence,
            "responsiblePersonId": responsible_person_id,
            "roundingId": rounding_id,
            "sequenceNumberId": sequence_number_id,
            "startDate": start_date,
            "statusId": status_id,
        }
    )


async def order_create(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``order/create.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: The form fields, from ``order_fields``.

    Raises:
        RequestRejected: Upstream refused the order, naming the fields.
    """
    raw = await post_form(org, "/order/create.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/create.json")
