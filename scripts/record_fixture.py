"""Record one exchange with the demo organisation into a fixture (``/record-fixture``).

Run from the repository root with the demo pair (``CASHCTRL_DEMO_SUBDOMAIN``,
``CASHCTRL_DEMO_API_KEY``) in the environment::

    uv run scripts/record_fixture.py account/read.json unknown_id id=999999999
    uv run scripts/record_fixture.py account/list.json wrong_key --wrong-key
    uv run scripts/record_fixture.py journal/delete.json ok --method POST ids=52

``<endpoint>`` is the upstream path after ``/api/v1/`` as ``docs/upstream/`` writes it;
the fixture lands at ``tests/fixtures/<endpoint>/<case>.json`` with the endpoint's slashes
as underscores and without its extension: ``tests/fixtures/account_read/unknown_id.json``.
``key=value`` arguments are query parameters of a GET and form fields of a POST, named
as upstream names them, sent in the order given.

The organisation is not a parameter. The recorder removes ``CASHCTRL_ORGS`` from its own
environment and always records through ``client_for("demo")``'s configuration, so it
cannot reach a productive organisation, in a client of its own that never retries
(``recording_client``, ``RetryPolicy(max_attempts=1)``): a 5xx is recorded as it came and
spends no request on a retry. ``--wrong-key`` sends ``not-a-valid-key`` instead of the
real key, through the same kind of client, to record a 401 without touching the real key.

The demo organisation holds synthetic books only, seeded by ``scripts/seed_demo.py`` and
described in ``docs/demo-org.md``: invented companies on placeholder streets,
``.example`` addresses, invented amounts. So every module and every amount may be
recorded. These policies stand all the same; every refusal writes nothing, says why,
never shows a value, and exits with status 1:

- GET, and POST for the eleven write paths only. ``--method POST`` is allowed for
  exactly the operations this package's write tools call (``WRITE_PATHS``):
  ``journal/create.json``, ``journal/update.json``, ``journal/delete.json``,
  ``person/create.json``, ``person/update.json``, ``person/delete.json``,
  ``order/create.json``, ``order/update.json``, ``order/delete.json``,
  ``order/update_status.json`` and ``order/payment/create.json``. It sends the
  ``key=value`` pairs as a form body, as the write tools do (``api/_form.py``:
  ``application/x-www-form-urlencoded; charset=UTF-8``). Every other POST
  (``order/continue.json``, ``account/create.json``, ``order/bookentry/create.json``,
  a POST to a list) and every other method is refused before a request is sent, and so is a
  ``create.json`` whose pairs do not carry the marker ``xippios-live`` (``MARK``) in a
  value: a write records a marked record, updates it or deletes it, and nothing else.
  ``order/update_status.json`` and ``order/payment/create.json`` change orders and carry
  no free text to mark (a payment has no text field): the recorder reads every order
  their ``ids`` or ``orderIds`` name (``order/read.json``, one GET each, through the
  recording client) and refuses the write, before it is sent, unless each order is
  marked as the live tests mark theirs, ``MARK`` in its ``description`` or ``MARK`` as
  its ``nr``; an order that cannot be read refuses it too (``unmarked_orders``, Johannes,
  2026-10-28). A recorded write changes the demo organisation: the recorder says so
  after the request and asks for the matching delete, recorded or run, so that no created
  record stays behind; upstream documents no delete of a payment, so after one it asks
  for the orders' delete, which leaves the payment behind.
- ``.json`` only. An endpoint without the extension answers a bare number or a document
  (``account/balance``, ``account/costcenter/balance``, ``fiscalperiod/result``,
  ``setting/get``) and an export (``.pdf``, ``.xlsx``, ``.csv``, ``.zip``) a file; both
  are refused before a request is sent.
- No e-mail addresses. Every e-mail-shaped string in the request URL, the request
  body, the response header values and the response body becomes ``user@example.com``,
  with ``@`` written plainly, as ``%40`` or as the HTML entities ``&#64;``, ``&#x40;``
  and ``&commat;`` (``notes`` and footers are HTML upstream); ``SYSTEM`` in
  ``createdBy`` is not an address and stays. The synthetic books use reserved
  ``.example`` addresses, but ``createdBy`` and ``lastUpdatedBy`` may carry the address
  of the user who wrote a record, a real person, so the scrub stays.
- No API user tags. CashCtrl names an API user in ``createdBy`` and ``lastUpdatedBy`` as
  ``API:`` and the first four characters of its key (observed on 2026-10-23 on the
  records ``scripts/seed_demo.py`` wrote). Every such tag becomes ``API:REDACTED``,
  whichever key it comes from, with the marker in any case, at the start of a word or
  right after a JSON escape. A tag the scrub cannot reach (glued to a word, or behind a
  Unicode escape) is refused by the final check.
- No token-like fields and no personal identifiers. A body field named ``hash``,
  ``token``, ``secret``, ``apiKey`` (``api_key``, ``api-key``) or ``ssn``, or whose name
  ends in ``iban`` (``iban``, ``qrIban``, ``qr_iban``, ``orgIban``, ``orgQrIban``,
  ``recipientIban``; queue row 243), the identifiers this package keeps out of its
  projections (ADR-0017), in any case, has its text value replaced by ``REDACTED``.
  ``order/read.json`` sends ``hash``, an undocumented 32-character text that may be the
  token of a public link to the order document (observed on 2026-10-23, not verified);
  ``person/list.json`` sends ``ssn`` and ``iban``, ``location/list.json`` ``iban`` and
  ``qrIban`` and ``order/document/read.json`` ``orgIban``, ``orgQrIban`` and
  ``recipientIban``, only ever seen ``null``; the others were never seen and are
  scrubbed should they appear. The final check refuses any value under such a name but ``null``
  or ``REDACTED``, whatever its type or shape: text behind an escaped field name, a
  number, an array, an object; in a write's form body as a field (``ssn=...``) and
  inside a JSON value (the ``iban`` of an item of ``bankAccounts``), which the raw-text
  scrub does not reach, so such a write is not recorded. A compound name
  (``publicHash``) is not scrubbed; it is written for review.

Nothing unscrubbed touches disk. The request goes through the real client with
``raise_on_error=False``, and core's ``fixture_from_response`` turns the exchange into a
fixture in memory with ``Scrub(secrets=[key, its basic-auth token])`` (conventions §10):
credentials scrubbed, the key and its token made ``REDACTED`` where they appear as given,
and a plain verify that refuses the exchange when either is still there as given; core
also refuses a body that is not UTF-8 text, which no scrub can read (exports are out of
scope for fixtures, which the recorder's message says first). Then the recorder's own
step, ``TenantScrub``, runs on the ``Fixture`` core returns (ADR-0024, decision 4): the
demo host (``<CASHCTRL_DEMO_SUBDOMAIN>.cashctrl.com``, in any case, IDNA or
percent-encoded) becomes ``demo.cashctrl.com``, the host offline tests replay against, in
the URL, the headers and both bodies; the key and its token become ``REDACTED`` in any
percent-encoded form too; and ``scrub_text`` runs over the URL, every response header
value and both bodies: every e-mail address becomes ``user@example.com``, every API user
tag ``API:REDACTED`` and every token-like field's value ``REDACTED``. Its verify then
searches the URL, every header name and value and both bodies, raw and, for a JSON body,
every decoded string, for the demo host, the subdomain on its own and the key or its
token, plain or percent-encoded, behind a JSON escape included, and refuses the fixture
in its own words. A refusal prints its reason, never a value. A response in which the
key or its basic-auth token was redacted is written, since nothing of either is left, but
goes to review with exit status 1: upstream should never send them back.

The fixture is then checked last, before the one write, in its serialised text, in
every decoded string of a JSON response body and, for a write, in the request body: its
raw text, every form field name and value decoded, and every decoded string of a value
that is JSON (``items``, ``addresses``). It looks for what core does not know: the subdomain on its
own, an e-mail address other than ``user@example.com``, an API user tag other than
``API:REDACTED`` in any case and position (the key's own tag also with ``:`` URL-encoded,
as an HTML entity or followed by a space), the key's first four characters on their own,
reported as a possible key prefix, or any value but ``null`` or ``REDACTED`` under a
token-like or identifier field name, also inside a JSON value of a form body; any of them
means nothing is written and the exit status is 1. A
key-like name whose value is not ``REDACTED`` is written for review, also with exit
status 1. Only the status and the scrubbed URL are printed.

The write is the recorder's own, not core's ``record``: ``record`` writes as soon as
core's verify passes, before the recorder's step and final check could run.
"""

