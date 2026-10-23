"""``GET /api/v1/tax/list.json``: every tax code of an organisation.

Reference: ``docs/upstream/common.md``, "List tax codes" ("Returns a list of all tax
codes."). The operation documents no parameters.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import ListResponse, TaxCode

__all__ = ["tax_list"]


async def tax_list(org: str) -> ListResponse[TaxCode]:
    """Call ``tax/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/tax/list.json")
    return parse(ListResponse[TaxCode], raw, source=SOURCE, endpoint="tax/list.json")
