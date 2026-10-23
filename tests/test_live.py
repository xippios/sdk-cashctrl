"""Live smoke tests: skipped unless XIPPIOS_LIVE_TESTS=1 (conventions §10).

Every task function gets one live smoke test here, next to the reachability check. Every
live test takes the ``demo_org`` fixture: live runs reach the demo organisation only, whose
books are synthetic (``scripts/seed_demo.py``). Each test makes one read-only call, but
``test_get_account``, which first looks account 1020 up by number.
"""

from datetime import date
from decimal import Decimal

import pytest

from xippios.cashctrl import tasks
from xippios.cashctrl._client import client_for
from xippios.cashctrl.models import Filter

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
