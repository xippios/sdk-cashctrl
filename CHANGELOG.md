# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/) (pre-1.0: breaking changes bump the minor).

## [Unreleased]

## [0.1.0] - 2026-10-25

First release. Named organisations declared in the environment, each with its own
client, key and rate limit, on core 0.2.0's `Tenants` (ADR-0014); twelve read tasks
over CashCtrl's ledger basics, journal, persons and orders, plus `list_organisations`,
as MCP tools and HTTP routes; eight confirm-gated write tools for journal entries,
persons and orders on a separate write server; fixtures and live tests against a
synthetic demo organisation only. It depends on `xippios-core~=0.2.0` from PyPI and is
built on sdk-template v0.2.0 and conventions 1.13. Nothing was published before, so
the entries under Changed, Removed and Fixed record steps on the way to this release;
a note marked superseded names what replaced one.

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
  `UpstreamError`. Neither status error messages nor `UpstreamError.body` name the
  organisation's subdomain, also where an error page echoes the host: the body names
  `cashctrl.com` instead.
- `scripts/record_fixture.py`: records fixtures from the demo organisation only. It
  scrubs credentials, rewrites the demo host to `demo.cashctrl.com`, every e-mail
  address to `user@example.com` (also written `%40` or as the HTML entities `&#64;`,
  `&#x40;`, `&commat;`) and CashCtrl's API user tag in `createdBy` and `lastUpdatedBy`
  (`API:` and the first four characters of the API user's key, observed on 2026-10-23)
  to `API:REDACTED`, and the text value of every token-like body field (`hash`, `token`,
  `secret`, `apiKey`, by name in any case; `order/read.json` sends `hash`, an
  undocumented 32-character text that may be the token of a public document link) to
  `REDACTED`, all in memory; checks the serialised fixture and the decoded strings of its
  body for the subdomain, the key, any other e-mail address, any other API user tag in
  any case and position, the key's first four characters on their own (a possible key
  prefix) and any value but `null` or `REDACTED` under a token-like name (a compound
  name such as `publicHash` goes to review, `hash` being key-like) before the one
  write; and refuses bodies that are not UTF-8 text
  (exports), any method but GET and any endpoint but `.json`. The demo organisation is
  synthetic (`scripts/seed_demo.py`, `docs/demo-org.md`), so any module and any amount
  may be recorded.
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
  `end_amount`), checked for every key of every tool and route result; `meta.request`
  keeps the parameters as sent, under upstream's names.
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
- Journal, persons and orders, six read-only tasks, each an MCP tool `cashctrl_<task>`
  and an HTTP route `/cashctrl/<task>`, all taking `org` first:
  - `list_journal_entries` (`journal/list.json`) with its eighteen documented
    parameters (`account_id`, `associate_id`, `dir`, `filter`, `fiscal_period_id`,
    `limit`, the nine `only_*` flags, `query`, `sort`, `start`), and
    `get_journal_entry` (`journal/read.json`) with the lines of a collective entry, the
    bookings per account, tax rows apart, and the persons the entry names;
  - `list_persons` (`person/list.json`) with its seventeen documented parameters
    (`category_id`, `dir`, `filter`, `limit`, the ten `only_*` flags, `query`, `sort`,
    `start`), and `get_person` (`person/read.json`) with addresses and contacts;
  - `list_orders` (`order/list.json`) with its sixteen documented parameters
    (`category_id`, `dir`, `filter`, `fiscal_period_id`, `group_id`, `limit`,
    `only_cost_centers`, `only_notes`, `only_open`, `only_overdue`, `person_id`,
    `query`, `sort`, `start`, `status_id`, `type`), `type` typed as `SALES` or
    `PURCHASE` and optional (both types without it, observed), and `get_order`
    (`order/read.json`) with its items.
  The three lists are `POST` routes (they take `filter`); an unknown id on a read raises
  `NotFoundError` (observed for the journal: "This book entry does not exist.").
