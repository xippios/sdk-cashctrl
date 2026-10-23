# The demo organisation

The family's fixtures and live tests for CashCtrl read one organisation, the demo
organisation, and nothing else. This document says why it holds synthetic books only, how
to create one, how to seed it with `scripts/seed_demo.py`, and exactly what the seeded
books contain.

## Why synthetic

This repository is public. Every fixture is a recorded answer of the demo organisation,
committed as it was recorded (credentials, host and e-mail addresses scrubbed); every live
test reads it. Whatever the demo organisation holds can therefore end up in a public
commit: names of customers and vendors, addresses, amounts, the audit trail.

The first demo organisation was a copy of real books (CashCtrl's Settings → Organizations
→ Copy, which the upstream introduction suggests for testing). It was retired: the
fixture recorder had to refuse every module but account, currency, fiscal period and tax,
and every non-zero amount, to keep real data out of the repository. A fresh organisation
with fictional books removes that reason. Everything in it is invented: the company
Muster Handel AG, its ten business partners (companies only, no natural persons), their
addresses on placeholder streets, their `.example` e-mail addresses (a reserved domain,
never delivered) and every amount.

The naming rule: every company name carries a placeholder marker as its first word
(Muster, Beispiel, Testfirma, Demo, Platzhalter, Probe, Fiktiv), the Swiss and German
convention for sample data, so that no name can pass for a company in the commercial
register. `tests/test_seed_demo.py` checks the rule against the data and this document.

## Creating the organisation

1. In CashCtrl, create a **new, empty** organisation, not a copy, and activate the PRO
   demo for it (the API is available to PRO organisations only,
   `docs/upstream/introduction.md`). Its name must contain `demo` in any case, for
   example `Muster Handel AG Demo`. Keep CashCtrl's defaults: the current fiscal period,
   the default Swiss chart of accounts, the default VAT codes and categories. Change no
   settings.
2. Enter only fictional data in the organisation creation wizard: a name like the one
   above and a placeholder address, nothing real. A new organisation has no location:
   `location/list.json` lists none until one is created under Settings → Locations,
   whatever the wizard asked (observed in October 2026). Create the main location (type
   `MAIN`) there before seeding, with fictional data only: a company name that contains
   `demo`, a placeholder address such as `Musterhof 1, 8001 Zürich`, no VAT UID, no
   IBAN, no logo. The seeder reads `location/list.json`, and that answer can feed
   fixtures, so whatever the location holds can end up in a public commit.
3. Check the company name of the main location: it must contain `demo` as well. The
   seeder reads the organisation's name there (`orgName` in `location/list.json`),
   because the documentation has no organisation read besides `domain/current/logo`
   (`docs/upstream/meta.md`). Without a location, guard 2 refuses.
4. Settings → Users & Roles → Add → Add API user (`docs/upstream/authentication.md`), with
   a role that may read locations, fiscal periods, accounts and their balances,
   currencies, tax codes, person and order categories, persons, the journal and orders,
   and may create currencies, fiscal periods, persons, journal entries and orders. After
   seeding, the role may be reduced to read-only; the write tools' live tests will need
   write rights again later.
5. Put the two variables into `~/github/sdk/.envrc` and run `direnv allow`:
   `CASHCTRL_DEMO_SUBDOMAIN` (the one label before `.cashctrl.com`) and
   `CASHCTRL_DEMO_API_KEY`. The subdomain is treated like the key: never in a file of
   this repository, a commit, a log line or a report. `demo` is reserved and is **never**
   an entry of `CASHCTRL_ORGS`.

## Seeding

Run both commands from the repository root of the sdk-cashctrl checkout. First the plan;
it makes no request and needs no variable:

```bash
uv run scripts/seed_demo.py            # same as --plan
```

Then the run, with the demo pair from direnv and `CASHCTRL_ORGS` removed from the
environment (the script never reads it, and nothing else should see it either):

```bash
direnv exec ~/github/sdk env -u CASHCTRL_ORGS uv run scripts/seed_demo.py --apply --yes
```

Before the first write, `--apply --yes` refuses with exit status 1, a message that shows
no value, and nothing written, unless

