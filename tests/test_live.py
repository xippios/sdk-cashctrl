"""Live smoke tests: skipped unless XIPPIOS_LIVE_TESTS=1 (conventions §10).

Every task function gets one live smoke test here, next to the reachability check. Every
live test takes the ``demo_org`` fixture: live runs reach the demo organisation only.
Each test makes one read-only call.
"""

from datetime import date
from decimal import Decimal

import pytest

from xippios.cashctrl import tasks
from xippios.cashctrl._client import client_for

pytestmark = [pytest.mark.live, pytest.mark.anyio]


async def test_upstream_answers(demo_org: str) -> None:
    client = client_for(demo_org)
    response = await client.request("GET", "/fiscalperiod/list.json", raise_on_error=False)
    assert response.status_code == 200


async def test_list_fiscal_periods(demo_org: str) -> None:
    result = await tasks.list_fiscal_periods_async(demo_org)
    assert result.data
    assert all(isinstance(period.start, date) for period in result.data)
    assert result.meta.request == {"org": demo_org}


async def test_list_currencies(demo_org: str) -> None:
    result = await tasks.list_currencies_async(demo_org)
    assert result.data
    assert sum(currency.is_default for currency in result.data) == 1


async def test_list_tax_codes(demo_org: str) -> None:
    result = await tasks.list_tax_codes_async(demo_org)
    assert result.data
    assert all(tax.rates for tax in result.data)


async def test_list_accounts(demo_org: str) -> None:
    # Narrowed as the recorded fixture is: never the whole chart with its balances.
    result = await tasks.list_accounts_async(demo_org, only_active=True, query="Abschreibungen")
    assert result.meta.request == {"org": demo_org, "onlyActive": "true", "query": "Abschreibungen"}
    assert result.data
    assert all(isinstance(account.end_amount, Decimal | None) for account in result.data)


async def test_get_account(demo_org: str) -> None:
    # The account recorded in tests/fixtures/account_read/by_id.json.
    result = await tasks.get_account_async(demo_org, 223)
    assert result.data.id == 223
    assert result.data.number
