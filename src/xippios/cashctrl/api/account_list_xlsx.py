"""``GET /api/v1/account/list.xlsx``: the accounts as an Excel file, streamed to ``dest``.

Reference: ``docs/upstream/account.md``, "Export to Excel" ("Returns an Excel file of
the account list."). Its documented parameters are those of ``account/list.json``, which
``account_list_params`` encodes, and ``columns`` ("The columns to include in the list,
comma-separated. Check the list.json for available column names."), all optional, which
``export_params`` adds. It documents no ``start`` or ``limit``, as the list: one file
holds every match. The file is written by ``_download.download``, which raises a refusal
sent as HTTP 200 instead of writing it (queue row 142).
"""

import os
from collections.abc import Mapping

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download

__all__ = ["account_list_xlsx"]


async def account_list_xlsx(
    org: str, params: Mapping[str, str | int], dest: str | os.PathLike[str]
) -> Downloaded:
    """Call ``account/list.xlsx`` for organisation ``org`` and write the file to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        params: The query under upstream's names, from ``account_list_params`` and
            ``export_params``.
        dest: The file to write, in a directory that exists.

    Raises:
        RequestRejected: Upstream refused the export (HTTP 200, ``"success": false``);
            ``dest`` is left as it was.
    """
    return await download(org, params, dest, endpoint="account/list.xlsx")
