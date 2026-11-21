"""CashCtrl's error shapes: the classify hook, RequestRejected, and the recorded refusals."""

import gzip
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
import respx
from xippios.core import (
    BODY_LIMIT,
    AuthError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    TransportError,
    UpstreamError,
    XippiosError,
)
from xippios.core.errors import request_description
from xippios.core.http import status_for
from xippios.core.mcp import error_to_text
from xippios.core.testing import fixture_path, load_fixture, response_from_fixture, sent_query

from xippios.cashctrl._client import DEMO, TENANTS, classify, client_for
from xippios.cashctrl.errors import FieldError, RequestRejected

pytestmark = pytest.mark.anyio

BASE = "https://demo.cashctrl.com/api/v1"
JSON = {"content-type": "application/json;charset=utf-8"}
# A subdomain no message may contain; distinctive, so a hit cannot be a coincidence.
TENANT = "xq-tenant-subdomain-7731"

# The example response of docs/upstream/error-handling.md, verbatim.
DOCUMENTED_REJECTION = {
    "success": False,
    "errors": [
        {"field": "debitId", "message": "This field cannot be empty."},
        {"field": "creditId", "message": "This field cannot be empty."},
        {"field": "amount", "message": "This field cannot be empty."},
    ],
}


def response(path: str, status: int, body: bytes, headers: dict[str, str]) -> httpx.Response:
    return httpx.Response(
        status, headers=headers, content=body, request=httpx.Request("GET", f"{BASE}{path}")
    )


def refusal(path: str, payload: dict[str, object]) -> httpx.Response:
    return response(path, 200, json.dumps(payload).encode(), JSON)


def recorded(fixtures_dir: Path, endpoint: str, case: str) -> httpx.Response:
    """The recorded answer with its recorded request, as core rebuilds it."""
    return response_from_fixture(load_fixture(fixture_path(fixtures_dir, endpoint, case)))


def test_the_documented_rejection_names_every_field() -> None:
    error = classify(refusal("/journal/create.json", DOCUMENTED_REJECTION))
    assert isinstance(error, RequestRejected)
    assert error.errors == [
        FieldError(field="debitId", message="This field cannot be empty."),
        FieldError(field="creditId", message="This field cannot be empty."),
        FieldError(field="amount", message="This field cannot be empty."),
    ]
    assert error.upstream_message is None
    assert str(error) == (
        "CashCtrl rejected the request: debitId: This field cannot be empty.; "
        "creditId: This field cannot be empty.; amount: This field cannot be empty. "
        "(GET /api/v1/journal/create.json)"
    )
    assert error.source == "cashctrl"


def test_a_rejection_is_an_invalid_request_for_both_adapters() -> None:
    error = RequestRejected(
        [FieldError(field=None, message="Nope.")], request="POST /api/v1/journal/create.json"
    )
    assert isinstance(error, InvalidRequestError)
    assert status_for(error) == 422
    assert error_to_text(error) == (
        "error: RequestRejected: CashCtrl rejected the request: Nope. "
        "(POST /api/v1/journal/create.json)"
    )


def test_a_rejection_built_without_its_request_names_none() -> None:
    """Built by a caller, with no answer to name the request from: the reasons alone."""
    assert str(RequestRejected([FieldError(field=None, message="Nope.")])) == (
        "CashCtrl rejected the request: Nope."
    )
    assert str(RequestRejected()) == "CashCtrl rejected the request: no reason given"


@pytest.mark.parametrize(
    ("endpoint", "case"),
    [
        ("account_read", "unknown_id"),
        ("journal_read", "unknown_id"),
        ("order_document_read_pdf", "unknown_id"),
        ("report_collection_download_xlsx", "unknown_id"),
    ],
)
def test_each_error_classify_words_names_the_request_by_cores_description(
    fixtures_dir: Path, endpoint: str, case: str
) -> None:
    """Conventions §5: the method and the path as core's ``request_description`` gives them.

    Never a description of the package's own, never the query or the host.
    """
    answer = recorded(fixtures_dir, endpoint, case)
    error = classify(answer)
    assert isinstance(error, NotFoundError)
    assert str(error).endswith(f" ({request_description(answer)})")
    assert request_description(answer).startswith("GET /api/v1/")


