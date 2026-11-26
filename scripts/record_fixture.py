r"""Record one exchange with the demo organisation into a fixture (``/record-fixture``).

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
environment and always records through ``client_for("demo")``, the demo organisation's own
client, so it cannot reach a productive organisation, and sends its one request with core's
``send_once``, which never retries and never answers from the cache, whatever the client's
``RetryPolicy`` says (sdk-core ADR-0066, decision 3): a 5xx is recorded as it came and
spends no request on a retry. ``--wrong-key`` sends ``not-a-valid-key`` instead of the
real key, as that one request's ``auth=``, to record a 401 without touching the real key.

The demo organisation holds synthetic books only, seeded by ``scripts/seed_demo.py`` and
described in ``docs/demo-org.md``: invented companies on placeholder streets,
``.example`` addresses, invented amounts. So every module and every amount may be
recorded. These policies stand all the same; every refusal writes nothing, says why,
never shows a value, and exits with status 1:

- GET for what the snapshot documents as a GET, and POST for the fourteen write paths
  only. A GET is sent only to a path whose Endpoint block in ``docs/upstream/``
  (``UPSTREAM``) reads ``GET`` and nothing else (``documented_methods``): a path the
  snapshot documents as a POST (``account/create.json``, ``fiscalperiod/switch.json``)
  or does not document at all is refused before a request is sent, since whether
  upstream acts on a GET to a POST path is unverified
  (https://github.com/xippios/sdk-cashctrl/issues/27); a refreshed snapshot moves the
  refusal with it. ``--method POST`` is allowed for exactly the operations this
  package's write tools call (``WRITE_PATHS``): ``journal/create.json``,
  ``journal/update.json``, ``journal/delete.json``, ``person/create.json``,
  ``person/update.json``, ``person/delete.json``, ``order/create.json``,
  ``order/update.json``, ``order/delete.json``, ``order/update_status.json``,
  ``order/payment/create.json``, ``order/bookentry/create.json``,
  ``order/bookentry/update.json`` and ``order/bookentry/delete.json``. It sends the
  ``key=value`` pairs as a form body, as the write tools do (``api/_form.py``:
  ``application/x-www-form-urlencoded; charset=UTF-8``). Every other POST
  (``order/continue.json``, ``account/create.json``, a POST to a list) and every other
  method is refused before a request is sent, and so are a GET to one of the write
  paths (a write is recorded as a POST or not at all) and a ``create.json`` whose pairs
  do not carry the marker ``xippios-live`` (``MARK``) in a value, the order writes
  excepted, whose orders are the marker: a write records a marked record, a change to
  it or its delete, and nothing else.
  ``order/update_status.json``, ``order/payment/create.json`` and
  ``order/bookentry/create.json`` change orders (``ORDER_WRITES``): a payment carries no
  text to mark, and a book entry carries its order's marker
  (https://github.com/xippios/sdk-cashctrl/issues/44). The recorder reads every order
  their ``ids`` or ``orderIds`` name (``order/read.json``, one GET each, through the
  demo organisation's own client) and refuses the write, before it is sent, unless each order is
  marked as the live tests mark theirs, ``MARK`` in its ``description`` or ``MARK`` as
  its ``nr``; an order that cannot be read refuses it too (``unmarked_orders``).
  ``order/bookentry/update.json`` and ``order/bookentry/delete.json`` name book entries
  (``BOOK_ENTRY_WRITES``): each entry is read (``order/bookentry/read.json``), its
  ``orderId`` taken, and that order read and checked the same way, two GETs per entry,
  since the entry's read names its order but not the order's marker
  (``docs/upstream/OBSERVED.md``); an entry that cannot be read or names no order refuses
  the write too. A
  recorded write changes the demo organisation: the recorder says so after the request
  and asks for the matching delete, recorded or run, so that no created record stays
  behind: after a book entry, the entry's delete before its orders'; upstream documents
  no delete of a payment, so after one it asks for the orders' delete, which leaves the
  payment behind.
- ``.json`` only, and five file paths for their refusals. An endpoint without the
  extension answers a bare number or a document (``account/balance``,
  ``account/costcenter/balance``, ``fiscalperiod/result``, ``setting/get``) and an export
  (``.pdf``, ``.xlsx``, ``.csv``, ``.zip``) a file; both are refused before a request is
  sent. ``FILE_PATHS`` names the five file paths a GET may be recorded for, the downloads
  whose 404 for an id no record has ``_client.classify`` maps: ``order/document/read.pdf``
  and the PDF and Excel files of a report element and of a report collection, as the
  maintainer decided on 2026-11-21, so that the mapping rests on recorded answers. Their
  answer is written only when it is no file: an error of HTTP 4xx or 5xx whose body is
  text, or at HTTP 2xx CashCtrl's refusal, a JSON object with ``success`` false. Any other
  2xx and any answer whose body is binary, whatever its content type says, is refused
  after its one request and nothing is written (``kept_at_a_file_path``), so the recorder
  never keeps a file. Give such a path an id no
  record has, ``elementId=999999999``; its fixture lands in its wrapper's directory, the
  extension the last word: ``tests/fixtures/report_element_download_pdf/unknown_id.json``.
- No 1xx or 3xx, at any path. Core's ``send_once`` refuses an answer of a 1xx or a 3xx
  status, which is no final answer of its operation, after its one request: nothing is
  written, and the message names the method, the path, the status and what to record
  instead (sdk-core ADR-0066, decision 4).
- No e-mail addresses. Every e-mail-shaped string in the request URL, the request
  body, the response header values and the response body becomes ``user@example.com``,
  with ``@`` written plainly, as ``%40`` or as the HTML entities ``&#64;``, ``&#x40;``
  and ``&commat;`` (``notes`` and footers are HTML upstream); ``SYSTEM`` in
  ``createdBy`` is not an address and stays. The synthetic books use reserved
  ``.example`` addresses, but ``createdBy`` and ``lastUpdatedBy`` may carry the address
  of the user who wrote a record, a real person, so the scrub stays.
- No API user tags. CashCtrl names an API user in ``createdBy`` and ``lastUpdatedBy`` as
``API:`` and the first four characters of its key (``docs/upstream/OBSERVED.md``). Every
such tag becomes ``API:REDACTED``,
  whichever key it comes from, with the marker in any case, at the start of a word or
  right after a JSON escape. A tag the scrub cannot reach (glued to a word, or behind a
  Unicode escape) is refused by the final check.
- No token-like fields and no personal identifiers. A body field named ``hash``,
  ``token``, ``secret``, ``apiKey`` (``api_key``, ``api-key``) or ``ssn``, or whose name
  ends in ``iban`` (``iban``, ``qrIban``, ``qr_iban``, ``orgIban``, ``orgQrIban``,
  ``recipientIban``), the identifiers this package keeps out of its
  projections (sdk-core ADR-0017), in any case, has its text value replaced by ``REDACTED``.
  ``order/read.json`` sends ``hash``, an undocumented 32-character text that may be the token
  of a public link to the order document (``docs/upstream/OBSERVED.md``);
  ``person/list.json`` sends ``ssn`` and ``iban``, ``location/list.json`` ``iban`` and
  ``qrIban`` and ``order/document/read.json`` ``orgIban``, ``orgQrIban`` and
  ``recipientIban``, only ever seen ``null``; the others were never seen and are
  scrubbed should they appear. The final check refuses any value under such a name but ``null``
  or ``REDACTED``, whatever its type or shape: text behind an escaped field name, a
  number, an array, an object; in a write's form body as a field (``ssn=...``) and
  inside a JSON value (the ``iban`` of an item of ``bankAccounts``), which the raw-text
  scrub does not reach, so such a write is not recorded. A compound name
  (``publicHash``) is not scrubbed; it is written for review.

Nothing unscrubbed touches disk. The request goes through the demo organisation's own
client with core's ``send_once``, which returns the answer whatever its final status, and
core's ``fixture_from_response`` turns the exchange into a fixture in memory with
``Scrub(secrets=[key, its basic-auth token])`` (conventions §10):
credentials scrubbed, the key and its token made ``REDACTED`` plain and in their encoded
forms, a percent-encoding behind a JSON escape among them, and a verify that searches every
place decoded to the end and refuses the exchange when either is still there;
core also refuses a body that is not UTF-8 text, which no scrub can read (exports are out of
scope for fixtures, which the recorder's message says first), after the recorder has
refused any file a file path answered. Then the recorder's own
step, ``TenantScrub``, passed as ``rewrite=``, runs on the ``Fixture`` core returns (sdk-core
ADR-0042, decision 4; ADR-0066, decisions 1 and 2), and returns it with every value it
replaced, the host and what ``scrub_text`` replaced, which core's check then searches for as
given: the
demo host (``<CASHCTRL_DEMO_SUBDOMAIN>.cashctrl.com``, in any case, IDNA or
percent-encoded) becomes ``demo.cashctrl.com``, the host offline tests replay against, in
the URL, the headers and both bodies; and ``scrub_text`` runs over the URL, every response header
value and both bodies: every e-mail address becomes ``user@example.com``, every API user
tag ``API:REDACTED`` and every token-like field's value ``REDACTED``. Its verify then
searches the URL, every header name and value and both bodies, raw and, for a JSON body,
every decoded string, for the demo host and the subdomain on its own, plain or
percent-encoded, behind a JSON escape included, and refuses the fixture in its own words.
A refusal prints its reason, never a value. A response in which the key or its basic-auth
token was redacted is written, since nothing of either is left, but goes to review with
exit status 1: upstream should never send them back.

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

The write is the recorder's own, not core's ``record``: ``record`` writes as soon as the
step and core's check pass, before the recorder's final check could run.

Before committing, check again from the repository root, never echoing a value::

    grep -rniE 'api[_-]?key|token|secret|authorization|password' tests/fixtures
    grep -rhoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' tests/fixtures | sort -u
    grep -rhoiE 'API:[A-Za-z0-9]+' tests/fixtures | sort -u
    grep -rhoiE '[a-z0-9.-]+\.cashctrl\.com' tests/fixtures | sort -u
    git diff --cached -U0 | grep -E '^\+' | grep -ohiE '[a-z0-9.-]+\.cashctrl\.com' | sort -u
    grep -rhoiE '(hash|token|secret|api[_-]?key)\\?": *\\?"[^"\\]*' tests/fixtures | sort -u
    grep -rhoiE --include='*.json' '\\?"(ssn|[a-z0-9_-]*iban)\\?" *: *[^,}]*' tests/fixtures \
        | grep -cvE ': *(null|\\?"REDACTED\\?")$'
    grep -rhoiE --include='*.json' '(ssn=|iban=|iban%22%3A)[^&"]*' tests/fixtures \
        | grep -cvE '(=|%3A)(REDACTED|null|%22REDACTED%22[^&"]*)$'

The first prints nothing but ``REDACTED`` values; a match in upstream's own text (a word
such as ``SECRETARY`` in a name or a description) is no credential: read every match by
eye. The second prints ``user@example.com`` and nothing else, the third ``API:REDACTED``
at most, and the fourth the placeholder's host, ``demo.cashctrl.com``, alone. The fifth
lists the hosts that the staged change adds: the placeholder's, the documentation's
``app.cashctrl.com`` and the invented hosts of the tests pass, and one that names a real
organisation goes from the change. Neither reads a variable of an organisation or
compares against its value: the recorder's own check refuses a fixture that holds the
subdomain before it writes one. The sixth prints ``REDACTED`` values only. The last two
count, without printing them, the values of ``ssn`` and of every field whose name ends
in ``iban`` that are neither ``null`` nor ``REDACTED``, in the JSON bodies and in a
write's form body (``ssn=``, a field ending in ``iban=``, and ``iban`` inside the
percent-encoded ``bankAccounts``): both print ``0``. A real value found means the file
is deleted, never committed. A fixture stays well under 40 KB, small enough to review:
narrow the query (``limit=``, a filter, a query), since the recorder cuts no body; the
default chart of accounts is too large for one fixture.
"""

