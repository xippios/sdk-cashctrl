"""``GET /api/v1/person/read.json``: one person by its id.

Reference: ``docs/upstream/person.md``, "Read person" ("Returns a single person by ID."),
one parameter, ``id`` (mandatory, NUMBER). An unknown id is answered with HTTP 200 and
``"success": false``, which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import PersonDetail, ReadResponse

__all__ = ["person_read"]


async def person_read(org: str, id: int) -> PersonDetail:
    """Call ``person/read.json`` for organisation ``org`` and return the person.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the person's id (not its number ``nr``).

    Raises:
        NotFoundError: No person has this id.
    """
    raw = await client_for(org).get_json("/person/read.json", params={"id": id})
    response = parse(ReadResponse[PersonDetail], raw, source=SOURCE, endpoint="person/read.json")
    return response.data
