"""``GET /api/v1/report/tree.json``: the report collections and elements of an organisation.

Reference: ``docs/upstream/report.md``, "Get tree of reports" ("Returns a tree of all
instanced reports containing collections and elements."). The operation documents no
parameters. Its answer, as ``docs/upstream/OBSERVED.md`` notes:
``{"total": 8, "data": [...]}``, the eight top-level
nodes of CashCtrl's default reports, each collection's elements nested under ``data``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import ListResponse, ReportTreeNode

__all__ = ["report_tree"]


async def report_tree(org: str) -> Answer[ListResponse[ReportTreeNode]]:
    """Call ``report/tree.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    return await client_for(org).get_answer(
        "/report/tree.json", parse=ListResponse[ReportTreeNode], endpoint="report/tree.json"
    )
