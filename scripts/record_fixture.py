"""Record one exchange with the demo organisation into a fixture (``/record-fixture``).

Run from the repository root with the demo pair (``CASHCTRL_DEMO_SUBDOMAIN``,
``CASHCTRL_DEMO_API_KEY``) in the environment::

    uv run scripts/record_fixture.py account/read.json unknown_id id=999999999
    uv run scripts/record_fixture.py account/list.json wrong_key --wrong-key

``<endpoint>`` is the upstream path after ``/api/v1/`` as ``docs/upstream/`` writes it;
the fixture lands at ``tests/fixtures/<endpoint>/<case>.json`` with the endpoint's slashes
as underscores and without its extension: ``tests/fixtures/account_read/unknown_id.json``.
``key=value`` arguments are query parameters, named as upstream names them.

The organisation is not a parameter. The recorder removes ``CASHCTRL_ORGS`` from its own
environment and always records through ``client_for("demo")``, so it cannot reach a
productive organisation. ``--wrong-key`` sends ``not-a-valid-key`` instead of the real key,
through a throwaway client with the demo organisation's configuration, to record a 401
without touching the real key.

The demo organisation holds synthetic books only, seeded by ``scripts/seed_demo.py`` and
described in ``docs/demo-org.md``: invented companies on placeholder streets,
``.example`` addresses, invented amounts. So every module and every amount may be
recorded. These policies stand all the same; every refusal writes nothing, says why,
never shows a value, and exits with status 1:

- GET only. Any other ``--method`` is refused before a request is sent; the recorder
  for the write tools will add writes deliberately.
- ``.json`` only. An endpoint without the extension answers a bare number or a document
  (``account/balance``, ``account/costcenter/balance``, ``fiscalperiod/result``,
  ``setting/get``) and an export (``.pdf``, ``.xlsx``, ``.csv``, ``.zip``) a file; both
  are refused before a request is sent.
- No e-mail addresses. Every e-mail-shaped string in the request URL, the response
  headers and the body becomes ``user@example.com``, with ``@`` written plainly, as
  ``%40`` or as the HTML entities ``&#64;``, ``&#x40;`` and ``&commat;`` (``notes`` and
  footers are HTML upstream); ``SYSTEM`` in ``createdBy`` is not an address and stays.
  The synthetic books use reserved ``.example`` addresses, but ``createdBy`` and
  ``lastUpdatedBy`` may carry the address of the user who wrote a record, a real person,
  so the scrub stays.
- No API user tags. CashCtrl names an API user in ``createdBy`` and ``lastUpdatedBy`` as
  ``API:`` and the first four characters of its key (observed on 2026-10-23 on the
  records ``scripts/seed_demo.py`` wrote). Every such tag becomes ``API:REDACTED``,
  whichever key it comes from, with the marker in any case, at the start of a word or
  right after a JSON escape. A tag the scrub cannot reach (glued to a word, or behind a
  Unicode escape) is refused by the final check.

Nothing unscrubbed touches disk. The request goes through the real client with
``raise_on_error=False``, and core's ``fixture_from_response`` turns the exchange into a
fixture in memory, credentials scrubbed. Then every occurrence of the demo host
(``<CASHCTRL_DEMO_SUBDOMAIN>.cashctrl.com``) in the request URL, the response headers and
the body becomes ``demo.cashctrl.com``, the host offline tests replay against, every
e-mail address becomes ``user@example.com`` and every API user tag ``API:REDACTED``. The
fixture is checked last, before the one write, in its serialised text and in every
decoded string of a JSON body: the real subdomain, the real key (plain or as a
basic-auth token), an e-mail address other than ``user@example.com``, an API user tag
other than ``API:REDACTED`` in any case and position (the key's own tag also with ``:``
URL-encoded, as an HTML entity or followed by a space), or the key's first four
characters on their own, reported as a possible key prefix, means nothing is written and
the exit status is 1; a key-like name whose value is not ``REDACTED`` is written for
review, also with exit status 1. Only the status and the scrubbed URL are printed.

A body that is not UTF-8 text, which core would keep as base64, is refused before
anything is written, should a ``.json`` endpoint ever send one: such a body can be
neither scrubbed nor reviewed.

Host, e-mail and API user tag scrubbing are local to this repository for now: they are
the pattern that moves into core's recorder (``xippios.core.testing.record``) later, for
every multi-tenant source.
"""

import argparse
import base64
import json
import os
import re
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import httpx
from xippios.core import AsyncClient, BasicKeyAuth, sync
from xippios.core.testing import REDACTED, Fixture, fixture_path
from xippios.core.testing.fixtures import fixture_from_response