import argparse
import base64
import json
import os
import re
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

import httpx
from xippios.core import AsyncClient, KeyAuth, sync
from xippios.core.testing import (
    REDACTED,
    Fixture,
    Scrub,
    fixture_from_response,
    fixture_path,
    fixture_text,
    send_once,
    write_fixture,
)

from xippios.cashctrl._client import DEMO, SOURCE, TENANTS, client_for
from xippios.cashctrl.api._form import FORM_CONTENT_TYPE
from xippios.cashctrl.models import is_identifier_key

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
UPSTREAM = ROOT / "docs" / "upstream"
"""The snapshot of the upstream documentation, whose Endpoint blocks give each path's method."""
_ENDPOINT_BLOCK = re.compile(
    r"^#### Endpoint\n\n(?P<fence>`{3,})\n(?P<method>[A-Z]+) /api/v1/(?P<path>\S+)\n(?P=fence)$",
    re.MULTILINE,
)
"""One operation's Endpoint block as ``scripts/refresh_upstream.py`` writes it."""
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
        "order/bookentry/create.json",
        "order/bookentry/update.json",
        "order/bookentry/delete.json",
    }
)
"""The endpoints a POST may be recorded for: exactly those the write tools call."""
FILE_PATHS = frozenset(
    {
        "order/document/read.pdf",
        "report/element/download.pdf",
        "report/element/download.xlsx",
        "report/collection/download.pdf",
        "report/collection/download.xlsx",
    }
)
"""The file paths a GET may be recorded for, its answer only when it is no file.

The downloads whose 404 for an id no record has ``_client.classify`` maps to
``NotFoundError``, admitted by the maintainer's decision of 2026-11-21 so that the mapping
rests on recorded answers; only an error of HTTP 4xx or 5xx with a text body or CashCtrl's
refusal at HTTP 2xx is written (``kept_at_a_file_path``).
"""
MARK = "xippios-live"
"""The marker a recorded create must carry in one of its values (title, company, ...)."""
ORDER_WRITES = {
    "order/update_status.json": "ids",
    "order/payment/create.json": "orderIds",
    "order/bookentry/create.json": "orderIds",
}
"""The writes that change existing orders, by the field that names them, comma-separated.

A status and a payment carry no text to mark, and a book entry carries its order's
marker, so every order they name must be marked (``unmarked_orders``) before the write is
sent.
"""
BOOK_ENTRY_WRITES = {"order/bookentry/update.json": "id", "order/bookentry/delete.json": "ids"}
"""The writes that change an order's book entries, by the field that names the entries.

An update names one entry, a delete one or more, comma-separated. Each entry is read for
its order, and that order must be marked (``unmarked_orders``).
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

TOKEN_NAME = re.compile(r"hash|token|secret|api[_-]?key", re.IGNORECASE)
"""Body fields whose value may grant access, by whole name in any case."""


def secret_name(name: str) -> bool:
    """Whether a body field's value is rewritten and checked: a token-like name or an identifier.

    A token-like name whole (``TOKEN_NAME``), and a personal identifier by the package's
    one rule, ``models.is_identifier_key``: ``ssn`` whole and every name that ends in
    ``iban``, in any case (sdk-core ADR-0017). ``ssn`` and ``iban`` are the
    documented personal identifiers this package keeps out of its projections;
    ``qrIban`` (``qr_iban``, ``qr-iban``) is the QR-IBAN of the organisation's own bank
    account that ``location/list.json`` sends next to its ``iban``, and
    ``order/document/read.json`` sends ``orgIban``, ``orgQrIban`` and ``recipientIban``
    (all only seen ``null``): fixtures never carry their values either.
    """
    return bool(TOKEN_NAME.fullmatch(name)) or is_identifier_key(name)


_RAW_SECRET_NAME = TOKEN_NAME.pattern + r'|ssn|[^"\\]*iban'
"""``secret_name`` as a raw JSON field name between its quotes, for the raw-text scrub.

