"""The demo seeder refuses unsafe states before any write and encodes writes as documented.

Offline only: a stateful fake of the upstream answers through respx, and the pace is
zero. The fake subdomain, key and owner e-mail must never reach the output.
"""

import base64
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from email import policy
from email.parser import BytesParser
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
import respx

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo.py"
SUB = "fakesub7x"
KEY = "fake-key-for-the-seed-test-0123456789"  # pragma: allowlist secret (a test value)
TOKEN = base64.b64encode(f"{KEY}:".encode()).decode("ascii")
OWNER = "owner@organisation-owner.test"
NUMBERS = ("1020", "1100", "2000", "2800", "3200", "4200", "6000", "6500", "6940")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
CURRENT_PERIOD = 1
"""The fake's current fiscal period, 2026: lists without ``fiscalPeriodId`` answer for it."""


def load_seeder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("seed_demo", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


seeder = load_seeder()
ENV = {seeder.SUBDOMAIN_ENV: SUB, seeder.API_KEY_ENV: KEY}


def _list(records: list[dict[str, Any]]) -> httpx.Response:
    return httpx.Response(200, json={"total": len(records), "data": records})


def _total(total: int) -> httpx.Response:
    return httpx.Response(200, json={"total": total, "data": []})


def _localized(de: str, en: str) -> str:
    return f"<values><de>{de}</de><en>{en}</en></values>"


class FakeCashCtrl:
    """Just enough of one organisation for the seeder: lists, creates and their counts."""

    def __init__(self) -> None:
        self.org_name: str | None = "Muster Handel AG Demo"
        self.existing = {"person": 0, "journal": 0, "order": 0}
        self.accounts = [
            {"id": 100 + n, "number": number, "isInactive": False, "createdBy": OWNER}
            for n, number in enumerate(NUMBERS)
        ]
        self.periods: list[dict[str, Any]] = [self._period(1, 2026)]
        self.currencies = [{"id": 1, "code": "CHF"}, {"id": 2, "code": "EUR"}]
        self.taxes: list[dict[str, Any]] = [
            {"id": 1, "code": "UN1", "components": [{"accountId": 30, "calcType": "NET"}]},
            {"id": 6, "code": "VN1"},  # no components in the list: the seeder reads tax/read.json
            {"id": 9, "code": "UN0"},
        ]
        self.tax_details: dict[int, dict[str, Any]] = {
            6: {"id": 6, "code": "VN1", "components": '[{"accountId":31,"calcType":"GROSS"}]'}
        }
        self.balances = {"2025-12-31": "0.0", "2026-09-30": "4850.0"}
        self.person_categories = [
            {"id": 1, "name": _localized("Kunden", "Customers")},
            {"id": 2, "name": _localized("Lieferanten", "Vendors")},
        ]
        self.order_categories: dict[str, list[dict[str, Any]]] = {
            "SALES": [
                {"id": 3, "nameSingular": _localized("Offerte", "Offer")},
                {"id": 4, "nameSingular": _localized("Rechnung", "Invoice")},
            ],
            "PURCHASE": [{"id": 7, "nameSingular": _localized("Bestellung", "Purchase order")}],
        }
        self.refuse: tuple[str, int] | None = None
        self.refuse_status = 200
        self.created: Counter[str] = Counter()
        self.journal_in: Counter[int] = Counter()
        self.orders_in: Counter[tuple[str, int]] = Counter()
        self.requests: list[httpx.Request] = []
        self.insert_ids: dict[str, list[int]] = defaultdict(list)
        self.next_id = 500
        self.persons: dict[int, dict[str, Any]] = {}
        self.read_without_company = False
        self.unreadable_period_after_create = False
        self.odd_ids = False
        self.refuse_headers: dict[str, str] = {}

    @staticmethod
    def _period(id_: int, year: int) -> dict[str, Any]:
        return {
            "id": id_,
            "name": str(year),
            "start": f"{year}-01-01 00:00:00.0",
            "end": f"{year}-12-31 23:59:59.0",
            "createdBy": OWNER,
        }

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.removeprefix("/api/v1/")
        if request.method == "GET":
            return self.get(path, request.url.params)
        return self.post(path, self.decode(request))

    @staticmethod
    def decode(request: httpx.Request) -> dict[str, str]:
        """The form as a servlet reads it: in the declared charset, else ISO-8859-1."""
        kind = request.headers.get("content-type", "")
        if kind.startswith("multipart/form-data"):
            return multipart_fields(request)
        charset = "utf-8" if "charset=utf-8" in kind.replace(" ", "").lower() else "iso-8859-1"
        pairs = parse_qs(request.content.decode("ascii"), encoding=charset)
        return {key: values[0] for key, values in pairs.items()}

    def get(self, path: str, params: httpx.QueryParams) -> httpx.Response:
        if path == "location/list.json":
            return _list([{"id": 1, "type": "MAIN", "orgName": self.org_name, "email": OWNER}])
        if path == "fiscalperiod/list.json":
            return _list(self.periods)
        if path == "person/list.json":
            return _total(self.existing["person"] + self.created["person/create.json"])
        if path == "person/read.json":
            record = dict(self.persons[int(params["id"])])
            if self.read_without_company:
                del record["company"]
            return httpx.Response(200, json={"success": True, "data": record})
        if path == "journal/list.json":
            period = int(params.get("fiscalPeriodId", CURRENT_PERIOD))
            return _total(self.existing["journal"] * (period == 1) + self.journal_in[period])
        if path == "order/list.json":
            period = int(params.get("fiscalPeriodId", CURRENT_PERIOD))
            existing = self.existing["order"] * (period == 1)
            return _total(existing + self.orders_in[(params["type"], period)])
        if path == "account/list.json":
            return _list(self.accounts)
        if path == "currency/list.json":
            return _list(self.currencies)
        if path == "tax/list.json":
            return _list(self.taxes)
        if path == "tax/read.json":
            return httpx.Response(
                200, json={"success": True, "data": self.tax_details[int(params["id"])]}
            )
        if path == "account/balance":
            assert params["id"] == str(
                next(a["id"] for a in self.accounts if a["number"] == "1100")
            )
            return httpx.Response(200, text=self.balances[params["date"]])
        if path == "person/category/list.json":
            return _list(self.person_categories)
        if path == "order/category/list.json":
            return _list(self.order_categories[params["type"]])
        return httpx.Response(404, text="unknown endpoint")

    def post(self, path: str, form: dict[str, str]) -> httpx.Response:
        self.created[path] += 1
        if self.refuse == (path, self.created[path]):
            self.created[path] -= 1
            body = {
                "success": False,
                "errors": [
                    {"field": "debitId", "message": f"Unknown at {SUB}.cashctrl.com, ask {OWNER}"}
                ],
            }
            return httpx.Response(self.refuse_status, json=body, headers=self.refuse_headers)
        if path == "fiscalperiod/create.json" and self.unreadable_period_after_create:
            self.periods.append({"id": 2, "name": "2025", "start": None, "end": None})
        elif path == "fiscalperiod/create.json":
            self.periods.append(self._period(2, 2025))
        elif path == "currency/create.json":
            self.currencies.append({"id": 10 + len(self.currencies), "code": form["code"]})
        elif path == "journal/create.json":
            self.journal_in[2 if form["dateAdded"].startswith("2025") else 1] += 1
        elif path == "order/create.json":
            sales = {str(c["id"]) for c in self.order_categories["SALES"]}
            order_type = "SALES" if form["categoryId"] in sales else "PURCHASE"
            self.orders_in[(order_type, 2 if form["date"].startswith("2025") else 1)] += 1
        self.next_id += 1
        self.insert_ids[path].append(self.next_id)
        insert_id: int | str = self.next_id
        if path == "person/create.json":
            self.persons[self.next_id] = {"id": self.next_id, "company": form["company"]}
        elif self.odd_ids:
            insert_id = f"{SUB}-{self.next_id} {OWNER}"
        return httpx.Response(
            200, json={"success": True, "message": "Saved", "insertId": insert_id}
        )

    def posts(self, path: str | None = None) -> list[httpx.Request]:
        return [
            r
            for r in self.requests
            if r.method == "POST" and (path is None or r.url.path == f"/api/v1/{path}")
        ]


@pytest.fixture(autouse=True)
def no_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seeder, "PACE_SECONDS", 0.0)


