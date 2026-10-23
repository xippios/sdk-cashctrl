# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/) (pre-1.0: breaking changes bump the minor).

## [Unreleased]

### Added

- Scaffold from [sdk-template](https://github.com/xippios/sdk-template): configured
  client for CashCtrl, empty task layer, MCP server and FastAPI router
  wired to it, test harness, CI and publishing.
- Upstream documentation snapshot in `docs/upstream/`, fetched 2026-10-23: the whole
  CashCtrl API documentation page as fifteen Markdown files, one per top-level entry of
  its table of contents (five general sections, ten modules), listed in `FETCHED.md`.
- `scripts/refresh_upstream.py`: regenerates the snapshot reproducibly from the one
  documentation page (`uv run scripts/refresh_upstream.py`).
- `scripts/seed_demo.py`: seeds a fresh, empty CashCtrl organisation with small
  synthetic books (Muster Handel AG: 10 fictional companies whose names start with a
  placeholder marker such as Muster, Beispiel or Fiktiv, 48 manual journal entries in
  2025 and 2026, 4 sales invoices and 2 purchase orders, EUR and USD if missing), so
  fixtures and live tests never touch real data. `--plan` (the default) prints the plan
  without a request; `--apply --yes` first refuses, before any write, an organisation
  whose name lacks `demo`, one with a journal entry or order in any fiscal period or a
  person other than the insurance records CashCtrl creates itself (`createdBy` SYSTEM,
  `isInsurance` true; a new organisation has two), and a chart of accounts without the
  account numbers it uses, and prints the `calcType` of the tax codes it uses. It then
  writes form-encoded with `charset=UTF-8` declared (`--multipart` for a manual rerun,
  never an automatic fallback), persons first, reads the first one (Muster Büro AG) back
  and stops unless its umlaut arrived byte for byte, starts requests 1.2 seconds apart
  with the family User-Agent, and stops at the first refusal or transport error; the
  summary, printed after a stop as well, includes the balance of 1100 at 2025-12-31 and
  2026-09-30. It reads only `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY`, never
  prints either, and scrubs every upstream text it shows.
- `docs/demo-org.md`: why the demo organisation is synthetic and the naming rule, how to
  create it with fictional data only (the main location included, which a new
  organisation lacks) and seed it, the books in full, the assumed account
  numbers and VAT codes, the balances of 1100 the books imply under a gross and a net
  reading, and the write semantics the first seeding run observed on 2026-10-23.
- Organisations: `_client.py` is a registry of named organisations instead of one
  client. `CASHCTRL_ORGS` lists them, each with `CASHCTRL_<NAME>_SUBDOMAIN` and
  `CASHCTRL_<NAME>_API_KEY`; the reserved `demo` is declared by its own pair.
  `client_for(org)` gives every organisation its own client (base URL, key, 60 requests
  per minute, no shared cache); an undeclared name is an `InvalidRequestError`.
- `--org <name>` on `xippios-cashctrl-mcp` and `xippios-cashctrl-mcp-write` locks the
  server to one organisation: an undeclared name or a missing or malformed subdomain
  stops it at startup (exit status 2), and its instructions name the organisation. Both
  servers keep httpx's request lines, which carry the subdomain, out of their log.
- `RequestRejected` (an `InvalidRequestError`, HTTP 422) for CashCtrl's HTTP 200
  `success: false` refusals, with the field errors or upstream's single message
  (`errorMessage`, else `message`). An unknown id on a `read.json` read by id (a
  non-empty `id`, at most `lang` besides) raises `NotFoundError`, as observed against the
  demo organisation; a 404, which upstream documents as an unknown endpoint, raises
  `UpstreamError`. Status error messages and `UpstreamError.body` name `cashctrl.com`,
  never the organisation's subdomain, also where an error page echoes the host.
- `scripts/record_fixture.py`: records fixtures from the demo organisation only. It
  scrubs credentials, rewrites the demo host to `demo.cashctrl.com`, every e-mail
  address to `user@example.com` (also written `%40` or as the HTML entities `&#64;`,
  `&#x40;`, `&commat;`) and CashCtrl's API user tag in `createdBy` and `lastUpdatedBy`
  (`API:` and the first four characters of the API user's key, observed on 2026-10-23)
  to `API:REDACTED`, all in memory; checks for the subdomain, the key, any other e-mail
  address and any other API user tag before the one write; and refuses bodies that are
  not UTF-8 text (exports), any method but GET and any endpoint but `.json`. The demo
  organisation is synthetic (`scripts/seed_demo.py`, `docs/demo-org.md`), so any module
  and any amount may be recorded.
- Ledger basics, five read-only tasks, each an MCP tool `cashctrl_<task>` and an HTTP
  route `/cashctrl/<task>`, all taking `org` first:
  - `list_fiscal_periods` (`fiscalperiod/list.json`), `list_currencies`
    (`currency/list.json`) and `list_tax_codes` (`tax/list.json`), which document no
    parameters;
  - `list_accounts` (`account/list.json`) with its nine documented parameters
    (`query`, `filter`, `category_id`, `fiscal_period_id`, `only_active`,
    `only_cost_centers`, `only_notes`, `sort`, `dir`); its HTTP route is a `POST`;
  - `get_account` (`account/read.json`); an unknown id raises `NotFoundError`.
- Models mirroring the payloads: `FiscalPeriod`, `Currency`, `TaxCode` with
  `TaxComponent` and `TaxRate`, `Account` (a `list.json` entry, with balances),
  `AccountDetail` (the `read.json` record), the envelopes `ListResponse` and
  `ReadResponse`, and `Filter` for the `filter` parameter. Amounts and rates are
  `Decimal`, dates `date`, timestamps naive `datetime` (`lastEntryDate`, undocumented
  and seen with a time of day, stays a timestamp). Upstream's camelCase spellings are
  read with `Field(validation_alias=...)`, so every result, in Python, over MCP and
  over HTTP, carries the snake_case names the tool arguments use (`is_current`,
  `end_amount`); `meta.request` keeps the parameters as sent, under upstream's names.
- `dir` and `Filter.comparison` are typed as their documented value sets, `Direction`
  (`ASC`, `DESC`) and `Comparison` (`eq`, `like`, `gt`, `lt`), so the tool schema lists
  them and the adapters refuse another value before the task runs.
- `list_accounts` takes each filter as a `Filter` or as a mapping with the same keys,
  and refuses, with `InvalidRequestError` and before any request, a `dir` other than
  `ASC` or `DESC`, a filter `comparison` other than `eq`, `like`, `gt` or `lt`, a
  `filter` that is not a list, an item that is neither a `Filter` nor a mapping that
  validates as one, and a `query` or `sort` that is not a string: upstream would
  silently ignore them.
- Nine fixtures recorded on 2026-10-23 from the synthetic demo organisation
  (`scripts/seed_demo.py`, `docs/demo-org.md`), with e-mail addresses and API user tags
  scrubbed: the fiscal periods, currencies and tax codes whole; the accounts narrowed
  twice from CashCtrl's default chart (number `1020`; active accounts matching
  `Finanz`), since the 139 accounts are too many for one fixture; account 1020 read by
  the id the filtered list gave; an unknown id, a missing id and a wrong key. Every
  recorded list holds its whole `total`.

### Changed

- chore: update to sdk-template v0.1.5.
  - Hygiene files: `.gitattributes` keeps `docs/upstream/` byte-exact, `.gitignore`
    covers `.env.*` and `.envrc.*`, the secrets baseline skips `.copier-answers.yml`.
  - Command texts: `/add-endpoint`, `/refresh-reference-data` and `/refresh-upstream`
    (which now runs `scripts/refresh_upstream.py` where it exists), the MCP server
    instructions and the `reference/README.md` wording follow the template.
  - Placeholder-key test: every test but a live one sends the placeholder key, pinned on
    `CASHCTRL_API_KEY` and on `auth.key` (now in `_client.__all__`), and
    `test_replay_tests_send_the_placeholder_key` checks the basic auth user name.
  - `validation_alias` rule for the models to come: upstream spellings are accepted with
    `Field(validation_alias=...)`, never `alias=` (`models.py` docstring, `/add-endpoint`).
- No reference data is packaged: CashCtrl's lists (accounts, currencies, tax codes,
  fiscal periods) are per-organisation data, served live by the list tasks. Only value
  sets the documentation fixes may ship, generated from `docs/upstream/`; none is needed
  yet, so `scripts/refresh_reference.py` is a stub that exits non-zero.
- The placeholder-key test follows the registry:
  `test_replay_tests_send_the_placeholder_key` sends a request through
  `client_for("demo")` and checks that the basic auth user name is the placeholder and
  that the shell's `CASHCTRL_DEMO_API_KEY` is nowhere in the request. Instead of pinning
  a module-level `auth.key`, `tests/conftest.py` drops every cached client before and
  after each test, and a `pytester` run of the conftest proves that a key a live test
  cached never reaches the next offline test (and that it would without the reset).

### Removed

- The scaffold's single client (`client`, `auth`, `config`, `BASE_URL` and `API_KEY_ENV`
  in `_client.py`) and its `CASHCTRL_API_KEY` variable, replaced by the organisation
  registry above.