Every name that ends in ``iban``, a dot or a space in it included (``bank.iban``); a name
behind a JSON escape is the decoded checks' to find.
"""
_TOKEN_FIELD = re.compile(
    r'(?P<field>"(?:' + _RAW_SECRET_NAME + r')"\s*:\s*)"(?P<value>(?:[^"\\]|\\.)*)"',
    re.IGNORECASE,
)
"""A token-like field with a text value in raw JSON: ``"hash": "..."``."""
_SETTLED_TOKEN_FIELD = re.compile(
    r'"(?i:' + _RAW_SECRET_NAME + r')"\s*:\s*(?:null|"' + REDACTED + r'")'
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

As ``docs/upstream/OBSERVED.md`` notes, the records an API user wrote carry ``"createdBy":
"API:<the first
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
        help=(
            "HTTP method: GET for a path docs/upstream/ documents as a GET, or POST for one "
            "of the fourteen write paths the write tools call"
        ),
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
    """The fixture directory of an endpoint, its wrapper's name (conventions §2, §10).

    ``account/read.json`` → ``account_read``, and a file path keeps its extension as the
    last word: ``order/document/read.pdf`` → ``order_document_read_pdf``.
    """
    return endpoint.removesuffix(".json").replace("/", "_").replace(".", "_")


def unmarked(method: str, endpoint: str, params: dict[str, str]) -> str | None:
    """Why a create must not be sent: none of its values carries ``MARK``; else ``None``.

    ``order/payment/create.json`` has no text to mark, and ``order/bookentry/create.json``
    carries its order's marker: the orders they name are checked instead
    (``unmarked_orders``).
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


