"""``GET /api/v1/customfield/list.json``: the custom fields of one module.

Reference: ``docs/upstream/common.md``, "List custom fields" ("Returns a list of custom
fields by type."). Its one documented parameter is mandatory: ``type`` ("The type of
custom field, meaning: which module the custom field belongs to. Possible values:
JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE,
SALARY_STATEMENT."). It documents no ``start`` or ``limit``: one answer carries every
custom field of the type. Its answer for ``PERSON``, as ``docs/upstream/OBSERVED.md`` notes:
``{"total": 0, "data": []}`` on the new demo organisation, and after
``scripts/seed_demo.py --discovery`` created one ``{"total": 1, "data": [...]}``, the record
``CustomField`` mirrors.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.api._params import present
from xippios.cashctrl.models import CustomField, CustomFieldType, ListResponse

__all__ = ["customfield_list", "customfield_list_params"]


def customfield_list_params(type: CustomFieldType) -> dict[str, str | int]:
    """The query parameters of ``customfield/list.json``: ``type``, always sent."""
    return present({"type": type})


async def customfield_list(org: str, type: CustomFieldType) -> Answer[ListResponse[CustomField]]:
    """Call ``customfield/list.json`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        type: ``type``, the module the custom fields belong to, e.g. ``PERSON``.
    """
    return await client_for(org).get_answer(
        "/customfield/list.json",
        params=customfield_list_params(type),
        parse=ListResponse[CustomField],
        endpoint="customfield/list.json",
    )
