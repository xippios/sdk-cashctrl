"""Live smoke tests: skipped unless XIPPIOS_LIVE_TESTS=1 (conventions §10).

Every task function gets a live smoke test here, next to the reachability check. Every
live test takes the ``demo_org`` fixture: live runs reach the demo organisation only, whose
books are synthetic (``scripts/seed_demo.py``). Each read test makes one call, but the
reads, which first look an id up in a list (account 1020 by number, the first journal
entry, person and sales order), ``list_order_book_entries``, which first lists the
purchase orders for one that books, and ``get_report_data``, which first reads the report
tree for the balance sheet's element id. ``fiscal_periods`` looks the fiscal periods up
once for the module: the API user's current period is 2025, and the orders are in 2026.

The write tools are tested live per resource, one test that calls each of its write
tools once with ``confirm=True`` (create, update, delete), so that every record a test
creates is deleted by the same test (decision 5 of the wave 2 interview, 2026-10-23):

- every record carries the marker ``xippios-live`` (``MARK``) in its title, company or
  description, and ``nr`` where it has one, so that no sequence number advances;
- before it writes, a test sweeps the leftovers of an earlier run: it lists its
  resource with ``query=xippios-live`` (the journal and the orders in 2026, where the
  tests write) and deletes every record whose marked field holds the marker or whose
  ``nr`` is the marker;
- an update is previewed first (its ``before`` is the record as stored), confirmed,
  and the record read back: the changed field holds the new value and every other
  field the update derives is unchanged, the end-to-end proof that an update sends the
  whole record; an order's items, sent back unchanged when no ``items`` are given, come
  back as they were but for their ids, and ``items`` given replace them;
- it deletes what it created by id with the delete tool, and a ``finally`` deletes it
  through the endpoint wrapper should an assertion fail first. A confirmed journal
  delete reads the entry first and refuses one an order or a salary run booked.

That refusal is checked live once, read-only: a delete without ``confirm`` of an entry a
seeded purchase order booked, found with GET calls, is refused before any preview.

The calls of one run: 29 for the reads (17, 9 for the discovery lists and the reports:
one each, and the tree ``get_report_data`` reads first, and 3 for the book entries of an
order, with the list of purchase orders they read first, and the history), 4 lookups
(accounts, tax codes, customers, the sales categories), 9 for the journal (sweep,
create, the sweep's query seeing the new entry, the update's preview, the update as read
and write, the read back, the delete as read and write), 7 for a person (the same
without the query, the delete one call), 10 for an order (sweep, create, the update's
preview, two updates as read and write, the first without items and the second with,
each read back, the delete) and 2 for the refused delete of an entry an order booked
(the list, the delete's read); 61 in all, one more per leftover swept, two for a journal
entry.
"""

import json
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from xippios.core import InvalidRequestError

from xippios.cashctrl import api, tasks, tasks_write
from xippios.cashctrl._client import DEMO, TENANTS, client_for
from xippios.cashctrl.models import (
    Filter,
    JournalEntryDetail,
    JournalEntryDetailProjection,
    OrderCategory,
    OrderDetail,
    PersonDetail,
    PersonDetailProjection,
    WritePreview,
    WriteResult,
)

MARK = "xippios-live"
"""The marker every record a live test creates carries, and the query its sweep lists."""
DAY = date(2026, 10, 24)
"""The date of every record a live test creates: in 2026, a fiscal period the seed holds."""

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


async def test_list_order_book_entries(demo_org: str, fiscal_periods: dict[str, int]) -> None:
    # A seeded purchase order in a status that books (docs/demo-org.md: both do, each
    # booked one entry); its id comes from the list, never from a constant.
    period = fiscal_periods["2026"]
    orders = await tasks.list_orders_async(
        demo_org, type="PURCHASE", fiscal_period_id=period, limit=20
    )
    booked = [order for order in orders.data if order.is_book]
    assert booked, "no purchase order of 2026 books; the seeded two do"
    result = await tasks.list_order_book_entries_async(demo_org, booked[0].id)
    assert result.meta.request == {"org": demo_org, "id": booked[0].id}
    assert result.meta.total == len(result.data) > 0
    assert all(entry.order_id == booked[0].id for entry in result.data)
    assert all(isinstance(entry.amount, Decimal) for entry in result.data)
    assert all(entry.rows for entry in result.data)


