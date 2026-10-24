"""``POST /api/v1/journal/delete.json``: delete manual journal entries.

Reference: ``docs/upstream/journal.md``, "Delete journal entries" ("Deletes one or
multiple manual journal entries. Note that you cannot delete automatically created
entries here ... Returns either a success or error message."), one parameter, ``ids``
(mandatory, CSV): "The IDs of the selected entries, comma-separated."
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import delete_fields, post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["journal_delete"]


async def journal_delete(org: str, ids: Sequence[int]) -> WriteAnswer:
    """Call ``journal/delete.json`` for organisation ``org``: delete the entries ``ids``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        ids: ``ids``, the entries' ids, e.g. ``[52]``.

    Raises:
        RequestRejected: Upstream refused the delete.
    """
    raw = await post_form(org, "/journal/delete.json", delete_fields(ids))
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="journal/delete.json")