def documented_methods(snapshot: Path) -> dict[str, frozenset[str]]:
    """Each path the snapshot documents, with its methods: ``{"account/create.json": {"POST"}}``.

    Read from the ``#### Endpoint`` block of every operation in ``snapshot/*.md``, its one
    line ``POST /api/v1/account/create.json``; a curl example or any other line counts for
    nothing. A path the blocks name twice keeps both methods, and ``refusal`` then refuses
    its GET.
    """
    methods: dict[str, set[str]] = {}
    for page in sorted(snapshot.glob("*.md")):
        for block in _ENDPOINT_BLOCK.finditer(page.read_text(encoding="utf-8")):
            methods.setdefault(block["path"], set()).add(block["method"])
    return {path: frozenset(found) for path, found in methods.items()}


def refusal(method: str, endpoint: str) -> str | None:
    """Why the request must not be sent at all, else ``None``.

    Refused: a method other than GET and POST; a POST to anything but ``WRITE_PATHS``;
    a GET to one of ``WRITE_PATHS``; an endpoint without ``.json`` but ``FILE_PATHS``; a
    GET to any other path the snapshot does not document as a GET alone
    (``documented_methods``), since whether upstream acts on a GET to a POST path is
    unverified (https://github.com/xippios/sdk-cashctrl/issues/27).
    """
    if method.upper() not in ("GET", "POST"):
        return (
            f"only GET, and POST for the write tools' operations, is recorded, not {method.upper()}"
        )
    if not is_write(method) and endpoint in WRITE_PATHS:
        return f"{endpoint} is a write: it is recorded with --method POST or not at all"
    if is_write(method) and endpoint not in WRITE_PATHS:
        return (
            f"a POST is recorded only for one of the fourteen write paths the write tools "
            f"call ({', '.join(sorted(WRITE_PATHS))}), not {endpoint}"
        )
    if not endpoint.endswith(".json") and endpoint not in FILE_PATHS:
        return (
            f"only .json endpoints and five file paths are recorded, not {endpoint}: one "
            "without the extension answers a bare number or a document, and an export is a "
            f"file; the file paths are {', '.join(sorted(FILE_PATHS))}, for their refusals"
        )
    if not is_write(method):
        documented = documented_methods(UPSTREAM).get(endpoint, frozenset())
        only_a_get = "a GET is recorded only for a path the snapshot documents as a GET alone"
        if not documented:
            return f"{endpoint} is not in docs/upstream/: {only_a_get}"
        if documented != {"GET"}:
            return (
                f"docs/upstream/ documents {endpoint} as {' and '.join(sorted(documented))}: "
                f"{only_a_get}"
            )
    return None


