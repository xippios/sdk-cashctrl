"""Structural checks every task must satisfy. Per-task tests with recorded fixtures go below."""

import dataclasses
import inspect
import json
import re
import typing
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import BeforeValidator
from xippios.core import InvalidRequestError, NotFoundError, UpstreamModel, sync
from xippios.core.mcp import build_server, tool_name
from xippios.core.testing import (
    Fixture,
    fixture_path,
    load_fixture,
    mcp_call,
    mcp_call_text,
    recorded_query,
    sent_query,
    sent_urls,
)

from xippios.cashctrl import api, models, tasks, tasks_write
from xippios.cashctrl._client import DEMO, SOURCE, TENANTS
from xippios.cashctrl.mcp import server
from xippios.cashctrl.models import (
    Account,
    Filter,
    JournalEntryDetail,
    JournalEntryDetailProjection,
    JournalItem,
    OrderItem,
    Person,
    PersonAddress,
    PersonDetail,
    PersonDetailProjection,
    PersonProjection,
)

TENANT_LIST = "list_organisations"
"""The package's tenant list (``_tenants.list_task``, ADR-0024): no ``org``, no async twin."""
ORG_TASK_NAMES = [name for name in tasks.__all__ if name != TENANT_LIST]
EVERY_TASK: dict[str, Callable[..., object]] = {
    f"{module.__name__.rsplit('.', 1)[-1]}.{name}": getattr(module, name)
    for module in (tasks, tasks_write)
    for name in module.__all__
    if (module, name) != (tasks, TENANT_LIST)
}


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


def test_list_organisations_lists_the_declared_names_only(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter
) -> None:
    """Core's tenant list over ``TENANTS``: names, in declared order, demo last; no request."""
    assert tasks.list_organisations.__name__ == TENANT_LIST
    assert tool_name(SOURCE, tasks.list_organisations) == "cashctrl_list_organisations"
    assert list(inspect.signature(tasks.list_organisations).parameters) == []
    assert tasks.list_organisations().data == [DEMO]
    monkeypatch.setenv(TENANTS.list_var, "xb,xa")
    monkeypatch.setenv(TENANTS.var("xa", "SUBDOMAIN"), "xa-hidden-subdomain")
    result = tasks.list_organisations()
    assert result.data == ["xb", "xa", DEMO]
    assert (result.meta.source, result.meta.endpoint) == ("cashctrl", TENANT_LIST)
    assert (result.meta.tenant, result.meta.request) == (None, {})
    assert "hidden" not in result.model_dump_json()
    assert not respx_mock.calls


def test_list_organisations_has_an_agent_docstring() -> None:
    doc = inspect.getdoc(tasks.list_organisations) or ""
    assert doc.splitlines()[0] == "List the organisations this server can reach, by name."
    assert "org" in doc


@pytest.mark.anyio
async def test_list_organisations_as_a_tool() -> None:
    payload = await mcp_call(server, "cashctrl_list_organisations", {})
    assert payload["data"] == [DEMO]
    assert payload["meta"]["tenant"] is None


@pytest.mark.anyio
async def test_the_organisation_list_is_on_the_read_server() -> None:
    assert "cashctrl_list_organisations" in {tool.name for tool in await server.list_tools()}


def test_list_organisations_as_a_route() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).get("/cashctrl/list_organisations")
    assert response.status_code == 200
    assert response.json()["data"] == [DEMO]
    assert response.json()["meta"]["tenant"] is None


# Per-task tests. Every fixture was recorded on 2026-10-23 from the demo organisation, whose
# books are synthetic: CashCtrl's defaults plus what scripts/seed_demo.py wrote.


def test_list_fiscal_periods_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("fiscalperiod_list", "default")
    result = tasks.list_fiscal_periods(DEMO)
    assert sent_query(route) == {}, "the operation documents no parameters"
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
    assert sent_query(route) == {}, "the operation documents no parameters"
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
    assert sent_query(route) == {}, "the operation documents no parameters"
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


def recorded(fixtures_dir: Path, endpoint: str, case: str) -> Fixture:
    """The recorded exchange ``<endpoint>/<case>``; core's ``recorded_query`` reads its query."""
    return load_fixture(fixture_path(fixtures_dir, endpoint, case))


