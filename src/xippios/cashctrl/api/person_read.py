"""``GET /api/v1/person/read.json``: one person by its id.

Reference: ``docs/upstream/person.md``, "Read person" ("Returns a single person by ID."),
one parameter, ``id`` (mandatory, NUMBER). An unknown id is assumed to be answered with
HTTP 200 and ``"success": false``, which ``_client.classify`` raises as
``NotFoundError``: recorded for ``account`` and ``journal`` reads
(``docs/upstream/OBSERVED.md``), not for ``person``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import PersonDetail, ReadResponse

__all__ = ["person_read"]


async def person_read(org: str, id: int) -> Answer[PersonDetail]:
    """Call ``person/read.json`` for organisation ``org`` and return the person.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the person's id (not its number ``nr``).

    Raises:
        NotFoundError: No person has this id.
    """
    answer = await client_for(org).get_answer(
        "/person/read.json",
        params={"id": id},
        parse=ReadResponse[PersonDetail],
        endpoint="person/read.json",
    )
    return Answer(answer.payload.data, answer.retrieved_at)
