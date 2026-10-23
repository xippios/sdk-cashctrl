"""The organisation registry for CashCtrl: one configured ``AsyncClient`` per organisation.

CashCtrl serves every organisation from its own subdomain, and an API user belongs to
exactly one organisation (``docs/upstream/introduction.md``, ``authentication.md``). So
there is no single client here: every task takes ``org``, the name of an organisation
declared in the environment, and ``client_for(org)`` returns that organisation's own
client, with its own base URL, its own key, its own token bucket and no shared cache.

Declaring organisations (the environment is the contract, conventions §7):

- ``CASHCTRL_ORGS``: comma-separated names matching ``^[a-z0-9_]+$``, e.g. ``acme,acme_test``;
- per name, ``CASHCTRL_<NAME>_SUBDOMAIN`` and ``CASHCTRL_<NAME>_API_KEY``, the name
  upper-cased (``CASHCTRL_ACME_TEST_SUBDOMAIN``);
- the reserved organisation ``demo`` is never listed in ``CASHCTRL_ORGS``: it exists when
  both ``CASHCTRL_DEMO_SUBDOMAIN`` and ``CASHCTRL_DEMO_API_KEY`` are set. Fixtures, live
  tests and the fixture recorder use ``demo`` and nothing else.

Isolation is by configuration: a deployment reaches exactly the organisations its
environment declares, and a deployment that does not set the demo pair has no ``demo``.
Nothing here spans organisations: ``orgs()`` returns names only, never values.
"""

import os
import re
import threading
from typing import Any

import httpx
from xippios.core import (
    AsyncClient,
    BasicKeyAuth,
    ClientConfig,
    ConfigError,
    InvalidRequestError,
    NotFoundError,
    RateLimit,
    UpstreamError,
    XippiosError,
)
from xippios.core.errors import BODY_LIMIT, error_from_response

from xippios.cashctrl._version import __version__
from xippios.cashctrl.errors import FieldError, RequestRejected

__all__ = [
    "BASE_URL_TEMPLATE",
    "DEMO",
    "NEUTRAL_HOST",
    "ORGS_ENV",
    "RATE_LIMIT",
    "SOURCE",
    "api_key_env",
    "classify",
    "client_for",
    "orgs",
    "require_org",
    "reset_clients",
    "subdomain_env",
]

SOURCE = "cashctrl"
BASE_URL_TEMPLATE = "https://{subdomain}.cashctrl.com/api/v1"
"""Base URL of one organisation; ``subdomain`` is the organisation's (introduction.md)."""
RATE_LIMIT = RateLimit(per_minute=60)
"""Per organisation and self-imposed: upstream documents only a 429 and "add delays".

Every response carries ``x-cashctrl-requests-left`` (299 observed on 2026-10-23, a 401
included); its window and scope are not documented, so nothing here reads it.
"""
ORGS_ENV = "CASHCTRL_ORGS"
DEMO = "demo"
"""The reserved organisation, declared by its own two variables and never listed."""

_ORG_NAME = re.compile(r"[a-z0-9_]+")
_SUBDOMAIN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def subdomain_env(org: str) -> str:
    """``CASHCTRL_<NAME>_SUBDOMAIN``, the variable holding ``org``'s subdomain."""
    return f"CASHCTRL_{org.upper()}_SUBDOMAIN"


def api_key_env(org: str) -> str:
    """``CASHCTRL_<NAME>_API_KEY``, the variable holding ``org``'s API key."""
    return f"CASHCTRL_{org.upper()}_API_KEY"