async def test_list_history(demo_org: str) -> None:
    result = await tasks.list_history_async(demo_org, limit=5)
    assert result.meta.request == {"org": demo_org, "start": 0, "limit": 5}
    assert 0 < len(result.data) <= 5
    assert result.meta.total is not None
    assert result.meta.total >= len(result.data)
    created = [entry.created for entry in result.data if entry.created is not None]
    assert created == sorted(created, reverse=True), "newest first, upstream's default"


@pytest.fixture(scope="module")
def write_ids(fiscal_periods: dict[str, int]) -> dict[str, int]:
    """The ids the write tests book with, looked up once: never constants.

    Accounts 1020 and 3200 by number, the tax code ``UN1`` by code, the first customer
    that no live test created (a leftover of an interrupted run could be one), and the
    2026 fiscal period.
    """
    names = TENANTS.names()
    assert names == (DEMO,), "live tests run against the demo organisation and nothing else"
    numbers = Filter(comparison="eq", field="number", value=["1020", "3200"])
    accounts = {a.number: a.id for a in tasks.list_accounts(DEMO, filter=[numbers]).data}
    taxes = {tax.code: tax.id for tax in tasks.list_tax_codes(DEMO).data}
    customers = tasks.list_persons(DEMO, only_customers=True, limit=20).data
    customer = next(person for person in customers if not marked(person.company, person.nr))
    return {
        "bank": accounts["1020"],
        "revenue": accounts["3200"],
        "un1": taxes["UN1"],
        "customer": customer.id,
        "fp2026": fiscal_periods["2026"],
    }


@pytest.fixture(scope="module")
def sales_categories() -> list[OrderCategory]:
    """``list_order_categories`` called once, live: its smoke test and the order test use it."""
    names = TENANTS.names()
    assert names == (DEMO,), "live tests run against the demo organisation and nothing else"
    result = tasks.list_order_categories(DEMO)
    assert result.meta.tenant == DEMO
    assert result.meta.total == len(result.data)
    return result.data


def test_list_order_categories(demo_org: str, sales_categories: list[OrderCategory]) -> None:
    assert sales_categories
    assert {category.type for category in sales_categories} == {"SALES"}
    assert all(category.status for category in sales_categories if not category.is_inactive)


async def test_list_custom_fields(demo_org: str) -> None:
    result = await tasks.list_custom_fields_async(demo_org, "PERSON")
    assert result.meta.request == {"org": demo_org, "type": "PERSON"}
    assert result.meta.tenant == demo_org
    assert result.meta.total == len(result.data), "the demo organisation has none (2026-10-27)"


async def test_list_person_categories(demo_org: str) -> None:
    result = await tasks.list_person_categories_async(demo_org)
    assert result.data
    assert result.meta.total == len(result.data)
    ids = {category.id for category in result.data}
    assert all(category.parent_id in ids for category in result.data if category.parent_id)


async def test_list_person_titles(demo_org: str) -> None:
    result = await tasks.list_person_titles_async(demo_org)
    assert result.data
    assert result.meta.total == len(result.data)
    assert {title.gender for title in result.data} <= {"MALE", "FEMALE", None}


async def test_list_account_categories(demo_org: str) -> None:
    result = await tasks.list_account_categories_async(demo_org)
    assert result.meta.total == len(result.data) > 0
    ids = {category.id for category in result.data}
    assert all(category.parent_id in ids for category in result.data if category.parent_id)
    assert any(category.parent_id is None for category in result.data)


async def test_list_cost_centers(demo_org: str) -> None:
    result = await tasks.list_cost_centers_async(demo_org, only_active=True)
    assert result.meta.request == {"org": demo_org, "onlyActive": "true"}
    assert result.meta.total == len(result.data), "the demo organisation has none (2026-10-27)"


async def test_list_locations(demo_org: str) -> None:
    result = await tasks.list_locations_async(demo_org)
    assert result.meta.total == len(result.data) > 0
    assert "MAIN" in {location.type for location in result.data}
    assert all(not hasattr(location, "iban") for location in result.data)


