"""``GET /api/v1/journal/read.json``: one journal entry by its id.

Reference: ``docs/upstream/journal.md``, "Read journal entry" ("Returns a single journal
entry by ID."), one parameter, ``id`` (mandatory, NUMBER). An unknown id is answered
with HTTP 200 and ``"success": false`` ("This book entry does not exist.", observed on
2026-10-23), which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import JournalEntryDetail, ReadResponse

__all__ = ["journal_read"]


async def journal_read(org: str, id: int) -> JournalEntryDetail:
    """Call ``journal/read.json`` for organisation ``org`` and return the entry.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the journal entry's id.

    Raises:
        NotFoundError: No journal entry has this id.
    """
    raw = await client_for(org).get_json("/journal/read.json", params={"id": id})
    response = parse(
        ReadResponse[JournalEntryDetail], raw, source=SOURCE, endpoint="journal/read.json"
    )
    return response.data
