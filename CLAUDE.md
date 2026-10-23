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
| Rate limit | 60 requests per minute per organisation, self-imposed in `_client.py`; upstream documents only a 429. Upstream answers every response with an `x-cashctrl-requests-left` header (observed 299 on 2026-10-23 across calls, including a 401; window and scope unknown); the client-side limit stays self-imposed |
| Write tools | yes, in `tasks_write.py`, served by `xippios-cashctrl-mcp-write` |

The snapshot in `docs/upstream/` is the reference for names, parameters and semantics.
If it is empty or stale, run `/refresh-upstream` first and review the diff. Never write a
wrapper from memory of the API.

## Organisations

CashCtrl serves each organisation from its own subdomain, and an API user belongs to one
organisation. `_client.py` is therefore a registry, not one client:

- `org` is the first, required parameter of every task and tool, the name of a declared
  organisation (`demo`, `acme`). `client_for(org)` returns that organisation's own
  client: own base URL, own key, own token bucket, no shared cache. An undeclared name is
  an `InvalidRequestError` listing the declared ones.
- `orgs()` reads `CASHCTRL_ORGS` (comma-separated, `^[a-z0-9_]+$`) on every call and
  appends `demo` when `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY` are both set.
- `--org <name>` locks an MCP server (read or write) to one organisation
  (`_org_lock.py`): an undeclared name or a missing or malformed subdomain stops it at
  startup (exit status 2), its instructions name the organisation, and a tool call naming
  another is refused before the tool runs. The HTTP router has no lock: consumers pass
  `org` explicitly.
- The subdomain stays out of messages and logs: status errors name `cashctrl.com`
  (`classify`), and both servers raise the `httpx` and `httpcore` loggers to WARNING so
  request URLs are never logged. The HTTP router does not: a consumer that logs at INFO
  logs httpx's request URLs with the tenant host and should set the `httpx` logger to
  WARNING, as the README says.
- Isolation is by configuration: a deployment reaches exactly what its environment
  declares. Nothing is cross-tenant: no task, tool or helper spans organisations, and
  `orgs()` returns names only.

**Demo only.** Fixtures, live tests and the fixture recorder use the organisation `demo`
and nothing else, ever. The recorder takes no organisation; every live test takes the
`demo_org` fixture, which fails unless `demo` is the only declared organisation;
`tests/conftest.py` removes every `CASHCTRL_*` variable but the demo pair when pytest
imports it, before any fixture runs, and `CASHCTRL_ORGS` again for every test. The demo
organisation is synthetic: invented books seeded by `scripts/seed_demo.py` and described
in `docs/demo-org.md` (both on the seed branch, merging separately), never a copy of real
books. So the recorder records any module and any amount; it still scrubs e-mail
addresses to `user@example.com` and refuses any method but GET and any endpoint but
`.json`. The demo subdomain is treated like a key: never in a file, a commit, a log line
or a report. The repository is public.

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
  _client.py       organisation registry: orgs(), require_org(), client_for(org), classify
  _org_lock.py     the --org lock both MCP servers use (middleware and command line)
  errors.py        RequestRejected (HTTP 200 with success:false) and FieldError
  models.py        pydantic models mirroring upstream payloads (UpstreamModel)
  api/             endpoint wrappers, one module per upstream operation
  tasks.py         task functions; __all__ is what the adapters register
  tasks_write.py   confirm-gated write tasks for the separate write server
  mcp_write.py     xippios-cashctrl-mcp-write entry point
  mcp.py           xippios-cashctrl-mcp entry point
  http.py          FastAPI router
  params.py        packaged value sets: PACKAGED_LISTS, packaged_values(); none yet
  enums.py         StrEnums generated from documented value sets; never edited by hand
  reference/       documented value sets plus README with provenance; never tenant data