@pytest.mark.parametrize(
    ("endpoint", "case"),
    [
        ("account_read", "missing_id"),
        ("journal_create", "rejected"),
        ("journal_delete", "already_deleted"),
        ("order_payment_create", "pain"),
    ],
)
def test_each_rejection_names_the_request_by_cores_description(
    fixtures_dir: Path, endpoint: str, case: str
) -> None:
    """Conventions §5: a refusal at HTTP 200 names its request as the two errors above do.

    The method and the path as core's ``request_description`` gives them, after the
    reasons; never the host or the query.
    """
    answer = recorded(fixtures_dir, endpoint, case)
    error = classify(answer)
    assert isinstance(error, RequestRejected)
    assert str(error).endswith(f" ({request_description(answer)})")
    assert request_description(answer).startswith(("GET /api/v1/", "POST /api/v1/"))
    assert answer.request.url.host not in str(error)


def test_the_observed_unknown_id_is_not_found(fixtures_dir: Path) -> None:
    error = classify(recorded(fixtures_dir, "account_read", "unknown_id"))
    assert isinstance(error, NotFoundError)
    assert str(error) == "CashCtrl: This account does not exist. (GET /api/v1/account/read.json)"


def test_the_observed_unknown_journal_entry_is_not_found(fixtures_dir: Path) -> None:
    error = classify(recorded(fixtures_dir, "journal_read", "unknown_id"))
    assert isinstance(error, NotFoundError)
    assert str(error) == "CashCtrl: This book entry does not exist. (GET /api/v1/journal/read.json)"


def test_the_observed_unknown_fiscal_period_is_not_found(fixtures_dir: Path) -> None:
    error = classify(recorded(fixtures_dir, "fiscalperiod_read", "unknown_id"))
    assert isinstance(error, NotFoundError)
    assert str(error) == (
        "CashCtrl: This fiscal period does not exist. (GET /api/v1/fiscalperiod/read.json)"
    )


def test_the_observed_missing_id_is_a_rejection_with_a_message(fixtures_dir: Path) -> None:
    error = classify(recorded(fixtures_dir, "account_read", "missing_id"))
    assert isinstance(error, RequestRejected)
    assert error.errors == []
    assert error.upstream_message == "ID missing."
    assert (
        str(error) == "CashCtrl rejected the request: ID missing. (GET /api/v1/account/read.json)"
    )


def test_a_field_list_on_read_by_id_is_a_rejection_not_absence() -> None:
    payload = {"success": False, "errors": [{"field": "id", "message": "Invalid."}]}
    error = classify(refusal("/account/read.json?id=7", payload))
    assert isinstance(error, RequestRejected)
    assert error.errors == [FieldError(field="id", message="Invalid.")]


@pytest.mark.parametrize(
    "payload",
    [
        {"success": False, "message": "Nope."},
        {"success": False, "errorMessage": None, "message": "Nope."},
        {"success": False, "errorMessage": "", "message": "Nope."},
    ],
    ids=["message", "null-errorMessage", "empty-errorMessage"],
)
def test_a_top_level_message_is_read_when_error_message_is_absent(
    payload: dict[str, object],
) -> None:
    error = classify(refusal("/account/delete.json", payload))
    assert isinstance(error, RequestRejected)
    assert error.upstream_message == "Nope."


@pytest.mark.parametrize(
    "path",
    [
        "/account/read.json?id=7",
        "/account/read.json?id=7&lang=de",
        "/fiscalperiod/read.json?id=3",
        "/order/document/read.pdf?ids=3",
        "/order/document/read.pdf?ids=3%2C5&lang=de",
    ],
)
def test_reading_one_record_by_id_is_not_found(path: str) -> None:
    """A ``read.json`` by ``id``, and a ``read.pdf`` by ``ids`` (assumed alike, not observed).

    NOT RECORDED: the refusal is composed in the shape ``account_read/unknown_id`` recorded,
    a documented error (conventions §10, kind 2).
    """
    error = classify(refusal(path, {"success": False, "errorMessage": "Gone.", "data": None}))
    assert isinstance(error, NotFoundError)


@pytest.mark.parametrize(
    "path",
    [
        "/account/read.json",
        "/account/read.json?id=",
        "/account/read.json?id=%20",
        "/sequencenumber/read.json?id=1&date=2026-01-15",
        "/sequencenumber/read.json?type=ORDER&categoryId=4",
        "/setting/read.json",
        "/order/category/read_status.json?id=7",
        "/account/balance?id=7",
        "/order/document/read.pdf?ids=",
        "/order/document/read.pdf?id=3",
        "/order/document/read.zip?ids=3",
        "/journal/list.csv?limit=5",
    ],
)
def test_anything_but_a_read_by_id_is_a_rejection(path: str) -> None:
    error = classify(refusal(path, {"success": False, "errorMessage": "Nope.", "data": None}))
    assert isinstance(error, RequestRejected)
    assert error.upstream_message == "Nope."