async def exchange_async(
    client: AsyncClient,
    method: str,
    path: str,
    params: dict[str, str],
    auth: httpx.Auth | None = None,
) -> httpx.Response:
    """The recording's one request, sent once by core's ``send_once``; any final status returned.

    A GET sends ``params`` as the query; a POST sends them as the form body, as the
    write tools send theirs (``api/_form.py``), and no query. ``auth`` replaces the client's
    credentials for this request (``--wrong-key``); ``None`` keeps the client's.

    Raises:
        ValueError: Core refused an answer of a 1xx or a 3xx status after the request,
            naming the method, the path and the status, never a value.
    """
    sent: dict[str, Any] = (
        {"method": "POST", "data": params, "headers": {"Content-Type": FORM_CONTENT_TYPE}}
        if is_write(method)
        else {"method": method, "params": params}
    )
    if auth is not None:
        sent["auth"] = auth
    return await send_once.async_fn(client, path, **sent)


exchange = sync(exchange_async)


def kept_at_a_file_path(response: httpx.Response) -> bool:
    """Whether a file path's answer is written: a text error, or CashCtrl's refusal.

    An error of HTTP 4xx or 5xx whose body is UTF-8 text, whatever its content type says,
    or at HTTP 2xx a JSON object with ``success`` false. Never another 2xx or an answer
    whose body is binary: the file an id fetched is never recorded. Core refuses a 1xx or
    a 3xx before this is asked.
    """
    if 400 <= response.status_code < 600:
        return _is_text(response.content)
    if not response.is_success:
        return False
    try:
        answer = json.loads(response.content)
    except ValueError:
        return False
    return isinstance(answer, dict) and answer.get("success") is False


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


async def _read_record(
    client: AsyncClient, path: str, record_id: int
) -> tuple[dict[str, Any] | None, str]:
    """``(record, status)`` of one ``read.json`` by ``id``; the record ``None`` unless read.

    Read means HTTP 200 with ``"success": true`` and a ``data`` object for this id. The
    read is sent once by core's ``send_once``, as the recording is, so a 5xx spends no
    second request; the status reads ``HTTP 500``, or names a 1xx or 3xx that core refused.
    The answer is returned to be checked and is never printed or kept.
    """
    try:
        response = await send_once.async_fn(client, path, params={"id": str(record_id)})
    except ValueError:  # core's refusal of a 1xx or 3xx, which names no value either
        return None, "a 1xx or 3xx, no final answer"
    try:
        answer = response.json()
    except ValueError:
        answer = None
    record = answer.get("data") if isinstance(answer, dict) else None
    readable = (
        response.status_code == 200
        and isinstance(answer, dict)
        and answer.get("success") is True
        and isinstance(record, dict)
        and record.get("id") == record_id
    )
    return (record if readable else None), f"HTTP {response.status_code}"


async def _unmarked_order(client: AsyncClient, order_id: int, named: str) -> str | None:
    """Why the order ``order_id`` does not admit a write, ``named`` as the reason says it."""
    order, status = await _read_record(client, "/order/read.json", order_id)
    if order is None:
        return f"{named} could not be read ({status}), so its marker is unknown"
    if not marked_order(order):
        return f"{named} carries no marker (its description holds no {MARK}, its nr is not {MARK})"
    return None


async def unmarked_orders_async(
    client: AsyncClient, method: str, endpoint: str, params: dict[str, str]
) -> str | None:
    """Why an order write must not be sent: an order it acts on is not marked; else ``None``.

    For ``ORDER_WRITES``: every id of its ids field is read with ``order/read.json``,
    one GET each, sent once through ``client``. For ``BOOK_ENTRY_WRITES``: every entry its
    field names is read with ``order/bookentry/read.json``, and the order its ``orderId``
    names with ``order/read.json``, two GETs per entry. The write is refused unless each
    answer is HTTP 200 with ``"success": true`` for the id asked and each order is
    marked (``marked_order``). Fails closed: no ids, an id that is not a whole number,
    an update naming more than one entry, a record that cannot be read or answers for
    another id, and an entry whose ``orderId`` is no whole number refuse it. The answers
    are read for the marker and never printed or kept.
    """
    if not is_write(method):
        return None
    refused = f"{endpoint} is recorded only for orders marked {MARK}: "
    field = ORDER_WRITES.get(endpoint)
    if field is not None:
        ids = order_ids(params.get(field, ""))
        if ids is None:
            return f"{refused}{field} must name the orders, comma-separated ids such as 20,21"
        for order_id in ids:
            reason = await _unmarked_order(client, order_id, f"order {order_id}")
            if reason is not None:
                return refused + reason
        return None
    field = BOOK_ENTRY_WRITES.get(endpoint)
    if field is None:
        return None
    entries = order_ids(params.get(field, ""))
    if field == "id" and (entries is None or len(entries) != 1):
        return f"{refused}id must name one book entry, its id such as 31"
    if entries is None:
        return f"{refused}{field} must name the book entries, comma-separated ids such as 31,32"
    for entry_id in entries:
        entry, status = await _read_record(client, "/order/bookentry/read.json", entry_id)
        if entry is None:
            return (
                f"{refused}book entry {entry_id} could not be read ({status}), so its "
                "order is unknown"
            )
        its_order = entry.get("orderId")
        if not isinstance(its_order, int) or isinstance(its_order, bool) or its_order < 1:
            return f"{refused}book entry {entry_id} names no order"
        named = f"order {its_order} of book entry {entry_id}"
        reason = await _unmarked_order(client, its_order, named)
        if reason is not None:
            return refused + reason
    return None


