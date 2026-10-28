# sdk-cashctrl — instructions for Claude Code

`xippios-cashctrl` wraps CashCtrl as a typed Python client, an MCP server
and FastAPI routes, built on `xippios-core`. This file is the contract for every session
that works here; the family rules it points to apply as well.

## What this package wraps

| | |
| --- | --- |
| Upstream | CashCtrl, https://cashctrl.com |
| API base URL | `https://<subdomain>.cashctrl.com/api/v1`, one per organisation |
| Documentation | https://app.cashctrl.com/static/help/en/api/index.html, snapshotted in `docs/upstream/` |
| Credentials | `CASHCTRL_ORGS` names the organisations; per name `CASHCTRL_<NAME>_SUBDOMAIN` and `CASHCTRL_<NAME>_API_KEY`, the key sent as the HTTP basic user name. The reserved `demo` is declared by its own pair and never listed |
| Rate limit | 60 requests per minute per organisation, burst 1; a self-imposed pace, upstream documents none, only a 429 (ADR-0010); enforced client-side in `_client.py`, one token bucket per organisation; see Rate limit below |
| Write tools | yes, in `tasks_write.py`, served by `xippios-cashctrl-mcp-write` |
| Core | `xippios-core~=0.3.0` from PyPI, its `mcp`, `http` and `testing` extras likewise: one core minor, adopted through conventions §15 (ADR-0018); sdk-template v0.2.2, the last release it updates to (Workflow rules) |

The snapshot in `docs/upstream/` is the reference for names, parameters and semantics.
If it is empty or stale, run `/refresh-upstream` first and review the diff. Never write a
wrapper from memory of the API.

## Organisations