import argparse
import base64
import dataclasses
import json
import os
import re
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

import httpx
from xippios.core import AsyncClient, BasicKeyAuth, RetryPolicy, sync
from xippios.core.testing import REDACTED, Fixture, Scrub, fixture_from_response, fixture_path

from xippios.cashctrl._client import DEMO, SOURCE, TENANTS, client_for
from xippios.cashctrl.api._form import FORM_CONTENT_TYPE

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
REPLAY_HOST = "demo.cashctrl.com"
WRONG_KEY = "not-a-valid-key"  # pragma: allowlist secret (a deliberately invalid key)
KEY_LIKE = re.compile(r"api[_-]?key|token|secret|authorization|password|hash", re.IGNORECASE)
_ENDPOINT = re.compile(r"[a-z][a-z0-9_]*(?:/[a-z][a-z0-9_]*)*(?:\.[a-z]+)?")
WRITE_PATHS = frozenset(
    {
        "journal/create.json",
        "journal/update.json",
        "journal/delete.json",
        "person/create.json",
        "person/update.json",
        "person/delete.json",
        "order/create.json",
        "order/update.json",
        "order/delete.json",
        "order/update_status.json",
        "order/payment/create.json",
    }
)
"""The endpoints a POST may be recorded for: exactly those the write tools call."""
MARK = "xippios-live"
"""The marker a recorded create must carry in one of its values (title, company, ...)."""
ORDER_WRITES = {"order/update_status.json": "ids", "order/payment/create.json": "orderIds"}
"""The writes that change existing orders, by the field that names them, comma-separated.

Neither carries a text to mark, so every order they name must be marked
(``unmarked_orders``) before the write is sent.
"""
_CASE = re.compile(r"[a-z0-9][a-z0-9_]*")

SCRUBBED_EMAIL = "user@example.com"
EMAIL = re.compile(
    r"(?:[\w.+-]|%(?![0-9A-Fa-f]{2}))+"
    r"(?P<at>@|%40|&#0*64;?|&#[xX]0*40;?|&commat;)[\w.-]+\.[^\W\d_]{2,}"
)
"""An e-mail-shaped string: ``@`` plain, as ``%40`` (a query string) or as an HTML entity.

The local part never takes in a percent-escape (``%22``): in a form body, the address
inside ``%7B%22address%22%3A%22user%40example.com`` starts after ``%22``, and the escapes
before it stay as they were sent.
"""
# The same, but never starting inside a JSON escape (\n, \u00e9) or a percent-escape, and
# allowed to start right after one (a form body): scrubbing the raw text of a JSON body
# then keeps it JSON, and the raw text of a form body keeps it the form that was sent.
_EMAIL_IN_TEXT = re.compile(
    r"(?:(?<=\\[nrtbf])|(?<=%[0-9A-Fa-f]{2})|(?<![\w.%+\\-]))" + EMAIL.pattern
)
_SCRUBBED_EMAILS = frozenset({SCRUBBED_EMAIL, SCRUBBED_EMAIL.replace("@", "%40")})