async def test_get_report_tree(demo_org: str) -> None:
    result = await tasks.get_report_tree_async(demo_org)
    assert result.data
    assert result.meta.total == len(result.data), "upstream counts the top-level nodes"
    elements = [node for top in result.data for node in [top, *top.data] if node.leaf]
    assert all(node.element_id is not None for node in elements)


async def test_get_report_data(demo_org: str, fiscal_periods: dict[str, int]) -> None:
    # The balance sheet of 2025, as report_element_data/balance_fp2025.json recorded it;
    # its element id comes from the tree, never from a constant.
    tree = await tasks.get_report_tree_async(demo_org)
    (balance, *_) = [
        node for top in tree.data for node in [top, *top.data] if node.type == "BALANCE"
    ]
    assert balance.element_id is not None
    period = fiscal_periods["2025"]
    result = await tasks.get_report_data_async(demo_org, balance.element_id, fiscal_period=period)
    assert result.meta.request == {
        "org": demo_org,
        "elementId": balance.element_id,
        "fiscalPeriod": period,
    }
    assert result.meta.total == result.data.total == len(result.data.data) > 0
    assert all(isinstance(row, dict) and "text" in row for row in result.data.data)


def marked(text: str | None, nr: str | None = None) -> bool:
    """Whether a record carries the marker in its marked field or as its ``nr``."""
    return MARK in (text or "") or nr == MARK


def journal_values(entry: JournalEntryDetailProjection) -> dict[str, Any]:
    """The parameters ``update_journal_entry`` derives from ``entry``, as a task returned it.

    The tasks return projections (ADR-0017), and ``_journal_values`` takes the read
    model, so it is rebuilt from the projection: only its persons lack ``ssn`` and
    ``iban``, which no journal parameter reads.
    """
    values, _ = tasks_write._journal_values(JournalEntryDetail.model_validate(entry.model_dump()))
    return values


def person_values(person: PersonDetailProjection) -> dict[str, Any]:
    """The parameters ``update_person`` derives from ``person``, as a task returned it.

    Rebuilt as the read model from the projection, which leaves out ``ssn`` and each bank
    account's ``iban`` (ADR-0017): the test person holds neither, so ``ssn`` compares as
    empty on both sides.
    """
    values, _, _ = tasks_write._person_values(PersonDetail.model_validate(person.model_dump()))
    return values


def order_values(order: OrderDetail) -> dict[str, Any]:
    """The parameters ``update_order`` derives from ``order``, its items included."""
    values, _ = tasks_write._order_values(order)
    return values


def item_values(order: OrderDetail) -> list[dict[str, Any]]:
    """The order's items as stored, every field but the id upstream gives them anew."""
    return [item.model_dump(exclude={"id"}) for item in order.items]


def derived_except(values: dict[str, Any], changed: str) -> dict[str, Any]:
    """The fields an update derives from the record, but the one the test changed."""
    return {name: value for name, value in values.items() if name != changed}


def performed(result: Any) -> WriteResult:
    """The ``WriteResult`` of a confirmed write, for the organisation the test named."""
    assert result.meta.tenant == DEMO
    assert isinstance(result.data, WriteResult)
    assert result.data.performed is True
    return result.data