CashCtrl serves each organisation from its own subdomain, and an API user belongs to one
organisation. `_client.py` is therefore a registry, not one client: `TENANTS`, a
`Tenants` of the package's own (`_tenants.py`, conventions §7), declared as
`CASHCTRL_ORGS` with the fields `SUBDOMAIN` and `API_KEY`, the reserved `demo` and
`check_subdomain` (one DNS label, lower-cased) as the subdomain's check. The registry,
`list_organisations` and the `--org` lock are this package's: core held them as
`xippios.core.Tenants`, `list_task` and `TenantLock` until 0.3.0 left them to it
(ADR-0024, which supersedes ADR-0014's decisions on them); `_tenants.py` and
`_org_lock.py` are private, copied from sdk-core `cb8ecdf`, and nothing outside the
package imports them. Core keeps `ResultMeta.tenant`, `main`'s option hooks and the
write server's rules.

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
  set. `list_organisations` (`_tenants.list_task`, the tool
  `cashctrl_list_organisations`) returns those names, nothing else, on the read server
  and as a route; on a bound server, the bound organisation only, `meta.tenant` `None`.
- `--org <name>` binds an MCP server (read or write) to one organisation (`_cli.py`
  through core's `main`'s `add_options` and `apply_options`, `_org_lock.py`): an
  undeclared name or a missing or malformed subdomain stops it at startup (exit status
  2). The lock is no middleware but a wrapper: `bind_tasks` hands `build_server` one tool
  per task with `org` bound at build, the same `__name__` (tool names and `MCP_CAPS` keys
  stay), the docstring without its `org` line, and a signature without `org`, so no tool
  of a bound server takes `org`; the instructions end "This server is bound to org
  <name>; every tool acts on that organisation and takes no org." A call that still
  passes `org` is not refused: core's argument check drops an argument the tool does not
  declare, and the tool acts on the bound organisation (observed under core 0.3.0,
  `tests/test_org_lock.py`). Core serves the write server over `--http` on a loopback
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
`tests/conftest.py` removes every `CASHCTRL_*` variable but the demo pair when pytest
imports it, before any fixture runs, and `CASHCTRL_ORGS` again for every test, sets the
placeholder subdomain in every offline test and calls `TENANTS.reset()` around each.
Core's plugin does the rest (ADR-0013): no network outside a test marked `live` or
`network`, no rate-limit waits, and the placeholder key on every auth object, with
`CASHCTRL_DEMO_API_KEY` named in `xippios_placeholder_key_envs`. The demo
organisation is synthetic: invented books seeded by `scripts/seed_demo.py` and described
in `docs/demo-org.md`, never a copy of real books. So the recorder records any module and
any amount; it still scrubs e-mail addresses to `user@example.com`, API user tags to
`API:REDACTED` and token-like body fields (`hash`, `token`, `secret`, `apiKey`) and the
personal identifiers `ssn` and `iban` to `REDACTED`, in the request body as well, and
refuses any method but GET and POST, a POST
to anything but the eight write paths, a create without the marker `xippios-live`, and
any endpoint but `.json`. Writes against demo create a record marked `xippios-live`,
update it and delete it again, nothing else (see Write tools). The demo subdomain is
treated like a key: never in a file, a commit, a log line or a report. The repository is
public.

## Rate limit (ADR-0010)

Decisions 1, 2, 3 and 5 of ADR-0010 are adopted; decision 4 is deliberately not applied.

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
   installed (decided by Johannes on 2026-10-25). Core's `QuotaPolicy` (ADR-0015) keeps
   a long-window quota, and CashCtrl documents none, nor a window for
   `x-cashctrl-requests-left`; its 429 asks only for delays, a pace refusal. With no
   window to give it, a policy would take its default of an hour and turn one 429
   without `Retry-After` into an hour of refusals once a call's retries are spent. A
   429 stays `RateLimitError`, with `Retry-After` when upstream sends it, and the
   self-imposed pace stands.
5. **Pauses are stated** by core's adapters: `error: RateLimitError: ... (retry after N s)`
   over MCP, a 429 problem with `retry_after` and `Retry-After` over HTTP.

## Read first, in this order

1. `docs/upstream/FETCHED.md` and the files it lists: what the upstream actually offers
2. The family conventions: `../sdk-core/docs/conventions.md` and `../sdk-core/docs/adr/`
   (also at https://github.com/xippios/sdk-core/tree/main/docs)
3. `../sdk-core/docs/definition-of-done.md`: what a PR must satisfy, and
   `../sdk-core/docs/review-checklist.md`: what the reviewer checks it against
4. The family file `../CLAUDE.md`
5. When a new core minor comes: conventions §15, the adoption checklist, which
   `/adopt-release` walks

## The one rule: three layers (ADR-0001)

```
api/<operation>.py   one async function per upstream operation, upstream names, returns models
tasks.py             the public API: composes wrappers, returns Result[T], sync facade via sync()
mcp.py  http.py      adapters: register tasks.__all__, nothing else. Never edited to add an endpoint.
```

Adapters call only task functions. Tasks call only endpoint wrappers and reference
data. If logic appears in `mcp.py` or `http.py`, it belongs in `tasks.py`.

## Layout

```
src/xippios/cashctrl/
  __init__.py      public surface: __version__ and re-exported task functions
  py.typed         PEP 561 marker; consumers' mypy --strict needs it
  _version.py      __version__ from distribution metadata
  _client.py       organisation registry: TENANTS, client_for(org), classify
  _tenants.py      Tenants and list_task, the registry's machinery (ADR-0024; private)
  _org_lock.py     the --org lock: OrgLock and bind_tasks, org bound on every tool (private)
  _cli.py          --org for both MCP servers through core main's option hooks
  errors.py        RequestRejected (HTTP 200 with success:false) and FieldError
  models.py        pydantic models mirroring upstream payloads (UpstreamModel), and the
                   projections tasks return without ssn and iban (ADR-0017)
  api/             endpoint wrappers, one module per upstream operation; _form.py encodes and posts writes
  tasks.py         task functions and list_organisations; __all__ is what the adapters register,
                   MCP_CAPS any per-tool result caps (none)
  tasks_write.py   confirm-gated write tasks for the separate write server (Write tools below)
  mcp_write.py     xippios-cashctrl-mcp-write entry point
  mcp.py           xippios-cashctrl-mcp entry point
  http.py          FastAPI router
scripts/
  refresh_upstream.py    regenerates docs/upstream/ and its FETCHED.md from upstream
  record_fixture.py      records one exchange with the demo organisation; core's Scrub, then its own
                         TenantScrub (host, encoded and JSON checks) and scrub_text
  seed_demo.py           seeds a fresh, empty demo organisation with synthetic books (docs/demo-org.md)
tests/
  conftest.py      core's plugin; demo-only environment, placeholder subdomain, clients reset per test, demo_org
  fixtures/        recorded responses, <endpoint>/<case>.json, never hand-written
  test_family.py   core's family check, one line: namespace levels, py.typed, __version__,
                   the adapters serving exactly the tasks, task shapes and docstrings, the
                   README status table, the template tag, the core bound
  test_tasks.py    structural checks on every task plus per-task replay tests
  test_tasks_write.py  the write tasks: previews send nothing, writes replay, updates fail
                   closed; the write server's own test (assert_write_tools)
  test_registry.py organisation declaration, lookup and per-organisation clients
  test_tenants.py  the registry's machinery (_tenants.py), core's tests of it plus the client close
  test_key_resolution.py  keys resolved as in production: placeholder_api_key pins nothing
  test_errors.py   classify, RequestRejected and the recorded refusals
  test_org_lock.py the --org lock: bound tools, driven through core's mcp_call_text (in-process)
  test_record_fixture.py  the recorder never writes the demo host, subdomain or key
  test_seed_demo.py       the seeder refuses unsafe states before any write, offline
  test_live.py     @pytest.mark.live smoke tests, demo_org only; the writes mark, sweep and delete
docs/upstream/     documentation snapshot and FETCHED.md
docs/demo-org.md   the synthetic demo organisation: why, how to create and seed it, its books
.github/workflows/ ci.yml (the required ci check, with the CHANGELOG and fixture-size steps),
                   publish.yml (the release train: tag, build, PyPI), live.yml (nightly live
                   tests), gates.yml (the merge gates as jobs, off until GATES_CALLER is 1)
.claude/commands/  add-endpoint, record-fixture, refresh-upstream, refresh-reference-data, release-prep,
                   adopt-release; refresh-reference-data does not apply here: cashctrl packages
                   no reference data and has no scripts/refresh_reference.py, until a documented
                   value set is needed
```

`src/xippios/` has **no** `__init__.py`: it is a PEP 420 namespace package shared with
`xippios-core` and every other source package.
Never add one; `tests/test_family.py` fails if it appears. The import path is
`xippios.cashctrl` (ADR-0006).

## How to add an endpoint

Run `/add-endpoint <upstream operation>`. In short:

1. Read the operation in `docs/upstream/`. Names, parameters and semantics come from
   there, snake_cased, nothing renamed, nothing normalised across sources.
2. `models.py`: an `UpstreamModel` per payload object; dates, numbers and enums typed.
   Upstream's camelCase spellings are accepted with `Field(validation_alias=...)`, never
   `Field(alias=...)`: the adapters serialise by alias, and results stay snake_case.
3. `api/<operation>.py`: one async wrapper that takes `org` first, calls
   `_client.client_for(org)` and returns models through `xippios.core.parse`.
4. `tasks.py`: an async task, `org` its first parameter, that composes wrappers and
   returns `Result[T]` with full `ResultMeta` through `_meta(org, ...)` (source,
   endpoint, `tenant=org`, request parameters, `published_at`/`vintage` when the upstream
   gives them). Derive the sync one with
   `sync()`, add its name to `__all__`, re-export it from `__init__.py`. What it returns
   leaves out documented personal identifiers (`ssn`, `iban` and their like) unless it
   fetches them deliberately and says so, and a write task does not echo one in
   `meta.request` (ADR-0017).
5. Docstring for agents: one sentence, then `Args:` with examples of valid values for
   every parameter. The MCP tool description and the OpenAPI summary come from it.
6. `/record-fixture` for at least one case (demo only), a replay test in `test_tasks.py`
   with `org="demo"` that also calls the tool end to end with
   `xippios.core.testing.mcp_call` (and compares what was sent through
   `sent_urls(route)` or `sent_query(route)` with `recorded_query(fixture)`, never a
   request from `route.calls`), a case in `TOOL_CASES` (which
   checks `meta.tenant` and snake_case keys for every tool), a live smoke test in
   `test_live.py` that takes the `demo_org` fixture.
7. `CHANGELOG.md` under Unreleased, README status table (the task's name first in its
   cell, in backticks, as the family check reads it), then the full check suite.

A list that documents `start` and `limit` (journal, persons, orders) pages through
`_offset_pages` in `tasks.py` (conventions §4, ADR-0012): `limit` given is one request
for the page at `start` (default 0); `limit` omitted collects every page from `start`
through core's `paginate_offset`, `PAGE_SIZE` (100, upstream's documented default) a
request. `meta.total` is upstream's `total` on every list task, never `len(data)`.

Lookups (accounts, currencies, tax codes, fiscal periods) are tasks too, named
`list_<thing>`, so agents can form valid calls; they serve the organisation's own data
live and are never packaged: a multi-tenant source packages no tenant data. Nor does the
package ship a value set `docs/upstream/` fixes, since no task needs one yet, so the
reference-data scaffolding (`params.py`, `enums.py`, `reference/`,
`scripts/refresh_reference.py`) is gone until a documented value set is needed; then it
comes back from the `render_enums` port deleted here, not from template v0.2.2's
scaffold, whose script needs renderers core 0.3.0 removed (`/refresh-reference-data` says
where). A lookup whose whole list an agent needs and the default result cap (200 rows or
64 KB) would cut gets a cap of its own in `MCP_CAPS` in `tasks.py`, which `mcp.py` passes
through (ADR-0016); none has one, since each list takes filters or pages and no list must
reach an agent whole. A task-shaped function that returns a subset of an upstream record
builds its model with `UpstreamModel.project`; nothing is renamed or computed, parsing a
value (`parse_decimal`) is the only override.
Upstream's documented error shapes go into `classify` in `_client.py`, once; wrappers
use `client_for(org).get_json` and never inspect status codes. CashCtrl refuses with
HTTP 200 and `success: false`: `classify` raises `RequestRejected`, or `NotFoundError`
for an unknown id on a `read.json` read by id; a 404 means an unknown endpoint and
raises `UpstreamError`. Observed shapes say so, with the date, in its docstring.

## Write tools

`tasks_write.py` holds the write tasks (`create_*`, `update_*`, `delete_*` for journal
entries, persons and orders), served by `xippios-cashctrl-mcp-write` only: never by the
read server, never on the HTTP router (`tests/test_tasks_write.py` checks it with
`assert_write_tools`). The decisions behind them were taken by Johannes in the wave 2
interview on 2026-10-23 and its follow-up on 2026-10-24; the recipe for one more:

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
   `update_*` reads the record, maps every parameter `update.json` documents from it
   (`_journal_values`, `_person_values`), applies the arguments given (not `None`), and
   sends all of them. A mandatory parameter neither the record nor the call gives
   raises `InvalidRequestError` before any write; so does a stored list whose shape was
   never observed (attachments, allocations, bank accounts, children, service periods,
   insurance contracts, certificate values), a stored key the input table does not
   document (an address's `titleId`, a contact's `purpose`), and a field whose absence
   from the read is unknown rather than empty (an insurance's `insuranceNr` and
   `insuranceMemberNr`, an employee's `userId`), unless the call gives or clears it.
   `person/read.json` returns every stored documented field and leaves empty ones out
   (verified live on 2026-10-24, `docs/demo-org.md`). `clear: list[str] | None` names
   parameters to send empty, a flag (`_FLAGS`) as `false`, checked against a
   `<RESOURCE>_UPDATE` table of the documented update parameters; one both given and
   cleared is refused, and so is one an update sends only when given (`_UNSENT`:
   `sequence_number_id`). A journal entry an order or a salary run booked (`orderId`,
   `orderBookEntryId`, `salaryBookEntryId`) is refused, by `delete_journal_entry` as
   well, which reads the entry first, confirmed or not. A confirmed call reads again and
   recomputes, so its payload can differ from the preview's if the record changed. Never
   send a partial record.
4. **Custom fields** are `customField<ID>` to text (`api/_form.py`'s `CUSTOM_FIELD`),
   rendered as `<values><customField1>...</customField1></values>`, values escaped; an
   update merges the given values into the stored XML (`merge_custom`) and refuses XML
   it cannot carry over value for value.
5. **Facts for docstrings.** A journal `amount` with a `tax_id` is gross, and order
   items' `unitPrice` was read as gross (observed, `docs/demo-org.md`); previews are
   free; `confirm=true` writes; ids come from `list_accounts`, `list_tax_codes`,
   `list_persons`, `list_order_categories`. Upstream refuses with HTTP 200 and an
   `errors` list (`RequestRejected` naming the fields); a delete of an id that no longer
   exists answers `success: false` with `message` (`RequestRejected`, not
   `NotFoundError`). `person.nr` is unique: a second person with the same `nr` is
   refused.
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

## Personal identifiers (ADR-0017)

CashCtrl documents two personal identifiers, a person's `ssn` ("Social security number
of the employee") and the `iban` of each of a person's `bankAccounts` (the list sends an
`iban` of its own). Decided by Johannes on 2026-10-25: exactly these two.

- The endpoint wrappers' read models stay faithful and carry them (`Person`,
  `PersonDetail`, `JournalEntryDetail.associates`; ADR-0003).
- The tasks return projections without them, built with `UpstreamModel.project` in
  `tasks.py`: `PersonProjection` (`list_persons`), `PersonDetailProjection`
  (`get_person`; each bank account kept without its `iban`, which the projection's own
  validator drops) and `JournalEntryDetailProjection` (`get_journal_entry`, its
  `associates` projected). A write preview's `before` is the same projection.
- `create_person` and `update_person` take `ssn` and, in `bank_accounts`, `iban`, and
  send them as given; a preview's `payload` and `changes` and a performed write's
  `meta.request` show `REDACTED` instead (`_shown` in `tasks_write.py`), a cleared `ssn`
  as empty.
- Fixtures never carry their values: the recorder rewrites both to `REDACTED` by name,
  and its final check refuses any other value (How to record a fixture).
- A task that fetches them deliberately may return them and says so in its docstring;
  none does.

## How to record a fixture

Run `/record-fixture <endpoint> <case> <parameters>`. It runs
`direnv exec ~/github/sdk uv run scripts/record_fixture.py <endpoint> <case> [key=value ...]`,
which performs one live request against the demo organisation, always and only, and
builds the fixture in memory with core's `fixture_from_response` and
`Scrub(secrets=[key, its basic-auth token], allow_binary=False)` (conventions §10):
credentials scrubbed and the key and its token made `REDACTED` where they appear as
given. Core's verify searches plain values only: it refuses the exchange when the key
or its token is still there as given, and when a body is not UTF-8 text (exports are out
of scope). Everything else is the recorder's own step, `TenantScrub`, on the `Fixture`
core returns, before the one write (ADR-0024, decision 4; copied from core's former
`Scrub(host=..., rewrite=...)`): the demo host, in any case, IDNA or percent-encoded,
becomes `demo.cashctrl.com` in the URL, the headers and both bodies; the key and its
token become `REDACTED` in every percent-encoded form too; and `scrub_text` runs over the
URL, the header values and both bodies: e-mail addresses to `user@example.com`,
CashCtrl's API user tags (`API:` and the first four characters of a key, in `createdBy`
and `lastUpdatedBy`) to `API:REDACTED` and the value of every token-like body field
(`hash`, `token`, `secret`, `apiKey`, by name; `order/read.json` sends `hash`) and of the
personal identifiers `ssn` and `iban` (ADR-0017; `person/list.json` sends both, only
ever `null`) to `REDACTED`. Its verify then refuses, in its own words, a fixture that
still holds the demo host, the subdomain on its own or the key or its token, plain or
percent-encoded, in the raw texts or in a decoded string of a JSON body (a value behind
a JSON escape). A response in which the key was redacted is written but goes to review
(exit status 1). The recorder's own final check then refuses,
before the one write to `tests/fixtures/<endpoint>/<case>.json`, a fixture that in its
text or in a decoded string of its body still holds the subdomain on its own, an e-mail
address, an API user tag in any case and position, the key's first four characters on
their own (a possible key prefix) or any value but `null` or `REDACTED` under a
token-like or identifier name, and the recorder refuses what a policy of the demo-only
rule above
refuses. The write stays the recorder's: core's `record` writes as soon as its own
verify passes, before the recorder's step and final check could run. A compound name such as
`publicHash` is not scrubbed and goes to review. Grep the file for key patterns, e-mail
addresses, API user tags, token-like fields and values under `ssn` and `iban` before
committing (`/record-fixture`, `tests/fixtures/README.md`). Fixtures are never typed in
by hand.