@contextmanager
def serving(upstream: FakeCashCtrl) -> Iterator[respx.MockRouter]:
    """Route the demo host to ``upstream``; any other host fails the test."""
    with respx.mock(assert_all_called=False) as router:
        router.route(host=f"{SUB}.cashctrl.com").mock(side_effect=upstream)
        yield router


@pytest.fixture
def fake() -> Iterator[FakeCashCtrl]:
    upstream = FakeCashCtrl()
    with serving(upstream):
        yield upstream


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    status = seeder.main(list(argv), environ=ENV)
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def multipart_fields(request: httpx.Request) -> dict[str, str]:
    """The fields of a ``multipart/form-data`` body, each part decoded as UTF-8."""
    head = f"Content-Type: {request.headers['content-type']}\r\n\r\n".encode("ascii")
    message = BytesParser(policy=policy.default).parsebytes(head + request.content)
    fields = {}
    for part in message.iter_parts():
        assert part.get_filename() is None
        assert part.get_content_type() == "text/plain"  # no Content-Type header on the part
        payload = part.get_payload(decode=True)
        assert isinstance(payload, bytes)
        fields[str(part.get_param("name", header="content-disposition"))] = payload.decode()
    return fields


def form_of(request: httpx.Request) -> dict[str, str]:
    assert request.headers["content-type"] == "application/x-www-form-urlencoded; charset=UTF-8"
    return {key: values[0] for key, values in parse_qs(request.content.decode()).items()}


