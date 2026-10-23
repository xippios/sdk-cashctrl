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


# Per-task tests. Every fixture was recorded from the demo organisation on 2026-10-23.


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
    assert [period.id for period in result.data] == [3, 4, 5]
    first = result.data[0]
    assert (first.name, first.start, first.end) == ("2024", date(2024, 1, 1), date(2024, 12, 31))
    assert first.salary_end == date(2024, 12, 31)
    assert first.last_entry_date == datetime(2024, 12, 31, 0, 0, 2), "undocumented: time kept"
    assert first.created == datetime(2024, 1, 10, 8, 19)
    assert first.is_closed is True
    assert first.closed_month_ids[:2] == ["2024-01", "2024-02"]
    assert [period.is_current for period in result.data] == [False, False, True]


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
        5,
        "2026-01-01",
        "2026-12-31",
        True,
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
    chf, eur, _ = result.data
    assert isinstance(eur.rate, Decimal)
    assert eur.rate == Decimal("0.920261")
    assert chf.rate == Decimal(1)
    assert chf.description == "<values><de>Schweizer Franken</de></values>"
    assert chf.created == datetime(2022, 1, 4, 14, 1, 41)


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
    assert len(result.data) == 12
    code = next(tax for tax in result.data if tax.code == "UN1")
    assert code.id == 1
    assert code.current_percentage == Decimal("8.1")
    assert isinstance(code.current_percentage, Decimal)
    assert code.current_percentage_flat is None
    assert code.form_codes == "200, 303"
    assert code.is_inactive is False
    (rate,) = code.rates
    assert (rate.percentage, rate.date_valid, rate.percentage_flat) == (Decimal("8.1"), None, None)
    (component,) = code.components
    assert (component.account_id, component.calc_type, component.apply_rule) == (
        33,
        "NET",
        "LEGACY_REV",
    )
    assert component.is_input_tax is False
    assert [tax.code for tax in result.data if tax.is_inactive] == ["U02"]


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


NUMBER_1000 = Filter(comparison="eq", field="number", value="1000")
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
    route = replay_fixture("account_list", "only_active_abschreibungen")
    result = tasks.list_accounts(DEMO, only_active=True, query="Abschreibungen")
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"onlyActive": "true", "query": "Abschreibungen"}
    assert sent == recorded_query(fixtures_dir, "account_list", "only_active_abschreibungen")
    assert result.meta.endpoint == "account/list.json"
    assert result.meta.request == {"org": DEMO, **sent}
    assert [(a.id, a.number) for a in result.data] == [(199, "6815"), (200, "6817")]
    account = result.data[0]
    assert account.name == "Abschreibungen Immaterielle Vermögensgegenstände"
    assert (account.category_id, account.account_class, account.currency_code) == (
        64,
        "EXPENSE",
        "CHF",
    )
    assert isinstance(account.end_amount, Decimal)
    assert account.end_amount == account.opening_amount == Decimal(0)
    assert account.default_currency_end_amount == Decimal(0)
    assert (account.currency_id, account.tax_id, account.cost_center_ids) == (None, None, None)
    assert account.is_inactive is False
    assert isinstance(account.created, datetime)


def test_an_account_takes_currency_id_as_a_number_a_string_or_null(fixtures_dir: Path) -> None:
    """The committed list entries carry ``null``; a string was seen in an uncommitted list."""
    fixture = fixture_path(fixtures_dir, "account_list", "only_active_abschreibungen")
    entry = json.loads(load_fixture(fixture).response.body)["data"][0]
    assert entry["currencyId"] is None
    for sent, parsed in (("2", 2), (2, 2), (None, None)):
        assert Account.model_validate({**entry, "currencyId": sent}).currency_id == parsed