Writes: `--method POST` is accepted for the eight write paths the write tools call only
(`journal/create|update|delete.json`, `person/create|update|delete.json`,
`order/create|delete.json`, `WRITE_PATHS`), every other POST and every other method
refused before a request, and a `create.json` only when one of its values carries
`xippios-live`; the `key=value` pairs go as the form body, in their order, with the
write tools' `Content-Type` (`application/x-www-form-urlencoded; charset=UTF-8`). Core
records the request body, and the recorder's rewrite and final check cover it (the raw
text, each form field decoded, each JSON value's strings): host, key, e-mail addresses,
API user tags, token-like fields and identifiers, a form field `ssn` or the `iban` inside
`bankAccounts` included, so a write that sends one is not recorded. After the request
the recorder says that the demo
organisation changed, names the `insertId` it answered, and asks for the matching
delete, recorded or run. Record only a record marked `xippios-live`, its update and its
delete; confirm afterwards with one list per resource (`query=xippios-live`, counts
only) that nothing is left.

## Commands

```bash
uv sync --all-extras
uv run pytest                      # offline, replays fixtures
direnv exec ~/github/sdk env -u CASHCTRL_ORGS XIPPIOS_LIVE_TESTS=1 uv run pytest -m live --tb=short   # demo only
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pre-commit run --all-files
uv run xippios-cashctrl-mcp --org demo   # stdio, bound to demo; --http for streamable HTTP
uv run xippios-cashctrl-mcp-write --org demo   # the write tools; --http on loopback only
```

