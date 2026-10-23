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
never delivered) and every amount. Any resemblance to a real company is coincidental.

## Creating the organisation

1. In CashCtrl, create a **new, empty** organisation, not a copy, on the PRO Demo plan (the
   API is available to PRO organisations only, `docs/upstream/introduction.md`). Its name
   must contain `demo` in any case, for example `Muster Handel AG Demo`. Keep CashCtrl's
   defaults: the current fiscal period, the default Swiss chart of accounts, the default
   VAT codes and categories. Change no settings.
2. Check the company name of the main location (Settings → Locations): it must contain
   `demo` as well. The seeder reads the organisation's name there (`orgName` in
   `location/list.json`), because the documentation has no organisation read besides
   `domain/current/logo` (`docs/upstream/meta.md`). If CashCtrl did not copy the
   organisation's name into the main location, set it to the same name.
3. Settings → Users & Roles → Add → Add API user (`docs/upstream/authentication.md`), with
   a role that may read locations, fiscal periods, accounts, currencies, tax codes, person
   and order categories, persons, the journal and orders, and may create currencies,
   fiscal periods, persons, journal entries and orders. After seeding, the role may be
   reduced to read-only; the write tools' live tests will need write rights again later.
4. Put the two variables into `~/github/sdk/.envrc` and run `direnv allow`:
   `CASHCTRL_DEMO_SUBDOMAIN` (the one label before `.cashctrl.com`) and
   `CASHCTRL_DEMO_API_KEY`. The subdomain is treated like the key: never in a file of
   this repository, a commit, a log line or a report. `demo` is reserved and is **never**
   an entry of `CASHCTRL_ORGS`.

## Seeding

First the plan; it makes no request and needs no variable:

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
3. the organisation is empty: `person/list.json`, `journal/list.json` for every fiscal
   period (the list shows the current period only unless `fiscalPeriodId` is given) and
   `order/list.json` for `SALES` and `PURCHASE` all report `total` 0. An organisation with
   data, such as a copy of real books, is refused; the script never deletes anything;
4. `account/list.json` has every account number the plan uses, none of them inactive; the
   refusal names the missing or inactive numbers. The script creates no accounts.

The lookups the writes need are resolved before the first write as well, and refuse the
same way: a fiscal period covering the 2026 dates; one covering 2025, or an earliest
period that starts on 2026-01-01 (then `fiscalperiod/create.json` with `type=EARLIEST`
creates 2025); the tax codes `UN1` and `VN1` by `code` in `tax/list.json` (the refusal
lists the active codes); an order category per type, matched by name (the refusal lists
the categories). Person categories are matched by name too, and a role without a match
gets none.

Then the script creates, in this order: the currencies `currency/list.json` lacks, the
2025 fiscal period, the ten persons, the 48 journal entries (2025 first) and the six
orders, last, so that a refusal there leaves everything else seeded. It sends at most one
request per second (about 90 requests, a minute and a half), and stops at the first
answer that is not HTTP 200 with `success: true`: it prints the status, upstream's
`errorMessage`/`message`/`errors` and which record failed, and sends no further request.
Of a successful create it shows the `insertId` only.

Writes are form-encoded (`application/x-www-form-urlencoded`, as the introduction says;
the upstream curl examples use multipart `-F`), nested values (`addresses`, `contacts`,
`items`) are JSON strings as in the examples, dates are `YYYY-MM-DD`, the key is the basic
auth user name with an empty password, and the User-Agent is `xippios-cashctrl-seed`.

At the end it prints the records created per resource, the `total` each list endpoint now
reports, and the section "Observed write semantics": the status codes per endpoint, the
keys of a successful create answer and the type of `insertId`, and the exact shape of
any refusal, scrubbed. Copy that section into the placeholder below.

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
| Records | 10 persons, 48 manual journal entries (12 in 2025, 36 in 2026, 3 of them collective), 6 orders |
| Writes | at most 67 (2 currencies, 1 fiscal period, 10 persons, 48 journal entries, 6 orders) |

The script does not name the organisation: its name is set by hand when it is created
(Creating the organisation, step 1).

### Currencies

| Code | Description | Rate to CHF |
| --- | --- | ---: |
| EUR | Euro | 0.95 |
| USD | US-Dollar | 0.88 |

Created only if `currency/list.json` lacks the code; the retired copy had EUR and USD from
the start, so a fresh organisation probably has them and nothing is created. The rates are
fixed and synthetic, and `common.md` says CashCtrl ignores `rate` for the currencies it
supports (EUR and USD among them) and fetches its own. No journal entry or order uses a
foreign currency.

