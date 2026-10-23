"""The fixture recorder records the demo organisation only and never writes its host or key.

It also holds to the policies that stand until the demo organisation is confirmed
synthetic: GET only, .json only, the allowed modules only, no non-zero amount, no e-mail
address.
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
KEY = "real-key-for-the-test"  # pragma: allowlist secret


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
        return_value=httpx.Response(200, json={"token": "abc"}, headers={"X-Csrf-Token": "abc"})
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
    assert (args.method, args.allow_amounts) == ("GET", False)
    assert recorder.parse_args(["account/list.json", "case", "--allow-amounts"]).allow_amounts


# Policies until the demo organisation is confirmed synthetic.


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
                "createdBy": "Jane.Doe+books@corp.example.ch",
                "lastUpdatedBy": "SYSTEM",
                "notes": "<p>ask\nhans.muster@beispiel.ch or <a href='mailto:x@y.org'>x</a></p>",
            }
        ],
    }
    route.mock(
        return_value=httpx.Response(200, json=body, headers={"X-Contact": "ops@corp.example.ch"})
    )
    assert recorder.main(["account/list.json", "with_users", "query=jane@corp.example.ch"]) == 0
    text = (tmp_path / "tests" / "fixtures" / "account_list" / "with_users.json").read_text()
    for gone in ("Jane.Doe", "hans.muster", "beispiel", "corp.example", "x@y.org", "jane"):
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
    route.mock(return_value=httpx.Response(200, content=b'{"notes": "\\u00e9mile@corp.ch"}'))
    assert recorder.main(["account/list.json", "escaped"]) == 1
    assert not (tmp_path / "tests" / "fixtures" / "account_list").exists()
    out = capsys.readouterr().out
    assert "not written" in out
    assert "an e-mail address other than user@example.com" in out
    assert "corp.ch" not in out


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
        fixture("https://demo.cashctrl.com/api/v1/x.json?q=a%40b.ch", [], "{}"),
        fixture("https://demo.cashctrl.com/", [["x-user", "a@b.ch"]], "{}"),
        fixture("https://demo.cashctrl.com/", [], '{"createdBy": "a@b.ch"}'),
        fixture("https://demo.cashctrl.com/", [], "plain text from a@b.ch"),
    ):
        leaks, _ = recorder.check(leaky, REAL, KEY)
        assert leaks == ["an e-mail address other than user@example.com"]


@pytest.mark.parametrize(
    ("body", "where"),
    [
        ({"total": 1, "data": [{"id": 1, "endAmount": 12.5}]}, "body.data[0].endAmount"),
        ({"data": {"openingAmount": 0, "targetMax": "1000.00"}}, "body.data.targetMax"),
        ({"data": [{"balance": [0, -3]}]}, "body.data[0].balance"),
        (
            {"data": [{"lines": [{"DEFAULTCURRENCYAMOUNT": 1}]}]},
            "body.data[0].lines[0].DEFAULTCURRENCYAMOUNT",
        ),
    ],
)
def test_a_non_zero_amount_is_refused(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    body: dict[str, Any],
    where: str,
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(return_value=httpx.Response(200, json=body))
    assert recorder.main(["account/list.json", "amounts"]) == 1
    assert not (tmp_path / "tests" / "fixtures").exists()
    out = capsys.readouterr().out
    assert out.startswith("not recorded: the body holds non-zero amounts under ")
    assert where in out
    assert "--allow-amounts is only for a synthetic demo organisation" in out
    for value in ("12.5", "1000", "-3"):
        assert value not in out


def test_zero_amounts_totals_rates_percentages_and_ids_are_recorded(
    recorder: ModuleType, tmp_path: Path, respx_mock: respx.MockRouter
) -> None:
    record = {
        "id": 7,
        "accountId": 33,
        "costCenterIds": [4, 5],
        "amountId": 9,
        "openingAmount": 0,
        "endAmount": 0.0,
        "defaultCurrencyEndAmount": "0.00",
        "targetMin": None,
        "isBalanceSheet": True,
        "rate": 0.925822,
        "percentage": 8.1,
        "percentageFlat": 6.2,
        "currentPercentage": 8.1,
        "rates": [{"percentage": 8.1}],
    }
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(return_value=httpx.Response(200, json={"total": 12, "data": [record]}))
    assert recorder.main(["account/list.json", "no_amounts"]) == 0
    assert (tmp_path / "tests" / "fixtures" / "account_list" / "no_amounts.json").exists()


def test_allow_amounts_lifts_the_amount_policy_only(
    recorder: ModuleType, tmp_path: Path, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(f"https://{REAL}.cashctrl.com/api/v1/account/list.json")
    route.mock(return_value=httpx.Response(200, json={"data": [{"endAmount": 12.5}]}))
    assert recorder.main(["account/list.json", "synthetic", "--allow-amounts"]) == 0
    assert (tmp_path / "tests" / "fixtures" / "account_list" / "synthetic.json").exists()
    assert recorder.main(["journal/list.json", "synthetic", "--allow-amounts"]) == 1
    assert recorder.main(["account/list.json", "x", "--allow-amounts", "--method", "POST"]) == 1


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
        "person/list.json",
        "person/contact/list.json",
        "order/document/list.json",
        "journal/list.json",
        "salary/statement/list.json",
        "report/collection/read.json",
        "file/list.json",
        "inventory/asset/list.json",
        "location/list.json",
        "history/list.json",
        "customfield/list.json",
        "rounding/list.json",
        "sequencenumber/list.json",
        "setting/read.json",
        "text/list.json",
        "domain/list.json",
    ],
)
def test_every_module_but_the_allowed_ones_fails_closed(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    endpoint: str,
) -> None:
    assert recorder.main([endpoint, "refused", "id=1"]) == 1
    assert not respx_mock.calls, "refused before any request"
    assert not (tmp_path / "tests" / "fixtures").exists()
    out = capsys.readouterr().out
    module = endpoint.split("/")[0]
    assert out.startswith(
        f"not recorded: {module}/ is not yet cleared for recording from the demo organisation; "
        "only account, currency, fiscalperiod and tax are "
    )
    assert "locations carry the company's address and VAT number" in out
    assert "until the demo organisation is confirmed synthetic" in out


@pytest.mark.parametrize(
    "endpoint", ["account/bank/list.json", "account/bank/read.json", "account/bank.json"]
)
def test_bank_accounts_are_refused_within_account(
    recorder: ModuleType,
    tmp_path: Path,
    respx_mock: respx.MockRouter,
    capsys: pytest.CaptureFixture[str],
    endpoint: str,
) -> None:
    assert recorder.main([endpoint, "bank"]) == 1
    assert not respx_mock.calls, "refused before any request"
    assert not (tmp_path / "tests" / "fixtures").exists()
    out = capsys.readouterr().out
    assert (
        out == "not recorded: account/bank/ is refused: bank accounts carry IBAN, BIC and QR-IBAN\n"
    )


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
        "account/read.json",
        "account/category/list.json",
        "account/costcenter/list.json",
        "currency/list.json",
        "fiscalperiod/list.json",
        "tax/list.json",
    ],
)
def test_the_allowed_modules_are_one_list(recorder: ModuleType, endpoint: str) -> None:
    assert recorder.ALLOWED_MODULES == ("account", "currency", "fiscalperiod", "tax")
    assert recorder.REFUSED_PATHS == ("account/bank",)
    assert recorder.refusal("GET", endpoint) is None


@pytest.mark.parametrize(
    "written",
    [
        "jane&#64;corp.ch",
        "jane&#064;corp.ch",
        "jane&#x40;corp.ch",
        "jane&#X40;corp.ch",
        "jane&commat;corp.ch",
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
    assert "corp.ch" not in text
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
