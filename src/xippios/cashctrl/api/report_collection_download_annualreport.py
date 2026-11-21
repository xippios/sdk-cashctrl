"""``GET /api/v1/report/collection/download_annualreport.pdf``: the annual report, to ``dest``.

Reference: ``docs/upstream/report.md``, "Download annual report" ("Downloads the PDF file
for the annual report (balance sheet and profit and loss statement by default)."), one
optional parameter, ``fiscalPeriodId`` ("The ID of the fiscal period."). The file is
written by ``_download.download``, which raises a refusal sent as HTTP 200 instead of
writing it. As ``docs/upstream/OBSERVED.md`` notes, the file is the PDF of the
one collection the report tree marks system, ``Jahresbericht`` (the balance sheet and the
profit and loss), but for its creation time and document id, named ``Annual report
2025.pdf``; without ``fiscalPeriodId``, and for an id no fiscal period has, upstream
answered with the API user's current period's report, 2025, and HTTP 200.
"""

import os

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download
from xippios.cashctrl.api._params import present

__all__ = ["report_collection_download_annualreport"]


async def report_collection_download_annualreport(
    org: str, dest: str | os.PathLike[str], *, fiscal_period_id: int | None = None
) -> Downloaded:
    """Call ``report/collection/download_annualreport.pdf`` for ``org``; write it to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        dest: The file to write, in a directory that exists.
        fiscal_period_id: ``fiscalPeriodId``, a fiscal period's id; not sent when
            ``None``.

    Raises:
        RequestRejected: Upstream refused the download (HTTP 200, ``"success": false``);
            ``dest`` is left as it was.
    """
    params = present({"fiscalPeriodId": fiscal_period_id})
    return await download(org, params, dest, endpoint="report/collection/download_annualreport.pdf")
