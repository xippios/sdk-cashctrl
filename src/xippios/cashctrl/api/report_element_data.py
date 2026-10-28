"""``GET /api/v1/report/element/data.json``: one report element's data for a period.

Reference: ``docs/upstream/report.md``, "Read JSON data" in "Element" ("Returns the JSON
data of a single element by ID for the given time period."). Its documented parameters:
``elementId`` (mandatory, "The ID of the element."), and, optional, ``endDate`` and
``startDate`` ("The end date of the report period." and the start date, "Format:
YYYY-MM-DD"), ``fiscalPeriod`` ("The ID of the fiscal period. This overrides the
``startDate`` and ``endDate`` parameter, as these are derived from the fiscal period."),
``language`` ("The language of the report.") and ``sort`` ("The column to sort the list
by."). The documentation gives no response schema. Observed on 2026-10-27 for the balance
sheet of fiscal period 2025: ``{"total": 2, "data": [...], "properties": {...}}``.
"""

from datetime import date

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._params import present
from xippios.cashctrl.models import ReportData

__all__ = ["report_element_data", "report_element_data_params"]


def report_element_data_params(
    element_id: int,
    *,
    end_date: date | None = None,
    fiscal_period: int | None = None,
    language: str | None = None,
    sort: str | None = None,
    start_date: date | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``report/element/data.json``; ``None`` is not sent.

    Dates are sent as ``YYYY-MM-DD``, the documented format.
    """
    return present(
        {
            "elementId": element_id,
            "endDate": None if end_date is None else end_date.isoformat(),
            "fiscalPeriod": fiscal_period,
            "language": language,
            "sort": sort,
            "startDate": None if start_date is None else start_date.isoformat(),
        }
    )


async def report_element_data(
    org: str,
    element_id: int,
    *,
    end_date: date | None = None,
    fiscal_period: int | None = None,
    language: str | None = None,
    sort: str | None = None,
    start_date: date | None = None,
) -> ReportData:
    """Call ``report/element/data.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        element_id: ``elementId``, the report element.
        end_date: ``endDate``, the last day of the report period.
        fiscal_period: ``fiscalPeriod``, a fiscal period's id; upstream derives the
            start and end date from it, overriding ``startDate`` and ``endDate``.
        language: ``language``, the language of the report.
        sort: ``sort``, the column to sort the list by.
        start_date: ``startDate``, the first day of the report period.
    """
    params = report_element_data_params(
        element_id,
        end_date=end_date,
        fiscal_period=fiscal_period,
        language=language,
        sort=sort,
        start_date=start_date,
    )
    raw = await client_for(org).get_json("/report/element/data.json", params=params)
    return parse(ReportData, raw, source=SOURCE, endpoint="report/element/data.json")
