"""``GET /api/v1/account/category/list.json``: every account category of an organisation.

Reference: ``docs/upstream/account.md``, "List categories" in "Category" ("Returns a list
of all categories."). The operation documents no parameters. Its answer, as
``docs/upstream/OBSERVED.md``
notes: ``{"total": 38, "data": [...]}``, CashCtrl's default chart, flat, each category with its
``parentId``. The same categories nested are ``account/category/tree.json`` ("Get tree
of categories"), which is not wrapped: ``AccountCategory`` says why.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import AccountCategory, ListResponse

__all__ = ["account_category_list"]


async def account_category_list(org: str) -> Answer[ListResponse[AccountCategory]]:
    """Call ``account/category/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    return await client_for(org).get_answer(
        "/account/category/list.json",
        parse=ListResponse[AccountCategory],
        endpoint="account/category/list.json",
    )
