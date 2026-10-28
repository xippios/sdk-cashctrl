"""CashCtrl's files, downloaded one way: core's ``download`` and the refusal it cannot see.

Every file operation this package wraps (the list exports ``<module>/list.csv``,
``list.xlsx`` and ``list.pdf``, and ``order/document/read.pdf``) is a ``GET`` whose query
is the operation's parameters under upstream's names, as for a ``.json`` read.
``download`` sends it through the organisation's client with core's
``AsyncClient.download`` (ADR-0019 decision 1): the body streams to a file, never held in
memory and never cached, and the limiter, ``classify`` and the retry rule apply as they
do to ``get``.

Core writes a 2xx body unread, so ``classify`` sees its status and headers only (queue
row 142), and CashCtrl refuses with HTTP 200 and ``"success": false``: a refused download
would be written as the file. ``download`` therefore streams to a temporary file beside
``dest`` and reads the answer's ``Content-Type`` before the file becomes ``dest``. JSON
(``application/json``, with or without a charset; every ``.json`` answer recorded since
2026-10-23 is ``application/json;charset=utf-8``) is a refusal: its first ``BODY_LIMIT``
bytes go through ``classify`` as an answer of the same request would, which raises
``RequestRejected``, or ``NotFoundError`` for a read by ids (``classify``), the
temporary file is removed and ``dest`` is left as it was. JSON that is no refusal
CashCtrl documents raises ``ValidationError`` the same way. Any other content type is
the file, renamed to ``dest``.
"""

import dataclasses
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import httpx
from xippios.core import (
    BODY_LIMIT,
    Downloaded,
    InvalidRequestError,
    ValidationError,
    XippiosError,
)

from xippios.cashctrl._client import NEUTRAL_HOST, SOURCE, classify, client_for

__all__ = ["JSON_MEDIA_TYPE", "download", "export_params", "is_json"]

JSON_MEDIA_TYPE = "application/json"
"""The media type of CashCtrl's JSON answers, a refusal of a download among them."""


def is_json(content_type: str | None) -> bool:
    """``application/json``, its parameters (``;charset=utf-8``) and letter case aside."""
    if content_type is None:
        return False
    return content_type.split(";", 1)[0].strip().lower() == JSON_MEDIA_TYPE


def export_params(
    params: Mapping[str, str | int], columns: Sequence[str] | None
) -> dict[str, str | int]:
    """A list's query with an export's ``columns``, "comma-separated", added when given.

    Example: ``export_params({"limit": 5}, ["dateAdded", "title"])`` gives
    ``{"limit": 5, "columns": "dateAdded,title"}``.
    """
    if columns is None:
        return dict(params)
    return {**params, "columns": ",".join(columns)}


def _refusal(
    path: Path, endpoint: str, params: Mapping[str, str | int], content_type: str
) -> XippiosError:
    """The error a JSON answer to a download stands for; ``path`` holds the answer."""
    with path.open("rb") as handle:
        head = handle.read(BODY_LIMIT + 1)
    request = httpx.Request("GET", f"https://{NEUTRAL_HOST}/api/v1/{endpoint}", params=params)
    answer = httpx.Response(
        200, headers={"Content-Type": content_type}, content=head, request=request
    )
    error = classify(answer) if len(head) <= BODY_LIMIT else None
    if error is not None:
        return error
    return ValidationError(
        f"{SOURCE}: {endpoint} answered JSON that is neither a file nor a refusal; "
        "nothing was written",
        raw=head[:BODY_LIMIT].decode("utf-8", errors="replace"),
        source=SOURCE,
    )


async def download(
    org: str,
    params: Mapping[str, str | int],
    dest: str | os.PathLike[str],
    *,
    endpoint: str,
) -> Downloaded:
    """Stream ``GET /api/v1/<endpoint>`` with ``params`` to ``dest`` for organisation ``org``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        params: The query under upstream's names, e.g. ``{"ids": "3"}``.
        dest: The file to write, e.g. ``Path("RE-2026-103.pdf")``, in a directory that
            exists; a file there is replaced once the download is complete.
        endpoint: The operation's path after ``/api/v1/``, e.g. ``"journal/list.csv"``.

    Returns:
        The file at ``dest``, as core's ``download`` describes it.

    Raises:
        InvalidRequestError: ``dest`` is a directory, or its directory does not exist,
            a bad argument (conventions §5) where core's ``download`` raises
            ``ValueError``; nothing is sent.
        RequestRejected: Upstream answered HTTP 200 with ``"success": false``.
        NotFoundError: An id no record has, on a read by ids (``order/document/read.pdf``
            answers it with HTTP 404, ``classify``).
        ValidationError: Upstream answered JSON that is no refusal.
        XippiosError: Core's taxonomy for any other failure; ``dest`` stays as it was.
    """
    client = client_for(org)
    target = Path(dest)
    if target.is_dir():
        raise InvalidRequestError("dest is a directory; name the file to write", source=SOURCE)
    if not target.parent.is_dir():
        raise InvalidRequestError("dest's directory does not exist; create it first", source=SOURCE)
    handle, name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".download"
    )
    os.close(handle)
    partial = Path(name)
    try:
        got = await client.download(str(httpx.URL(f"/{endpoint}", params=params)), partial)
        if is_json(got.content_type):
            raise _refusal(partial, endpoint, params, got.content_type or JSON_MEDIA_TYPE)
        partial.replace(target)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return dataclasses.replace(got, path=target)
