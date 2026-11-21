# What CashCtrl does but never documents

Notes, written by hand, on what CashCtrl's API was seen doing that no page of this snapshot
states (sdk-core's conventions §3, sdk-core ADR-0028). The pages beside this file are the
reference for names, parameters and semantics; they give no response schema for most
operations, document a refusal only as "either a success or multiple error messages", and
say of an HTTP 404 only "The requested endpoint doesn't exist." The answers' shapes, the
refusals and the writes' effects below come from the wire, from the demo organisation,
whose books are synthetic (`docs/demo-org.md`), and `models.py`, `_client.classify`, the
tasks and `tests/fixtures/` follow them. `scripts/refresh_upstream.py` neither writes nor
checks this file, and `FETCHED.md` lists it in a row of its own.

Each note ends with its probe: the date, the operation as the snapshot's Endpoint block
writes it, and the sample. A sample recorded as a fixture is named by its path under
`tests/fixtures/`, whose `recorded_at` gives the UTC time of the request. A probe that kept
no answer says so and names its request and its date, as the text that held the note gave
them. The notes moved here on 2026-11-21 from `CLAUDE.md`, `README.md`, `docs/demo-org.md`
and the docstrings of `src/xippios/cashctrl/`; the five recordings of 2026-11-21 below were
the only requests sent to write this file.

## The answers' shapes

### A list answers `total` and `data`, without `success`

Every `list.json` answers `{"total": <int>, "data": [...]}` with no `success` key, `total`
counting every record the request matches. A list that documents no `start` or `limit`
answers every record at once, `total` equal to the records sent. A page past the end of a
paged list answers an empty `data` and the same `total`.

Probe: 2026-10-23, `GET currency/list.json`, `GET tax/list.json`,
`GET fiscalperiod/list.json` and `GET journal/list.json`; samples
`tests/fixtures/currency_list/default.json`, `tests/fixtures/tax_list/default.json`,
`tests/fixtures/fiscalperiod_list/default.json` and
`tests/fixtures/journal_list/fp2025_start_15_limit_5.json`, the page past the end, `total`
12 and no record.

### A read answers `success` and `data`, and leaves out what is empty

Every `read.json` answers `{"success": true, "data": {...}}`. The read sends another set of
fields than the list: an account's read has no balances, no `categoryDisplay`, `taxCode` or
`targetDisplay`; a person's, a journal entry's and an order's add structured lists and
derived names and drop some of the list's fields. A person's read leaves out every field
whose value is `null`, which the list sends as `null`.

Probe: 2026-10-23, `GET account/read.json`, `GET person/read.json`,
`GET journal/read.json` and `GET order/read.json`, beside the lists of the same day;
samples `tests/fixtures/account_read/by_id.json`, `tests/fixtures/person_read/by_id.json`,
`tests/fixtures/journal_read/by_id.json` and `tests/fixtures/order_read/by_id.json`.

### Timestamps and dates come without a zone

A timestamp comes as `YYYY-MM-DD HH:MM:SS.f` without a zone (`2026-10-23 07:06:40.0`), and a
date in the same form (`2025-12-31 23:59:59.0` for the end of a fiscal period). The
undocumented `lastEntryDate` comes with a time of day.

Probe: 2026-10-23, `GET fiscalperiod/list.json` and `GET journal/list.json`; samples
`tests/fixtures/fiscalperiod_list/default.json` and
`tests/fixtures/journal_list/fp2025_start_0_limit_5.json`.

### An API user signs its records with its key's first characters

A record an API user wrote names it in `createdBy` and `lastUpdatedBy` as `API:` and the
first four characters of its key. The recorder writes `API:REDACTED` in its place, so the
fixtures show where the tag stood.

Probe: 2026-10-23, `GET person/list.json` and `GET journal/list.json`, the records
`scripts/seed_demo.py` wrote that day; samples `tests/fixtures/person_list/default.json` and
`tests/fixtures/journal_list/fp2026_start_0_limit_5.json`, each tag scrubbed.

### Every answer carries `x-cashctrl-requests-left`

Every answer carries the header `x-cashctrl-requests-left`, `299` on each one recorded, a
401 included; its window and scope are not documented.

Probe: 2026-10-23 and 2026-11-21, `GET account/list.json` with a wrong key and
`GET report/element/download.pdf`; samples `tests/fixtures/account_list/wrong_key.json`,
the 401 of 2026-10-23, and `tests/fixtures/report_element_download_pdf/unknown_id.json`,
recorded 2026-11-21.

### A `.json` answer is `application/json;charset=utf-8`

Every answer of HTTP 200 of a `.json` operation recorded so far, a refusal included, is
`application/json;charset=utf-8`; the 401 of a wrong key is `text/plain;charset=utf-8`. `api/_download.py` reads a file operation's JSON answer as
a refusal.

Probe: 2026-10-23, `GET currency/list.json` and `GET account/read.json`, and `GET account/list.json`
with a wrong key; samples `tests/fixtures/currency_list/default.json`,
`tests/fixtures/account_read/missing_id.json` and `tests/fixtures/account_list/wrong_key.json`.

### Fields no table describes

The models type the fields no parameter table describes from the recorded answers, as each
model's docstring names them: the balances of `account/list.json` and its `accountClass`, a
tax code's components and rates, a journal entry's `rows` with their `fc*`, `ac*` and `dc*`
amounts, an order's items with `baseValue` and `taxCalcType`, a person's derived names, the
order categories with their statuses and book templates, the discovery lists' records and an
order document's fields. A field only ever seen as `null` or `[]` is kept as upstream sends
it.

Probe: 2026-10-23, 2026-10-24, 2026-10-27, 2026-10-28 and 2026-10-29, `GET account/list.json`,
`GET tax/list.json`, `GET journal/read.json`, `GET order/read.json`,
`GET order/category/list.json`, `GET person/category/list.json` and
`GET order/document/read.json`; samples
`tests/fixtures/account_list/only_active_finanz.json`, `tests/fixtures/tax_list/default.json`,
`tests/fixtures/journal_read/collective.json`, `tests/fixtures/order_read/by_id.json`,
`tests/fixtures/order_category_list/default.json`, recorded 2026-10-24,
`tests/fixtures/person_category_list/default.json` and
`tests/fixtures/order_document_read/by_id.json`, recorded 2026-10-28 UTC, 2026-10-29 CET.

### The default lists of a new organisation

The lists of an organisation's defaults answer every record at once: `account/category/list.json`
38 categories, CashCtrl's default chart, flat, each with its `parentId`;
`person/category/list.json` the four default categories and `person/title/list.json` the
three default titles; `order/category/list.json` without `type` the six default sales
categories, `total` equal to the records; and `location/list.json` the one location created
in the app. `account/category/tree.json` answers the same 38 categories nested, with display
fields alone and without the list's `accountClass` and `fullName`.

Probe: 2026-10-24 and 2026-10-27, `GET account/category/list.json`,
`GET person/category/list.json`, `GET person/title/list.json`, `GET order/category/list.json`
and `GET location/list.json`; samples `tests/fixtures/account_category_list/default.json`,
`tests/fixtures/person_category_list/default.json`,
`tests/fixtures/person_title_list/default.json`, `tests/fixtures/order_category_list/default.json`,
recorded 2026-10-24, and `tests/fixtures/location_list/default.json`. The tree, of
`GET account/category/tree.json` on 2026-10-27, kept no answer.

### An order's read sends `hash`

`order/read.json` sends `hash`, an undocumented text of 32 characters that may be the token
of a public link to the order's document; that was not verified. The recorder writes
`REDACTED` in its place.

Probe: 2026-10-23, `GET order/read.json?id=3`; sample `tests/fixtures/order_read/by_id.json`,
its `hash` scrubbed.

### A book entry is `MANUAL` or `GENERATED`

An order's book entry booked by hand has `type` `MANUAL`; the one its items book has
`GENERATED`. The entry's read names its order in `orderId`, but not the order's
description.

Probe: 2026-10-27 and 2026-11-17, `GET order/bookentry/list.json` and
`GET order/bookentry/read.json`; samples `tests/fixtures/order_bookentry_list/booked.json`,
`tests/fixtures/order_bookentry_read/generated.json` and
`tests/fixtures/order_bookentry_read/for_update.json`.

### The history

`history/list.json` lists a record's changes newest first, `changeType` `CREATE` and
`STATUS` in the recording, and `UPDATE` in a recording of the same day that a later one
overwrote. An order deleted a minute before has no history left: `total` 0.

Probe: 2026-10-27, `GET history/list.json`; samples
`tests/fixtures/history_list/order.json` and `tests/fixtures/history_list/deleted_order.json`.
The answer with `UPDATE`, of `GET history/list.json` on 2026-10-27, kept no answer.

### The report tree and a report's data

`report/tree.json` answers eight top-level nodes, each collection's elements nested under
`data`, and marks one collection `isSystem`, `Jahresbericht`. `report/element/data.json`
answers `{"total", "data", "properties"}`: `total` counts the top-level rows, `data` nests
the rows under upstream's camelCase names with amounts as JSON numbers, and the rows differ
by report type.

Probe: 2026-10-27, `GET report/tree.json` and `GET report/element/data.json?elementId=1&fiscalPeriod=2`;
samples `tests/fixtures/report_tree/default.json` and
`tests/fixtures/report_element_data/balance_fp2025.json`.

## Reads

### `fiscalperiod/read.json` sends `isCurrent` false

The read of a fiscal period, the current one read without `id` included, sends `current`
and `isCurrent` false and `lastEntryDate` `null`; `fiscalperiod/list.json` marks the
current period.

Probe: 2026-11-17, `GET fiscalperiod/read.json` and `GET fiscalperiod/read.json?id=1`;
samples `tests/fixtures/fiscalperiod_read/current.json` and
`tests/fixtures/fiscalperiod_read/by_id.json`.

### The journal and order lists answer for the current period

Without `fiscalPeriodId`, `journal/list.json` and `order/list.json` answer for the API
user's current fiscal period, server-side state that `fiscalperiod/switch.json` changes,
and `account/list.json` gives that period's balances. Without `type`, `order/list.json`
lists both types.

Probe: 2026-10-23, after the seed run of the same day left 2025 the current period, as
`GET fiscalperiod/list.json` marks it, and `GET account/list.json` without `fiscalPeriodId`;
samples `tests/fixtures/fiscalperiod_list/default.json`,
`tests/fixtures/account_list/filter_number_eq.json`, account 1020 with `endAmount` 101230,
its balance at the end of 2025, and `tests/fixtures/account_list/only_active_finanz.json`.
The journal's and the order's lists without `fiscalPeriodId`, and the order list without
`type`, of `GET journal/list.json` and `GET order/list.json` on 2026-10-23, kept no answer:
their recordings send both.

### The discovery lists

`account/costcenter/list.json` and `customfield/list.json` answered `total` 0 on the new
demo organisation, and one record each after `scripts/seed_demo.py --discovery` created
one.

Probe: 2026-10-27 and 2026-10-28, `GET account/costcenter/list.json` and
`GET customfield/list.json?type=PERSON`; samples
`tests/fixtures/account_costcenter_list/default.json` and
`tests/fixtures/customfield_list/person.json`, each with its one record. The empty answers,
of `GET account/costcenter/list.json` and `GET customfield/list.json?type=PERSON` on
2026-10-27, kept no answer.

## Refusals

### A refusal with one message is a top-level `errorMessage`

An operation documented to return "a success or error message" refuses with HTTP 200 and
`{"success": false, "errorMessage": "...", "data": null}`; a write with a field list sends
`message` `null` beside it, and a delete of an id that no longer exists sends its text under
`message`.

Probe: 2026-10-23 and 2026-10-24, `GET account/read.json` without `id`,
`POST journal/create.json` without `debitId` and `POST journal/delete.json` for a deleted
entry; samples `tests/fixtures/account_read/missing_id.json`,
`tests/fixtures/journal_create/rejected.json` and
`tests/fixtures/journal_delete/already_deleted.json`.

### An unknown id on a read is a refusal at HTTP 200

A `read.json` by an id no record has answers HTTP 200, `success` false and an
`errorMessage` that names the record: "This account does not exist.", "This book entry does
not exist.", "This fiscal period does not exist."; the text follows `lang`. A book entry's
read after its order's delete answers the same.

Probe: 2026-10-23 and 2026-11-17, `GET account/read.json?id=999999999`,
`GET journal/read.json?id=999999999`, `GET fiscalperiod/read.json?id=999999999` and
`GET order/bookentry/read.json`; samples `tests/fixtures/account_read/unknown_id.json`,
`tests/fixtures/journal_read/unknown_id.json`,
`tests/fixtures/fiscalperiod_read/unknown_id.json` and
`tests/fixtures/order_bookentry_read/order_deleted.json`. The currency's, of
`GET currency/read.json?id=999999999` on 2026-10-23, kept no answer.

### An unknown id on a file operation is HTTP 404

`order/document/read.pdf` by `ids`, and a report element's or collection's `download.pdf`
and `download.xlsx` by `elementId` or `collectionId`, answer an id no record has with
HTTP 404, `text/plain;charset=utf-8`, `CashCtrl - 404 Not Found`, where the existing
record's file is served. `_client.classify` raises `NotFoundError` there, the one 404 that
is no unknown endpoint.

Probe: 2026-10-29, 2026-11-17 and 2026-11-21, `GET order/document/read.pdf`,
`GET report/element/download.pdf`, `GET report/element/download.xlsx`,
`GET report/collection/download.pdf` and `GET report/collection/download.xlsx`. The order
document's 404 was seen in the live run of 2026-10-29, beside the existing order's PDF in
the same run, and the element's PDF and the collection's Excel file in the live run of
2026-11-17; samples, recorded 2026-11-21 for an id no record has, `999999999`:
`tests/fixtures/order_document_read_pdf/unknown_id.json`,
`tests/fixtures/report_element_download_pdf/unknown_id.json`,
`tests/fixtures/report_element_download_xlsx/unknown_id.json`,
`tests/fixtures/report_collection_download_pdf/unknown_id.json` and
`tests/fixtures/report_collection_download_xlsx/unknown_id.json`.

## Writes

### A create answers its `insertId`

`journal/create.json`, `person/create.json` and `order/create.json` answer `success`,
`message` and `insertId`, the new record's id as a JSON integer; an update answers the
record's own id. `fiscalperiod/create.json` answers `success` and `message` alone, and
`order/update_status.json` and `order/payment/create.json` answer `"Status changed"` and
`"Payment order created"` without an `insertId`.

Probe: 2026-10-23, 2026-10-24, 2026-10-27 and 2026-10-28, `POST journal/create.json`,
`POST journal/update.json`,
`POST person/create.json`, `POST order/create.json`, `POST order/update.json`,
`POST order/update_status.json` and `POST order/payment/create.json`; samples `tests/fixtures/journal_create/ok.json`, `tests/fixtures/journal_update/ok.json`,
`tests/fixtures/person_create/ok.json`,
`tests/fixtures/order_create/ok.json`, `tests/fixtures/order_update/ok.json`,
`tests/fixtures/order_update_status/ok.json` and
`tests/fixtures/order_payment_create/cash_pdf.json`. The fiscal period's, of
`POST fiscalperiod/create.json` in the seed run of 2026-10-23, kept no answer.

### An amount with a tax code is gross

A journal entry's `amount` with a `taxId` is the gross amount, VAT included, and an
order's items' `unitPrice` was read as gross, `baseValue` `GROSS`, although the components
of the two tax codes the seed run used, `UN1` and `VN1`, read `calcType` `NET`: the balance of account 1100 after seeding was `0.00` at
2025-12-31 and `4850.00` at 2026-09-30, the gross reading of the seeded entries exactly.

Probe: 2026-10-23, `GET account/balance` for account 1100 after the seed run,
`GET tax/list.json` and `GET order/read.json`; samples `tests/fixtures/tax_list/default.json`,
the components of `UN1` and `VN1`, and `tests/fixtures/order_read/by_id.json`, every item
`GROSS` and `NET`. The balances, of `GET account/balance` on 2026-10-23, kept no answer.

### Writes are form-encoded UTF-8

A write sent `application/x-www-form-urlencoded; charset=UTF-8` is read as UTF-8: the
company `Muster Büro AG`, written by the seed run's 65 writes, came back byte for byte.

Probe: 2026-10-23, `POST person/create.json` and `GET person/read.json`; sample
`tests/fixtures/person_list/default.json`, which lists the company as written.

### A person's read returns what was stored

`person/read.json` returns every stored documented field under its own name and leaves
the empty ones out. An address's `titleId` sent with a create is stored and read back with
`titleName`, a key the addresses tables do not document; a contact's `purpose` sent is not
stored and reads `null`. The insurance numbers of a person who is no insurance do not come
back. A create with all five roles is refused: "Invalid role combination." and "At least
one insurance contract must be set."

Probe: 2026-10-24, `POST person/create.json`, `GET person/read.json` and
`POST person/delete.json`, four requests of the live verification that day, a refused
create among them, kept no answer. The read the update tests start from is
`tests/fixtures/person_read/for_update.json`, recorded 2026-10-24.

### An update stores an order's items anew

`order/update.json` stores the items it is sent anew: each comes back with a new id.

Probe: 2026-10-27, `GET order/read.json` before and after `POST order/update.json`; samples
`tests/fixtures/order_read/for_update.json`, item 26, and
`tests/fixtures/order_read/after_update.json`, item 27.

### An order that books creates journal entries of its own

A purchase order in a status that books creates a journal entry of `type` `ORDER` with its
`orderId`; the list and the read of such an entry send `attachmentCount` `null`. The sales
invoices seeded in Draft book nothing.

Probe: 2026-10-26, `GET journal/list.json?onlyPurchase=true` and
`GET journal/read.json?id=50`; samples `tests/fixtures/journal_list/order_booked.json` and
`tests/fixtures/journal_read/order_booked.json`.

### Deleting an order deletes its book entries

`order/delete.json` deletes the order's book entries with it, those booked by hand
included, and the journal entries its items booked.

Probe: 2026-11-17, `POST order/delete.json` and `GET order/bookentry/read.json` for the
entry booked to the deleted order; sample
`tests/fixtures/order_bookentry_read/order_deleted.json`.

### A payment by pain.001 needs bank details, a cash payment none

`order/payment/create.json` with `type` `PAIN` refuses a date in the past and an order whose
sender or recipient holds no bank account or whose sender has no BIC; `CASH_PDF` for the
same order and the same past date is created. The order with a payment is deleted like any
other, "1 document deleted". After the order's delete,
`order/payment/download` answers HTTP 400 with `text/plain`: no file for the payment of a
deleted order.

Probe: 2026-10-28 UTC, 2026-10-29 CET, `POST order/payment/create.json` for the marked order
26 and `POST order/delete.json`; samples `tests/fixtures/order_payment_create/pain.json` and
`tests/fixtures/order_payment_create/cash_pdf.json`, and `tests/fixtures/order_delete/ok.json`,
an order's delete of 2026-10-27 with the same answer. The download after the delete, of
`GET order/payment/download` in the live run of 2026-10-29, kept no answer.

## A new organisation

### What a new organisation holds

A new organisation holds the fiscal period it was created with, CHF and the currencies EUR
and USD with CashCtrl's automatic rates (`createdBy` `SYSTEM`), two insurance persons
`SYSTEM` created, and the accounts 6950, 6960 and 6961; `location/list.json` lists no
location until one is created in the app, whatever the setup wizard asked. After
`fiscalperiod/create.json` with `type` `EARLIEST` created 2025, the API user's current
period was 2025, the period the run created.

Probe: 2026-10-23, `GET currency/list.json`, `GET person/list.json` and
`GET fiscalperiod/list.json` after the seed run; samples
`tests/fixtures/currency_list/default.json`, `tests/fixtures/person_list/default.json`,
`total` 12, and `tests/fixtures/fiscalperiod_list/default.json`, 2025 current. The empty
`GET location/list.json` and the three accounts of `GET account/list.json`, seen while the
organisation was set up in October 2026, before the seed run of 2026-10-23, kept no answer;
the one location created then is `tests/fixtures/location_list/default.json`, recorded
2026-10-27.

## Files

### A report file's type and name

A report element's PDF comes as `application/pdf;charset=UTF-8` named after the report and
its period (`Balance 2025.pdf`), its Excel file as the spreadsheet media type with
`charset=UTF-8` (`Balance 2025.xlsx`), for a fiscal period and for two dates alike;
collection 1 came as `Annual report 2025.pdf` and `.xlsx`.

Probe: 2026-11-17, `GET report/element/download.pdf`, `GET report/element/download.xlsx`,
`GET report/collection/download.pdf` and `GET report/collection/download.xlsx` for the
balance sheet and collection 1 of 2025, in the live run that day, kept no answer: a file is
not recorded.

### The annual report is the system collection's PDF

`report/collection/download_annualreport.pdf` answers the PDF of the one collection the
report tree marks `isSystem`, `Jahresbericht`, the same file as that collection's
`download.pdf` but for its creation time and document id. Without `fiscalPeriodId`, and for
an id no fiscal period has, it answers the API user's current period's report.

Probe: 2026-11-17, `GET report/collection/download_annualreport.pdf` beside
`GET report/collection/download.pdf?collectionId=1`, in the live run that day, kept no
answer: a file is not recorded.