1. both variables are set and the subdomain is one DNS label;
2. `location/list.json` answers and the company name (`orgName`) of the main location
   contains `demo` in any case;
3. the organisation is empty: `journal/list.json` and `order/list.json` for `SALES` and
   `PURCHASE` in every fiscal period (the lists answer for the current period only unless
   `fiscalPeriodId` is given) report `total` 0, and `person/list.json` (the whole list,
   `onlyActive` left at its default, false) lists no person but the insurance records
   CashCtrl creates itself. A new organisation lists two of them, with `createdBy`
   `SYSTEM` and `isInsurance` true (observed in October 2026): they are expected, the
   guard tolerates them, and the person `total` after seeding includes them (12, not
   10). Every other person refuses, a `SYSTEM`-created one that is not an insurance
   included, so a copy with system-imported data still fails closed; the refusal says
   how many such persons there are. Persons beyond the records the list returns (a
   `total` above them) count as others; a person record without `createdBy`, or a list
   without a numeric `total`, refuses as unconfirmable. An organisation with data, such
   as a copy of real books, is refused; the script never deletes anything. If a fresh
   organisation lists any other record (a person or an entry from the wizard, for
   instance), the guard names the list and refuses as well: delete that record in
   CashCtrl, or start over with a new organisation;
4. `account/list.json` has every account number the plan uses, none of them inactive; the
   refusal names the missing or inactive numbers. The script creates no accounts.

The lookups the writes need are resolved before the first write as well, and refuse the
same way: a fiscal period covering the 2026 dates; one covering 2025, or an earliest
period that starts on 2026-01-01 (then `fiscalperiod/create.json` with `type=EARLIEST`
creates 2025); the tax codes `UN1` and `VN1` by `code` in `tax/list.json` (the refusal
lists the active codes); an order category per type, matched by name (the refusal lists
the categories). Person categories are matched by name too, and a role without a match
gets none. For each of the two tax codes the run prints the `calcType` of its components
(`NET` or `GROSS`, `docs/upstream/common.md`), from `tax/list.json` or, when the list
record has no components, from `tax/read.json`: whether a journal `amount` with a
`taxId` is net or gross is observed there, not assumed (see the assumptions below).

Then the script creates, in this order: the ten persons, the currencies
`currency/list.json` lacks, the 2025 fiscal period, the 48 journal entries (2025 first)
and the six orders, last, so that a refusal there leaves everything else seeded. The
persons come first because `person/create.json` has a mandatory field, so a body
upstream cannot read is refused rather than saved with defaults (every parameter of
`fiscalperiod/create.json` is optional). The first person, Muster Büro AG, carries an
umlaut: right after its create the run reads it back with `person/read.json` and compares
`company` with what it sent, byte for byte. On a mismatch it stops before any other
write, says that the backend garbled UTF-8 and shows both names; delete that person in
CashCtrl and rerun with `--multipart` (below).