### Persons

| Role | Company | Address | Postcode, city | Canton | Language | E-mail |
| --- | --- | --- | --- | --- | --- | --- |
| customer | Alpha Consulting GmbH | Musterstrasse 1 | 8001 Zürich | ZH | DE | `info@alpha-consulting.example` |
| customer | Beta Logistik AG | Beispielweg 12 | 4051 Basel | BS | DE | `info@beta-logistik.example` |
| customer | Gamma Design Studio | Musterplatz 3 | 3011 Bern | BE | DE | `info@gamma-design-studio.example` |
| customer | Delta Bau AG | Beispielgasse 7 | 6003 Luzern | LU | DE | `info@delta-bau.example` |
| customer | Epsilon Software SA | Rue de l'Exemple 21 | 1003 Lausanne | VD | FR | `info@epsilon-software.example` |
| customer | Zeta Gastro GmbH | Musterallee 4 | 8400 Winterthur | ZH | DE | `info@zeta-gastro.example` |
| vendor | Omega Büro AG | Beispielring 9 | 9000 St. Gallen | SG | DE | `info@omega-buero.example` |
| vendor | Sigma Telecom AG | Musterweg 15 | 6300 Zug | ZG | DE | `info@sigma-telecom.example` |
| vendor | Kappa Immobilien AG | Beispielstrasse 2 | 8004 Zürich | ZH | DE | `info@kappa-immobilien.example` |
| vendor | Theta Versicherung AG | Mustergasse 8 | 5000 Aarau | AG | DE | `info@theta-versicherung.example` |

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

