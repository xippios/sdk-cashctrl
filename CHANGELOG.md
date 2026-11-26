# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/) (pre-1.0: breaking changes bump the minor).

## [0.6.0] - 2026-11-26

### Added

- A person's `language` and `country`, a person's `language_code` and a report tree node's
  `type` declare with core's `NamedBy` the field beside them that holds their name, so a check
  of the models finds each code beside its label. Answers are unchanged: the name stands on the
  record, and `meta.names` takes no entry for these codes.
  (sdk-core ADR-0067, https://github.com/xippios/sdk-cashctrl/issues/167)
- A write tool's preview carries `reads`, the operations it read: the record's `read.json`
  for the previews of the eight updates and deletes, such as `["journal/read.json"]`, and
  `[]` for the four creates, `update_order_status` and `create_order_payment`, which send no
  request. Each of the fourteen tools' descriptions says whether its preview reads and what
  that costs, one request or none. (sdk-core ADR-0050,
  https://github.com/xippios/sdk-cashctrl/issues/88)

### Changed

- `docs/upstream/FETCHED.md` is written whole by xippios-core's snapshot frame: one row per
  file with its page's HTTP status, size, sha256, ETag and Last-Modified, the copyright line
  and the link to the terms as the page prints them, the table `Not fetched` with CashCtrl's
  terms page as not requested, and a last line that names the frame's form of the file. The
  fifteen files of the snapshot are unchanged, since the page is the one captured on
  2026-11-17. (sdk-core ADR-0062, https://github.com/xippios/sdk-core/issues/482,
  https://github.com/xippios/sdk-cashctrl/issues/145)
- A write whose answer is not JSON raises `ValidationError` with core's text, which names
  why after `is not JSON`, as in `cashctrl: response from /journal/create.json is not JSON:
  Expecting value at line 1 column 1 (char 0)`, where the text of 0.4.0 ended at
  `is not JSON`. The text changed with 0.5.0, whose notes left it out, and the class, `raw`
  and `source` are unchanged. (https://github.com/xippios/sdk-cashctrl/issues/131)
- The fourteen write tools send their write once, after a 429 too: an error after a 5xx or a
  failure in transit says that the request was sent once and that its outcome is unknown,
  and each tool's description names the read that shows whether the write was applied,
  `list_journal_entries`, `get_journal_entry`, `list_persons`, `get_person`, `list_orders`,
  `get_order` or `list_order_book_entries`, and for `create_order_payment` the orders' status
  where the payment sets one. (https://github.com/xippios/sdk-core/issues/480)
- The MCP tools' refusal of an argument that their schema refuses ends with "Nothing was
  sent.", as the package's own refusals do, and so does the refusal of a `dest` that names a
  directory or a directory that does not exist, which is core's `check_dest`. The refusals'
  classes are unchanged. (https://github.com/xippios/sdk-core/issues/481)
- The write server is named `xippios-cashctrl`, as the read server is, where it was
  `xippios-cashctrl-write`, so a client that reads a server's name sees the change. The help
  of `--allow-remote` takes core's one wording, and both servers' instructions come from the
  tasks modules. (https://github.com/xippios/sdk-core/issues/476)
- An amount without fractional digits is a JSON integer in the answers of the tools and
  routes, `45` where it read `45.0`. (https://github.com/xippios/sdk-core/issues/478)
- An organisation's client is kept until `TENANTS.reset()`, so a changed subdomain or key
  takes effect at the next start, where a running server built a new client. A malformed
  subdomain is refused by the package's own `ConfigError`, which names the variable and the
  expected form and no value. (https://github.com/xippios/sdk-core/issues/475)
- `meta.retrieved_at` of every read task is the client's time of upstream's answer, the
  oldest page's for a list that collects several, where it was the time the result was
  built. (https://github.com/xippios/sdk-core/issues/479)
- The description of `get_report_data`, `list_journal_entries`, `list_orders`,
  `list_history`, `list_persons`, `get_order_document` and of the write tools
  `create_journal_entry`, `update_journal_entry`, `delete_journal_entry`, `create_person`,
  `update_person`, `create_order`, `update_order`, `update_order_status`,
  `create_order_payment`, `create_order_book_entry` and `update_order_book_entry` is its
  task's docstring before `Args:`, under 1,000 characters, and the text of each of a tool's
  arguments stands in its input schema. The description of each of them that spends more
  than one request states the most a call sends, retries counted. (https://github.com/xippios/sdk-core/issues/485,
  https://github.com/xippios/sdk-cashctrl/issues/144)
- `list_journal_entries`, `list_persons`, `list_orders` and `list_history` without `limit`
  collect at most 24 pages of 100, for Python and MCP alike, and send no request at or past
  upstream's count. Where they need more pages they refuse with `InvalidRequestError` after
  the first request and return nothing, naming the count, the bound, the paging arguments,
  the requests sent, the page reached and the total of pages.
  (https://github.com/xippios/sdk-core/issues/480,
  https://github.com/xippios/sdk-cashctrl/issues/135)
- A refusal of a call names the first problem it finds, where it named every problem at
  once, and ends with what was sent: "Nothing was sent." before any request, and that the
  record was read and nothing was written when an update or a delete refuses after its
  read. The refusal of a payroll or people report says that only the report tree was read,
  or that nothing was sent where the tree kept from an earlier call answered.
  (https://github.com/xippios/sdk-cashctrl/issues/138)

### Removed

- `xippios.cashctrl.api` no longer exports `check_dest`, the package's own check of a
  download's `dest`. Core's `check_dest(dest, *, source=None)`, exported from
  `xippios.core`, takes its place, and the file tasks call it before their first request.
  (https://github.com/xippios/sdk-core/issues/481)

### Breaking

- The package depends on `xippios-core~=0.5.0`, its extras likewise, is updated to
  sdk-template v0.5.0 and applies conventions 1.30. The endpoint wrappers under `api/`
  answer core's `Answer`, the payload with the time it was retrieved.
  (https://github.com/xippios/sdk-cashctrl/issues/137)
- `download_persons` without `columns` sends none, so the file holds upstream's default
  columns, ten labels such as `Name` and `E-Mail Work`, none of them `ssn` or an `iban`,
  where it held the fields `list_persons` returns. Pass `columns=list(tasks.PERSON_COLUMNS)`
  for those fields. (https://github.com/xippios/sdk-cashctrl/issues/143)
- `get_order` and the `before` of an order's write preview leave out `hash`, an undocumented
  text that may be the token of a public link to the order's document and that the fixture
  recorder already treated as one. They return the new `OrderDetailProjection`, every field
  of `OrderDetail` but `hash`. (https://github.com/xippios/sdk-cashctrl/issues/142)
- Thirteen fields that upstream sends with a time of day are naive `datetime` values, where
  they were dates cut from it: a fiscal period's `start`, `end`, `salary_start` and
  `salary_end`, a tax rate's `date_valid`, a journal entry's `date_added`, `start_date` and
  `end_date`, a person's `date_birth`, an order's `date`, `start_date` and `end_date`, and a
  book entry's `date`. A fiscal period's `end` reads `2025-12-31T23:59:59` where it read
  `2025-12-31`, and a write still sends the date alone.
  (https://github.com/xippios/sdk-cashctrl/issues/141)
- The four list files take the verb `download_`: `export_journal_entries`,
  `export_accounts`, `export_persons` and `export_orders` are now `download_journal_entries`,
  `download_accounts`, `download_persons` and `download_orders`, with no alias.
  `list_order_book_entries` takes the order as `id`, upstream's name, in place of
  `order_id`, and `dest` of the eight file tasks is keyword-only
  (`download_report(org, 1, "pdf", dest=path)`).
  (https://github.com/xippios/sdk-cashctrl/issues/140)

## [0.5.0] - 2026-11-21

### Added

- `xippios.cashctrl.mcp.ENV_VARS` and `xippios.cashctrl.mcp_write.ENV_VARS` name the
  variables the package reads, as core's `EnvVar` entries: `CASHCTRL_ORGS`, then each
  organisation's `CASHCTRL_<NAME>_API_KEY` and `CASHCTRL_<NAME>_SUBDOMAIN`, both secret. A
  host reads them to configure the package without its documentation.
  (https://github.com/xippios/sdk-core/issues/245,
  https://github.com/xippios/sdk-template/issues/81)

### Changed

- Every answer the tests build or change in memory says where it comes from and which kind
  of sdk-core's conventions §10 it is, or that it is an input of the test and no answer from
  CashCtrl, and `tests/test_built_answers.py` fails a test that builds one without saying
  so. Nothing changes for a caller.
  (https://github.com/xippios/sdk-cashctrl/issues/124)
- Two errors that the client words from CashCtrl's answers name the request by its method
  and path, as xippios-core's `request_description` gives it and sdk-core's conventions §5
  ask: a refusal sent as HTTP 200, `RequestRejected`, after the fields or upstream's
  message, and the `ValidationError` of a file task whose answer is JSON but no refusal. A
  refused journal entry reads `CashCtrl rejected the request: debitId: This field cannot be empty. (POST /api/v1/journal/create.json)`,
  where it read `CashCtrl rejected the request: debitId: This field cannot be empty.`, in the
  exception's message, in a tool's answer after `error: RequestRejected:` and in a route's
  problem `detail`, and an export's stray JSON reads `CashCtrl: the answer is JSON that is neither a file nor a refusal; nothing was written (GET /api/v1/account/list.pdf)`,
  where it read `cashctrl: account/list.pdf answered JSON that is neither a file nor a refusal; nothing was written`.
  The classes, their bases, their statuses and every attribute stay, and a
  `RequestRejected` built without the new keyword `request` names no request, as before.
  (https://github.com/xippios/sdk-cashctrl/issues/117)
- `CLAUDE.md` keeps every rule it held in fewer than 37,000 characters, below the 40,000 at
  which Claude Code cuts it, and a test holds it under that bound. The recipe for a write
  tool moves into `docs/write-tools.md`, which the README's documents list, and the
  package's tests and documents cite each decision by the public pull request whose text
  holds it. No tool or result changes.
  (https://github.com/xippios/sdk-cashctrl/issues/65)
- What CashCtrl was seen doing beside its documentation moved from `CLAUDE.md`,
  `README.md`, `docs/demo-org.md` and the docstrings into `docs/upstream/OBSERVED.md`,
  each note ending with its probe: its date, its operation and its recording or request.
  `docs/upstream/FETCHED.md` lists the file in a row of its own. The descriptions of the
  MCP tools `cashctrl_get_fiscal_period`, `cashctrl_list_history`,
  `cashctrl_create_journal_entry` and `cashctrl_create_order_payment` keep what they say of
  upstream without the probe's date or the word observed, and the 404 of an unknown id on a
  report download or an order's document now rests on recorded answers.
  (https://github.com/xippios/sdk-cashctrl/issues/70)
- The two errors that `classify` words itself name the request by its method and path, as
  xippios-core's `request_description` gives it, where they named the path alone, as
  sdk-core's conventions §5 and its ADR-0030, decision 4, ask. An unknown id on a read
  reads `CashCtrl: This account does not exist. (GET /api/v1/account/read.json)`, where it
  read `CashCtrl: This account does not exist. (/account/read.json)`, and the 404 of an
  unknown id on a file path reads `CashCtrl: no record has an id asked, HTTP 404
  (GET /api/v1/report/element/download.pdf)`, where it read `CashCtrl: no record has an id
  asked, HTTP 404 (/report/element/download.pdf)`. The class, the status and every
  attribute stay. (https://github.com/xippios/sdk-cashctrl/issues/107)
- The refusal of a payroll or people report by `get_report_data`, `download_report`,
  `download_report_collection` and `download_annual_report` ends
  `(personal data, sdk-core ADR-0017)`, where it ended `(personal data, ADR-0017)`. The
  record it names is sdk-core's, since the package keeps none of its own, and no other
  refusal of the package cites a record.
  (https://github.com/xippios/sdk-cashctrl/pull/113)
- A server bound with `--org` gives instructions of its own, without the clause that every
  tool takes `org`, before the sentence that names the organisation, where it gave the
  unbound server's instructions and then that sentence. Its tools, which take no `org`,
  are unchanged. (https://github.com/xippios/sdk-template/issues/219,
  https://github.com/xippios/sdk-cashctrl/issues/112)
- Each entry point names itself in its usage line and in an error of its command line,
  `xippios-cashctrl-mcp-read: error: ...`, where both named their servers,
  `xippios-cashctrl` and `xippios-cashctrl-write`. The help of `--allow-remote` says on the
  read server that it changes nothing, since that server is not held to loopback, and on
  the write server that it serves this write server beyond loopback.
  (https://github.com/xippios/sdk-core/issues/167)
- A tool's error answer sets `isError` on its result beside the text
  `error: <ErrorClass>: <message>`, for an error the task raises, an argument the tool's
  schema refuses and one it does not declare, where it came back as a result like any
  other. A client tells an error from data without reading the text.
  (https://github.com/xippios/sdk-core/issues/168)
- `cashctrl_get_report_data` over its cap of 128 KB answers the report with its top-level
  rows cut, `total` and `properties` whole, and the note naming the period parameters,
  where it answered the note and a preview of the text alone.
  (https://github.com/xippios/sdk-core/issues/131,
  https://github.com/xippios/sdk-cashctrl/issues/61)
- A route answers an argument its schema refuses, a `dir` outside `ASC` and `DESC` or a
  missing `id` say, as problem details before the task runs: status 422, title
  `InvalidRequestError` and a detail that starts with the argument's name, where FastAPI's
  own 422 answered a `detail` list that echoed the input.
  (https://github.com/xippios/sdk-core/issues/66,
  https://github.com/xippios/sdk-cashctrl/issues/61)
- A write task's refusal that names another task names its MCP tool beside it, e.g.
  `create a new person with create_person (over MCP, the tool cashctrl_create_person)
  first`, for `list_order_categories`, `create_person`, `update_order` and
  `list_accounts`. (https://github.com/xippios/sdk-core/issues/111,
  https://github.com/xippios/sdk-cashctrl/issues/61)

### Breaking

- `xippios.cashctrl.mcp.build()` and `xippios.cashctrl.mcp_write.build()` return core's
  `ToolSet`, the tools a host serves as the entry point does, and take core's
  `TenantLock`, where they returned the server and took the package's own lock. A caller
  that built a server from `build()` passes the tool set to
  `xippios.core.mcp.build_server`, and `mcp.server` and `mcp_write.server` are the servers
  as before. (https://github.com/xippios/sdk-core/issues/245,
  https://github.com/xippios/sdk-core/issues/166)
- `xippios.cashctrl.params` and `xippios.cashctrl.enums` are gone: they held no list,
  `PACKAGED_LISTS` empty and no enumeration, since the package packages none, and no
  task, tool or route used them. A caller that imported either drops the import, and a
  value set upstream documents is a `Literal` type in `xippios.cashctrl.models`.
  (https://github.com/xippios/sdk-cashctrl/issues/111)
- A tool of either server refuses an argument that it does not declare, before it runs,
  and its error names the arguments the tool takes, where the argument was dropped and the
  tool ran without it. So a server bound with `--org` refuses a call that still names
  `org`, where it ran the tool for the bound organisation, and a client leaves out what
  the tool's schema does not list. (https://github.com/xippios/sdk-core/issues/84,
  https://github.com/xippios/sdk-cashctrl/issues/61)
- Adopts sdk-template v0.4.0, from v0.3.4, with `core_version=0.4.0`, `live_secrets=[CASHCTRL_DEMO_SUBDOMAIN]`, `api_key_location=basic`.
  The package depends on `xippios-core~=0.4.0`, whose tenant kit replaces the package's
  copies, and follows conventions 1.28. The answers `write_server=true`, `tenant_param=org`
  and `has_reference_data=false` render its two servers, their `--org` binding and the
  live run's key, and no reference scaffold.
  (https://github.com/xippios/sdk-template/releases/tag/v0.4.0, https://github.com/xippios/sdk-cashctrl/issues/112,
  https://github.com/xippios/sdk-cashctrl/issues/105)

## [0.4.0] - 2026-11-18

### Added

- Reports download as PDF and Excel files, Python only like the other file tasks:
  `download_report` writes one report, such as the balance sheet, `download_report_collection`
  a collection of them as one document, and `download_annual_report` the annual report's
  PDF. A file that holds a payroll or people report is refused before its download, by the
  rule of `get_report_data` on the report tree read right then.
  (https://github.com/xippios/sdk-cashctrl/issues/45)
- `list_cost_centers` takes `fiscal_period_id`, the fiscal period of the balances
  `opening_amount` and `end_amount`, and sends it as `fiscalPeriodId`, so `meta.request`
  names the period that answered. Left out, the balances are assumed to be the current
  period's, as before.
  (https://github.com/xippios/sdk-cashctrl/issues/24)
- `get_fiscal_period` (`fiscalperiod/read.json`, the tool `cashctrl_get_fiscal_period`)
  reads one fiscal period by its `id`, or without one the API user's current period, the
  one the lists and balances answer for when given no `fiscal_period_id`. Its
  `is_current` comes back false even for the current period, as upstream sends it, and
  `list_fiscal_periods` marks the current one.
  (https://github.com/xippios/sdk-cashctrl/issues/53)
- The write server books, changes and deletes the book entries of orders, such as a
  payment received for an invoice: `create_order_book_entry`, `update_order_book_entry`
  and `delete_order_book_entry`, confirm-gated as every write tool is. The update reads
  the entry and sends it whole, and the update and the delete write only an entry booked
  by hand, refusing one that the order's items booked. `docs/demo-org.md` names them among
  the demo role's write needs.
  (https://github.com/xippios/sdk-cashctrl/issues/43,
  https://github.com/xippios/sdk-cashctrl/issues/68)

### Changed

- The fixture recorder records the three book entry writes on marked orders only: a
  create on orders marked `xippios-live`, and an update or a delete on an entry whose
  order is marked, which it reads before the write is sent.
  (https://github.com/xippios/sdk-cashctrl/issues/44)
- The upstream documentation snapshot is refreshed as of 2026-11-17. The page is the one of
  2026-10-23 byte for byte, so no operation, parameter or semantics changed upstream, and
  `docs/upstream/FETCHED.md` now gives the fetch as a UTC time with `Z` and notes the files
  that keep nested tables as HTML. (https://github.com/xippios/sdk-cashctrl/issues/51)
- Adopts sdk-template v0.3.4, from v0.2.2, with conventions 1.27 and no new core minor: the
  floor stays `xippios-core~=0.3.0`, the write server, the organisation registry and the
  `--org` lock are unchanged, and the wheel ships the template's empty reference-data
  scaffold, `xippios/cashctrl/params.py`, `enums.py` and `reference/README.md`, which
  packages no list. The README lists the package's documents under `## Documents` and
  links its license by URL, and `CLAUDE.md` holds the rules that `.claude/family.md`
  carried, which leaves with `/adopt-release`, and cites sdk-core's decision records as
  `sdk-core ADR-NNNN`. Changelog entries are fragments under `changelog/`, the package's
  own decisions go into `docs/adr/` with the index that `scripts/adr_index.py` writes, and
  a pull request runs the organization's checks from `organization.yml`, where
  `gates.yml` was.
  (https://github.com/xippios/sdk-template/releases/tag/v0.3.4,
  https://github.com/xippios/sdk-cashctrl/issues/37,
  https://github.com/xippios/sdk-cashctrl/issues/38)

### Fixed

- The fixture recorder sends a GET only to a path that the snapshot in `docs/upstream/`
  documents as a GET: a GET to a path documented as a POST, such as `account/create.json`
  or `order/bookentry/create.json`, or to a path the snapshot does not name, is refused
  before a request is sent, as a GET to the eleven write paths already was. The method
  comes from each operation's Endpoint block, so a refreshed snapshot moves the refusal
  with it. (https://github.com/xippios/sdk-cashctrl/issues/27)

### Breaking

- The read server starts as `xippios-cashctrl-mcp-read`, beside `xippios-cashctrl-mcp-write`,
  and `xippios-cashctrl-mcp` is gone, with no alias. An MCP configuration that starts the
  read server names `xippios-cashctrl-mcp-read`. The server's name, its tools and its
  options are unchanged.
  (https://github.com/xippios/sdk-core/blob/main/docs/adr/0026-the-host-xippios-mcp.md,
  https://github.com/xippios/sdk-cashctrl/issues/29)

## [0.3.0] - 2026-10-29

The third release. It ships on xippios-core 0.3.0 (`xippios-core~=0.3.0` from PyPI, its
`mcp`, `http` and `testing` extras likewise) and sdk-template v0.2.2, aligned with
template v0.3.0 by hand: the family rules are imported from `.claude/family.md`, a frozen
copy of the template's file, and the package follows conventions 1.22. The three points
0.2.0 carried forward are settled: `get_report_data` refuses payroll and people reports
by their type before any data is requested, the API user tag CashCtrl writes into
`created_by` and `last_updated_by` reaches every result masked as `API:REDACTED`, and a
discovery mode of the demo seeder (`scripts/seed_demo.py --discovery`) creates a custom
field and a cost centre, from whose recorded answers `CustomField` and `CostCenter` are
typed again. New are `get_order_document`, an order's document as it is printed and sent;
five Python-facing file tasks, `download_order_document` and the list exports
`export_journal_entries`, `export_accounts`, `export_persons` and `export_orders`, which
stream a file to the path the caller gives and serve no MCP tool or HTTP route; and two
write tools, `update_order_status` and `create_order_payment`. The fixture recorder sends
an order write only after it has read every order the write names and found it marked
`xippios-live`, and it treats every field whose name ends in `iban` as a personal
identifier, as `get_report_data` now does for report rows. That makes 24 read tasks,
`list_organisations` among them, 5 file tasks and 11 write tools. Three changes break
0.2.0's surface, hence the minor: `get_report_data` refuses the payroll and people
reports it answered, `created_by` and `last_updated_by` come back masked, and
`CustomField` and `CostCenter` require fields they did not (`type`, `data_type` and
`row_label`; `number` and `name`).

Not covered: the fiscal period writes (`fiscalperiod/create`, `complete`, `reopen`,
`delete`, `complete_months`, `reopen_months`, `switch`; fiscal periods stay read-only,
as Johannes decided on 2026-10-28), salary (`salary/*`, which holds personal data
beyond `ssn` and `iban`, for which no policy exists yet), journal imports
(`journal/import/*`), the book-entry writes (`order/bookentry/create`, `update`,
`delete`), dossiers, `order/continue`, `order/document/mail` and
`order/document/update`, `order/document/read.zip`, `order/payment/download`,
`person/list.vcf`, `fiscalperiod/update` and `fiscalperiod/task/*`, the file module
(`file/*`, its writes and its own lists), inventory, settings, sequence numbers,
depreciation and exchange-difference bookings. cashctrl stays on template v0.2.2 and is
never updated to template v0.3.0 by `copier update`, which would delete the write
server; it adopts later core minors by hand.

Known points, carried into the next release: a payment cannot be deleted, since
CashCtrl documents no payment delete, so the `CASH_PDF` payment the live test creates
stays behind after its order is deleted (it books nothing and moves no amount);
`list_cost_centers` sends no `fiscalPeriodId`, which upstream documents for the
balances, so `opening_amount` and `end_amount` are assumed to be the current fiscal
period's, and a fiscal period parameter is left to a later release; and the fixture
recorder refuses a GET to the eleven write paths but not yet to any other path the
snapshot documents as a POST, a general check a later release adds.

### Added

- `get_order_document` (`order/document/read.json`, the tool
  `cashctrl_get_order_document`): one order's document, how it is printed and sent: its
  layout and language, the sender's and the recipient's address as printed, the payment
  references of the QR-bill and the mailing defaults. `OrderDocument` is typed from the
  answer recorded on 2026-10-29; the task returns `OrderDocumentProjection`, without
  `orgIban`, `orgQrIban` and `recipientIban` (decided by Johannes on 2026-10-28;
  ADR-0017); the recorded document holds `null` for all three, which the recorder now
  rewrites and refuses by name (under Fixed).
- Five file tasks, `download_order_document` and the list exports
  `export_journal_entries`, `export_accounts`, `export_persons` and `export_orders`,
  named in `BULK_TASKS`: Python only, no MCP tool or HTTP route (decided by Johannes on
  2026-10-28; ADR-0019 decision 4). Each streams one file to `dest`, the path its caller
  gives, through core's `AsyncClient.download` and returns `Result[Downloaded]` as core
  gives it; nothing is read into a result, held in memory or cached.
  `download_order_document` downloads `order/document/read.pdf` for `ids`, at least one
  order, one PDF a call, sent comma-separated; its docstring and the README disclose that
  an invoice's QR-bill may carry the organisation's IBAN or QR-IBAN and the recipient's
  address (Johannes, 2026-10-28: disclosed, not stripped). An export takes `format`
  (`csv`, `xlsx` or `pdf`, `models.ExportFormat`, an exported `Literal` of the documented
  values, as `Direction` and `OrderType` are), every parameter of the list it mirrors and
  `columns`; `limit` is passed through, its upstream default of 100 stated with the
  advice to read the list's `meta.total` first (the account export documents no `limit`).
  Without `columns` the person export names `PersonProjection`'s fields
  (`PERSON_COLUMNS`), so `ssn` and `iban` stay out unless the caller names them; the
  other exports send `columns` as given (Johannes, 2026-10-28). One wrapper per endpoint,
  `<module>_list_csv|xlsx|pdf` and `order_document_read_pdf` (named by conventions 1.22
  §2: a file suffix stays as the last word), none with a fixture directory, since the
  recorder records no binary body: the tests mount synthetic bytes with respx, and the
  live tests download one order document, the journal and the persons as CSV, and expect
  the refusal of an unknown order's document (the test approach as Johannes decided on
  2026-10-28).
- `update_order_status` (`order/update_status.json`) and `create_order_payment`
  (`order/payment/create.json`), the tenth and eleventh write tools, on the write server
  only and confirm-gated as the others (decided by Johannes on 2026-10-28): a preview
  sends no request and holds the exact payload, `confirm=True` sends it, nothing read
  first. `ids` and `order_ids` are lists of order ids, sent comma-separated; `status_id`
  is an id from a category's `status` in `list_order_categories`; `type` is
  `models.PaymentType` (`PAIN`, `SEPA_PAIN`, `WIRE_PDF`, `CASH_PDF`; an exported
  `Literal` of the documented values), left to upstream's default `PAIN` when not given.
  A payment is the pain.001 or PDF payment order upstream's `order/payment/download`
  delivers (not wrapped), creates no book entry and has no documented delete, as the
  docstring says. One wrapper per endpoint, `order_update_status` and
  `order_payment_create` (named by conventions 1.22 §2), their fixtures recorded on
  2026-10-29 on a marked purchase order with the purchase categories
  (`order_category_list/purchase`): the status set, the payment as `PAIN` refused (a date
  in the past, no bank accounts or BIC in the synthetic books) and as `CASH_PDF` created,
  neither answer with an `insertId`. `order/continue.json` and the book-entry writes stay
  out.
- The fixture recorder accepts the two order writes, eleven write paths, for orders
  marked `xippios-live` only: it reads every order their `ids` or `orderIds` name
  (`order/read.json`, one GET each) and refuses the write before it is sent unless each
  is marked (the marker in its description, or as its `nr`), an order it cannot read
  refusing it too (Johannes, 2026-10-28). A GET to one of the write paths is refused;
  a GET to any other path the snapshot documents as a POST is left to a later release.
- A live round trip on a marked purchase order of a seeded vendor: created, its status
  set, its payment created (`CASH_PDF`, which demo accepts), the order deleted and no
  journal entry of it left; then `order/payment/download` is probed once with the
  payment's parameters, never recorded, to see whether the payment outlived its order:
  on 2026-10-29 it answered HTTP 400, no file. The payment of a deleted order is the
  accepted residue: no book entry, no amount moved, the order gone (Johannes,
  2026-10-28).
- A download refused with HTTP 200 and `success: false` is raised, never kept as the
  file: core writes a 2xx body unread, so `api/_download.py` streams to a temporary file
  beside `dest` and reads `Content-Type` first. JSON goes through `classify`
  (`RequestRejected`, or `NotFoundError` for a read by ids); the file is removed and a
  file already at `dest` stays as it was. An id no order has is answered with HTTP 404
  (observed on 2026-10-29): `classify` raises `NotFoundError` for a 404 on a `read.pdf`
  asked by `ids` and keeps every other 404 an unknown endpoint's `UpstreamError`.
- `scripts/seed_demo.py --discovery`, the seeder's second mode: one custom field on
  persons (`Kundenreferenz`, `TEXT`) and one cost centre (`100 Verkauf Büromöbel`) in a
  demo organisation seeded before. It keeps guards 1 and 2 and has its own guard 3: both
  lists empty, and it creates the two; both holding exactly its two records, and it exits
  0 with nothing to do; anything else is refused before the first write. It never deletes
  (decided by Johannes on 2026-10-28; `docs/demo-org.md`). The demo organisation now
  holds one custom field and one cost centre.

### Changed

- Aligned with sdk-template v0.3.0 by hand, on template v0.2.2 and conventions 1.22
  (conventions §15 applied to a package that stays on its template tag and adopts core
  minors alone; no `copier update`, which would delete the write server): `CLAUDE.md`
  holds the package's facts and imports the family rules from `.claude/family.md`, a
  frozen copy of the template's file, its own lines from the former family sections moved
  into a "CashCtrl specifics" section, into which `tests/fixtures/README.md` is folded
  and then deleted (decided by Johannes on 2026-10-28); the six `.claude/commands`
  re-based on v0.3.0's text, the core-only `/adopt-release` and the write paths kept;
  `.claude/settings.json` allows `gh pr merge --auto` and no longer denies `gh pr merge`;
  `ci.yml`'s CHANGELOG step no longer exempts an adoption PR; `live.yml`'s comments and
  the PR template's enum item in v0.3.0's wording; `pyproject.toml` pins ruff 0.17.1, the
  pre-commit hook's rev, sets `junit_family = "xunit1"` and drops the `accounting`
  keyword; `BULK_TASKS` beside `MCP_CAPS` (ADR-0019 decision 4), which names the five
  file tasks under Added, and the adapters' docstrings say core skips it. Core stays at
  0.3.0.
- `get_report_data` refuses payroll and people reports with `InvalidRequestError` before
  any data request: a report whose type starts with `SALARY_` or contains `PERSON`, or is
  `SETTLEMENT`, `WITHHOLDING_TAX_SETTLEMENT`, `PEOPLE` or `ORG_CHART` (15 of the 41
  documented report types, ten of them in CashCtrl's default reports;
  `WITHHOLDING_TAX_RATES` is read), the message naming the element, its type and the
  rule. The type comes from `report/tree.json`, read once per organisation and process
  and kept with the organisation's client, so `TENANTS.reset()` drops it;
  `get_report_tree` refreshes it, and an element the kept tree lacks reads it once more.
  The drop of `ssn`, `iban` and `qrIban` keys stays the second guard (the refusal decided
  by Johannes on 2026-10-28; its rule extended in this release to the documented types
  the demo organisation's tree lacks; settles the point 0.2.0 carried forward).
- `CustomField` and `CostCenter` re-typed from `customfield/list.json` (`type=PERSON`)
  and `account/costcenter/list.json`, both recorded again with the records the new seed
  mode created (decided by Johannes on 2026-10-28): `CustomField` requires `type`,
  `data_type` and `row_label` and adds `field_id` (the `customField<id>` key a write's
  `custom` takes), `default_variable_name`, `name`, `column_name`, `pos` and the `multi`
  and `inactive` twins; `CostCenter` requires `number` (text, `"100"`) and `name` and
  adds the balances `opening_amount` and `end_amount`, which `list_cost_centers` now
  returns, `attachment_count` and the `inactive` twin.
- The fixture recorder records through a client that never retries
  (`RetryPolicy(max_attempts=1)`, `recording_client`), so a 5xx spends no request on a
  retry.
- `list_history`'s docstring says that `message`, kept as upstream writes it, names
  records and may name persons, and that no identifier comes back (decided by Johannes
  on 2026-10-28).

### Fixed

- The fixture recorder rewrites to `REDACTED` the value of every body field whose name
  ends in `iban`, in any case and at any depth, not only `iban` and `qrIban`, and its
  final check refuses one that survives, so `order/document/read.json`'s `orgIban`,
  `orgQrIban` and `recipientIban` (only seen `null` in demo) can never be recorded set;
  `ssn` stays a whole name. The count-only fixture greps follow, and `get_report_data`
  drops every key ending in `iban` from report rows by the same rule, not only `iban`
  and `qrIban`. One predicate, `models.is_identifier_key`, decides for both, and the
  raw-text scrub reaches a name with a dot or a space too (`bank.iban`).
- CashCtrl's API user tag (`API:` and the first four characters of the key) no longer
  reaches results: every model's `created_by` and `last_updated_by` masks it to
  `API:REDACTED`, as the fixtures hold it, so a live answer has a fixture's shape;
  `SYSTEM` and user names pass (decided by Johannes on 2026-10-28; settles the point
  0.2.0 carried forward).

## [0.2.0] - 2026-10-28

The second release. It ships on xippios-core 0.3.0 (`xippios-core~=0.3.0` from PyPI,
its `mcp`, `http` and `testing` extras likewise) and sdk-template v0.2.2, the floor it
needs, and follows conventions 1.21. The adoption of core 0.3.0 makes the organisation
registry, the `--org` lock, the write-server check and the recorder's host, JSON and
percent-encoded checks the package's own, copied from sdk-core (ADR-0024), and the
empty reference-data scaffolding is gone. Eight read tasks add the discovery lists the
write tools' ids come from (custom fields, person categories and titles, account
categories, cost centers, locations) and the reports (`get_report_tree`,
`get_report_data`); `update_order`, the ninth write tool, comes with two reads, an
order's book entries (`list_order_book_entries`) and the audit log (`list_history`).
That makes 23 read tasks, `list_organisations` among them, and nine write tools.

Not covered: salary (`salary/*`, which holds personal data beyond `ssn` and `iban`),
journal imports, the fiscal period create, complete and reopen, depreciation and
exchange-difference bookings, file downloads and list exports, `order/document/*`,
`order/payment/create`, `order/continue`, and inventory articles (`inventory/article/*`),
which neither `create_order` nor `update_order` needs: an order item's `inventory_id` is
optional, and every item recorded from the demo organisation has none. cashctrl stays on
template v0.2.2 and adopts later core minors by hand: template v0.3.0's update would
delete the write server (D35).

Known points, carried into 0.3.0: `CustomField` and `CostCenter` are typed from the
snapshot's create tables alone, since the demo organisation holds neither; payroll and
people reports pass through `get_report_data` with every key named `ssn`, `iban` or
`qrIban` dropped, but their type is not refused, so other personal data under
undocumented names passes (queue row 123, Johannes decides); and the API user tag
CashCtrl writes into `created_by` and `last_updated_by` (`API:` and the first four
characters of the API user's key) reaches agents as upstream sends it (row 129).

### Added

- Eight read tasks, each an MCP tool and an HTTP route, with recorded fixtures and live
  smoke tests: the discovery lists the write tools' ids come from,
  `list_custom_fields` (`customfield/list.json`, one module's `type` a call, checked
  against the documented set), `list_person_categories` (`person/category/list.json`),
  `list_person_titles` (`person/title/list.json`), `list_account_categories`
  (`account/category/list.json`), `list_cost_centers` (`account/costcenter/list.json`,
  with its filters) and `list_locations` (`location/list.json`, without the bank
  account numbers `iban` and `qr_iban`, ADR-0017); and the reports, `get_report_tree`
  (`report/tree.json`) and `get_report_data` (`report/element/data.json` for a
  `fiscal_period` or a `start_date` and `end_date`, the two forms refused together
  before a request; its rows kept as upstream sends them, every key named `ssn`, `iban`
  or `qrIban` dropped from them at any depth). The six lists, the two reports and the
  rows kept as sent were decided by Johannes on 2026-10-27 (G5 (4), (5)); the rest is
  the session's. Account categories come from the flat `list.json`, each with its
  `parent_id`, not from `tree.json`, which nests the same 38 categories with display
  fields only and lacks `accountClass` and `fullName` (compared on the demo
  organisation on 2026-10-27). The demo organisation has no custom field and no cost
  center, so those two models are typed from the create tables alone.
- `MCP_CAPS` (ADR-0016): `list_custom_fields` at 500 rows or 128 KB and
  `get_report_data` at 128 KB, since an agent needs them whole, and `list_cost_centers`
  and `list_history` with a note naming their filters.
- `update_order` (`order/update.json`), the ninth write tool, on the write server only:
  it reads the order, carries every documented parameter back unless given, its items
  too, each under the keys the items table documents and in its position, replaced
  whole when `items` is given, and sends the whole record, since upstream empties what
  an update omits; `clear` sends parameters empty (`is_display_item_gross` as `false`).
  Refused before a write: an order holding attachments, an item with allocations,
  attachments or `isOptional` or without its account, name or unit price, and an order
  that gives no `associateId`, `categoryId` or `date`. No refusal for a booked order:
  upstream documents that an order's automatic book entries change through its items.
  Recorded against demo on 2026-10-27 (order 20: created, read, updated, read, deleted;
  the read after the update shows the item as it was but for its id, which upstream
  stores anew), and tested live on a marked order with two items, updated without and
  then with `items`. The items, the live carry-back check and the scope were decided by
  Johannes on 2026-10-27 (G5 (6), (8)): no inventory articles, since an item needs no
  article id.
- `list_order_book_entries` (`order/bookentry/list.json`, one order's entries, the
  order's id as `order_id`) and `list_history` (`history/list.json`, the audit log,
  paged by `start` and `limit` with upstream's `total`, filtered by `order_id`,
  `person_id`, `statement_id`, `query` and `filter`), read tools and HTTP routes with
  recorded fixtures and live smoke tests (G5 (7), Johannes, 2026-10-27). The history
  holds who made a change (`created_by`) and upstream's text of it; the history of an
  order deleted a minute before was empty (observed).

### Changed

- Adopted xippios-core 0.3.0, sdk-template v0.2.2 and conventions 1.21 (conventions §15);
  the organisation registry, the `--org` lock, the write-server check and the recorder's
  host, JSON and percent-encoded checks are the package's own from here (ADR-0024).
- On a server started with `--org`, the tools no longer take `org`: it is bound on every
  tool at build, and the organisation list shows the bound one alone, as in 0.1.0. A
  call that still passes `org` is answered for the bound organisation, where 0.1.0
  refused another organisation's name (ADR-0024; G5 (1), Johannes, 2026-10-27; queue
  row 115).
- The write tools' descriptions name the read tools their ids come from, the discovery
  lists included: `list_person_categories`, `list_person_titles`, `list_locations`,
  `list_cost_centers`, `list_account_categories` and `list_custom_fields` (by module).
- The fixture recorder accepts a POST to `order/update.json`, nine write paths, and
  rewrites a location's `qrIban` (`qr_iban`, `qr-iban`) to `REDACTED` as it does `iban`,
  refusing a value that survives.
- The MCP descriptions of `list_accounts`, `list_journal_entries`, `list_persons` and
  `list_orders` no longer describe the result cap, which the cap's note carries (ADR-0016,
  conventions §8); what they say on paging stays.

### Removed

- The empty reference-data scaffolding: `src/xippios/cashctrl/params.py`
  (`PACKAGED_LISTS` was empty), `src/xippios/cashctrl/enums.py` (no enum),
  `src/xippios/cashctrl/reference/README.md` with its directory,
  `scripts/refresh_reference.py` (a stub that refused) and
  `tests/test_refresh_reference.py`. There is nothing to package: a multi-tenant source
  packages no tenant data, and no task needs a value set `docs/upstream/` fixes. Neither
  module was part of the public API (`__init__.py`). The fixture recorder, the upstream
  refresh and the seeder stay. `/refresh-reference-data` does not apply until a
  documented value set is needed; then the scaffold comes back from the `render_enums`
  port deleted here (`git show dfb65ce:scripts/refresh_reference.py`, dfb65ce on main,
  the merge of #13), not from template v0.2.2's, whose script needs renderers core 0.3.0
  removed.

## [0.1.0] - 2026-10-26

First release. Named organisations declared in the environment, each with its own
client, key and rate limit, on core 0.2.0's `Tenants` (ADR-0014); twelve read tasks
over CashCtrl's ledger basics, journal, persons and orders, plus `list_organisations`,
as MCP tools and HTTP routes; eight confirm-gated write tools for journal entries,
persons and orders on a separate write server; fixtures and live tests against a
synthetic demo organisation only. It depends on `xippios-core~=0.2.0` from PyPI and is
built on sdk-template v0.2.0 and conventions 1.13. The last changes before the release
enforce ADR-0017 by the projection type (`PersonDetailProjection` drops each bank
account's `iban` itself), accept the `null` `attachmentCount` CashCtrl sends for a
journal entry an order booked, and run the live tests with short tracebacks, which keep
each frame's arguments, the upstream payload among them, out of the public log. Nothing
was published before, so the entries under Changed, Removed and Fixed record steps on
the way to this release; a note marked superseded names what replaced one.

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
- Two fixtures recorded on 2026-10-26 from the demo organisation, GET only: the 2026
  journal with `onlyPurchase` (`journal_list/order_booked`, the two entries the seeded
  purchase orders booked) and the read of one of them (`journal_read/order_booked`).
- A read-only live check: the delete of a journal entry an order booked, found with
  `only_purchase`, is asked for without `confirm` and refused before any preview; a
  delete is never attempted. Two calls more, 42 a run.

### Changed

- Pre-release leftovers (decided by Johannes on 2026-10-26):
  - `PersonDetailProjection` drops the `iban` of each of `bank_accounts` itself, the
    key in any case, with a field validator, however the projection is built:
    `PersonDetailProjection.project(person)` carries no IBAN without help from the
    task, and the task's override in `tasks.py` is gone (ADR-0017, enforced by the
    type). The read model `PersonDetail` is unchanged.
  - `PersonAddress.title_id` is `int | None`, the id of a title, where it was kept as
    sent: `titleId` is "optional, NUMBER", a person title, whose `id` is "mandatory,
    NUMBER" (`docs/upstream/person.md`, lines 314 and 683).
  - The dev group pins beautifulsoup4 (`==4.15.0`) and markdownify (`==1.2.3`) to the
    versions `scripts/refresh_upstream.py` pins in its PEP 723 block, where it took
    them with `>=`.
  - The nightly `live.yml` and the live command in CLAUDE.md run pytest with
    `--tb=short`: the long traceback prints each frame's arguments, so a failed parse
    would print the upstream payload, API user tags included, into the public log.
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
  window and scope); decision 4 waits for core's quota helper (superseded: no
  QuotaPolicy, decided 2026-10-25, see the core 0.2.0 adoption entry).
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
- The write tasks showed the `iban` of an item of `bankAccounts` as `REDACTED` only
  under the key `iban` exactly; the key is now matched in any case, as the projection
  and the recorder match it (ADR-0017).
- A journal entry an order booked (`type` `ORDER`, `orderId` set) sends
  `attachmentCount` `null` in the list and the read (seen in the demo organisation on
  2026-10-26), where `JournalEntry` and `JournalEntryDetail` required a number:
  `list_journal_entries` failed with `ValidationError` on any page holding one (the
  whole 2026 journal of the demo organisation, for one), and `get_journal_entry`,
  `update_journal_entry` and `delete_journal_entry` failed at their read, before the
  booked-entry refusal. `attachment_count` is now `int | None`.