def _is_set(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def orgs() -> tuple[str, ...]:
    """The declared organisations: ``CASHCTRL_ORGS`` in order, then ``demo`` if declared.

    Read from the environment on every call; nothing is cached.

    Raises:
        ConfigError: A listed name is malformed, listed twice, or is the reserved ``demo``.
    """
    listed = [part.strip() for part in os.environ.get(ORGS_ENV, "").split(",")]
    names: list[str] = []
    for name in filter(None, listed):
        if name == DEMO:
            raise ConfigError(
                f"{ORGS_ENV} lists {DEMO!r}, which is reserved: the demo organisation is "
                f"declared by {subdomain_env(DEMO)} and {api_key_env(DEMO)} alone",
                source=SOURCE,
            )
        if not _ORG_NAME.fullmatch(name):
            raise ConfigError(
                f"{ORGS_ENV} lists {name!r}; organisation names use only lower-case "
                "letters, digits and underscores",
                source=SOURCE,
            )
        if name in names:
            raise ConfigError(f"{ORGS_ENV} lists {name!r} twice", source=SOURCE)
        names.append(name)
    if _is_set(subdomain_env(DEMO)) and _is_set(api_key_env(DEMO)):
        names.append(DEMO)
    return tuple(names)


def require_org(org: str) -> str:
    """Return ``org`` when it is declared.

    Raises:
        InvalidRequestError: ``org`` is not declared; the message names the declared
            organisations, or the variables to set when there are none.
        ConfigError: ``CASHCTRL_ORGS`` is malformed.
    """
    declared = orgs()
    if org in declared:
        return org
    if declared:
        hint = "declared organisations: " + ", ".join(declared)
    else:
        hint = (
            f"no organisation is declared; set {ORGS_ENV} and, per name, "
            "CASHCTRL_<NAME>_SUBDOMAIN and CASHCTRL_<NAME>_API_KEY"
        )
    raise InvalidRequestError(f"unknown organisation {org!r}; {hint}", source=SOURCE)


def _subdomain(org: str) -> str:
    variable = subdomain_env(org)
    subdomain = os.environ.get(variable, "").strip().lower()
    if not subdomain:
        raise ConfigError(
            f"{variable} is not set; export the organisation's subdomain", source=SOURCE
        )
    if not _SUBDOMAIN.fullmatch(subdomain):
        raise ConfigError(
            f"{variable} is not a subdomain: give the one label before .cashctrl.com",
            source=SOURCE,
        )
    return subdomain


NEUTRAL_HOST = "cashctrl.com"
"""The host a quoted error body names instead of an organisation's own.

See ``_without_tenant_host``.
"""

_REJECTED = re.compile(rb'"success"\s*:\s*false')
_BODY_HEADERS = frozenset(
    {"content-encoding", "content-length", "content-type", "transfer-encoding"}
)
_READ_ONE_PARAMS = frozenset({"id", "lang"})


def _field_errors(items: Any) -> list[FieldError]:
    if not isinstance(items, list):
        return []
    return [
        FieldError(
            field=item["field"] if isinstance(item.get("field"), str) else None,
            message=str(item.get("message", "")),
        )
        for item in items
        if isinstance(item, dict)
    ]


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _reads_one_record(url: httpx.URL) -> bool:
    """``<...>/read.json`` asked for one record: a non-empty ``id``, at most ``lang`` besides."""
    params = url.params
    return (
        url.path.endswith("/read.json")
        and set(params.keys()) <= _READ_ONE_PARAMS
        and _text(params.get("id")) is not None
    )


def _full_text(response: httpx.Response) -> str:
    try:
        return response.text
    except (httpx.ResponseNotRead, UnicodeDecodeError):
        return ""


def _without_tenant_host(response: httpx.Response) -> httpx.Response:
    """A copy of ``response`` whose body names ``cashctrl.com`` wherever it named the tenant's host.

    Every occurrence of the request's host in the body text, in any letter case, becomes
    ``cashctrl.com``: an error page that echoes the host cannot leak it through the
    message snippet or ``UpstreamError.body``, both of which core quotes from the body.
    The request is kept as it is: core's messages name the method and the path, never
    the host (conventions §5, sdk-core#14). Status, reason phrase and the other headers
    are kept, so core's mapping (status, ``Retry-After``, body truncation) is unchanged.
    The copy's body is that text encoded as UTF-8, so the headers that describe the
    original bytes (``Content-Type``, ``Content-Encoding``, ``Content-Length``,
    ``Transfer-Encoding``) are left out.
    """
    request = response.request
    host = request.url.host
    text = _full_text(response)
    if host and host != NEUTRAL_HOST:
        text = re.sub(re.escape(host), NEUTRAL_HOST, text, flags=re.IGNORECASE)
    headers = [
        (name, value)
        for name, value in response.headers.multi_items()
        if name.lower() not in _BODY_HEADERS
    ]
    reason = response.extensions.get("reason_phrase")
    return httpx.Response(
        response.status_code,
        headers=headers,
        content=text.encode("utf-8"),
        request=request,
        extensions={"reason_phrase": reason} if reason is not None else None,
    )


def _body_text(response: httpx.Response) -> str:
    return _full_text(response)[:BODY_LIMIT]


def _status_error(response: httpx.Response) -> XippiosError | None:
    # Core's error_from_response names the method and the path, never the host, but it
    # quotes the body in the message and keeps it as UpstreamError.body, and an error
    # page may echo the organisation's host, its subdomain, which is treated like a key.
    # Core maps a copy whose body names cashctrl.com instead.
    neutral = _without_tenant_host(response)
    error = error_from_response(neutral, source=SOURCE)
    if isinstance(error, NotFoundError):
        # error-handling.md: "404 - Not Found: The requested endpoint doesn't exist." An
        # absent record is a 200 refusal (classify), so NotFoundError keeps that one meaning.
        return UpstreamError(
            f"{error.message} (the endpoint does not exist upstream)",
            status=404,
            body=_body_text(neutral),
            source=SOURCE,
        )
    return error


def classify(response: httpx.Response) -> XippiosError | None:
    """CashCtrl's error shapes, mapped once (ADR-0008); the client calls it on every response.

    HTTP status codes (``docs/upstream/error-handling.md``): every 4xx and 5xx is mapped
    by core's ``error_from_response`` (401/403 ``AuthError``, 429 ``RateLimitError``,
    anything else ``UpstreamError``), whose message names the method and the path but
    never the host. It is applied to a copy of the response whose body names
    ``cashctrl.com`` instead of the organisation's host, so neither the quoted snippet
    nor ``UpstreamError.body`` carries an organisation's subdomain. A 404
    means "The requested endpoint doesn't exist" and raises ``UpstreamError`` with
    ``status=404``: ``NotFoundError`` only ever means an absent record (ADR-0003).

    Documented refusals: validation errors come back as HTTP 200 with
    ``{"success": false, "errors": [{"field": ..., "message": ...}]}``. They raise
    ``RequestRejected`` naming the fields. Other operations are documented to return
    "either a success or error message", one message instead of a list (e.g. "Delete
    accounts" in ``account.md``).

    On 2026-10-23, observed against the demo organisation, not stated in docs/upstream/:
    that one message is a top-level ``errorMessage``, HTTP 200
    ``{"success": false, "errorMessage": "...", "data": null}``. A top-level ``message``
    (not observed) is read when ``errorMessage`` is missing, null or empty.

    - ``account/read.json`` without ``id`` answers ``"errorMessage": "ID missing."``:
      ``RequestRejected`` with that message as ``upstream_message``.
    - ``account/read.json`` and ``currency/read.json`` with an unknown ``id`` answer
      ``"errorMessage": "This account does not exist."`` (``"This currency ..."``). A
      refusal with a message and no field list raises ``NotFoundError`` when the request
      reads one record by id: the path ends in ``/read.json`` and the query is a
      non-empty ``id`` plus at most ``lang``. The test is the request, not the text,
      because the text follows ``lang``. In docs/upstream/ that covers every
      ``<module>/read.json`` whose one parameter is ``id`` (``account``, ``journal``,
      ``order``, ``person`` and the rest), ``fiscalperiod/read.json`` with an ``id`` and
      ``sequencenumber/read.json`` called by ``id`` alone; never
      ``sequencenumber/read.json`` with ``type``, ``categoryId`` or ``date``, nor
      ``setting/read.json``, which takes no ``id``. Known gaps:
      ``order/category/read_status.json``, ``account/balance`` and
      ``account/costcenter/balance`` also read by ``id`` under other paths, so an unknown
      id there stays a ``RequestRejected``. ``account``, ``currency`` and ``journal``
      (``"This book entry does not exist."``) were observed; the other operations are
      assumed to refuse alike.

    Everything else falls through (``None``): a 200 that is not a JSON object with
    ``"success": false`` (data, the CSV, Excel and PDF exports, malformed JSON) and every
    other 2xx or 3xx. There is no content-type check: a byte pre-check for
    ``"success": false`` and a tolerant JSON parse decide, as ``get_json`` does.
    """
    if response.status_code >= 400:
        return _status_error(response)
    if response.status_code != 200 or _REJECTED.search(response.content) is None:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict) or payload.get("success") is not False:
        return None
    errors = _field_errors(payload.get("errors"))
    message = _text(payload.get("errorMessage")) or _text(payload.get("message"))
    url = response.request.url
    if not errors and message and _reads_one_record(url):
        return NotFoundError(
            f"CashCtrl: {message} ({url.path.rsplit('/api/v1', 1)[-1]})", source=SOURCE
        )
    return RequestRejected(errors, upstream_message=message, source=SOURCE)


