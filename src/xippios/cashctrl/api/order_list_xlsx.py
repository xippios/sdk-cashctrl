"""``GET /api/v1/order/list.xlsx``: the orders as an Excel file, streamed to ``dest``.

Reference: ``docs/upstream/order.md``, "Export to Excel" ("Returns an Excel file of the
orders list per type (sales or purchase)."). Its documented parameters are those of
``order/list.json``, which ``order_list_params`` encodes, and ``columns`` ("The columns
to include in the list, comma-separated. Check the list.json for available column
names."), all optional, which ``export_params`` adds. The file is written by
``_download.download``, which raises a refusal sent as HTTP 200 instead of writing it
(queue row 142).
"""

import os
from collections.abc import Mapping

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download

__all__ = ["order_list_xlsx"]


async def order_list_xlsx(
    org: str, params: Mapping[str, str | int], dest: str | os.PathLike[str]
) -> Downloaded:
    """Call ``order/list.xlsx`` for organisation ``org`` and write the file to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        params: The query under upstream's names, from ``order_list_params`` and
            ``export_params``.
        dest: The file to write, in a directory that exists.

    Raises:
        RequestRejected: Upstream refused the export (HTTP 200, ``"success": false``);
            ``dest`` is left as it was.
    """
    return await download(org, params, dest, endpoint="order/list.xlsx")
