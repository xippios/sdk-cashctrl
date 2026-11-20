# sdk-cashctrl — instructions for Claude Code

`xippios-cashctrl` wraps CashCtrl as a typed Python client, an MCP server
and FastAPI routes, built on `xippios-core`. This file holds what an agent needs to work on
the package: what it wraps, its layout, its commands and its code rules. The documents it
follows, sdk-core's conventions among them, are listed under
[`## Documents` in the README](README.md#documents); read them before you change a file.

## What this package wraps

| | |
| --- | --- |
| Upstream | CashCtrl, https://cashctrl.com |
| API base URL | `https://<subdomain>.cashctrl.com/api/v1`, one per organisation |
| Documentation | https://app.cashctrl.com/static/help/en/api/index.html, snapshotted in `docs/upstream/` |
| Credentials | `CASHCTRL_ORGS` names the organisations; per name `CASHCTRL_<NAME>_SUBDOMAIN` and `CASHCTRL_<NAME>_API_KEY`, the key sent as the HTTP basic user name. The reserved `demo` is declared by its own pair and never listed |
| Rate limit | 60 requests per minute per organisation, burst 1; a self-imposed pace, upstream documents none, only a 429 (sdk-core ADR-0033, decision 1); enforced client-side in `_client.py`, one token bucket per organisation; see Rate limit below |
| Write tools | yes, in `tasks_write.py`, served by `xippios-cashctrl-mcp-write` |
| Core | `xippios-core~=0.3.0` from PyPI, its `mcp`, `http` and `testing` extras likewise: one core minor, adopted through conventions §15 (sdk-core ADR-0039) |

The snapshot listed in `docs/upstream/FETCHED.md` is the reference for names, parameters and
semantics; a wrapper is never written from memory of the API.

## Organisations

CashCtrl serves each organisation from its own subdomain, and an API user belongs to one
organisation. `_client.py` is therefore a registry, not one client: `TENANTS`, core's
`Tenants` (conventions §7), declared as `CASHCTRL_ORGS` with the fields `SUBDOMAIN` and
`API_KEY`, `param="org"`, the parameter that names an organisation, the reserved `demo`
and `check_subdomain` (one DNS label, lower-cased) as the subdomain's check. The registry,
`list_organisations` and the `--org` lock are core's: `Tenants`, `list_task`,
`TenantLock`, `bind_tasks` and `tenant_instructions` from `xippios.core` and
`serve_tenants` from `xippios.core.mcp`, which core 0.3.0 left to this package and 0.4.0
took back (sdk-core ADR-0042, decision 1). Core keeps `ResultMeta.tenant` and the write server's
rules too.

- `org` is the first, required parameter of every task; the MCP tools take it too unless
  the server is started with `--org`, which binds it so no tool takes it. It is the name
  of a declared organisation (`demo`, `acme`), and every result names it as
  `meta.tenant` (it stays in `meta.request` as well). `client_for(org)` is `TENANTS.client_for(org, _build)`: that
  organisation's own client, own base URL, own key, own token bucket, no shared cache,
  rebuilt when one of its variables changes (the key included); the client it replaces
  is closed through its `aclose()`, on the running event loop or, outside one, on core's
  background loop (`Tenants.client_for`; `TENANTS.reset()` drops without closing). An
  undeclared name is an `InvalidRequestError` listing the declared ones ("unknown
  tenant"); a malformed `CASHCTRL_ORGS` or a missing or malformed subdomain is a
  `ConfigError` naming the variable, never its value, a malformed subdomain with what it
  should hold (`Tenants(hints=...)`).
- `TENANTS.names()` reads `CASHCTRL_ORGS` (comma-separated, `^[a-z0-9_]+$`) on every call
  and appends `demo` when `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY` are both
  set. `list_organisations` (core's `list_task`, the tool
  `cashctrl_list_organisations`) returns those names, nothing else, on the read server
  and as a route; on a bound server, the bound organisation only, `meta.tenant` `None`.
- `--org <name>` binds an MCP server (read or write) to one organisation (core's
  `serve_tenants(server, build, TENANTS, noun="organisation", check=check_org)` in
  `mcp.py` and `mcp_write.py`): an undeclared name or a missing or malformed subdomain
  (`check_org` in `_client.py`) stops it at startup (exit status 2). The lock is no
  middleware but a wrapper: `build(TenantLock(TENANTS, org))` returns the tool set whose
  tasks `bind_tasks` binds, one tool per task with `org` bound at build, the same
  `__name__` (tool names and `MCP_CAPS` keys stay), the docstring without its `org`
  line, and a signature without `org`, so no tool of a bound server takes `org`; the
  instructions end "This server is bound to org <name>; every tool acts on that
  organisation and takes no org." A call that still passes `org` is refused by core's
  argument check before the tool runs, naming the tool's arguments
  (`tests/test_org_lock.py`). Core serves the write server over `--http` on a loopback
  `--host` only, unless `--allow-remote` is passed. The HTTP router has no lock:
  consumers pass `org` explicitly.
- The subdomain stays out of messages and logs: core's status errors name the method and
  the path, never the host, and `classify` hands core a copy of an error response whose
  body names `cashctrl.com` instead of the organisation's host, so neither the quoted
  snippet nor `UpstreamError.body` carries it. Both servers are built and run by core's
  `build_server` and `main`, which raise the `httpx` and `httpcore` loggers to WARNING so
  request URLs are never logged. The HTTP router does not: a consumer that logs at INFO
  logs httpx's request URLs with the tenant host and should set the `httpx` logger to
  WARNING, as the README says.
- Isolation is by configuration: a deployment reaches exactly what its environment
  declares. Nothing is cross-tenant: no task, tool or helper spans organisations, and
  `TENANTS.names()` and `list_organisations` return names only.

**Demo only.** Fixtures, live tests and the fixture recorder use the organisation `demo`
and nothing else, ever. The recorder takes no organisation; every live test takes the
`demo_org` fixture, which fails unless `demo` is the only declared organisation;
`tests/conftest.py` removes `CASHCTRL_ORGS` and every organisation's pair but demo's
through core's `keep_reserved_tenants` when pytest imports it, before any fixture runs, and
`CASHCTRL_ORGS` again for every test, sets the placeholder subdomain in every offline test
and calls `TENANTS.reset()` around each.
Core's plugin does the rest (sdk-core ADR-0035): no network outside a test marked `live` or
`network`, no rate-limit waits, and the placeholder key on every auth object, with
`CASHCTRL_DEMO_API_KEY` named in `xippios_placeholder_key_envs`. The demo organisation is
synthetic: invented books seeded by `scripts/seed_demo.py` and described in
`docs/demo-org.md`, never a copy of real books. So the recorder records any module and
any amount; it still scrubs e-mail addresses, API user tags, token-like body fields,
`ssn` and every name ending in `iban`, in the request body as well (How to record a
fixture), and refuses any method but GET and POST, a POST to anything but the fourteen
write paths, a GET to a path `docs/upstream/` does not document as a GET, a create
without the marker `xippios-live`, an order write naming an unmarked order or a book
entry's update or delete whose order is unmarked, and any endpoint but `.json`. Writes
against demo create a record marked `xippios-live`, update it and delete it again,
nothing else but a payment of a deleted order (see Write tools). The demo subdomain is
treated like a key: never in a file, a commit, a log line or a report. The repository is
public.

## Rate limit (sdk-core ADR-0033)

Decisions 1, 2, 3 and 5 of sdk-core ADR-0033 are adopted; decision 4 is deliberately not applied.

1. **Pace.** 60 requests per minute per organisation with a burst of 1, one request at
   a time and then one a second, one token bucket per client (`RATE_LIMIT` in
   `_client.py`). The pace is self-imposed: CashCtrl documents no per-second or
   per-minute limit, only a 429 ("We recommend adding delays between your requests",
   `docs/upstream/error-handling.md`).
2. **Quotas.** No longer-window quota is documented, so nothing is rationed.
3. **A spent limit.** A 429 becomes `RateLimitError` through core's status mapping inside
   `classify`, with `retry_after` from `Retry-After` when upstream sends it; retries
   honour it up to `backoff_max`, beyond which the error reaches the caller
   (`tests/test_errors.py`). CashCtrl documents no fallback, and every answer carries
   `x-cashctrl-requests-left` (299 on every answer observed on 2026-10-23, a 401
   included) with an unknown window and scope, so it is not read.
4. **No firing into a spent quota** is deliberately not applied: no `QuotaPolicy` is
   installed. Core's `QuotaPolicy` (sdk-core ADR-0037, decision 2) keeps a long-window quota, and
   CashCtrl documents none, nor a window for
   `x-cashctrl-requests-left`; its 429 asks only for delays, a pace refusal. With no
   window to give it, a policy would take its default of an hour and turn one 429
   without `Retry-After` into an hour of refusals once a call's retries are spent.
5. **Pauses are stated** by core's adapters: `error: RateLimitError: ... (retry after N s)`
   over MCP, a 429 problem with `retry_after` and `Retry-After` over HTTP.

## Layout

```
src/xippios/cashctrl/
  __init__.py      public surface: __version__ and re-exported task functions
  py.typed         PEP 561 marker; consumers' mypy --strict needs it
  _version.py      __version__ from distribution metadata
  _client.py       organisation registry: TENANTS, client_for(org), check_org, classify
  errors.py        RequestRejected (HTTP 200 with success:false) and FieldError
  models.py        pydantic models mirroring upstream payloads (UpstreamModel), the
                   projections tasks return without ssn and iban (sdk-core ADR-0017) and, written by
                   hand, the value sets upstream documents that no packaged list renders
  api/             endpoint wrappers, one module per upstream operation (conventions §2);
                   _form.py encodes and posts writes, _download.py streams files
  tasks.py         task functions and list_organisations; __all__ is what the adapters register but
                   BULK_TASKS, the file tasks (Python only); MCP_CAPS the per-tool result caps
                   (list_custom_fields, list_cost_centers, get_report_data, list_history)
  tasks_write.py   confirm-gated write tasks for the separate write server (Write tools below)
  mcp_write.py     xippios-cashctrl-mcp-write entry point
  mcp.py           xippios-cashctrl-mcp-read entry point
  http.py          FastAPI router
  params.py, enums.py, reference/  the packaged lists' scaffold: none is packaged
                   (/refresh-reference-data)
scripts/
  refresh_reference.py   the template's skeleton, until a value set is packaged
  refresh_upstream.py    regenerates docs/upstream/ and its FETCHED.md from upstream
  record_fixture.py      records one exchange with the demo organisation; core's Scrub, then its own
                         TenantScrub (host, encoded and JSON checks) and scrub_text
  seed_demo.py           seeds a fresh, empty demo organisation with synthetic books (docs/demo-org.md);
                         --discovery adds one custom field and one cost centre
  adr_index.py           writes docs/adr.md and docs/adr.json from the records in docs/adr/;
                         --check fails while either is stale
tests/
  conftest.py      core's plugin; demo-only environment, placeholder subdomain, clients reset per test, demo_org
  fixtures/        recorded responses, <wrapper>/<case>.json, never hand-written
  test_family.py   core's family check, one line: namespace levels, py.typed, __version__,
                   the adapters serving exactly the tasks, task shapes and docstrings, the
                   README status table, the template tag, the core bound
  test_tasks.py    structural checks on every task plus per-task replay tests
  test_downloads.py  the file tasks on synthetic bytes mounted by respx; a refusal leaves no file
  test_tasks_write.py  the write tasks: previews send nothing, writes replay, updates fail
                   closed; the write server's own test (core's assert_write_tools)
  test_registry.py organisation declaration, lookup and per-organisation clients
  test_key_resolution.py  keys resolved as in production: placeholder_api_key pins nothing
  test_errors.py   classify, RequestRejected and the recorded refusals
  test_org_lock.py the --org lock's wiring: bound tasks, both entry points, through core's mcp_call
  test_entry_points.py  the servers' entry points, -read and -write, and the text that names them
  test_record_fixture.py  the recorder never writes the demo host, subdomain or key
  test_seed_demo.py       the seeder refuses unsafe states before any write, offline
  test_live.py     @pytest.mark.live smoke tests, demo_org only; the writes mark, sweep and delete
docs/
  upstream/        documentation snapshot and FETCHED.md
  demo-org.md      the synthetic demo organisation: why, how to create and seed it, its books
  adr/             this package's design decisions, one NNNN-<slug>.md record each, laid
                   out in its README.md
  adr.md           the index of the decisions, written by scripts/adr_index.py, never by hand
  adr.json         the same index, for machines
  reports/         dated reports, the evidence a decision cites, laid out in its README.md
changelog/         the next release's changelog entries, one fragment per change, laid out
                   in its README.md
CHANGELOG.md       the releases, each section assembled from the fragments
.github/workflows/ ci.yml (the required ci check, with the changelog and fixture-size steps),
                   publish.yml (the release train: tag, build, PyPI), live.yml (nightly live
                   tests), organization.yml (the organization's checks from xippios/.github:
                   conventions, a review of a pull request against the documents the README
                   lists, and adr-index, which runs scripts/adr_index.py --check)
.claude/commands/  add-endpoint, record-fixture, refresh-upstream, refresh-reference-data, release-prep
```

`src/xippios/` has **no** `__init__.py`: it is a PEP 420 namespace package shared with
`xippios-core` and every other source package. The import path is `xippios.cashctrl`
(sdk-core ADR-0006).
Where the API's operation ids repeat across its services, `api/` keeps one module per service
instead, named after the service, and this Layout says so (conventions §2).

## Write tools

`tasks_write.py` holds fourteen write tasks, `create_*`, `update_*` and `delete_*` for
journal entries, persons, orders and an order's book entries, `update_order_status` and
`create_order_payment`, served by `xippios-cashctrl-mcp-write` only: never by the read
server, never on the HTTP router (core's `assert_write_tools` in `tests/test_tasks_write.py`).
The recipe for one more:

1. **Layer 1.** `api/<module>_create.py` (and `_update`, `_delete`): a `<module>_fields`
   builder takes every parameter the create table documents, snake_cased, and returns
   the form fields under upstream's names through `api/_form.py`'s `form_fields`
   (booleans `true`/`false`, `Decimal` as plain digits, dates `YYYY-MM-DD`, lists as
   compact JSON with upstream's keys, `None` and empty lists left out); the wrapper
   takes `org` and those fields and posts them with `post_form` (core's `data=`, with
   `charset=UTF-8` declared), returning a `WriteAnswer`. A `delete.json` takes
   `delete_fields(ids)`. JSON array items are `*Input` models in `models.py`
   (`validation_alias=AliasChoices(snake, camel)`, `serialization_alias=camel`,
   unknown keys refused).
2. **Layer 2.** An async task, `org` first and `confirm: bool = False` last (core
   refuses to register a write task without it), the create table's parameters as
   keyword arguments, `custom: Mapping[str, str] | None` among them. The gate is
   `if confirm is not True:`, never truthiness: from Python only `True` writes (over
   MCP the schema turns `"true"`, `"yes"`, `"1"`, `1` into `True` and refuses what is
   no boolean). Ids are ids: journal `associate_id` is an `int`, since upstream would
   create a person from a name. It returns
   `Result[WritePreview[<record>] | WriteResult]`: while `confirm` is false a
   `WritePreview` (`performed=False`, `endpoint`, `payload` = the exact fields,
   `before` = the record for an update or a delete as the read task's projection,
   `changes` for an update) with `meta.request` = `{"org": org}`; with `confirm` a
   `WriteResult` (`performed=True`, `insert_id`, `message`) with `meta.request` = `org`
   plus the fields as sent. `ssn` and an `iban` show as `REDACTED` in `payload`,
   `changes` and `meta.request` (Personal identifiers below). The payload is never in a
   result twice. A create's preview sends nothing; an update's or a delete's sends one
   read, never a write.
3. **Updates read, merge, send.** Upstream empties every parameter an update omits.
   An `update.json` task reads the record, maps every parameter it documents from it
   (`_journal_values`, `_person_values`, `_order_values`, `_book_entry_values`),
   applies the arguments given (not `None`), and sends all of them. An order's items go
   back under the keys the items table documents (`_order_items`, in their `pos`), the
   computed ones left out; upstream stores the items an update sends anew, with new ids
   (observed 2026-10-27).
   A mandatory parameter neither the record nor the call gives raises
   `InvalidRequestError` before any write; so does a stored list whose shape was never
   observed (attachments, allocations, bank accounts, children, service periods,
   insurance contracts, certificate values, an order item's allocations), a stored key
   the input table does not document (an address's `titleId`, a contact's `purpose`,
   an order item's `attachments` or `isOptional`), and a field whose absence
   from the read is unknown rather than empty (an insurance's `insuranceNr` and
   `insuranceMemberNr`, an employee's `userId`), unless the call gives or clears it.
   `person/read.json` returns every stored documented field and leaves empty ones out
   (verified live on 2026-10-24, `docs/demo-org.md`). `clear: list[str] | None` names
   parameters to send empty, a flag (`_FLAGS`) as `false`, checked against a
   `<RESOURCE>_UPDATE` table of the documented update parameters; one both given and
   cleared is refused, and so is one an update sends only when given (`_UNSENT`:
   `sequence_number_id`). A journal entry an order or a salary run booked (`orderId`,
   `orderBookEntryId`, `salaryBookEntryId`) is refused, by `delete_journal_entry` as
   well, which reads the entry first, confirmed or not; an order is not refused for
   being booked, since upstream changes an order's automatic book entries through its
   items (`docs/upstream/order.md`, Book entry), and a book entry's update and delete
   read it first and write only one of `type` `MANUAL`, booked by hand (the items' are
   `GENERATED`). A confirmed call reads again and recomputes, so its payload can differ
   from the preview's if the record changed. Never send a partial record.
4. **Custom fields** are `customField<ID>` to text (`api/_form.py`'s `CUSTOM_FIELD`),
   rendered as `<values><customField1>...</customField1></values>`, values escaped; an
   update merges the given values into the stored XML (`merge_custom`) and refuses XML
   it cannot carry over value for value.
5. **Facts for docstrings.** A journal `amount` with a `tax_id` is gross, and order
   items' `unitPrice` was read as gross (observed, `docs/demo-org.md`); previews are
   free; `confirm=true` writes; ids come from `list_accounts`, `list_tax_codes`,
   `list_persons`, `list_order_categories`, `list_currencies` and the discovery lists:
   `list_person_categories` (a person's `category_id`), `list_person_titles`
   (`title_id`), `list_locations` (an employee's `location_id`), `list_account_categories`
   (the `category_id` that narrows `list_accounts`), `list_cost_centers` (an
   allocation's `to_cost_center_id`) and `list_custom_fields` (`customField<id>`, by the
   module's `type`); each write docstring names the lists its ids come from. Upstream
   refuses with HTTP 200 and an `errors` list (`RequestRejected` naming the fields); a
   delete of an id that no longer exists answers `success: false` with `message`
   (`RequestRejected`, not `NotFoundError`). `person.nr` is unique: a second person with
   the same `nr` is refused.
6. **Tests.** Record the create, the read the update starts from, the update, the
   delete, in that order, so every record created is deleted again; compute the
   payload offline through the task's preview and pass exactly those pairs to the
   recorder. In `tests/test_tasks_write.py`: the preview sends no request and its
   `payload` equals the recorded request body; `confirm=True` replays it; an update's
   refusal is tested on a recorded read changed in memory (say so). In
   `tests/test_live.py`: one test per resource calls each write tool once with
   `confirm=True`, every record marked `xippios-live` (title, company or description,
   and `nr` where it has one, so no sequence number advances), dated 2026-10-24; it
   first sweeps leftovers (list with `query=xippios-live`, delete each whose marked
   field holds the marker), deletes what it created by id with the delete tool, and a
   `finally` deletes it through the wrapper if an assertion failed first. An update is
   previewed, confirmed and read back: the changed field holds the new value and every
   other derived field is unchanged.
7. **Statuses and payments**: `update_order_status` and
   `create_order_payment` send the fields given, nothing read: a preview sends no
   request. A payment (pain.001 or PDF) books nothing and has no documented delete: the
   live test deletes the paid order and leaves the payment, an accepted residue.

## Personal identifiers (sdk-core ADR-0017)

CashCtrl documents two personal identifiers, a person's `ssn` ("Social security number
of the employee") and the `iban` of each of a person's `bankAccounts` (the list sends an
`iban` of its own). The rule is `ssn` and `iban` wherever it appears: a person's
`bankAccounts[].iban` and the organisation's locations' `iban` and `qrIban` alike, kept
out of every projection a task returns and dropped from the raw report rows
`get_report_data` returns. `iban` covers the organisation's own bank account numbers too,
as sdk-core ADR-0017's "bank account number", since conventions §3 leaves to the source
what it judges equivalent to a personal identifier. The recorder rewrites any
value under `iban` in a body to `REDACTED`, so a projection that kept one could never be
replay-tested with a real value.

- The endpoint wrappers' read models stay faithful and carry them (`Person`,
  `PersonDetail`, `JournalEntryDetail.associates`, `Location`, `OrderDocument`; sdk-core ADR-0028, decision 1).
- The tasks return projections without them, built with `UpstreamModel.project` in
  `tasks.py`: `PersonProjection` (`list_persons`), `PersonDetailProjection`
  (`get_person`; each bank account kept without its `iban`, which the projection's own
  validator drops), `JournalEntryDetailProjection` (`get_journal_entry`, its
  `associates` projected), `LocationProjection` (`list_locations`, without `iban` and
  `qr_iban`, both undocumented and only seen `null`) and `OrderDocumentProjection`
  (`get_order_document`, without `orgIban`, `orgQrIban` and `recipientIban`, only seen
  `null`). A write preview's `before` is the same projection.
- `create_person` and `update_person` take `ssn` and, in `bank_accounts`, `iban`, and
  send them as given; a preview's `payload` and `changes` and a performed write's
  `meta.request` show `REDACTED` instead (`_shown` in `tasks_write.py`), a cleared `ssn`
  as empty.
- Fixtures never carry their values: the recorder rewrites the value of `ssn` and of
  every name ending in `iban` (`qrIban`, `orgIban`, ...) to `REDACTED`, in any
  letter case, and its final check refuses a value that survives the rewrite (How to
  record a fixture); the recorded location holds `null` for `iban` and `qrIban`.
- `get_report_data` refuses payroll and people reports before their data is requested:
  a type that starts with `SALARY_` or contains `PERSON`, or is `SETTLEMENT`,
  `WITHHOLDING_TAX_SETTLEMENT`, `PEOPLE` or `ORG_CHART`. The answer never names its
  type, so `_report_type` reads `report/tree.json` once per organisation into a `WeakKeyDictionary` keyed on its
  client, which `TENANTS.reset()` or a changed variable drops; `get_report_tree`
  refreshes it; an element the kept tree lacks reads it once more, one still missing is
  asked of upstream. Other reports come back as sent, every key `ssn` or ending in `iban`
  dropped at any depth, in any case (`_report`; sdk-core ADR-0028, decision 1).
- A task that fetches them deliberately may return them and says so in its docstring.
  Files may carry them, at the caller's path, never in a result or a tool
  (`BULK_TASKS`): `export_persons` names `PERSON_COLUMNS` unless its caller names
  columns, `ssn` or `iban` among them; `download_order_document`'s PDF
  may carry the organisation's IBAN or QR-IBAN and the recipient's address (QR-bill);
  a report file is refused by `get_report_data`'s type rule on the tree read right
  before it (`_tree_now`), but no key is dropped from a file.

## Commands

```bash
uv sync --all-extras
uv run pytest                      # offline, replays the fixtures
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pre-commit run --all-files
python3 scripts/adr_index.py --check   # the index matches the records in docs/adr/
direnv exec . env -u CASHCTRL_ORGS XIPPIOS_LIVE_TESTS=1 uv run pytest -m live --tb=short --assert=plain   # demo only

uv run xippios-cashctrl-mcp-read --org demo   # stdio, bound to demo; --http for streamable HTTP
uv run xippios-cashctrl-mcp-write --org demo   # the write tools; --http on loopback only
```

`uv run pytest` is offline: core's plugin refuses the network and skips the rate limiter's
waits in every test not marked `live` (conventions §10, sdk-core ADR-0035). A test that
asserts a limiter wait or a quota pause is marked `rate_limited`, one that must reach the
network `network`. It sends the key's placeholder, with `CASHCTRL_DEMO_API_KEY` set to it
because `pyproject.toml` names that variable under `xippios_placeholder_key_envs`; the
package keeps no placeholder fixture of its own (`tests/conftest.py` keeps the demo-only
environment, Organisations above).

A keyed command, the live tests, the recorder and the seeder, runs under `direnv exec .`
from the clone or a directory under it, a worktree among them: direnv loads the demo
organisation's pair from the clone's own `.envrc`, which `.gitignore` lists and nobody
reads or prints (Never below).

`.github/workflows/live.yml` runs the live tests nightly at 02:36 UTC, a time derived from
the slug so that sources sharing a key never start together, and on demand; a pull request
never runs them. Every `live` test runs, write tests included, so a live write test acts
only on data kept for testing (the demo organisation, sdk-core ADR-0036, decision 2) and cleans up after itself.
Only its `uv run pytest -m live --tb=short --assert=plain` step sees the demo
organisation's pair, from the secrets `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY`
(the `live_secrets` answer and the reserved organisation's key); both must give
sdk-cashctrl access for the nightly run to pass. Every live run takes `--tb=short --assert=plain`, since
the log of `live.yml` is public: the first keeps a failing test's frame arguments out of
it, a raw upstream payload among them, and the second the values a failed `assert`
compares. A live test asserts on shapes and counts, never on a raw payload.

## Code rules

- Three layers (sdk-core ADR-0001, conventions §2): endpoint wrappers in `api/`, task
  functions in `tasks.py`, adapters in `mcp.py` and `http.py`. The adapters register
  `tasks.__all__` and call only tasks, the tasks call only wrappers and reference data, and
  a wrapper returns models.
- Upstream's documented error shapes go into `classify` in `_client.py`, once, and an error
  class of the package's own into `errors.py`; a wrapper never inspects a status code
  (conventions §5, §6).
- A change brings its tests, written before the code, and passes the offline checks above;
  its changelog entry is a fragment under `changelog/`, one file holding its bullet, as
  `changelog/README.md` lays it out (conventions §12). Commit subjects follow Conventional
  Commits (conventions §13): the rule binds a pull request's own commits, not the commit
  that lands the pull request on `main`, whose subject GitHub writes.
- `ruff` leaves `docs/` and `.claude/` alone (`pyproject.toml`), so the upstream snapshot
  keeps its bytes: never reformat it.
- A convention that seems wrong is followed anyway and said in the pull request; changing
  it is a change of sdk-core's `docs/conventions.md` with an ADR.

## Never

- Never hand-write a fixture, and never commit one without grepping it for key patterns
  (conventions §10).
- Never read or print `.envrc`, `.env`, the credential variables of this package,
  `CASHCTRL_<NAME>_SUBDOMAIN` and `CASHCTRL_<NAME>_API_KEY` of every organisation,
  `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY` among them, or any variable ending in `_API_KEY`, `_REFRESH_TOKEN` or `_SECRET`.
- Never write a key, a token or another credential into a file or a commit.
- Never put logic in `mcp.py` or `http.py`, and never add a route or a tool by hand: the
  adapters register `tasks.__all__` (sdk-core ADR-0001).
- Never rename or re-map an upstream concept to another source's (sdk-core ADR-0028, decision 1).
- Never return a documented personal identifier in a task's projection, echo one in
  `meta.request`, or commit one in a fixture (sdk-core ADR-0017).
- Never edit `docs/upstream/` by hand: `/refresh-upstream` fetches it, and the pull request
  shows its diff (conventions §3).
- Never add `src/xippios/__init__.py`, nor an `__init__.py` at a level between it and the
  package (sdk-core ADR-0006).
- Never push a tag by hand: a release's tag comes from `publish.yml` alone (conventions §12).

## Template updates

This repository is generated from sdk-template, at the tag `.copier-answers.yml` records. A
template release reaches it in a pull request of its own, with
`uvx --from 'copier>=9.19' copier update --defaults --vcs-ref=<tag>` (conventions §15): the
update renders the template's files again and never overwrites the files this package
fills, `__init__.py`, `_client.py`, `errors.py`, `models.py`, `api/`, `parse/`, `tasks.py`,
`params.py`, `enums.py`, `reference/`, `scripts/refresh_reference.py`,
`scripts/refresh_upstream.py`, `tests/test_tasks.py`, `tests/test_live.py`,
`tests/fixtures/`, `docs/upstream/`, `docs/adr.md`, `docs/adr.json`, `README.md`,
`CHANGELOG.md` and `CLAUDE.md`. sdk-template's
[CHANGELOG](https://github.com/xippios/sdk-template/blob/main/CHANGELOG.md) says, per
release, what to port into those by hand in the same pull request.

## When something is unclear

Prefer the smallest change that satisfies the documents the README lists, state the
assumption in the pull request's description, and stop rather than guess at upstream
semantics or the shape of the public API.

## CashCtrl specifics

The sections above and the commands under `.claude/commands/` hold here as well. The
subsections below hold cashctrl's own lines, and where a command and this section differ,
this section is cashctrl's form.

### How to add an endpoint

`/add-endpoint` walks it. Steps 1, 5 and 7 are the command's, step 7's task name
first in its README cell as the family check reads it (cashctrl's README has no comment
above its status table); steps 2 to 4 and 6 read here:

2. `models.py`: an `UpstreamModel` per payload object; dates, numbers and enums typed.
   Upstream's camelCase spellings are accepted with `Field(validation_alias=...)`, never
   `Field(alias=...)`: the adapters serialise by alias, and results stay snake_case.
   `created_by` and `last_updated_by` are `AuditUser`, which masks CashCtrl's API user
   tag to `API:REDACTED`, the fixtures' value.
3. `api/<operation>.py`: one async wrapper that takes `org` first, calls
   `_client.client_for(org)` and returns models through `xippios.core.parse`.
4. `tasks.py`: an async task, `org` its first parameter, that composes wrappers and
   returns `Result[T]` with full `ResultMeta` through `_meta(org, ...)` (source,
   endpoint, `tenant=org`, request parameters, `published_at`/`vintage` when the upstream
   gives them). Derive the sync one with
   `sync()`, add its name to `__all__`, re-export it from `__init__.py`. What it returns
   leaves out documented personal identifiers (`ssn`, `iban` and their like) unless it
   fetches them deliberately and says so, and a write task does not echo one in
   `meta.request` (sdk-core ADR-0017).

Step 5, the docstring for agents, is the command's; then:

6. `/record-fixture` for at least one case (demo only), a replay test in `test_tasks.py`
   with `org="demo"` that also calls the tool end to end with
   `xippios.core.testing.mcp_call` (and compares what was sent through
   `sent_urls(route)` or `sent_query(route)` with `recorded_query(fixture)`, never a
   request from `route.calls`), a case in `TOOL_CASES` (which
   checks `meta.tenant` and snake_case keys for every tool; a tool whose recorded
   answer is empty goes into `UNOBSERVED`, whose models' field names are checked as
   well, and a field kept as upstream sends it into `AS_SENT`), a live smoke test in
   `test_live.py` that takes the `demo_org` fixture.

A list that documents `start` and `limit` (journal, persons, orders, history) pages through
`_offset_pages` in `tasks.py` (conventions §4, sdk-core ADR-0034): `limit` given is one request
for the page at `start` (default 0); `limit` omitted collects every page from `start`
through core's `paginate_offset`, `PAGE_SIZE` (100, upstream's documented default) a
request. `meta.total` is upstream's `total` on every list task, never `len(data)`.

Lookups (accounts, currencies, tax codes, fiscal periods, account and person categories,
titles, cost centers, locations, custom fields) are tasks too, named `list_<thing>`, so
agents can form valid calls; they serve the organisation's own data live and are never
packaged: a multi-tenant source packages no tenant data, nor a value set
`docs/upstream/` fixes (`PACKAGED_LISTS` is empty; `/refresh-reference-data` says how
one would come). A lookup whose whole list an
agent needs and the default result cap (200 rows or 64 KB) would cut gets a cap of its
own in `MCP_CAPS` in `tasks.py`, which `mcp.py` passes through (sdk-core ADR-0038, decision 5):
`list_custom_fields` (500 rows or 128 KB; no filter but `type`, and a write needs a
type's custom fields whole) and `get_report_data` (128 KB; a report is read whole, and
over its bound its top-level rows are cut, `total` and `properties` kept whole, with the
note); `list_cost_centers` and
`list_history` keep the default bound with a note naming their filters (the history's
note also names `limit`, and core's cut ends with where to resume). Every other list
takes filters or pages, or is short. Where the documentation gives no schema and the
shape differs by kind, as the rows of `report/element/data.json` differ by report type,
the task returns upstream's JSON as sent (`JsonValue`, camelCase keys included) and says
so in its docstring; `AS_SENT` in
`tests/test_tasks.py` names those fields for the snake_case check. A task-shaped
function that returns a subset of an upstream record builds its model with
`UpstreamModel.project`; nothing is renamed or computed, parsing a value
(`parse_decimal`) is the only override.

Upstream's documented error shapes go into `classify` in `_client.py`, once; wrappers
use `client_for(org).get_json` and never inspect status codes. CashCtrl refuses with
HTTP 200 and `success: false`: `classify` raises `RequestRejected`, or `NotFoundError`
for an unknown id on a `read.json` by `id`; a 404 is an unknown endpoint
(`UpstreamError`), on a `read.pdf` by `ids` or a report download by its id an unknown
id (`NotFoundError`, observed 2026-10-29 and 2026-11-17). Observed shapes say so, with the date, in its docstring.

Files: the wrappers `<module>_list_csv|xlsx|pdf`,
`order_document_read_pdf` and `report_*_download_*` (conventions §2) call `api/_download.py`'s `download`, which streams
through core's `download` into a temporary file beside `dest` and renames it there: a
file lands where the caller says, and nothing is read into a result, held in memory or
cached. Core writes a 2xx body unread, so `download` reads `Content-Type`
first: JSON is a refusal sent as HTTP 200, whose head goes through `classify`; the file
is removed and `dest` left as it was. The recorder never records a binary body or a
file endpoint, so a file wrapper has no fixture directory: `tests/test_downloads.py`
mounts synthetic bytes; `test_live.py` downloads one order document, two exports and
the five report files, and expects an unknown order's and an unknown report's refusal.

### How to record a fixture

`/record-fixture <endpoint> <case> <parameters>` walks it, and the docstring of
`scripts/record_fixture.py` holds the recorder's policies in full: one request through a
client that never retries, core's `Scrub` (conventions §10) and its own `TenantScrub`
(sdk-core ADR-0042, decision 4), the final check before the one write, and the delete it
asks for after a write. The demo-only rule above names what it scrubs and refuses.
Before committing, run the grep block of `/record-fixture` (step 5); its last two greps
print `0`. Fixtures are never typed in by hand.

### Never

Besides the list under Never above:

- Never hand-write a fixture, and never commit one without grepping for key patterns
  and for values under `ssn` and every name ending in `iban`.
- Never record a fixture, run a live test or make a live call against any organisation
  but `demo`; never set `CASHCTRL_ORGS` with real names in a session or a test.
- Never print, log or commit `CASHCTRL_DEMO_SUBDOMAIN` or any organisation's subdomain.
- Never add a task, tool or helper that spans organisations.
- Never point fixtures, live tests or the seeder at an organisation with real data: the
  demo organisation holds synthetic books only, created and seeded as `docs/demo-org.md`
  describes.
