"""``GET /api/v1/journal/read.json``: one journal entry by its id.

Reference: ``docs/upstream/journal.md``, "Read journal entry" ("Returns a single journal
entry by ID."), one parameter, ``id`` (mandatory, NUMBER). An unknown id is answered
with HTTP 200 and ``"success": false`` ("This book entry does not exist.",
``docs/upstream/OBSERVED.md``), which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import JournalEntryDetail, ReadResponse

__all__ = ["journal_read"]


async def journal_read(org: str, id: int) -> Answer[JournalEntryDetail]:
    """Call ``journal/read.json`` for organisation ``org`` and return the entry.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the journal entry's id.

    Raises:
        NotFoundError: No journal entry has this id.
    """
    answer = await client_for(org).get_answer(
        "/journal/read.json",
        params={"id": id},
        parse=ReadResponse[JournalEntryDetail],
        endpoint="journal/read.json",
    )
    return Answer(answer.payload.data, answer.retrieved_at)
