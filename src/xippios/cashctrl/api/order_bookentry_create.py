"""``POST /api/v1/order/bookentry/create.json``: book an entry against orders.

Reference: ``docs/upstream/order.md``, Book entry ("These are all the journal book
entries that are created for an order ... either automatically from items or manually
by the user, like payments for example. Automatically created book entries cannot be
manipulated directly, only by changing items.") and "Create book entry" ("Creates a new
book entry. Returns either a success or multiple error messages (for each issue).").
Its documented parameters: ``accountId`` (mandatory, "The ID of the account (e.g. a bank
account). This is the contra account to the account defined in the order category
(typically the debtors or creditors account).") and ``orderIds`` (mandatory, CSV, "The
IDs of one or multiple orders, comma-separated."), and optionally ``amount`` ("Leave
empty to use open amount of order."), ``currencyId`` ("Leave empty to use the default
currency."), ``currencyRate``, ``date`` (``YYYY-MM-DD``), ``description`` (at most 200
characters), ``reference`` (at most 100), ``taxId`` and ``templateId`` ("The ID of the
book entry template. The templates are defined in the order category.").
``order/bookentry/update.json`` documents the same ones but ``orderIds``, and ``id``, so
``order_bookentry_fields`` encodes both.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import form_fields, ids_csv, post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["order_bookentry_create", "order_bookentry_fields"]


def order_bookentry_fields(
    *,
    id: int | None = None,
    account_id: int | None = None,
    order_ids: Sequence[int] | None = None,
    amount: Decimal | None = None,
    currency_id: int | None = None,
    currency_rate: Decimal | None = None,
    date: date | None = None,
    description: str | None = None,
    reference: str | None = None,
    tax_id: int | None = None,
    template_id: int | None = None,
) -> dict[str, str]:
    """The form fields of ``order/bookentry/create.json`` (``id`` unset) or ``update.json``.

    Upstream's names, in the order of its tables, ``id`` first: ``orderIds``
    comma-separated (``20,21``), ``date`` as ``YYYY-MM-DD``; a value left at ``None`` is
    not sent, so upstream applies its own default (the open amount, the default
    currency). Checking the values is the task's.
    """
    return form_fields(
        {
            "id": id,
            "accountId": account_id,
            "orderIds": None if order_ids is None else ids_csv(order_ids),
            "amount": amount,
            "currencyId": currency_id,
            "currencyRate": currency_rate,
            "date": date,
            "description": description,
            "reference": reference,
            "taxId": tax_id,
            "templateId": template_id,
        }
    )


async def order_bookentry_create(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``order/bookentry/create.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: The form fields, from ``order_bookentry_fields``.

    Raises:
        RequestRejected: Upstream refused the book entry, naming the fields.
    """
    raw = await post_form(org, "/order/bookentry/create.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/bookentry/create.json")
