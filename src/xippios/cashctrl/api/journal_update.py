"""``POST /api/v1/journal/update.json``: change an existing manual journal entry.

Reference: ``docs/upstream/journal.md``, "Update journal entry": the parameters of
"Create journal entry" and ``id`` (mandatory). "Note that you cannot update
automatically created entries this way" and "Note that all parameters must be
submitted, omitted parameters are treated as empty values." The form fields come from
``journal_fields`` with ``id`` set; ``tasks_write.update_journal_entry`` derives every
one of them from the record before it changes any.
"""

from collections.abc import Mapping

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["journal_update"]


async def journal_update(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``journal/update.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: Every form field of the entry, ``id`` included, from ``journal_fields``.

    Raises:
        RequestRejected: Upstream refused the update.
    """
    raw = await post_form(org, "/journal/update.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="journal/update.json")