unmarked_orders = sync(unmarked_orders_async)


_PLACEHOLDERS = frozenset({REDACTED, SCRUBBED_API_USER, *_SCRUBBED_EMAILS})
"""What the recorder writes in place of a value, which it never notes as a value replaced."""


def _noted(replaced: list[str] | None, value: str, replacement: str) -> str:
    """``replacement``, with ``value`` appended to ``replaced`` unless it reads as a placeholder.

    A value that already reads as a placeholder the recorder writes, the placeholder address,
    ``API:REDACTED`` or ``REDACTED``, was replaced by nothing, or by an earlier scrub that
    noted what it replaced: core would find it in every place that rightly holds it. An empty
    value cannot survive.
    """
    if replaced is not None and value and value != replacement and value not in _PLACEHOLDERS:
        replaced.append(value)
    return replacement


def _placeholder(match: re.Match[str], replaced: list[str] | None = None) -> str:
    placeholder = SCRUBBED_EMAIL.replace("@", "%40") if match["at"] == "%40" else SCRUBBED_EMAIL
    return _noted(replaced, match.group(0), placeholder)


def scrub_emails(text: str, replaced: list[str] | None = None) -> str:
    """``text`` with every e-mail address made the placeholder, each appended to ``replaced``."""
    return _EMAIL_IN_TEXT.sub(lambda match: _placeholder(match, replaced), text)


def _decoded(body: str) -> tuple[bool, Any]:
    """``(True, value)`` for a JSON body, ``(False, None)`` for any other."""
    try:
        return True, json.loads(body)
    except ValueError:
        return False, None


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


def scrub_api_users(text: str, replaced: list[str] | None = None) -> str:
    """``text`` with every API user tag made ``API:REDACTED``, each appended to ``replaced``."""
    return API_USER.sub(lambda match: _noted(replaced, match.group(0), SCRUBBED_API_USER), text)


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


def _token_value(match: re.Match[str], replaced: list[str] | None) -> str:
    """The field with ``REDACTED`` for its value; the value as it stood and decoded noted."""
    value = match["value"]
    try:
        decoded = json.loads(f'"{value}"')
    except ValueError:
        decoded = value
    for form in dict.fromkeys((value, decoded)):
        _noted(replaced, form, REDACTED)
    return f'{match["field"]}"{REDACTED}"'


def scrub_token_fields(text: str, replaced: list[str] | None = None) -> str:
    """``text`` with the text value of every token-like JSON field made ``REDACTED``.

    Only the value changes, in the raw text, so the body stays the JSON upstream sent.
    A ``null`` or a number under such a name is left as it is. Each value replaced is
    appended to ``replaced`` as it stood in the raw text and, where a JSON escape makes it
    differ, decoded as well, so that a copy of it elsewhere in either form is found.
    """
    return _TOKEN_FIELD.sub(lambda match: _token_value(match, replaced), text)


def scrub_text(text: str, replaced: list[str] | None = None) -> str:
    """The recorder's own scrub: e-mail addresses, API user tags, token-like fields, identifiers.

    ``TenantScrub``'s ``text_rewrite``: applied after the host and the key to the request
    URL, every response header value and both bodies. Each value it replaces is appended to
    ``replaced`` as it stood in ``text``, but one that already reads as its replacement, so
    that the step returns it for core's check (conventions §10).
    """
    return scrub_token_fields(
        scrub_api_users(scrub_emails(text, replaced), replaced),
        replaced,
    )


def secrets_of(key: str) -> list[str]:
    """The key and its basic-auth token, the values never written; none without a key."""
    if not key:
        return []
    token = base64.b64encode(f"{key}:".encode()).decode("ascii")
    return [key, token]


def scrub(key: str) -> Scrub:
    """What core removes besides credentials: the key and its basic-auth token.

    Args:
        key: The demo key, ``""`` when none is set; with its basic-auth token, it becomes
            ``REDACTED`` wherever it appears, plain or in its encoded forms, and core refuses
            the exchange if either survives in any of them.
    """
    return Scrub(secrets=secrets_of(key), allow_binary=False)