def test_list_accounts_replays_a_narrowed_list(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_list", "only_active_finanz")
    result = tasks.list_accounts(DEMO, only_active=True, query="Finanz")
    sent = sent_query(route)
    assert sent == {"onlyActive": "true", "query": "Finanz"}
    assert sent == recorded_query(recorded(fixtures_dir, "account_list", "only_active_finanz"))
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
    sent = sent_query(route)
    assert sent == {"filter": '[{"comparison":"eq","field":"number","value":"1020"}]'}
    assert sent == recorded_query(recorded(fixtures_dir, "account_list", "filter_number_eq"))
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
    sent = sent_query(route)
    assert sent == recorded_query(recorded(fixtures_dir, "account_list", "filter_number_eq"))
    assert [account.number for account in result.data] == ["1020"]
    arguments = {"filter": [{"field": "number", "value": ["1000", "1020"]}]}
    tasks.list_accounts(DEMO, **arguments)
    assert sent_query(route) == {
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
    # Refused by the tool's schema, before the task runs: core answers conventions §8's
    # text (ADR-0014, amendment 2026-10-27).
    bad = {"org": DEMO, "filter": [{**item, "comparison": "equals"}]}
    assert await mcp_call_text(server, "cashctrl_list_accounts", bad) == (
        "error: InvalidRequestError: filter.0.comparison: "
        "Input should be 'eq', 'like', 'gt' or 'lt'"
    )
    assert await mcp_call_text(server, "cashctrl_list_accounts", {"org": DEMO, "dir": "up"}) == (
        "error: InvalidRequestError: dir: Input should be 'ASC' or 'DESC'"
    )
    unknown_key = {"org": DEMO, "filter": [{**item, "op": "eq"}]}  # Filter refuses unknown keys
    assert await mcp_call_text(server, "cashctrl_list_accounts", unknown_key) == (
        "error: InvalidRequestError: filter.0.op: Extra inputs are not permitted"
    )


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
    assert recorded_query(recorded(fixtures_dir, "account_read", "by_id")) == {
        "id": str(account_id)
    }
    route = replay_fixture("account_read", "by_id")
    result = tasks.get_account(DEMO, account_id)
    assert sent_query(route) == {"id": str(account_id)}
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
    sent = sent_query(route)
    assert route.call_count == 1, "limit given: one request"
    assert sent == {"fiscalPeriodId": "1", "start": "0", "limit": "5"}
    assert sent == recorded_query(recorded(fixtures_dir, "journal_list", "fp2026_start_0_limit_5"))
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
    assert sent_query(route) == {
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
    assert sent_query(route)["limit"] == "100", "sent explicitly"


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
    refused = {"org": DEMO, "limit": "many"}
    assert await mcp_call_text(server, "cashctrl_list_journal_entries", refused) == (
        "error: InvalidRequestError: limit: "
        "Input should be a valid integer, unable to parse string as an integer"
    )


def collective_line_associates(fixtures_dir: Path) -> list[object]:
    """``associateId`` of each line as recorded: text, though the entry's own is a number."""
    body = recorded_body(fixtures_dir, "journal_read", "collective")
    return [item["associateId"] for item in body["data"]["items"]]


def test_get_journal_entry_replays_a_taxed_entry(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    assert recorded_query(recorded(fixtures_dir, "journal_read", "by_id")) == {"id": "11"}
    route = replay_fixture("journal_read", "by_id")
    result = tasks.get_journal_entry(DEMO, 11)
    assert sent_query(route) == {"id": "11"}
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
    assert isinstance(partner, PersonDetailProjection)
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


def test_list_journal_entries_parses_the_entries_an_order_booked(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    """Recorded on 2026-10-26: an entry an order booked sends ``attachmentCount`` ``null``.

    The 2026 journal with ``onlyPurchase``: the two entries the seeded purchase orders
    booked, ``type`` ``ORDER`` with ``orderId`` set. Their ``attachmentCount`` failed the
    whole list before it was typed ``int | None``.
    """
    route = replay_fixture("journal_list", "order_booked")
    result = tasks.list_journal_entries(DEMO, fiscal_period_id=FP2026, only_purchase=True, limit=20)
    recorded = load_fixture(fixture_path(fixtures_dir, "journal_list", "order_booked"))
    assert sent_urls(route) == [recorded.request.url]
    assert result.meta.total == 2
    assert [(entry.id, entry.type, entry.order_id) for entry in result.data] == [
        (50, "ORDER", 6),
        (49, "ORDER", 5),
    ]
    assert all(entry.attachment_count is None for entry in result.data)
    assert all(entry.order_type == "PURCHASE" for entry in result.data)


def test_get_journal_entry_parses_an_entry_an_order_booked(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """Recorded on 2026-10-26: the read of entry 50 sends ``attachmentCount`` ``null`` too."""
    route = replay_fixture("journal_read", "order_booked")
    entry = tasks.get_journal_entry(DEMO, 50).data
    assert sent_urls(route) == ["https://demo.cashctrl.com/api/v1/journal/read.json?id=50"]
    assert isinstance(entry, JournalEntryDetailProjection)
    assert (entry.id, entry.type, entry.order_id) == (50, "ORDER", 6)
    assert (entry.attachment_count, entry.order_book_entry_id) == (None, None)
    assert entry.rows


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
    sent = sent_query(route)
    assert sent == {"start": "0", "limit": "100"}, "every page: 100 a request, from 0"
    assert sent == recorded_query(recorded(fixtures_dir, "person_list", "default"))
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
    assert (buero.discount_percentage, buero.date_birth) == (None, None)
    assert isinstance(buero, PersonProjection)
    assert not hasattr(buero, "iban"), "ADR-0017: no personal identifier in a projection"
    assert not hasattr(buero, "ssn")


def test_list_persons_only_vendors(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("person_list", "only_vendors")
    result = tasks.list_persons(DEMO, only_vendors=True)
    sent = sent_query(route)
    assert sent == {"onlyVendors": "true", "start": "0", "limit": "100"}
    assert sent == recorded_query(recorded(fixtures_dir, "person_list", "only_vendors"))
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
    assert recorded_query(recorded(fixtures_dir, "person_read", "by_id")) == {"id": "3"}
    route = replay_fixture("person_read", "by_id")
    result = tasks.get_person(DEMO, 3)
    assert sent_query(route) == {"id": "3"}
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


BASE = "https://demo.cashctrl.com/api/v1"
SSN = "756.0000.0000.00"
"""A made-up social security number: tests only, never sent anywhere."""
IBAN = "CH00 TEST 0000 0000 0000 0"
"""A made-up IBAN: tests only, never sent anywhere."""


def test_the_projections_leave_out_ssn_and_iban_and_nothing_else() -> None:
    """ADR-0017: the read models stay faithful; the projections differ by exactly these."""
    assert set(Person.model_fields) - set(PersonProjection.model_fields) == {"ssn", "iban"}
    assert set(PersonProjection.model_fields) <= set(Person.model_fields)
    assert set(PersonDetail.model_fields) - set(PersonDetailProjection.model_fields) == {"ssn"}
    assert set(PersonDetailProjection.model_fields) == set(PersonDetail.model_fields) - {"ssn"}
    assert set(JournalEntryDetailProjection.model_fields) == set(JournalEntryDetail.model_fields)
    for model in (Person, PersonDetail):
        assert {"ssn"} <= set(model.model_fields), model.__name__


@pytest.mark.anyio
async def test_the_person_list_wrapper_stays_faithful(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """The endpoint wrapper keeps ``ssn`` and ``iban`` (``null`` in the fixture); the task not."""
    replay_fixture("person_list", "default")
    listed = await api.person_list(DEMO, start=0, limit=100)
    assert all(isinstance(person, Person) for person in listed.data)
    assert all((person.ssn, person.iban) == (None, None) for person in listed.data)
    result = await tasks.list_persons_async(DEMO)
    for person in result.model_dump()["data"]:
        assert "ssn" not in person
        assert "iban" not in person


def person_with_identifiers(fixtures_dir: Path) -> dict[str, typing.Any]:
    """The recorded person read with an ``ssn`` and a bank account, changed in memory."""
    body = recorded_body(fixtures_dir, "person_read", "by_id")
    body["data"]["ssn"] = SSN
    body["data"]["bankAccounts"] = [{"iban": IBAN, "type": "DEFAULT", "bic": "TESTCHZZ"}]
    return body


def test_the_person_projection_itself_drops_each_iban(fixtures_dir: Path) -> None:
    """ADR-0017 enforced by the type: ``project`` alone, no task, carries no IBAN.

    The recorded person read with bank accounts, changed in memory; the key in any case.
    """
    body = person_with_identifiers(fixtures_dir)
    body["data"]["bankAccounts"] = [
        {"iban": IBAN, "type": "DEFAULT", "bic": "TESTCHZZ"},
        {"IBAN": IBAN, "type": "SALARY"},
        {"Iban": IBAN, "type": "OTHER", "notes": "kept"},
    ]
    read = PersonDetail.model_validate(body["data"])
    assert read.bank_accounts == body["data"]["bankAccounts"], "the read model stays faithful"
    person = PersonDetailProjection.project(read)
    assert person.bank_accounts == [
        {"type": "DEFAULT", "bic": "TESTCHZZ"},
        {"type": "SALARY"},
        {"type": "OTHER", "notes": "kept"},
    ]
    assert IBAN not in person.model_dump_json()
    assert IBAN not in PersonDetailProjection.model_validate(body["data"]).model_dump_json()


@pytest.mark.anyio
async def test_get_person_leaves_out_ssn_and_each_iban(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """A read changed in memory, not a fixture: no fixture carries the values (ADR-0017).

    The wrapper keeps them; the task, its tool and its route show neither.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    respx_mock.get(f"{BASE}/person/read.json").respond(
        200, json=person_with_identifiers(fixtures_dir)
    )
    read = await api.person_read(DEMO, 3)
    assert (read.ssn, read.bank_accounts[0]) == (
        SSN,
        {"iban": IBAN, "type": "DEFAULT", "bic": "TESTCHZZ"},
    )
    person = (await tasks.get_person_async(DEMO, 3)).data
    assert isinstance(person, PersonDetailProjection)
    assert not hasattr(person, "ssn")
    assert person.bank_accounts == [{"type": "DEFAULT", "bic": "TESTCHZZ"}]
    payload = await mcp_call(server, "cashctrl_get_person", {"org": DEMO, "id": 3})
    app = FastAPI()
    app.include_router(router)
    answer = TestClient(app).get(f"/{SOURCE}/get_person", params={"org": DEMO, "id": 3})
    for shown in (person.model_dump_json(), json.dumps(payload), answer.text):
        assert SSN not in shown
        assert IBAN not in shown
        assert '"ssn"' not in shown
        assert '"iban"' not in shown


def test_get_journal_entry_projects_the_persons_it_names(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """A read changed in memory: an associate's ``ssn`` and ``iban`` stay out (ADR-0017)."""
    body = recorded_body(fixtures_dir, "journal_read", "collective")
    for associate in body["data"]["associates"]:
        associate["ssn"] = SSN
        associate["bankAccounts"] = [{"iban": IBAN, "type": "DEFAULT"}]
    respx_mock.get(f"{BASE}/journal/read.json").respond(200, json=body)
    entry = tasks.get_journal_entry(DEMO, 47).data
    assert isinstance(entry, JournalEntryDetailProjection)
    assert [person.id for person in entry.associates] == [3, 4]
    assert all(person.bank_accounts == [{"type": "DEFAULT"}] for person in entry.associates)
    assert SSN not in entry.model_dump_json()
    assert IBAN not in entry.model_dump_json()


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
    sent = sent_query(route)
    assert sent == {"fiscalPeriodId": "1", "type": "SALES", "start": "0", "limit": "100"}
    assert sent == recorded_query(recorded(fixtures_dir, "order_list", "fp2026_sales"))
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
    assert await mcp_call_text(server, "cashctrl_list_orders", {"org": DEMO, "type": "sales"}) == (
        "error: InvalidRequestError: type: Input should be 'SALES' or 'PURCHASE'"
    )


def test_get_order_replays_the_recorded_read(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    assert recorded_query(recorded(fixtures_dir, "order_read", "by_id")) == {"id": "3"}
    route = replay_fixture("order_read", "by_id")
    result = tasks.get_order(DEMO, 3)
    assert sent_query(route) == {"id": "3"}
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


# The book entries of an order and the history, recorded on 2026-10-27: the entry the
# seeded purchase order EK-2026-001 (order 5) booked from its items, that order's history,
# and the history of the order a write fixture created, updated and deleted (order 20),
# read after the delete.

BOOKED_ORDER = 5
"""The seeded purchase order EK-2026-001, in a status that books (``docs/demo-org.md``)."""


def test_list_order_book_entries_replays_a_booked_purchase_order(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("order_bookentry_list", "booked")
    result = tasks.list_order_book_entries(DEMO, BOOKED_ORDER)
    assert sent_query(route) == {"id": "5"}, "the order's id, under upstream's name"
    assert sent_query(route) == recorded_query(
        recorded(fixtures_dir, "order_bookentry_list", "booked")
    )
    assert result.meta.endpoint == "order/bookentry/list.json"
    assert result.meta.request == {"org": DEMO, "id": BOOKED_ORDER}
    assert (result.meta.tenant, result.meta.total, len(result.data)) == (DEMO, 1, 1)
    (entry,) = result.data
    assert (entry.order_id, entry.type, entry.date) == (BOOKED_ORDER, "GENERATED", date(2026, 2, 2))
    assert (entry.amount, entry.net_amount, entry.tax_amount) == (
        Decimal(4650),
        Decimal("4301.57"),
        Decimal("348.43"),
    ), "EK-2026-001's total, read as gross (docs/demo-org.md)"
    assert entry.net_amount + entry.tax_amount == entry.amount  # type: ignore[operator]
    assert (entry.debit_id, entry.credit_id, entry.tax_id) == (45, 9, 13)
    assert (entry.debit_name or "").startswith("4200 ")
    assert (entry.credit_name or "").startswith("2000 ")
    assert [(row.account_id, row.is_tax) for row in entry.rows] == [
        (45, False),
        (9, False),
        (34, True),
    ], "a row per account, the input tax apart, as a journal entry's rows"
    assert entry.created_by == "API:REDACTED"


@pytest.mark.anyio
async def test_list_order_book_entries_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("order_bookentry_list", "booked")
    arguments = {"org": DEMO, "order_id": BOOKED_ORDER}
    payload = await mcp_call(server, "cashctrl_list_order_book_entries", arguments)
    assert payload["meta"]["total"] == 1
    assert payload["meta"]["request"] == {"org": DEMO, "id": BOOKED_ORDER}
    assert (payload["data"][0]["amount"], payload["data"][0]["net_amount"]) == (4650, 4301.57)


def test_list_order_book_entries_as_a_route(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    replay_fixture("order_bookentry_list", "booked")
    response = TestClient(app).get(
        "/cashctrl/list_order_book_entries", params={"org": DEMO, "order_id": BOOKED_ORDER}
    )
    assert response.status_code == 200, response.text
    assert response.json()["meta"]["total"] == 1
    assert response.json()["meta"]["tenant"] == DEMO


def test_list_history_replays_an_orders_history(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("history_list", "order")
    result = tasks.list_history(DEMO, order_id=BOOKED_ORDER)
    sent = sent_query(route)
    assert sent == {"orderId": "5", "start": "0", "limit": "100"}, "every page, 100 a request"
    assert sent == recorded_query(recorded(fixtures_dir, "history_list", "order"))
    assert result.meta.endpoint == "history/list.json"
    assert result.meta.request == {"org": DEMO, "orderId": BOOKED_ORDER, "start": 0}
    assert (result.meta.tenant, result.meta.total, len(result.data)) == (DEMO, 2, 2)
    assert [(e.change_type, e.type, e.order_id, e.person_id) for e in result.data] == [
        ("STATUS", "ORDER", BOOKED_ORDER, 3),
        ("CREATE", "ORDER", BOOKED_ORDER, 3),
    ], "newest first, upstream's default dir"
    assert [entry.message for entry in result.data] == [
        "Rechnung 'EK-2026-001' Status changed to Offen.",
        "Rechnung 'EK-2026-001' created.",
    ]
    assert {entry.created_by for entry in result.data} == {"API:REDACTED"}
    assert result.data[0].created == datetime(2026, 10, 23, 10, 30, 23)
    assert result.data[0].statement_id is None


def test_list_history_with_limit_is_one_page(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("history_list", "order")
    result = tasks.list_history(DEMO, order_id=BOOKED_ORDER, limit=100)
    assert sent_query(route) == {"orderId": "5", "start": "0", "limit": "100"}
    assert route.call_count == 1
    assert result.meta.request == {
        "org": DEMO,
        "orderId": BOOKED_ORDER,
        "start": 0,
        "limit": 100,
    }
    assert result.meta.total == 2


def test_the_history_of_a_deleted_order_is_empty(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """Order 20, created, updated and deleted for the write fixtures, read after the delete.

    Its create and update were listed before the delete; after it upstream lists none.
    """
    replay_fixture("history_list", "deleted_order")
    result = tasks.list_history(DEMO, order_id=20)
    assert (result.data, result.meta.total) == ([], 0)


def test_list_history_sends_its_parameters_as_upstream_reads_them(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """What is sent; the answer is the recorded history, which matches any query."""
    route = replay_fixture("history_list", "order")
    result = tasks.list_history(
        DEMO,
        person_id=3,
        statement_id=4,
        query="EK-2026-001",
        filter=[{"comparison": "eq", "field": "changeType", "value": "CREATE"}],  # type: ignore[list-item]
        dir="ASC",
        start=20,
        limit=20,
    )
    sent = sent_query(route)
    assert sent == {
        "dir": "ASC",
        "filter": '[{"comparison":"eq","field":"changeType","value":"CREATE"}]',
        "personId": "3",
        "query": "EK-2026-001",
        "statementId": "4",
        "start": "20",
        "limit": "20",
    }
    assert result.meta.request == {
        "org": DEMO,
        **sent,
        "personId": 3,
        "statementId": 4,
        "start": 20,
        "limit": 20,
    }


@pytest.mark.anyio
async def test_list_history_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("history_list", "order")
    payload = await mcp_call(server, "cashctrl_list_history", {"org": DEMO, "order_id": 5})
    assert payload["meta"]["total"] == 2
    assert [entry["change_type"] for entry in payload["data"]] == ["STATUS", "CREATE"]
    assert "note" not in payload


@pytest.mark.anyio
async def test_a_history_over_its_cap_names_the_filters_and_where_to_resume(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """``MCP_CAPS``'s note for ``list_history``, on the recorded history with one row a page.

    The recorded history, two entries, fits the default bound, so the bound is lowered
    here and the note kept; the cut and the resume hint are core's (ADR-0016).
    """
    replay_fixture("history_list", "order")
    cap = dataclasses.replace(tasks.MCP_CAPS["list_history"], max_rows=1)
    capped = build_server(SOURCE, [tasks.list_history], caps={"list_history": cap})
    arguments = {"org": DEMO, "order_id": BOOKED_ORDER}
    payload = json.loads(await mcp_call_text(capped, "cashctrl_list_history", arguments))
    assert len(payload["data"]) == 1
    assert payload["note"].startswith("showing 1 of 2 rows")
    assert payload["note"].endswith(
        "narrow the history with order_id, person_id, statement_id, query or filter, or "
        "page it with limit; resume with start=1"
    )


def test_list_order_categories_replays_the_sales_categories(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("order_category_list", "default")
    result = tasks.list_order_categories(DEMO)
    assert sent_query(route) == {}, "upstream's default type, SALES"
    assert result.meta.endpoint == "order/category/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total) == (DEMO, 6)
    assert {category.type for category in result.data} == {"SALES"}
    (invoice,) = [
        c for c in result.data if c.name_singular and "<en>Invoice</en>" in c.name_singular
    ]
    assert (invoice.id, invoice.account_id, invoice.sequence_nr_id) == (4, 4, 1)
    draft, opened = invoice.status[:2]
    assert (draft.id, draft.is_book, opened.id, opened.is_book) == (12, False, 16, True)
    assert "<en>Draft</en>" in (draft.name or "")
    assert [template.account_id for template in invoice.book_templates] == [3, 157]


def test_list_order_categories_sends_type_and_period(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://demo.cashctrl.com/api/v1/order/category/list.json")
    route.respond(200, json={"total": 0, "data": []})
    result = tasks.list_order_categories(DEMO, type="PURCHASE", fiscal_period_id=1)
    assert sent_query(route) == {"fiscalPeriodId": "1", "type": "PURCHASE"}
    assert result.meta.request == {"org": DEMO, "fiscalPeriodId": 1, "type": "PURCHASE"}
    with pytest.raises(InvalidRequestError, match="type must be SALES or PURCHASE, not 'sales'"):
        tasks.list_order_categories(DEMO, type="sales")  # type: ignore[arg-type]
    assert route.call_count == 1


@pytest.mark.anyio
async def test_list_order_categories_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("order_category_list", "default")
    payload = await mcp_call(server, "cashctrl_list_order_categories", {"org": DEMO})
    assert payload["meta"]["total"] == 6
    invoice = next(c for c in payload["data"] if c["id"] == 4)
    assert [status["id"] for status in invoice["status"]] == [12, 16, 40, 43, 18, 17]


def test_list_order_categories_as_a_route(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    replay_fixture("order_category_list", "default")
    response = TestClient(app).get(
        "/cashctrl/list_order_categories", params={"org": DEMO, "type": "SALES"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["meta"]["total"] == 6
    assert response.json()["meta"]["tenant"] == DEMO


@pytest.mark.anyio
async def test_the_order_categories_are_on_the_read_server_and_the_router() -> None:
    """``list_order_categories`` is a read task: agents need its ids to form ``create_order``."""
    from fastapi.routing import APIRoute

    from xippios.cashctrl.http import router
    from xippios.cashctrl.mcp_write import server as write_server

    assert "cashctrl_list_order_categories" in {tool.name for tool in await server.list_tools()}
    routes = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert f"/{SOURCE}/list_order_categories" in routes
    write_tools = {tool.name for tool in await write_server.list_tools()}
    assert "cashctrl_list_order_categories" not in write_tools


# The discovery lists and the reports, recorded on 2026-10-27 from the demo organisation:
# CashCtrl's defaults (person categories and titles, the chart's account categories, the
# report tree) and the main location made by hand with placeholder data (docs/demo-org.md).
# The demo organisation has no custom field and no cost center, so both answers are empty.


def test_list_custom_fields_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("customfield_list", "person")
    result = tasks.list_custom_fields(DEMO, "PERSON")
    assert sent_query(route) == {"type": "PERSON"}
    assert sent_query(route) == recorded_query(recorded(fixtures_dir, "customfield_list", "person"))
    assert result.meta.endpoint == "customfield/list.json"
    assert result.meta.request == {"org": DEMO, "type": "PERSON"}
    assert (result.meta.tenant, result.meta.total, result.data) == (DEMO, 0, [])


@pytest.mark.parametrize("value", ["person", "CONTACT", "", None])
def test_list_custom_fields_refuses_a_type_outside_the_documented_set(
    respx_mock: respx.MockRouter, value: object
) -> None:
    allowed = "JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, "
    message = f"type must be one of {allowed}SALARY_STATEMENT, not {value!r}"
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks.list_custom_fields(DEMO, value)  # type: ignore[arg-type]
    assert not respx_mock.calls


@pytest.mark.anyio
async def test_list_custom_fields_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("customfield_list", "person")
    payload = await mcp_call(server, "cashctrl_list_custom_fields", {"org": DEMO, "type": "PERSON"})
    assert (payload["data"], payload["meta"]["total"]) == ([], 0)
    assert payload["meta"]["request"] == {"org": DEMO, "type": "PERSON"}
    refused = {"org": DEMO, "type": "person"}
    text = await mcp_call_text(server, "cashctrl_list_custom_fields", refused)
    assert text.startswith("error: InvalidRequestError: type: Input should be 'JOURNAL'")
    missing = await mcp_call_text(server, "cashctrl_list_custom_fields", {"org": DEMO})
    assert missing == "error: InvalidRequestError: type: Field required"


def test_list_custom_fields_as_a_route(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """A ``GET``, ``type`` a query parameter the route requires and checks as the tool does."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    replay_fixture("customfield_list", "person")
    client = TestClient(app)
    response = client.get("/cashctrl/list_custom_fields", params={"org": DEMO, "type": "PERSON"})
    assert response.status_code == 200, response.text
    assert (response.json()["data"], response.json()["meta"]["total"]) == ([], 0)
    assert response.json()["meta"]["tenant"] == DEMO
    refused = client.get("/cashctrl/list_custom_fields", params={"org": DEMO, "type": "person"})
    assert refused.status_code == 422
    missing = client.get("/cashctrl/list_custom_fields", params={"org": DEMO})
    assert missing.status_code == 422


def test_list_person_categories_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("person_category_list", "default")
    result = tasks.list_person_categories(DEMO)
    assert sent_query(route) == {}, "the operation documents no parameters"
    assert result.meta.endpoint == "person/category/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total) == (DEMO, 4)
    assert [(c.id, c.parent_id) for c in result.data] == [
        (1, None),
        (2, None),
        (3, None),
        (4, None),
    ]
    customers = result.data[0]
    assert customers.name.startswith("<values><de>Kunden</de><en>Customers</en>"), "verbatim"
    assert (customers.sequence_nr_id, customers.discount_percentage) == (None, None)
    assert (customers.sequence_nr_id_inherited, customers.discount_effective) == (None, None)
    assert (customers.created, customers.created_by) == (datetime(2026, 10, 23, 7, 6, 40), "SYSTEM")
    # The persons' category_id comes from here: customers, vendors and insurances.
    persons = json.loads(recorded(fixtures_dir, "person_list", "default").response.body)["data"]
    assert {p["categoryId"] for p in persons} <= {c.id for c in result.data}


def test_list_person_titles_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("person_title_list", "default")
    result = tasks.list_person_titles(DEMO)
    assert sent_query(route) == {}, "the operation documents no parameters"
    assert result.meta.endpoint == "person/title/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total) == (DEMO, 3)
    assert [(t.id, t.gender, t.value) for t in result.data] == [
        (3, None, "3"),
        (2, "FEMALE", "2"),
        (1, "MALE", "1"),
    ], "upstream's order"
    they, _, mr = result.data
    assert "<en>Mr.</en>" in mr.name
    assert "<en>Dear Mr.</en>" in (mr.sentence or "")
    assert (they.sentence, they.text) == (None, None)


def test_list_account_categories_replays_the_flat_list(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("account_category_list", "default")
    result = tasks.list_account_categories(DEMO)
    assert sent_query(route) == {}, "the operation documents no parameters"
    assert result.meta.endpoint == "account/category/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total, len(result.data)) == (DEMO, 38, 38)
    by_id = {category.id: category for category in result.data}
    top = [category for category in result.data if category.parent_id is None]
    assert [(c.number, c.name, c.account_class, c.is_system) for c in top] == [
        ("1", "Assets", "ASSET", True),
        ("2", "Liabilities & Equity", "LIABILITY", True),
        ("3", "Expense", "EXPENSE", True),
        ("4", "Revenue", "REVENUE", True),
        ("5", "Balance", "BALANCE", True),
    ]
    below = [category for category in result.data if category.parent_id is not None]
    assert all(category.parent_id in by_id for category in below), "every parent is listed"
    assert not any(category.is_system or category.system for category in below)
    liquid = by_id[51]
    assert (liquid.number, liquid.parent_id, liquid.account_class) == ("100", 50, "ASSET")
    assert "<en>Liquid funds</en>" in liquid.name
    assert (liquid.full_name or "").startswith("100 <values><de>Flüssige Mittel</de>")
    # Account 6900 (account_list/only_active_finanz) carries category_id 64.
    assert (by_id[64].number, by_id[64].account_class) == ("60", "EXPENSE")


def test_list_cost_centers_replays_the_recorded_list(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("account_costcenter_list", "default")
    result = tasks.list_cost_centers(DEMO)
    assert sent_query(route) == {}
    assert sent_query(route) == recorded_query(
        recorded(fixtures_dir, "account_costcenter_list", "default")
    )
    assert result.meta.endpoint == "account/costcenter/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total, result.data) == (DEMO, 0, [])


def test_list_cost_centers_sends_its_parameters_as_upstream_reads_them(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """What is sent; the answer is the recorded empty list, which matches any query."""
    route = replay_fixture("account_costcenter_list", "default")
    result = tasks.list_cost_centers(
        DEMO,
        query="Projekt",
        filter=[{"comparison": "eq", "field": "number", "value": "100"}],  # type: ignore[list-item]
        category_id=1,
        only_active=True,
        only_notes=True,
        sort="name",
        dir="DESC",
    )
    sent = sent_query(route)
    assert sent == {
        "categoryId": "1",
        "dir": "DESC",
        "filter": '[{"comparison":"eq","field":"number","value":"100"}]',
        "onlyActive": "true",
        "onlyNotes": "true",
        "query": "Projekt",
        "sort": "name",
    }
    assert result.meta.request == {"org": DEMO, **sent, "categoryId": 1}


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"dir": "up"}, "dir must be ASC or DESC, not 'up'"),
        (
            {"filter": [{"comparison": "equals", "field": "number", "value": "1"}]},
            "filter[0].comparison must be one of eq, like, gt, lt, not 'equals'",
        ),
        ({"query": 1}, "query must be a string, not int"),
    ],
)
def test_list_cost_centers_refuses_what_upstream_would_ignore(
    respx_mock: respx.MockRouter, arguments: dict[str, typing.Any], message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks.list_cost_centers(DEMO, **arguments)
    assert not respx_mock.calls


def test_list_cost_centers_is_a_post_route(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from xippios.cashctrl.http import router

    app = FastAPI()
    app.include_router(router)
    replay_fixture("account_costcenter_list", "default")
    client = TestClient(app)
    response = client.post("/cashctrl/list_cost_centers", json={"org": DEMO, "only_active": True})
    assert response.status_code == 200, response.text
    assert response.json()["meta"]["request"] == {"org": DEMO, "onlyActive": "true"}
    rejected = client.post("/cashctrl/list_cost_centers", json={"org": DEMO, "dir": "up"})
    assert rejected.status_code == 422


@pytest.mark.parametrize("model", [models.CustomField, models.CostCenter])
def test_the_unobserved_models_serialise_under_snake_case_names(
    model: type[UpstreamModel],
) -> None:
    """No record of these was observed (empty lists), so their field names are checked."""
    properties = model.model_json_schema(mode="serialization")["properties"]
    assert [name for name in properties if not SNAKE_CASE.fullmatch(name)] == []


def test_list_locations_replays_the_main_location(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("location_list", "default")
    result = tasks.list_locations(DEMO)
    assert sent_query(route) == {}, "the operation documents no parameters"
    assert result.meta.endpoint == "location/list.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total) == (DEMO, 1)
    (main,) = result.data
    assert isinstance(main, models.LocationProjection)
    assert (main.id, main.type, main.name, main.org_name) == (
        1,
        "MAIN",
        "Musterstandort",
        "Muster Handel AG (Demo)",
    )
    assert (main.address, main.street_name, main.street_number) == ("Musterhof 1", "Musterhof", "1")
    assert (main.zip, main.city, main.canton, main.country) == ("8001", "Zürich", "ZH", "CHE")
    assert (main.full_address or "").splitlines() == [
        "Muster Handel AG (Demo)",
        "Musterhof 1",
        "8001 Zürich",
        "Schweiz",
    ]
    assert (main.vat_uid, main.email, main.bank_account_id, main.attachments) == (
        None,
        None,
        None,
        [],
    )
    assert (main.is_inactive, main.created_by) == (False, "user@example.com"), "scrubbed"


def test_the_location_projection_leaves_out_iban_and_qr_iban_and_nothing_else() -> None:
    assert set(models.Location.model_fields) - set(models.LocationProjection.model_fields) == {
        "iban",
        "qr_iban",
    }
    assert set(models.LocationProjection.model_fields) < set(models.Location.model_fields)


@pytest.mark.anyio
async def test_the_location_wrapper_stays_faithful(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("location_list", "default")
    (location,) = (await api.location_list(DEMO)).data
    assert isinstance(location, models.Location)
    assert (location.iban, location.qr_iban, location.bic) == (None, None, None), "seen null"


@pytest.mark.anyio
async def test_list_locations_as_a_tool_leaves_out_the_bank_account_numbers(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("location_list", "default")
    payload = await mcp_call(server, "cashctrl_list_locations", {"org": DEMO})
    (main,) = payload["data"]
    assert (main["id"], main["type"], main["org_name"]) == (1, "MAIN", "Muster Handel AG (Demo)")
    assert not {"iban", "qr_iban", "qrIban"} & set(main)


def report_nodes(nodes: list[models.ReportTreeNode]) -> Iterator[models.ReportTreeNode]:
    """Every node of a report tree, depth first."""
    for node in nodes:
        yield node
        yield from report_nodes(node.data)


def test_get_report_tree_replays_the_default_reports(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    route = replay_fixture("report_tree", "default")
    result = tasks.get_report_tree(DEMO)
    assert sent_query(route) == {}, "the operation documents no parameters"
    assert result.meta.endpoint == "report/tree.json"
    assert result.meta.request == {"org": DEMO}
    assert (result.meta.tenant, result.meta.total) == (DEMO, 8), "upstream's top-level count"
    assert [node.id for node in result.data] == [
        "collection-1",
        "collection-3",
        "collection-5",
        "collection-6",
        "collection-7",
        "collection-8",
        "element-3",
        "element-14",
    ]
    annual = result.data[0]
    assert (annual.text, annual.leaf, annual.element_id, annual.type) == (
        "Jahresbericht",
        False,
        None,
        None,
    )
    balance, profit_loss = annual.data
    assert (balance.id, balance.element_id, balance.collection_id) == ("element-1", 1, 1)
    assert (balance.type, balance.type_name, balance.text, balance.leaf) == (
        "BALANCE",
        "Balance",
        "Bilanz",
        True,
    )
    assert (profit_loss.element_id, profit_loss.type) == (2, "PLS")
    nodes = list(report_nodes(result.data))
    elements = [node for node in nodes if node.leaf]
    assert (len(nodes), len(elements)) == (44, 38)
    assert all(node.element_id is not None and node.type for node in elements)
    assert len({node.element_id for node in elements}) == 38, "an element id names one report"
    statements = result.data[-2]
    assert (statements.type, statements.collection_id, statements.data) == ("STATEMENTS", None, [])


def test_get_report_data_replays_the_balance_sheet_of_2025(
    replay_fixture: Callable[[str, str], respx.Route], fixtures_dir: Path
) -> None:
    route = replay_fixture("report_element_data", "balance_fp2025")
    result = tasks.get_report_data(DEMO, 1, fiscal_period=FP2025)
    sent = sent_query(route)
    assert sent == {"elementId": "1", "fiscalPeriod": str(FP2025)}
    assert sent == recorded_query(recorded(fixtures_dir, "report_element_data", "balance_fp2025"))
    assert result.meta.endpoint == "report/element/data.json"
    assert result.meta.request == {"org": DEMO, "elementId": 1, "fiscalPeriod": FP2025}
    assert (result.meta.tenant, result.meta.total, result.data.total) == (DEMO, 2, 2)
    rows = result.data.data
    assert all(isinstance(row, dict) for row in rows)
    assets, liabilities = typing.cast(list[dict[str, typing.Any]], rows)
    assert (assets["text"], liabilities["text"]) == ("Assets", "Liabilities & Equity")
    assert assets["endAmount"] == liabilities["endAmount"] == 101709.56, "the sheet balances"
    assert "end_amount" not in assets, "kept as upstream sends it: camelCase, JSON numbers"

    def rows_below(row: dict[str, typing.Any]) -> Iterator[dict[str, typing.Any]]:
        yield row
        for child in row["data"]:
            yield from rows_below(child)

    every = [row for top in (assets, liabilities) for row in rows_below(top)]
    assert len(every) == 25
    # Account 1020, id 3, ends 2025 at 101'230.00 (docs/demo-org.md).
    (bank,) = [row for row in every if row["accountId"] == 3]
    assert (bank["text"], bank["endAmount"], bank["leaf"]) == ("1020 Bank account", 101230, True)
    properties = typing.cast(dict[str, typing.Any], result.data.properties)
    assert [column["title"] for column in properties["columns"]] == [
        "Label",
        "01/01/2025",
        "31/12/2025 (II)",
        "±%",
    ]


def test_get_report_data_drops_identifier_keys_at_any_depth(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """On the recorded balance sheet changed in memory: no recorded report holds them.

    A payroll or people report's rows may carry ``ssn`` or ``iban`` (ADR-0017; the demo
    organisation has no payroll), so the keys are injected in three letter cases, in a
    top-level row, in a row two levels down and in ``properties``. The task drops them
    and changes nothing else; the wrapper keeps them (ADR-0003).
    """
    original = recorded_body(fixtures_dir, "report_element_data", "balance_fp2025")
    changed = json.loads(json.dumps(original))
    top = changed["data"][0]
    nested = top["data"][0]["data"][0]
    top["ssn"] = SSN
    nested["IBAN"] = IBAN
    nested["qrIban"] = IBAN
    changed["properties"]["columns"][0]["Ssn"] = SSN
    respx_mock.get(f"{BASE}/report/element/data.json").respond(200, json=changed)
    result = tasks.get_report_data(DEMO, 1, fiscal_period=FP2025)
    assert result.data.data == original["data"], "the keys are gone, nothing else changed"
    assert result.data.properties == original["properties"]
    assert result.data.total == original["total"]
    assert SSN not in result.model_dump_json()
    assert IBAN not in result.model_dump_json()
    faithful = sync(api.report_element_data)(DEMO, 1, fiscal_period=FP2025)
    assert typing.cast(dict[str, typing.Any], faithful.data[0])["ssn"] == SSN


def test_get_report_data_sends_the_dates_as_upstream_reads_them(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """What is sent; the answer is the recorded one, which matches any query on the path."""
    route = replay_fixture("report_element_data", "balance_fp2025")
    result = tasks.get_report_data(
        DEMO,
        1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 30),
        language="en",
        sort="text",
    )
    sent = sent_query(route)
    assert sent == {
        "elementId": "1",
        "startDate": "2025-01-01",
        "endDate": "2025-06-30",
        "language": "en",
        "sort": "text",
    }
    assert result.meta.request == {"org": DEMO, **sent, "elementId": 1}


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            {"fiscal_period": 2, "start_date": date(2025, 1, 1)},
            "give fiscal_period or start_date and end_date, not both",
        ),
        (
            {"fiscal_period": 2, "end_date": date(2025, 12, 31)},
            "upstream derives the dates from the fiscal period and would ignore the ones given",
        ),
        ({"element_id": "1"}, "element_id must be a whole number, not '1'"),
        ({"element_id": True}, "element_id must be a whole number, not True"),
        ({"fiscal_period": "2"}, "fiscal_period must be a whole number, not '2'"),
        ({"start_date": "2025-01-01"}, "start_date must be a date (YYYY-MM-DD), not str"),
        (
            {"end_date": datetime(2025, 12, 31)},
            "end_date must be a date (YYYY-MM-DD), not datetime",
        ),
        ({"language": 1}, "language must be a string, not int"),
        ({"sort": ["text"]}, "sort must be a string, not list"),
    ],
)
def test_get_report_data_refuses_before_anything_is_sent(
    respx_mock: respx.MockRouter, arguments: dict[str, typing.Any], message: str
) -> None:
    arguments = {"element_id": 1, **arguments}
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks.get_report_data(DEMO, **arguments)
    assert not respx_mock.calls


@pytest.mark.anyio
async def test_get_report_data_as_a_tool(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    replay_fixture("report_element_data", "balance_fp2025")
    arguments = {"org": DEMO, "element_id": 1, "fiscal_period": FP2025}
    payload = await mcp_call(server, "cashctrl_get_report_data", arguments)
    assert payload["meta"]["total"] == payload["data"]["total"] == 2
    assert [row["text"] for row in payload["data"]["data"]] == ["Assets", "Liabilities & Equity"]
    both = {**arguments, "start_date": "2025-01-01"}
    text = await mcp_call_text(server, "cashctrl_get_report_data", both)
    assert text.startswith("error: InvalidRequestError: ")
    assert "give fiscal_period or start_date and end_date, not both" in text
    bad_date = {**arguments, "fiscal_period": None, "end_date": "31.12.2025"}
    text = await mcp_call_text(server, "cashctrl_get_report_data", bad_date)
    assert text.startswith("error: InvalidRequestError: end_date: ")


@pytest.mark.anyio
async def test_a_report_over_its_cap_is_a_note_naming_the_period_parameters(
    replay_fixture: Callable[[str, str], respx.Route],
) -> None:
    """``MCP_CAPS``'s note for ``get_report_data``, on the recorded sheet with a smaller bound.

    The recorded balance sheet, about 17 KB, fits the 128 KB the tool has, so the bound is
    lowered here and the note kept; the cut is core's (``cap_result``).
    """
    replay_fixture("report_element_data", "balance_fp2025")
    cap = dataclasses.replace(tasks.MCP_CAPS["get_report_data"], max_bytes=2_000)
    capped = build_server(SOURCE, [tasks.get_report_data], caps={"get_report_data": cap})
    arguments = {"org": DEMO, "element_id": 1, "fiscal_period": FP2025}
    payload = json.loads(await mcp_call_text(capped, "cashctrl_get_report_data", arguments))
    assert set(payload) == {"note", "preview"}
    assert payload["note"].startswith("result is ")
    assert payload["note"].endswith(
        "bytes, over the cap of 2000; narrow the period (fiscal_period, or start_date and "
        "end_date) or read a smaller report of get_report_tree to see the rest"
    )
    whole = await mcp_call(server, "cashctrl_get_report_data", arguments)
    assert "note" not in whole, "the tool's own cap, 128 KB, holds the recorded sheet"


def test_every_cap_names_a_task_and_only_parameters_it_takes() -> None:
    """A cap's note never promises a filter the tool lacks (ADR-0016)."""
    every_parameter = {
        name
        for task_name in tasks.__all__
        for name in inspect.signature(getattr(tasks, task_name)).parameters
    }
    assert set(tasks.MCP_CAPS) <= set(tasks.__all__)
    for name, cap in tasks.MCP_CAPS.items():
        named = set(re.findall(r"[a-z]+(?:_[a-z]+)*", cap.note or "")) & every_parameter
        assert named <= set(inspect.signature(getattr(tasks, name)).parameters), name
    assert {"query", "filter", "category_id", "only_active"} <= set(
        re.findall(r"[a-z]+(?:_[a-z]+)*", tasks.MCP_CAPS["list_cost_centers"].note or "")
    )
    assert {"order_id", "person_id", "statement_id", "query", "filter", "limit"} <= set(
        re.findall(r"[a-z]+(?:_[a-z]+)*", tasks.MCP_CAPS["list_history"].note or "")
    )


@pytest.mark.anyio
async def test_the_discovery_lists_and_reports_are_read_tools_and_routes() -> None:
    """Agents need their ids to form write calls: on the read server, never the write one.

    The book entries of an order and the history are reads too, served the same way.
    """
    from fastapi.routing import APIRoute

    from xippios.cashctrl.http import router
    from xippios.cashctrl.mcp_write import server as write_server

    new = [
        "list_custom_fields",
        "list_person_categories",
        "list_person_titles",
        "list_account_categories",
        "list_cost_centers",
        "list_locations",
        "get_report_tree",
        "get_report_data",
        "list_order_book_entries",
        "list_history",
    ]
    read_tools = {tool.name for tool in await server.list_tools()}
    write_tools = {tool.name for tool in await write_server.list_tools()}
    routes = {route.path for route in router.routes if isinstance(route, APIRoute)}
    for name in new:
        assert f"cashctrl_{name}" in read_tools
        assert f"cashctrl_{name}" not in write_tools
        assert f"/{SOURCE}/{name}" in routes


PAGED_LISTS: dict[str, Callable[..., typing.Any]] = {
    "list_journal_entries": tasks.list_journal_entries,
    "list_persons": tasks.list_persons,
    "list_orders": tasks.list_orders,
    "list_history": tasks.list_history,
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
    "list_history": ("history_list/order", {"order_id": BOOKED_ORDER}, 2),
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
    "order_category_list/default": (api.order_category_list, {}),
    "person_category_list/default": (api.person_category_list, {}),
    "person_title_list/default": (api.person_title_list, {}),
    "account_category_list/default": (api.account_category_list, {}),
    "location_list/default": (api.location_list, {}),
    "report_tree/default": (api.report_tree, {}),
    "order_bookentry_list/booked": (api.order_bookentry_list, {"id": BOOKED_ORDER}),
    "history_list/order": (api.history_list, {"order_id": BOOKED_ORDER, "start": 0, "limit": 100}),
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
    "cashctrl_list_order_categories": ("order_category_list/default", {}),
    "cashctrl_list_custom_fields": ("customfield_list/person", {"type": "PERSON"}),
    "cashctrl_list_person_categories": ("person_category_list/default", {}),
    "cashctrl_list_person_titles": ("person_title_list/default", {}),
    "cashctrl_list_account_categories": ("account_category_list/default", {}),
    "cashctrl_list_cost_centers": ("account_costcenter_list/default", {}),
    "cashctrl_list_locations": ("location_list/default", {}),
    "cashctrl_get_report_tree": ("report_tree/default", {}),
    "cashctrl_get_report_data": (
        "report_element_data/balance_fp2025",
        {"element_id": 1, "fiscal_period": FP2025},
    ),
    "cashctrl_list_order_book_entries": ("order_bookentry_list/booked", {"order_id": 5}),
    "cashctrl_list_history": ("history_list/order", {"order_id": 5}),
}
UNOBSERVED = frozenset({"cashctrl_list_custom_fields", "cashctrl_list_cost_centers"})
"""Tools whose recorded answer is an empty list: their snake_case names are checked on the
models instead (``test_the_unobserved_models_serialise_under_snake_case_names``)."""
AS_SENT: dict[str, frozenset[str]] = {"cashctrl_get_report_data": frozenset({"data", "properties"})}
"""Fields of a tool's ``data`` that hold upstream's JSON as sent (``JsonValue``, decided by
Johannes on 2026-10-27): their own names are snake_case, the keys inside them upstream's."""
SNAKE_CASES = {tool: case for tool, case in TOOL_CASES.items() if tool not in UNOBSERVED}


def test_every_task_has_a_tool_case() -> None:
    assert set(TOOL_CASES) == {tool_name(SOURCE, getattr(tasks, n)) for n in ORG_TASK_NAMES}


def tool_arguments(
    tool: str, case: tuple[str, dict[str, typing.Any]], fixtures_dir: Path
) -> dict[str, typing.Any]:
    """The arguments ``case`` was recorded with, as JSON: a read by id takes the recorded id."""
    arguments = case[1]
    query = recorded_query(recorded(fixtures_dir, *case[0].split("/")))
    if tool.startswith("cashctrl_get_") and "id" in query:
        arguments = {"id": int(query["id"])}
    return {
        key: [item.model_dump() for item in value] if key == "filter" else value
        for key, value in arguments.items()
    }


def snake_case_violations(data: object, as_sent: frozenset[str] = frozenset()) -> list[str]:
    """The keys of ``data``, at any depth, that are not snake_case; none must be.

    ``as_sent`` names fields of ``data`` that hold upstream's JSON as sent (``AS_SENT``):
    their names are checked, the keys inside them are not.
    """
    if isinstance(data, dict) and as_sent:
        data = {name: None if name in as_sent else value for name, value in data.items()}
    found = sorted(set(keys(data)))
    assert found, "a result without keys proves nothing"
    return [key for key in found if not SNAKE_CASE.fullmatch(key)]


@pytest.mark.anyio
@pytest.mark.parametrize(("tool", "case"), SNAKE_CASES.items(), ids=SNAKE_CASES.keys())
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
    assert snake_case_violations(payload["data"], AS_SENT.get(tool, frozenset())) == []


@pytest.mark.parametrize(("tool", "case"), SNAKE_CASES.items(), ids=SNAKE_CASES.keys())
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
    data = response.json()["data"]
    assert snake_case_violations(data, AS_SENT.get(tool, frozenset())) == []


@pytest.mark.parametrize(("tool", "case"), TOOL_CASES.items(), ids=TOOL_CASES.keys())
def test_every_task_names_its_organisation_as_the_tenant(
    replay_fixture: Callable[[str, str], respx.Route],
    fixtures_dir: Path,
    tool: str,
    case: tuple[str, dict[str, typing.Any]],
) -> None:
    """``meta.tenant`` is ``org``, by name (ADR-0014); ``org`` stays in ``meta.request``."""
    replay_fixture(*case[0].split("/"))
    task = getattr(tasks, tool.removeprefix("cashctrl_"))
    result = task(DEMO, **tool_arguments(tool, case, fixtures_dir))
    assert result.meta.tenant == DEMO
    assert result.meta.request["org"] == DEMO


@pytest.mark.anyio
@pytest.mark.parametrize(("tool", "case"), TOOL_CASES.items(), ids=TOOL_CASES.keys())
async def test_every_tool_names_its_organisation_as_the_tenant(
    replay_fixture: Callable[[str, str], respx.Route],
    fixtures_dir: Path,
    tool: str,
    case: tuple[str, dict[str, typing.Any]],
) -> None:
    replay_fixture(*case[0].split("/"))
    arguments = tool_arguments(tool, case, fixtures_dir)
    payload = await mcp_call(server, tool, {"org": DEMO, **arguments})
    assert payload["meta"]["tenant"] == DEMO


# The API user tag (G5 (2) of 2026-10-28, queue row 129). CashCtrl names the API user that
# wrote a record ``API:`` and the first four characters of its key in ``createdBy`` and
# ``lastUpdatedBy``; the recorder writes ``API:REDACTED``, and every model masks a live
# tag to the same, so a live answer has a fixture's shape.

LIVE_TAG = "API:Zq7k"
"""A tag shaped as upstream writes it, four made-up characters: tests only."""
AUDIT_KEYS = frozenset({"createdBy", "lastUpdatedBy"})
"""Where upstream writes who made or last changed a record, at any depth."""
AUDIT_FIELDS = frozenset({"created_by", "last_updated_by"})
"""The same fields as every model and every result names them."""
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def tagged(node: typing.Any, tag: str) -> tuple[typing.Any, int]:
    """``node`` with every ``createdBy`` and ``lastUpdatedBy`` value made ``tag``, and how many."""
    if isinstance(node, dict):
        count = 0
        changed: dict[str, typing.Any] = {}
        for name, value in node.items():
            if name in AUDIT_KEYS:
                changed[name], count = tag, count + 1
            else:
                changed[name], found = tagged(value, tag)
                count += found
        return changed, count
    if isinstance(node, list):
        items = [tagged(item, tag) for item in node]
        return [item for item, _ in items], sum(found for _, found in items)
    return node, 0


def audit_values(node: object) -> Iterator[object]:
    """Every value of a ``created_by`` or ``last_updated_by`` key in a dumped result."""
    if isinstance(node, dict):
        for name, value in node.items():
            if name in AUDIT_FIELDS:
                yield value
            else:
                yield from audit_values(value)
    elif isinstance(node, list):
        for item in node:
            yield from audit_values(item)


def _audited(fixture: str) -> bool:
    body = json.loads(load_fixture(FIXTURES / f"{fixture}.json").response.body)
    return tagged(body, LIVE_TAG)[1] > 0


AUDITED_CASES = {tool: case for tool, case in TOOL_CASES.items() if _audited(case[0])}
"""Every tool whose recorded answer names who wrote its records: each model family once."""


def test_the_audited_cases_cover_every_model_family() -> None:
    reports = {"cashctrl_get_report_tree", "cashctrl_get_report_data"}
    assert set(TOOL_CASES) - set(AUDITED_CASES) == reports | UNOBSERVED, (
        "every recorded answer but the reports and the empty ones names who wrote its records"
    )


@pytest.mark.anyio
@pytest.mark.parametrize(("tool", "case"), AUDITED_CASES.items(), ids=AUDITED_CASES.keys())
async def test_every_model_family_masks_a_live_api_user_tag(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    tool: str,
    case: tuple[str, dict[str, typing.Any]],
) -> None:
    """On the recorded answer changed in memory: every author put back as a live tag.

    The task's result and the tool's carry ``API:REDACTED`` wherever the answer carried
    the tag, nested records (a journal entry's ``associates``, an order category's
    statuses) included, and the tag nowhere.
    """
    fixture = recorded(fixtures_dir, *case[0].split("/"))
    body, count = tagged(json.loads(fixture.response.body), LIVE_TAG)
    assert count > 0
    respx_mock.get(str(httpx.URL(fixture.request.url).copy_with(query=None))).respond(
        200, json=body
    )
    arguments = tool_arguments(tool, case, fixtures_dir)
    task = getattr(tasks, f"{tool.removeprefix('cashctrl_')}_async")
    result = await task(DEMO, **arguments)
    users = list(audit_values(result.model_dump(mode="json")["data"]))
    assert users
    assert set(users) == {models.API_USER_MASK}
    payload = await mcp_call(server, tool, {"org": DEMO, **arguments})
    assert set(audit_values(payload["data"])) == {models.API_USER_MASK}
    assert LIVE_TAG.lower() not in json.dumps(payload).lower()


@pytest.mark.parametrize(
    ("sent", "kept"),
    [
        (LIVE_TAG, "API:REDACTED"),
        ("api:zq7k", "API:REDACTED"),
        ("API:Zq-7", "API:REDACTED"),
        ("API:REDACTED", "API:REDACTED"),
        ("SYSTEM", "SYSTEM"),
        ("user@example.com", "user@example.com"),
        ("Anna Muster", "Anna Muster"),
        ("XAPI:Zq7k", "XAPI:Zq7k"),
        ("", ""),
        (None, None),
    ],
)
def test_the_mask_rewrites_an_api_user_tag_and_nothing_else(sent: str | None, kept: str) -> None:
    """A text starting with ``API:``, in any letter case, is masked whole; the rest passes."""
    by_alias = models.HistoryEntry.model_validate({"id": 1, "createdBy": sent})
    by_name = models.Currency.model_validate(
        {
            "id": 1,
            "code": "CHF",
            "default": True,
            "isDefault": True,
            "auto": False,
            "isAuto": False,
            "last_updated_by": sent,
        }
    )
    assert (by_alias.created_by, by_name.last_updated_by) == (kept, kept)


def test_every_model_with_an_author_field_masks_it() -> None:
    """``created_by`` and ``last_updated_by`` are ``AuditUser`` wherever a model has them."""
    found: list[tuple[str, str]] = []
    for name in dir(models):
        model = getattr(models, name)
        if not (isinstance(model, type) and issubclass(model, UpstreamModel)):
            continue
        for field in sorted(AUDIT_FIELDS & set(model.model_fields)):
            metadata = model.model_fields[field].metadata
            masks = [
                item
                for item in metadata
                if isinstance(item, BeforeValidator) and item.func is models._mask_api_user
            ]
            assert masks, f"{name}.{field} is not AuditUser"
            found.append((name, field))
    assert {"FiscalPeriod", "Person", "PersonDetailProjection", "CustomField", "CostCenter"} <= {
        name for name, _ in found
    }
    assert ("HistoryEntry", "created_by") in found


def test_no_fixture_carries_an_api_user_tag_but_the_mask(fixtures_dir: Path) -> None:
    """Fixtures hold ``API:REDACTED`` only, so a replayed answer and a live one look alike."""
    tags = {
        tag
        for path in sorted(fixtures_dir.rglob("*.json"))
        for tag in re.findall(r"API:[A-Za-z0-9]+", path.read_text(encoding="utf-8"), re.IGNORECASE)
    }
    assert tags == {models.API_USER_MASK}
