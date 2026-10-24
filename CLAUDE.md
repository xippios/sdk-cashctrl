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
| Rate limit | 60 requests per minute per organisation, a self-imposed pace in `_client.py` (upstream documents no limit, only a 429); ADR-0010 decisions 1, 2, 3 and 5 adopted, see Rate limit below |
| Write tools | yes, in `tasks_write.py`, served by `xippios-cashctrl-mcp-write` |
| Core pin | `xippios-core` from git at sdk-core `863a443` (`core_git_ref` in `.copier-answers.yml`, `[tool.uv.sources]` in `pyproject.toml`), the unreleased merge of sdk-core#17, for the tenant registry, the tenant lock and the option hooks (ADR-0014), the plugin's offline guarantees (ADR-0013), the recorder's `Scrub`, `ResultMeta.total` (ADR-0012) and `ResultMeta.tenant`, host-free error messages and the quiet request log. Decided on 2026-10-24: re-pin at core 0.2.0. This package releases only after core 0.2.0 is on PyPI. Removing the pin (`uvx copier update -d core_git_ref=`) is not enough: it would let core 0.1.0 back in, which has no `Tenants`, no `TenantLock`, no `Scrub` and no `ResultMeta.tenant`, names the tenant host in status error messages and ignores `total`. The same change raises `xippios-core` and its three extras (`mcp`, `http`, `testing`) to `>=0.2.0` in `pyproject.toml` and deletes the `# pragma: allowlist secret` comment by hand. The bound cannot be raised yet: core main still reports version 0.1.0 |

The snapshot in `docs/upstream/` is the reference for names, parameters and semantics.
If it is empty or stale, run `/refresh-upstream` first and review the diff. Never write a
wrapper from memory of the API.

## Organisations

CashCtrl serves each organisation from its own subdomain, and an API user belongs to one
organisation. `_client.py` is therefore a registry, not one client: `TENANTS`, an
`xippios.core.Tenants` (ADR-0014, conventions §7), declared as `CASHCTRL_ORGS` with the
fields `SUBDOMAIN` and `API_KEY`, the reserved `demo` and `check_subdomain` (one DNS
label, lower-cased) as the subdomain's check.

- `org` is the first, required parameter of every task and tool, the name of a declared
  organisation (`demo`, `acme`), and every result names it as `meta.tenant` (it stays in
  `meta.request` as well). `client_for(org)` is `TENANTS.client_for(org, _build)`: that
  organisation's own client, own base URL, own key, own token bucket, no shared cache,
  rebuilt when one of its variables changes (the key included). An undeclared name is an
  `InvalidRequestError` listing the declared ones ("unknown tenant"); a malformed
  `CASHCTRL_ORGS` or a missing or malformed subdomain is a `ConfigError` naming the
  variable, never its value.