_HOST_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?")
SUBDOMAIN_VAR = TENANTS.var(DEMO, "SUBDOMAIN")


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
    JSON encoders write it. Copied from core's ``Scrub`` (sdk-core ADR-0042, decision 6). With
    ``any_case`` a letter's encoding is taken in either letter case as well (``%52`` and ``%72`` for
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
    the JSON-decoded verify until 0.3.0 left them to this recorder (sdk-core ADR-0042, decisions 3
    and 4; copied from sdk-core ``cb8ecdf``, ``src/xippios/core/testing/scrub.py``).
    Bound to the request it scrubs, it rewrites the fixture (``rewrite``) and refuses
    what survives (``verify``):

    - the request's host, in any letter case, in its IDNA form too where that differs,
      plain or percent-encoded, becomes ``host``, and the URL's host is set to it;
    - then ``text_rewrite`` (the recorder's ``scrub_text``) runs over the URL, every
      response header value and both bodies.

    The key and its token are core's: its ``Scrub`` replaces a secret in its every form, a
    percent-encoding behind a JSON escape among them, and its verify searches every place
    decoded to the end (``scrub``; sdk-core ADR-0066, decision 11), so this step takes no
    secrets. Header names and the request's content type get the host, not the rewrite. A
    body stored base64 is left alone: core refuses one first, since the recorder never sets
    ``allow_binary``.

    Args:
        url: The request's URL as sent, whose host is the demo organisation's.
        subdomain: The demo organisation's subdomain, searched for on its own by the verify.
        host: The placeholder host, ``demo.cashctrl.com``.
        text_rewrite: The text hook applied after the host: it takes a text and a list,
            appends to the list each value it replaces, and returns the text rewritten, as
            ``scrub_text`` does.

    Raises:
        ValueError: ``host`` is no plain host name or is the request's own host; the
            message names neither.
    """

    def __init__(
        self,
        url: httpx.URL,
        *,
        subdomain: str,
        host: str = REPLAY_HOST,
        text_rewrite: Callable[[str, list[str]], str] | None = None,
    ) -> None:
        if not _HOST_NAME.fullmatch(host):
            raise ValueError(
                "the replay host must be a plain host name such as 'demo.example.test'"
            )
        forms = {form for form in (url.host, url.raw_host.decode("ascii")) if form}
        if host.lower() in {form.lower() for form in forms}:
            raise ValueError(
                "the replay host is the request's own host, which would be written as it is"
            )
        self._placeholder = host
        self._replaced = sorted(forms)
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
        self._rewrite = text_rewrite

    def text(self, text: str) -> str:
        """``text`` with the request's host made the placeholder."""
        placeholder = self._placeholder
        return self._host.sub(lambda _: placeholder, text)

    def rewritten(self, text: str, replaced: list[str]) -> str:
        """``text`` scrubbed, then passed through ``text_rewrite``, which notes in ``replaced``."""
        text = self.text(text)
        return self._rewrite(text, replaced) if self._rewrite is not None else text

    def url(self, url: str, replaced: list[str]) -> str:
        """The URL scrubbed in one pass, its host set to the placeholder, then rewritten.

        The host is set after the pass, so a placeholder that contains the original host
        is not replaced again.
        """
        scrubbed = str(httpx.URL(self.text(url)).copy_with(host=self._placeholder))
        return self._rewrite(scrubbed, replaced) if self._rewrite is not None else scrubbed

    def headers(
        self, items: Iterable[tuple[str, str]], replaced: list[str]
    ) -> list[tuple[str, str]]:
        """Header names scrubbed, header values scrubbed and rewritten."""
        return [(self.text(name), self.rewritten(value, replaced)) for name, value in items]

    def rewrite(self, fixture: Fixture, replaced: list[str] | None = None) -> Fixture:
        """``fixture`` with the host and ``text_rewrite`` applied; not verified.

        Each value that ``text_rewrite`` replaced is appended to ``replaced`` when it is given.
        """
        noted: list[str] = [] if replaced is None else replaced
        sent = fixture.request
        body = sent.body
        request = sent.model_copy(
            update={
                "url": self.url(sent.url, noted),
                "body": body if body is None or sent.body_base64 else self.rewritten(body, noted),
                "content_type": None if sent.content_type is None else self.text(sent.content_type),
            }
        )
        answer = fixture.response
        response = answer.model_copy(
            update={
                "headers": self.headers(answer.headers, noted),
                "body": answer.body if answer.body_base64 else self.rewritten(answer.body, noted),
            }
        )
        return fixture.model_copy(update={"request": request, "response": response})

    def apply(self, fixture: Fixture) -> tuple[Fixture, list[str]]:
        """``rewrite``, then ``verify``: the fixture as the recorder writes it, as core's step.

        Passed as ``rewrite=`` of core's ``fixture_from_response`` (sdk-core ADR-0066,
        decisions 1 and 2), it returns the fixture with every value it replaced, each once:
        the request's host as given and its IDNA form where that differs, then what
        ``text_rewrite`` replaced as it stood, the e-mail addresses, the API user tags and the
        values of token-like fields. Core's check then refuses a fixture in which one of them
        still stands as given. The step's own verify by pattern refuses first what such a
        search would miss, the host in another letter case or encoded, and the subdomain on
        its own, which the step never replaces but refuses wherever it stands; the recorder's
        final check finds an address, a tag or a token-like value that the hook could not
        reach. The values are held for this one call, and no message names one.
        """
        replaced: list[str] = []
        rewritten = self.rewrite(fixture, replaced)
        self.verify(rewritten)
        return rewritten, list(dict.fromkeys([*self._replaced, *replaced]))

    def verify(self, fixture: Fixture) -> None:
        r"""Refuse a rewritten fixture that still holds the demo host or the subdomain.

        The URL, the content type, every response header name and value and both bodies
        are searched raw with the step's patterns (the host and the subdomain in any letter
        case, plain or percent-encoded); a body that is JSON is searched decoded
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
        return None


def scrubbed(response: httpx.Response, key: str, subdomain: str) -> Fixture:
    """The exchange as the recorder writes it: core's scrub, then ``TenantScrub`` as its step.

    Raises:
        ValueError: Core refused it (a body that is not UTF-8 text, the key or its token
            left as given) or the recorder's step did; the message names what and where,
            never a value.
    """
    step = TenantScrub(response.request.url, subdomain=subdomain, text_rewrite=scrub_text)
    return fixture_from_response(response, scrub=scrub(key), rewrite=step.apply)


def redacted_a_secret(response: httpx.Response, written: Fixture, key: str, subdomain: str) -> bool:
    """Whether the key or its basic-auth token was redacted in the response.

    The response is scrubbed once more without the secrets, through the same step, and
    compared, so core's scrub decides (plain or encoded); only the answer leaves this
    function.
    """
    if not key:
        return False
    plain = TenantScrub(response.request.url, subdomain=subdomain, text_rewrite=scrub_text).rewrite(
        fixture_from_response(response, scrub=Scrub())
    )
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
            if secret_name(str(name)) and value is not None and value != REDACTED:
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
        if secret_name(name) and value != REDACTED:
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
    for a create, the record's own for an update, ``docs/upstream/OBSERVED.md``), and nothing
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
        if endpoint == "order/bookentry/create.json":
            due = f"order/bookentry/delete.json for the entry it booked, then {due}"
    else:
        due = "the matching delete.json"
    return (
        f"the demo organisation changed: POST {endpoint} was sent;{created} record or run "
        f"{due} so that no record created for a fixture stays behind"
    )


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
    client = client_for(DEMO)
    refused = unmarked_orders(client, args.method, args.endpoint, args.params)
    if refused:
        print(f"not recorded: {refused}")  # noqa: T201
        return 1
    key_var = TENANTS.var(DEMO, "API_KEY")
    path = fixture_path(FIXTURES, fixture_endpoint(args.endpoint), args.case)
    key = os.environ.get(key_var, "")
    subdomain = TENANTS.field(DEMO, "SUBDOMAIN")
    method = "POST" if is_write(args.method) else "GET"
    wrong = KeyAuth(key_var, location="basic", key=WRONG_KEY, source=SOURCE)
    auth = wrong if args.wrong_key else None
    try:
        response = exchange(client, method, f"/{args.endpoint}", args.params, auth)
    except ValueError as no_final_answer:  # core's refusal of a 1xx or 3xx, never a value
        print(f"not written {path.relative_to(ROOT)}: {no_final_answer}")  # noqa: T201
        return 1
    if method == "POST":
        print(changed_reminder(args.endpoint, response))  # noqa: T201
    if args.endpoint in FILE_PATHS and not kept_at_a_file_path(response):
        content_type = response.headers.get("content-type") or "no content type"
        print(  # noqa: T201
            f"not written {path.relative_to(ROOT)}: {args.endpoint} answered HTTP "
            f"{response.status_code} ({content_type}), which a file path does not record: "
            "only an error of HTTP 4xx or 5xx with a text body, or CashCtrl's refusal at "
            "HTTP 2xx, success false, never a file"
        )
        return 1
    try:
        fixture = scrubbed(response, key, subdomain)
    except ValueError as refused_by_scrub:  # names what and where, never a value
        reason = str(refused_by_scrub)
        if not _is_text(response.content):  # the recorder's reason before core's
            reason = f"exports are out of scope for fixtures; {reason}"
        print(f"not written {path.relative_to(ROOT)}: {reason}")  # noqa: T201
        return 1
    text = fixture_text(fixture)

    leaks, suspicions = check(text, subdomain, key)
    if redacted_a_secret(response, fixture, key, subdomain):
        suspicions.append(
            f"the response carried the value of {key_var} or its basic-auth token, "
            "redacted by the scrub: find out why upstream sent it back"
        )
    if leaks:
        print(f"not written {path.relative_to(ROOT)}: it would contain " + "; ".join(leaks))  # noqa: T201
        return 1
    write_fixture(fixture, path)
    print(fixture.response.status, fixture.request.url)  # noqa: T201
    if suspicions:
        print(f"review {path.relative_to(ROOT)} before committing:")  # noqa: T201
        for item in suspicions:
            print(f"  {item}")  # noqa: T201
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
