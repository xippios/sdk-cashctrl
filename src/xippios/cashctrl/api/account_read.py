"""``GET /api/v1/account/read.json``: one account by its id.

Reference: ``docs/upstream/account.md``, "Read account" ("Returns a single account by
ID."), one parameter, ``id`` (mandatory, NUMBER). An unknown id is answered with HTTP 200
and ``"success": false``, which ``_client.classify`` raises as ``NotFoundError``.
"""

from xippios.core import Answer

from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import AccountDetail, ReadResponse

__all__ = ["account_read"]


async def account_read(org: str, id: int) -> Answer[AccountDetail]:
    """Call ``account/read.json`` for organisation ``org`` and return the account.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        id: ``id``, the account's id (not its number).

    Raises:
        NotFoundError: No account has this id.
    """
    answer = await client_for(org).get_answer(
        "/account/read.json",
        params={"id": id},
        parse=ReadResponse[AccountDetail],
        endpoint="account/read.json",
    )
    return Answer(answer.payload.data, answer.retrieved_at)
