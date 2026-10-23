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
from xippios.cashctrl.models import Account, Filter

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
        token = base64.b64encode(f"{SHELL_KEY}:".encode()).decode()
        outgoing = [str(sent.url), *sent.headers.values(), basic_user(sent), sent.content.decode()]
        leaked = any(SHELL_KEY in part or token in part for part in outgoing)
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
    assert len(result.data) == 20, "CashCtrl's default tax codes"
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


RECORDED_LISTS: dict[str, tuple[Callable[..., typing.Any], dict[str, typing.Any]]] = {
    "fiscalperiod_list/default": (api.fiscalperiod_list, {}),
    "currency_list/default": (api.currency_list, {}),
    "tax_list/default": (api.tax_list, {}),
    "account_list/only_active_finanz": (
        api.account_list,
        {"only_active": True, "query": "Finanz"},
    ),
    "account_list/filter_number_eq": (api.account_list, {"filter": [NUMBER_1020]}),
}


@pytest.mark.anyio
@pytest.mark.parametrize(("case", "call"), RECORDED_LISTS.items(), ids=RECORDED_LISTS.keys())
async def test_a_recorded_list_is_whole(
    replay_fixture: Callable[[str, str], respx.Route],
    case: str,
    call: tuple[Callable[..., typing.Any], dict[str, typing.Any]],
) -> None:
    """Upstream's ``total`` equals the records in the one answer: nothing is left behind."""
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
}


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
    fixture, arguments = case
    endpoint, name = fixture.split("/")
    replay_fixture(endpoint, name)
    if tool == "cashctrl_get_account":
        arguments = {"id": account_1020_id(fixtures_dir)}
    arguments = {
        key: [item.model_dump() for item in value] if key == "filter" else value
        for key, value in arguments.items()
    }
    payload = await mcp_call(server, tool, {"org": DEMO, **arguments})
    found = sorted(set(keys(payload["data"])))
    assert found
    assert [key for key in found if not SNAKE_CASE.fullmatch(key)] == []
