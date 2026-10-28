"""``GET /api/v1/location/list.json``: every location of an organisation.

Reference: ``docs/upstream/meta.md``, "List locations" ("Returns a list of all
locations."). The operation documents no parameters. Observed on 2026-10-27:
``{"total": 1, "data": [...]}``, the demo organisation's main location.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import ListResponse, Location

__all__ = ["location_list"]


async def location_list(org: str) -> ListResponse[Location]:
    """Call ``location/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    raw = await client_for(org).get_json("/location/list.json")
    return parse(ListResponse[Location], raw, source=SOURCE, endpoint="location/list.json")