The offline run is core's plugin's (ADR-0013): in every test not marked `live` it refuses
the network and skips the rate limiter's waits, and the key sent is its placeholder,
with `CASHCTRL_DEMO_API_KEY` set to it because `pyproject.toml` names that variable under
`xippios_placeholder_key_envs`; the package keeps no placeholder fixture of its own
(`tests/conftest.py` keeps the demo-only environment, Organisations above).
A test that asserts a limiter wait or a quota pause is marked `rate_limited`, one that
must reach the network `network`.

`.github/workflows/live.yml` runs `uv run pytest -m live --tb=short` with
`XIPPIOS_LIVE_TESTS=1` nightly at 02:36 UTC, a time derived from the slug so that sources
sharing a key never start together, and on demand from the Actions tab; pull requests
never run live tests.
Every `live` test runs, write tests included, so a live write test acts only on data kept
for testing (the demo organisation, ADR-0024) and cleans up after itself. Only its
`uv run pytest -m live --tb=short` step sees the demo organisation's pair, from the org
secrets `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY`: the template renders the
scaffold's `CASHCTRL_API_KEY`, which nothing reads, so the workflow names the pair by
hand, and both org secrets must give sdk-cashctrl access for the nightly run to pass.
`--tb=short` is added by hand too, and every live run here uses it: pytest's long
traceback prints each frame's arguments, so a failed parse would print the upstream
payload it was given, API user tags included, into the public Actions log.

