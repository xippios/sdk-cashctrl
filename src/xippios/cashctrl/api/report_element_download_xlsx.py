"""``GET /api/v1/report/element/download.xlsx``: one report as an Excel file, to ``dest``.

Reference: ``docs/upstream/report.md``, "Download Excel" in "Element" ("Downloads the
Excel file for a single element by ID and time period."). Its documented parameters are
those of ``report/element/data.json``, which ``report_element_data_params`` encodes, as
for ``download.pdf``. The file is written by ``_download.download``, which raises a
refusal sent as HTTP 200 instead of writing it. As ``docs/upstream/OBSERVED.md`` notes, the
balance sheet
of 2025 came as ``application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;
charset=UTF-8`` named ``Balance 2025.xlsx``, for a fiscal period and for two dates alike.
"""

import os
from datetime import date

from xippios.core import Downloaded

from xippios.cashctrl.api._download import download
from xippios.cashctrl.api.report_element_data import report_element_data_params

__all__ = ["report_element_download_xlsx"]


async def report_element_download_xlsx(
    org: str,
    element_id: int,
    dest: str | os.PathLike[str],
    *,
    end_date: date | None = None,
    fiscal_period: int | None = None,
    language: str | None = None,
    sort: str | None = None,
    start_date: date | None = None,
) -> Downloaded:
    """Call ``report/element/download.xlsx`` for organisation ``org`` and write it to ``dest``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        element_id: ``elementId``, the report element.
        dest: The file to write, in a directory that exists.
        end_date: ``endDate``, the last day of the report period.
        fiscal_period: ``fiscalPeriod``, a fiscal period's id; upstream derives the
            start and end date from it, overriding ``startDate`` and ``endDate``.
        language: ``language``, the language of the report.
        sort: ``sort``, the column to sort the list by.
        start_date: ``startDate``, the first day of the report period.

    Raises:
        NotFoundError: An ``elementId`` no report has (HTTP 404, as for ``download.pdf``).
        RequestRejected: Upstream refused the download otherwise; ``dest`` is left as it
            was.
    """
    params = report_element_data_params(
        element_id,
        end_date=end_date,
        fiscal_period=fiscal_period,
        language=language,
        sort=sort,
        start_date=start_date,
    )
    return await download(org, params, dest, endpoint="report/element/download.xlsx")