At the end of September 2026, the invoices RE-2026-006 (Zeta Gastro GmbH, 1'250.00) and
RE-2026-007 (Alpha Consulting GmbH, 3'600.00) are open; every other invoice and purchase
is paid. Theta Versicherung AG has no bookings.

### Journal entries 2025

| Date | Debit | Credit | Amount (CHF) | Tax code | Partner | Reference | Title |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 2025-01-06 | 1020 | 2800 | 100'000.00 |  |  |  | Einzahlung Aktienkapital |
| 2025-02-03 | 1100 | 3200 | 4'800.00 | UN1 | Alpha Consulting GmbH | RE-2025-001 | Rechnung RE-2025-001 Alpha Consulting GmbH |
| 2025-03-05 | 1020 | 1100 | 4'800.00 |  | Alpha Consulting GmbH | RE-2025-001 | Zahlung RE-2025-001 |
| 2025-03-31 | 6000 | 1020 | 7'200.00 |  | Kappa Immobilien AG |  | Miete 1. Quartal 2025 |
| 2025-04-14 | 4200 | 2000 | 6'400.00 | VN1 | Omega Büro AG | ER-2025-001 | Wareneinkauf ER-2025-001 Omega Büro AG |
| 2025-05-12 | 1100 | 3200 | 15'000.00 | UN1 | Delta Bau AG | RE-2025-002 | Rechnung RE-2025-002 Delta Bau AG |
| 2025-06-09 | 1020 | 1100 | 15'000.00 |  | Delta Bau AG | RE-2025-002 | Zahlung RE-2025-002 |
| 2025-06-30 | 6000 | 1020 | 7'200.00 |  | Kappa Immobilien AG |  | Miete 2. Quartal 2025 |
| 2025-07-15 | 2000 | 1020 | 6'400.00 |  | Omega Büro AG | ER-2025-001 | Zahlung ER-2025-001 |
| 2025-09-30 | 6940 | 1020 | 120.00 |  |  |  | Bankspesen Januar bis September 2025 |
| 2025-10-20 | 1100 | 3200 | 3'600.00 | UN1 | Beta Logistik AG | RE-2025-003 | Rechnung RE-2025-003 Beta Logistik AG |
| 2025-12-15 | collective | | 3'600.00 | | | | Bankauszug Dezember 2025 |
| | 1020 |  | 2'350.00 | |  | | Saldo Bankauszug Dezember 2025 |
| | 6500 |  | 1'250.00 | | Sigma Telecom AG | | IT-Support 2025 |
| |  | 1100 | 3'600.00 | | Beta Logistik AG | | Zahlung RE-2025-003 |

### Journal entries 2026

| Date | Debit | Credit | Amount (CHF) | Tax code | Partner | Reference | Title |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 2026-01-05 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete Januar 2026 |
| 2026-01-12 | 1100 | 3200 | 4'800.00 | UN1 | Alpha Consulting GmbH | RE-2026-001 | Rechnung RE-2026-001 Alpha Consulting GmbH |
| 2026-01-20 | 4200 | 2000 | 3'200.00 | VN1 | Omega Büro AG | ER-2026-001 | Wareneinkauf ER-2026-001 Omega Büro AG |
| 2026-01-30 | 6500 | 1020 | 180.00 |  | Sigma Telecom AG |  | Telefon und Internet Januar 2026 |
| 2026-02-05 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete Februar 2026 |
| 2026-02-10 | 1020 | 1100 | 4'800.00 |  | Alpha Consulting GmbH | RE-2026-001 | Zahlung RE-2026-001 |
| 2026-02-16 | 1100 | 3200 | 7'500.00 | UN1 | Beta Logistik AG | RE-2026-002 | Rechnung RE-2026-002 Beta Logistik AG |
| 2026-02-27 | 6500 | 1020 | 180.00 |  | Sigma Telecom AG |  | Telefon und Internet Februar 2026 |
| 2026-03-05 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete März 2026 |
| 2026-03-12 | 2000 | 1020 | 3'200.00 |  | Omega Büro AG | ER-2026-001 | Zahlung ER-2026-001 |
| 2026-03-18 | 1100 | 3200 | 2'500.00 | UN1 | Gamma Design Studio | RE-2026-003 | Rechnung RE-2026-003 Gamma Design Studio |
| 2026-03-31 | 6940 | 1020 | 45.00 |  |  |  | Bankspesen 1. Quartal 2026 |
| 2026-04-03 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete April 2026 |
| 2026-04-09 | collective | | 10'000.00 | | | | Sammelzahlung Debitoren April 2026 |
| | 1020 |  | 10'000.00 | |  | | Zahlungseingang |
| |  | 1100 | 7'500.00 | | Beta Logistik AG | | Zahlung RE-2026-002 |
| |  | 1100 | 2'500.00 | | Gamma Design Studio | | Zahlung RE-2026-003 |
| 2026-04-15 | 4200 | 2000 | 5'600.00 | VN1 | Omega Büro AG | ER-2026-002 | Wareneinkauf ER-2026-002 Omega Büro AG |
| 2026-04-30 | 6500 | 1020 | 650.00 |  | Sigma Telecom AG |  | IT-Support April 2026 |
| 2026-05-05 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete Mai 2026 |
| 2026-05-19 | 1100 | 3200 | 15'000.00 | UN1 | Delta Bau AG | RE-2026-004 | Rechnung RE-2026-004 Delta Bau AG |
| 2026-05-26 | 1100 | 3200 | 6'200.00 | UN1 | Epsilon Software SA | RE-2026-005 | Rechnung RE-2026-005 Epsilon Software SA |
| 2026-05-29 | 6500 | 1020 | 180.00 |  | Sigma Telecom AG |  | Telefon und Internet Mai 2026 |
| 2026-06-05 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete Juni 2026 |
| 2026-06-10 | 2000 | 1020 | 5'600.00 |  | Omega Büro AG | ER-2026-002 | Zahlung ER-2026-002 |
| 2026-06-22 | 1020 | 1100 | 15'000.00 |  | Delta Bau AG | RE-2026-004 | Zahlung RE-2026-004 |
| 2026-06-30 | 6940 | 1020 | 45.00 |  |  |  | Bankspesen 2. Quartal 2026 |
| 2026-07-03 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete Juli 2026 |
| 2026-07-14 | 1020 | 1100 | 6'200.00 |  | Epsilon Software SA | RE-2026-005 | Zahlung RE-2026-005 |
| 2026-07-21 | 1100 | 3200 | 1'250.00 | UN1 | Zeta Gastro GmbH | RE-2026-006 | Rechnung RE-2026-006 Zeta Gastro GmbH |
| 2026-07-31 | 6500 | 1020 | 180.00 |  | Sigma Telecom AG |  | Telefon und Internet Juli 2026 |
| 2026-08-05 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete August 2026 |
| 2026-08-18 | 4200 | 2000 | 2'400.00 | VN1 | Omega Büro AG | ER-2026-003 | Wareneinkauf ER-2026-003 Omega Büro AG |
| 2026-08-28 | 6500 | 1020 | 650.00 |  | Sigma Telecom AG |  | IT-Support August 2026 |
| 2026-08-31 | 6500 | 1020 | 180.00 |  | Sigma Telecom AG |  | Telefon und Internet August 2026 |
| 2026-09-04 | 6000 | 1020 | 2'400.00 |  | Kappa Immobilien AG |  | Miete September 2026 |
| 2026-09-15 | 1100 | 3200 | 3'600.00 | UN1 | Alpha Consulting GmbH | RE-2026-007 | Rechnung RE-2026-007 Alpha Consulting GmbH |
| 2026-09-22 | collective | | 2'580.00 | | | | Sammelzahlung Kreditoren September 2026 |
| | 2000 |  | 2'400.00 | | Omega Büro AG | | Zahlung ER-2026-003 |
| | 6500 |  | 180.00 | | Sigma Telecom AG | | Telefon und Internet September 2026 |
| |  | 1020 | 2'580.00 | |  | | Zahlungsausgang |
| 2026-09-30 | 6940 | 1020 | 45.00 |  |  |  | Bankspesen 3. Quartal 2026 |

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
| SALES | RE-2026-101 | 2026-03-02 | Alpha Consulting GmbH | Beratung Büroeinrichtung | Beratung (Planung Büroeinrichtung, Stundenansatz) | 12 | 150.00 | 3200 | UN1 |
| | | | | | Spesenpauschale (Anfahrt und Unterlagen) | 1 | 250.00 | 3200 | UN1 |
| SALES | RE-2026-102 | 2026-04-14 | Beta Logistik AG | Büromöbel Standort Basel | Büromöbel-Set Standard (Schreibtisch, Stuhl und Korpus) | 4 | 850.00 | 3200 | UN1 |
| | | | | | Lieferung und Montage (Pauschal) | 1 | 300.00 | 3200 | UN1 |
| SALES | RE-2026-103 | 2026-06-08 | Delta Bau AG | Einrichtung Baubüro | Bürostuhl Ergo (Ergonomischer Drehstuhl) | 10 | 420.00 | 3200 | UN1 |
| | | | | | Schreibtisch Basic (160 x 80 cm) | 5 | 680.00 | 3200 | UN1 |
| | | | | | Lieferung (Pauschal) | 1 | 150.00 | 3200 | UN1 |
| SALES | RE-2026-104 | 2026-09-07 | Zeta Gastro GmbH | Büromaterial | Druckerpapier A4 (Karton mit 2500 Blatt) | 20 | 45.00 | 3200 | UN1 |
| PURCHASE | EK-2026-001 | 2026-02-02 | Omega Büro AG | Wareneinkauf Büromöbel | Bürostuhl Ergo (Ergonomischer Drehstuhl) | 10 | 260.00 | 4200 | VN1 |
| | | | | | Schreibtisch Basic (160 x 80 cm) | 5 | 410.00 | 4200 | VN1 |
| PURCHASE | EK-2026-002 | 2026-05-04 | Sigma Telecom AG | Netzwerk Büro Zürich | Router Business (Router mit Firewall) | 1 | 480.00 | 6500 | VN1 |
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
| 4200 | purchases of goods | purchases and the purchase order to Omega Büro AG |
| 6000 | premises | rent |
| 6500 | administration | IT support, telecom and the purchase order to Sigma Telecom AG |
| 6940 | bank charges | bank fees |

- The numbers follow the Swiss SME chart of accounts (KMU-Kontenrahmen), which CashCtrl's
  default chart is assumed to follow. The snapshot does not confirm them; guard 4
  resolves each to its id through `account/list.json` and refuses, naming them, if one is
  missing or inactive. There is no opening-balance entry (the documentation says nothing
  about opening balances, so `9100` is not used); the books start with the payment of
  the share capital in 2025.
- VAT codes `UN1` (VAT due on sales, 8.1 %) and `VN1` (input VAT, 8.1 %): not in the
  documentation; they are the system-created codes the retired demo organisation's
  `tax/list.json` showed. Looked up by `code`; missing ones refuse the run.
- Whether `amount` with a `taxId` on a manual journal entry is the gross or the net
  amount is not documented. The payments assume the invoice amount is what the customer
  pays (gross). If upstream reads it as net, the debtors keep the VAT of each paid
  invoice; the first run checks the balance of 1100.
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

To be filled from the section the first `--apply --yes` run prints, with its date:

- Status codes per endpoint: _pending_
- Keys of a successful create answer (`success`, `message`, `insertId`, ...) and the type
  of `insertId`, per create endpoint: _pending_
- The exact shape of a refusal, if one occurred: _pending_
- Whether order creation booked journal entries (journal totals above 36 for 2026):
  _pending_
- Whether `amount` with a `taxId` was read as gross (balance of 1100 after the run):
  _pending_
- The `total` each list endpoint reported after seeding: _pending_