from xippios.cashctrl._client import (
    DEMO,
    ORGS_ENV,
    SOURCE,
    api_key_env,
    client_for,
    subdomain_env,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
REPLAY_HOST = "demo.cashctrl.com"
WRONG_KEY = "not-a-valid-key"  # pragma: allowlist secret (a deliberately invalid key)
KEY_LIKE = re.compile(r"api[_-]?key|token|secret|authorization|password", re.IGNORECASE)
_ENDPOINT = re.compile(r"[a-z][a-z0-9_]*(?:/[a-z][a-z0-9_]*)*(?:\.[a-z]+)?")
_CASE = re.compile(r"[a-z0-9][a-z0-9_]*")

SCRUBBED_EMAIL = "user@example.com"
EMAIL = re.compile(r"[\w.%+-]+(?P<at>@|%40|&#0*64;?|&#[xX]0*40;?|&commat;)[\w.-]+\.[^\W\d_]{2,}")
"""An e-mail-shaped string: ``@`` plain, as ``%40`` (a query string) or as an HTML entity."""
# The same, but never starting inside a JSON escape (\n, \u00e9): scrubbing the raw text
# of a JSON body then keeps it JSON.
_EMAIL_IN_TEXT = re.compile(r"(?:(?<=\\[nrtbf])|(?<![\w.%+\\-]))" + EMAIL.pattern)
_SCRUBBED_EMAILS = frozenset({SCRUBBED_EMAIL, SCRUBBED_EMAIL.replace("@", "%40")})

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
        "params", nargs="*", metavar="key=value", help="query parameters, e.g. id=999999999"
    )
    parser.add_argument("--method", default="GET", help="HTTP method; only GET is recorded")
    parser.add_argument(
        "--wrong-key", action="store_true", help=f"send {WRONG_KEY!r} instead of the key"
    )
    args = parser.parse_args(argv)
    args.endpoint = args.endpoint.removeprefix("/").removeprefix("api/v1/")
    if not _ENDPOINT.fullmatch(args.endpoint):
        parser.error(f"endpoint {args.endpoint!r} is not an upstream path like account/read.json")
    if not _CASE.fullmatch(args.case):
        parser.error(f"case {args.case!r}: use lower-case letters, digits and underscores")
    if any("=" not in item for item in args.params):
        parser.error("query parameters are key=value")
    args.params = {key: value for key, _, value in (item.partition("=") for item in args.params)}
    return args


def fixture_endpoint(endpoint: str) -> str:
    """``account/read.json`` → ``account_read``: the fixture directory of an endpoint."""
    return endpoint.rsplit(".", 1)[0].replace("/", "_")