def test_a_refusal_is_classified_whatever_the_content_type() -> None:
    """NOT RECORDED: a refusal composed in the shape ``account_read/missing_id`` recorded, a
    documented error (conventions §10, kind 2).

    Its content type, ``text/html``, is an input of the test, not an answer from CashCtrl:
    ``classify`` must not read it, and a byte pre-check and a JSON parse decide.
    """
    body = b'{"success":false,"errorMessage":"Nope."}'
    error = classify(response("/account/delete.json", 200, body, {"content-type": "text/html"}))
    assert isinstance(error, RequestRejected)


@pytest.mark.parametrize(
    ("path", "status", "body", "content_type"),
    [
        ("/fiscalperiod/list.json", 200, b'{"total":1,"data":[{"success":false}]}', JSON),
        ("/account/read.json?id=1", 200, b'{"success":true,"data":{"id":1}}', JSON),
        ("/account/list.csv", 200, b'"success":false;x', {"content-type": "text/csv"}),
        ("/report/a.pdf", 200, b"%PDF-1.7 \xff\xfe", {"content-type": "application/pdf"}),
        ("/account/read.json", 200, b'{"success":false', JSON),
        ("/account/read.json", 200, b'["success":false]', JSON),
        ("/account/read.json", 204, b"", {}),
        ("/account/read.json", 302, b'{"success":false}', JSON),
    ],
)
def test_everything_else_falls_through(
    path: str, status: int, body: bytes, content_type: dict[str, str]
) -> None:
    """NOT RECORDED: bodies composed in the test (conventions §10).

    A list and a read in the shapes recorded (kind 2), and a CSV, a PDF, malformed JSON, a
    204 and a 302 of no shape upstream sends (kind 5), to show that ``classify`` lets them be.
    """
    assert classify(response(path, status, body, content_type)) is None


def test_a_404_means_the_endpoint_does_not_exist() -> None:
    """NOT RECORDED: the documented 404 of an unknown endpoint (``error-handling.md``).

    No recording holds its body, so ``Not here``, of no shape upstream sends, stands in
    (conventions §10, kinds 2 and 5); ``_status_error`` words the error from the status.
    """
    error = classify(response("/account/nope.json", 404, b"Not here", {}))
    assert isinstance(error, UpstreamError)
    assert not isinstance(error, NotFoundError)
    assert error.status == 404
    assert error.body == "Not here"
    assert str(error) == (
        "404 from GET /api/v1/account/nope.json: Not here (the endpoint does not exist upstream)"
    )


FILE_404S = {
    "/order/document/read.pdf": ("order_document_read_pdf", "unknown_id"),
    "/report/element/download.pdf": ("report_element_download_pdf", "unknown_id"),
    "/report/element/download.xlsx": ("report_element_download_xlsx", "unknown_id"),
    "/report/collection/download.pdf": ("report_collection_download_pdf", "unknown_id"),
    "/report/collection/download.xlsx": ("report_collection_download_xlsx", "unknown_id"),
}
"""The file paths whose 404 for an id no record has is recorded, by path: the fixture."""


def recorded_at(fixtures_dir: Path, path: str) -> httpx.Response:
    """The recorded 404 of the operation of ``path``, served for the request ``path`` names.

    A recorded answer served at another URL of the same operation, for a state upstream
    answers alike there (conventions §10): an id no record has, with other parameters.
    """
    answer = recorded(fixtures_dir, *FILE_404S[path.split("?", 1)[0]])
    return response(path, answer.status_code, answer.content, dict(answer.headers))


@pytest.mark.parametrize("path", sorted(FILE_404S))
def test_the_recorded_404_of_an_unknown_id_is_not_found(fixtures_dir: Path, path: str) -> None:
    """Each file path answered an id no record has with HTTP 404 (docs/upstream/OBSERVED.md)."""
    answer = recorded(fixtures_dir, *FILE_404S[path])
    assert answer.status_code == 404
    error = classify(answer)
    assert isinstance(error, NotFoundError)
    assert str(error) == (f"CashCtrl: no record has an id asked, HTTP 404 (GET /api/v1{path})"), (
        "the path, never the query or the host"
    )


@pytest.mark.parametrize(
    "path",
    [
        "/order/document/read.pdf?ids=999999",
        "/order/document/read.pdf?ids=3%2C5&lang=de",
        "/report/element/download.pdf?elementId=999999&fiscalPeriod=2",
        "/report/element/download.xlsx?elementId=999999&startDate=2025-01-01&language=de",
        "/report/collection/download.pdf?collectionId=999999",
        "/report/collection/download.xlsx?collectionId=999999&fiscalPeriod=2",
    ],
)
def test_a_404_by_the_id_with_other_parameters_is_not_found(fixtures_dir: Path, path: str) -> None:
    """The recorded 404 served for a request by the id with more parameters, or other ids."""
    error = classify(recorded_at(fixtures_dir, path))
    assert isinstance(error, NotFoundError)
    assert str(error) == (
        f"CashCtrl: no record has an id asked, HTTP 404 (GET /api/v1{path.split('?', 1)[0]})"
    ), "the path, never the query or the host"