## Workflow rules

- Branch from `main` as `feature/<topic>`, `fix/<topic>`, `chore/<topic>` or `docs/<topic>`.
  Never commit to `main`.
- Commit small, with Conventional Commits messages (`feat(tasks): add get_balance_sheet`).
- Open the PR with `gh pr create`; the body is the definition-of-done checklist from
  `.github/PULL_REQUEST_TEMPLATE.md`, ticked honestly, with assumptions and open
  questions listed, the live calls the PR spent counted (keyed calls by number; `none`
  is a count), and, after the checklist, a `## Decisions taken` block: one line per
  decision the session made, each backed by a convention, an ADR, a coordination rule, a
  dated decision of Johannes's or `gap, row N`. The reviewer judges the PR against
  sdk-core's `docs/review-checklist.md`.
- Every PR but a release, an adoption or Dependabot's adds an entry under Unreleased in
  `CHANGELOG.md`; `ci.yml` fails without one (conventions §12).
- Releases follow the release train (conventions §12): `/release-prep` opens a release
  PR that changes only `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, `README.md`,
  `CLAUDE.md` and `docs/handover.md` (and `scripts/check-siblings.sh` where the source
  has one); its merge runs `publish.yml`, which tags the version on the merge commit,
  and Johannes approves the `pypi` run. A reference-data refresh or a core pin's removal
  is a PR of its own before it.
- `ruff` leaves `docs/` alone; never reformat the upstream snapshot.
- Core updates: a new core minor arrives in one adoption PR, a `chore/template-update*`
  branch, before the next release (conventions §15); when its merge class is `auto` the
  session enables auto-merge after the reviewer's `ready` (ADR-0018, amendment (e)). An
  adoption of a later core minor runs no `copier update` (D35, D85): it raises the floor
  to `~=X.Y.0` by hand in `pyproject.toml`, runs `uv lock` and ports that core release's
  Hand-apply list (`/adopt-release`). The reference-data scaffolding (`params.py`,
  `enums.py`, `reference/`, `scripts/refresh_reference.py`) does not come back, since
  cashctrl runs no further `copier update` (D35); a future value set brings the script
  back by hand from the `render_enums` port deleted here (`/refresh-reference-data`).
  From template v0.2.2 on every template-rendered file is cashctrl's own (`ci.yml`,
  `publish.yml`, `gates.yml`, `live.yml`, the PR template, the `.claude/commands` files,
  the template's parts of this file), and a core adoption hand-applies the template
  changes the conventions version it adopts needs (row 118).
- cashctrl stays on template v0.2.2 after template v0.3.0 and keeps adopting core minors
  through conventions §15; `copier update` must never be run past v0.2.2: the v0.3.0
  template deletes `mcp_write.py`, `tasks_write.py` and `tests/test_tasks_write.py` and
  rewrites `api_key_location: basic` to `query` without a conflict marker.
- If a convention seems wrong, say so in the PR and follow it anyway; changing it is a
  PR against `sdk-core/docs/conventions.md` plus an ADR.

## Never

- Never hand-write a fixture, and never commit one without grepping for key patterns
  and for values under `ssn` and `iban`.
- Never record a fixture, run a live test or make a live call against any organisation
  but `demo`; never set `CASHCTRL_ORGS` with real names in a session or a test.
- Never print, log or commit `CASHCTRL_DEMO_SUBDOMAIN` or any organisation's subdomain.
- Never add a task, tool or helper that spans organisations.
- Never read or print `.envrc`, `.env`, or any variable ending in `_API_KEY`.
- Never write a key into a file or a commit.
- Never put logic in `mcp.py` or `http.py`; never add a route or tool by hand.
- Never rename or re-map an upstream concept to another source's (ADR-0003).
- Never return a documented personal identifier in a task's projection, echo one in
  `meta.request`, or commit one in a fixture (ADR-0017).
- Never edit `docs/upstream/` by hand; `/refresh-upstream` fetches, a PR reviews.
- Never add `src/xippios/__init__.py`.
- Never run `copier update` past template v0.2.2: the v0.3.0 template deletes
  `mcp_write.py`, `tasks_write.py` and `tests/test_tasks_write.py` and rewrites
  `api_key_location: basic` to `query` without a conflict marker.
- Never tag, merge, release, force-push, or touch `gh secret`: a release PR's merge tags
  through `publish.yml`, and Johannes approves the `pypi` run. The one exception is
  enabling auto-merge on a `chore/template-update*` or `chore/release-*` PR whose merge
  class is `auto`, after the reviewer's `ready` (ADR-0018, amendment (e)).
- Never point fixtures, live tests or the seeder at an organisation with real data: the
  demo organisation holds synthetic books only, created and seeded as `docs/demo-org.md`
  describes.

## When something is unclear

Prefer the smallest change that satisfies the documents above, state the assumption in
the PR description, and stop rather than guess at upstream semantics or public API shape.