def refusal(method: str, endpoint: str) -> str | None:
    """Why the request must not be sent at all, else ``None``: not GET, or not ``.json``."""
    if method.upper() != "GET":
        return (
            f"only GET is recorded, not {method.upper()}: recordings are read-only, and the "
            "recorder for the write tools will add writes deliberately"
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
    """One request through the real client; an error status is returned, not raised."""
    return await client.request(method, path, params=params, raise_on_error=False)


exchange = sync(exchange_async)


def rewrite(fixture: Fixture, sub: Callable[[str], str]) -> Fixture:
    """``fixture`` with ``sub`` applied to the request URL, every header and the body."""
    request = fixture.request.model_copy(update={"url": sub(fixture.request.url)})
    response = fixture.response.model_copy(
        update={
            "headers": [(sub(name), sub(value)) for name, value in fixture.response.headers],
            "body": sub(fixture.response.body),
        }
    )
    return fixture.model_copy(update={"request": request, "response": response})


def scrub_host(fixture: Fixture, host: re.Pattern[str]) -> Fixture:
    """``fixture`` with every match of ``host`` in URL, headers and body made the replay host."""
    return rewrite(fixture, lambda text: host.sub(REPLAY_HOST, text))


def _placeholder(match: re.Match[str]) -> str:
    return SCRUBBED_EMAIL.replace("@", "%40") if match["at"] == "%40" else SCRUBBED_EMAIL


def scrub_emails(fixture: Fixture) -> Fixture:
    """``fixture`` with every e-mail address in URL, headers and body made the placeholder."""
    return rewrite(fixture, lambda text: _EMAIL_IN_TEXT.sub(_placeholder, text))


def _decoded(body: str) -> tuple[bool, Any]:
    """``(True, value)`` for a JSON body, ``(False, None)`` for any other."""
    try:
        return True, json.loads(body)
    except ValueError:
        return False, None


def to_json(fixture: Fixture) -> str:
    """The fixture as text, laid out as core's ``write_fixture`` lays it out."""
    return json.dumps(fixture.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"


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


def _holds_an_address(fixture: dict[str, Any]) -> bool:
    """An e-mail address other than the placeholder in the URL, a header or the body.

    The raw texts are searched as they are scrubbed; the decoded strings of a JSON body
    with the plain pattern, so an address the scrub could not reach is still found.
    """
    request, response = fixture.get("request", {}), fixture.get("response", {})
    body = response.get("body", "")
    raw = [request.get("url", ""), body]
    raw += [part for header in response.get("headers", []) for part in header]
    found = [match.group(0) for text in raw for match in _EMAIL_IN_TEXT.finditer(text)]
    is_json, decoded = _decoded(body)
    if is_json:
        found += [match.group(0) for text in _strings(decoded) for match in EMAIL.finditer(text)]
    return any(address not in _SCRUBBED_EMAILS for address in found)


def scrub_api_users(fixture: Fixture) -> Fixture:
    """``fixture`` with every API user tag in URL, headers and body made ``API:REDACTED``."""
    return rewrite(fixture, lambda text: API_USER.sub(SCRUBBED_API_USER, text))


def _searched_texts(text: str, fixture: dict[str, Any]) -> list[str]:
    """The serialised fixture and, for a JSON body, every decoded key and string in it."""
    is_json, decoded = _decoded(fixture.get("response", {}).get("body", ""))
    return [text, *(_strings(decoded) if is_json else [])]


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


def check(text: str, subdomain: str, key: str) -> tuple[list[str], list[str]]:
    """``(leaks, suspicions)`` in a serialised fixture; neither ever contains a value."""
    leaks: list[str] = []
    if subdomain != DEMO and subdomain in text.lower():
        leaks.append(f"the value of {subdomain_env(DEMO)}")
    token = base64.b64encode(f"{key}:".encode()).decode("ascii")
    if key and (key in text or token in text):
        leaks.append(f"the value of {api_key_env(DEMO)}")
    fixture = json.loads(text)
    texts = _searched_texts(text, fixture)
    if _holds_an_api_user_tag(texts, key):
        leaks.append(f"an API user tag other than {SCRUBBED_API_USER}")
    if _holds_the_bare_prefix(texts, key):
        leaks.append(
            f"a possible key prefix: the first four characters of {api_key_env(DEMO)}, "
            "without the API: marker (four characters alone may be a coincidence; "
            "find them in the response before recording again)"
        )
    if _holds_an_address(fixture):
        leaks.append(f"an e-mail address other than {SCRUBBED_EMAIL}")
    suspicions = list(_key_like_values(fixture, "fixture"))
    url = fixture.get("request", {}).get("url", "")
    suspicions += [f"request URL mentions {word!r}" for word in _body_mentions(url)]
    body = fixture.get("response", {}).get("body", "")
    suspicions += [f"response body mentions {word!r}" for word in _body_mentions(body)]
    return leaks, suspicions


def main(argv: Sequence[str] | None = None) -> int:
    """Refuse or record, scrub in memory, check, write; return the exit status."""
    args = parse_args(argv)
    refused = refusal(args.method, args.endpoint)
    if refused:
        print(f"not recorded: {refused}")  # noqa: T201
        return 1
    os.environ.pop(ORGS_ENV, None)  # the recorder sees the demo organisation and nothing else
    client = client_for(DEMO)
    if args.wrong_key:
        auth = BasicKeyAuth(api_key_env(DEMO), key=WRONG_KEY, source=SOURCE)
        client = AsyncClient(client.config, auth=auth)
    path = fixture_path(FIXTURES, fixture_endpoint(args.endpoint), args.case)
    fixture = fixture_from_response(exchange(client, "GET", f"/{args.endpoint}", args.params))
    if fixture.response.body_base64:
        print(  # noqa: T201
            f"not recorded: the body of {args.endpoint} is not UTF-8 text; exports are out "
            "of scope for fixtures, and such a body can be neither scrubbed nor reviewed"
        )
        return 1

    subdomain = os.environ[subdomain_env(DEMO)].strip().lower()
    host = re.compile(re.escape(f"{subdomain}.cashctrl.com"), re.IGNORECASE)
    fixture = scrub_api_users(scrub_emails(scrub_host(fixture, host)))
    text = to_json(fixture)

    leaks, suspicions = check(text, subdomain, os.environ.get(api_key_env(DEMO), ""))
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
