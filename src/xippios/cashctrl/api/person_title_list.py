"""``GET /api/v1/person/title/list.json``: every title of an organisation.

Reference: ``docs/upstream/person.md``, "List titles" in "Title" ("Returns a list of all
titles."). The operation documents no parameters. Observed on 2026-10-27: ``{"total": 3,
"data": [...]}``, CashCtrl's three default titles.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import ListResponse, PersonTitle

__all__ = ["person_title_list"]


async def person_title_list(org: str) -> ListResponse[PersonTitle]:
    """Call ``person/title/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/person/title/list.json")
    return parse(ListResponse[PersonTitle], raw, source=SOURCE, endpoint="person/title/list.json")