async def test_journal_entry_create_update_delete(demo_org: str, write_ids: dict[str, int]) -> None:
    period = write_ids["fp2026"]
    leftovers = await tasks.list_journal_entries_async(
        demo_org, query=MARK, fiscal_period_id=period, limit=50
    )
    for entry in leftovers.data:
        if marked(entry.title):
            performed(
                await tasks_write.delete_journal_entry_async(demo_org, entry.id, confirm=True)
            )
    arguments: dict[str, Any] = {
        "date_added": DAY,
        "amount": Decimal("100.00"),
        "debit_id": write_ids["bank"],
        "credit_id": write_ids["revenue"],
        "tax_id": write_ids["un1"],
        "title": f"{MARK} test",
    }
    preview = await tasks_write.create_journal_entry_async(demo_org, **arguments)
    assert isinstance(preview.data, WritePreview)
    created: int | None = None
    try:
        result = await tasks_write.create_journal_entry_async(demo_org, **arguments, confirm=True)
        created = performed(result).insert_id
        assert isinstance(created, int)
        assert result.meta.request == {"org": demo_org, **preview.data.payload}
        found = await tasks.list_journal_entries_async(
            demo_org, query=MARK, fiscal_period_id=period, limit=50
        )
        assert created in {entry.id for entry in found.data}, "the sweep's query finds it"
        title = f"{MARK} test updated"
        planned = await tasks_write.update_journal_entry_async(demo_org, created, title=title)
        assert isinstance(planned.data, WritePreview)
        assert isinstance(planned.data.before, JournalEntryDetailProjection)
        before = journal_values(planned.data.before)
        updated = await tasks_write.update_journal_entry_async(
            demo_org, created, title=title, confirm=True
        )
        assert performed(updated).insert_id == created
        assert updated.meta.request["debitId"] == str(write_ids["bank"]), "the whole record"
        read_back = await tasks.get_journal_entry_async(demo_org, created)
        after = journal_values(read_back.data)
        assert after["title"] == title
        assert derived_except(after, "title") == derived_except(before, "title")
        deleted = await tasks_write.delete_journal_entry_async(demo_org, created, confirm=True)
        assert performed(deleted).message
        created = None
    finally:
        if created is not None:
            await api.journal_delete(demo_org, [created])


