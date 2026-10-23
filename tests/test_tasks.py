"""Structural checks every task must satisfy. Per-task tests with recorded fixtures go below."""

import base64
import inspect
import json
import os
import re
import typing
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx
from mcp.server.mcpserver.exceptions import ToolError
from xippios.core import InvalidRequestError, NotFoundError, sync
from xippios.core.testing import fixture_path, load_fixture, mcp_call

from xippios.cashctrl import __version__, api, tasks, tasks_write
from xippios.cashctrl._client import DEMO, api_key_env, client_for
from xippios.cashctrl.mcp import server
from xippios.cashctrl.models import (
    Account,
    Filter,
    JournalItem,
    OrderItem,
    PersonAddress,
    PersonDetail,
)

SHELL_KEY = os.environ.get(api_key_env(DEMO))
"""The demo key the shell held when the tests were collected, before any fixture; never printed."""
CONFTEST = Path(__file__).with_name("conftest.py")
LIST_URL = "https://demo.cashctrl.com/api/v1/fiscalperiod/list.json"

TASKS = [getattr(tasks, name) for name in tasks.__all__]
EVERY_TASK: dict[str, Callable[..., object]] = {
    f"{module.__name__.rsplit('.', 1)[-1]}.{name}": getattr(module, name)
    for module in (tasks, tasks_write)
    for name in module.__all__
}


def test_package_has_a_version() -> None:
    assert __version__


def basic_user(request: httpx.Request) -> str:
    """The basic auth user name of ``request``, where CashCtrl expects the key."""
    encoded = request.headers.get("Authorization", "").removeprefix("Basic ")
    return base64.b64decode(encoded).decode().partition(":")[0]


def carries(request: httpx.Request, key: str) -> bool:
    """Whether ``key``, plain or as a basic auth token, is anywhere in ``request``.

    Only the answer leaves this function, so no test frame ever holds the key or its token
    in a local that ``pytest -l`` could print.
    """
    token = base64.b64encode(f"{key}:".encode()).decode()
    outgoing = [str(request.url), *request.headers.values(), basic_user(request)]
    outgoing.append(request.content.decode())
    return any(key in part or token in part for part in outgoing)


@pytest.mark.anyio
async def test_replay_tests_send_the_placeholder_key(
    demo_only: str | None, respx_mock: respx.MockRouter
) -> None:
    """A request through the registry outside a live test carries the placeholder only.

    The demo client is ``client_for("demo")``; the shell's ``CASHCTRL_DEMO_API_KEY``, if
    direnv loaded one, appears nowhere in the request, neither plain nor as the basic auth
    token. Every assertion is on a boolean, so a failure says where the key went, never
    the key.
    """
    assert demo_only is not None
    variable = api_key_env(DEMO)
    env_holds_placeholder = os.environ[variable] == demo_only
    assert env_holds_placeholder, f"{variable} does not hold the placeholder"
    route = respx_mock.get(LIST_URL).respond(200, json={"total": 0, "data": []})
    await client_for(DEMO).get_json("/fiscalperiod/list.json")
    sent = route.calls.last.request
    sends_placeholder = basic_user(sent) == demo_only
    assert sends_placeholder, "the basic auth user name does not carry the placeholder"
    if SHELL_KEY and demo_only != SHELL_KEY:
        leaked = carries(sent, SHELL_KEY)
        assert not leaked, f"the key in {variable} went out with the request"


# Run by pytester in a subprocess, with this repository's conftest: a live test caches a
# key in the demo client's auth, then an offline test sends a request. The live run uses
# the replay host too, so a client the live test left in the cache would be handed to the
# offline test as it is: only the conftest's reset_clients() keeps the key away.
LIVE_THEN_OFFLINE = f"""
import base64

import httpx
import pytest
import respx

from xippios.cashctrl._client import DEMO, client_for

LIVE_KEY = "key-a-live-test-cached"  # pragma: allowlist secret
URL = "{LIST_URL}"


def user(request: httpx.Request) -> str:
    encoded = request.headers["Authorization"].removeprefix("Basic ")
    return base64.b64decode(encoded).decode().partition(":")[0]


@pytest.mark.live
@pytest.mark.anyio
async def test_1_live(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(URL).respond(200, json={{"total": 0, "data": []}})
    await client_for(DEMO).get_json("/fiscalperiod/list.json")
    assert user(route.calls.last.request) == LIVE_KEY


@pytest.mark.anyio
async def test_2_offline(respx_mock: respx.MockRouter, demo_only: str | None) -> None:
    route = respx_mock.get(URL).respond(200, json={{"total": 0, "data": []}})
    await client_for(DEMO).get_json("/fiscalperiod/list.json")
    sent = route.calls.last.request
    assert user(sent) == demo_only == "placeholder-for-fixture-replay"
    assert LIVE_KEY not in str(sent.headers)
"""


@pytest.mark.parametrize("reset", [True, False], ids=["conftest", "without-reset"])
def test_a_key_a_live_test_cached_never_reaches_the_next(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, reset: bool
) -> None:
    """The cached auth of a live test's client cannot carry its key into an offline test.

    ``conftest.py`` drops every cached client before and after each test; with those
    calls removed, the same two tests fail, so the check is not vacuous. No network: the
    inner tests are respx-mocked, and the live gate is opened with a made-up demo pair.
    """
    conftest = CONFTEST.read_text(encoding="utf-8")
    if not reset:
        assert conftest.count("    reset_clients()\n") == 2
        conftest = conftest.replace("    reset_clients()\n", "    pass\n")
    pytester.makeconftest(conftest)
    pytester.makepyfile(test_live_then_offline=LIVE_THEN_OFFLINE)
    monkeypatch.setenv("XIPPIOS_LIVE_TESTS", "1")
    monkeypatch.setenv(api_key_env(DEMO), "key-a-live-test-cached")  # pragma: allowlist secret
    outcome = pytester.runpytest_subprocess("-p", "no:cacheprovider", "-q")
    if reset:
        outcome.assert_outcomes(passed=2)
    else:
        outcome.assert_outcomes(passed=1, failed=1)
        outcome.stdout.fnmatch_lines(["FAILED test_live_then_offline.py::test_2_offline - *"])


def org_comes_first(fn: Callable[..., object]) -> bool:
    """``org: str`` is the first parameter, positional and without a default."""
    parameters = list(inspect.signature(fn).parameters.values())
    if not parameters:
        return False
    first = parameters[0]
    return (
        first.name == "org"
        and typing.get_type_hints(fn).get("org") is str
        and first.default is inspect.Parameter.empty
        and first.kind in (first.POSITIONAL_ONLY, first.POSITIONAL_OR_KEYWORD)
    )


def test_the_org_check_tells_good_from_bad() -> None:
    def good(org: str, fiscal_period_id: int | None = None) -> None: ...
    def second(fiscal_period_id: int, org: str) -> None: ...
    def optional(org: str = "demo") -> None: ...
    def untyped(org) -> None: ...  # type: ignore[no-untyped-def]
    def keyword_only(*, org: str) -> None: ...
    def no_parameters() -> None: ...
    async def read_account_async(org: str, id: int) -> None: ...

    assert org_comes_first(good)
    assert org_comes_first(sync(read_account_async)), "tasks are sync() facades"
    for bad in (second, optional, untyped, keyword_only, no_parameters):
        assert not org_comes_first(bad), bad.__name__