Requests start at least 1.2 seconds apart (50 a minute, a margin under the 60 a minute
the package's client allows itself): about 90 requests, about two minutes. The run stops
at the first answer that is not HTTP 200 with `success: true`, and at a request that gets
no answer: it prints the status, upstream's `errorMessage`/`message`/`errors` or the
transport error, and which record failed, and sends no further request. Of a successful
create it shows the `insertId` only.

Writes are form-encoded with the charset declared, `Content-Type:
application/x-www-form-urlencoded; charset=UTF-8` (the introduction says the API accepts
form-encoded bodies; the upstream curl examples use multipart `-F`). Nested values
(`addresses`, `contacts`, `items`) are JSON strings as in the examples, dates are
`YYYY-MM-DD`, the key is the basic auth user name with an empty password, and the
User-Agent is the family's, `xippios-cashctrl/<version> (+https://github.com/xippios)`.

If upstream refuses the form-encoded writes, or garbles the umlaut, rerun by hand with

```bash
direnv exec ~/github/sdk env -u CASHCTRL_ORGS uv run scripts/seed_demo.py --apply --yes --multipart
```

which sends the same fields as `multipart/form-data`, as the curl examples do. The script
never switches encoding by itself: a second attempt after an ambiguous answer could
create a record twice. Before the rerun, delete what the first run created (the guard
refuses an organisation that is not empty), or start over with a new organisation.

At the end it prints the records created per resource, the `total` each list endpoint now
reports, the balance of account 1100 (debtors) at 2025-12-31 and 2026-09-30
(`account/balance`, `docs/upstream/account.md`), and the section "Observed write
semantics": the encoding used, the UTF-8 round trip, the `calcType` of `UN1` and `VN1`,
the two balances, the status codes per endpoint, the keys of a successful create answer
and the type of `insertId`, and the exact shape of any refusal, scrubbed. After a stop
during the writes, the records created and the section are printed as well (the totals
and the balances only after a complete run). The first run's section is recorded
below.

A run that stops halfway leaves a partly seeded organisation, which the script then
refuses as not empty. Either finish the rest by hand or delete the organisation and start
over with a fresh one; the script never deletes or repairs anything.

## The books

| | |
| --- | --- |
| Company | Muster Handel AG, Zürich (fictional), a small trading company for office furniture and supplies |
| Currency | CHF; fiscal year = calendar year |
| Fiscal periods | 2026 (the organisation's current one, as created) and 2025 (created by the seeder) |
| Chart of accounts, VAT codes | CashCtrl's defaults, unchanged |
| Records | 10 persons (4 vendors, 6 customers), 48 manual journal entries (12 in 2025, 36 in 2026, 3 of them collective), 6 orders |
| Writes | at most 67 (10 persons, 2 currencies, 1 fiscal period, 48 journal entries, 6 orders) |

The script does not name the organisation: its name is set by hand when it is created
(Creating the organisation, step 1).

### Currencies

| Code | Description | Rate to CHF |
| --- | --- | ---: |
| EUR | Euro | 0.95 |
| USD | US-Dollar | 0.88 |

Created only if `currency/list.json` lacks the code. A new organisation has both from the
start: the first run created neither (Observed write semantics, below). The rates are
fixed and synthetic, and `common.md` says CashCtrl ignores `rate` for the currencies it
supports (EUR and USD among them) and fetches its own. No journal entry or order uses a
foreign currency.

### Persons

| Role | Company | Address | Postcode, city | Canton | Language | E-mail |
| --- | --- | --- | --- | --- | --- | --- |
| vendor | Muster Büro AG | Beispielring 9 | 9000 St. Gallen | SG | DE | `info@muster-buero.example` |
| vendor | Beispiel Telecom AG | Musterweg 15 | 6300 Zug | ZG | DE | `info@beispiel-telecom.example` |
| vendor | Fiktiv Immobilien AG | Beispielstrasse 2 | 8004 Zürich | ZH | DE | `info@fiktiv-immobilien.example` |
| vendor | Probe Versicherung AG | Mustergasse 8 | 5000 Aarau | AG | DE | `info@probe-versicherung.example` |
| customer | Muster Consulting GmbH | Musterstrasse 1 | 8001 Zürich | ZH | DE | `info@muster-consulting.example` |
| customer | Beispiel Logistik AG | Beispielweg 12 | 4051 Basel | BS | DE | `info@beispiel-logistik.example` |
| customer | Testfirma Design GmbH | Musterplatz 3 | 3011 Bern | BE | DE | `info@testfirma-design.example` |
| customer | Demo Bau AG | Beispielgasse 7 | 6003 Luzern | LU | DE | `info@demo-bau.example` |
| customer | Platzhalter Software SA | Rue de l'Exemple 21 | 1003 Lausanne | VD | FR | `info@platzhalter-software.example` |
| customer | Probe Gastro GmbH | Musterallee 4 | 8400 Winterthur | ZH | DE | `info@probe-gastro.example` |

### Journal entries by month

All amounts in CHF. Invoices carry the VAT code `UN1`, purchases of goods `VN1`; every
other entry is booked without tax. Invoices and payments name the partner
(`associateId`) and carry the invoice number as `reference`.

| Month | Entries | What |
| --- | ---: | --- |
| January 2025 | 1 | share capital paid in (100'000.00) |
| February 2025 | 1 | invoice RE-2025-001 |
| March 2025 | 2 | payment RE-2025-001, rent (quarter) |
| April 2025 | 1 | purchase ER-2025-001 |
| May 2025 | 1 | invoice RE-2025-002 |
| June 2025 | 2 | payment RE-2025-002, rent (quarter) |
| July 2025 | 1 | payment ER-2025-001 |
| September 2025 | 1 | bank fees |
| October 2025 | 1 | invoice RE-2025-003 |
| December 2025 | 1 | collective: bank statement with payment RE-2025-003 and IT support |
| January 2026 | 4 | rent, invoice RE-2026-001, purchase ER-2026-001, telecom |
| February 2026 | 4 | rent, payment RE-2026-001, invoice RE-2026-002, telecom |
| March 2026 | 4 | rent, payment ER-2026-001, invoice RE-2026-003, bank fees |
| April 2026 | 4 | rent, collective: payments RE-2026-002 and RE-2026-003, purchase ER-2026-002, IT support |
| May 2026 | 4 | rent, invoices RE-2026-004 and RE-2026-005, telecom |
| June 2026 | 4 | rent, payment ER-2026-002, payment RE-2026-004, bank fees |
| July 2026 | 4 | rent, payment RE-2026-005, invoice RE-2026-006, telecom |
| August 2026 | 4 | rent, purchase ER-2026-003, IT support, telecom |
| September 2026 | 4 | rent, invoice RE-2026-007, collective: payment ER-2026-003 and telecom, bank fees |

At the end of September 2026, the invoices RE-2026-006 (Probe Gastro GmbH, 1'250.00) and
RE-2026-007 (Muster Consulting GmbH, 3'600.00) are open; every other invoice and purchase
is paid. Probe Versicherung AG has no bookings.

### Journal entries 2025

| Date | Debit | Credit | Amount (CHF) | Tax code | Partner | Reference | Title |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 2025-01-06 | 1020 | 2800 | 100'000.00 |  |  |  | Einzahlung Aktienkapital |
| 2025-02-03 | 1100 | 3200 | 4'800.00 | UN1 | Muster Consulting GmbH | RE-2025-001 | Rechnung RE-2025-001 Muster Consulting GmbH |
| 2025-03-05 | 1020 | 1100 | 4'800.00 |  | Muster Consulting GmbH | RE-2025-001 | Zahlung RE-2025-001 |
| 2025-03-31 | 6000 | 1020 | 7'200.00 |  | Fiktiv Immobilien AG |  | Miete 1. Quartal 2025 |
| 2025-04-14 | 4200 | 2000 | 6'400.00 | VN1 | Muster Büro AG | ER-2025-001 | Wareneinkauf ER-2025-001 Muster Büro AG |
| 2025-05-12 | 1100 | 3200 | 15'000.00 | UN1 | Demo Bau AG | RE-2025-002 | Rechnung RE-2025-002 Demo Bau AG |
| 2025-06-09 | 1020 | 1100 | 15'000.00 |  | Demo Bau AG | RE-2025-002 | Zahlung RE-2025-002 |
| 2025-06-30 | 6000 | 1020 | 7'200.00 |  | Fiktiv Immobilien AG |  | Miete 2. Quartal 2025 |
| 2025-07-15 | 2000 | 1020 | 6'400.00 |  | Muster Büro AG | ER-2025-001 | Zahlung ER-2025-001 |
| 2025-09-30 | 6900 | 1020 | 120.00 |  |  |  | Bankspesen Januar bis September 2025 |
| 2025-10-20 | 1100 | 3200 | 3'600.00 | UN1 | Beispiel Logistik AG | RE-2025-003 | Rechnung RE-2025-003 Beispiel Logistik AG |
| 2025-12-15 | collective | | 3'600.00 | | | | Bankauszug Dezember 2025 |
| | 1020 |  | 2'350.00 | |  | | Saldo Bankauszug Dezember 2025 |
| | 6500 |  | 1'250.00 | | Beispiel Telecom AG | | IT-Support 2025 |
| |  | 1100 | 3'600.00 | | Beispiel Logistik AG | | Zahlung RE-2025-003 |

### Journal entries 2026

| Date | Debit | Credit | Amount (CHF) | Tax code | Partner | Reference | Title |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 2026-01-05 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete Januar 2026 |
| 2026-01-12 | 1100 | 3200 | 4'800.00 | UN1 | Muster Consulting GmbH | RE-2026-001 | Rechnung RE-2026-001 Muster Consulting GmbH |
| 2026-01-20 | 4200 | 2000 | 3'200.00 | VN1 | Muster Büro AG | ER-2026-001 | Wareneinkauf ER-2026-001 Muster Büro AG |
| 2026-01-30 | 6500 | 1020 | 180.00 |  | Beispiel Telecom AG |  | Telefon und Internet Januar 2026 |
| 2026-02-05 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete Februar 2026 |
| 2026-02-10 | 1020 | 1100 | 4'800.00 |  | Muster Consulting GmbH | RE-2026-001 | Zahlung RE-2026-001 |
| 2026-02-16 | 1100 | 3200 | 7'500.00 | UN1 | Beispiel Logistik AG | RE-2026-002 | Rechnung RE-2026-002 Beispiel Logistik AG |
| 2026-02-27 | 6500 | 1020 | 180.00 |  | Beispiel Telecom AG |  | Telefon und Internet Februar 2026 |
| 2026-03-05 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete März 2026 |
| 2026-03-12 | 2000 | 1020 | 3'200.00 |  | Muster Büro AG | ER-2026-001 | Zahlung ER-2026-001 |
| 2026-03-18 | 1100 | 3200 | 2'500.00 | UN1 | Testfirma Design GmbH | RE-2026-003 | Rechnung RE-2026-003 Testfirma Design GmbH |
| 2026-03-31 | 6900 | 1020 | 45.00 |  |  |  | Bankspesen 1. Quartal 2026 |
| 2026-04-03 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete April 2026 |
| 2026-04-09 | collective | | 10'000.00 | | | | Sammelzahlung Debitoren April 2026 |
| | 1020 |  | 10'000.00 | |  | | Zahlungseingang |
| |  | 1100 | 7'500.00 | | Beispiel Logistik AG | | Zahlung RE-2026-002 |
| |  | 1100 | 2'500.00 | | Testfirma Design GmbH | | Zahlung RE-2026-003 |
| 2026-04-15 | 4200 | 2000 | 5'600.00 | VN1 | Muster Büro AG | ER-2026-002 | Wareneinkauf ER-2026-002 Muster Büro AG |
| 2026-04-30 | 6500 | 1020 | 650.00 |  | Beispiel Telecom AG |  | IT-Support April 2026 |
| 2026-05-05 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete Mai 2026 |
| 2026-05-19 | 1100 | 3200 | 15'000.00 | UN1 | Demo Bau AG | RE-2026-004 | Rechnung RE-2026-004 Demo Bau AG |
| 2026-05-26 | 1100 | 3200 | 6'200.00 | UN1 | Platzhalter Software SA | RE-2026-005 | Rechnung RE-2026-005 Platzhalter Software SA |
| 2026-05-29 | 6500 | 1020 | 180.00 |  | Beispiel Telecom AG |  | Telefon und Internet Mai 2026 |
| 2026-06-05 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete Juni 2026 |
| 2026-06-10 | 2000 | 1020 | 5'600.00 |  | Muster Büro AG | ER-2026-002 | Zahlung ER-2026-002 |
| 2026-06-22 | 1020 | 1100 | 15'000.00 |  | Demo Bau AG | RE-2026-004 | Zahlung RE-2026-004 |
| 2026-06-30 | 6900 | 1020 | 45.00 |  |  |  | Bankspesen 2. Quartal 2026 |
| 2026-07-03 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete Juli 2026 |
| 2026-07-14 | 1020 | 1100 | 6'200.00 |  | Platzhalter Software SA | RE-2026-005 | Zahlung RE-2026-005 |
| 2026-07-21 | 1100 | 3200 | 1'250.00 | UN1 | Probe Gastro GmbH | RE-2026-006 | Rechnung RE-2026-006 Probe Gastro GmbH |
| 2026-07-31 | 6500 | 1020 | 180.00 |  | Beispiel Telecom AG |  | Telefon und Internet Juli 2026 |
| 2026-08-05 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete August 2026 |
| 2026-08-18 | 4200 | 2000 | 2'400.00 | VN1 | Muster Büro AG | ER-2026-003 | Wareneinkauf ER-2026-003 Muster Büro AG |
| 2026-08-28 | 6500 | 1020 | 650.00 |  | Beispiel Telecom AG |  | IT-Support August 2026 |
| 2026-08-31 | 6500 | 1020 | 180.00 |  | Beispiel Telecom AG |  | Telefon und Internet August 2026 |
| 2026-09-04 | 6000 | 1020 | 2'400.00 |  | Fiktiv Immobilien AG |  | Miete September 2026 |
| 2026-09-15 | 1100 | 3200 | 3'600.00 | UN1 | Muster Consulting GmbH | RE-2026-007 | Rechnung RE-2026-007 Muster Consulting GmbH |
| 2026-09-22 | collective | | 2'580.00 | | | | Sammelzahlung Kreditoren September 2026 |
| | 2000 |  | 2'400.00 | | Muster Büro AG | | Zahlung ER-2026-003 |
| | 6500 |  | 180.00 | | Beispiel Telecom AG | | Telefon und Internet September 2026 |
| |  | 1020 | 2'580.00 | |  | | Zahlungsausgang |
| 2026-09-30 | 6900 | 1020 | 45.00 |  |  |  | Bankspesen 3. Quartal 2026 |

### Orders

Four sales invoices and two purchase orders, all in 2026 and in CHF, each to a person
above. The script sets `associateId`, `categoryId`, `date`, `nr`, `description`,
`language` (`DE`) and `items` (`accountId`, `name`, `description`, `quantity`,
`unitPrice`, `taxId`); it leaves `accountId` to the category, `statusId` empty (the first
status of the category), and no sequence number, rounding, due days or recurrence. Net
totals before VAT: RE-2026-101 2'050.00, RE-2026-102 3'700.00, RE-2026-103 7'750.00,
RE-2026-104 900.00, EK-2026-001 4'650.00, EK-2026-002 830.00.

The sales category is the active one named Invoice (Rechnung, Facture, Fattura) in
`order/category/list.json?type=SALES`; the purchase category is the active one named like
an invoice (also Lieferantenrechnung, Kreditorenrechnung, Eingangsrechnung, vendor or
supplier invoice), else like a purchase order (Bestellung, Commande, Ordine, order). The
names are compared in every language a localized name carries, in any case.

| Type | Number | Date | Partner | Description | Item | Quantity | Unit price (CHF) | Account | Tax code |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| SALES | RE-2026-101 | 2026-03-02 | Muster Consulting GmbH | Beratung Büroeinrichtung | Beratung (Planung Büroeinrichtung, Stundenansatz) | 12 | 150.00 | 3200 | UN1 |
| | | | | | Spesenpauschale (Anfahrt und Unterlagen) | 1 | 250.00 | 3200 | UN1 |
| SALES | RE-2026-102 | 2026-04-14 | Beispiel Logistik AG | Büromöbel Standort Basel | Büromöbel-Set Standard (Schreibtisch, Stuhl und Korpus) | 4 | 850.00 | 3200 | UN1 |
| | | | | | Lieferung und Montage (Pauschal) | 1 | 300.00 | 3200 | UN1 |
| SALES | RE-2026-103 | 2026-06-08 | Demo Bau AG | Einrichtung Baubüro | Bürostuhl Ergo (Ergonomischer Drehstuhl) | 10 | 420.00 | 3200 | UN1 |
| | | | | | Schreibtisch Basic (160 x 80 cm) | 5 | 680.00 | 3200 | UN1 |
| | | | | | Lieferung (Pauschal) | 1 | 150.00 | 3200 | UN1 |
| SALES | RE-2026-104 | 2026-09-07 | Probe Gastro GmbH | Büromaterial | Druckerpapier A4 (Karton mit 2500 Blatt) | 20 | 45.00 | 3200 | UN1 |
| PURCHASE | EK-2026-001 | 2026-02-02 | Muster Büro AG | Wareneinkauf Büromöbel | Bürostuhl Ergo (Ergonomischer Drehstuhl) | 10 | 260.00 | 4200 | VN1 |
| | | | | | Schreibtisch Basic (160 x 80 cm) | 5 | 410.00 | 4200 | VN1 |
| PURCHASE | EK-2026-002 | 2026-05-04 | Beispiel Telecom AG | Netzwerk Büro Zürich | Router Business (Router mit Firewall) | 1 | 480.00 | 6500 | VN1 |
| | | | | | Einrichtung Netzwerk (Pauschal) | 1 | 350.00 | 6500 | VN1 |

## Account numbers and other assumptions

The documentation snapshot names no account number, no default VAT code and no default
category; these are the assumptions the seeder makes, each checked at apply time before
the first write:

| Number | Used for | |
| --- | --- | --- |
| 1020 | bank | payments, fees, rent, the share capital |
| 1100 | debtors | sales invoices and customer payments |
| 2000 | creditors | purchases and vendor payments |
| 2800 | share capital | the payment of the share capital, January 2025 |
| 3200 | revenue from goods | sales invoices and sales order items |
| 4200 | purchases of goods | purchases and the purchase order to Muster Büro AG |
| 6000 | premises | rent |
| 6500 | administration | IT support, telecom and the purchase order to Beispiel Telecom AG |
| 6900 | financial expenses | bank fees |

- The numbers follow the Swiss SME chart of accounts (KMU-Kontenrahmen), which CashCtrl's
  default chart is assumed to follow. The snapshot does not confirm them; guard 4
  resolves each to its id through `account/list.json` and refuses, naming them, if one is
  missing or inactive. There is no opening-balance entry (the documentation says nothing
  about opening balances, so `9100` is not used); the books start with the payment of
  the share capital in 2025.
- Bank fees go to 6900, financial expenses (Finanzaufwand). CashCtrl's default chart has
  no bank-charges account: the first seeding attempt was refused by guard 4 for a
  missing 6940, the SME chart's bank charges, and the default chart's accounts from 6800
  to 6999 are 6800 depreciation, 6801 fixed asset disposals, 6900 financial expenses,
  6950 financial revenue, 6960 exchange differences and 6961 rounding differences
  (observed in October 2026). The other eight numbers are in the default chart.
- VAT codes `UN1` (VAT due on sales, 8.1 %) and `VN1` (input VAT, 8.1 %): not in the
  documentation; they are the system-created codes the retired demo organisation's
  `tax/list.json` showed. Looked up by `code`; missing ones refuse the run.
- Whether `amount` with a `taxId` on a manual journal entry is the gross or the net
  amount is not documented for the journal; the tax code's components carry a `calcType`
  of `NET` or `GROSS` (`docs/upstream/common.md`), which the run prints before the first
  write. The payments assume the invoice amount is what the customer pays (gross). If
  upstream reads it as net and adds the VAT, the debtors keep the VAT of each paid
  invoice. The run prints the balance of 1100 at both dates; the human compares it with
  what the books imply under each reading, at 8.1 %:

  | Balance of 1100 at | amount read as gross | amount read as net, VAT added |
  | --- | ---: | ---: |
  | 2025-12-31 | 0.00 | 1'895.40 |
  | 2026-09-30 | 4'850.00 | 8'158.85 for 2026 alone, 10'054.25 with 2025 carried forward |

  Gross leaves the two open invoices, RE-2026-006 and RE-2026-007, as the only balance.
  The first run matched the gross reading exactly (Observed write semantics, below).
  Whether the balance at 2026-09-30 includes the 2025 closing balance depends on how
  CashCtrl opens a period, which the documentation does not say; under the gross
  reading it does not matter. If the sales orders booked journal entries (journal total
  for 2026 above 36), their totals are in 1100 as well (14'400.00 net, 15'566.40 with
  VAT added) and have to be subtracted before comparing.
- `journal/create.json` documents `amount`, `debitId` and `creditId` as mandatory but
  ignored when `items` is set; collective entries send `items` only, as the documented
  curl example does.
- `associateId` is typed TEXT and accepts a name to create a person on the fly; the
  seeder always sends the `insertId` of a person it created. Inside `items` it is a JSON
  number, as the documented order example sends the TEXT-typed `unitId`.
- `order/create.json`: `nr` becomes mandatory when neither the request nor the category
  sets a sequence number; the seeder sets `nr` always (`RE-2026-101`, `EK-2026-001`). The
  categories are matched by name, as above; the first status of a category may or may
  not book journal entries, which the totals after the run show.
- Person categories: matched by name (Customers, Kunden, Clients, Clienti; Vendors,
  Suppliers, Lieferanten, Fournisseurs, Fornitori); persons without a match get no
  category. Persons are created with `isCustomer` or `isVendor`, one `MAIN` address in
  `CHE` and one `EMAIL_WORK` contact; no phone numbers, no VAT numbers, no bank details.
- `fiscalperiod/create.json` with `type=EARLIEST` creates the calendar year before the
  earliest existing one; the seeder uses it only when the earliest period starts on
  2026-01-01, and checks afterwards that a period covers 2025.
- Nothing else is created or changed: no accounts, tax codes, locations, settings,
  salary, files, inventory or custom fields.

## Observed write semantics (filled by the first run)

The first complete `--apply --yes` run, on 2026-10-23 against the new demo organisation,
printed the following; the balances and totals are quoted as printed.

- Encoding of the writes: form-encoded, `application/x-www-form-urlencoded;
  charset=UTF-8`. `--multipart` was not needed.
- UTF-8 round trip: `person/read.json` answered the company `Muster Büro AG` byte for
  byte.
- `calcType` of the components of `UN1` and `VN1`: `NET` for both, read from
  `tax/list.json` (no `tax/read.json` needed). `common.md` defines `calcType` as the
  calculation basis of the tax, not as how a journal `amount` is read; the balances below
  show that reading.
- Status codes: HTTP 200 for every request, 88 in all. The 65 writes were
  `person/create.json` x10, `fiscalperiod/create.json` x1, `journal/create.json` x48 and
  `order/create.json` x6. The 23 reads were the guards and lookups, the read-back, the
  fiscal period re-read and the summary.
- Create answers: `person/create.json`, `journal/create.json` and `order/create.json`
  answer with the keys `insertId`, `message` and `success`, `insertId` a JSON integer.
  `fiscalperiod/create.json` answers with `message` and `success` only, without
  `insertId`; the seeder finds the new period by reading `fiscalperiod/list.json` again.
  Every create answer carries a `message`; the seeder never prints its text.
- Refusals: none.
- Currencies: the new organisation already had EUR and USD, so the run sent no
  `currency/create.json` request.
- Fiscal period 2025: the new organisation had 2026 only. `fiscalperiod/create.json` with
  `type=EARLIEST` created 2025, and `fiscalperiod/list.json` then listed a period
  covering the 2025 dates.
- Whether order creation booked journal entries: `journal/list.json` reports 38 entries
  for 2026, two more than the 36 manual entries. The balance of 1100 holds no sales order
  amount, so the four sales invoices did not book to the debtors. Which records the two
  extra entries are was not read; the two purchase orders are the likeliest source, not
  verified.
- Balance of 1100 (`account/balance`): `0.00` at 2025-12-31 and `4850.00` at 2026-09-30,
  exactly the gross reading in the table above. The `amount` of a manual journal entry
  with a `taxId` is the gross amount, VAT included, although the tax codes' `calcType` is
  `NET`.
- The `total` each list endpoint reported after seeding: `person/list.json` 12 (the ten
  seeded persons and CashCtrl's two system insurance persons); `journal/list.json` 12 for
  2025 and 38 for 2026; `order/list.json` 4 `SALES` and 2 `PURCHASE` for 2026;
  `currency/list.json` 3; `fiscalperiod/list.json` 2.
- `x-cashctrl-requests-left`: the seeder does not record response headers. The read-only
  freshness check before the run saw the header on every answer (8 of 8, name only).
