"""``GET /api/v1/account/category/list.json``: every account category of an organisation.

Reference: ``docs/upstream/account.md``, "List categories" in "Category" ("Returns a list
of all categories."). The operation documents no parameters. Observed on 2026-10-27:
``{"total": 38, "data": [...]}``, CashCtrl's default chart, flat, each category with its
``parentId``. The same categories nested are ``account/category/tree.json`` ("Get tree
of categories"), which is not wrapped: ``AccountCategory`` says why.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import AccountCategory, ListResponse

__all__ = ["account_category_list"]


async def account_category_list(org: str) -> ListResponse[AccountCategory]:
    """Call ``account/category/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/account/category/list.json")
    return parse(
        ListResponse[AccountCategory], raw, source=SOURCE, endpoint="account/category/list.json"
    )
