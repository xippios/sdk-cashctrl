"""``POST /api/v1/person/delete.json``: delete persons.

Reference: ``docs/upstream/person.md``, "Delete people" ("Deletes one or multiple
people. Returns either a success or error message."), one parameter, ``ids`` (mandatory,
CSV): "The IDs of the selected entries, comma-separated."
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import delete_fields, post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["person_delete"]


async def person_delete(org: str, ids: Sequence[int]) -> WriteAnswer:
    """Call ``person/delete.json`` for organisation ``org``: delete the persons ``ids``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        ids: ``ids``, the persons' ids, e.g. ``[13]``.

    Raises:
        RequestRejected: Upstream refused the delete.
    """
    raw = await post_form(org, "/person/delete.json", delete_fields(ids))
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="person/delete.json")
