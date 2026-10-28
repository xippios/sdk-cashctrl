"""``GET /api/v1/person/category/list.json``: every person category of an organisation.

Reference: ``docs/upstream/person.md``, "List categories" in "Category" ("Returns a list
of all categories."). The operation documents no parameters. Observed on 2026-10-27:
``{"total": 4, "data": [...]}``, CashCtrl's four default categories, flat, each with its
``parentId``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import ListResponse, PersonCategory

__all__ = ["person_category_list"]


async def person_category_list(org: str) -> ListResponse[PersonCategory]:
    """Call ``person/category/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/person/category/list.json")
    return parse(
        ListResponse[PersonCategory], raw, source=SOURCE, endpoint="person/category/list.json"
    )