- `TENANTS.names()` reads `CASHCTRL_ORGS` (comma-separated, `^[a-z0-9_]+$`) on every call
  and appends `demo` when `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY` are both
  set. `list_organisations` (core's `list_task`, the tool `cashctrl_list_organisations`)
  returns those names, nothing else, on the read server and as a route; on a locked
  server, the locked organisation only.
- `--org <name>` locks an MCP server (read or write) to one organisation (`_cli.py`,
  core's `TenantLock` through `main`'s `add_options` and `apply_options`): an undeclared
  name or a missing or malformed subdomain stops it at startup (exit status 2), its
  instructions name the organisation, and a tool call that names another organisation,
  or leaves `org` out of a tool that takes it, is refused with
  `error: InvalidRequestError: this server is locked to org=<name>; ...` before the tool
  runs. Core serves the write server over `--http` on a loopback `--host` only, unless
  `--allow-remote` is passed. Three things differ from the former local lock
  (`_org_lock.py`): a call without `org` is refused by the lock, not left to the tool's
  argument validation; the list lists the locked organisation only; and the write server
  needs `--allow-remote` beyond loopback. The HTTP router has no lock: consumers pass
  `org` explicitly.
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
`API:REDACTED` and token-like body fields (`hash`, `token`, `secret`, `apiKey`) to
`REDACTED`, in the request body as well, and refuses any method but GET and POST, a POST
to anything but a `create.json`, `update.json` or `delete.json`, and any endpoint but
`.json`. Writes against demo create a record marked `xippios-live`, update it and delete
it again, nothing else (see Write tools). The demo subdomain is treated like a key: never
in a file, a commit, a log line or a report. The repository is public.

## Rate limit (ADR-0010)

Decisions 1, 2, 3 and 5 of ADR-0010 are adopted; decision 4 waits for core's quota helper.

1. **Pace.** 60 requests per minute per organisation, one token bucket per client
   (`RATE_LIMIT` in `_client.py`). The pace is self-imposed: CashCtrl documents no
   per-second or per-minute limit, only a 429 ("We recommend adding delays between your
   requests", `docs/upstream/error-handling.md`).
2. **Quotas.** No longer-window quota is documented, so nothing is rationed.
3. **A spent limit.** A 429 becomes `RateLimitError` through core's status mapping inside
   `classify`, with `retry_after` from `Retry-After` when upstream sends it; retries
   honour it up to `backoff_max`, beyond which the error reaches the caller
   (`tests/test_errors.py`). CashCtrl documents no fallback, and every answer carries
   `x-cashctrl-requests-left` (299 on every answer observed on 2026-10-23, a 401
   included) with an unknown window and scope, so it is not read.
4. **No firing into a spent quota** waits for the core helper ADR-0010 announces.
5. **Pauses are stated** by core's adapters: `error: RateLimitError: ... (retry after N s)`
   over MCP, a 429 problem with `retry_after` and `Retry-After` over HTTP.

## Read first, in this order

1. `docs/upstream/FETCHED.md` and the files it lists: what the upstream actually offers
2. The family conventions: `../sdk-core/docs/conventions.md` and `../sdk-core/docs/adr/`
   (also at https://github.com/xippios/sdk-core/tree/main/docs)
3. `../sdk-core/docs/definition-of-done.md`: what a PR must satisfy
4. The family file `../CLAUDE.md`

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
  _client.py       organisation registry: TENANTS (core's Tenants), client_for(org), classify
  _cli.py          --org for both MCP servers: core's TenantLock through main's option hooks
  errors.py        RequestRejected (HTTP 200 with success:false) and FieldError
  models.py        pydantic models mirroring upstream payloads (UpstreamModel)
  api/             endpoint wrappers, one module per upstream operation; _form.py encodes and posts writes
  tasks.py         task functions and list_organisations; __all__ is what the adapters register
  tasks_write.py   confirm-gated write tasks for the separate write server (Write tools below)
  mcp_write.py     xippios-cashctrl-mcp-write entry point
  mcp.py           xippios-cashctrl-mcp entry point
  http.py          FastAPI router
  params.py        packaged value sets: PACKAGED_LISTS, packaged_values(); none yet
  enums.py         StrEnums generated from documented value sets; never edited by hand
  reference/       documented value sets plus README with provenance; never tenant data
scripts/
  refresh_reference.py   stub until a documented value set is needed (refresh-reference-data)
  refresh_upstream.py    regenerates docs/upstream/ and its FETCHED.md from upstream
  record_fixture.py      records one exchange with the demo organisation; core's Scrub plus e-mails, API tags, tokens
  seed_demo.py           seeds a fresh, empty demo organisation with synthetic books (docs/demo-org.md)
tests/
  conftest.py      core's plugin; demo-only environment, placeholder subdomain, clients reset per test, demo_org
  fixtures/        recorded responses, <endpoint>/<case>.json, never hand-written
  test_tasks.py    structural checks on every task plus per-task replay tests
  test_tasks_write.py  the write tasks: previews send nothing, writes replay, updates fail closed
  test_adapters.py the adapters expose exactly tasks.__all__
  test_layout.py   namespace levels stay empty; py.typed ships
  test_registry.py organisation declaration, lookup and per-organisation clients
  test_errors.py   classify, RequestRejected and the recorded refusals
  test_org_lock.py the --org lock, driven through core's mcp_call_text (an in-process MCP client)
  test_record_fixture.py  the recorder never writes the demo host or key
  test_seed_demo.py       the seeder refuses unsafe states before any write, offline
  test_refresh_reference.py  nothing is packaged; the refresh script is a stub
  test_live.py     @pytest.mark.live smoke tests, demo_org only; the writes mark, sweep and delete
docs/upstream/     documentation snapshot and FETCHED.md
docs/demo-org.md   the synthetic demo organisation: why, how to create and seed it, its books
.claude/commands/  add-endpoint, record-fixture, refresh-upstream, refresh-reference-data, release-prep
```

`src/xippios/` has **no** `__init__.py`: it is a PEP 420 namespace package shared with
`xippios-core` and every other source package.
Never add one; `tests/test_layout.py` fails if it appears. The import path is
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
   `sync()`, add its name to `__all__`, re-export it from `__init__.py`.
5. Docstring for agents: one sentence, then `Args:` with examples of valid values for
   every parameter. The MCP tool description and the OpenAPI summary come from it.
6. `/record-fixture` for at least one case (demo only), a replay test in `test_tasks.py`
   with `org="demo"` that also calls the tool end to end with
   `xippios.core.testing.mcp_call`, a case in `TOOL_CASES` (which checks `meta.tenant`
   and snake_case keys for every tool), a live smoke test in `test_live.py` that takes
   the `demo_org` fixture.
7. `CHANGELOG.md` under Unreleased, README status table, then the full check suite.

A list that documents `start` and `limit` (journal, persons, orders) pages through
`_offset_pages` in `tasks.py` (conventions §4, ADR-0012): `limit` given is one request
for the page at `start` (default 0); `limit` omitted collects every page from `start`
through core's `paginate_offset`, `PAGE_SIZE` (100, upstream's documented default) a
request. `meta.total` is upstream's `total` on every list task, never `len(data)`.

Lookups (accounts, currencies, tax codes, fiscal periods) are tasks too, named
`list_<thing>`, so agents can form valid calls; they serve the organisation's own data
live and are never packaged (`/refresh-reference-data`). A task-shaped function that
returns a subset of an upstream record builds its model with `UpstreamModel.project`;
nothing is renamed or computed, parsing a value (`parse_decimal`) is the only override.
Upstream's documented error shapes go into `classify` in `_client.py`, once; wrappers
use `client_for(org).get_json` and never inspect status codes. CashCtrl refuses with
HTTP 200 and `success: false`: `classify` raises `RequestRejected`, or `NotFoundError`
for an unknown id on a `read.json` read by id; a 404 means an unknown endpoint and
raises `UpstreamError`. Observed shapes say so, with the date, in its docstring.

## Write tools

`tasks_write.py` holds the write tasks (`create_*`, `update_*`, `delete_*` for journal
entries, persons and orders), served by `xippios-cashctrl-mcp-write` only: never by the
read server, never on the HTTP router (`tests/test_adapters.py` runs core's
`assert_write_tools`). The decisions behind them were taken by Johannes in the PR 6
interview on 2026-10-23; the recipe for one more:

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
   keyword arguments, `custom: Mapping[str, str] | None` among them. It returns
   `Result[WritePreview[<record>] | WriteResult]`: while `confirm` is false a
   `WritePreview` (`performed=False`, `endpoint`, `payload` = the exact fields,
   `before` = the record for an update or a delete, `changes` for an update) with
   `meta.request` = `{"org": org}`; with `confirm` a `WriteResult` (`performed=True`,
   `insert_id`, `message`) with `meta.request` = `org` plus the fields as sent. The
   payload is never in a result twice. A create's preview sends nothing; an update's
   or a delete's sends one read, never a write.
3. **Updates read, merge, send.** Upstream empties every parameter an update omits.
   `update_*` reads the record, maps every parameter `update.json` documents from it
   (`_journal_values`, `_person_values`), applies the arguments given (not `None`), and
   sends all of them. A mandatory parameter neither the record nor the call gives
   raises `InvalidRequestError` before any write; so does a stored list whose shape was
   never observed (attachments, allocations, bank accounts, children, service periods,
   insurance contracts, certificate values) unless the call replaces it. Never send a
   partial record.
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
   `finally` deletes it through the wrapper if an assertion failed first.

## How to record a fixture

Run `/record-fixture <endpoint> <case> <parameters>`. It runs
`direnv exec ~/github/sdk uv run scripts/record_fixture.py <endpoint> <case> [key=value ...]`,
which performs one live request against the demo organisation, always and only, and
builds the fixture in memory with core's `fixture_from_response` and
`Scrub(host="demo.cashctrl.com", secrets=[key, its basic-auth token], rewrite=scrub_text)`
(conventions §10): credentials scrubbed, the demo host made `demo.cashctrl.com`, the key
made `REDACTED`, and the recorder's `scrub_text` over the body, the header values and
(applied by the recorder, which core's rewrite does not reach) the request URL: e-mail
addresses to `user@example.com`, CashCtrl's API user tags (`API:` and the first four
characters of a key, in `createdBy` and `lastUpdatedBy`) to `API:REDACTED` and the value
of every token-like body field (`hash`, `token`, `secret`, `apiKey`, by name;
`order/read.json` sends `hash`) to `REDACTED`. Core refuses the exchange when its verify
still finds the demo host or the key, a JSON body decoded included, and when the body is
not UTF-8 text (exports are out of scope). A response in which core redacted the key is
written but goes to review (exit status 1). The recorder's own final check then refuses,
before the one write to `tests/fixtures/<endpoint>/<case>.json`, a fixture that in its
text or in a decoded string of its body still holds the subdomain on its own, an e-mail
address, an API user tag in any case and position, the key's first four characters on
their own (a possible key prefix) or any value but `null` or `REDACTED` under a
token-like name, and the recorder refuses what a policy of the demo-only rule above
refuses. The write stays the recorder's: core's `record` writes as soon as its own
verify passes, before a source's final check could run. A compound name such as
`publicHash` is not scrubbed and goes to review. Grep the file for key patterns, e-mail
addresses, API user tags and token-like fields before committing. Fixtures are never
typed in by hand.

Writes: `--method POST` is accepted for a path ending in `/create.json`,
`/update.json` or `/delete.json` only, every other POST and every other method refused
before a request; the `key=value` pairs go as the form body, in their order, with the
write tools' `Content-Type` (`application/x-www-form-urlencoded; charset=UTF-8`). Core
records the request body, and the recorder's rewrite and final check cover it (the raw
text, each form field decoded, each JSON value's strings): host, key, e-mail addresses,
API user tags, token-like fields. After the request the recorder says that the demo
organisation changed, names the `insertId` it answered, and asks for the matching
delete, recorded or run. Record only a record marked `xippios-live`, its update and its
delete; confirm afterwards with one list per resource (`query=xippios-live`, counts
only) that nothing is left.

## Commands

```bash
uv sync --all-extras
uv run pytest                      # offline, replays fixtures
direnv exec ~/github/sdk env -u CASHCTRL_ORGS XIPPIOS_LIVE_TESTS=1 uv run pytest -m live   # demo only
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pre-commit run --all-files
uv run xippios-cashctrl-mcp --org demo   # stdio, locked to demo; --http for streamable HTTP
uv run xippios-cashctrl-mcp-write --org demo   # the write tools; --http on loopback only
```

## Workflow rules

- Branch from `main` as `feature/<topic>`, `fix/<topic>`, `chore/<topic>` or `docs/<topic>`.
  Never commit to `main`.
- Commit small, with Conventional Commits messages (`feat(tasks): add get_balance_sheet`).
- Open the PR with `gh pr create`; the body is the definition-of-done checklist from
  `.github/PULL_REQUEST_TEMPLATE.md`, ticked honestly, with assumptions listed.
- `ruff` leaves `docs/` alone; never reformat the upstream snapshot.
- Template updates: `uvx copier update` pulls the latest sdk-template tag into the
  infrastructure files (answers are in `.copier-answers.yml`; content files such as
  `tasks.py`, `api/`, `tests/` and `README.md` are never overwritten). Review the diff
  and open a `chore/template-update` PR.
- If a convention seems wrong, say so in the PR and follow it anyway; changing it is a
  PR against `sdk-core/docs/conventions.md` plus an ADR.

## Never

- Never hand-write a fixture, and never commit one without grepping for key patterns.
- Never record a fixture, run a live test or make a live call against any organisation
  but `demo`; never set `CASHCTRL_ORGS` with real names in a session or a test.
- Never print, log or commit `CASHCTRL_DEMO_SUBDOMAIN` or any organisation's subdomain.
- Never add a task, tool or helper that spans organisations.
- Never read or print `.envrc`, `.env`, or any variable ending in `_API_KEY`.
- Never write a key into a file or a commit.
- Never put logic in `mcp.py` or `http.py`; never add a route or tool by hand.
- Never rename or re-map an upstream concept to another source's (ADR-0003).
- Never edit `docs/upstream/` by hand; `/refresh-upstream` fetches, a PR reviews.
- Never add `src/xippios/__init__.py`.
- Never tag, merge, release, force-push, or touch `gh secret`. Those are human actions.
- Never point fixtures, live tests or the seeder at an organisation with real data: the
  demo organisation holds synthetic books only, created and seeded as `docs/demo-org.md`
  describes.

## When something is unclear

Prefer the smallest change that satisfies the documents above, state the assumption in
the PR description, and stop rather than guess at upstream semantics or public API shape.
