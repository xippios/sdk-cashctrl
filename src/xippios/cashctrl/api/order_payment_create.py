"""``POST /api/v1/order/payment/create.json``: create the payment of orders.

Reference: ``docs/upstream/order.md``, "Payment" ("Note that this does not create any
book entries ... Here we are either creating an ISO 20022 pain.001 file or a PDF to
download. The pain.001 file can be used in e-banking to automatically process multiple
payments. Please first use the Create endpoint (don't skip this!), and then the Download
endpoint.") and "Create payment" ("Creates a new payment. This must first be executed
before downloading the pain.001 or PDF file with the next endpoint, otherwise we won't
be able to match the payments from a camt.052/053/054 file later on. Returns either a
success or multiple error messages (for each issue)."). Its documented parameters:
``date`` (mandatory, "The execution date for the payment", ``YYYY-MM-DD``), ``orderIds``
(mandatory, CSV, "The IDs of the selected orders, comma-separated."), and optionally
``amount`` ("A partial payment amount per order. Leave empty to pay all open amounts."),
``isCombine`` ("If set, merges multiple payments to the same payee into one
transaction."), ``statusId`` ("The ID of the new status for the order.") and ``type``
("Defaults to PAIN (pain.001). Possible values: PAIN, SEPA_PAIN, WIRE_PDF, CASH_PDF.").
The snapshot documents no payment read, list or delete; ``order/payment/download``, the
file, takes the same parameters and is not wrapped here.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import form_fields, ids_csv, post_form
from xippios.cashctrl.models import PaymentType, WriteAnswer

__all__ = ["order_payment_create", "order_payment_create_fields"]


def order_payment_create_fields(
    *,
    date: date,
    order_ids: Sequence[int],
    amount: Decimal | None = None,
    is_combine: bool | None = None,
    status_id: int | None = None,
    type: PaymentType | None = None,
) -> dict[str, str]:
    """The form fields of ``order/payment/create.json``, in the order of its table.

    ``orderIds`` comma-separated (``20,21``), ``date`` as ``YYYY-MM-DD``, ``isCombine``
    ``true`` or ``false``; a value left at ``None`` is not sent, so upstream applies its
    own default (every open amount, ``PAIN``). Checking the values is the task's.
    """
    return form_fields(
        {
            "date": date,
            "orderIds": ids_csv(order_ids),
            "amount": amount,
            "isCombine": is_combine,
            "statusId": status_id,
            "type": type,
        }
    )


async def order_payment_create(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``order/payment/create.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: The form fields, from ``order_payment_create_fields``.

    Raises:
        RequestRejected: Upstream refused the payment, naming the fields.
    """
    raw = await post_form(org, "/order/payment/create.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="order/payment/create.json")
