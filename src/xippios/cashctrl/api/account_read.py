"""``GET /api/v1/account/read.json``: one account by its id.

Reference: ``docs/upstream/account.md``, "Read account" ("Returns a single account by
ID."), one parameter, ``id`` (mandatory, NUMBER). An unknown id is answered with HTTP 200
and ``"success": false``, which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.models import AccountDetail, ReadResponse

__all__ = ["account_read"]


async def account_read(org: str, id: int) -> AccountDetail:
    """Call ``account/read.json`` for organisation ``org`` and return the account.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the account's id (not its number).

    Raises:
        NotFoundError: No account has this id.
    """
    raw = await client_for(org).get_json("/account/read.json", params={"id": id})
    response = parse(ReadResponse[AccountDetail], raw, source=SOURCE, endpoint="account/read.json")
    return response.data