_clients: dict[str, tuple[str, AsyncClient]] = {}
_clients_lock = threading.Lock()


def client_for(org: str) -> AsyncClient:
    """The configured client of organisation ``org``, built on first use and then reused.

    Each organisation has its own client: its own base URL, key, token bucket and no
    response cache. The key is read from ``CASHCTRL_<NAME>_API_KEY`` on the first request,
    so a declared organisation without a key fails then, with ``ConfigError``. The cache
    entry remembers the subdomain it was built for: when the environment changes the
    subdomain, the next call builds a new client. A changed key alone is picked up after
    ``reset_clients()`` or a restart.

    Raises:
        InvalidRequestError: ``org`` is not declared.
        ConfigError: The organisation's subdomain variable is missing or malformed.
    """
    require_org(org)
    subdomain = _subdomain(org)
    with _clients_lock:
        cached = _clients.get(org)
        if cached is not None and cached[0] == subdomain:
            return cached[1]
        config = ClientConfig(
            source=SOURCE,
            version=__version__,
            base_url=BASE_URL_TEMPLATE.format(subdomain=subdomain),
            rate_limit=RATE_LIMIT,
            cache=None,
            classify=classify,
        )
        client = AsyncClient(config, auth=BasicKeyAuth(api_key_env(org), source=SOURCE))
        _clients[org] = (subdomain, client)
        return client


def reset_clients() -> None:
    """Forget every cached client; the next ``client_for`` builds afresh. For tests."""
    with _clients_lock:
        _clients.clear()