@pytest.mark.parametrize(
    "path",
    [
        "/order/document/read.pdf",
        "/order/document/read.pdf?ids=",
        "/order/document/read.pdf?id=3",
        "/order/document/read.zip?ids=3",
        "/order/read.json?id=3",
        "/journal/list.pdf?limit=5",
        "/report/element/download.pdf?fiscalPeriod=2",
        "/report/element/download.pdf?elementId=",
        "/report/element/download.pdf?collectionId=1",
        "/report/element/download.xml?elementId=1",
        "/report/collection/download.pdf?elementId=1",
        "/report/collection/download_annualreport.pdf?fiscalPeriodId=2",
    ],
)
def test_every_other_404_is_an_unknown_endpoint(path: str) -> None:
    """NOT RECORDED: the documented 404 of an unknown endpoint (``error-handling.md``).

    No recording holds its body, so ``Not here``, of no shape upstream sends, stands in
    (conventions §10, kinds 2 and 5): ``_status_error`` words every 404 but a file
    operation's by its id as an unknown endpoint, from the status, whatever the body.
    """
    error = classify(response(path, 404, b"Not here", {}))
    assert isinstance(error, UpstreamError)
    assert not isinstance(error, NotFoundError)
    assert str(error).endswith("(the endpoint does not exist upstream)")


def test_core_keeps_mapping_status_retry_after_and_body() -> None:
    """NOT RECORDED: the documented 403, 429 and 503 of ``error-handling.md``, composed.

    Their bodies are of no shape upstream sends (conventions §10, kinds 2 and 5), to show
    that core's mapping of status, ``Retry-After`` and body stays.
    """
    plain = {"content-type": "text/plain"}
    auth = classify(response("/account/list.json", 403, b"Forbidden", plain))
    assert isinstance(auth, AuthError)
    assert auth.status == 403
    limited = classify(response("/account/list.json", 429, b"", {"Retry-After": "7"}))
    assert isinstance(limited, RateLimitError)
    assert limited.retry_after == 7.0
    failed = classify(response("/account/list.json", 503, b"x" * (BODY_LIMIT + 10), plain))
    assert isinstance(failed, UpstreamError)
    assert failed.status == 503
    assert len(failed.body) == BODY_LIMIT


@pytest.fixture
def tenant(monkeypatch: pytest.MonkeyPatch) -> str:
    """The demo organisation served from a distinctive subdomain, for the leak tests."""
    monkeypatch.setenv(TENANTS.var(DEMO, "SUBDOMAIN"), TENANT)
    return f"https://{TENANT}.cashctrl.com/api/v1"


async def raised(path: str) -> XippiosError:
    with pytest.raises(XippiosError) as info:
        await client_for(DEMO).get_json(path)
    return info.value


def assert_no_tenant(error: XippiosError) -> None:
    body = getattr(error, "body", "")
    for text in (str(error), repr(error), *map(str, error.args), body):
        assert TENANT not in text.lower()
    # Core names the method and the path, never the host (conventions §5, sdk-core#14).
    assert " from GET /api/v1/" in str(error)


def echoing(status: int, headers: dict[str, str], content: bytes) -> httpx.Response:
    """A response from the tenant host whose body names that host, as error pages may."""
    url = f"https://{TENANT}.cashctrl.com/api/v1/account/list.json"
    return httpx.Response(
        status, headers=headers, content=content, request=httpx.Request("GET", url)
    )


ECHO = (
    f"Service unavailable: https://{TENANT.upper()}.cashctrl.com/api/v1 (see {TENANT}.cashctrl.com)"
)


def test_a_503_body_naming_the_host_names_cashctrl_com() -> None:
    error = classify(echoing(503, {"content-type": "text/plain"}, ECHO.encode()))
    assert isinstance(error, UpstreamError)
    assert error.status == 503
    assert error.body == ("Service unavailable: https://cashctrl.com/api/v1 (see cashctrl.com)")
    assert "503 from GET /api/v1/account/list.json: Service unavailable" in str(error)
    assert_no_tenant(error)


