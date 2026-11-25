"""``GET /api/v1/location/list.json``: every location of an organisation.

Reference: ``docs/upstream/meta.md``, "List locations" ("Returns a list of all
locations."). The operation documents no parameters. Its answer, as
``docs/upstream/OBSERVED.md`` notes:
``{"total": 1, "data": [...]}``, the demo organisation's main location.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import ListResponse, Location

__all__ = ["location_list"]


async def location_list(org: str) -> Answer[ListResponse[Location]]:
    """Call ``location/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
    """
    return await client_for(org).get_answer(
        "/location/list.json", parse=ListResponse[Location], endpoint="location/list.json"
    )
