"""``GET /api/v1/report/tree.json``: the report collections and elements of an organisation.

Reference: ``docs/upstream/report.md``, "Get tree of reports" ("Returns a tree of all
instanced reports containing collections and elements."). The operation documents no
parameters. Observed on 2026-10-27: ``{"total": 8, "data": [...]}``, the eight top-level
nodes of CashCtrl's default reports, each collection's elements nested under ``data``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import ListResponse, ReportTreeNode

__all__ = ["report_tree"]


async def report_tree(org: str) -> ListResponse[ReportTreeNode]:
    """Call ``report/tree.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/report/tree.json")
    return parse(ListResponse[ReportTreeNode], raw, source=SOURCE, endpoint="report/tree.json")
