"""``GET /api/v1/person/list.pdf``: the persons as a PDF file, streamed to ``dest``.

Reference: ``docs/upstream/person.md``, "Export to PDF" ("Returns a PDF file of the
people list."). Its documented parameters are those of ``person/list.json``, which
``person_list_params`` encodes, and ``columns`` ("The columns to include in the list,
comma-separated. Check the list.json for available column names."), all optional, which
``export_params`` adds. The file is written by ``_download.download``, which raises a
refusal sent as HTTP 200 instead of writing it (queue row 142).
"""

import os
from collections.abc import Mapping

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download

__all__ = ["person_list_pdf"]


async def person_list_pdf(
    org: str, params: Mapping[str, str | int], dest: str | os.PathLike[str]
) -> Downloaded:
    """Call ``person/list.pdf`` for organisation ``org`` and write the file to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        params: The query under upstream's names, from ``person_list_params`` and
            ``export_params``.
        dest: The file to write, in a directory that exists.

    Raises:
        RequestRejected: Upstream refused the export (HTTP 200, ``"success": false``);
            ``dest`` is left as it was.
    """
    return await download(org, params, dest, endpoint="person/list.pdf")