def test_list_accounts_sends_the_filter_as_upstream_reads_it(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_list", "filter_number_eq")
    result = tasks.list_accounts(DEMO, filter=[NUMBER_1000])
    sent = dict(route.calls.last.request.url.params)
    assert sent == {"filter": '[{"comparison":"eq","field":"number","value":"1000"}]'}
    assert sent == recorded_query(fixtures_dir, "account_list", "filter_number_eq")
    assert result.meta.request == {"org": DEMO, **sent}
    (account,) = result.data
    assert (account.id, account.number, account.is_inactive) == (1, "1000", True)


def test_list_accounts_takes_filters_as_mappings_too(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_list", "filter_number_eq")
    item = {"comparison": "eq", "field": "number", "value": "1000"}
    arguments: dict[str, typing.Any] = {"filter": [item]}
    result = tasks.list_accounts(DEMO, **arguments)
    sent = dict(route.calls.last.request.url.params)
    assert sent == recorded_query(fixtures_dir, "account_list", "filter_number_eq")
    assert [account.number for account in result.data] == ["1000"]
    arguments = {"filter": [{"field": "number", "value": ["1000", "1020"]}]}
    tasks.list_accounts(DEMO, **arguments)
    assert dict(route.calls.last.request.url.params) == {
        "filter": '[{"comparison":"like","field":"number","value":["1000","1020"]}]'
    }, "a mapping is validated into a Filter: upstream's default comparison is sent"


def test_the_filter_encoding_keeps_lists_and_text() -> None:
    filters = [Filter(field="name", value=["Kasse", "Büro"]), NUMBER_1000]
    assert api.encode_filter(filters) == (
        '[{"comparison":"like","field":"name","value":["Kasse","Büro"]},'
        '{"comparison":"eq","field":"number","value":"1000"}]'
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
    arguments: dict[str, typing.Any] = {"dir": "down", "filter": [NUMBER_1000, bad]}
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
    item = {"comparison": "eq", "field": "number", "value": "1000"}
    payload = await mcp_call(server, "cashctrl_list_accounts", {"org": DEMO, "filter": [item]})
    (account,) = payload["data"]
    assert (account["number"], account["end_amount"], account["is_inactive"]) == ("1000", 0, True)
    assert payload["meta"]["request"]["filter"] == (
        '[{"comparison":"eq","field":"number","value":"1000"}]'
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
    replay_fixture("account_list", "only_active_abschreibungen")
    body = {"org": DEMO, "only_active": True, "query": "Abschreibungen"}
    response = client.post("/cashctrl/list_accounts", json=body)
    assert response.status_code == 200, response.text
    row = response.json()["data"][0]
    assert ("end_amount" in row, "endAmount" in row) == (True, False), "snake_case over HTTP"
    assert [account["number"] for account in response.json()["data"]] == ["6815", "6817"]
    rejected = client.post("/cashctrl/list_accounts", json={"org": DEMO, "dir": "up"})
    assert rejected.status_code == 422
    assert rejected.json()["detail"][0]["type"] == "literal_error", "FastAPI's own 422"
    unknown = client.post("/cashctrl/list_accounts", json={"org": "nowhere"})
    assert unknown.status_code == 422
    assert unknown.json()["title"] == "InvalidRequestError", "the task's refusals as problems"


def test_get_account_replays_the_recorded_read(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("account_read", "by_id")
    result = tasks.get_account(DEMO, 223)
    assert dict(route.calls.last.request.url.params) == {"id": "223"}
    assert result.meta.endpoint == "account/read.json"
    assert result.meta.request == {"org": DEMO, "id": 223}
    account = result.data
    assert (account.id, account.number, account.category_id) == (223, "6781", 64)
    assert account.name == "<values><de>Laufende Fahrzeugkosten (in EUR)</de></values>"
    assert (account.currency_id, account.currency_code) == (2, "EUR")
    assert (account.is_foreign_currency, account.is_default_currency) == (True, False)
    assert (account.attachments, account.allocations) == ([], [])
    assert account.full_name == "6781 <values><de>Laufende Fahrzeugkosten (in EUR)</de></values>"
    assert (account.custom, account.notes, account.tax_id) == ("", None, None)
    assert account.last_updated == datetime(2024, 4, 5, 11, 39, 39)


def test_get_account_raises_not_found_for_an_unknown_id(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_read", "unknown_id")
    with pytest.raises(NotFoundError, match="This account does not exist"):
        tasks.get_account(DEMO, 999999999)


@pytest.mark.anyio
async def test_get_account_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("account_read", "by_id")
    payload = await mcp_call(server, "cashctrl_get_account", {"org": DEMO, "id": 223})
    assert (payload["data"]["number"], payload["data"]["currency_id"]) == ("6781", 2)
    assert payload["meta"]["request"] == {"org": DEMO, "id": 223}


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
    "account_list/only_active_abschreibungen": (
        api.account_list,
        {"only_active": True, "query": "Abschreibungen"},
    ),
    "account_list/filter_number_eq": (api.account_list, {"filter": [NUMBER_1000]}),
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
    "cashctrl_list_accounts": ("account_list/filter_number_eq", {"filter": [NUMBER_1000]}),
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
        arguments = {"id": int(recorded_query(fixtures_dir, endpoint, name)["id"])}
    arguments = {
        key: [item.model_dump() for item in value] if key == "filter" else value
        for key, value in arguments.items()
    }
    payload = await mcp_call(server, tool, {"org": DEMO, **arguments})
    found = sorted(set(keys(payload["data"])))
    assert found
    assert [key for key in found if not SNAKE_CASE.fullmatch(key)] == []