TOKEN_FIELD_NAME = re.compile(r"hash|token|secret|api[_-]?key|ssn|[\w-]*iban", re.IGNORECASE)
"""Body fields whose value may grant access or identify a person, by name in any case.

Whole names, but for an IBAN: every name that ends in ``iban``. ``ssn`` and ``iban`` are
the documented personal identifiers this package keeps out of its projections
(ADR-0017); ``qrIban`` (``qr_iban``, ``qr-iban``) is the QR-IBAN of the organisation's
own bank account that ``location/list.json`` sends next to its ``iban``, and
``order/document/read.json`` sends ``orgIban``, ``orgQrIban`` and ``recipientIban``
(all only seen ``null``; queue row 243): fixtures never carry their values either.
"""
_TOKEN_FIELD = re.compile(
    r'(?P<field>"(?:' + TOKEN_FIELD_NAME.pattern + r')"\s*:\s*)"(?:[^"\\]|\\.)*"',
    re.IGNORECASE,
)
"""A token-like field with a text value in raw JSON: ``"hash": "..."``."""
_SETTLED_TOKEN_FIELD = re.compile(
    r'"(?i:' + TOKEN_FIELD_NAME.pattern + r')"\s*:\s*(?:null|"' + REDACTED + r'")'
)
"""A token-like field whose value is ``null`` or ``"REDACTED"``: no mention to review.

The final check refuses every other value under such a name, so a settled one needs no
review; a compound name (``publicHash``) is not settled and goes to review.
"""

SCRUBBED_API_USER = "API:REDACTED"
_NOT_SCRUBBED = r"(?!REDACTED(?![A-Za-z0-9]))"
API_USER = re.compile(
    r"(?:(?<=\\[nrtbf])|(?<![\w.\\-]))API:" + _NOT_SCRUBBED + r"[A-Za-z0-9]+", re.IGNORECASE
)
"""CashCtrl's tag for an API user in ``createdBy``/``lastUpdatedBy``: ``API:`` and key[:4].

Observed on 2026-10-23: the records an API user wrote carry ``"createdBy": "API:<the first
four characters of its key>"``. The scrub is narrow, as the e-mail scrub is: the marker in
any case, at the start of a word or right after a JSON escape (``\\n``), never inside a
JSON escape. What it cannot reach, ``API_USER_ANYWHERE`` finds and the check refuses.
"""
API_USER_ANYWHERE = re.compile(r"API:" + _NOT_SCRUBBED + r"[^\s\"'<>,;&\\]+", re.IGNORECASE)
"""Any API user tag but the scrubbed one, in any case and any position: the final check."""
_TAG_SEPARATOR = r"(?::|%3A|&#0*58;?|&#x0*3a;?|&colon;)\s*"
"""``:`` plain, URL-encoded or as an HTML entity, for the recorder's own key prefix."""


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """The command line: endpoint, case, query parameters and the options."""
    parser = argparse.ArgumentParser(
        prog="record_fixture.py",
        description="Record one request to the demo organisation as a test fixture.",
    )
    parser.add_argument("endpoint", help="upstream path after /api/v1/, e.g. account/read.json")
    parser.add_argument("case", help="fixture name, e.g. unknown_id")
    parser.add_argument(
        "params",
        nargs="*",
        metavar="key=value",
        help="query parameters of a GET or form fields of a POST, e.g. id=999999999",
    )
    parser.add_argument(
        "--method",
        default="GET",
        help="HTTP method: GET, or POST for one of the eleven write paths the write tools call",
    )
    parser.add_argument(
        "--wrong-key", action="store_true", help=f"send {WRONG_KEY!r} instead of the key"
    )
    # Intermixed: the key=value pairs may follow --method or --wrong-key. Plain
    # parse_args does not collect a nargs="*" positional after an option on every 3.12
    # patch level (3.12.3 refused "unrecognized arguments"; 3.12.15 accepted them).
    args = parser.parse_intermixed_args(argv)
    args.endpoint = args.endpoint.removeprefix("/").removeprefix("api/v1/")
    if not _ENDPOINT.fullmatch(args.endpoint):
        parser.error(f"endpoint {args.endpoint!r} is not an upstream path like account/read.json")
    if not _CASE.fullmatch(args.case):
        parser.error(f"case {args.case!r}: use lower-case letters, digits and underscores")
    if any("=" not in item for item in args.params):
        parser.error("parameters are key=value")
    args.params = {key: value for key, _, value in (item.partition("=") for item in args.params)}
    return args


def fixture_endpoint(endpoint: str) -> str:
    """``account/read.json`` → ``account_read``: the fixture directory of an endpoint."""
    return endpoint.rsplit(".", 1)[0].replace("/", "_")


def unmarked(method: str, endpoint: str, params: dict[str, str]) -> str | None:
    """Why a create must not be sent: none of its values carries ``MARK``; else ``None``.

    ``order/payment/create.json`` has no text to mark: the orders it pays are checked
    instead (``unmarked_orders``).
    """
    creates = (
        is_write(method) and endpoint.endswith("/create.json") and endpoint not in ORDER_WRITES
    )
    if creates and not any(MARK in value for value in params.values()):
        return (
            f"a create.json is recorded only for a record marked {MARK} (in its title, "
            "company or description): none of the pairs carries the marker"
        )
    return None


