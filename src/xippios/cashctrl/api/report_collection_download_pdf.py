"""``GET /api/v1/report/collection/download.pdf``: a report collection as one PDF, to ``dest``.

Reference: ``docs/upstream/report.md``, "Download PDF" in "Collection" ("Downloads the
PDF file for a report collection by ID and time period."; a collection "form[s] one
document" of its report elements). Its documented parameters: ``collectionId``
(mandatory, "The ID of the collection."), and, optional, ``endDate``, ``fiscalPeriod``,
``language``, ``sort`` and ``startDate``, as an element's; ``report_collection_params``
encodes them for the PDF and the Excel file alike. The file is written by
``_download.download``, which raises a refusal sent as HTTP 200 instead of writing it.
Observed on 2026-11-17: collection 1 of the demo organisation, ``Jahresbericht``, came as
``application/pdf;charset=UTF-8`` named ``Annual report 2025.pdf``, the annual report's
file but for its creation time and document id
(``report_collection_download_annualreport_pdf``).
"""

import os
from datetime import date

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download
from xippios.cashctrl.api._params import present

__all__ = ["report_collection_download_pdf", "report_collection_params"]


def report_collection_params(
    collection_id: int,
    *,
    end_date: date | None = None,
    fiscal_period: int | None = None,
    language: str | None = None,
    sort: str | None = None,
    start_date: date | None = None,
) -> dict[str, str | int]:
    """The query of a collection's ``download.pdf`` and ``download.xlsx``; ``None`` is not sent.

    Dates are sent as ``YYYY-MM-DD``, the documented format.
    """
    return present(
        {
            "collectionId": collection_id,
            "endDate": None if end_date is None else end_date.isoformat(),
            "fiscalPeriod": fiscal_period,
            "language": language,
            "sort": sort,
            "startDate": None if start_date is None else start_date.isoformat(),
        }
    )


async def report_collection_download_pdf(
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
    """Call ``report/collection/download.pdf`` for organisation ``org``; write it to ``dest``.

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
        NotFoundError: A ``collectionId`` no collection has (HTTP 404, observed for the
            Excel file on 2026-11-17).
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
    return await download(org, params, dest, endpoint="report/collection/download.pdf")
