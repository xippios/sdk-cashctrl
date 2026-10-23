"""The fixture recorder records the demo organisation only and never writes its host or key.

It also holds to its policies: GET only, .json only, no e-mail address. The demo
organisation is synthetic, so every module and every amount may be recorded.
"""

import base64
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest
import respx

from xippios.cashctrl._client import DEMO, ORGS_ENV, api_key_env, subdomain_env

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "record_fixture.py"
REAL = "realsub"
KEY = "Qz7k-key-for-the-test"  # pragma: allowlist secret


def load_recorder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("record_fixture", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    module = load_recorder()
    monkeypatch.setattr(module, "FIXTURES", tmp_path / "tests" / "fixtures")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setenv(subdomain_env(DEMO), REAL)
    monkeypatch.setenv(api_key_env(DEMO), KEY)
    return module


def test_fixture_directory_follows_the_endpoint() -> None:
    recorder = load_recorder()
    assert recorder.fixture_endpoint("account/read.json") == "account_read"
    assert recorder.fixture_endpoint("account/bank/list.json") == "account_bank_list"


def test_the_demo_host_becomes_the_replay_host(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa")  # ignored: the recorder sees demo only
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/read.json")
    route.mock(
        return_value=httpx.Response(
            200,
            json={"success": False, "message": f"see https://{REAL.upper()}.cashctrl.com/x"},
            headers={"Location": f"https://{REAL}.cashctrl.com/"},
        )
    )
    assert recorder.main(["account/read.json", "unknown_id", "id=999999999"]) == 0
    sent = route.calls.last.request
    assert sent.url.params["id"] == "999999999"
    assert sent.headers["Authorization"].startswith("Basic ")
    written = tmp_path / "tests" / "fixtures" / "account_read" / "unknown_id.json"
    text = written.read_text()
    assert REAL not in text.lower()
    assert "https://demo.cashctrl.com/api/v1/account/read.json?id=999999999" in text
    assert "https://demo.cashctrl.com/x" in json.loads(text)["response"]["body"]
    out = capsys.readouterr().out
    assert out == "200 https://demo.cashctrl.com/api/v1/account/read.json?id=999999999\n"


def test_wrong_key_never_sends_the_real_key(
    recorder: ModuleType, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(return_value=httpx.Response(401, text="Unauthorized"))
    assert recorder.main(["account/list.json", "wrong_key", "--wrong-key"]) == 0
    token = base64.b64encode(f"{recorder.WRONG_KEY}:".encode()).decode()
    assert route.calls.last.request.headers["Authorization"] == f"Basic {token}"


@pytest.mark.parametrize("leak", [REAL, KEY, base64.b64encode(f"{KEY}:".encode()).decode()])
def test_a_leak_is_never_written(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    leak: str,
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(return_value=httpx.Response(200, json={"name": f"{leak} ltd"}))
    assert recorder.main(["account/list.json", "leaky"]) == 1
    assert not (tmp_path / "tests" / "fixtures" / "account_list").exists()
    out = capsys.readouterr().out
    assert "not written" in out
    assert leak not in out


def test_nothing_unscrubbed_touches_disk(
    recorder: ModuleType, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    writes: list[str] = []
    write_text = Path.write_text

    def spy(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
        writes.append(data)
        return write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", spy)
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/read.json")
    route.mock(
        return_value=httpx.Response(
            200,
            json={"success": False, "errorMessage": f"see https://{REAL}.cashctrl.com/"},
            headers={"Location": f"https://{REAL}.cashctrl.com/"},
        )
    )
    assert recorder.main(["account/read.json", "one_write", "id=1"]) == 0
    assert len(writes) == 1, "one write, of the scrubbed fixture"
    assert REAL not in writes[0].lower()
    assert "https://demo.cashctrl.com/api/v1/account/read.json?id=1" in writes[0]


def test_a_binary_body_is_refused(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A .json endpoint that answers with a file anyway: refused after the request.
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(
        return_value=httpx.Response(
            200, content=b"%PDF-1.7 \xff\xfe", headers={"content-type": "application/pdf"}
        )
    )
    assert recorder.main(["account/list.json", "export"]) == 1
    assert not (tmp_path / "tests" / "fixtures").exists()
    out = capsys.readouterr().out
    assert "not UTF-8 text" in out
    assert "exports are out of scope" in out
    assert REAL not in out


def test_key_like_names_need_a_review(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(
        return_value=httpx.Response(
            200, json={"accessToken": "abc"}, headers={"X-Csrf-Token": "abc"}
        )
    )
    assert recorder.main(["account/list.json", "suspicious"]) == 1
    assert (tmp_path / "tests" / "fixtures" / "account_list" / "suspicious.json").exists()
    out = capsys.readouterr().out
    assert "header 'x-csrf-token'" in out
    assert "response body mentions 'token'" in out
    assert "abc" not in out


def test_arguments_are_checked() -> None:
    recorder = load_recorder()
    with pytest.raises(SystemExit):
        recorder.parse_args(["account/read.json", "Bad-Case"])
    with pytest.raises(SystemExit):
        recorder.parse_args(["https://x/account/read.json", "case"])
    with pytest.raises(SystemExit):
        recorder.parse_args(["account/read.json", "case", "id"])
    args = recorder.parse_args(["/api/v1/account/read.json", "case", "id=1", "q=a=b"])
    assert args.endpoint == "account/read.json"
    assert args.params == {"id": "1", "q": "a=b"}
    assert args.method == "GET"
    with pytest.raises(SystemExit):  # lifted with the amount refusal: the demo is synthetic
        recorder.parse_args(["account/list.json", "case", "--allow-amounts"])


# The recorder's policies.


def test_e_mail_addresses_become_the_placeholder(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    body = {
        "total": 1,
        "data": [
            {
                "createdBy": "Jane.Doe+books@corp.example",
                "lastUpdatedBy": "SYSTEM",
                "notes": (
                    "<p>ask\nhans.muster@beispiel.example or <a href='mailto:x@y.example'>x</a></p>"
                ),
            }
        ],
    }
    route.mock(
        return_value=httpx.Response(200, json=body, headers={"X-Contact": "ops@corp.example"})
    )
    assert recorder.main(["account/list.json", "with_users", "query=jane@corp.example"]) == 0
    text = (tmp_path / "tests" / "fixtures" / "account_list" / "with_users.json").read_text()
    for gone in ("Jane.Doe", "hans.muster", "beispiel", "corp.example", "x@y.example", "jane"):
        assert gone not in text
    fixture = json.loads(text)
    assert fixture["request"]["url"].endswith("?query=user%40example.com")
    assert ["x-contact", "user@example.com"] in fixture["response"]["headers"]
    (record,) = json.loads(fixture["response"]["body"])["data"]
    assert record["createdBy"] == "user@example.com"
    assert record["lastUpdatedBy"] == "SYSTEM"
    assert record["notes"] == (
        "<p>ask\nuser@example.com or <a href='mailto:user@example.com'>x</a></p>"
    ), "the body is still the JSON upstream sent, escapes intact"
    assert "jane" not in capsys.readouterr().out.lower()


def test_an_address_the_scrub_cannot_reach_is_never_written(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # An escape right before the address: the raw text is left alone, the decoded body
    # still shows the address, so the final check refuses the write.
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(return_value=httpx.Response(200, content=b'{"notes": "\\u00e9mile@corp.example"}'))
    assert recorder.main(["account/list.json", "escaped"]) == 1
    assert not (tmp_path / "tests" / "fixtures" / "account_list").exists()
    out = capsys.readouterr().out
    assert "not written" in out
    assert "an e-mail address other than user@example.com" in out
    assert "corp.example" not in out


def test_the_check_names_an_address_but_never_shows_it(recorder: ModuleType) -> None:
    def fixture(url: str, headers: list[list[str]], body: str) -> str:
        return json.dumps({"request": {"url": url}, "response": {"headers": headers, "body": body}})

    clean = fixture(
        "https://demo.cashctrl.com/api/v1/x.json?q=user%40example.com",
        [["x-user", "user@example.com"]],
        '{"createdBy": "user@example.com", "lastUpdatedBy": "SYSTEM"}',
    )
    assert recorder.check(clean, REAL, KEY) == ([], [])
    for leaky in (
        fixture("https://demo.cashctrl.com/api/v1/x.json?q=a%40b.example", [], "{}"),
        fixture("https://demo.cashctrl.com/", [["x-user", "a@b.example"]], "{}"),
        fixture("https://demo.cashctrl.com/", [], '{"createdBy": "a@b.example"}'),
        fixture("https://demo.cashctrl.com/", [], "plain text from a@b.example"),
    ):
        leaks, _ = recorder.check(leaky, REAL, KEY)
        assert leaks == ["an e-mail address other than user@example.com"]


@pytest.mark.parametrize("method", ["POST", "post", "PUT", "DELETE"])
def test_only_get_is_recorded(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    method: str,
) -> None:
    assert recorder.main(["account/create.json", "write", "--method", method]) == 1
    assert not respx_mock.calls, "refused before any request"
    assert not (tmp_path / "tests" / "fixtures").exists()
    out = capsys.readouterr().out
    assert out.startswith(f"not recorded: only GET is recorded, not {method.upper()}")
    assert "the write tools will add writes deliberately" in out


def test_get_may_be_spelt_in_lower_case(recorder: ModuleType, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/currency/list.json")
    route.mock(return_value=httpx.Response(200, json={"total": 0, "data": []}))
    assert recorder.main(["currency/list.json", "empty", "--method", "get"]) == 0
    assert route.calls.last.request.method == "GET"


@pytest.mark.parametrize(
    "endpoint",
    [
        "account/balance",
        "account/costcenter/balance",
        "fiscalperiod/result",
        "setting/get",
        "currency/exchangerate",
        "account/list.pdf",
        "account/list.xlsx",
        "account/list.csv",
        "order/document/read.zip",
    ],
)
def test_only_json_endpoints_are_recorded(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    endpoint: str,
) -> None:
    assert recorder.main([endpoint, "not_json", "id=1"]) == 1
    assert not respx_mock.calls, "refused before any request"
    assert not (tmp_path / "tests" / "fixtures").exists()
    out = capsys.readouterr().out
    assert out.startswith(f"not recorded: only .json endpoints are recorded, not {endpoint}: ")
    assert "a bare number or a document" in out


@pytest.mark.parametrize(
    "endpoint",
    [
        "account/list.json",
        "account/bank/list.json",
        "currency/list.json",
        "fiscalperiod/list.json",
        "tax/list.json",
        "person/list.json",
        "order/list.json",
        "journal/list.json",
        "location/list.json",
        "history/list.json",
        "setting/read.json",
    ],
)
def test_every_json_get_of_any_module_may_be_recorded(recorder: ModuleType, endpoint: str) -> None:
    """The demo organisation is synthetic: no module is refused, ``account/bank/`` included."""
    assert recorder.refusal("GET", endpoint) is None
    for gone in ("ALLOWED_MODULES", "REFUSED_PATHS", "AMOUNT_KEY", "body_amounts"):
        assert not hasattr(recorder, gone), f"{gone} went with the provisional policies"


def test_amounts_are_recorded(
    recorder: ModuleType, tmp_path: Path, respx_mock: respx.MockRouter
) -> None:
    """Non-zero amounts are recorded as sent: the demo organisation's books are invented."""
    record = {"id": 7, "openingAmount": 100000, "endAmount": "4850.00", "targetMax": 12.5}
    entry = {"id": 3, "amount": 4800.0, "debitId": 4, "creditId": 9}
    for endpoint, body in (
        ("account/list.json", {"total": 1, "data": [record]}),
        ("journal/list.json", {"total": 1, "data": [entry]}),
    ):
        route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/{endpoint}")
        route.mock(return_value=httpx.Response(200, json=body))
        assert recorder.main([endpoint, "with_amounts"]) == 0
        directory = recorder.fixture_endpoint(endpoint)
        written = tmp_path / "tests" / "fixtures" / directory / "with_amounts.json"
        assert json.loads(json.loads(written.read_text())["response"]["body"]) == body


@pytest.mark.parametrize(
    "written",
    [
        "jane&#64;corp.example",
        "jane&#064;corp.example",
        "jane&#x40;corp.example",
        "jane&#X40;corp.example",
        "jane&commat;corp.example",
    ],
)
def test_html_entities_count_as_at(
    recorder: ModuleType, tmp_path: Path, respx_mock: respx.MockRouter, written: str
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/read.json")
    notes = f"<p>Questions to <a href='mailto:{written}'>{written}</a></p>"
    route.mock(return_value=httpx.Response(200, json={"success": True, "data": {"notes": notes}}))
    assert recorder.main(["account/read.json", "html", "id=1"]) == 0
    text = (tmp_path / "tests" / "fixtures" / "account_read" / "html.json").read_text()
    assert "jane" not in text
    assert "corp.example" not in text
    data = json.loads(json.loads(text)["response"]["body"])["data"]
    assert data["notes"] == (
        "<p>Questions to <a href='mailto:user@example.com'>user@example.com</a></p>"
    )
    leaks, _ = recorder.check(
        json.dumps({"request": {"url": ""}, "response": {"headers": [], "body": notes}}),
        REAL,
        KEY,
    )
    assert leaks == ["an e-mail address other than user@example.com"], "and in the final check"


OWN = f"API:{KEY[:4]}"
"""The tag CashCtrl gives the recorder's own API user: ``API:`` and the key's first four."""


def fixture_text(url: str = "", headers: list[list[str]] | None = None, body: str = "{}") -> str:
    """A serialised fixture as ``check`` reads it."""
    response = {"headers": headers or [], "body": body}
    return json.dumps({"request": {"url": url}, "response": response})


def test_api_user_tags_become_redacted(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """In ``createdBy`` and ``lastUpdatedBy``, in any case, also right after a JSON escape."""
    record = {
        "id": 2,
        "createdBy": OWN,
        "lastUpdatedBy": "api:zq7x",  # another API user's key, in lower case
        "notes": "first line\nAPI:Ab12 wrote this",  # raw JSON: \n, then the tag
        "custom": "SYSTEM",
    }
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/fiscalperiod/list.json")
    route.mock(return_value=httpx.Response(200, json={"total": 1, "data": [record]}))
    assert recorder.main(["fiscalperiod/list.json", "api_users"]) == 0
    text = (tmp_path / "tests" / "fixtures" / "fiscalperiod_list" / "api_users.json").read_text()
    for gone in (KEY[:4], "zq7x", "Ab12"):
        assert gone not in text
    (written,) = json.loads(json.loads(text)["response"]["body"])["data"]
    assert (written["createdBy"], written["lastUpdatedBy"]) == ("API:REDACTED", "API:REDACTED")
    assert written["notes"] == "first line\nAPI:REDACTED wrote this", "still the JSON sent"
    assert written["custom"] == "SYSTEM"
    assert KEY[:4] not in capsys.readouterr().out


@pytest.mark.parametrize(
    "content",
    [
        b'{"notes": "xAPI:Ab12"}',  # glued to a word: the scrub leaves it
        ('{"notes": "x' + OWN + '"}').encode(),
        b'{"createdBy": "\\u0041PI:Ab12"}',  # only the decoded string shows the marker
        ('{"createdBy": "\\u0041PI:' + KEY[:4] + '"}').encode(),
    ],
    ids=["glued", "own-glued", "escaped-marker", "own-escaped-marker"],
)
def test_a_tag_the_scrub_cannot_reach_is_never_written(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    content: bytes,
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/fiscalperiod/list.json")
    route.mock(return_value=httpx.Response(200, content=content))
    assert recorder.main(["fiscalperiod/list.json", "unreachable"]) == 1
    assert not (tmp_path / "tests" / "fixtures" / "fiscalperiod_list").exists()
    out = capsys.readouterr().out
    assert "an API user tag other than API:REDACTED" in out
    for hidden in ("Ab12", KEY[:4]):
        assert hidden not in out


@pytest.mark.parametrize(
    "text",
    [
        fixture_text(body=json.dumps({"createdBy": "API:Zq7x"})),
        fixture_text(body=json.dumps({"createdBy": "api:zq7x"})),
        fixture_text(body=json.dumps({"lastUpdatedBy": "Api:Zq7x"})),
        fixture_text(body=json.dumps({"notes": "xAPI:Ab12"})),
        fixture_text(body=json.dumps({"notes": "line\nAPI:Ab12"})),
        fixture_text(body=json.dumps({"createdBy": OWN})),
        fixture_text(body=json.dumps({"createdBy": OWN.lower()})),
        fixture_text(headers=[["x-user", "API:Zq7x"]]),
        fixture_text(url="https://demo.cashctrl.com/api/v1/x.json?q=API:Zq7x"),
    ],
    ids=[
        "body",
        "lower-case",
        "mixed-case",
        "glued",
        "after-escape",
        "own",
        "own-lower-case",
        "header",
        "url",
    ],
)
def test_the_check_refuses_any_tag_in_any_case_and_position(
    recorder: ModuleType, text: str
) -> None:
    leaks, _ = recorder.check(text, REAL, KEY)
    assert "an API user tag other than API:REDACTED" in leaks
    for hidden in ("Zq7x", "zq7x", "Ab12", KEY[:4], KEY[:4].lower()):
        assert all(hidden not in leak for leak in leaks)


@pytest.mark.parametrize(
    "written",
    [f"API%3A{KEY[:4]}", f"API: {KEY[:4]}", f"API&#58;{KEY[:4]}", f"api&colon;{KEY[:4]}"],
    ids=["url-encoded", "space", "decimal-entity", "named-entity"],
)
def test_the_own_tag_is_found_where_the_general_pattern_is_not(
    recorder: ModuleType, written: str
) -> None:
    """The deciding branch here is the key's own tag: the general pattern needs ``API:``."""
    text = fixture_text(body=json.dumps({"createdBy": written}))
    assert recorder.API_USER_ANYWHERE.search(text) is None
    leaks, _ = recorder.check(text, REAL, KEY)
    assert "an API user tag other than API:REDACTED" in leaks
    other, _ = recorder.check(text, REAL, "Wv3m-another-key")  # pragma: allowlist secret
    assert other == [], "without the key's own prefix nothing decides"


def test_a_bare_key_prefix_is_refused_as_a_possible_prefix(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Four characters alone may be a coincidence; nothing is written all the same."""
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/fiscalperiod/list.json")
    route.mock(return_value=httpx.Response(200, json={"notes": f"ref {KEY[:4]} only"}))
    assert recorder.main(["fiscalperiod/list.json", "bare_prefix"]) == 1
    assert not (tmp_path / "tests" / "fixtures" / "fiscalperiod_list").exists()
    out = capsys.readouterr().out
    assert "possible key prefix" in out
    assert "an API user tag" not in out
    assert KEY[:4] not in out
    leaks, _ = recorder.check(fixture_text(body=json.dumps({"n": KEY[:4]})), REAL, KEY)
    assert len(leaks) == 1
    assert leaks[0].startswith("a possible key prefix: ")


def test_the_scrubbed_tag_and_other_api_words_pass(recorder: ModuleType) -> None:
    body = json.dumps({"createdBy": "API:REDACTED", "notes": "the API: see the docs; api:"})
    assert recorder.check(fixture_text(body=body), REAL, KEY) == ([], [])


TOKEN = "AbCd" * 8  # the shape of the observed order hash: 32 characters, both cases


def test_token_like_fields_become_redacted(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``hash`` (seen in ``order/read.json``) by its name, at any depth; nothing else.

    ``hashtag`` keeps its value: it is no token-like name, and as a key-like word it goes
    to review.
    """
    order = {
        "id": 3,
        "hash": TOKEN,
        "hashtag": "kept",
        "items": [{"id": 6, "HASH": "Zx" * 16, "name": "Bürostuhl"}],
        "fileId": None,
    }
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/order/read.json")
    route.mock(return_value=httpx.Response(200, json={"success": True, "data": order}))
    assert recorder.main(["order/read.json", "by_id", "id=3"]) == 1, "hashtag: review"
    text = (tmp_path / "tests" / "fixtures" / "order_read" / "by_id.json").read_text()
    assert TOKEN not in text
    assert "Zx" * 16 not in text
    written = json.loads(json.loads(text)["response"]["body"])["data"]
    assert (written["hash"], written["items"][0]["HASH"]) == ("REDACTED", "REDACTED")
    assert (written["hashtag"], written["items"][0]["name"], written["fileId"]) == (
        "kept",
        "Bürostuhl",
        None,
    ), "only the token-like values change"
    out = capsys.readouterr().out
    assert "response body mentions 'hash'" in out, "hashtag, not the settled hash fields"
    assert TOKEN not in out


def test_other_token_like_fields_are_redacted(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``token``, ``secret`` and ``apiKey`` were never seen; scrubbed, they need no review."""
    body = {
        "token": "t-value",
        "secret": "s-value",  # pragma: allowlist secret
        "apiKey": "k-value",  # pragma: allowlist secret
        "api_key": None,
    }
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/setting/read.json")
    route.mock(return_value=httpx.Response(200, json=body))
    assert recorder.main(["setting/read.json", "tokens"]) == 0
    text = (tmp_path / "tests" / "fixtures" / "setting_read" / "tokens.json").read_text()
    written = json.loads(json.loads(text)["response"]["body"])
    assert written == {
        "token": "REDACTED",
        "secret": "REDACTED",  # pragma: allowlist secret
        "apiKey": "REDACTED",  # pragma: allowlist secret
        "api_key": None,
    }
    out = capsys.readouterr().out
    assert "review" not in out, "a settled token-like field is no mention to review"
    assert "value" not in out.replace("REDACTED", "")


ESCAPED_40 = "Xy" * 20  # 40 characters, longer than the observed hash


@pytest.mark.parametrize(
    ("content", "name"),
    [
        (
            ('{"success": true, "data": {"h\\u0061sh": "' + ESCAPED_40 + '"}}').encode(),
            "hash",
        ),
        (json.dumps({"data": {"hash": [TOKEN, "Zx" * 16]}}).encode(), "hash"),
        (json.dumps({"data": {"token": {"value": TOKEN}}}).encode(), "token"),
        (json.dumps({"data": {"Secret": 7731}}).encode(), "Secret"),
    ],
    ids=["escaped-name-40-characters", "array-under-hash", "object-under-token", "number"],
)
def test_a_value_the_scrub_cannot_reach_is_never_written(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    content: bytes,
    name: str,
) -> None:
    """The raw-text scrub takes text values under the plain name; the check refuses the rest.

    An escaped field name hides ``hash`` from the scrub, and an array, an object or a
    number is no text to replace: anything but ``null`` or ``REDACTED`` writes nothing.
    """
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/order/read.json")
    route.mock(return_value=httpx.Response(200, content=content))
    assert recorder.main(["order/read.json", "unreachable"]) == 1
    assert not (tmp_path / "tests" / "fixtures" / "order_read").exists()
    out = capsys.readouterr().out
    assert f"a value other than null or REDACTED under {name}" in out
    for hidden in (ESCAPED_40, TOKEN, "Zx" * 16, "7731"):
        assert hidden not in out


def test_a_compound_name_goes_to_review(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``publicHash`` is not a token-like name to scrub, but ``hash`` is key-like: review."""
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/order/read.json")
    route.mock(return_value=httpx.Response(200, json={"data": {"publicHash": TOKEN}}))
    assert recorder.main(["order/read.json", "compound"]) == 1
    assert (tmp_path / "tests" / "fixtures" / "order_read" / "compound.json").exists()
    out = capsys.readouterr().out
    assert "review" in out
    assert "response body mentions 'hash'" in out
    assert TOKEN not in out


@pytest.mark.parametrize(
    ("body", "refused"),
    [
        ({"hash": TOKEN}, True),
        ({"data": [{"Token": TOKEN}]}, True),
        ({"hash": TOKEN.lower()}, True),
        ({"hash": TOKEN[:31]}, True),
        ({"hash": ""}, True),
        ({"hash": "redacted"}, True),
        ({"apiKey": 1}, True),
        ({"hash": ["REDACTED"]}, True),
        ({"token": {}}, True),
        ({"hash": "REDACTED"}, False),
        ({"hash": None}, False),
        ({"hashtag": TOKEN}, False),
        ({"publicHash": TOKEN}, False),
    ],
    ids=[
        "hash",
        "nested-token",
        "one-case",
        "31-characters",
        "empty",
        "lower-case-marker",
        "number",
        "array",
        "object",
        "scrubbed",
        "null",
        "other-name",
        "compound-name",
    ],
)
def test_the_check_refuses_anything_but_null_or_redacted_under_a_token_like_name(
    recorder: ModuleType, body: dict[str, Any], refused: bool
) -> None:
    leaks, _ = recorder.check(fixture_text(body=json.dumps(body)), REAL, KEY)
    marker = "a value other than null or REDACTED under "
    assert any(leak.startswith(marker) for leak in leaks) is refused
    assert all(TOKEN not in leak and TOKEN.lower() not in leak for leak in leaks)


def test_a_settled_token_like_field_needs_no_review(recorder: ModuleType) -> None:
    body = json.dumps({"hash": "REDACTED", "Token": None, "notes": "no key-like word"})
    assert recorder.check(fixture_text(body=body), REAL, KEY) == ([], [])
    _, suspicions = recorder.check(fixture_text(body=json.dumps({"publicHash": "x"})), REAL, KEY)
    assert suspicions == ["response body mentions 'hash'"]


def test_every_committed_fixture_passes_the_final_check(recorder: ModuleType) -> None:
    """The recorded fixtures hold no tag, address or credential the check would refuse."""
    fixtures = sorted((Path(__file__).parent / "fixtures").glob("*/*.json"))
    assert len(fixtures) == 23
    for path in fixtures:
        assert recorder.check(path.read_text(encoding="utf-8"), "demo", "") == ([], []), path.name