def is_write(method: str) -> bool:
    """Whether ``method`` records a write, a POST, in any case."""
    return method.upper() == "POST"


def refusal(method: str, endpoint: str) -> str | None:
    """Why the request must not be sent at all, else ``None``.

    Refused: a method other than GET and POST; a POST to anything but ``WRITE_PATHS``;
    an endpoint without ``.json``.
    """
    if method.upper() not in ("GET", "POST"):
        return (
            f"only GET, and POST for the write tools' operations, is recorded, not {method.upper()}"
        )
    if is_write(method) and endpoint not in WRITE_PATHS:
        return (
            f"a POST is recorded only for one of the eleven write paths the write tools "
            f"call ({', '.join(sorted(WRITE_PATHS))}), not {endpoint}"
        )
    if not endpoint.endswith(".json"):
        return (
            f"only .json endpoints are recorded, not {endpoint}: one without the extension "
            "answers a bare number or a document, and an export is a file"
        )
    return None


async def exchange_async(
    client: AsyncClient, method: str, path: str, params: dict[str, str]
) -> httpx.Response:
    """One request through the real client; an error status is returned, not raised.

    A GET sends ``params`` as the query; a POST sends them as the form body, as the
    write tools send theirs (``api/_form.py``), and no query.
    """
    if is_write(method):
        return await client.request(
            "POST",
            path,
            data=params,
            headers={"Content-Type": FORM_CONTENT_TYPE},
            raise_on_error=False,
        )
    return await client.request(method, path, params=params, raise_on_error=False)


exchange = sync(exchange_async)


def order_ids(text: str) -> list[int] | None:
    """``"20,21"`` → ``[20, 21]``; ``None`` unless every part is a whole number of at least 1."""
    parts = text.split(",")
    if not all(part.strip().isascii() and part.strip().isdigit() for part in parts):
        return None
    ids = [int(part) for part in parts]
    return ids if all(order_id >= 1 for order_id in ids) else None


def marked_order(order: object) -> bool:
    """Whether a read order is marked as the live tests mark theirs (``marked`` there).

    ``MARK`` in its ``description``, or ``MARK`` as its ``nr``.
    """
    if not isinstance(order, dict):
        return False
    description = order.get("description")
    return (isinstance(description, str) and MARK in description) or order.get("nr") == MARK


async def unmarked_orders_async(
    client: AsyncClient, method: str, endpoint: str, params: dict[str, str]
) -> str | None:
    """Why an order write must not be sent: an order it names is not marked; else ``None``.

    For ``ORDER_WRITES`` only: every id of its ids field is read with ``order/read.json``,
    one GET each, through ``client``, and the write is refused unless each answer is
    HTTP 200 with ``"success": true`` and the order marked (``marked_order``). Fails
    closed: no ids, an id that is not a whole number, an order that cannot be read or
    answers for another id refuses it. The answers are read for the marker and never
    printed or kept.
    """
    field = ORDER_WRITES.get(endpoint) if is_write(method) else None
    if field is None:
        return None
    ids = order_ids(params.get(field, ""))
    if ids is None:
        return (
            f"{endpoint} is recorded only for orders marked {MARK}: {field} must name the "
            "orders, comma-separated ids such as 20,21"
        )
    for order_id in ids:
        response = await client.request(
            "GET", "/order/read.json", params={"id": str(order_id)}, raise_on_error=False
        )
        try:
            answer = response.json()
        except ValueError:
            answer = None
        order = answer.get("data") if isinstance(answer, dict) else None
        readable = (
            response.status_code == 200
            and isinstance(answer, dict)
            and answer.get("success") is True
            and isinstance(order, dict)
            and order.get("id") == order_id
        )
        if not readable:
            return (
                f"{endpoint} is recorded only for orders marked {MARK}: order {order_id} "
                f"could not be read (HTTP {response.status_code}), so its marker is unknown"
            )
        if not marked_order(order):
            return (
                f"{endpoint} is recorded only for orders marked {MARK}: order {order_id} "
                f"carries no marker (its description holds no {MARK}, its nr is not {MARK})"
            )
    return None


unmarked_orders = sync(unmarked_orders_async)


def _placeholder(match: re.Match[str]) -> str:
    return SCRUBBED_EMAIL.replace("@", "%40") if match["at"] == "%40" else SCRUBBED_EMAIL


def scrub_emails(text: str) -> str:
    """``text`` with every e-mail address made the placeholder."""
    return _EMAIL_IN_TEXT.sub(_placeholder, text)


def _decoded(body: str) -> tuple[bool, Any]:
    """``(True, value)`` for a JSON body, ``(False, None)`` for any other."""
    try:
        return True, json.loads(body)
    except ValueError:
        return False, None


_CUT_MARKS = ("truncated", "original_bytes", "original_count", "sha256")
"""The response fields that mark a cut body; core's writer leaves them out of one not cut."""


def to_json(fixture: Fixture) -> str:
    """The fixture as text, laid out as core's ``write_fixture`` lays it out.

    The recorder never cuts a body (no ``max_bytes=``), so the cut markers are left out,
    as core leaves them out of a fixture that was not cut.
    """
    data = fixture.model_dump(mode="json")
    if not fixture.response.truncated:
        for name in _CUT_MARKS:
            data["response"].pop(name, None)
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _key_like_values(node: Any, where: str) -> Iterator[str]:
    """Locations whose name looks like a credential and whose value is not REDACTED."""
    if isinstance(node, dict):
        for name, value in node.items():
            if KEY_LIKE.search(str(name)) and value != REDACTED:
                yield f"{where}.{name}"
            yield from _key_like_values(value, f"{where}.{name}")
    elif isinstance(node, list):
        if len(node) == 2 and all(isinstance(item, str) for item in node):
            name, value = node
            if KEY_LIKE.search(name) and value != REDACTED:
                yield f"{where} header {name!r}"
        for index, item in enumerate(node):
            yield from _key_like_values(item, f"{where}[{index}]")


