"""``GET /api/v1/report/collection/download.xlsx``: a collection as one Excel file, to ``dest``.

Reference: ``docs/upstream/report.md``, "Download Excel" in "Collection" ("Downloads the
Excel file for a report collection by ID and time period. Each report element is a
worksheet within the Excel file."). Its documented parameters are those of
``download.pdf``, which ``report_collection_params`` encodes. The file is written by
``_download.download``, which raises a refusal sent as HTTP 200 instead of writing it.
As ``docs/upstream/OBSERVED.md`` notes, collection 1 came as the spreadsheet media type with
``charset=UTF-8``, named ``Annual report 2025.xlsx``, and a ``collectionId`` no
collection has was answered with HTTP 404, which ``_client.classify`` raises as
``NotFoundError``.
"""

import os
from datetime import date

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download
from xippios.cashctrl.api.report_collection_download_pdf import report_collection_params

__all__ = ["report_collection_download_xlsx"]


async def report_collection_download_xlsx(
    org: str,
    collection_id: int,
    dest: str | os.PathLike[str],
    *,
    end_date: date | None = None,
    fiscal_period: int | None = None,
    language: str | None = None,
    sort: str | None = None,
    start_date: date | None = None,
) -> Downloaded:
    """Call ``report/collection/download.xlsx`` for organisation ``org``; write it to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        collection_id: ``collectionId``, the report collection.
        dest: The file to write, in a directory that exists.
        end_date: ``endDate``, the last day of the report period.
        fiscal_period: ``fiscalPeriod``, a fiscal period's id; upstream derives the
            start and end date from it, overriding ``startDate`` and ``endDate``.
        language: ``language``, the language of the report.
        sort: ``sort``, the column to sort the list by.
        start_date: ``startDate``, the first day of the report period.

    Raises:
        NotFoundError: A ``collectionId`` no collection has (HTTP 404).
        RequestRejected: Upstream refused the download otherwise; ``dest`` is left as it
            was.
    """
    params = report_collection_params(
        collection_id,
        end_date=end_date,
        fiscal_period=fiscal_period,
        language=language,
        sort=sort,
        start_date=start_date,
    )
    return await download(org, params, dest, endpoint="report/collection/download.xlsx")