@pytest.mark.parametrize("task", EVERY_TASK.values(), ids=EVERY_TASK.keys())
def test_every_task_takes_org_first(task: Callable[..., object]) -> None:
    assert org_comes_first(task), "org: str is the first, required parameter of every task"


@pytest.mark.parametrize("task", TASKS, ids=tasks.__all__)
def test_task_is_a_sync_facade_with_an_agent_docstring(task: object) -> None:
    assert callable(task)
    assert hasattr(task, "async_fn"), "write the async function and derive the sync one with sync()"
    doc = inspect.getdoc(task) or ""
    assert doc, "task functions need a docstring: agents read it"
    assert doc.splitlines()[0].endswith("."), "the first line is one sentence"
    if inspect.signature(task).parameters:
        assert "Args:" in doc, "explain every parameter under Args: with valid-value examples"


# Per-task tests. Every fixture was recorded on 2026-10-23 from the demo organisation, whose
# books are synthetic: CashCtrl's defaults plus what scripts/seed_demo.py wrote.


def test_list_fiscal_periods_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("fiscalperiod_list", "default")
    result = tasks.list_fiscal_periods(DEMO)
    assert not route.calls.last.request.url.params, "the operation documents no parameters"
    assert result.meta.source == "cashctrl"
    assert result.meta.endpoint == "fiscalperiod/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.published_at, result.meta.vintage) == (None, None)
    assert result.meta.total == 2, "upstream's total (ADR-0012)"
    assert [(period.id, period.name) for period in result.data] == [(2, "2025"), (1, "2026")]
    first = result.data[0]  # created by the seeder, as the API user
    assert (first.start, first.end) == (date(2025, 1, 1), date(2025, 12, 31)), "date part kept"
    assert first.salary_end == date(2025, 12, 31)
    assert first.last_entry_date == datetime(2025, 12, 15), "undocumented: kept a datetime"
    assert first.created == datetime(2026, 10, 23, 10, 29, 24)
    assert first.created_by == "API:REDACTED", "the recorder scrubs the API user tag"
    assert (first.is_closed, first.closed_month_ids) == (False, [])
    assert first.open_month_ids[:2] == ["2025-01", "2025-02"]
    assert len(first.open_month_ids) == 12
    assert result.data[1].created_by == "SYSTEM"
    assert [period.is_current for period in result.data] == [True, False]


@pytest.mark.anyio
async def test_list_fiscal_periods_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("fiscalperiod_list", "default")
    payload = await mcp_call(server, "cashctrl_list_fiscal_periods", {"org": DEMO})
    last = payload["data"][-1]
    assert "is_current" in last, "results carry the snake_case names (validation_alias)"
    assert "isCurrent" not in last, "never upstream's spelling: the adapters dump by alias"
    assert (last["id"], last["start"], last["end"], last["is_current"]) == (
        1,
        "2026-01-01",
        "2026-12-31",
        False,
    )
    assert payload["meta"]["endpoint"] == "fiscalperiod/list.json"
    assert payload["meta"]["request"] == {"org": DEMO}


def test_list_currencies_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("currency_list", "default")
    result = tasks.list_currencies(DEMO)
    assert not route.calls.last.request.url.params, "the operation documents no parameters"
    assert result.meta.endpoint == "currency/list.json"
    assert result.meta.request == {"org": DEMO}
    assert result.meta.total == 3
    assert [(c.id, c.code, c.is_default) for c in result.data] == [
        (1, "CHF", True),
        (2, "EUR", False),
        (3, "USD", False),
    ]
    chf, eur, usd = result.data
    assert isinstance(eur.rate, Decimal)
    assert (eur.rate, usd.rate) == (Decimal("0.920261"), Decimal("0.820845"))
    assert chf.rate == Decimal(1)
    assert chf.description == (
        "<values><de>Schweizer Franken</de><en>Swiss Franc</en>"
        "<fr>Franc suisse</fr><it>Franco svizzero</it></values>"
    ), "localised text kept verbatim"
    assert [(c.is_auto, c.value) for c in result.data] == [(False, "1"), (True, "2"), (True, "3")]
    assert chf.created == datetime(2026, 10, 23, 7, 6, 39)
    assert chf.created_by == "SYSTEM"


@pytest.mark.anyio
async def test_list_currencies_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("currency_list", "default")
    payload = await mcp_call(server, "cashctrl_list_currencies", {"org": DEMO})
    eur = payload["data"][1]
    assert (eur["code"], eur["rate"], eur["is_default"]) == ("EUR", 0.920261, False)
    assert payload["meta"]["endpoint"] == "currency/list.json"


def test_list_tax_codes_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("tax_list", "default")
    result = tasks.list_tax_codes(DEMO)
    assert not route.calls.last.request.url.params, "the operation documents no parameters"
    assert result.meta.endpoint == "tax/list.json"
    assert result.meta.request == {"org": DEMO}
    assert len(result.data) == result.meta.total == 20, "CashCtrl's default tax codes"
    code = next(tax for tax in result.data if tax.code == "UN1")
    assert code.id == 9
    assert code.current_percentage == Decimal("8.1")
    assert isinstance(code.current_percentage, Decimal)
    assert code.current_percentage_flat is None
    assert (code.form_codes, code.account_display) == ("200, 303", "2200")
    assert code.is_inactive is False
    (rate,) = code.rates
    assert (rate.percentage, rate.date_valid, rate.percentage_flat) == (Decimal("8.1"), None, None)
    (component,) = code.components
    assert (component.account_id, component.calc_type, component.apply_rule) == (
        33,
        "NET",
        "REVENUE",
    )
    assert component.is_input_tax is False
    both = next(tax for tax in result.data if tax.code == "BN1")
    assert [(c.account_id, c.apply_rule, c.is_input_tax) for c in both.components] == [
        (33, "CREDIT", False),
        (34, "DEBIT", True),
    ], "up to two components"
    assert both.account_display == "2200, 1170"
    assert [tax.code for tax in result.data if tax.is_inactive] == []


@pytest.mark.anyio
async def test_list_tax_codes_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("tax_list", "default")
    payload = await mcp_call(server, "cashctrl_list_tax_codes", {"org": DEMO})
    code = next(tax for tax in payload["data"] if tax["code"] == "UN1")
    assert code["rates"][0]["percentage"] == 8.1
    assert code["components"][0]["account_id"] == 33
    assert payload["meta"]["endpoint"] == "tax/list.json"


NUMBER_1020 = Filter(comparison="eq", field="number", value="1020")
UNVALIDATED = Filter.model_construct(  # built without validation, so the type is bypassed
    comparison="equals",  # type: ignore[arg-type]
    field="number",
    value="1000",
)


def recorded_query(fixtures_dir: Path, endpoint: str, case: str) -> dict[str, str]:
    """The query parameters the fixture was recorded with."""
    url = load_fixture(fixture_path(fixtures_dir, endpoint, case)).request.url
    return dict(httpx.URL(url).params)