def _body_mentions(body: str) -> list[str]:
    return sorted({match.group(0).lower() for match in KEY_LIKE.finditer(body)})


def _strings(node: Any) -> Iterator[str]:
    """Every key and string value of a decoded JSON document."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for name, value in node.items():
            yield str(name)
            yield from _strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _strings(item)


def _request_body(fixture: dict[str, Any]) -> str:
    body = fixture.get("request", {}).get("body")
    return body if isinstance(body, str) else ""


def _form(body: str) -> list[tuple[str, str]]:
    """The fields of a form body, names and values decoded; none for any other body."""
    try:
        return parse_qsl(body, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return []


def _request_body_strings(fixture: dict[str, Any]) -> list[str]:
    """A write's request body decoded; nothing for a GET.

    Every form field name and value, and every string of a value that is JSON
    (``items``, ``addresses``).
    """
    texts: list[str] = []
    for name, value in _form(_request_body(fixture)):
        texts += [name, value]
        is_json, decoded = _decoded(value)
        if is_json:
            texts += list(_strings(decoded))
    return texts


def _holds_an_address(fixture: dict[str, Any]) -> bool:
    """An e-mail address other than the placeholder in the URL, the bodies or a header.

    The raw texts are searched as they are scrubbed; the decoded strings of a JSON body
    and of a form body with the plain pattern, so an address the scrub could not reach
    is still found.
    """
    request, response = fixture.get("request", {}), fixture.get("response", {})
    body = response.get("body", "")
    raw = [request.get("url", ""), _request_body(fixture), body]
    raw += [part for header in response.get("headers", []) for part in header]
    found = [match.group(0) for text in raw for match in _EMAIL_IN_TEXT.finditer(text)]
    is_json, decoded = _decoded(body)
    decoded_texts = [*(_strings(decoded) if is_json else []), *_request_body_strings(fixture)]
    found += [match.group(0) for text in decoded_texts for match in EMAIL.finditer(text)]
    return any(address not in _SCRUBBED_EMAILS for address in found)


def scrub_api_users(text: str) -> str:
    """``text`` with every API user tag made ``API:REDACTED``."""
    return API_USER.sub(SCRUBBED_API_USER, text)


def _searched_texts(text: str, fixture: dict[str, Any]) -> list[str]:
    """The serialised fixture and every decoded string the check searches as well.

    Every key and string of a JSON response body, and a write's request body decoded
    (``_request_body_strings``).
    """
    is_json, decoded = _decoded(fixture.get("response", {}).get("body", ""))
    return [text, *(_strings(decoded) if is_json else []), *_request_body_strings(fixture)]


def _holds_an_api_user_tag(texts: Sequence[str], key: str) -> bool:
    """An API user tag other than ``API:REDACTED``, or the key's own tag, in any of ``texts``.

    Any tag in any case and position; the key's own prefix also after ``API`` with ``:``
    URL-encoded or as an HTML entity, or after a space, which the general pattern misses.
    """
    own = (
        re.compile(rf"API{_TAG_SEPARATOR}{re.escape(key[:4])}(?![A-Za-z0-9])", re.IGNORECASE)
        if len(key) >= 4
        else None
    )
    return any(
        API_USER_ANYWHERE.search(text) or (own is not None and own.search(text)) for text in texts
    )


def _holds_the_bare_prefix(texts: Sequence[str], key: str) -> bool:
    """The key's first four characters anywhere, without the marker: a possible prefix."""
    return len(key) >= 4 and any(key[:4] in text for text in texts)


def scrub_token_fields(text: str) -> str:
    """``text`` with the text value of every token-like JSON field made ``REDACTED``.

    Only the value changes, in the raw text, so the body stays the JSON upstream sent.
    A ``null`` or a number under such a name is left as it is.
    """
    return _TOKEN_FIELD.sub(lambda m: f'{m["field"]}"{REDACTED}"', text)


def scrub_text(text: str) -> str:
    """The recorder's own scrub: e-mail addresses, API user tags, token-like fields, identifiers.

    ``TenantScrub``'s ``text_rewrite``: applied after the host and the key to the request
    URL, every response header value and both bodies.
    """
    return scrub_token_fields(scrub_api_users(scrub_emails(text)))


def secrets_of(key: str) -> list[str]:
    """The key and its basic-auth token, the values never written; none without a key."""
    if not key:
        return []
    token = base64.b64encode(f"{key}:".encode()).decode("ascii")
    return [key, token]


def scrub(key: str) -> Scrub:
    """What core removes besides credentials: the key and its basic-auth token, as given.

    Args:
        key: The demo key, ``""`` when none is set; with its basic-auth token, it becomes
            ``REDACTED`` wherever it appears as given, and core refuses the exchange if it
            survives as given. Every other form is the recorder's step (``TenantScrub``).
    """
    return Scrub(secrets=secrets_of(key), allow_binary=False)


_HOST_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?")
SUBDOMAIN_VAR = TENANTS.var(DEMO, "SUBDOMAIN")
KEY_VAR = TENANTS.var(DEMO, "API_KEY")


def _percent_encoded(char: str) -> str:
    """A pattern for ``char`` percent-encoded, its UTF-8 bytes in either hex case."""
    return "".join(
        "%" + "".join(f"[{c}{c.lower()}]" if c.isalpha() else c for c in f"{byte:02X}")
        for byte in char.encode("utf-8")
    )