def test_a_compressed_404_body_is_scrubbed_after_decoding() -> None:
    headers = {"content-type": "text/html;charset=utf-8", "content-encoding": "gzip"}
    response = echoing(404, headers, gzip.compress(ECHO.encode()))
    error = classify(response)
    assert isinstance(error, UpstreamError)
    assert error.status == 404
    assert error.body.startswith("Service unavailable: https://cashctrl.com/api/v1")
    assert_no_tenant(error)
    assert TENANT in response.text, "the original response is left as it was"


async def test_a_replayed_401_does_not_name_the_subdomain(
    tenant: str, respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    fixture = load_fixture(fixture_path(fixtures_dir, "account_list", "wrong_key"))
    respx_mock.get(f"{tenant}/account/list.json").respond(
        fixture.response.status,
        headers=fixture.response.headers,
        content=fixture.response.content,
    )
    error = await raised("/account/list.json")
    assert isinstance(error, AuthError)
    assert error.status == 401
    assert_no_tenant(error)


@pytest.mark.parametrize(
    ("status", "headers", "kind"),
    [
        # Retry-After beyond the policy's backoff_max: no retry, no wait.
        (503, {"Retry-After": "120"}, UpstreamError),
        (429, {"Retry-After": "120"}, RateLimitError),
        (404, {}, UpstreamError),
    ],
)
async def test_status_errors_do_not_name_the_subdomain(
    tenant: str,
    respx_mock: respx.MockRouter,
    status: int,
    headers: dict[str, str],
    kind: type[XippiosError],
) -> None:
    route = respx_mock.get(f"{tenant}/account/list.json")
    route.respond(status, headers=headers, text=f"CashCtrl - error at {TENANT}.cashctrl.com")
    error = await raised("/account/list.json")
    assert type(error) is kind
    assert route.call_count == 1
    assert_no_tenant(error)


async def test_a_transport_error_does_not_name_the_subdomain(
    tenant: str, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure before any answer, quoting the host as a TLS mismatch does, hides it.

    Core replaces the request's host with ``<host>`` in a ``TransportError`` (sdk-core#14);
    nothing here masks it locally, so this guards every later core pin. The retries of a
    GET are run without their waits.
    """

    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            f"hostname '{TENANT.upper()}.cashctrl.com' doesn't match '*.example.org' "
            f"(https://{TENANT}.cashctrl.com/api/v1/account/list.json)",
            request=request,
        )

    async def no_wait(seconds: float) -> None:
        return None

    route = respx_mock.get(f"{tenant}/account/list.json").mock(side_effect=fail)
    monkeypatch.setattr(client_for(DEMO), "_sleep", no_wait)
    error = await raised("/account/list.json")
    assert isinstance(error, TransportError)
    assert route.call_count >= 1
    for text in (str(error), repr(error), *map(str, error.args)):
        assert TENANT not in text.lower()
    assert "<host>" in str(error)


async def test_a_429_is_a_rate_limit_error_with_retry_after(
    respx_mock: respx.MockRouter,
) -> None:
    """sdk-core ADR-0033, decision 3: core's mapping inside ``classify``, ``Retry-After`` as sent.

    CashCtrl documents the 429 and nothing about its window (``error-handling.md``); 120
    seconds is beyond the retry policy's backoff, so the client raises at once. NOT
    RECORDED: the documented 429, composed as CashCtrl's status pages were recorded,
    ``CashCtrl - 401 Unauthorized`` and ``CashCtrl - 404 Not Found`` under
    ``text/plain;charset=utf-8`` (conventions §10, kind 2). Its ``Retry-After`` is an input
    of the test, not an answer from CashCtrl.
    """
    route = respx_mock.get(f"{BASE}/account/list.json")
    plain = {"Retry-After": "120", "content-type": "text/plain;charset=utf-8"}
    route.respond(429, headers=plain, text="CashCtrl - 429 Too Many Requests")
    error = await raised("/account/list.json")
    assert isinstance(error, RateLimitError)
    assert error.retry_after == 120.0
    assert route.call_count == 1


async def test_wrong_key_replays_as_auth_error(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_list", "wrong_key")
    with pytest.raises(AuthError) as info:
        await client_for(DEMO).get_json("/account/list.json")
    assert info.value.status == 401


async def test_unknown_id_replays_as_not_found(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("account_read", "unknown_id")
    with pytest.raises(NotFoundError, match="This account does not exist"):
        await client_for(DEMO).get_json("/account/read.json", params={"id": 999999999})
    assert sent_query(route)["id"] == "999999999"


async def test_missing_id_replays_as_request_rejected(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_read", "missing_id")
    with pytest.raises(RequestRejected) as info:
        await client_for(DEMO).get_json("/account/read.json")
    assert info.value.upstream_message == "ID missing."
    assert info.value.errors == []