def test_list_accounts_replays_a_narrowed_list(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_list", "only_active_finanz")
    result = tasks.list_accounts(DEMO, only_active=True, query="Finanz")
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"onlyActive": "true", "query": "Finanz"}
    assert sent == recorded_query(fixtures_dir, "account_list", "only_active_finanz")
    assert result.meta.endpoint == "account/list.json"
    assert result.meta.request == {"org": DEMO, **sent}
    assert result.meta.total == 8
    assert [account.number for account in result.data] == [
        "1400",
        "1430",
        "1440",
        "1441",
        "2120",
        "2420",
        "6900",
        "6950",
    ], "upstream's default order: by number"
    account = next(account for account in result.data if account.number == "6900")
    assert account.id == 26
    assert account.name.startswith("<values><de>Finanzaufwand</de>"), "kept verbatim"
    assert (account.category_id, account.account_class, account.currency_code) == (
        64,
        "EXPENSE",
        "CHF",
    )
    # The bank fees of 2025 (docs/demo-org.md), the period the API user has as current.
    assert isinstance(account.end_amount, Decimal)
    assert (account.opening_amount, account.end_amount) == (Decimal(0), Decimal(120))
    assert account.default_currency_end_amount == Decimal(120)
    assert (account.currency_id, account.tax_id, account.cost_center_ids) == (None, None, None)
    assert (account.is_inactive, account.is_bank_account) == (False, False)
    assert account.created == datetime(2026, 10, 23, 7, 6, 39)
    assert {a.account_class for a in result.data} == {"ASSET", "LIABILITY", "EXPENSE"}


def test_an_account_takes_currency_id_as_a_number_a_string_or_null(fixtures_dir: Path) -> None:
    """The committed entries carry ``null``; a number and a string were seen, never committed."""
    fixture = fixture_path(fixtures_dir, "account_list", "only_active_finanz")
    entry = json.loads(load_fixture(fixture).response.body)["data"][0]
    assert entry["currencyId"] is None
    for sent, parsed in (("2", 2), (2, 2), (None, None)):
        assert Account.model_validate({**entry, "currencyId": sent}).currency_id == parsed


def test_list_accounts_sends_the_filter_as_upstream_reads_it(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_list", "filter_number_eq")
    result = tasks.list_accounts(DEMO, filter=[NUMBER_1020])
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"filter": '[{"comparison":"eq","field":"number","value":"1020"}]'}
    assert sent == recorded_query(fixtures_dir, "account_list", "filter_number_eq")
    assert result.meta.request == {"org": DEMO, **sent}
    (account,) = result.data
    assert (account.id, account.number, account.is_inactive) == (3, "1020", False)
    assert (account.category_id, account.account_class) == (51, "ASSET")
    # The bank account at the end of 2025 (docs/demo-org.md): share capital, invoices paid,
    # rent, a purchase, fees; 101'230.00 in the current period, 2025.
    assert (account.opening_amount, account.end_amount) == (Decimal(0), Decimal(101230))


