"""``GET /api/v1/person/category/list.json``: every person category of an organisation.

Reference: ``docs/upstream/person.md``, "List categories" in "Category" ("Returns a list
of all categories."). The operation documents no parameters. Its answer, as
``docs/upstream/OBSERVED.md`` notes:
``{"total": 4, "data": [...]}``, CashCtrl's four default categories, flat, each with its
``parentId``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import ListResponse, PersonCategory

__all__ = ["person_category_list"]


async def person_category_list(org: str) -> Answer[ListResponse[PersonCategory]]:
    """Call ``person/category/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    return await client_for(org).get_answer(
        "/person/category/list.json",
        parse=ListResponse[PersonCategory],
        endpoint="person/category/list.json",
    )
