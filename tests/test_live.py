"""Live smoke tests: skipped unless XIPPIOS_LIVE_TESTS=1 (conventions §10).

Every task function gets one live smoke test here, next to the reachability check. Every
live test takes the ``demo_org`` fixture: live runs reach the demo organisation only, whose
books are synthetic (``scripts/seed_demo.py``). Each test makes one read-only call, but
the reads, which first look an id up in a list (account 1020 by number, the first journal
entry, person and sales order). ``fiscal_periods`` looks the fiscal periods up once for
the module: the API user's current period is 2025, and the orders are in 2026.
"""

from datetime import date
from decimal import Decimal

import pytest

from xippios.cashctrl import tasks
from xippios.cashctrl._client import DEMO, TENANTS, client_for
from xippios.cashctrl.models import Filter

pytestmark = [pytest.mark.live, pytest.mark.anyio]


@pytest.fixture(scope="module")
def fiscal_periods() -> dict[str, int]:
    """The demo organisation's fiscal period ids by name (``2025``, ``2026``), read once."""
    names = TENANTS.names()
    assert names == (DEMO,), "live tests run against the demo organisation and nothing else"
    return {
        period.name: period.id
        for period in tasks.list_fiscal_periods(DEMO).data
        if period.name is not None
    }


async def test_upstream_answers(demo_org: str) -> None:
    client = client_for(demo_org)
    response = await client.request("GET", "/fiscalperiod/list.json", raise_on_error=False)
    assert response.status_code == 200


def test_list_organisations(demo_org: str) -> None:
    """Names only, and no request: the live environment declares the demo organisation alone."""
    result = tasks.list_organisations()
    assert result.data == [demo_org] == ["demo"]
    assert result.meta.tenant is None


async def test_list_fiscal_periods(demo_org: str) -> None:
    result = await tasks.list_fiscal_periods_async(demo_org)
    assert result.data
    assert all(isinstance(period.start, date) for period in result.data)
    assert result.meta.request == {"org": demo_org}
    assert result.meta.tenant == demo_org


async def test_list_currencies(demo_org: str) -> None:
    result = await tasks.list_currencies_async(demo_org)
    assert result.data
    assert sum(currency.is_default for currency in result.data) == 1


async def test_list_tax_codes(demo_org: str) -> None:
    result = await tasks.list_tax_codes_async(demo_org)
    assert result.data
    assert all(tax.rates for tax in result.data)


async def test_list_accounts(demo_org: str) -> None:
    # Narrowed as the recorded fixture is: the default chart of 139 accounts is too much.
    result = await tasks.list_accounts_async(demo_org, only_active=True, query="Finanz")
    assert result.meta.request == {"org": demo_org, "onlyActive": "true", "query": "Finanz"}
    assert result.data
    assert all(isinstance(account.end_amount, Decimal | None) for account in result.data)


async def test_get_account(demo_org: str) -> None:
    # Account 1020, the bank account of the default chart, as account_read/by_id.json
    # recorded it; its id comes from the list, never from a constant.
    number = Filter(comparison="eq", field="number", value="1020")
    (listed,) = (await tasks.list_accounts_async(demo_org, filter=[number])).data
    result = await tasks.get_account_async(demo_org, listed.id)
    assert (result.data.id, result.data.number) == (listed.id, "1020")


async def test_list_journal_entries(demo_org: str, fiscal_periods: dict[str, int]) -> None:
    period = fiscal_periods["2025"]
    result = await tasks.list_journal_entries_async(demo_org, fiscal_period_id=period, limit=5)
    assert result.meta.request == {
        "org": demo_org,
        "fiscalPeriodId": period,
        "start": 0,
        "limit": 5,
    }
    assert 0 < len(result.data) <= 5
    assert result.meta.total is not None
    assert result.meta.total >= len(result.data)
    assert all(isinstance(entry.amount, Decimal) for entry in result.data)
    assert all(entry.date_added.year == 2025 for entry in result.data)


async def test_get_journal_entry(demo_org: str) -> None:
    # The newest entry of the current fiscal period; its id comes from the list.
    (listed,) = (await tasks.list_journal_entries_async(demo_org, limit=1)).data
    result = await tasks.get_journal_entry_async(demo_org, listed.id)
    assert (result.data.id, result.data.amount) == (listed.id, listed.amount)
    assert result.data.rows


async def test_list_persons(demo_org: str) -> None:
    result = await tasks.list_persons_async(demo_org, only_vendors=True)
    assert result.meta.request == {"org": demo_org, "onlyVendors": "true", "start": 0}
    assert result.data
    assert result.meta.total == len(result.data)
    assert all(person.is_vendor for person in result.data)


async def test_get_person(demo_org: str) -> None:
    (listed,) = (await tasks.list_persons_async(demo_org, limit=1)).data
    result = await tasks.get_person_async(demo_org, listed.id)
    assert (result.data.id, result.data.name) == (listed.id, listed.name)


async def test_list_orders(demo_org: str, fiscal_periods: dict[str, int]) -> None:
    period = fiscal_periods["2026"]
    result = await tasks.list_orders_async(demo_org, type="SALES", fiscal_period_id=period)
    assert result.data
    assert result.meta.total == len(result.data)
    assert all(order.type == "SALES" for order in result.data)
    assert all(isinstance(order.total, Decimal) for order in result.data)


async def test_get_order(demo_org: str, fiscal_periods: dict[str, int]) -> None:
    period = fiscal_periods["2026"]
    orders = await tasks.list_orders_async(demo_org, type="SALES", fiscal_period_id=period, limit=1)
    (listed,) = orders.data
    result = await tasks.get_order_async(demo_org, listed.id)
    assert (result.data.id, result.data.nr, result.data.total) == (
        listed.id,
        listed.nr,
        listed.total,
    )
    assert result.data.items