scripts/
  refresh_reference.py   stub until a documented value set is needed (refresh-reference-data)
  refresh_upstream.py    regenerates docs/upstream/ and its FETCHED.md from upstream
  record_fixture.py      records one exchange with the demo organisation, host and e-mails scrubbed
tests/
  conftest.py      core's plugin; demo-only environment, placeholder demo pair, clients reset per test, demo_org
  fixtures/        recorded responses, <endpoint>/<case>.json, never hand-written
  test_tasks.py    structural checks on every task plus per-task replay tests
  test_adapters.py the adapters expose exactly tasks.__all__
  test_layout.py   namespace levels stay empty; py.typed ships
  test_registry.py organisation declaration, lookup and per-organisation clients
  test_errors.py   classify, RequestRejected and the recorded refusals
  test_org_lock.py the --org lock, driven through an in-process MCP client
  test_record_fixture.py  the recorder never writes the demo host or key
  test_refresh_reference.py  nothing is packaged; the refresh script is a stub
  test_live.py     @pytest.mark.live smoke tests, one per task, demo_org only
docs/upstream/     documentation snapshot and FETCHED.md
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
   returns `Result[T]` with full `ResultMeta` (source, endpoint, request parameters,
   `published_at`/`vintage` when the upstream gives them). Derive the sync one with
   `sync()`, add its name to `__all__`, re-export it from `__init__.py`.
5. Docstring for agents: one sentence, then `Args:` with examples of valid values for
   every parameter. The MCP tool description and the OpenAPI summary come from it.
6. `/record-fixture` for at least one case (demo only), a replay test in `test_tasks.py`
   with `org="demo"` that also calls the tool end to end with
   `xippios.core.testing.mcp_call`, a live smoke test in `test_live.py` that takes the
   `demo_org` fixture.
7. `CHANGELOG.md` under Unreleased, README status table, then the full check suite.

Lookups (accounts, currencies, tax codes, fiscal periods) are tasks too, named
`list_<thing>`, so agents can form valid calls; they serve the organisation's own data
live and are never packaged (`/refresh-reference-data`). A task-shaped function that
returns a subset of an upstream record builds its model with `UpstreamModel.project`;
nothing is renamed or computed, parsing a value (`parse_decimal`) is the only override.
Upstream's
documented error shapes go into `classify` in `_client.py`, once; wrappers use
`client_for(org).get_json` and never inspect status codes. CashCtrl refuses with HTTP 200
and `success: false`: `classify` raises `RequestRejected`, or `NotFoundError` for an
unknown id on a `read.json` read by id; a 404 means an unknown endpoint and raises
`UpstreamError`. Observed shapes say so, with the date, in its docstring.

## How to record a fixture

Run `/record-fixture <endpoint> <case> <parameters>`. It runs
`direnv exec ~/github/sdk uv run scripts/record_fixture.py <endpoint> <case> [key=value ...]`,
which performs one live request against the demo organisation, always and only, builds
the fixture in memory with credentials scrubbed and the demo host rewritten to
`demo.cashctrl.com` and e-mail addresses to `user@example.com`, and only then writes
`tests/fixtures/<endpoint>/<case>.json`. It writes nothing when the fixture still holds
the subdomain, the key or an e-mail address, when the body is not UTF-8 text (exports
are out of scope), or when a policy of the demo-only rule above refuses it. Grep the
file for key patterns and e-mail addresses before committing. Fixtures are never typed
in by hand.

## Commands

```bash
uv sync --all-extras
uv run pytest                      # offline, replays fixtures
direnv exec ~/github/sdk env -u CASHCTRL_ORGS XIPPIOS_LIVE_TESTS=1 uv run pytest -m live   # demo only
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pre-commit run --all-files
uv run xippios-cashctrl-mcp --org demo   # stdio, locked to demo; --http for streamable HTTP
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

## When something is unclear

Prefer the smallest change that satisfies the documents above, state the assumption in
the PR description, and stop rather than guess at upstream semantics or public API shape.