# --- plan ------------------------------------------------------------------------------


def test_plan_is_the_default_and_sends_nothing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_client(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("--plan must not build a client")

    monkeypatch.setattr(seeder.httpx, "Client", no_client)
    with respx.mock() as router:
        for argv in ([], ["--plan"]):
            status, out, err = run(capsys, *argv)
            assert status == 0
            assert err == ""
            assert re.search(r"persons\s+10\s+6 customers, 4 vendors", out)
            assert re.search(r"journal entries\s+48\s+12 in 2025, 36 in 2026", out)
            assert re.search(r"orders\s+6\s+4 SALES invoices, 2 PURCHASE orders", out)
            assert re.search(r"currencies\s+2\s+EUR 0.95, USD 0.88", out)
            assert re.search(r"writes, at most\s+67", out)
            assert "Rechnung RE-2026-001 Muster Consulting GmbH" in out
            assert "info@muster-buero.example" in out
        assert router.calls.call_count == 0


def test_apply_without_yes_is_refused_without_a_request(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with respx.mock() as router:
        status, _, err = run(capsys, "--apply")
        assert router.calls.call_count == 0
    assert status == 1
    assert "--yes" in err


def test_yes_alone_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        seeder.main(["--yes"], environ=ENV)
    assert stop.value.code == 2
    capsys.readouterr()


# --- guard 1: the variables ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("environ", "named"),
    [
        ({}, ["CASHCTRL_DEMO_SUBDOMAIN", "CASHCTRL_DEMO_API_KEY"]),
        ({"CASHCTRL_DEMO_API_KEY": KEY}, ["CASHCTRL_DEMO_SUBDOMAIN"]),
        (
            {"CASHCTRL_DEMO_SUBDOMAIN": SUB, "CASHCTRL_DEMO_API_KEY": "  "},
            ["CASHCTRL_DEMO_API_KEY"],
        ),
        ({"CASHCTRL_DEMO_SUBDOMAIN": SUB, "CASHCTRL_ORGS": "real"}, ["CASHCTRL_DEMO_API_KEY"]),
    ],
)
def test_missing_variables_are_refused(
    capsys: pytest.CaptureFixture[str], environ: dict[str, str], named: list[str]
) -> None:
    with respx.mock() as router:
        status = seeder.main(["--apply", "--yes"], environ=environ)
        assert router.calls.call_count == 0
    err = capsys.readouterr().err
    assert status == 1
    assert "refused (guard 1)" in err
    for name in named:
        assert name in err
    assert SUB not in err
    assert KEY not in err


@pytest.mark.parametrize("subdomain", ["fake.sub", "fakesub.cashctrl.com", "-fakesub", "fake_sub"])
def test_the_subdomain_must_be_one_dns_label(
    capsys: pytest.CaptureFixture[str], subdomain: str
) -> None:
    environ = {seeder.SUBDOMAIN_ENV: subdomain, seeder.API_KEY_ENV: KEY}
    with respx.mock() as router:
        status = seeder.main(["--apply", "--yes"], environ=environ)
        assert router.calls.call_count == 0
    captured = capsys.readouterr()
    assert status == 1
    assert "not one DNS label" in captured.err
    assert subdomain not in captured.out + captured.err


def test_the_os_environment_is_read_when_none_is_given(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(seeder.SUBDOMAIN_ENV, raising=False)
    monkeypatch.delenv(seeder.API_KEY_ENV, raising=False)
    with respx.mock() as router:
        assert seeder.main(["--apply", "--yes"]) == 1
        assert router.calls.call_count == 0
    assert seeder.SUBDOMAIN_ENV in capsys.readouterr().err


# --- guards 2 to 4 and the lookups: refused before any write ---------------------------


@pytest.mark.parametrize("name", ["Echte Firma AG", None, ""])
def test_a_name_without_demo_is_refused_before_any_write(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str], name: str | None
) -> None:
    fake.org_name = name
    status, out, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert [r.url.path for r in fake.requests] == ["/api/v1/location/list.json"]
    assert "does not contain 'demo'" in err
    assert "nothing was written" in err
    assert "Echte Firma" not in out + err


@pytest.mark.parametrize("org_name", ["Muster Handel AG DEMO", "demo", "Testdemo GmbH"])
def test_demo_in_any_case_passes_guard_2(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str], org_name: str
) -> None:
    fake.org_name = org_name
    fake.existing["person"] = 1  # stop at guard 3, after guard 2 passed
    status, out, _ = run(capsys, "--apply", "--yes")
    assert status == 1
    assert "guard 2: the organisation's name contains 'demo'" in out


