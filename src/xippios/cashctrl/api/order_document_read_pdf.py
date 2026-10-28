"""``GET /api/v1/order/document/read.pdf``: order documents as one PDF, streamed to ``dest``.

Reference: ``docs/upstream/order.md``, "Download PDF" ("Downloads one or multiple order
documents in one PDF file."), one parameter, ``ids`` (mandatory, CSV, "The IDs of one or
multiple orders, comma-separated."). The document is the order as upstream renders it
for its recipient; an invoice's carries the QR-bill, with the organisation's IBAN or
QR-IBAN and the recipient's address. The file is written by ``_download.download``,
which raises a refusal sent as HTTP 200 instead of writing it (queue row 142); an unknown
id is assumed to be refused as ``read.json`` refuses one (``NotFoundError``, not
observed).
"""

import os
from collections.abc import Sequence

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download
from xippios.cashctrl.api._form import ids_csv

__all__ = ["order_document_read_pdf", "order_document_read_pdf_params"]


def order_document_read_pdf_params(ids: Sequence[int]) -> dict[str, str | int]:
    """The query of ``order/document/read.pdf``: ``{"ids": "3,5"}``, the CSV upstream reads."""
    return {"ids": ids_csv(ids)}


async def order_document_read_pdf(
    org: str, ids: Sequence[int], dest: str | os.PathLike[str]
) -> Downloaded:
    """Call ``order/document/read.pdf`` for organisation ``org`` and write the PDF to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        ids: ``ids``, the orders' ids (not their numbers ``nr``), sent comma-separated.
        dest: The file to write, in a directory that exists.

    Raises:
        NotFoundError: An id no order has (assumed, as for ``order/read.json``).
        RequestRejected: Upstream refused the download otherwise; ``dest`` is left as it
            was.
    """
    params = order_document_read_pdf_params(ids)
    return await download(org, params, dest, endpoint="order/document/read.pdf")