async def test_delete_journal_entry_refuses_an_entry_an_order_booked(
    demo_org: str, fiscal_periods: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The preview of a delete of an entry an order booked is refused; GET calls only.

    The journal of 2026 is listed with ``only_purchase`` ("Flag to only include purchase
    order book entries", ``docs/upstream/journal.md`` line 47): the seeded purchase
    orders booked two (``journal_list/order_booked``, recorded on 2026-10-26). The first
    entry that names its order (``order_id`` or ``order_book_entry_id``, marks the delete
    refuses) is deleted without ``confirm``: the task reads it and refuses it before any
    preview. Nothing is created or deleted, and the delete wrapper is replaced by one
    that fails the test.
    """

    async def no_delete(org: str, ids: Sequence[int]) -> Any:
        raise AssertionError("a delete without confirm never deletes")

    monkeypatch.setattr(api, "journal_delete", no_delete)
    listed = await tasks.list_journal_entries_async(
        demo_org, fiscal_period_id=fiscal_periods["2026"], only_purchase=True, limit=20
    )
    booked = [
        entry
        for entry in listed.data
        if entry.order_id is not None or entry.order_book_entry_id is not None
    ]
    assert booked, "no entry a purchase order booked in 2026; journal_list/order_booked has two"
    entry = booked[0]
    with pytest.raises(
        InvalidRequestError,
        match=rf"journal entry {entry.id} was booked by an order or a salary run "
        r"\((orderId|orderBookEntryId)[^)]* set\); upstream documents that such entries "
        "cannot be deleted here",
    ):
        await tasks_write.delete_journal_entry_async(demo_org, entry.id)


async def test_person_create_update_delete(demo_org: str) -> None:
    leftovers = await tasks.list_persons_async(demo_org, query=MARK, limit=50)
    for person in leftovers.data:
        if marked(person.company, person.nr):
            performed(await tasks_write.delete_person_async(demo_org, person.id, confirm=True))
    created: int | None = None
    try:
        result = await tasks_write.create_person_async(
            demo_org,
            company=f"{MARK} Test GmbH",
            addresses=[{"type": "MAIN", "city": "Zürich", "country": "CHE"}],  # type: ignore[list-item]
            contacts=[{"type": "EMAIL_WORK", "address": "user@example.com"}],  # type: ignore[list-item]
            is_customer=True,
            nr=MARK,
            confirm=True,
        )
        created = performed(result).insert_id
        assert isinstance(created, int)
        planned = await tasks_write.update_person_async(demo_org, created, department=MARK)
        assert isinstance(planned.data, WritePreview)
        assert isinstance(planned.data.before, PersonDetailProjection)
        before = person_values(planned.data.before)
        updated = await tasks_write.update_person_async(
            demo_org, created, department=MARK, confirm=True
        )
        assert performed(updated).insert_id == created
        assert updated.meta.request["company"] == f"{MARK} Test GmbH", "the whole record"
        read_back = await tasks.get_person_async(demo_org, created)
        after = person_values(read_back.data)
        assert after["department"] == MARK
        assert derived_except(after, "department") == derived_except(before, "department")
        deleted = await tasks_write.delete_person_async(demo_org, created, confirm=True)
        assert performed(deleted).message
        created = None
    finally:
        if created is not None:
            await api.person_delete(demo_org, [created])


async def test_order_create_update_delete(
    demo_org: str, write_ids: dict[str, int], sales_categories: list[OrderCategory]
) -> None:
    (invoice,) = [
        category
        for category in sales_categories
        if "<en>Invoice</en>" in (category.name_singular or "") and not category.is_inactive
    ]
    leftovers = await tasks.list_orders_async(
        demo_org, query=MARK, fiscal_period_id=write_ids["fp2026"], limit=50
    )
    for order in leftovers.data:
        if marked(order.description, order.nr):
            performed(await tasks_write.delete_order_async(demo_org, order.id, confirm=True))
    revenue, un1 = write_ids["revenue"], write_ids["un1"]
    created: int | None = None
    try:
        result = await tasks_write.create_order_async(
            demo_org,
            associate_id=write_ids["customer"],
            category_id=invoice.id,
            date=DAY,
            nr=MARK,
            description=f"{MARK} test",
            status_id=invoice.status[0].id,
            items=[
                {  # type: ignore[list-item]
                    "account_id": revenue,
                    "name": f"{MARK} item",
                    "unit_price": Decimal("100.00"),
                    "tax_id": un1,
                },
                {  # type: ignore[list-item]
                    "account_id": revenue,
                    "name": f"{MARK} second item",
                    "description": MARK,
                    "unit_price": Decimal("45.50"),
                    "quantity": Decimal(3),
                    "tax_id": un1,
                },
            ],
            confirm=True,
        )
        created = performed(result).insert_id
        assert isinstance(created, int)
        description = f"{MARK} test updated"
        planned = await tasks_write.update_order_async(demo_org, created, description=description)
        assert isinstance(planned.data, WritePreview)
        before = planned.data.before
        assert isinstance(before, OrderDetail)
        assert [item.name for item in before.items] == [f"{MARK} item", f"{MARK} second item"]
        updated = await tasks_write.update_order_async(
            demo_org, created, description=description, confirm=True
        )
        assert performed(updated).insert_id == created
        assert json.loads(updated.meta.request["items"]) == json.loads(
            planned.data.payload["items"]
        ), "the stored items sent back"
        read_back = (await tasks.get_order_async(demo_org, created)).data
        assert read_back.description == description
        assert item_values(read_back) == item_values(before), "every item as it was, but its id"
        assert derived_except(order_values(read_back), "description") == derived_except(
            order_values(before), "description"
        )
        assert (read_back.sub_total, read_back.tax, read_back.total) == (
            before.sub_total,
            before.tax,
            before.total,
        )
        replacement = {
            "account_id": revenue,
            "name": f"{MARK} replaced",
            "unit_price": Decimal("250.00"),
            "quantity": Decimal(2),
            "tax_id": un1,
        }
        replaced = await tasks_write.update_order_async(
            demo_org,
            created,
            items=[replacement],  # type: ignore[list-item]
            confirm=True,
        )
        assert performed(replaced).insert_id == created
        after = (await tasks.get_order_async(demo_org, created)).data
        assert [
            (item.name, item.quantity, item.unit_price, item.account_id, item.tax_id)
            for item in after.items
        ] == [(f"{MARK} replaced", Decimal(2), Decimal(250), revenue, un1)]
        assert after.total == Decimal(500), "two units at 250.00, read as gross"
        assert derived_except(order_values(after), "items") == derived_except(
            order_values(read_back), "items"
        ), "the header carried back with the new items"
        deleted = await tasks_write.delete_order_async(demo_org, created, confirm=True)
        assert performed(deleted).message
        created = None
    finally:
        if created is not None:
            await api.order_delete(demo_org, [created])