@pytest.mark.parametrize("resource", ["person", "journal", "order"])
def test_a_non_empty_organisation_is_refused_before_any_write(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str], resource: str
) -> None:
    fake.existing[resource] = 3
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "the organisation is not empty" in err
    assert f"{resource}/list.json" in err
    assert "never deletes" in err


def test_the_journal_of_every_fiscal_period_is_checked(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.periods.append(fake._period(2, 2025))
    fake.journal_in[2] = 1
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "journal/list.json fiscal period 2025 total 1" in err
    periods = [r.url.params.get("fiscalPeriodId") for r in fake.requests]
    assert {"1", "2"} <= set(periods)


def test_the_orders_of_every_fiscal_period_are_checked(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.periods.append(fake._period(2, 2025))
    fake.orders_in[("PURCHASE", 2)] = 1  # not in the current period, 2026
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "order/list.json type PURCHASE fiscal period 2025 total 1" in err
    scopes = {
        (r.url.params["type"], r.url.params["fiscalPeriodId"])
        for r in fake.requests
        if r.url.path == "/api/v1/order/list.json"
    }
    assert scopes == {("SALES", "1"), ("PURCHASE", "1"), ("SALES", "2"), ("PURCHASE", "2")}


def test_a_missing_total_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    upstream = FakeCashCtrl()
    with respx.mock(assert_all_called=False) as router:
        router.get(f"https://{SUB}.cashctrl.com/api/v1/person/list.json").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        router.route(host=f"{SUB}.cashctrl.com").mock(side_effect=upstream)
        status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert upstream.posts() == []
    assert "cannot confirm the organisation is empty" in err


def test_missing_or_inactive_account_numbers_are_refused_by_number(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.accounts = [a for a in fake.accounts if a["number"] != "6940"]
    next(a for a in fake.accounts if a["number"] == "6000")["isInactive"] = True
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "missing: 6940" in err
    assert "inactive: 6000" in err


def test_a_missing_tax_code_is_refused_listing_the_codes(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.taxes = [{"id": 1, "code": "UN1"}, {"id": 5, "code": "VR1"}]
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "no active tax code VN1" in err
    assert "UN1, VR1" in err


def test_an_order_type_without_a_matching_category_is_refused(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.order_categories["PURCHASE"] = [{"id": 8, "nameSingular": _localized("Gutschrift", "")}]
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "no PURCHASE order category" in err
    assert "id 8: gutschrift" in err


def test_no_period_for_2026_is_refused(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.periods = [fake._period(1, 2027)]
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "no fiscal period covers 2026-01-05 to 2026-09-30" in err


def test_2025_that_type_earliest_would_not_create_is_refused(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.periods = [fake._period(1, 2026), fake._period(3, 2024)]
    status, _, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.posts() == []
    assert "type EARLIEST would not create 2025" in err


def test_a_wrong_key_stops_at_the_first_read(capsys: pytest.CaptureFixture[str]) -> None:
    with respx.mock(assert_all_called=False) as router:
        route = router.route(host=f"{SUB}.cashctrl.com")
        route.mock(
            return_value=httpx.Response(401, text=f"<html>{SUB}.cashctrl.com: unauthorized</html>")
        )
        status, out, err = run(capsys, "--apply", "--yes")
        assert route.call_count == 1
    assert status == 1
    assert "HTTP 401, not JSON" in err
    assert SUB not in out + err


# --- seeding ----------------------------------------------------------------------------


def test_a_full_run_creates_everything_in_dependency_order(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, err = run(capsys, "--apply", "--yes")
    assert (status, err) == (0, "")
    writes = [r.url.path.removeprefix("/api/v1/") for r in fake.posts()]
    assert writes == (
        ["person/create.json"] * 10
        + ["currency/create.json"]
        + ["fiscalperiod/create.json"]
        + ["journal/create.json"] * 48
        + ["order/create.json"] * 6
    )
    first_write = fake.requests.index(fake.posts()[0])
    assert all(r.method == "GET" for r in fake.requests[:first_write])
    assert form_of(fake.posts("currency/create.json")[0]) == {
        "code": "USD",
        "description": "US-Dollar",
        "rate": "0.88",
    }
    assert form_of(fake.posts("fiscalperiod/create.json")[0]) == {"type": "EARLIEST"}
    assert (
        "Created: persons 10, currencies 1, fiscal periods 1, journal entries 48, orders 6" in out
    )
    for line in [
        "person/list.json: total 10",
        "journal/list.json 2025: total 12",
        "journal/list.json 2026: total 36",
        "order/list.json SALES 2026: total 4",
        "order/list.json PURCHASE 2026: total 2",
        "currency/list.json: total 3",
        "fiscalperiod/list.json: total 2",
    ]:
        assert line in out
    assert "Observed write semantics" in out
    assert "journal/create.json success answer keys: insertId, message, success" in out
    assert "insertId type: int" in out
    assert "refusals: none" in out
    assert "Saved" not in out
    assert len(fake.posts()) <= 120


def test_the_first_write_is_the_umlaut_person_read_back_byte_for_byte(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, _ = run(capsys, "--apply", "--yes")
    assert status == 0
    first = fake.posts()[0]
    assert first.url.path == "/api/v1/person/create.json"
    assert form_of(first)["company"] == "Muster Büro AG"
    assert "Muster B%C3%BCro AG".replace(" ", "+") in first.content.decode("ascii")
    check = fake.requests[fake.requests.index(first) + 1]
    assert (check.method, check.url.path) == ("GET", "/api/v1/person/read.json")
    assert check.url.params["id"] == str(fake.insert_ids["person/create.json"][0])
    assert all(r.headers["content-type"].endswith("; charset=UTF-8") for r in fake.posts())
    assert "person 1/10 Muster Büro AG: read back byte for byte" in out
    assert "UTF-8 round trip: person/read.json answers company 'Muster Büro AG' byte for" in out


def test_a_garbled_umlaut_stops_before_any_further_write(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Without the declared charset the fake decodes as a servlet does, in ISO-8859-1.
    monkeypatch.setattr(seeder, "FORM_CONTENT_TYPE", "application/x-www-form-urlencoded")
    status, out, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert len(fake.posts()) == 1
    last = fake.requests[-1]
    assert (last.method, last.url.path) == ("GET", "/api/v1/person/read.json")
    assert (
        "stopped at person 1/10 Muster Büro AG: the backend garbled UTF-8: sent 'Muster Büro AG', "
        "person/read.json answers 'Muster BÃ¼ro AG'"
    ) in err
    assert "no further request was sent" in err
    assert "Created: persons 1, currencies 0, fiscal periods 0, journal entries 0" in out
    assert "UTF-8 round trip: garbled: sent 'Muster B\\xfcro AG'" in out
    assert "answered 'Muster B\\xc3\\xbcro AG'" in out


def test_a_read_back_without_company_stops_before_any_further_write(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.read_without_company = True
    status, out, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert len(fake.posts()) == 1
    assert fake.requests[-1].url.path == "/api/v1/person/read.json"
    assert "answered no company, so the UTF-8 round trip cannot be checked" in err
    assert "Created: persons 1," in out
    assert "UTF-8 round trip: not checked: person/read.json answered no company" in out


def test_calc_types_are_printed_before_any_write_and_the_balance_after(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    status, out, _ = run(capsys, "--apply", "--yes")
    assert status == 0
    lines = out.splitlines()
    first_write = next(i for i, line in enumerate(lines) if line.startswith("person 1/10"))
    lookups = [line for line in lines[:first_write] if line.startswith("lookup: tax code")]
    assert lookups == [
        "lookup: tax code UN1, components calcType NET (from tax/list.json)",
        "lookup: tax code VN1, components calcType GROSS (from tax/read.json)",
    ]
    read = next(r for r in fake.requests if r.url.path == "/api/v1/tax/read.json")
    assert read.url.params["id"] == "6"
    assert fake.requests.index(read) < fake.requests.index(fake.posts()[0])
    balances = [r for r in fake.requests if r.url.path == "/api/v1/account/balance"]
    assert [r.url.params["date"] for r in balances] == ["2025-12-31", "2026-09-30"]
    assert fake.requests.index(balances[0]) > fake.requests.index(fake.posts()[-1])
    assert "Balance of account 1100 (debtors), to compare with docs/demo-org.md" in out
    assert "  2025-12-31: 0.0\n  2026-09-30: 4850.0\n" in out
    assert "  tax code VN1, components calcType GROSS (from tax/read.json)" in out
    assert "  account 1100 balance at 2026-09-30: 4850.0" in out


def test_a_tax_code_without_components_anywhere_is_reported_not_guessed(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.tax_details[6] = {"id": 6, "code": "VN1"}
    status, out, _ = run(capsys, "--apply", "--yes")
    assert status == 0
    assert (
        "lookup: tax code VN1, components calcType not reported by tax/list.json or tax/read.json"
    ) in out


def test_an_existing_2025_period_is_used_not_created(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.periods.append(fake._period(2, 2025))
    fake.currencies.append({"id": 3, "code": "USD"})
    status, out, _ = run(capsys, "--apply", "--yes")
    assert status == 0
    assert fake.posts("fiscalperiod/create.json") == []
    assert fake.posts("currency/create.json") == []
    assert "journal/list.json 2025: total 12" in out


def test_persons_without_a_fitting_category_get_none(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.person_categories = [{"id": 5, "name": "Partner"}]
    status, out, _ = run(capsys, "--apply", "--yes")
    assert status == 0
    assert "none fits, persons get no category" in out
    assert all("categoryId" not in form_of(r) for r in fake.posts("person/create.json"))


@pytest.mark.parametrize(
    ("path", "nth", "what", "created"),
    [
        (
            "person/create.json",
            3,
            "person 3/10 Fiktiv Immobilien AG",
            "persons 2, currencies 0, fiscal periods 0, journal entries 0",
        ),
        ("journal/create.json", 5, "journal entry 5/48 2025-04-14", "journal entries 4, orders 0"),
        ("order/create.json", 2, "order 2/6 SALES RE-2026-102", "journal entries 48, orders 1"),
    ],
)
def test_success_false_stops_the_run_at_that_record(
    fake: FakeCashCtrl,
    capsys: pytest.CaptureFixture[str],
    path: str,
    nth: int,
    what: str,
    created: str,
) -> None:
    fake.refuse = (path, nth)
    status, out, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.requests[-1] is fake.posts(path)[nth - 1]
    assert len(fake.posts(path)) == nth
    # no second attempt in another encoding: a retry after an ambiguous answer could duplicate
    assert all(r.headers["content-type"] == seeder.FORM_CONTENT_TYPE for r in fake.posts())
    assert f"stopped at {what}" in err
    assert "success: false" in err
    assert "field 'debitId': Unknown at <subdomain>.cashctrl.com, ask <e-mail>" in err
    assert "no further request was sent" in err
    assert created in out
    assert "refusal: POST " in out
    assert '"success": false' in out


def test_a_status_other_than_200_stops_the_run(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.refuse = ("person/create.json", 1)
    fake.refuse_status = 403
    status, out, err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert fake.requests[-1] is fake.posts()[-1]
    assert "POST person/create.json answered HTTP 403" in err
    assert "POST person/create.json: HTTP 403 x1" in out


def test_a_refusal_after_the_first_write_still_prints_the_summary(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.unreadable_period_after_create = True  # the re-read after the create refuses
    status, out, err = run(capsys, "--apply", "--yes")
    assert status == 1
    last = fake.requests[-1]
    assert (last.method, last.url.path) == ("GET", "/api/v1/fiscalperiod/list.json")
    assert fake.posts()[-1].url.path == "/api/v1/fiscalperiod/create.json"
    assert (
        "stopped at fiscalperiod/list.json: a fiscal period without a readable start and end "
        "date; no further request was sent"
    ) in err
    assert "Created: persons 10, currencies 1, fiscal periods 1, journal entries 0" in out
    assert "Observed write semantics" in out
    assert "fiscalperiod/create.json success answer keys: insertId, message, success" in out


def test_multipart_is_a_manual_switch_with_the_same_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    forms: dict[str, list[dict[str, str]]] = {}
    for argv in (["--apply", "--yes"], ["--apply", "--yes", "--multipart"]):
        upstream = FakeCashCtrl()
        with serving(upstream):
            status, out, _ = run(capsys, *argv)
        assert status == 0
        kinds = {r.headers["content-type"].split(";")[0] for r in upstream.posts()}
        forms[argv[-1]] = [upstream.decode(r) for r in upstream.posts()]
        if argv[-1] == "--multipart":
            assert kinds == {"multipart/form-data"}
            assert "writes sent as: multipart/form-data" in out
            assert "person 1/10 Muster Büro AG: read back byte for byte" in out
        else:
            assert kinds == {"application/x-www-form-urlencoded"}
            assert "writes sent as: application/x-www-form-urlencoded; charset=UTF-8" in out
    assert forms["--multipart"] == forms["--yes"]
    assert forms["--multipart"][0]["company"] == "Muster Büro AG"


def test_multipart_without_apply_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        seeder.main(["--multipart"], environ=ENV)
    assert stop.value.code == 2
    assert "--multipart only changes how --apply writes" in capsys.readouterr().err


def test_writes_are_form_encoded_with_json_items_and_iso_dates(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(capsys, "--apply", "--yes")[0] == 0
    accounts = {a["number"]: a["id"] for a in fake.accounts}
    person_ids = [str(i) for i in fake.insert_ids["person/create.json"]]
    assert len(person_ids) == 10

    journal = [form_of(r) for r in fake.posts("journal/create.json")]
    assert all(DAY.fullmatch(form["dateAdded"]) for form in journal)

    invoice = journal[1]
    assert invoice == {
        "dateAdded": "2025-02-03",
        "title": "Rechnung RE-2025-001 Muster Consulting GmbH",
        "debitId": str(accounts["1100"]),
        "creditId": str(accounts["3200"]),
        "amount": "4800.00",
        "taxId": "1",
        "associateId": invoice["associateId"],
        "reference": "RE-2025-001",
    }
    assert invoice["associateId"] == person_ids[4]  # Muster Consulting GmbH

    collective = next(
        form for form in journal if form["title"].startswith("Sammelzahlung Debitoren")
    )
    assert set(collective) == {"dateAdded", "title", "items"}
    assert collective["dateAdded"] == "2026-04-09"
    items = json.loads(collective["items"])
    assert items[0] == {
        "accountId": accounts["1020"],
        "debit": 10000,
        "description": "Zahlungseingang",
    }
    assert items[1]["accountId"] == accounts["1100"]
    assert items[1]["credit"] == 7500
    assert items[1]["associateId"] == int(person_ids[5])  # Beispiel Logistik AG, a JSON number

    orders = [form_of(r) for r in fake.posts("order/create.json")]
    sales, purchase = orders[0], orders[4]
    assert sales["categoryId"] == "4"
    assert purchase["categoryId"] == "7"
    assert sales["date"] == "2026-03-02"
    assert all(DAY.fullmatch(form["date"]) for form in orders)
    assert sales["nr"] == "RE-2026-101"
    assert sales["associateId"] == person_ids[4]
    assert json.loads(sales["items"]) == [
        {
            "accountId": accounts["3200"],
            "name": "Beratung",
            "description": "Planung Büroeinrichtung, Stundenansatz",
            "quantity": 12,
            "unitPrice": 150,
            "taxId": 1,
        },
        {
            "accountId": accounts["3200"],
            "name": "Spesenpauschale",
            "description": "Anfahrt und Unterlagen",
            "quantity": 1,
            "unitPrice": 250,
            "taxId": 1,
        },
    ]
    assert {item["taxId"] for item in json.loads(purchase["items"])} == {6}
    assert {item["accountId"] for item in json.loads(purchase["items"])} == {accounts["4200"]}

    vendor = form_of(fake.posts("person/create.json")[0])
    assert vendor == {
        "company": "Muster Büro AG",
        "isVendor": "true",
        "language": "DE",
        "categoryId": "2",
        "addresses": vendor["addresses"],
        "contacts": vendor["contacts"],
    }
    assert json.loads(vendor["addresses"]) == [
        {
            "type": "MAIN",
            "address": "Beispielring 9",
            "zip": "9000",
            "city": "St. Gallen",
            "canton": "SG",
            "country": "CHE",
        }
    ]
    assert json.loads(vendor["contacts"]) == [
        {"type": "EMAIL_WORK", "address": "info@muster-buero.example"}
    ]
    customer = form_of(fake.posts("person/create.json")[4])
    assert customer["company"] == "Muster Consulting GmbH"
    assert customer["isCustomer"] == "true"
    assert customer["categoryId"] == "1"
    assert json.loads(customer["addresses"])[0]["city"] == "Zürich"


def test_every_request_sends_basic_auth_and_the_user_agent(
    fake: FakeCashCtrl, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(capsys, "--apply", "--yes")[0] == 0
    assert fake.requests
    for request in fake.requests:
        assert request.headers["authorization"] == f"Basic {TOKEN}"
        assert request.headers["user-agent"] == "xippios-cashctrl-seed"
        assert request.url.scheme == "https"
        assert request.url.host == f"{SUB}.cashctrl.com"


def test_the_subdomain_key_and_e_mail_never_reach_the_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    texts: list[str] = []
    upstream = FakeCashCtrl()
    with serving(upstream):
        texts += run(capsys, "--apply", "--yes")[1:]  # a full run
        texts += run(capsys, "--apply", "--yes")[1:]  # refused: no longer empty
    for path in ("person/create.json", "journal/create.json", "order/create.json"):
        refusing = FakeCashCtrl()
        refusing.refuse = (path, 1)
        with serving(refusing):
            texts += run(capsys, "--apply", "--yes")[1:]
    shown = "\n".join(texts).lower()
    assert "<subdomain>" in shown
    assert "<e-mail>" in shown
    for secret in (SUB, KEY, TOKEN, OWNER):
        assert secret.lower() not in shown


def test_insert_ids_calc_types_balances_and_refusal_headers_are_shown_scrubbed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    upstream = FakeCashCtrl()
    upstream.odd_ids = True
    upstream.taxes[0]["components"] = [{"calcType": f"NET {SUB}"}]
    upstream.balances["2025-12-31"] = f"0.0 {OWNER} {KEY}"
    with serving(upstream):
        status, out, err = run(capsys, "--apply", "--yes")
    assert status == 0
    assert "lookup: tax code UN1, components calcType NET <subdomain> (from tax/list.json)" in out
    assert "  2025-12-31: 0.0 <e-mail> <key>" in out
    assert 'journal entry 1/48 2025-01-06 Einzahlung Aktienkapital: insertId "<subdomain>-' in out
    assert re.search(r'order 6/6 PURCHASE EK-2026-002: insertId "<subdomain>-\d+ <e-mail>"', out)
    assert (
        "journal/create.json success answer keys: insertId, message, success; insertId type: str"
        in out
    )

    refusing = FakeCashCtrl()
    refusing.refuse = ("journal/create.json", 1)
    refusing.refuse_headers = {"content-type": f"application/json; origin={SUB}.cashctrl.com"}
    with serving(refusing):
        status, more_out, more_err = run(capsys, "--apply", "--yes")
    assert status == 1
    assert (
        "refusal: POST journal/create.json: HTTP 200, application/json; origin=<subdomain>"
        in more_out
    )
    shown = "\n".join([out, err, more_out, more_err]).lower()
    for secret in (SUB, KEY, TOKEN, OWNER):
        assert secret.lower() not in shown


def test_the_scrubber_hides_values_in_any_case_and_keeps_example_addresses() -> None:
    scrub = seeder.Scrubber(seeder.Credentials(subdomain=SUB, key=KEY))
    text = f"https://{SUB.upper()}.cashctrl.com {KEY} {TOKEN} {OWNER} a%40b.test info@x.example"
    assert scrub(text) == (
        "https://<subdomain>.cashctrl.com <key> <key> <e-mail> <e-mail> info@x.example"
    )
    assert SUB not in repr(seeder.Credentials(subdomain=SUB, key=KEY))
    assert KEY not in repr(seeder.Credentials(subdomain=SUB, key=KEY))


def test_the_pacer_keeps_one_second_between_requests() -> None:
    now = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    pacer = seeder.Pacer(1.0, clock=lambda: now[0], sleep=sleep)
    pacer.wait()
    now[0] += 0.25
    pacer.wait()
    now[0] += 3.0
    pacer.wait()
    assert slept == [0.75]


# --- the synthetic books ------------------------------------------------------------------


def test_the_books_are_small_balanced_and_fictional() -> None:
    entries = seeder.all_entries()
    assert len(seeder.PERSONS) == 10
    assert sum(p.role == "customer" for p in seeder.PERSONS) == 6
    assert len(seeder.ENTRIES_2025) == 12
    assert len(seeder.ENTRIES_2026) == 36
    assert len(seeder.ORDERS) == 6
    assert seeder.max_writes() <= 120
    assert all(p.email.endswith(".example") for p in seeder.PERSONS)
    assert len({p.email for p in seeder.PERSONS}) == 10
    assert all(p.company.endswith((" AG", " GmbH", " SA")) for p in seeder.PERSONS)
    names = [seeder.COMPANY] + [p.company for p in seeder.PERSONS]
    assert all(name.split()[0] in seeder.PLACEHOLDER_MARKERS for name in names)
    assert {name.split()[0] for name in names} == set(seeder.PLACEHOLDER_MARKERS)
    keys = {p.key for p in seeder.PERSONS}
    for entry in entries:
        assert len(entry.title) <= 250
        if entry.lines:
            debit = sum((line.debit or Decimal(0) for line in entry.lines), Decimal(0))
            credit = sum((line.credit or Decimal(0) for line in entry.lines), Decimal(0))
            assert debit == credit > 0
            assert all((line.debit is None) != (line.credit is None) for line in entry.lines)
            assert {line.associate for line in entry.lines} - {None} <= keys
        else:
            assert entry.amount is not None
            assert entry.amount > 0
            assert entry.debit != entry.credit
            assert entry.associate is None or entry.associate in keys
    assert all(entry.day.year == 2025 for entry in seeder.ENTRIES_2025)
    assert all(date(2026, 1, 1) <= entry.day <= date(2026, 9, 30) for entry in seeder.ENTRIES_2026)
    for order in seeder.ORDERS:
        assert order.day.year == 2026
        assert order.associate in keys
        assert 1 <= len(order.items) <= 3
        role = "customer" if order.type == "SALES" else "vendor"
        assert next(p for p in seeder.PERSONS if p.key == order.associate).role == role
    assert seeder.account_numbers() == list(NUMBERS)


def test_the_document_describes_every_record() -> None:
    doc = (SCRIPT.parents[1] / "docs" / "demo-org.md").read_text(encoding="utf-8")
    for person in seeder.PERSONS:
        assert f"| {person.company} | {person.address} |" in doc
        assert f"`{person.email}`" in doc
    for entry in seeder.all_entries():
        assert f"| {entry.day} |" in doc
        assert f"| {entry.title} |" in doc
    for order in seeder.ORDERS:
        assert f"| {order.type} | {order.nr} | {order.day} |" in doc
    for number in seeder.account_numbers():
        assert f"| {number} |" in doc
    for currency in seeder.CURRENCIES:
        assert f"| {currency.code} | {currency.description} | {currency.rate} |" in doc
    assert f"at most {seeder.max_writes()}" in doc
    assert "## Observed write semantics (filled by the first run)" in doc
    prose = " ".join(doc.split())
    rule = re.search(
        r"every company name carries a placeholder marker as its first word \(([^)]*)\)", prose
    )
    assert rule is not None
    assert rule.group(1) == ", ".join(seeder.PLACEHOLDER_MARKERS)
