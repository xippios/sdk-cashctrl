"""``POST /api/v1/person/update.json``: change an existing person.

Reference: ``docs/upstream/person.md``, "Update person": the parameters of "Create
person" and ``id`` (mandatory). "Note that all parameters must be submitted, omitted
parameters are treated as empty values." The form fields come from ``person_fields``
with ``id`` set; ``tasks_write.update_person`` derives every one of them from the record
before it changes any.
"""

from collections.abc import Mapping

from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import post_form
from xippios.cashctrl.models import WriteAnswer

__all__ = ["person_update"]


async def person_update(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``person/update.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: Every form field of the person, ``id`` included, from ``person_fields``.

    Raises:
        RequestRejected: Upstream refused the update.
    """
    raw = await post_form(org, "/person/update.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="person/update.json")
