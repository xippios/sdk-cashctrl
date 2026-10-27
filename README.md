# xippios-cashctrl

Typed Python client, MCP server and FastAPI routes for
[CashCtrl](https://cashctrl.com), part of the
[xippios SDK family](https://github.com/xippios). Names and semantics follow the
upstream documentation; every response carries release metadata (source, endpoint,
retrieved_at, published_at, vintage).

## Install

```bash
uv add xippios-cashctrl            # client only
uv add "xippios-cashctrl[mcp]"     # + MCP server
uv add "xippios-cashctrl[http]"    # + FastAPI router
```

## Configuration

CashCtrl serves every organisation from its own subdomain
(`https://<subdomain>.cashctrl.com/api/v1`) and gives every organisation its own API
user. The package therefore works with named organisations, declared in the environment;
nothing is read from files.

| Variable | Meaning |
| --- | --- |
| `CASHCTRL_ORGS` | the organisations, comma-separated, lower-case letters, digits and `_`: `acme,acme_test` |
| `CASHCTRL_<NAME>_SUBDOMAIN` | per organisation, the subdomain: `CASHCTRL_ACME_SUBDOMAIN=acme` |
| `CASHCTRL_<NAME>_API_KEY` | per organisation, the API user's key (Settings → Users & Roles) |
| `CASHCTRL_DEMO_SUBDOMAIN`, `CASHCTRL_DEMO_API_KEY` | the reserved organisation `demo`, used by this repository's tests; never listed in `CASHCTRL_ORGS` |

Every task and tool takes `org`, the name of one declared organisation, as its first
parameter, and every result names it as `meta.tenant`. `list_organisations()` (the tool
`cashctrl_list_organisations`) returns the declared names, nothing else. Each
organisation gets its own client, key and rate limit (60 requests per minute,
self-imposed); nothing spans organisations. A deployment reaches exactly the
organisations its environment declares. An unknown name is refused with the declared
ones; a malformed `CASHCTRL_ORGS` or a missing or malformed subdomain is a configuration
error naming the variable, never its value.

## 30-second example

```python
from xippios.cashctrl import tasks
from xippios.cashctrl.models import Filter

print(tasks.list_organisations().data)  # the declared organisations, e.g. ["acme", "demo"]

# "demo" stands for any declared organisation; the first argument is always org.
periods = tasks.list_fiscal_periods("demo")
current = next(period for period in periods.data if period.is_current)

accounts = tasks.list_accounts("demo", fiscal_period_id=current.id, only_active=True)
for account in accounts.data:
    print(account.number, account.name, account.end_amount)  # a Decimal, or None

bank = tasks.list_accounts("demo", filter=[Filter(comparison="eq", field="number", value="1020")])
record = tasks.get_account("demo", bank.data[0].id)
print(record.meta.endpoint, record.meta.request, record.meta.retrieved_at)

# The journal, persons and orders page by offset: limit gives one page, and meta.total
# says how many match; without limit every page is collected.
page = tasks.list_journal_entries("demo", fiscal_period_id=current.id, limit=20)
print(len(page.data), "of", page.meta.total)
entry = tasks.get_journal_entry("demo", page.data[0].id)  # with lines and bookings
invoices = tasks.list_orders("demo", type="SALES", fiscal_period_id=current.id)
```

Every task returns `Result[T]`: `data` holds models that mirror CashCtrl's payloads
under upstream's names in snake_case (`is_current`, `end_amount`), in Python and in every
tool and route result alike (the report rows of `get_report_data` excepted, which come
as upstream sends them), `meta` the upstream operation, the parameters as sent under
upstream's names (`onlyActive`), the organisation as `tenant`, when they were fetched
and, for a list, `total`, upstream's count of the matching records. Async twins are
named `<task>_async` (`list_organisations` has none). The tasks are listed in the status
table below. Persons come back without the personal identifiers `ssn` and `iban`
(`list_persons`, `get_person`, the persons `get_journal_entry` names; ADR-0017), and
locations without their bank account numbers `iban` and `qr_iban` (`list_locations`).

## MCP

```json
{
  "mcpServers": {
    "cashctrl": {
      "command": "uvx",
      "args": ["--from", "xippios-cashctrl[mcp]", "xippios-cashctrl-mcp", "--org", "acme"],
      "env": {
        "CASHCTRL_ORGS": "acme",
        "CASHCTRL_ACME_SUBDOMAIN": "acme",
        "CASHCTRL_ACME_API_KEY": "..."
      }
    }
  }
}
```

`--org acme` binds the server to one organisation: it stops at startup unless `acme` is
declared with a well-formed subdomain, its instructions name the organisation, and every
tool acts on `acme` and takes no `org`, so no call reaches another organisation;
`cashctrl_list_organisations` then lists `acme` only. Without
`--org`, a server serves every declared organisation and the agent picks one per call,
after `cashctrl_list_organisations` has named them. Its tools are read-only and named
`cashctrl_<verb>_<noun>`. Results are capped at 200 rows or 64 KB with a note on how to
narrow the query; `cashctrl_list_custom_fields` at 500 rows or 128 KB and
`cashctrl_get_report_data` at 128 KB, since an agent needs them whole. `--http` serves
streamable HTTP instead of stdio.

Write tools run in a separate server, `xippios-cashctrl-mcp-write` (see Write tools
below); every write tool previews its change unless called with `confirm=true`. It
takes `--org` too. It carries no authentication, so `--http` serves it on a loopback
`--host` (`127.0.0.1`, `localhost`, `::1`) only; `--allow-remote` serves it beyond,
behind a gateway that authenticates.

```json
{
  "mcpServers": {
    "cashctrl-write": {
      "command": "uvx",
      "args": ["--from", "xippios-cashctrl[mcp]", "xippios-cashctrl-mcp-write", "--org", "acme"],
      "env": {
        "CASHCTRL_ORGS": "acme",
        "CASHCTRL_ACME_SUBDOMAIN": "acme",
        "CASHCTRL_ACME_API_KEY": "..."
      }
    }
  }
}
```

## Write tools

Nine tools create, change and delete journal entries, persons and orders. They are
tasks in `xippios.cashctrl.tasks_write` (re-exported from `xippios.cashctrl`), served
by the write server only: never by the read server, never as an HTTP route.

| Upstream operation | Task function | MCP tool |
| --- | --- | --- |
| `POST journal/create.json` (Create journal entry) | `create_journal_entry` | `cashctrl_create_journal_entry` |
| `POST journal/update.json` (Update journal entry) | `update_journal_entry` | `cashctrl_update_journal_entry` |
| `POST journal/delete.json` (Delete journal entries) | `delete_journal_entry` | `cashctrl_delete_journal_entry` |
| `POST person/create.json` (Create person) | `create_person` | `cashctrl_create_person` |
| `POST person/update.json` (Update person) | `update_person` | `cashctrl_update_person` |
| `POST person/delete.json` (Delete people) | `delete_person` | `cashctrl_delete_person` |
| `POST order/create.json` (Create order) | `create_order` | `cashctrl_create_order` |
| `POST order/update.json` (Update order) | `update_order` | `cashctrl_update_order` |
| `POST order/delete.json` (Delete orders) | `delete_order` | `cashctrl_delete_order` |

- **The confirm gate.** Every write tool takes `confirm`, last, `false` by default.
  Without it nothing is written: the result is a preview, `performed: false`, with
  `endpoint`, `payload` (the exact form fields CashCtrl would receive, under upstream's
  names: booleans `true`/`false`, dates `YYYY-MM-DD`, lists as JSON, custom fields as
  XML; `ssn` and an `iban` as `REDACTED`, as in `meta.request` after a write), `before`
  (for an update or a delete, the record as it is now, as the read tools show it) and
  `changes` (for an update). A create's preview sends no request; an update's or a
  delete's sends one read and never a write. With `confirm=true` the write is sent and
  the result is `performed: true` with `insert_id` (the new record's id; an update
  answers the record's own) and upstream's `message`. Call once without `confirm`, show
  the preview, then confirm. Only `confirm=True` writes: from Python anything else
  (`"false"`, `1`) previews; over MCP the schema turns `"true"`, `"yes"`, `"1"`, `1`
  into true and `"false"`, `"no"`, `"0"`, `0` into false, and refuses anything else.
  In Python the result is `Result[WritePreview[<record>] | WriteResult]`; narrow it
  with `isinstance` or `if result.data.performed:`.
- **Updates send the whole record.** CashCtrl empties every parameter an update leaves
  out. `update_journal_entry` and `update_person` therefore read the record, apply the
  parameters given, and send every parameter `update.json` documents, the rest taken
  from the record. A parameter left out keeps its value; `clear` names parameters to
  send empty (`clear=["tax_id", "notes"]`; a flag such as `is_vendor` is sent `false`),
  and a parameter both given and cleared is refused, as is `sequence_number_id`, which
  an update sends only when given. Refused with `InvalidRequestError` before anything is
  written, unless the call gives or clears what is missing: a record that gives no value
  for a mandatory parameter; one holding a list whose shape was never observed
  (attachments, allocations, bank accounts, children, service periods, insurance
  contracts, certificate values), an address with a `titleId` or a contact with a
  `purpose` (keys the tables do not document); an insurance whose read shows no
  insurance numbers or an employee whose read shows no `user_id` (the read leaves empty
  fields out, and these were never seen come back); and a journal entry an order or a
  salary run booked. A confirmed update reads the record again and recomputes the
  payload, so it can differ from the preview if the record changed in between.
- **Deletes** take one id; the preview shows the record that would go.
  `delete_journal_entry` reads the entry with `confirm=true` as well and refuses, with
  `InvalidRequestError` before anything is deleted, an entry an order or a salary run
  booked; an unknown id is `NotFoundError` there. A person or an order that no longer
  exists, or an entry deleted between that read and the delete, is refused by upstream
  (`RequestRejected`).
- **Custom fields**: `custom` maps upstream's names (`customField1`, `customField<ID>`,
  the ids from `cashctrl_list_custom_fields`) to text, sent as
  `<values><customField1>...</customField1></values>`, values escaped. An update keeps
  every stored value it is not given.
- **Amounts.** A journal `amount` with a `tax_id` is the gross amount, VAT included, and
  order items' `unit_price` was read as gross too (observed on the demo organisation,
  although the tax codes' calculation type reads NET; `docs/demo-org.md`).
- **Ids** come from the read tools: account ids from `cashctrl_list_accounts` (the
  `id`, not the account number), tax codes from `cashctrl_list_tax_codes`, persons from
  `cashctrl_list_persons`, order categories and their statuses from
  `cashctrl_list_order_categories`, currencies from `cashctrl_list_currencies`, a
  person's `category_id` from `cashctrl_list_person_categories`, its `title_id` from
  `cashctrl_list_person_titles` and an employee's `location_id` from
  `cashctrl_list_locations`, an allocation's `to_cost_center_id` from
  `cashctrl_list_cost_centers`; the record to update or delete from
  `cashctrl_list_journal_entries`, `cashctrl_list_persons` or `cashctrl_list_orders`
  (the `id`, not the `nr`). A journal `associate_id` is a person's id; create a new
  person with `cashctrl_create_person` first (upstream would create one from a name,
  which the tools do not send).
- CashCtrl checks every write and refuses with the fields it objects to, e.g.
  `error: RequestRejected: CashCtrl rejected the request: debitId: This field cannot be
  empty.`; a refused write changed nothing. A write that meets a server error or a
  timeout is never repeated (ADR-0011): read back before sending it again.

```python
from datetime import date
from decimal import Decimal

from xippios.cashctrl import tasks_write
from xippios.cashctrl.models import WritePreview, WriteResult

entry = dict(
    date_added=date(2026, 10, 24),
    amount=Decimal("100.00"),  # gross, VAT included, with a tax_id
    debit_id=3,  # account ids from list_accounts, not account numbers
    credit_id=42,
    tax_id=9,  # from list_tax_codes
    title="xippios-live README example",  # marked, should it ever run against demo
)
preview = tasks_write.create_journal_entry("demo", **entry)
assert isinstance(preview.data, WritePreview)
print(preview.data.payload)  # what CashCtrl would receive; nothing was written
done = tasks_write.create_journal_entry("demo", **entry, confirm=True)
assert isinstance(done.data, WriteResult)
print(done.data.insert_id)  # the new entry's id
```

## HTTP

`xippios.cashctrl.http.router` is a FastAPI router the consumer mounts. It has no lock:
every route but `GET /cashctrl/list_organisations` takes `org`, and the consumer passes
it explicitly on each request. A deployment that must reach one organisation only
declares only that one. A task whose
parameters are all scalars is a `GET /cashctrl/<task>` with query parameters; the list
tasks that take a `filter`, a list (`list_accounts`, `list_cost_centers`,
`list_journal_entries`, `list_persons`, `list_orders`), are a `POST` with a JSON body
keyed by parameter name.
The MCP entry points quiet httpx's request log; the router does not, so a consumer that
logs at INFO logs httpx's request lines, whose URLs carry the organisation's host (its
subdomain): set the `httpx` logger to WARNING.

## Status

| Upstream operation | Task function | MCP tool | Status |
| --- | --- | --- | --- |
| none: the declared organisations | `list_organisations` | `cashctrl_list_organisations` | available; names only, no request |
| `GET fiscalperiod/list.json` (List fiscal periods) | `list_fiscal_periods` | `cashctrl_list_fiscal_periods` | available |
| `GET currency/list.json` (List currencies) | `list_currencies` | `cashctrl_list_currencies` | available |
| `GET tax/list.json` (List tax codes) | `list_tax_codes` | `cashctrl_list_tax_codes` | available |
| `GET account/list.json` (List accounts) | `list_accounts` | `cashctrl_list_accounts` | available; HTTP route is `POST` |
| `GET account/read.json` (Read account) | `get_account` | `cashctrl_get_account` | available |
| `GET journal/list.json` (List journal entries) | `list_journal_entries` | `cashctrl_list_journal_entries` | available; paged; HTTP route is `POST` |
| `GET journal/read.json` (Read journal entry) | `get_journal_entry` | `cashctrl_get_journal_entry` | available |
| `GET person/list.json` (List people) | `list_persons` | `cashctrl_list_persons` | available; paged; HTTP route is `POST` |
| `GET person/read.json` (Read person) | `get_person` | `cashctrl_get_person` | available |
| `GET order/list.json` (List orders) | `list_orders` | `cashctrl_list_orders` | available; paged; HTTP route is `POST` |
| `GET order/read.json` (Read order) | `get_order` | `cashctrl_get_order` | available |
| `GET order/category/list.json` (List categories) | `list_order_categories` | `cashctrl_list_order_categories` | available |
| `GET customfield/list.json` (List custom fields) | `list_custom_fields` | `cashctrl_list_custom_fields` | available; one module (`type`) a call |
| `GET person/category/list.json` (List categories) | `list_person_categories` | `cashctrl_list_person_categories` | available |
| `GET person/title/list.json` (List titles) | `list_person_titles` | `cashctrl_list_person_titles` | available |
| `GET account/category/list.json` (List categories) | `list_account_categories` | `cashctrl_list_account_categories` | available; flat, linked by `parent_id` |
| `GET account/costcenter/list.json` (List cost centers) | `list_cost_centers` | `cashctrl_list_cost_centers` | available; HTTP route is `POST`; no balances yet |
| `GET location/list.json` (List locations) | `list_locations` | `cashctrl_list_locations` | available; without `iban` and `qr_iban` |
| `GET report/tree.json` (Get tree of reports) | `get_report_tree` | `cashctrl_get_report_tree` | available |
| `GET report/element/data.json` (Read JSON data) | `get_report_data` | `cashctrl_get_report_data` | available; rows as upstream sends them |
| `POST journal/create.json`, `update.json`, `delete.json` | `create_journal_entry`, `update_journal_entry`, `delete_journal_entry` | `cashctrl_create_journal_entry`, ... | available on the write server only |
| `POST person/create.json`, `update.json`, `delete.json` | `create_person`, `update_person`, `delete_person` | `cashctrl_create_person`, ... | available on the write server only |
| `POST order/create.json`, `update.json`, `delete.json` | `create_order`, `update_order`, `delete_order` | `cashctrl_create_order`, ... | available on the write server only |

`lang` (`de`, `fr`, `it`, `en`), which upstream takes on every request and which matters
mostly for error messages and exports, is not exposed yet. `list_accounts` checks `dir`
(`ASC`, `DESC`) and each filter's `comparison` (`eq`, `like`, `gt`, `lt`) before
anything is sent, since upstream silently ignores values it does not know; both are
typed as these value sets, so the tool schema lists them. A filter is a `Filter` or,
from Python, a mapping with the same keys.

The paged lists (`list_journal_entries`, `list_persons`, `list_orders`) take `start`
(default 0) and `limit`. With `limit` they return one page of at most `limit` records
from `start`; without it, every record from `start` on, fetched 100 at a time (upstream's
documented page size, about 1 s per 100 at the self-imposed pace). `meta.total` is
upstream's count of every record the request matches. The next page starts at `start`
plus the number of records received: over MCP the result cap (200 rows or 64 KB) may
return fewer than `limit`, so never advance by `limit`. MCP agents should always pass a
`limit` of about 20. Offset pages over a list that changes meanwhile can repeat or skip
records. Every other list returns its whole answer in one request and reports
upstream's `total` too.

The journal and order lists answer for the API user's current fiscal period unless
`fiscal_period_id` is given; that period is server-side state that
`fiscalperiod/switch.json` changes, and `meta.request` does not show which period
answered, so pass `fiscal_period_id` (an id from `list_fiscal_periods`) for a
reproducible answer. Without `type` (`SALES`, `PURCHASE`), `list_orders` returns both;
`list_order_categories` lists `SALES` (upstream's default) unless given `PURCHASE`.

`get_report_tree` lists the organisation's reports, collections of report elements;
`get_report_data` reads one element (`element_id`, a balance sheet, a profit and loss
statement, a VAT settlement, ...) for `fiscal_period` or for `start_date` to
`end_date`. Giving the fiscal period and a date is refused before anything is sent:
upstream derives the dates from the period and would ignore the ones given. The report
comes back as upstream sends it (`data`, the rows, nested; `properties`, the columns
shown; `total`), under upstream's camelCase names and with amounts as JSON numbers: the
documentation gives no schema, and the rows differ by report type.
`list_account_categories` is the flat `account/category/list.json`, each category with
its `parent_id`; `account/category/tree.json` nests the same categories with display
fields only. `list_custom_fields` takes the module (`type`: `JOURNAL`, `PERSON`,
`ORDER`, ...) and refuses any other value; `list_cost_centers` checks `dir` and the
filters as `list_accounts` does.

## Upstream terms and attribution

Data comes from CashCtrl (https://cashctrl.com) under its own terms of use;
this package adds no rights to it. Documentation snapshot: `docs/upstream/`.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
