"""``GET /api/v1/tax/list.json``: every tax code of an organisation.

Reference: ``docs/upstream/common.md``, "List tax codes" ("Returns a list of all tax
codes."). The operation documents no parameters.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import ListResponse, TaxCode

__all__ = ["tax_list"]


async def tax_list(org: str) -> Answer[ListResponse[TaxCode]]:
    """Call ``tax/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    return await client_for(org).get_answer(
        "/tax/list.json", parse=ListResponse[TaxCode], endpoint="tax/list.json"
    )