def test_list_accounts_takes_filters_as_mappings_too(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_list", "filter_number_eq")
    item = {"comparison": "eq", "field": "number", "value": "1020"}
    arguments: dict[str, typing.Any] = {"filter": [item]}
    result = tasks.list_accounts(DEMO, **arguments)
    sent = dict(route.calls.last.request.url.params)
    assert sent == recorded_query(fixtures_dir, "account_list", "filter_number_eq")
    assert [account.number for account in result.data] == ["1020"]
    arguments = {"filter": [{"field": "number", "value": ["1000", "1020"]}]}
    tasks.list_accounts(DEMO, **arguments)
    assert dict(route.calls.last.request.url.params) == {
        "filter": '[{"comparison":"like","field":"number","value":["1000","1020"]}]'
    }, "a mapping is validated into a Filter: upstream's default comparison is sent"


def test_the_filter_encoding_keeps_lists_and_text() -> None:
    filters = [Filter(field="name", value=["Kasse", "Büro"]), NUMBER_1020]
    assert api.encode_filter(filters) == (
        '[{"comparison":"like","field":"name","value":["Kasse","Büro"]},'
        '{"comparison":"eq","field":"number","value":"1020"}]'
    )
    assert api.account_list_params(filter=[], only_active=False, dir="DESC") == {
        "onlyActive": "false",
        "dir": "DESC",
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"dir": "up"}, "dir must be ASC or DESC, not 'up'"),
        ({"dir": "asc"}, "dir must be ASC or DESC, not 'asc'"),
        (
            {"filter": [{"comparison": "equals", "field": "number", "value": "1000"}]},
            "filter[0].comparison must be one of eq, like, gt, lt, not 'equals'",
        ),
        (
            {"filter": [UNVALIDATED]},
            "filter[0].comparison must be one of eq, like, gt, lt, not 'equals'",
        ),
        ({"filter": '[{"field": "number"}]'}, "filter takes a list of filters"),
        (
            {"filter": [{"field": "number", "value": "1000", "op": "eq"}]},
            "filter[0].op: Extra inputs are not permitted",
        ),
        ({"filter": [{"value": "1000"}]}, "filter[0].field: Field required"),
        ({"filter": [1000]}, "filter[0] must be a Filter or a mapping, not int"),
        ({"query": 1000}, "query must be a string, not int"),
        ({"sort": ["number"]}, "sort must be a string, not list"),
    ],
)
def test_list_accounts_refuses_what_upstream_would_ignore(
    respx_mock: respx.MockRouter, arguments: dict[str, typing.Any], message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks.list_accounts(DEMO, **arguments)
    assert not respx_mock.calls


def test_every_problem_is_named_at_once(respx_mock: respx.MockRouter) -> None:
    bad = {"comparison": "EQ", "field": "number", "value": 1000}
    arguments: dict[str, typing.Any] = {"dir": "down", "filter": [NUMBER_1020, bad]}
    with pytest.raises(InvalidRequestError) as info:
        tasks.list_accounts(DEMO, **arguments)
    assert str(info.value) == (
        "dir must be ASC or DESC, not 'down'; "
        "filter[1].comparison must be one of eq, like, gt, lt, not 'EQ'; "
        "filter[1].value.str: Input should be a valid string; "
        "filter[1].value.list[str]: Input should be a valid list"
    )
    assert not respx_mock.calls


@pytest.mark.anyio
async def test_the_tool_schema_shows_the_value_sets() -> None:
    tools = {tool.name: tool for tool in await server.list_tools()}
    schema = tools["cashctrl_list_accounts"].input_schema
    assert {"enum": ["ASC", "DESC"], "type": "string"} in schema["properties"]["dir"]["anyOf"]
    comparison = schema["$defs"]["Filter"]["properties"]["comparison"]
    assert (comparison["enum"], comparison["default"]) == (["eq", "like", "gt", "lt"], "like")
    assert set(schema["$defs"]["Filter"]["required"]) == {"field", "value"}


@pytest.mark.anyio
async def test_list_accounts_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_list", "filter_number_eq")
    item = {"comparison": "eq", "field": "number", "value": "1020"}
    payload = await mcp_call(server, "cashctrl_list_accounts", {"org": DEMO, "filter": [item]})
    (account,) = payload["data"]
    assert (account["number"], account["end_amount"], account["is_inactive"]) == (
        "1020",
        101230,
        False,
    )
    assert payload["meta"]["request"]["filter"] == (
        '[{"comparison":"eq","field":"number","value":"1020"}]'
    )
    # Refused by the tool's schema, before the task runs: the MCP SDK's tool error.
    bad = {"org": DEMO, "filter": [{**item, "comparison": "equals"}]}
    with pytest.raises(ToolError, match=r"filter\.0\.comparison[\s\S]*literal_error"):
        await mcp_call(server, "cashctrl_list_accounts", bad)
    with pytest.raises(ToolError, match=r"dir[\s\S]*literal_error"):
        await mcp_call(server, "cashctrl_list_accounts", {"org": DEMO, "dir": "up"})
    with pytest.raises(ToolError, match="extra_forbidden"):  # Filter refuses unknown keys
        await mcp_call(server, "cashctrl_list_accounts", {"org": DEMO, "filter": [{"op": "eq"}]})


def test_list_accounts_is_a_post_route(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    replay_fixture("account_list", "only_active_finanz")
    body = {"org": DEMO, "only_active": True, "query": "Finanz"}
    response = client.post("/cashctrl/list_accounts", json=body)
    assert response.status_code == 200, response.text
    row = response.json()["data"][0]
    assert ("end_amount" in row, "endAmount" in row) == (True, False), "snake_case over HTTP"
    numbers = [account["number"] for account in response.json()["data"]]
    assert (len(numbers), numbers[-2:]) == (8, ["6900", "6950"])
    rejected = client.post("/cashctrl/list_accounts", json={"org": DEMO, "dir": "up"})
    assert rejected.status_code == 422
    assert rejected.json()["detail"][0]["type"] == "literal_error", "FastAPI's own 422"
    unknown = client.post("/cashctrl/list_accounts", json={"org": "nowhere"})
    assert unknown.status_code == 422
    assert unknown.json()["title"] == "InvalidRequestError", "the task's refusals as problems"


def account_1020_id(fixtures_dir: Path) -> int:
    """The id of account 1020 as the filtered list recorded it: the id ``by_id`` reads."""
    fixture = load_fixture(fixture_path(fixtures_dir, "account_list", "filter_number_eq"))
    (entry,) = json.loads(fixture.response.body)["data"]
    assert entry["number"] == "1020"
    return int(entry["id"])


BANK = (
    "<values><de>Bank</de><en>Bank account</en><fr>Compte courant</fr>"
    "<it>Conto corrente</it></values>"
)


def test_get_account_replays_the_recorded_read(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    account_id = account_1020_id(fixtures_dir)
    assert recorded_query(fixtures_dir, "account_read", "by_id") == {"id": str(account_id)}
    route = replay_fixture("account_read", "by_id")
    result = tasks.get_account(DEMO, account_id)
    assert dict(route.calls.last.request.url.params) == {"id": str(account_id)}
    assert result.meta.endpoint == "account/read.json"
    assert result.meta.request == {"org": DEMO, "id": account_id}
    account = result.data
    assert (account.id, account.number, account.category_id) == (account_id, "1020", 51)
    assert (account.name, account.full_name) == (BANK, f"1020 {BANK}")
    assert (account.account_class, account.is_inactive) == ("ASSET", False)
    # The read sends no currency code for an account in the default currency; the list
    # entry of the same account says CHF (account_list/filter_number_eq).
    assert (account.currency_id, account.currency_code) == (None, None)
    assert (account.is_foreign_currency, account.is_default_currency) == (False, True)
    assert (account.attachments, account.allocations) == ([], [])
    assert (account.custom, account.notes, account.tax_id) == (None, None, None)
    assert account.last_updated == datetime(2026, 10, 23, 7, 6, 39)
    assert account.last_updated_by == "SYSTEM"


def test_get_account_raises_not_found_for_an_unknown_id(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_read", "unknown_id")
    with pytest.raises(NotFoundError, match="This account does not exist"):
        tasks.get_account(DEMO, 999999999)


@pytest.mark.anyio
async def test_get_account_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    account_id = account_1020_id(fixtures_dir)
    replay_fixture("account_read", "by_id")
    payload = await mcp_call(server, "cashctrl_get_account", {"org": DEMO, "id": account_id})
    data = payload["data"]
    assert (data["number"], data["currency_id"], data["is_default_currency"]) == (
        "1020",
        None,
        True,
    )
    assert payload["meta"]["request"] == {"org": DEMO, "id": account_id}


@pytest.mark.anyio
async def test_an_unknown_account_is_an_error_text_for_the_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_read", "unknown_id")
    with pytest.raises(AssertionError, match="error: NotFoundError: CashCtrl: This account"):
        await mcp_call(server, "cashctrl_get_account", {"org": DEMO, "id": 999999999})


# Journal entries, persons and orders: the offset-paged lists and their reads. The 2025
# journal holds 12 entries (docs/demo-org.md), recorded in pages of five: 5, 5 and 2, and
# the page past the end; 2026 holds 38, recorded as its first page of five.

JOURNAL_LIST_URL = "https://demo.cashctrl.com/api/v1/journal/list.json"
FP2025 = 2
FP2026 = 1
FP2025_PAGES = {
    0: "fp2025_start_0_limit_5",
    5: "fp2025_start_5_limit_5",
    10: "fp2025_start_10_limit_5",
    15: "fp2025_start_15_limit_5",
}


def recorded_body(fixtures_dir: Path, endpoint: str, case: str) -> dict[str, typing.Any]:
    """The decoded JSON body of a recorded answer."""
    body: dict[str, typing.Any] = json.loads(
        load_fixture(fixture_path(fixtures_dir, endpoint, case)).response.body
    )
    return body


def answer_with(body: dict[str, typing.Any]) -> httpx.Response:
    return httpx.Response(200, json=body)


@pytest.fixture
def journal_2025_pages(fixtures_dir: Path) -> dict[int, dict[str, typing.Any]]:
    """The recorded 2025 pages of five, keyed by the ``start`` they were recorded with."""
    return {
        start: recorded_body(fixtures_dir, "journal_list", case)
        for start, case in FP2025_PAGES.items()
    }


def serve_by_start(
    respx_mock: respx.MockRouter, pages: dict[int, dict[str, typing.Any]]
) -> respx.Route:
    """A route answering each request with the page recorded for its ``start``.

    ``replay_fixture`` ignores query strings, so the multi-page replay dispatches on the
    ``start`` each request sends; a ``start`` nothing was recorded for fails the test.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        return answer_with(pages[int(request.url.params["start"])])

    return respx_mock.get(JOURNAL_LIST_URL).mock(side_effect=answer)


def starts(route: respx.Route) -> list[int]:
    return [int(call.request.url.params["start"]) for call in route.calls]


def test_list_journal_entries_with_limit_is_one_page_and_upstreams_total(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("journal_list", "fp2026_start_0_limit_5")
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2026, limit=5)
    sent = dict(route.calls.last.request.url.params)
    assert route.call_count == 1, "limit given: one request"
    assert sent == {"fiscalPeriodId": "1", "start": "0", "limit": "5"}
    assert sent == recorded_query(fixtures_dir, "journal_list", "fp2026_start_0_limit_5")
    assert result.meta.endpoint == "journal/list.json"
    assert result.meta.request == {"org": DEMO, "fiscalPeriodId": 1, "start": 0, "limit": 5}
    assert (len(result.data), result.meta.total) == (5, 38), "upstream's count, not len(data)"
    # Newest first (upstream's default: dateAdded, DESC).
    assert [entry.date_added for entry in result.data] == [
        date(2026, 9, 30),
        date(2026, 9, 22),
        date(2026, 9, 15),
        date(2026, 9, 4),
        date(2026, 8, 31),
    ]
    fees, collective, invoice = result.data[:3]
    assert (fees.id, fees.type, fees.amount) == (48, "MANUAL", Decimal(45))
    assert isinstance(fees.amount, Decimal)
    assert (fees.debit_id, fees.credit_id, fees.associate_id) == (26, 3, None)
    assert fees.debit_name is not None
    assert fees.debit_name.startswith("6900 <values>")
    assert (collective.id, collective.type, collective.items_count) == (47, "COLLECTIVE", 3)
    assert (collective.debit_id, collective.credit_id) == (None, 3), "lines are in the read"
    assert (invoice.reference, invoice.tax_code) == ("RE-2026-007", "UN1")
    assert invoice.tax_rate == Decimal("8.1")
    assert isinstance(invoice.tax_rate, Decimal)
    assert (invoice.associate_id, invoice.associate_name) == (7, "Muster Consulting GmbH")
    assert (invoice.currency_code, invoice.currency_rate) == ("CHF", Decimal(1))
    assert (invoice.order_id, invoice.is_recurring) == (None, False)
    assert invoice.created_by == "API:REDACTED"


def test_list_journal_entries_pages_from_start(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("journal_list", "fp2025_start_10_limit_5")
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025, start=10, limit=5)
    assert dict(route.calls.last.request.url.params) == {
        "fiscalPeriodId": "2",
        "start": "10",
        "limit": "5",
    }
    assert [entry.id for entry in result.data] == [2, 1]
    assert result.meta.total == 12
    assert result.data[-1].amount == Decimal(100000), "the share capital, January 2025"


def test_a_page_past_the_end_is_empty_with_upstreams_total(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """Observed on 2026-10-23: HTTP 200, ``data`` empty, ``total`` unchanged."""
    route = replay_fixture("journal_list", "fp2025_start_15_limit_5")
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025, start=15, limit=5)
    assert route.call_count == 1
    assert (result.data, result.meta.total) == ([], 12)


def test_list_journal_entries_without_limit_collects_every_page(
    respx_mock: respx.MockRouter,
    journal_2025_pages: dict[int, dict[str, typing.Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tasks, "PAGE_SIZE", 5)  # the size the pages were recorded with
    route = serve_by_start(respx_mock, journal_2025_pages)
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025)
    assert [dict(call.request.url.params) for call in route.calls] == [
        {"fiscalPeriodId": "2", "start": str(start), "limit": "5"} for start in (0, 5, 10)
    ], "three requests: the third page is short"
    assert [entry.id for entry in result.data] == list(range(12, 0, -1))
    assert result.meta.total == 12
    assert result.meta.request == {"org": DEMO, "fiscalPeriodId": 2, "start": 0}, (
        "limit, the page size, is left out: the same arguments collect the same entries"
    )


def test_start_without_limit_collects_every_page_from_start(
    respx_mock: respx.MockRouter,
    journal_2025_pages: dict[int, dict[str, typing.Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tasks, "PAGE_SIZE", 5)
    route = serve_by_start(respx_mock, journal_2025_pages)
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025, start=5)
    assert starts(route) == [5, 10]
    assert [entry.id for entry in result.data] == [7, 6, 5, 4, 3, 2, 1]
    assert result.meta.total == 12
    assert result.meta.request == {"org": DEMO, "fiscalPeriodId": 2, "start": 5}


def test_the_default_page_size_is_upstreams_100(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    assert tasks.PAGE_SIZE == 100
    route = replay_fixture("journal_list", "fp2025_start_10_limit_5")
    tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025)
    assert route.call_count == 1, "a page shorter than 100 ends the collection"
    assert route.calls.last.request.url.params["limit"] == "100", "sent explicitly"


def test_collecting_stops_at_upstreams_total_without_a_further_request(
    respx_mock: respx.MockRouter,
    journal_2025_pages: dict[int, dict[str, typing.Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pages of four end exactly at the 12 upstream counts: no fourth, empty request.

    The answers are cut from the recorded 2025 entries by each request's ``start`` and
    ``limit``, as upstream cuts them.
    """
    entries = [entry for start in (0, 5, 10) for entry in journal_2025_pages[start]["data"]]
    monkeypatch.setattr(tasks, "PAGE_SIZE", 4)

    def answer(request: httpx.Request) -> httpx.Response:
        start, limit = (int(request.url.params[name]) for name in ("start", "limit"))
        return answer_with({"total": 12, "data": entries[start : start + limit]})

    route = respx_mock.get(JOURNAL_LIST_URL).mock(side_effect=answer)
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025)
    assert starts(route) == [0, 4, 8]
    assert (len(result.data), result.meta.total) == (12, 12)


def test_the_count_kept_is_the_last_pages_and_never_corrected(
    respx_mock: respx.MockRouter,
    journal_2025_pages: dict[int, dict[str, typing.Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Conventions §4: a mismatch with ``len(data)`` is upstream's and stays."""
    monkeypatch.setattr(tasks, "PAGE_SIZE", 5)
    pages = {**journal_2025_pages, 10: {**journal_2025_pages[10], "total": 11}}
    serve_by_start(respx_mock, pages)
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2025)
    assert (len(result.data), result.meta.total) == (12, 11)


@pytest.mark.anyio
async def test_list_journal_entries_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("journal_list", "fp2026_start_0_limit_5")
    arguments = {"org": DEMO, "fiscal_period_id": FP2026, "limit": 5}
    payload = await mcp_call(server, "cashctrl_list_journal_entries", arguments)
    assert payload["meta"]["total"] == 38
    assert payload["meta"]["request"] == {
        "org": DEMO,
        "fiscalPeriodId": 1,
        "start": 0,
        "limit": 5,
    }
    first = payload["data"][0]
    assert (first["id"], first["date_added"], first["amount"]) == (48, "2026-09-30", 45)
    with pytest.raises(ToolError, match=r"limit[\s\S]*int_parsing"):
        await mcp_call(server, "cashctrl_list_journal_entries", {"org": DEMO, "limit": "many"})


def collective_line_associates(fixtures_dir: Path) -> list[object]:
    """``associateId`` of each line as recorded: text, though the entry's own is a number."""
    body = recorded_body(fixtures_dir, "journal_read", "collective")
    return [item["associateId"] for item in body["data"]["items"]]


def test_get_journal_entry_replays_a_taxed_entry(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    assert recorded_query(fixtures_dir, "journal_read", "by_id") == {"id": "11"}
    route = replay_fixture("journal_read", "by_id")
    result = tasks.get_journal_entry(DEMO, 11)
    assert dict(route.calls.last.request.url.params) == {"id": "11"}
    assert result.meta.endpoint == "journal/read.json"
    assert result.meta.request == {"org": DEMO, "id": 11}
    assert result.meta.total is None, "a read reports no count"
    entry = result.data
    assert (entry.id, entry.type, entry.date_added) == (11, "MANUAL", date(2025, 10, 20))
    assert (entry.title, entry.reference, entry.nr) == (
        "Rechnung RE-2025-003 Beispiel Logistik AG",
        "RE-2025-003",
        "RE-2025-003",
    )
    assert (entry.amount, entry.default_currency_amount) == (Decimal(3600), Decimal(3600))
    assert (entry.debit_id, entry.credit_id, entry.tax_id, entry.taxed) == (4, 42, 9, True)
    assert entry.items == [], "a simple entry has no lines"
    # The amount is gross (docs/demo-org.md): the revenue row is net, the tax row apart.
    receivable, revenue, vat = entry.rows
    assert (receivable.account_id, receivable.dc_debit) == (4, Decimal(3600))
    assert (revenue.account_id, revenue.dc_credit, revenue.is_taxed) == (
        42,
        Decimal("3330.25"),
        True,
    )
    assert (vat.account_id, vat.dc_credit, vat.is_tax) == (33, Decimal("269.75"), True)
    assert vat.tax_percentage == Decimal("8.1")
    (partner,) = entry.associates
    assert isinstance(partner, PersonDetail)
    assert (partner.id, partner.company, partner.is_customer) == (8, "Beispiel Logistik AG", True)
    assert [(a.type, a.zip, a.city) for a in partner.addresses] == [("MAIN", "4051", "Basel")]
    assert [(c.type, c.address) for c in partner.contacts] == [("EMAIL_WORK", "user@example.com")]
    assert entry.account_ids == '["33","4","42"]', "kept as sent"


def test_get_journal_entry_replays_a_collective_entry(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    replay_fixture("journal_read", "collective")
    entry = tasks.get_journal_entry(DEMO, 47).data
    assert (entry.type, entry.amount, entry.debit_id, entry.credit_id) == (
        "COLLECTIVE",
        Decimal(2580),
        None,
        3,
    )
    assert all(isinstance(item, JournalItem) for item in entry.items)
    assert [(i.account_id, i.debit, i.credit, i.associate_id) for i in entry.items] == [
        (9, Decimal(2400), None, 3),
        (22, Decimal(180), None, 4),
        (3, None, Decimal(2580), None),
    ]
    assert collective_line_associates(fixtures_dir) == ["3", "4", None], "sent as text"
    assert [item.description for item in entry.items] == [
        "Zahlung ER-2026-003",
        "Telefon und Internet September 2026",
        "Zahlungsausgang",
    ]
    assert [item.associate_name for item in entry.items][:2] == [
        "Muster Büro AG",
        "Beispiel Telecom AG",
    ]
    assert sum(row.dc_debit for row in entry.rows) == sum(row.dc_credit for row in entry.rows)
    assert [person.id for person in entry.associates] == [3, 4]


def test_get_journal_entry_raises_not_found_for_an_unknown_id(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("journal_read", "unknown_id")
    with pytest.raises(NotFoundError, match="This book entry does not exist"):
        tasks.get_journal_entry(DEMO, 999999999)


@pytest.mark.anyio
async def test_get_journal_entry_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("journal_read", "collective")
    payload = await mcp_call(server, "cashctrl_get_journal_entry", {"org": DEMO, "id": 47})
    first = payload["data"]["items"][0]
    assert (first["account_id"], first["debit"], first["associate_id"]) == (9, 2400, 3)
    assert payload["meta"]["request"] == {"org": DEMO, "id": 47}


def test_list_persons_replays_every_person(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("person_list", "default")
    result = tasks.list_persons(DEMO)
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"start": "0", "limit": "100"}, "every page: 100 a request, from 0"
    assert sent == recorded_query(fixtures_dir, "person_list", "default")
    assert route.call_count == 1, "12 < 100: the first page is the last"
    assert result.meta.endpoint == "person/list.json"
    assert result.meta.request == {"org": DEMO, "start": 0}
    assert len(result.data) == result.meta.total == 12, "ten seeded and two system insurances"
    assert [person.name for person in result.data][:3] == [
        "Beispiel Logistik AG",
        "Beispiel Telecom AG",
        "Demo Bau AG",
    ], "upstream's default order: by name"
    insurances = [person for person in result.data if person.is_insurance]
    assert [(p.nr, p.created_by) for p in insurances] == [
        ("INAHV01", "SYSTEM"),
        ("INBVG01", "SYSTEM"),
    ]
    buero = next(person for person in result.data if person.nr == "P-00001")
    assert (buero.company, buero.is_vendor, buero.is_customer) == ("Muster Büro AG", True, False)
    assert (buero.zip, buero.city, buero.canton, buero.country) == (
        "9000",
        "St. Gallen",
        "SG",
        "CHE",
    )
    assert (buero.email_work, buero.language, buero.first_name) == ("user@example.com", "DE", None)
    assert buero.created == datetime(2026, 10, 23, 10, 29, 12)
    assert (buero.discount_percentage, buero.date_birth, buero.iban) == (None, None, None)


def test_list_persons_only_vendors(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("person_list", "only_vendors")
    result = tasks.list_persons(DEMO, only_vendors=True)
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"onlyVendors": "true", "start": "0", "limit": "100"}
    assert sent == recorded_query(fixtures_dir, "person_list", "only_vendors")
    assert result.meta.request == {"org": DEMO, "onlyVendors": "true", "start": 0}
    assert result.meta.total == 4
    assert [person.nr for person in result.data] == ["P-00002", "P-00003", "P-00001", "P-00004"]
    assert all(person.is_vendor for person in result.data)


@pytest.mark.anyio
async def test_list_persons_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("person_list", "only_vendors")
    payload = await mcp_call(server, "cashctrl_list_persons", {"org": DEMO, "only_vendors": True})
    assert (payload["meta"]["total"], len(payload["data"])) == (4, 4)
    assert payload["data"][0]["is_vendor"] is True


def test_get_person_replays_the_recorded_read(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    assert recorded_query(fixtures_dir, "person_read", "by_id") == {"id": "3"}
    route = replay_fixture("person_read", "by_id")
    result = tasks.get_person(DEMO, 3)
    assert dict(route.calls.last.request.url.params) == {"id": "3"}
    assert result.meta.endpoint == "person/read.json"
    assert result.meta.request == {"org": DEMO, "id": 3}
    person = result.data
    assert (person.id, person.nr, person.company) == (3, "P-00001", "Muster Büro AG"), "UTF-8"
    assert (person.is_vendor, person.category_id, person.language_code) == (True, 2, "de")
    assert person.category_name is not None
    assert "<en>Vendors</en>" in person.category_name
    (address,) = person.addresses
    assert isinstance(address, PersonAddress)
    assert (address.type, address.street_name, address.street_number) == (
        "MAIN",
        "Beispielring",
        "9",
    )
    assert (address.zip, address.city, address.country_code2) == ("9000", "St. Gallen", "CH")
    assert (address.company_for_address, address.is_hide_company) == ("Muster Büro AG", False)
    (contact,) = person.contacts
    assert (contact.type, contact.address, contact.pos) == ("EMAIL_WORK", "user@example.com", 0)
    assert (person.bank_accounts, person.children, person.attachments) == ([], [], [])
    # The read leaves out null fields; they come back empty.
    assert "firstName" not in recorded_body(fixtures_dir, "person_read", "by_id")["data"]
    assert (person.first_name, person.notes, person.vat_uid) == (None, None, None)


@pytest.mark.anyio
async def test_get_person_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("person_read", "by_id")
    payload = await mcp_call(server, "cashctrl_get_person", {"org": DEMO, "id": 3})
    assert payload["data"]["addresses"][0]["city"] == "St. Gallen"
    assert payload["data"]["contacts"][0]["type"] == "EMAIL_WORK"


def test_list_orders_replays_the_sales_orders(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("order_list", "fp2026_sales")
    result = tasks.list_orders(DEMO, type="SALES", fiscal_period_id=FP2026)
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"fiscalPeriodId": "1", "type": "SALES", "start": "0", "limit": "100"}
    assert sent == recorded_query(fixtures_dir, "order_list", "fp2026_sales")
    assert result.meta.endpoint == "order/list.json"
    assert result.meta.request == {"org": DEMO, "fiscalPeriodId": 1, "type": "SALES", "start": 0}
    assert len(result.data) == result.meta.total == 4
    assert [order.nr for order in result.data] == [
        "RE-2026-104",
        "RE-2026-103",
        "RE-2026-102",
        "RE-2026-101",
    ], "upstream's default order: by date, DESC"
    order = result.data[0]
    assert (order.type, order.book_type, order.date) == ("SALES", "DEBIT", date(2026, 9, 7))
    assert (order.associate_id, order.associate_name) == (12, "Probe Gastro GmbH")
    # 20 x 45.00 (docs/demo-org.md), the unit price read as gross, VAT 8.1 % included.
    assert (order.sub_total, order.tax, order.total) == (
        Decimal("832.56"),
        Decimal("67.44"),
        Decimal(900),
    )
    assert isinstance(order.sub_total, Decimal)
    assert (order.is_book, order.open, order.date_due) == (False, None, None)
    assert order.status_name is not None
    assert "<en>Draft</en>" in order.status_name
    assert order.date_last_booked == datetime(2026, 9, 7)


def test_list_orders_replays_the_purchase_orders(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("order_list", "fp2026_purchase")
    result = tasks.list_orders(DEMO, type="PURCHASE", fiscal_period_id=FP2026)
    assert result.meta.total == 2
    assert [(o.nr, o.book_type, o.is_book, o.open) for o in result.data] == [
        ("EK-2026-002", "CREDIT", True, Decimal(830)),
        ("EK-2026-001", "CREDIT", True, Decimal(4650)),
    ], "their status Open books them"


@pytest.mark.anyio
async def test_list_orders_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("order_list", "fp2026_sales")
    arguments = {"org": DEMO, "type": "SALES", "fiscal_period_id": FP2026}
    payload = await mcp_call(server, "cashctrl_list_orders", arguments)
    assert payload["meta"]["total"] == 4
    assert (payload["data"][0]["nr"], payload["data"][0]["sub_total"]) == ("RE-2026-104", 832.56)
    with pytest.raises(ToolError, match=r"type[\s\S]*literal_error"):
        await mcp_call(server, "cashctrl_list_orders", {"org": DEMO, "type": "sales"})


def test_get_order_replays_the_recorded_read(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    assert recorded_query(fixtures_dir, "order_read", "by_id") == {"id": "3"}
    route = replay_fixture("order_read", "by_id")
    result = tasks.get_order(DEMO, 3)
    assert dict(route.calls.last.request.url.params) == {"id": "3"}
    assert result.meta.endpoint == "order/read.json"
    assert result.meta.request == {"org": DEMO, "id": 3}
    order = result.data
    assert (order.nr, order.type, order.date, order.associate_name) == (
        "RE-2026-103",
        "SALES",
        date(2026, 6, 8),
        "Demo Bau AG",
    )
    assert (order.sub_total, order.tax, order.total, order.total_to_pay) == (
        Decimal("7169.29"),
        Decimal("580.71"),
        Decimal(7750),
        Decimal(7750),
    )
    assert (order.tax_type, order.due, order.is_book) == ("AGREED", False, False)
    assert order.hash == "REDACTED", "scrubbed by the recorder, by its field name"
    assert all(isinstance(item, OrderItem) for item in order.items)
    assert [(i.name, i.quantity, i.unit_price, i.gross_total) for i in order.items] == [
        ("Bürostuhl Ergo", Decimal(10), Decimal(420), Decimal(4200)),
        ("Schreibtisch Basic", Decimal(5), Decimal(680), Decimal(3400)),
        ("Lieferung", Decimal(1), Decimal(150), Decimal(150)),
    ]
    chair = order.items[0]
    assert (chair.net_unit_price, chair.net_total, chair.tax_total) == (
        Decimal("388.52913969"),
        Decimal("3885.29"),
        Decimal("314.71"),
    ), "Decimal keeps upstream's digits"
    assert (chair.type, chair.tax_code, chair.tax_calc_type, chair.base_value) == (
        "ARTICLE",
        "UN1",
        "NET",
        "GROSS",
    )
    assert sum(item.gross_total or 0 for item in order.items) == order.total


@pytest.mark.anyio
async def test_get_order_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("order_read", "by_id")
    payload = await mcp_call(server, "cashctrl_get_order", {"org": DEMO, "id": 3})
    assert [item["quantity"] for item in payload["data"]["items"]] == [10, 5, 1]
    assert payload["data"]["total"] == 7750


PAGED_LISTS: dict[str, Callable[..., typing.Any]] = {
    "list_journal_entries": tasks.list_journal_entries,
    "list_persons": tasks.list_persons,
    "list_orders": tasks.list_orders,
}


@pytest.mark.parametrize("task", PAGED_LISTS.values(), ids=PAGED_LISTS.keys())
@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"dir": "up"}, "dir must be ASC or DESC, not 'up'"),
        (
            {"filter": [{"comparison": "equals", "field": "nr", "value": "1"}]},
            "filter[0].comparison must be one of eq, like, gt, lt, not 'equals'",
        ),
        ({"filter": [UNVALIDATED]}, "filter[0].comparison must be one of eq, like, gt, lt"),
        ({"query": 1}, "query must be a string, not int"),
        ({"start": -1}, "start must be a whole number of at least 0, not -1"),
        ({"start": "5"}, "start must be a whole number of at least 0, not '5'"),
        ({"limit": 0}, "limit must be a whole number of at least 1, not 0"),
        ({"limit": True}, "limit must be a whole number of at least 1, not True"),
    ],
)
def test_the_paged_lists_refuse_what_upstream_would_ignore(
    respx_mock: respx.MockRouter,
    task: Callable[..., typing.Any],
    arguments: dict[str, typing.Any],
    message: str,
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        task(DEMO, **arguments)
    assert not respx_mock.calls


@pytest.mark.parametrize("value", ["sales", "BOTH", ""])
def test_list_orders_refuses_an_unknown_type(respx_mock: respx.MockRouter, value: str) -> None:
    arguments: dict[str, typing.Any] = {"type": value}
    with pytest.raises(InvalidRequestError, match=re.escape(f"not {value!r}")):
        tasks.list_orders(DEMO, **arguments)
    assert not respx_mock.calls


@pytest.mark.anyio
async def test_the_paged_tool_schemas_show_paging_and_value_sets() -> None:
    tools = {tool.name: tool for tool in await server.list_tools()}
    for name in PAGED_LISTS:
        properties = tools[f"cashctrl_{name}"].input_schema["properties"]
        assert (properties["start"]["type"], properties["start"]["default"]) == ("integer", 0)
        assert {"type": "integer"} in properties["limit"]["anyOf"]
        assert {"enum": ["ASC", "DESC"], "type": "string"} in properties["dir"]["anyOf"]
    order_type = tools["cashctrl_list_orders"].input_schema["properties"]["type"]
    assert {"enum": ["SALES", "PURCHASE"], "type": "string"} in order_type["anyOf"]


PAGED_ROUTES: dict[str, tuple[str, dict[str, typing.Any], int]] = {
    "list_journal_entries": (
        "journal_list/fp2026_start_0_limit_5",
        {"fiscal_period_id": FP2026, "limit": 5},
        38,
    ),
    "list_persons": ("person_list/only_vendors", {"only_vendors": True}, 4),
    "list_orders": ("order_list/fp2026_sales", {"type": "SALES", "fiscal_period_id": FP2026}, 4),
}


@pytest.mark.parametrize(("task", "case"), PAGED_ROUTES.items(), ids=PAGED_ROUTES.keys())
def test_the_paged_lists_are_post_routes_with_upstreams_total(
    replay_fixture: Callable[[str, str], respx.Route],
    task: str,
    case: tuple[str, dict[str, typing.Any], int],
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    fixture, arguments, total = case
    replay_fixture(*fixture.split("/"))
    response = client.post(f"/cashctrl/{task}", json={"org": DEMO, **arguments})
    assert response.status_code == 200, response.text
    assert response.json()["meta"]["total"] == total
    rejected = client.post(f"/cashctrl/{task}", json={"org": DEMO, "start": -1})
    assert rejected.status_code == 422
    assert rejected.json()["title"] == "InvalidRequestError"
    assert "start must be a whole number" in rejected.json()["detail"]


RECORDED_LISTS: dict[str, tuple[Callable[..., typing.Any], dict[str, typing.Any]]] = {
    "fiscalperiod_list/default": (api.fiscalperiod_list, {}),
    "currency_list/default": (api.currency_list, {}),
    "tax_list/default": (api.tax_list, {}),
    "account_list/only_active_finanz": (
        api.account_list,
        {"only_active": True, "query": "Finanz"},
    ),
    "account_list/filter_number_eq": (api.account_list, {"filter": [NUMBER_1020]}),
    "person_list/default": (api.person_list, {"start": 0, "limit": 100}),
    "person_list/only_vendors": (api.person_list, {"only_vendors": True}),
    "order_list/fp2026_sales": (api.order_list, {"type": "SALES", "fiscal_period_id": 1}),
    "order_list/fp2026_purchase": (api.order_list, {"type": "PURCHASE", "fiscal_period_id": 1}),
}


@pytest.mark.anyio
@pytest.mark.parametrize(("case", "call"), RECORDED_LISTS.items(), ids=RECORDED_LISTS.keys())
async def test_a_recorded_list_is_whole(
    replay_fixture: Callable[[str, str], respx.Route],
    case: str,
    call: tuple[Callable[..., typing.Any], dict[str, typing.Any]],
) -> None:
    """Upstream's ``total`` equals the records in the one answer: nothing is left behind.

    The journal pages are not whole by design (``journal_list/fp2025_*``, ``fp2026_*``).
    """
    replay_fixture(*case.split("/"))
    wrapper, arguments = call
    response = await wrapper(DEMO, **arguments)
    assert response.total == len(response.data) > 0


SNAKE_CASE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")


def keys(node: object) -> Iterator[str]:
    """Every key of a decoded JSON document, at any depth."""
    if isinstance(node, dict):
        for name, value in node.items():
            yield str(name)
            yield from keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from keys(item)


TOOL_CASES: dict[str, tuple[str, dict[str, typing.Any]]] = {
    "cashctrl_list_fiscal_periods": ("fiscalperiod_list/default", {}),
    "cashctrl_list_currencies": ("currency_list/default", {}),
    "cashctrl_list_tax_codes": ("tax_list/default", {}),
    "cashctrl_list_accounts": ("account_list/filter_number_eq", {"filter": [NUMBER_1020]}),
    "cashctrl_get_account": ("account_read/by_id", {}),
    "cashctrl_list_journal_entries": (
        "journal_list/fp2026_start_0_limit_5",
        {"fiscal_period_id": 1, "limit": 5},
    ),
    "cashctrl_get_journal_entry": ("journal_read/collective", {}),
    "cashctrl_list_persons": ("person_list/default", {}),
    "cashctrl_get_person": ("person_read/by_id", {}),
    "cashctrl_list_orders": ("order_list/fp2026_sales", {"type": "SALES", "fiscal_period_id": 1}),
    "cashctrl_get_order": ("order_read/by_id", {}),
}


def tool_arguments(
    tool: str, case: tuple[str, dict[str, typing.Any]], fixtures_dir: Path
) -> dict[str, typing.Any]:
    """The arguments ``case`` was recorded with, as JSON: a read takes the recorded id."""
    arguments = case[1]
    if tool.startswith("cashctrl_get_"):
        arguments = {"id": int(recorded_query(fixtures_dir, *case[0].split("/"))["id"])}
    return {
        key: [item.model_dump() for item in value] if key == "filter" else value
        for key, value in arguments.items()
    }


def snake_case_violations(data: object) -> list[str]:
    """The keys of ``data``, at any depth, that are not snake_case; none must be."""
    found = sorted(set(keys(data)))
    assert found, "a result without keys proves nothing"
    return [key for key in found if not SNAKE_CASE.fullmatch(key)]


@pytest.mark.anyio
@pytest.mark.parametrize(("tool", "case"), TOOL_CASES.items(), ids=TOOL_CASES.keys())
async def test_tool_results_carry_snake_case_keys(
    replay_fixture: Callable[[str, str], respx.Route],
    fixtures_dir: Path,
    tool: str,
    case: tuple[str, dict[str, typing.Any]],
) -> None:
    """Models read upstream's camelCase with ``validation_alias``; nothing dumps it back.

    ``meta.request`` is not checked: it records the parameters as sent, under upstream's
    names (``onlyActive``).
    """
    replay_fixture(*case[0].split("/"))
    arguments = tool_arguments(tool, case, fixtures_dir)
    payload = await mcp_call(server, tool, {"org": DEMO, **arguments})
    assert snake_case_violations(payload["data"]) == []


@pytest.mark.parametrize(("tool", "case"), TOOL_CASES.items(), ids=TOOL_CASES.keys())
def test_route_results_carry_snake_case_keys(
    replay_fixture: Callable[[str, str], respx.Route],
    fixtures_dir: Path,
    tool: str,
    case: tuple[str, dict[str, typing.Any]],
) -> None:
    """The HTTP twin: every key of every route's ``data`` is snake_case, GET and POST alike."""
    from fastapi import FastAPI
    from fastapi.routing import APIRoute
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    path = f"/cashctrl/{tool.removeprefix('cashctrl_')}"
    (route,) = [r for r in router.routes if isinstance(r, APIRoute) and r.path == path]
    replay_fixture(*case[0].split("/"))
    arguments = {"org": DEMO, **tool_arguments(tool, case, fixtures_dir)}
    client = TestClient(app)
    if route.methods == {"POST"}:
        response = client.post(path, json=arguments)
    else:
        response = client.get(path, params=arguments)
    assert response.status_code == 200, response.text
    assert snake_case_violations(response.json()["data"]) == []