- Offset pagination for the three lists (conventions 1.7 §4, ADR-0012), in one helper:
  with `limit`, one request for the page at `start` (default 0); without it, every page
  from `start` on through core's `paginate_offset`, 100 records a request (upstream's
  documented default, sent explicitly), ending after a short page or, without a further
  request, once the next offset reaches upstream's `total`. `meta.total` is upstream's
  `total`, the page's or the last page's, never computed from `len(data)`. `meta.request`
  holds the parameters as sent, `limit` left out when every page is collected. A
  `start` below 0, a `limit` below 1, either not a whole number, and an unknown `type`
  are refused with `InvalidRequestError` before any request.
- `meta.total` on the four other list tasks as well: upstream's `total`, which equals
  the records of their one answer.
- Models: `JournalEntry` and `JournalEntryDetail` with `JournalItem` (the lines of a
  collective entry) and `JournalRow` (the bookings per account), `Person` and
  `PersonDetail` with `PersonAddress` and `PersonContact`, `Order` and `OrderDetail`
  with `OrderItem`, and `OrderType`. Every observed field, typed from the create and
  update tables where they describe it and from the recorded answers otherwise
  (each model's docstring names which); amounts `Decimal`, documented dates `date`,
  undocumented timestamps `datetime`, fields only ever seen empty kept as sent. A read
  differs from its list entry, and `person/read.json` leaves out null fields.
- Fourteen fixtures recorded on 2026-10-23 from the synthetic demo organisation: the
  2025 journal in pages of five (`total` 12: 5, 5 and 2 records) and the page past the
  end (empty, `total` 12), the first five 2026 entries (`total` 38), a taxed and a
  collective entry read and an unknown id; all twelve persons (the ten seeded and
  CashCtrl's two insurance records) and the four vendors; the four 2026 sales and two
  purchase orders and one order read, re-recorded after the token field scrub so its
  `hash` is `REDACTED`.
- `list_organisations`, the MCP tool `cashctrl_list_organisations` and the route
  `GET /cashctrl/list_organisations` (ADR-0014): the declared organisations' names,
  nothing else, without a request; core's `list_task` over the registry. It stays off the
  write server; on a server locked with `--org` it lists that organisation only.
- `meta.tenant` on every task's result: the organisation the data came from, by name
  (`ResultMeta.tenant`, ADR-0014); `org` stays in `meta.request` too. `None` for
  `list_organisations`.
- Write tools, eight confirm-gated tasks in `tasks_write.py`, re-exported from
  `xippios.cashctrl` and served by `xippios-cashctrl-mcp-write` only (never by the read
  server, never as an HTTP route): `create_journal_entry`, `update_journal_entry`,
  `delete_journal_entry` (`journal/create.json`, `update.json`, `delete.json`),
  `create_person`, `update_person`, `delete_person` (`person/...`), `create_order` and
  `delete_order` (`order/create.json`, `delete.json`). Decided by Johannes in the wave 2
  interview on 2026-10-23, and in the follow-up on 2026-10-24:
  - every create and update takes exactly the parameters its create table documents,
    snake_cased, `custom` among them, and `confirm: bool = False` last;
  - while `confirm` is false nothing is written: the result is a `WritePreview`
    (`performed` false) with the exact form `payload` upstream would receive and, for
    an update or a delete, the record as it is (`before`), for an update next to the
    `changes`; a create's preview sends no request, an update's or a delete's one read.
    With `confirm` the result is a `WriteResult` (`performed` true, `insert_id`,
    `message`). Results are `Result[WritePreview[<record>] | WriteResult]`;
    `meta.request` holds `org` and, for a performed write, the fields as sent;
  - updates fail closed: they read the record, apply the arguments given and send every
    parameter `update.json` documents, derived from the record, and refuse with
    `InvalidRequestError` before any write when a mandatory parameter cannot be derived
    or a stored list of a shape never observed (attachments, allocations, bank accounts,
    children, service periods, insurance contracts, certificate values) would be lost;
  - `custom` maps `customField<ID>` names to text, sent as upstream's
    `<values>...</values>` XML with every value escaped; an update keeps the stored
    values it is not given;
  - deletes take one id and preview the record they would delete;
  - the gate is `confirm is True`: from Python anything else (`"false"`, `1`, `[0]`)
    previews; over MCP the schema turns `"true"`, `"yes"`, `"1"`, `1` into true and
    `"false"`, `"no"`, `"0"`, `0` into false and refuses anything else;
  - `update_journal_entry` and `update_person` take `clear`, the parameters to send
    empty, checked against the documented update parameters (an unknown name, or one
    both given and cleared, is refused before any request) and shown in `changes`,
    where a list given empty shows as `[]`;
  - journal `associate_id` (entry and lines) is a person's id; a name, which upstream
    would turn into a new person, is refused;
  - `update_journal_entry` refuses an entry an order or a salary run booked
    (`orderId`, `orderBookEntryId` or `salaryBookEntryId` set);
  - `update_person` follows what a live read showed on 2026-10-24: every stored
    documented field comes back under its own name, empty ones left out; an
    insurance's `insuranceNr` and `insuranceMemberNr` and an employee's `userId`, never
    seen come back, must be given or cleared; a stored address `titleId` or contact
    `purpose`, which the tables do not document, refuses the update unless the list is
    given or cleared;
  - `update_order` is left for a later wave; a delete of an unknown id stays a
    `RequestRejected` (for a journal entry the read now comes first, see Changed);
    custom field names stay `customField<ID>`.
- `list_order_categories` (`order/category/list.json`, with `type` and
  `fiscal_period_id`), a read tool `cashctrl_list_order_categories` and route
  `GET /cashctrl/list_order_categories`: the categories and their statuses, the ids
  `create_order` takes. Models `OrderCategory`, `OrderCategoryStatus`,
  `OrderBookTemplate`, typed from the category tables and the recorded answer.
- `api/_form.py`: the one form encoding (booleans `true`/`false`, `Decimal` as plain
  digits, dates `YYYY-MM-DD`, lists as compact JSON under upstream's keys, `None` and
  empty lists left out), the custom field XML, and `post_form`, which posts through
  core's `data=` with `charset=UTF-8` declared, as the seeder did. Write wrappers
  `journal_create`, `journal_update`, `journal_delete`, `person_create`,
  `person_update`, `person_delete`, `order_create`, `order_delete` with the field
  builders `journal_fields`, `person_fields`, `order_fields` and `delete_fields`, and
  `order_category_list`.
- Models for the write payloads, snake_case with upstream's camelCase accepted and
  written to the form (`JournalItemInput`, `OrderItemInput`, `PersonAddressInput`,
  `PersonContactInput`, `AllocationInput`, `AttachmentInput`, `BankAccountInput`,
  `ChildInput`, `InsuranceContractInput`, `ServicePeriodInput`; unknown keys refused),
  the documented value sets as `Literal` types (`NotifyType`, `Recurrence`,
  `Language`, `Color`, `AddressType`, `Canton`, `ContactType`, `BankAccountType`,
  `OrderItemType`), `WriteAnswer` for upstream's `{success, insertId, message}`, and
  `WritePreview` and `WriteResult`. `PersonDetail.certificate_values`.
- The recorder records writes against the demo organisation: `--method POST` for the
  eight write paths the write tools call only (`journal/create|update|delete.json`,
  `person/create|update|delete.json`, `order/create|delete.json`; every other POST and
  method refused before a request), and a `create.json` only when one of its values
  carries `xippios-live`; the `key=value` pairs are sent as the form body in their
  order; it then says that the organisation changed and asks for the matching delete.
  Its rewrite and final check cover the request body as well (raw, each form field
  decoded, each JSON value's strings).
- Thirteen fixtures recorded on 2026-10-24 from the synthetic demo organisation, every
  record marked `xippios-live` and deleted again: the sales order categories; a journal
  entry created (1020/3200, 100.00 with `UN1`), a create refused without `debitId`
  (the first recorded field-error list), the entry read back, updated (title changed,
  the whole record sent), deleted, and deleted again; a person created (an address in
  Zürich, one contact), read back, updated and deleted; a sales invoice with one item
  created and deleted.
- Live tests for the write tools: one per resource that creates a marked record,
  updates it (journal, person; previewed first, read back after, every other derived
  field unchanged) and deletes it with the tools, after sweeping marked leftovers (by
  marked text or `nr`); and one for `list_order_categories`.

### Changed

- Adopted xippios-core 0.2.0, sdk-template v0.2.0 and conventions 1.13 (conventions §15).
  - `xippios-core~=0.2.0` from PyPI, and its `mcp`, `http` and `testing` extras
    likewise: one core minor (conventions §12, ADR-0018). The git pin of sdk-core
    `863a443` is gone, `core_git_ref` is empty, and the pin's
    `# pragma: allowlist secret` with it.
  - Personal identifiers stay out of what the tasks return (ADR-0017, decided by
    Johannes on 2026-10-25: `ssn` and `iban`). `list_persons`, `get_person` and
    `get_journal_entry` return `PersonProjection`, `PersonDetailProjection` and
    `JournalEntryDetailProjection`: no `ssn`, no `iban`, and each bank account without
    its `iban`, its other keys kept. The endpoint wrappers' `Person`, `PersonDetail`
    and `JournalEntryDetail` keep both. A write preview's `before` is the projection;
    `create_person` and `update_person` send `ssn` and an `iban` as given, but a
    preview's `payload` and `changes` and a performed write's `meta.request` show
    `REDACTED` (a cleared `ssn` shows empty). The recorder rewrites both to `REDACTED`
    by name and refuses a write that sends either, inside a JSON form value too; the
    fixture grep counts their values.
  - The pace keeps 60 requests per minute and gets a burst of 1, where it allowed 60 at
    once (ADR-0010 decision 1). No `QuotaPolicy` is installed: CashCtrl documents no
    quota and no window (CLAUDE.md, Rate limit). A malformed
    `CASHCTRL_<NAME>_SUBDOMAIN` is refused with what it should hold (`Tenants(hints=)`).
  - `test_replay_tests_send_the_placeholder_key` and its helpers are gone: core's plugin
    pins the key on every auth object and proves it (ADR-0013). The key-resolution test
    moved to `tests/test_key_resolution.py`, whose module-level `placeholder_api_key`
    pins nothing.
  - From the template: `/adopt-release`; the nightly `.github/workflows/live.yml`, its
    pytest step given `CASHCTRL_DEMO_SUBDOMAIN` and `CASHCTRL_DEMO_API_KEY` instead of
    the rendered `CASHCTRL_API_KEY`; pre-commit in CI; `publish.yml` refusing a
    git-pinned core; an sdist without tests; `MCP_CAPS` passed through by both servers
    (none set); `mypy --strict` over `scripts/`, with beautifulsoup4 and markdownify in
    the dev group for `refresh_upstream.py`; `scripts/refresh_reference.py
    --render-only`, and `enums.py` re-rendered with it (its first line); the command
    texts and CLAUDE.md rows that go with them.
  - `scripts/refresh_upstream.py` writes `Fetched` as the UTC time with `Z` and a note
    per file kept with HTML tables (conventions §3); the committed `FETCHED.md` keeps
    the date of the first fetch until the next refresh.
- Write tools, after the wave 2 review (decided by Johannes on 2026-10-24):
  - `clear` on a flag (`is_customer`, `is_inactive` and the other boolean update
    parameters of `update_person`) sends `false`, and the preview's `changes` shows
    `"false"` instead of an empty string: clearing a yes/no value means false.
    `clear=["sequence_number_id"]`, a parameter that is not stored and sent only when
    given, was a silent no-op; it is refused before any request with a hint to drop it.
  - `delete_journal_entry` reads the entry with `confirm=true` as well (one more
    request), and both the preview and the confirmed delete refuse, with
    `InvalidRequestError` before any write, an entry whose record carries `orderId`,
    `orderBookEntryId` or `salaryBookEntryId`, as `update_journal_entry` does: upstream
    documents that such entries cannot be deleted here, and its answer to such a
    delete was never observed. A confirmed delete of an unknown id is now
    `NotFoundError` from the read; `RequestRejected` remains for an entry deleted
    between the read and the delete. The live journal test makes one call more (40 a
    run).
- The recorder's e-mail scrub no longer takes percent-escapes into an address's local
  part: in the form body `contacts=%5B%7B%22address%22%3A%22user%40example.com...` it
  read `%5B%7B%22address%22%3A%22user` as the local part and wrote a body other than
  the one sent; now only the address is rewritten (found recording
  `person_create/ok`, whose first recording was replaced).
- `classify` documents the refusal shapes the writes showed on 2026-10-24: the
  documented `errors` list with `"message": null`, and a single `message` (not
  `errorMessage`) for a delete of an id that no longer exists; both stay
  `RequestRejected`.
- `xippios-core` is pinned to sdk-core commit `863a443` (`core_git_ref` in
  `.copier-answers.yml`, `[tool.uv.sources]` in `pyproject.toml`), the unreleased merge
  of sdk-core#17, for the tenant registry, the tenant lock and the option hooks
  (ADR-0014), the plugin's offline guarantees (ADR-0013), `Scrub`, `ResultMeta.total`
  (ADR-0012) and `ResultMeta.tenant`; before, `dbe2eba`. It is re-pinned at core 0.2.0.
  This package releases only after core 0.2.0 is on PyPI. Removing the pin alone would
  let core 0.1.0 back in, which has none of these, names the tenant host in status error
  messages and ignores `total`, so the same change raises `xippios-core` and its three
  extras to `>=0.2.0` and deletes the pin's `# pragma: allowlist secret` comment by hand.
  The bound cannot be raised yet: core main still reports 0.1.0 (superseded: core 0.2.0
  from PyPI, `~=0.2.0`, see the adoption above).
- Adopted from that core: status error messages name the method and the path, never the
  host (`404 from GET /api/v1/account/nope.json: ...`, sdk-core#14), so `classify` no
  longer rewrites the request URL; it still hands core a copy of the response whose body
  names `cashctrl.com`, because core quotes the body in the message and keeps it as
  `UpstreamError.body`. Core's `build_server` and `main` set the `httpx` and `httpcore`
  loggers to WARNING (sdk-core#12), so the local `quiet_request_logging` is gone.
- `api/_params.py` encodes booleans and drops unset parameters once, for every list
  wrapper.
- chore: update to sdk-template v0.1.5.
  - Hygiene files: `.gitattributes` keeps `docs/upstream/` byte-exact, `.gitignore`
    covers `.env.*` and `.envrc.*`, the secrets baseline skips `.copier-answers.yml`.
  - Command texts: `/add-endpoint`, `/refresh-reference-data` and `/refresh-upstream`
    (which now runs `scripts/refresh_upstream.py` where it exists), the MCP server
    instructions and the `reference/README.md` wording follow the template.
  - Placeholder-key test: every test but a live one sends the placeholder key, pinned on
    `CASHCTRL_API_KEY` and on `auth.key` (now in `_client.__all__`), and
    `test_replay_tests_send_the_placeholder_key` checks the basic auth user name
    (superseded by the registry, see Removed below).
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
  cached never reaches the next offline test (and that it would without the reset)
  (superseded by core's class-level pin, see Removed below).
- Rate limit, ADR-0010 decisions 1, 2, 3 and 5 adopted (CLAUDE.md, Rate limit): 60
  requests per minute per organisation, a self-imposed pace since CashCtrl documents no
  limit; no longer-window quota to ration; a 429 is `RateLimitError` with `retry_after`
  from `Retry-After` through core's mapping in `classify`, now tested through the client;
  pauses are stated by core's adapters. `x-cashctrl-requests-left` is not read (unknown
  window and scope); decision 4 waits for core's quota helper.
- Adopted from core (ADR-0014): the organisation registry is `xippios.core.Tenants`,
  `TENANTS` in `_client.py`, with the same variables (`CASHCTRL_ORGS`,
  `CASHCTRL_<NAME>_SUBDOMAIN`, `CASHCTRL_<NAME>_API_KEY`, the reserved `demo`) and the
  one-label subdomain check, lower-cased, as `check_subdomain`; `client_for(org)` is
  `TENANTS.client_for(org, ...)`. Messages read "unknown tenant" and "declared tenants"
  for an undeclared name; a malformed `CASHCTRL_ORGS` entry is named by its position,
  never quoted; a refused subdomain is "does not hold a valid SUBDOMAIN". A changed key
  now builds a new client, as a changed subdomain did.
- Adopted from core: `--org` on both servers is core's `TenantLock`, reached through
  `main`'s `add_options` and `apply_options` (`_cli.py`), the command line parsed once.
  Three behaviours follow core: a call that leaves `org` out of a tool that takes it is
  refused by the lock (`... the call did not name the tenant`) instead of by the tool's
  argument validation; a refused call reads `error: InvalidRequestError: this server is
  locked to org=<name>; the call named another tenant`; the instructions end with "This
  server is locked to org <name>; every tool call that takes org must pass org=<name>."
  Core also serves the write server over `--http` on a loopback `--host` only, unless
  `--allow-remote` is passed.
- Adopted from core (conventions §10): the recorder scrubs with
  `Scrub(host="demo.cashctrl.com", secrets=[key, its basic-auth token],
  rewrite=scrub_text, allow_binary=False)` through `fixture_from_response`. A key in a
  response is now written as `REDACTED` instead of refusing the fixture, and the fixture
  goes to review (exit status 1, a note naming the variable); core's verify refuses a key
  the scrub could not reach (behind a JSON escape); core refuses a body that is not UTF-8
  text with its own message, which the recorder prefixes with "exports are out of scope
  for fixtures;". The e-mail, API user tag and
  token-field scrubs stay local, as `scrub_text`, which the recorder also applies to the
  request URL, since core's rewrite does not reach it; the final check keeps the bare
  subdomain, e-mail addresses, API user tags, the key prefix and token-like values, and
  runs before the one write, which stays the recorder's own.
- Adopted from core (ADR-0013): the plugin keeps the run offline and sends the
  placeholder key from every auth object; `CASHCTRL_DEMO_API_KEY` is named in
  `xippios_placeholder_key_envs`. `tests/conftest.py` keeps the demo-only handling: the
  `CASHCTRL_*` strip at import, `CASHCTRL_ORGS` removed per test, the placeholder
  subdomain and `TENANTS.reset()` around each test. Tests that resolve keys themselves
  override `placeholder_api_key`. `mcp_call` goes through an in-process `mcp.Client`, so
  a schema refusal fails it with `AssertionError` instead of `ToolError`.

### Removed

- `_org_lock.py` (`org_lock`, `announce_lock`, `parse_org` and its `main`), replaced by
  core's `TenantLock` and option hooks; and from `_client.py` `orgs()`, `require_org()`,
  `reset_clients()`, `subdomain_env()`, `api_key_env()`, `ORGS_ENV` and the local client
  cache, replaced by `TENANTS.names()`, `require()`, `reset()`, `var()` and `list_var`.
  Nothing was released, so no compatibility names remain.
- The `pytester` proof that a key a live test cached never reaches the next offline
  test, and its `pytester` plugin: core's class-level placeholder pin guarantees it and
  core's own tests prove it.
- The scaffold's single client (`client`, `auth`, `config`, `BASE_URL` and `API_KEY_ENV`
  in `_client.py`) and its `CASHCTRL_API_KEY` variable, replaced by the organisation
  registry above.

### Fixed

- The `PersonAddress` docstring said `title_id` was only seen as `null`; an address
  `titleId` was stored and read back in the live verification of 2026-10-24
  (`docs/demo-org.md`, Person reads). It is in neither `addresses` table of
  `person/create.json` or `person/update.json`, but reads return it.