def _plain_or_encoded(value: str, *, any_case: bool = False) -> str:
    r"""A pattern for ``value`` with each character plain or percent-encoded.

    Covers any mix: what a URL encoder leaves alone and what it encodes, in either hex
    case, ``+`` for a space as in a form body or a query, and ``\/`` for ``/`` as some
    JSON encoders write it. Copied from core's ``Scrub`` (ADR-0024). With ``any_case``
    a letter's encoding is taken in either letter case as well (``%52`` and ``%72`` for
    ``r``), for a pattern compiled with ``re.IGNORECASE``: the host and the subdomain.
    """
    parts = []
    for char in value:
        cases = {char.lower(), char.upper()} if any_case else {char}
        encoded = "|".join(_percent_encoded(case) for case in sorted(cases))
        options = [re.escape(char), encoded]
        if char == " ":
            options.append(r"\+")
        elif char == "/":
            options.append(r"\\/")
        parts.append("(?:" + "|".join(options) + ")")
    return "".join(parts)


def _json_strings(body: str) -> Iterator[str]:
    """Every key and string of ``body`` decoded as JSON; nothing when it is not JSON."""
    is_json, decoded = _decoded(body)
    return _strings(decoded) if is_json else iter(())


class TenantScrub:
    r"""The recorder's own step on the ``Fixture`` core returns, before the one write.

    Core's ``Scrub`` held it as ``host=``, ``rewrite=``, the percent-encoded matching and
    the JSON-decoded verify until 0.3.0 left them to this recorder (ADR-0024, decisions 3
    and 4; copied from sdk-core ``cb8ecdf``, ``src/xippios/core/testing/scrub.py``).
    Bound to the request it scrubs, it rewrites the fixture (``rewrite``) and refuses
    what survives (``verify``):

    - the request's host, in any letter case, in its IDNA form too where that differs,
      plain or percent-encoded, becomes ``host``, and the URL's host is set to it;
    - each of ``secrets``, plain or percent-encoded (either hex case, ``+`` for a space,
      ``\/`` for ``/``), the longest first, in the letter case given, becomes ``REDACTED``;
    - then ``text_rewrite`` (the recorder's ``scrub_text``) runs over the URL, every
      response header value and both bodies.

    Header names and the request's content type get the host and the secrets, not the
    rewrite. A body stored base64 is left alone: core refuses one first, since the
    recorder never sets ``allow_binary``.

    Args:
        url: The request's URL as sent, whose host is the demo organisation's.
        subdomain: The demo organisation's subdomain, searched for on its own by the verify.
        secrets: The values never written, e.g. ``secrets_of(key)``.
        host: The placeholder host, ``demo.cashctrl.com``.
        text_rewrite: The text hook applied after the host and the secrets.

    Raises:
        ValueError: ``host`` is no plain host name, a secret is empty, ``host`` contains a
            secret in any letter case, or ``host`` is the request's own host; the
            message names neither the host nor a value.
    """

    def __init__(
        self,
        url: httpx.URL,
        *,
        subdomain: str,
        secrets: Sequence[str],
        host: str = REPLAY_HOST,
        text_rewrite: Callable[[str], str] | None = None,
    ) -> None:
        if not _HOST_NAME.fullmatch(host):
            raise ValueError(
                "the replay host must be a plain host name such as 'demo.example.test'"
            )
        if any(not value for value in secrets):
            raise ValueError("the secrets must not contain an empty string")
        if any(value.lower() in host.lower() for value in secrets):
            raise ValueError(
                "the replay host contains one of the secrets, and would write it into every "
                "recorded URL"
            )
        forms = {form for form in (url.host, url.raw_host.decode("ascii")) if form}
        if host.lower() in {form.lower() for form in forms}:
            raise ValueError(
                "the replay host is the request's own host, which would be written as it is"
            )
        self._placeholder = host
        longest_first = sorted(forms, key=len, reverse=True)
        self._host = re.compile(
            "|".join(_plain_or_encoded(form, any_case=True) for form in longest_first),
            re.IGNORECASE,
        )
        self._subdomain = (
            re.compile(_plain_or_encoded(subdomain, any_case=True), re.IGNORECASE)
            if subdomain
            else None
        )
        self._secrets = [
            re.compile(_plain_or_encoded(value)) for value in sorted(secrets, key=len, reverse=True)
        ]
        self._rewrite = text_rewrite

    def text(self, text: str) -> str:
        """``text`` with the request's host made the placeholder, then the secrets redacted.

        A ``REDACTED`` core already wrote is kept as it is: a secret found inside it (a
        short one, such as ``ACT``) is not redacted again.
        """
        placeholder = self._placeholder
        parts = self._host.sub(lambda _: placeholder, text).split(REDACTED)
        for pattern in self._secrets:
            parts = [pattern.sub(lambda _: REDACTED, part) for part in parts]
        return REDACTED.join(parts)

    def rewritten(self, text: str) -> str:
        """``text`` scrubbed, then passed through ``text_rewrite``."""
        text = self.text(text)
        return self._rewrite(text) if self._rewrite is not None else text

    def url(self, url: str) -> str:
        """The URL scrubbed in one pass, its host set to the placeholder, then rewritten.

        The host is set after the pass, so a placeholder that contains the original host
        is not replaced again.
        """
        scrubbed = str(httpx.URL(self.text(url)).copy_with(host=self._placeholder))
        return self._rewrite(scrubbed) if self._rewrite is not None else scrubbed

    def headers(self, items: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
        """Header names scrubbed, header values scrubbed and rewritten."""
        return [(self.text(name), self.rewritten(value)) for name, value in items]

    def rewrite(self, fixture: Fixture) -> Fixture:
        """``fixture`` with the host, the secrets and ``text_rewrite`` applied; not verified."""
        sent = fixture.request
        body = sent.body
        request = sent.model_copy(
            update={
                "url": self.url(sent.url),
                "body": body if body is None or sent.body_base64 else self.rewritten(body),
                "content_type": None if sent.content_type is None else self.text(sent.content_type),
            }
        )
        answer = fixture.response
        response = answer.model_copy(
            update={
                "headers": self.headers(answer.headers),
                "body": answer.body if answer.body_base64 else self.rewritten(answer.body),
            }
        )
        return fixture.model_copy(update={"request": request, "response": response})

    def apply(self, fixture: Fixture) -> Fixture:
        """``rewrite``, then ``verify``: the fixture as the recorder writes it."""
        rewritten = self.rewrite(fixture)
        self.verify(rewritten)
        return rewritten

    def verify(self, fixture: Fixture) -> None:
        r"""Refuse a rewritten fixture that still holds the demo host, the subdomain or a secret.

        The URL, the content type, every response header name and value and both bodies
        are searched raw with the step's patterns (the host and the subdomain in any letter
        case, each value plain or percent-encoded); a body that is JSON is searched decoded
        as well, every key and string in it, so a value behind a ``\uXXXX`` escape is found.
        The placeholder host and ``REDACTED`` are masked first and never count.

        Raises:
            ValueError: Naming what survived (the demo host, the variable whose value it
                is) and where (``request URL``, a header by name, ``request body``,
                ``response body``), never the value.
        """
        __tracebackhide__ = True  # pytest would print the arguments: the refused text
        request, response = fixture.request, fixture.response
        places: list[tuple[str, list[str]]] = [("request URL", [request.url])]
        if request.content_type is not None:
            places.append(("request header 'content-type'", [request.content_type]))
        for name, value in response.headers:
            places.append(("name of a response header", [name]))
            places.append((f"response header {name!r}", [value]))
        for location, body, base64_body in (
            ("request body", request.body, request.body_base64),
            ("response body", response.body, response.body_base64),
        ):
            if body is not None and not base64_body:
                places.append((location, [body, *_json_strings(body)]))
        for location, texts in places:
            kind = self._left_in(texts)
            if kind is not None:
                raise ValueError(
                    f"the scrubbed fixture still holds {kind} in the {location}; nothing is written"
                )

    def _left_in(self, texts: Iterable[str]) -> str | None:
        """What survives in ``texts``, by name, or ``None``."""
        __tracebackhide__ = True
        for text in texts:
            masked = text.replace(REDACTED, "\0")
            masked = re.sub(re.escape(self._placeholder), "\0", masked, flags=re.IGNORECASE)
            if self._host.search(masked):
                return "the demo organisation's host"
            if self._subdomain is not None and self._subdomain.search(masked):
                return f"the value of {SUBDOMAIN_VAR}"
            if any(pattern.search(masked) for pattern in self._secrets):
                return f"the value of {KEY_VAR} or its basic-auth token"
        return None


def scrubbed(response: httpx.Response, key: str, subdomain: str) -> Fixture:
    """The exchange as the recorder writes it: core's scrub, then ``TenantScrub``.

    Raises:
        ValueError: Core refused it (a body that is not UTF-8 text, the key or its token
            left as given) or the recorder's step did; the message names what and where,
            never a value.
    """
    fixture = fixture_from_response(response, scrub=scrub(key))
    step = TenantScrub(
        response.request.url, subdomain=subdomain, secrets=secrets_of(key), text_rewrite=scrub_text
    )
    return step.apply(fixture)


def redacted_a_secret(response: httpx.Response, written: Fixture, key: str, subdomain: str) -> bool:
    """Whether the key or its basic-auth token was redacted in the response.

    The response is scrubbed once more without the secrets, through the same step, and
    compared, so the scrub's own patterns decide (plain or percent-encoded); only the
    answer leaves this function.
    """
    if not key:
        return False
    plain = TenantScrub(
        response.request.url, subdomain=subdomain, secrets=(), text_rewrite=scrub_text
    ).rewrite(fixture_from_response(response, scrub=Scrub()))
    return plain.response != written.response


def _is_text(content: bytes) -> bool:
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _unsettled_token_fields(node: Any) -> Iterator[str]:
    """Names of token-like fields, at any depth, whose value is not ``null`` or ``REDACTED``.

    Any other value is refused, whatever its type or shape: text the scrub could not
    reach (an escaped field name), a number, an array, an object.
    """
    if isinstance(node, dict):
        for name, value in node.items():
            if TOKEN_FIELD_NAME.fullmatch(str(name)) and value is not None and value != REDACTED:
                yield str(name)
            yield from _unsettled_token_fields(value)
    elif isinstance(node, list):
        for item in node:
            yield from _unsettled_token_fields(item)


def check(text: str, subdomain: str, key: str) -> tuple[list[str], list[str]]:
    """``(leaks, suspicions)`` in a serialised fixture; neither ever contains a value.

    What the scrub verifies (the demo host, the key and its basic-auth token) is not
    checked again; ``key`` serves the API user tag and the key prefix.
    """
    leaks: list[str] = []
    if subdomain != DEMO and subdomain in text.lower():
        leaks.append(f"the value of {TENANTS.var(DEMO, 'SUBDOMAIN')}")
    fixture = json.loads(text)
    texts = _searched_texts(text, fixture)
    if _holds_an_api_user_tag(texts, key):
        leaks.append(f"an API user tag other than {SCRUBBED_API_USER}")
    if _holds_the_bare_prefix(texts, key):
        leaks.append(
            f"a possible key prefix: the first four characters of {TENANTS.var(DEMO, 'API_KEY')}, "
            "without the API: marker (four characters alone may be a coincidence; "
            "find them in the response before recording again)"
        )
    is_json, decoded = _decoded(fixture.get("response", {}).get("body", ""))
    tokens = set(_unsettled_token_fields(decoded)) if is_json else set()
    for name, value in _form(_request_body(fixture)):
        if TOKEN_FIELD_NAME.fullmatch(name) and value != REDACTED:
            tokens.add(name)
        is_json_value, decoded_value = _decoded(value)  # bankAccounts, items, addresses
        if is_json_value:
            tokens.update(_unsettled_token_fields(decoded_value))
    if tokens:
        leaks.append(f"a value other than null or {REDACTED} under {', '.join(sorted(tokens))}")
    if _holds_an_address(fixture):
        leaks.append(f"an e-mail address other than {SCRUBBED_EMAIL}")
    suspicions = list(_key_like_values(fixture, "fixture"))
    url = fixture.get("request", {}).get("url", "")
    suspicions += [f"request URL mentions {word!r}" for word in _body_mentions(url)]
    sent = _request_body(fixture)
    suspicions += [f"request body mentions {word!r}" for word in _body_mentions(sent)]
    body = fixture.get("response", {}).get("body", "")
    unsettled = _SETTLED_TOKEN_FIELD.sub("", body)
    suspicions += [f"response body mentions {word!r}" for word in _body_mentions(unsettled)]
    return leaks, suspicions


def changed_reminder(endpoint: str, response: httpx.Response) -> str:
    """The note after a recorded write: the organisation changed, and the delete is due.

    Names the ``insertId`` when the answer carries one (an integer: the new record's id
    for a create, the record's own for an update, observed on 2026-10-24), and nothing
    else of the answer.
    """
    try:
        answer = response.json()
    except ValueError:
        answer = None
    insert_id = answer.get("insertId") if isinstance(answer, dict) else None
    created = (
        f" upstream answered insertId {insert_id};"
        if isinstance(insert_id, int) and not isinstance(insert_id, bool)
        else ""
    )
    if endpoint in ORDER_WRITES:
        due = "order/delete.json for the marked orders it named"
        if endpoint == "order/payment/create.json":
            due += " (upstream documents no delete of a payment, which stays behind)"
    else:
        due = "the matching delete.json"
    return (
        f"the demo organisation changed: POST {endpoint} was sent;{created} record or run "
        f"{due} so that no record created for a fixture stays behind"
    )


def recording_client(*, wrong_key: bool = False) -> AsyncClient:
    """The client the recorder sends through: the demo organisation's, never retrying.

    ``client_for("demo")``'s configuration (base URL, pace, ``classify``) with
    ``RetryPolicy(max_attempts=1)``, so a 5xx or a timeout is recorded as it came and
    spends no further request on a retry (queue row 138 item 3); core's ``record`` takes
    no ``retry=``, so the client carries it. The key is read from
    ``CASHCTRL_DEMO_API_KEY`` on the request, as the package's own client reads it, or is
    ``WRONG_KEY`` with ``wrong_key``.
    """
    config = dataclasses.replace(client_for(DEMO).config, retry=RetryPolicy(max_attempts=1))
    key_var = TENANTS.var(DEMO, "API_KEY")
    auth = BasicKeyAuth(key_var, key=WRONG_KEY if wrong_key else None, source=SOURCE)
    return AsyncClient(config, auth=auth)


def main(argv: Sequence[str] | None = None) -> int:
    """Refuse or record, scrub in memory, check, write; return the exit status."""
    args = parse_args(argv)
    refused = refusal(args.method, args.endpoint) or unmarked(
        args.method, args.endpoint, args.params
    )
    if refused:
        print(f"not recorded: {refused}")  # noqa: T201
        return 1
    os.environ.pop(TENANTS.list_var, None)  # the recorder sees the demo organisation only
    client = recording_client(wrong_key=args.wrong_key)
    refused = unmarked_orders(client, args.method, args.endpoint, args.params)
    if refused:
        print(f"not recorded: {refused}")  # noqa: T201
        return 1
    key_var = TENANTS.var(DEMO, "API_KEY")
    path = fixture_path(FIXTURES, fixture_endpoint(args.endpoint), args.case)
    key = os.environ.get(key_var, "")
    subdomain = TENANTS.field(DEMO, "SUBDOMAIN")
    method = "POST" if is_write(args.method) else "GET"
    response = exchange(client, method, f"/{args.endpoint}", args.params)
    if method == "POST":
        print(changed_reminder(args.endpoint, response))  # noqa: T201
    try:
        fixture = scrubbed(response, key, subdomain)
    except ValueError as refused_by_scrub:  # names what and where, never a value
        reason = str(refused_by_scrub)
        if not _is_text(response.content):  # the recorder's reason before core's
            reason = f"exports are out of scope for fixtures; {reason}"
        print(f"not written {path.relative_to(ROOT)}: {reason}")  # noqa: T201
        return 1
    text = to_json(fixture)

    leaks, suspicions = check(text, subdomain, key)
    if redacted_a_secret(response, fixture, key, subdomain):
        suspicions.append(
            f"the response carried the value of {key_var} or its basic-auth token, "
            "redacted by the scrub: find out why upstream sent it back"
        )
    if leaks:
        print(f"not written {path.relative_to(ROOT)}: it would contain " + "; ".join(leaks))  # noqa: T201
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(fixture.response.status, fixture.request.url)  # noqa: T201
    if suspicions:
        print(f"review {path.relative_to(ROOT)} before committing:")  # noqa: T201
        for item in suspicions:
            print(f"  {item}")  # noqa: T201
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
