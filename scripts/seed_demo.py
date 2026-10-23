"""Seed a fresh, empty CashCtrl demo organisation with small synthetic books.

The family's fixtures and live tests read the demo organisation, and the repository is
public, so the demo organisation holds fictional books only: Muster Handel AG, a trading
company in Zürich keeping its books in CHF; four vendors and six customers, all of them
companies whose name starts with a placeholder marker (``PLACEHOLDER_MARKERS``); 48
manual journal entries in 2025 and 2026; four sales invoices and two purchase orders.
``docs/demo-org.md`` describes the books, how to create the organisation and how to run
this script, from the repository root of the sdk-cashctrl checkout::

    uv run scripts/seed_demo.py                 # --plan: the plan, no network at all
    direnv exec ~/github/sdk env -u CASHCTRL_ORGS uv run scripts/seed_demo.py --apply --yes

The script reads ``CASHCTRL_DEMO_SUBDOMAIN`` and ``CASHCTRL_DEMO_API_KEY`` and nothing
else, never ``CASHCTRL_ORGS``, and prints neither value: upstream text it shows (error
messages, category names, tax codes, ``calcType``, balances, an ``insertId`` that is not
a number, a transport error) has the key, the subdomain and every e-mail address outside
``.example`` replaced first, and it never shows the body of a successful create beyond
its ``insertId``. It never deletes anything.

``--apply --yes`` refuses, with exit status 1 and before the first write, unless

1. both variables are set and the subdomain is one DNS label;
2. ``location/list.json`` answers and the company name (``orgName``) of the main
   location contains ``demo`` in any case. The documentation has no organisation read
   besides ``domain/current/logo``, so the main location stands for the organisation;
3. the organisation is empty: ``person/list.json``, and ``journal/list.json`` and
   ``order/list.json`` (SALES and PURCHASE) for every fiscal period, report ``total`` 0;
4. ``account/list.json`` has every account number the plan uses, none of them inactive;

and unless the lookups the writes need resolve: a fiscal period covering the 2026 dates;
one covering 2025, or an earliest period that starts on 2026-01-01 so that
``fiscalperiod/create.json`` with ``type=EARLIEST`` creates 2025; the tax codes by
``code``, whose components' ``calcType`` (NET or GROSS) it prints; and an invoice
category per order type. Person categories are optional.

Then it creates, in this order, the persons, the currencies ``currency/list.json``
lacks, the 2025 fiscal period, the journal entries (2025, then 2026) and the orders,
starting requests at least 1.2 seconds apart. The first person, Muster Büro AG, is read
back with ``person/read.json``; unless its ``company`` is what was sent, byte for byte,
the run stops there: the backend garbled UTF-8. It stops as well at the first answer
that is not HTTP 200 with ``success: true``, naming the record; no request follows.
Writes are form-encoded with ``charset=UTF-8`` declared, or ``multipart/form-data`` with
``--multipart``, a switch for a manual rerun and never an automatic fallback; nested
values (``addresses``, ``contacts``, ``items``) are JSON strings; dates are
``YYYY-MM-DD``; the key is the basic-auth user name with an empty password. The summary
lists what was created, the ``total`` each list now reports, the balance of 1100 at
2025-12-31 and 2026-09-30 and the observed write semantics, which the first run copies
into ``docs/demo-org.md``.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal

import httpx

from xippios.cashctrl import __version__

SUBDOMAIN_ENV = "CASHCTRL_DEMO_SUBDOMAIN"
API_KEY_ENV = "CASHCTRL_DEMO_API_KEY"  # pragma: allowlist secret (a variable name, not a key)
USER_AGENT = f"xippios-cashctrl/{__version__} (+https://github.com/xippios)"
"""The family's one User-Agent (sdk-core conventions, section 6). It has no slot for a
marker, so the seeder sends it unchanged."""
PACE_SECONDS = 1.2
"""The least time between the starts of two requests: 50 a minute, a margin under the 60 a
minute the package's client allows itself."""
FORM_CONTENT_TYPE = "application/x-www-form-urlencoded; charset=UTF-8"
"""The content type of every form-encoded write, the charset declared explicitly."""
MULTIPART = "multipart/form-data"
"""The writes' encoding with ``--multipart``, as the upstream curl examples send (``-F``)."""
TIMEOUT_SECONDS = 30.0
DEMO_MARK = "demo"
"""What the organisation's name must contain, in any case."""

_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_EMAIL = re.compile(r"[\w.%+-]+(?:@|%40|&#0*64;?|&#[xX]0*40;?|&commat;)[\w-]+(?:\.[\w-]+)+")
_LOCALIZED = re.compile(r"<([a-z]{2})>(.*?)</\1>", re.DOTALL)
_SHOWN_CHARS = 600
"""The most characters of an upstream refusal body shown, after scrubbing."""
_SHOWN_VALUE_CHARS = 80
"""The most characters of one upstream value shown (an ``insertId`` that is not a number, a
balance), after scrubbing."""

Role = Literal["customer", "vendor"]
OrderType = Literal["SALES", "PURCHASE"]
TaxKind = Literal["sales", "purchase"]


# --- The synthetic books --------------------------------------------------------------


@dataclass(frozen=True)
class Currency:
    """A currency created unless ``currency/list.json`` already has its code."""

    code: str
    description: str
    rate: Decimal


_LEGAL_FORMS = (" GmbH", " AG", " SA")
_TRANSLITERATION = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "é": "e", "è": "e"})


@dataclass(frozen=True)
class Person:
    """A fictional company, customer or vendor, with one main address and one e-mail."""

    key: str
    company: str
    role: Role
    address: str
    postcode: str
    city: str
    canton: str
    language: str = "DE"

    @property
    def email(self) -> str:
        """``info@<company without legal form>.example``, e.g. ``info@muster-buero.example``.

        The reserved ``.example`` domain is never delivered.
        """
        name = self.company
        for form in _LEGAL_FORMS:
            name = name.removesuffix(form)
        slug = "-".join(name.lower().translate(_TRANSLITERATION).split())
        return f"info@{slug}.example"


@dataclass(frozen=True)
class Line:
    """One item of a collective journal entry: an account with a debit or a credit."""

    account: str
    debit: Decimal | None = None
    credit: Decimal | None = None
    associate: str | None = None
    description: str | None = None


_REFERENCE = re.compile(r"\b(?:RE|ER)-\d{4}-\d{3}\b")


@dataclass(frozen=True)
class Entry:
    """A manual journal entry, simple (debit, credit, amount) or collective (lines)."""

    day: date
    title: str
    debit: str | None = None
    credit: str | None = None
    amount: Decimal | None = None
    tax: TaxKind | None = None
    associate: str | None = None
    lines: tuple[Line, ...] = ()

    @property
    def reference(self) -> str | None:
        """The invoice number in the title (``RE-2026-001``, ``ER-2026-001``), if any."""
        match = _REFERENCE.search(self.title)
        return match.group(0) if match else None

    @property
    def total(self) -> Decimal:
        """The amount of a simple entry, the debit side of a collective one."""
        if self.lines:
            return sum((line.debit or Decimal(0) for line in self.lines), Decimal(0))
        return self.amount or Decimal(0)


@dataclass(frozen=True)
class Item:
    """One order item: name, description, quantity, unit price and the account number."""

    name: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    account: str


@dataclass(frozen=True)
class Order:
    """A sales invoice or a purchase order to one person, dated in 2026."""

    type: OrderType
    nr: str
    day: date
    associate: str
    description: str
    items: tuple[Item, ...]

    @property
    def net(self) -> Decimal:
        """The sum of quantity times unit price over the items, before tax."""
        return sum((item.quantity * item.unit_price for item in self.items), Decimal(0))


COMPANY = "Muster Handel AG"
"""The fictional company the books belong to; the organisation itself is named by hand."""

CURRENCIES = (
    Currency("EUR", "Euro", Decimal("0.95")),
    Currency("USD", "US-Dollar", Decimal("0.88")),
)

PLACEHOLDER_MARKERS = ("Muster", "Beispiel", "Testfirma", "Demo", "Platzhalter", "Probe", "Fiktiv")
"""Every company name starts with one of these words, so none can pass for a real company."""

PERSONS = (
    Person("buero", "Muster Büro AG", "vendor", "Beispielring 9", "9000", "St. Gallen", "SG"),
    Person("telecom", "Beispiel Telecom AG", "vendor", "Musterweg 15", "6300", "Zug", "ZG"),
    Person(
        "immobilien", "Fiktiv Immobilien AG", "vendor", "Beispielstrasse 2", "8004", "Zürich", "ZH"
    ),
    Person(
        "versicherung", "Probe Versicherung AG", "vendor", "Mustergasse 8", "5000", "Aarau", "AG"
    ),
    Person(
        "consulting",
        "Muster Consulting GmbH",
        "customer",
        "Musterstrasse 1",
        "8001",
        "Zürich",
        "ZH",
    ),
    Person("logistik", "Beispiel Logistik AG", "customer", "Beispielweg 12", "4051", "Basel", "BS"),
    Person("design", "Testfirma Design GmbH", "customer", "Musterplatz 3", "3011", "Bern", "BE"),
    Person("bau", "Demo Bau AG", "customer", "Beispielgasse 7", "6003", "Luzern", "LU"),
    Person(
        "software",
        "Platzhalter Software SA",
        "customer",
        "Rue de l'Exemple 21",
        "1003",
        "Lausanne",
        "VD",
        language="FR",
    ),
    Person("gastro", "Probe Gastro GmbH", "customer", "Musterallee 4", "8400", "Winterthur", "ZH"),
)
"""The business partners, vendors first; the first one carries an umlaut."""
_COMPANIES = {person.key: person.company for person in PERSONS}

BANK, DEBTORS, CREDITORS, SHARE_CAPITAL = "1020", "1100", "2000", "2800"
REVENUE, PURCHASES, RENT, ADMIN, BANK_FEES = "3200", "4200", "6000", "6500", "6940"


def _entry(
    day: str,
    debit: str,
    credit: str,
    amount: str,
    title: str,
    tax: TaxKind | None = None,
    who: str | None = None,
) -> Entry:
    return Entry(
        day=date.fromisoformat(day),
        title=title,
        debit=debit,
        credit=credit,
        amount=Decimal(amount),
        tax=tax,
        associate=who,
    )


def _invoice(day: str, nr: str, amount: str, who: str) -> Entry:
    """A sales invoice: debtors to revenue, VAT due."""
    return _entry(day, DEBTORS, REVENUE, amount, f"Rechnung {nr} {_COMPANIES[who]}", "sales", who)


def _payment(day: str, nr: str, amount: str, who: str) -> Entry:
    """A customer's payment: bank to debtors."""
    return _entry(day, BANK, DEBTORS, amount, f"Zahlung {nr}", None, who)


def _purchase(day: str, nr: str, amount: str, who: str) -> Entry:
    """A purchase of goods: purchases to creditors, input VAT."""
    title = f"Wareneinkauf {nr} {_COMPANIES[who]}"
    return _entry(day, PURCHASES, CREDITORS, amount, title, "purchase", who)


def _vendor_payment(day: str, nr: str, amount: str, who: str) -> Entry:
    """A payment to a vendor: creditors to bank."""
    return _entry(day, CREDITORS, BANK, amount, f"Zahlung {nr}", None, who)


def _rent(day: str, period: str, amount: str) -> Entry:
    """Rent paid to the landlord, Fiktiv Immobilien AG."""
    return _entry(day, RENT, BANK, amount, f"Miete {period}", None, "immobilien")


def _expense(day: str, title: str, amount: str) -> Entry:
    """IT and telecom paid to Beispiel Telecom AG."""
    return _entry(day, ADMIN, BANK, amount, title, None, "telecom")


def _fees(day: str, period: str, amount: str) -> Entry:
    """Bank fees."""
    return _entry(day, BANK_FEES, BANK, amount, f"Bankspesen {period}")


def _collective(day: str, title: str, *lines: Line) -> Entry:
    return Entry(day=date.fromisoformat(day), title=title, lines=lines)


def _debit(account: str, amount: str, who: str | None, description: str) -> Line:
    return Line(account, debit=Decimal(amount), associate=who, description=description)


def _credit(account: str, amount: str, who: str | None, description: str) -> Line:
    return Line(account, credit=Decimal(amount), associate=who, description=description)


def _order(order_type: OrderType, nr: str, day: str, who: str, title: str, *items: Item) -> Order:
    return Order(order_type, nr, date.fromisoformat(day), who, title, items)


def _item(name: str, description: str, quantity: str, unit_price: str, account: str) -> Item:
    return Item(name, description, Decimal(quantity), Decimal(unit_price), account)


ENTRIES_2025 = (
    _entry("2025-01-06", BANK, SHARE_CAPITAL, "100000.00", "Einzahlung Aktienkapital"),
    _invoice("2025-02-03", "RE-2025-001", "4800.00", "consulting"),
    _payment("2025-03-05", "RE-2025-001", "4800.00", "consulting"),
    _rent("2025-03-31", "1. Quartal 2025", "7200.00"),
    _purchase("2025-04-14", "ER-2025-001", "6400.00", "buero"),
    _invoice("2025-05-12", "RE-2025-002", "15000.00", "bau"),
    _payment("2025-06-09", "RE-2025-002", "15000.00", "bau"),
    _rent("2025-06-30", "2. Quartal 2025", "7200.00"),
    _vendor_payment("2025-07-15", "ER-2025-001", "6400.00", "buero"),
    _fees("2025-09-30", "Januar bis September 2025", "120.00"),
    _invoice("2025-10-20", "RE-2025-003", "3600.00", "logistik"),
    _collective(
        "2025-12-15",
        "Bankauszug Dezember 2025",
        _debit(BANK, "2350.00", None, "Saldo Bankauszug Dezember 2025"),
        _debit(ADMIN, "1250.00", "telecom", "IT-Support 2025"),
        _credit(DEBTORS, "3600.00", "logistik", "Zahlung RE-2025-003"),
    ),
)

ENTRIES_2026 = (
    _rent("2026-01-05", "Januar 2026", "2400.00"),
    _invoice("2026-01-12", "RE-2026-001", "4800.00", "consulting"),
    _purchase("2026-01-20", "ER-2026-001", "3200.00", "buero"),
    _expense("2026-01-30", "Telefon und Internet Januar 2026", "180.00"),
    _rent("2026-02-05", "Februar 2026", "2400.00"),
    _payment("2026-02-10", "RE-2026-001", "4800.00", "consulting"),
    _invoice("2026-02-16", "RE-2026-002", "7500.00", "logistik"),
    _expense("2026-02-27", "Telefon und Internet Februar 2026", "180.00"),
    _rent("2026-03-05", "März 2026", "2400.00"),
    _vendor_payment("2026-03-12", "ER-2026-001", "3200.00", "buero"),
    _invoice("2026-03-18", "RE-2026-003", "2500.00", "design"),
    _fees("2026-03-31", "1. Quartal 2026", "45.00"),
    _rent("2026-04-03", "April 2026", "2400.00"),
    _collective(
        "2026-04-09",
        "Sammelzahlung Debitoren April 2026",
        _debit(BANK, "10000.00", None, "Zahlungseingang"),
        _credit(DEBTORS, "7500.00", "logistik", "Zahlung RE-2026-002"),
        _credit(DEBTORS, "2500.00", "design", "Zahlung RE-2026-003"),
    ),
    _purchase("2026-04-15", "ER-2026-002", "5600.00", "buero"),
    _expense("2026-04-30", "IT-Support April 2026", "650.00"),
    _rent("2026-05-05", "Mai 2026", "2400.00"),
    _invoice("2026-05-19", "RE-2026-004", "15000.00", "bau"),
    _invoice("2026-05-26", "RE-2026-005", "6200.00", "software"),
    _expense("2026-05-29", "Telefon und Internet Mai 2026", "180.00"),
    _rent("2026-06-05", "Juni 2026", "2400.00"),
    _vendor_payment("2026-06-10", "ER-2026-002", "5600.00", "buero"),
    _payment("2026-06-22", "RE-2026-004", "15000.00", "bau"),
    _fees("2026-06-30", "2. Quartal 2026", "45.00"),
    _rent("2026-07-03", "Juli 2026", "2400.00"),
    _payment("2026-07-14", "RE-2026-005", "6200.00", "software"),
    _invoice("2026-07-21", "RE-2026-006", "1250.00", "gastro"),
    _expense("2026-07-31", "Telefon und Internet Juli 2026", "180.00"),
    _rent("2026-08-05", "August 2026", "2400.00"),
    _purchase("2026-08-18", "ER-2026-003", "2400.00", "buero"),
    _expense("2026-08-28", "IT-Support August 2026", "650.00"),
    _expense("2026-08-31", "Telefon und Internet August 2026", "180.00"),
    _rent("2026-09-04", "September 2026", "2400.00"),
    _invoice("2026-09-15", "RE-2026-007", "3600.00", "consulting"),
    _collective(
        "2026-09-22",
        "Sammelzahlung Kreditoren September 2026",
        _debit(CREDITORS, "2400.00", "buero", "Zahlung ER-2026-003"),
        _debit(ADMIN, "180.00", "telecom", "Telefon und Internet September 2026"),
        _credit(BANK, "2580.00", None, "Zahlungsausgang"),
    ),
    _fees("2026-09-30", "3. Quartal 2026", "45.00"),
)

ORDERS = (
    _order(
        "SALES",
        "RE-2026-101",
        "2026-03-02",
        "consulting",
        "Beratung Büroeinrichtung",
        _item("Beratung", "Planung Büroeinrichtung, Stundenansatz", "12", "150.00", REVENUE),
        _item("Spesenpauschale", "Anfahrt und Unterlagen", "1", "250.00", REVENUE),
    ),
    _order(
        "SALES",
        "RE-2026-102",
        "2026-04-14",
        "logistik",
        "Büromöbel Standort Basel",
        _item("Büromöbel-Set Standard", "Schreibtisch, Stuhl und Korpus", "4", "850.00", REVENUE),
        _item("Lieferung und Montage", "Pauschal", "1", "300.00", REVENUE),
    ),
    _order(
        "SALES",
        "RE-2026-103",
        "2026-06-08",
        "bau",
        "Einrichtung Baubüro",
        _item("Bürostuhl Ergo", "Ergonomischer Drehstuhl", "10", "420.00", REVENUE),
        _item("Schreibtisch Basic", "160 x 80 cm", "5", "680.00", REVENUE),
        _item("Lieferung", "Pauschal", "1", "150.00", REVENUE),
    ),
    _order(
        "SALES",
        "RE-2026-104",
        "2026-09-07",
        "gastro",
        "Büromaterial",
        _item("Druckerpapier A4", "Karton mit 2500 Blatt", "20", "45.00", REVENUE),
    ),
    _order(
        "PURCHASE",
        "EK-2026-001",
        "2026-02-02",
        "buero",
        "Wareneinkauf Büromöbel",
        _item("Bürostuhl Ergo", "Ergonomischer Drehstuhl", "10", "260.00", PURCHASES),
        _item("Schreibtisch Basic", "160 x 80 cm", "5", "410.00", PURCHASES),
    ),
    _order(
        "PURCHASE",
        "EK-2026-002",
        "2026-05-04",
        "telecom",
        "Netzwerk Büro Zürich",
        _item("Router Business", "Router mit Firewall", "1", "480.00", ADMIN),
        _item("Einrichtung Netzwerk", "Pauschal", "1", "350.00", ADMIN),
    ),
)

TAX_CODES: dict[TaxKind, str] = {"sales": "UN1", "purchase": "VN1"}
"""The tax codes looked up by ``code`` in ``tax/list.json``: VAT due on sales, input VAT.

Not in the documentation; observed as the system-created codes at 8.1 % in the retired
demo organisation's ``tax/list.json``. The run refuses, listing the codes there are,
before any write if either is missing.
"""
ORDER_TAX: dict[OrderType, TaxKind] = {"SALES": "sales", "PURCHASE": "purchase"}

PERSON_CATEGORY_NAMES: dict[Role, frozenset[str]] = {
    "customer": frozenset(
        {"customers", "customer", "kunden", "kunde", "clients", "client", "clienti", "cliente"}
    ),
    "vendor": frozenset(
        {
            "vendors",
            "vendor",
            "suppliers",
            "supplier",
            "lieferanten",
            "lieferant",
            "fournisseurs",
            "fournisseur",
            "fornitori",
            "fornitore",
        }
    ),
}
"""Names (any language, any case) of the person category per role; none fits, none is set."""

_INVOICE_NAMES = frozenset(
    {"invoice", "invoices", "rechnung", "rechnungen", "facture", "factures", "fattura", "fatture"}
)
ORDER_CATEGORY_NAMES: dict[OrderType, tuple[frozenset[str], ...]] = {
    "SALES": (_INVOICE_NAMES,),
    "PURCHASE": (
        _INVOICE_NAMES
        | {
            "lieferantenrechnung",
            "lieferantenrechnungen",
            "kreditorenrechnung",
            "kreditorenrechnungen",
            "eingangsrechnung",
            "eingangsrechnungen",
            "vendor invoice",
            "vendor invoices",
            "supplier invoice",
            "supplier invoices",
            "purchase invoice",
            "purchase invoices",
        },
        frozenset(
            {
                "purchase order",
                "purchase orders",
                "order",
                "orders",
                "bestellung",
                "bestellungen",
                "commande",
                "commandes",
                "ordine",
                "ordini",
            }
        ),
    ),
}
"""Names of the order category per type, in order of preference; none fits, the run refuses."""


def all_entries() -> tuple[Entry, ...]:
    """The journal entries in booking order: 2025, then 2026."""
    return ENTRIES_2025 + ENTRIES_2026


def account_numbers() -> list[str]:
    """Every account number the plan uses, sorted."""
    numbers: set[str] = set()
    for entry in all_entries():
        numbers.update(n for n in (entry.debit, entry.credit) if n)
        numbers.update(line.account for line in entry.lines)
    numbers.update(item.account for order in ORDERS for item in order.items)
    return sorted(numbers)


def max_writes() -> int:
    """The most write calls a run makes: every currency and the 2025 period included."""
    return len(CURRENCIES) + 1 + len(PERSONS) + len(all_entries()) + len(ORDERS)


# --- Output and scrubbing ---------------------------------------------------------------


def say(text: str = "", *, err: bool = False) -> None:
    """Print one line to stdout, or to stderr for a refusal or a failure."""
    print(text, file=sys.stderr if err else sys.stdout, flush=True)


class Refused(Exception):
    """A guard refused before the first write; the message shows no value."""


class Failed(Exception):
    """A request failed or upstream refused; the run stops and sends nothing more."""


@dataclass(frozen=True, repr=False)
class Credentials:
    """The demo pair; ``repr`` hides both values."""

    subdomain: str
    key: str

    def __repr__(self) -> str:
        return "Credentials(<hidden>)"


def read_credentials(environ: Mapping[str, str]) -> Credentials:
    """The demo subdomain and key from ``environ``; refuses when unset or malformed."""
    subdomain = environ.get(SUBDOMAIN_ENV, "").strip().lower()
    key = environ.get(API_KEY_ENV, "").strip()
    missing = [
        name for name, value in ((SUBDOMAIN_ENV, subdomain), (API_KEY_ENV, key)) if not value
    ]
    if missing:
        raise Refused(f"{' and '.join(missing)} not set: export the demo pair (docs/demo-org.md)")
    if not _LABEL.fullmatch(subdomain):
        raise Refused(
            f"{SUBDOMAIN_ENV} is not one DNS label: give the one label before .cashctrl.com"
        )
    return Credentials(subdomain=subdomain, key=key)


def _hide_email(match: re.Match[str]) -> str:
    address = match.group(0)
    return address if address.lower().endswith(".example") else "<e-mail>"


class Scrubber:
    """Replaces the key, the subdomain and foreign e-mail addresses in upstream text."""

    def __init__(self, credentials: Credentials) -> None:
        token = base64.b64encode(f"{credentials.key}:".encode()).decode("ascii")
        self._secrets = [credentials.key, token]
        self._subdomain = re.compile(re.escape(credentials.subdomain), re.IGNORECASE)

    def __call__(self, text: str) -> str:
        """``text`` with the key, the subdomain and foreign e-mail addresses replaced."""
        for secret in self._secrets:
            text = text.replace(secret, "<key>")
        text = _EMAIL.sub(_hide_email, text)
        return self._subdomain.sub("<subdomain>", text)


# --- Requests ----------------------------------------------------------------------------


class Pacer:
    """Keeps the starts of two requests at least ``interval`` seconds apart."""

    def __init__(
        self,
        interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.interval = interval
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def wait(self) -> None:
        """Sleep until the next request may start."""
        if self._last is not None:
            delay = self._last + self.interval - self._clock()
            if delay > 0:
                self._sleep(delay)
        self._last = self._clock()


@dataclass
class Observed:
    """What the writes looked like: statuses, answer keys, ``insertId`` types, refusals."""

    statuses: Counter[tuple[str, str, int]] = field(default_factory=Counter)
    answer_keys: dict[str, set[str]] = field(default_factory=dict)
    insert_id_types: dict[str, set[str]] = field(default_factory=dict)
    refusals: list[str] = field(default_factory=list)
    encoding: str = FORM_CONTENT_TYPE
    utf8: str = "not checked: no person was created"
    calc_types: dict[str, str] = field(default_factory=dict)
    balances: dict[str, str] = field(default_factory=dict)

    def lines(self) -> list[str]:
        """The section "Observed write semantics", one line per finding."""
        out = [
            "Observed write semantics",
            f"  writes sent as: {self.encoding}",
            f"  UTF-8 round trip: {self.utf8}",
        ]
        for code, shown in self.calc_types.items():
            out.append(f"  tax code {code}, components calcType {shown}")
        for day, shown in self.balances.items():
            out.append(f"  account {DEBTORS} balance at {day}: {shown}")
        for (method, path, status), count in sorted(self.statuses.items()):
            out.append(f"  {method} {path}: HTTP {status} x{count}")
        for path in sorted(self.answer_keys):
            keys = ", ".join(sorted(self.answer_keys[path]))
            types = ", ".join(sorted(self.insert_id_types.get(path, set()))) or "absent"
            out.append(f"  {path} success answer keys: {keys}; insertId type: {types}")
        out.extend(f"  refusal: {refusal}" for refusal in self.refusals)
        if not self.refusals:
            out.append("  refusals: none")
        return out


def _shorten(shown: str) -> str:
    return shown if len(shown) <= _SHOWN_VALUE_CHARS else shown[:_SHOWN_VALUE_CHARS] + " ..."


def _json_or_none(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


class Session:
    """The paced, scrubbed requests of one run against the demo organisation."""

    def __init__(
        self,
        client: httpx.Client,
        scrub: Scrubber,
        pacer: Pacer,
        observed: Observed,
        *,
        multipart: bool = False,
    ) -> None:
        self.client = client
        self.scrub = scrub
        self.pacer = pacer
        self.observed = observed
        self.multipart = multipart  # chosen by hand for a rerun, never as a fallback
        observed.encoding = MULTIPART if multipart else FORM_CONTENT_TYPE

    def _send(
        self,
        method: str,
        path: str,
        what: str,
        params: Mapping[str, str] | None = None,
        form: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        self.pacer.wait()
        try:
            if form is None:
                response = self.client.request(method, path, params=params)
            elif self.multipart:
                fields = {name: (None, value) for name, value in form.items()}
                response = self.client.request(method, path, files=fields)
            else:
                response = self.client.request(
                    method, path, data=form, headers={"Content-Type": FORM_CONTENT_TYPE}
                )
        except httpx.HTTPError as error:
            reason = self.scrub(f"{type(error).__name__}: {error}")
            raise Failed(f"{what}: {method} {path} sent no answer ({reason})") from None
        self.observed.statuses[(method, path, response.status_code)] += 1
        return response

    def _upstream_message(self, body: Any) -> str:
        """``errorMessage``, ``message`` and ``errors`` of a refusal, scrubbed."""
        if not isinstance(body, dict):
            return ""
        parts = []
        for name in ("errorMessage", "message"):
            if isinstance(body.get(name), str) and body[name].strip():
                parts.append(f"{name}: {body[name]}")
        errors = body.get("errors")
        if isinstance(errors, list):
            for error in errors:
                if isinstance(error, dict):
                    parts.append(f"field {error.get('field')!r}: {error.get('message')}")
                else:
                    parts.append(f"error: {error}")
        return self.scrub("; ".join(parts))

    def _refusal_shape(self, method: str, path: str, response: httpx.Response) -> str:
        body = _json_or_none(response)
        kind = self.scrub(response.headers.get("content-type", "no content type"))
        if body is None:
            return f"{method} {path}: HTTP {response.status_code}, {kind}, body not JSON"
        shown = self.scrub(json.dumps(body, ensure_ascii=False, sort_keys=True))
        if len(shown) > _SHOWN_CHARS:
            shown = shown[:_SHOWN_CHARS] + " ..."
        return f"{method} {path}: HTTP {response.status_code}, {kind}, {shown}"

    def read(self, path: str, what: str, params: Mapping[str, str] | None = None) -> Any:
        """GET ``path``; HTTP 200 with a JSON body that is not ``success: false``."""
        response = self._send("GET", path, what, params=params)
        body = _json_or_none(response)
        if response.status_code != 200 or body is None:
            message = self._upstream_message(body)
            raise Failed(
                f"{what}: GET {path} answered HTTP {response.status_code}"
                + ("" if body is not None else ", not JSON")
                + (f" ({message})" if message else "")
            )
        if isinstance(body, dict) and body.get("success") is False:
            raise Failed(
                f"{what}: GET {path} answered success: false ({self._upstream_message(body)})"
            )
        return body

    def create(self, path: str, form: Mapping[str, str], what: str) -> dict[str, Any]:
        """POST ``form`` to ``path``; HTTP 200 with ``success: true`` or ``Failed``."""
        response = self._send("POST", path, what, form=form)
        body = _json_or_none(response)
        if (
            response.status_code != 200
            or not isinstance(body, dict)
            or body.get("success") is not True
        ):
            self.observed.refusals.append(self._refusal_shape("POST", path, response))
            message = self._upstream_message(body)
            raise Failed(
                f"{what}: POST {path} answered HTTP {response.status_code}"
                + ("" if isinstance(body, dict) else ", not a JSON object")
                + (
                    f", success: {json.dumps(body.get('success'))}"
                    if isinstance(body, dict)
                    else ""
                )
                + (f" ({message})" if message else "")
            )
        self.observed.answer_keys.setdefault(path, set()).update(
            self.scrub(str(key)) for key in body
        )
        insert_id = body.get("insertId")
        kind = "absent" if insert_id is None else type(insert_id).__name__
        self.observed.insert_id_types.setdefault(path, set()).add(kind)
        return body

    def shown_id(self, body: Mapping[str, Any]) -> str:
        """The ``insertId`` of a create answer as printed: a number, else scrubbed JSON."""
        value = body.get("insertId")
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        return _shorten(self.scrub(json.dumps(value, ensure_ascii=False)))

    def read_text(self, path: str, what: str, params: Mapping[str, str]) -> str:
        """GET ``path``, whose answer need not be JSON; HTTP 200, shown scrubbed and short."""
        response = self._send("GET", path, what, params=params)
        body = _json_or_none(response)
        refused = isinstance(body, dict) and body.get("success") is False
        if response.status_code != 200 or refused:
            message = self._upstream_message(body)
            raise Failed(
                f"{what}: GET {path} answered HTTP {response.status_code}"
                + (", success: false" if refused else "")
                + (f" ({message})" if message else "")
            )
        return _shorten(self.scrub(response.text.strip())) or "(empty)"


# --- Reading upstream answers --------------------------------------------------------


def records(body: Any, path: str) -> list[dict[str, Any]]:
    """The records of a list answer: ``data`` of an object, or a bare array."""
    data = body.get("data") if isinstance(body, dict) else body
    if not isinstance(data, list) or not all(isinstance(record, dict) for record in data):
        raise Failed(f"{path}: the answer holds no list of records under data")
    return data


def total_of(body: Any) -> int | None:
    """``total`` of a list answer, or ``None`` when it is missing or not a whole number."""
    value = body.get("total") if isinstance(body, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def texts(value: Any) -> list[str]:
    """The language variants of a localized value (``<values><de>..</de>``), else the text."""
    if not isinstance(value, str):
        return []
    found = [match.group(2) for match in _LOCALIZED.finditer(value)]
    return found or [value]


def names_of(record: Mapping[str, Any]) -> set[str]:
    """Every name a category record carries, case-folded, in every language."""
    names: set[str] = set()
    for key in ("name", "nameSingular", "namePlural", "text"):
        names.update(text.strip().casefold() for text in texts(record.get(key)))
    return names - {""}


def _id(record: Mapping[str, Any], path: str) -> int:
    value = record.get("id")
    if isinstance(value, bool) or not isinstance(value, int):
        raise Failed(f"{path}: a record without a numeric id")
    return value


def _day(value: Any) -> date | None:
    """The date of ``2026-01-01`` or ``2026-01-01 00:00:00.0``, else ``None``."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _inactive(record: Mapping[str, Any]) -> bool:
    return record.get("isInactive") is True


def _record(body: Any) -> Any:
    """The record of a read answer: ``data`` when it is an object, else the answer itself."""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def calc_types(components: Any) -> list[str] | None:
    """The ``calcType`` of each tax code component, from a list of objects or its JSON text."""
    if isinstance(components, str):
        try:
            components = json.loads(components)
        except ValueError:
            return None
    if not isinstance(components, list) or not components:
        return None
    return [
        c["calcType"] if isinstance(c, dict) and isinstance(c.get("calcType"), str) else "(none)"
        for c in components
    ]


# --- Guards and lookups ---------------------------------------------------------------


@dataclass(frozen=True)
class Period:
    """A fiscal period: its id and the dates it covers."""

    id: int
    start: date
    end: date

    def covers(self, first: date, last: date) -> bool:
        """Whether the period covers every date from ``first`` to ``last``."""
        return self.start <= first and last <= self.end


@dataclass
class Context:
    """Everything the writes need, resolved before the first one."""

    accounts: dict[str, int]
    taxes: dict[TaxKind, int]
    person_categories: dict[Role, int]
    order_categories: dict[OrderType, int]
    missing_currencies: list[Currency]
    period_2026: int
    period_2025: int | None
    """``None`` when ``fiscalperiod/create.json`` creates it."""


def _span(days: Iterable[date]) -> tuple[date, date]:
    ordered = sorted(days)
    return ordered[0], ordered[-1]


SPAN_2025 = _span(entry.day for entry in ENTRIES_2025)
SPAN_2026 = _span([entry.day for entry in ENTRIES_2026] + [order.day for order in ORDERS])


def check_organisation_name(session: Session) -> None:
    """Guard 2: the company name of the main location contains ``demo``."""
    path = "location/list.json"
    locations = records(session.read(path, "guard 2, organisation name"), path)
    main = [record for record in locations if record.get("type") == "MAIN"] or locations
    names = [record.get("orgName") for record in main]
    if not names or not all(
        isinstance(name, str) and DEMO_MARK in name.casefold() for name in names
    ):
        raise Refused(
            "the organisation's name does not contain 'demo' (read as the company name, "
            "orgName, of its main location in location/list.json; the documentation has no "
            "other organisation read). Seed only a fresh organisation named like "
            "'Muster Handel AG Demo'"
        )


def read_periods(session: Session) -> list[Period]:
    """The fiscal periods from ``fiscalperiod/list.json``; refuses unreadable dates."""
    path = "fiscalperiod/list.json"
    periods = []
    for record in records(session.read(path, "fiscal periods"), path):
        start, end = _day(record.get("start")), _day(record.get("end"))
        if start is None or end is None:
            raise Refused(f"{path}: a fiscal period without a readable start and end date")
        periods.append(Period(_id(record, path), start, end))
    if not periods:
        raise Refused(f"{path} lists no fiscal period")
    return periods


def check_empty(session: Session, periods: Sequence[Period]) -> None:
    """Guard 3: no person; no journal entry, sales or purchase order in any fiscal period.

    The journal and order lists answer for the current fiscal period unless
    ``fiscalPeriodId`` is given (``docs/upstream/meta.md``, Switch fiscal period).
    """
    what = "guard 3, empty organisation"
    totals: list[tuple[str, int | None]] = [
        ("person/list.json", total_of(session.read("person/list.json", what)))
    ]
    for period in periods:
        scope = {"fiscalPeriodId": str(period.id)}
        body = session.read("journal/list.json", what, scope)
        totals.append((f"journal/list.json fiscal period {period.start.year}", total_of(body)))
        for order_type in ("SALES", "PURCHASE"):
            body = session.read("order/list.json", what, {"type": order_type, **scope})
            label = f"order/list.json type {order_type} fiscal period {period.start.year}"
            totals.append((label, total_of(body)))
    unknown = [name for name, total in totals if total is None]
    found = [f"{name} total {total}" for name, total in totals if total]
    if unknown:
        raise Refused(
            f"cannot confirm the organisation is empty: no numeric total from {', '.join(unknown)}"
        )
    if found:
        raise Refused(
            f"the organisation is not empty ({'; '.join(found)}): seed only a fresh, empty "
            "organisation; this script never deletes anything"
        )


def resolve_accounts(session: Session, numbers: Sequence[str]) -> dict[str, int]:
    """Guard 4: the id of every account number the plan uses; refuses missing or inactive."""
    path = "account/list.json"
    by_number: dict[str, dict[str, Any]] = {}
    for record in records(session.read(path, "guard 4, chart of accounts"), path):
        by_number.setdefault(str(record.get("number", "")).strip(), record)
    missing = [number for number in numbers if number not in by_number]
    inactive = [
        number for number in numbers if number in by_number and _inactive(by_number[number])
    ]
    if missing or inactive:
        problems = []
        if missing:
            problems.append(f"missing: {', '.join(missing)}")
        if inactive:
            problems.append(f"inactive: {', '.join(inactive)}")
        raise Refused(
            f"the chart of accounts lacks account numbers the plan uses ({'; '.join(problems)}); "
            "the script creates no accounts"
        )
    return {number: _id(by_number[number], path) for number in numbers}


def plan_periods(periods: Sequence[Period]) -> tuple[int, int | None]:
    """The 2026 period's id, and the 2025 one's or ``None`` when it is to be created."""
    current = next((p for p in periods if p.covers(*SPAN_2026)), None)
    if current is None:
        raise Refused(
            f"no fiscal period covers {SPAN_2026[0]} to {SPAN_2026[1]}, the 2026 entries and orders"
        )
    previous = next((p for p in periods if p.covers(*SPAN_2025)), None)
    if previous is not None:
        return current.id, previous.id
    if min(p.start for p in periods) != date(2026, 1, 1):
        raise Refused(
            f"no fiscal period covers {SPAN_2025[0]} to {SPAN_2025[1]}, and the earliest one does "
            "not start on 2026-01-01, so fiscalperiod/create.json with type EARLIEST would not "
            "create 2025"
        )
    return current.id, None


def missing_currencies(session: Session) -> list[Currency]:
    """The planned currencies whose code ``currency/list.json`` lacks."""
    path = "currency/list.json"
    found = records(session.read(path, "currencies"), path)
    codes = {str(record.get("code", "")).upper() for record in found}
    return [currency for currency in CURRENCIES if currency.code not in codes]


def resolve_taxes(session: Session) -> dict[TaxKind, int]:
    """The ids of the planned tax codes, active ones only; refuses a missing code.

    Prints the ``calcType`` (NET or GROSS) of each one's components, so whether a journal
    ``amount`` with a ``taxId`` is read as net or gross is observed, not assumed.
    """
    path = "tax/list.json"
    found = records(session.read(path, "tax codes"), path)
    active = {str(record.get("code", "")): record for record in found if not _inactive(record)}
    by_code = {code: _id(record, path) for code, record in active.items()}
    missing = [code for code in TAX_CODES.values() if code not in by_code]
    if missing:
        available = ", ".join(sorted(code for code in by_code if code)) or "none"
        raise Refused(
            f"tax/list.json has no active tax code {', '.join(missing)} "
            f"(active codes: {session.scrub(available)})"
        )
    for code in TAX_CODES.values():
        observe_calc_type(session, code, active[code], by_code[code])
    return {kind: by_code[code] for kind, code in TAX_CODES.items()}


def observe_calc_type(session: Session, code: str, record: Mapping[str, Any], tax_id: int) -> None:
    """Print the ``calcType`` of one tax code's components.

    From the ``tax/list.json`` record, or from ``tax/read.json`` when the record has none.
    """
    source = "tax/list.json"
    found = calc_types(record.get("components"))
    if found is None:
        source = "tax/read.json"
        detail = _record(session.read(source, f"tax code {code}", {"id": str(tax_id)}))
        found = calc_types(detail.get("components")) if isinstance(detail, dict) else None
    if found is None:
        shown = "not reported by tax/list.json or tax/read.json"
    else:
        shown = f"{session.scrub(', '.join(found))} (from {source})"
    session.observed.calc_types[code] = shown
    say(f"lookup: tax code {code}, components calcType {shown}")


def resolve_person_categories(session: Session) -> dict[Role, int]:
    """The person category per role, matched by name; a role without a match gets none."""
    path = "person/category/list.json"
    found = records(session.read(path, "person categories"), path)
    chosen: dict[Role, int] = {}
    for role, names in PERSON_CATEGORY_NAMES.items():
        match = next((r for r in found if not _inactive(r) and names_of(r) & names), None)
        if match is not None:
            chosen[role] = _id(match, path)
    return chosen


def resolve_order_categories(session: Session) -> dict[OrderType, int]:
    """The order category per type, matched by name; refuses a type without a match."""
    path = "order/category/list.json"
    chosen: dict[OrderType, int] = {}
    for order_type, preferences in ORDER_CATEGORY_NAMES.items():
        body = session.read(path, f"order categories {order_type}", {"type": order_type})
        found = [r for r in records(body, path) if not _inactive(r)]
        for names in preferences:
            match = next((r for r in found if names_of(r) & names), None)
            if match is not None:
                chosen[order_type] = _id(match, path)
                break
        else:
            listed = "; ".join(
                f"id {r.get('id')}: {' / '.join(sorted(names_of(r))) or '(no name)'}" for r in found
            )
            raise Refused(
                f"no {order_type} order category is named like an invoice"
                + (" or a purchase order" if order_type == "PURCHASE" else "")
                + f" (categories: {session.scrub(listed) or 'none'})"
            )
    return chosen


def run_guards(session: Session) -> Context:
    """Guards 2 to 4 and the lookups, in order; nothing is written."""
    check_organisation_name(session)
    say("guard 2: the organisation's name contains 'demo'")
    periods = read_periods(session)
    check_empty(session, periods)
    say("guard 3: no persons, journal entries or orders")
    accounts = resolve_accounts(session, account_numbers())
    say(f"guard 4: the chart of accounts has {', '.join(accounts)}")
    period_2026, period_2025 = plan_periods(periods)
    context = Context(
        accounts=accounts,
        taxes=resolve_taxes(session),
        person_categories=resolve_person_categories(session),
        order_categories=resolve_order_categories(session),
        missing_currencies=missing_currencies(session),
        period_2026=period_2026,
        period_2025=period_2025,
    )
    roles = ", ".join(f"{role} id {cid}" for role, cid in context.person_categories.items())
    say(
        "lookups: fiscal periods, tax codes, order categories resolved; person categories: "
        + (roles or "none fits, persons get no category")
    )
    return context


# --- Forms --------------------------------------------------------------------------


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


def _number(value: Decimal) -> int | float:
    """A JSON number: whole values as integers, others as floats."""
    return int(value) if value == value.to_integral_value() else float(value)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def currency_form(currency: Currency) -> dict[str, str]:
    """``currency/create.json``: code, description and the synthetic rate."""
    return {"code": currency.code, "description": currency.description, "rate": str(currency.rate)}


def person_form(person: Person, category_id: int | None) -> dict[str, str]:
    """``person/create.json``: the company with its role, main address and e-mail."""
    form = {
        "company": person.company,
        "isCustomer" if person.role == "customer" else "isVendor": "true",
        "language": person.language,
        "addresses": _json(
            [
                {
                    "type": "MAIN",
                    "address": person.address,
                    "zip": person.postcode,
                    "city": person.city,
                    "canton": person.canton,
                    "country": "CHE",
                }
            ]
        ),
        "contacts": _json([{"type": "EMAIL_WORK", "address": person.email}]),
    }
    if category_id is not None:
        form["categoryId"] = str(category_id)
    return form


def journal_form(entry: Entry, context: Context, persons: Mapping[str, int]) -> dict[str, str]:
    """``journal/create.json``: a simple entry, or a collective one with ``items``."""
    form = {"dateAdded": entry.day.isoformat(), "title": entry.title}
    if entry.lines:
        items: list[dict[str, Any]] = []
        for line in entry.lines:
            item: dict[str, Any] = {"accountId": context.accounts[line.account]}
            if line.debit is not None:
                item["debit"] = _number(line.debit)
            if line.credit is not None:
                item["credit"] = _number(line.credit)
            if line.associate is not None:
                item["associateId"] = persons[line.associate]
            if line.description is not None:
                item["description"] = line.description
            items.append(item)
        form["items"] = _json(items)
        return form
    if entry.debit is None or entry.credit is None or entry.amount is None:
        raise ValueError(f"{entry.title}: a simple entry needs debit, credit and amount")
    form["debitId"] = str(context.accounts[entry.debit])
    form["creditId"] = str(context.accounts[entry.credit])
    form["amount"] = _money(entry.amount)
    if entry.tax is not None:
        form["taxId"] = str(context.taxes[entry.tax])
    if entry.associate is not None:
        form["associateId"] = str(persons[entry.associate])
    if entry.reference is not None:
        form["reference"] = entry.reference
    return form


def order_form(order: Order, context: Context, persons: Mapping[str, int]) -> dict[str, str]:
    """``order/create.json``: person, category, date, number and the items as JSON."""
    tax_id = context.taxes[ORDER_TAX[order.type]]
    items = [
        {
            "accountId": context.accounts[item.account],
            "name": item.name,
            "description": item.description,
            "quantity": _number(item.quantity),
            "unitPrice": _number(item.unit_price),
            "taxId": tax_id,
        }
        for item in order.items
    ]
    return {
        "associateId": str(persons[order.associate]),
        "categoryId": str(context.order_categories[order.type]),
        "date": order.day.isoformat(),
        "nr": order.nr,
        "description": order.description,
        "language": "DE",
        "items": _json(items),
    }


# --- Seeding ----------------------------------------------------------------------------


def _insert_id(body: Mapping[str, Any], what: str) -> int:
    value = body.get("insertId")
    if isinstance(value, bool) or not isinstance(value, int | str) or not str(value).isdigit():
        raise Failed(f"{what}: success without a numeric insertId, which the next steps need")
    return int(value)


def check_round_trip(session: Session, person: Person, person_id: int, what: str) -> None:
    """Read the first person back; stop unless ``company`` is what was sent, byte for byte.

    Its company name carries an umlaut, so a backend that decoded the form in another
    charset than the declared UTF-8 shows here, after one record and before any other.
    """
    path = "person/read.json"
    body = session.read(path, f"{what}, UTF-8 check", {"id": str(person_id)})
    record = _record(body)
    company = record.get("company") if isinstance(record, dict) else None
    if not isinstance(company, str):
        session.observed.utf8 = f"not checked: {path} answered no company"
        raise Failed(
            f"{what}: {path} answered no company, so the UTF-8 round trip cannot be "
            "checked; nothing further is written"
        )
    if company.encode("utf-8") != person.company.encode("utf-8"):
        shown = session.scrub(company)
        session.observed.utf8 = f"garbled: sent {person.company!a}, {path} answered {shown!a}"
        raise Failed(
            f"{what}: the backend garbled UTF-8: sent {person.company!r}, {path} answers "
            f"{shown!r} (code points: sent {person.company!a}, answered {shown!a}); "
            "nothing further is written (docs/demo-org.md, Seeding)"
        )
    session.observed.utf8 = f"{path} answers company {person.company!r} byte for byte"
    say(f"{what}: read back byte for byte, the umlaut arrived as UTF-8")


def seed(session: Session, context: Context, created: Counter[str]) -> int:
    """Create everything in dependency order; returns the 2025 fiscal period's id.

    The persons come first: ``person/create.json`` has a mandatory field, so a body
    upstream cannot read is refused instead of saved with defaults (every parameter of
    ``fiscalperiod/create.json`` is optional), and the first person is read back
    (``check_round_trip``) before anything else is written.
    """
    persons: dict[str, int] = {}
    for number, person in enumerate(PERSONS, start=1):
        what = f"person {number}/{len(PERSONS)} {person.company}"
        category = context.person_categories.get(person.role)
        body = session.create("person/create.json", person_form(person, category), what)
        persons[person.key] = _insert_id(body, what)
        created["persons"] += 1
        say(f"{what}: insertId {persons[person.key]}")
        if number == 1:
            check_round_trip(session, person, persons[person.key], what)

    for currency in context.missing_currencies:
        what = f"currency {currency.code}"
        body = session.create("currency/create.json", currency_form(currency), what)
        created["currencies"] += 1
        say(f"{what}: insertId {session.shown_id(body)}")

    period_2025 = context.period_2025
    if period_2025 is None:
        what = "fiscal period 2025"
        body = session.create("fiscalperiod/create.json", {"type": "EARLIEST"}, what)
        created["fiscal periods"] += 1
        say(f"{what}: insertId {session.shown_id(body)}")
        covering = [p for p in read_periods(session) if p.covers(*SPAN_2025)]
        if not covering:
            raise Failed(f"{what}: created, but no fiscal period covers {SPAN_2025[0]} now")
        period_2025 = covering[0].id

    entries = all_entries()
    for number, entry in enumerate(entries, start=1):
        what = f"journal entry {number}/{len(entries)} {entry.day} {entry.title}"
        body = session.create("journal/create.json", journal_form(entry, context, persons), what)
        created["journal entries"] += 1
        say(f"{what}: insertId {session.shown_id(body)}")

    for number, order in enumerate(ORDERS, start=1):
        what = f"order {number}/{len(ORDERS)} {order.type} {order.nr}"
        body = session.create("order/create.json", order_form(order, context, persons), what)
        created["orders"] += 1
        say(f"{what}: insertId {session.shown_id(body)}")
    return period_2025


def report_totals(session: Session, context: Context, period_2025: int) -> None:
    """The ``total`` each list endpoint reports after seeding."""
    what = "summary"
    reads: list[tuple[str, str, dict[str, str] | None]] = [
        ("person/list.json", "person/list.json", None),
        ("journal/list.json 2025", "journal/list.json", {"fiscalPeriodId": str(period_2025)}),
        (
            "journal/list.json 2026",
            "journal/list.json",
            {"fiscalPeriodId": str(context.period_2026)},
        ),
        (
            "order/list.json SALES 2026",
            "order/list.json",
            {"type": "SALES", "fiscalPeriodId": str(context.period_2026)},
        ),
        (
            "order/list.json PURCHASE 2026",
            "order/list.json",
            {"type": "PURCHASE", "fiscalPeriodId": str(context.period_2026)},
        ),
        ("currency/list.json", "currency/list.json", None),
        ("fiscalperiod/list.json", "fiscalperiod/list.json", None),
    ]
    say("Totals now reported")
    for label, path, params in reads:
        say(f"  {label}: total {total_of(session.read(path, what, params))}")


BALANCE_DATES = (date(2025, 12, 31), date(2026, 9, 30))
"""The days the summary reads the balance of 1100 (debtors) at: the end of 2025, and the
last day of the 2026 entries."""


def report_balances(session: Session, context: Context) -> None:
    """The balance of 1100 (debtors) at ``BALANCE_DATES``, for the gross-or-net comparison."""
    say(f"Balance of account {DEBTORS} (debtors), to compare with docs/demo-org.md")
    for day in BALANCE_DATES:
        params = {"id": str(context.accounts[DEBTORS]), "date": day.isoformat()}
        shown = session.read_text("account/balance", "summary", params)
        session.observed.balances[day.isoformat()] = shown
        say(f"  {day}: {shown}")


def report_created(created: Counter[str]) -> None:
    """The count of records created per resource."""
    resources = ("persons", "currencies", "fiscal periods", "journal entries", "orders")
    say("Created: " + ", ".join(f"{resource} {created[resource]}" for resource in resources))


# --- The plan ------------------------------------------------------------------------


def plan_lines() -> list[str]:
    """The plan: counts per resource, then a compact table of every record."""
    customers = sum(person.role == "customer" for person in PERSONS)
    collective = sum(bool(entry.lines) for entry in all_entries())
    sales = sum(order.type == "SALES" for order in ORDERS)
    rates = ", ".join(f"{c.code} {c.rate}" for c in CURRENCIES)
    out = [
        f"Plan: synthetic books of {COMPANY} (fictional), Zürich, CHF, for a fresh CashCtrl "
        "demo organisation",
        "",
        f"  persons           {len(PERSONS):>3}  {customers} customers, "
        f"{len(PERSONS) - customers} vendors; the first, {PERSONS[0].company}, is read back "
        "to check UTF-8 before any other write",
        f"  currencies        {len(CURRENCIES):>3}  {rates}; only those missing are created",
        "  fiscal periods      1  2025 (type EARLIEST); only if no period covers 2025",
        f"  journal entries   {len(all_entries()):>3}  {len(ENTRIES_2025)} in 2025, "
        f"{len(ENTRIES_2026)} in 2026, {collective} of them collective",
        f"  orders            {len(ORDERS):>3}  {sales} SALES invoices, "
        f"{len(ORDERS) - sales} PURCHASE orders",
        f"  writes, at most   {max_writes():>3}  in this order, as {FORM_CONTENT_TYPE} "
        f"(--multipart: {MULTIPART})",
        "",
        f"Account numbers: {' '.join(account_numbers())}",
        f"Tax codes: {TAX_CODES['sales']} on sales, {TAX_CODES['purchase']} on purchases",
        "",
        "Persons",
    ]
    for person in PERSONS:
        out.append(
            f"  {person.role:<8}  {person.company:<23}  {person.address:<20}  "
            f"{person.postcode} {person.city:<10}  {person.email}"
        )
    out += ["", "Journal entries (debit / credit, amount, tax)"]
    for entry in all_entries():
        tax = TAX_CODES[entry.tax] if entry.tax else ""
        accounts = "collective " if entry.lines else f"{entry.debit} / {entry.credit}"
        out.append(f"  {entry.day}  {accounts}  {_money(entry.total):>10}  {tax:<4} {entry.title}")
        for line in entry.lines:
            side, amount = (
                ("debit ", line.debit) if line.debit is not None else ("credit", line.credit)
            )
            shown = _money(amount) if amount is not None else ""
            out.append(f"      {side} {line.account}  {shown:>10}  {line.description}")
    out += ["", "Orders (net, before tax)"]
    names = {person.key: person.company for person in PERSONS}
    for order in ORDERS:
        out.append(
            f"  {order.type:<8}  {order.nr}  {order.day}  {names[order.associate]:<23}  "
            f"{_money(order.net):>9}  {TAX_CODES[ORDER_TAX[order.type]]}"
        )
        for item in order.items:
            quantity, price = _number(item.quantity), _money(item.unit_price)
            out.append(f"      {item.account}  {quantity:>3} x {price:>7}  {item.name}")
    return out


# --- Command line ------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """``--plan`` (the default) or ``--apply --yes``, optionally ``--multipart``."""
    parser = argparse.ArgumentParser(
        prog="seed_demo.py",
        description="Seed a fresh, empty CashCtrl demo organisation with synthetic books.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="print the plan, no network (default)")
    mode.add_argument("--apply", action="store_true", help="seed the demo organisation")
    parser.add_argument("--yes", action="store_true", help="confirm --apply")
    parser.add_argument(
        "--multipart",
        action="store_true",
        help="with --apply: send the writes as multipart/form-data instead of form-encoded, "
        "for a manual rerun only (docs/demo-org.md)",
    )
    args = parser.parse_args(argv)
    if args.yes and not args.apply:
        parser.error("--yes only confirms --apply")
    if args.multipart and not args.apply:
        parser.error("--multipart only changes how --apply writes")
    return args


def apply(environ: Mapping[str, str], *, multipart: bool = False) -> int:
    """Run the guards, seed, summarise; return the exit status."""
    try:
        credentials = read_credentials(environ)
    except Refused as refusal:
        say(f"refused (guard 1): {refusal}", err=True)
        return 1
    say("guard 1: the demo pair is set and the subdomain is one DNS label")
    scrub = Scrubber(credentials)
    observed = Observed()
    created: Counter[str] = Counter()
    client = httpx.Client(
        base_url=f"https://{credentials.subdomain}.cashctrl.com/api/v1/",
        auth=httpx.BasicAuth(credentials.key, ""),
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )
    with client:
        session = Session(client, scrub, Pacer(PACE_SECONDS), observed, multipart=multipart)
        try:
            context = run_guards(session)
        except (Refused, Failed) as refusal:
            say(f"refused: {refusal}; nothing was written", err=True)
            return 1
        say(
            f"all guards passed; writing at most {max_writes()} records as "
            f"{observed.encoding}, one request every {PACE_SECONDS} seconds"
        )
        status = 0
        try:
            period_2025 = seed(session, context, created)
        except (Refused, Failed) as failure:
            say(f"stopped at {failure}; no further request was sent", err=True)
            status = 1
        report_created(created)
        if status == 0:
            try:
                report_totals(session, context, period_2025)
                report_balances(session, context)
            except (Refused, Failed) as failure:
                say(f"summary incomplete: {failure}", err=True)
                status = 1
    for line in observed.lines():
        say(line)
    return status


def main(argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    """Print the plan, or apply it after the guards; return the exit status."""
    args = parse_args(argv)
    if not args.apply:
        for line in plan_lines():
            say(line)
        return 0
    if not args.yes:
        say("refused: --apply writes to the demo organisation; confirm with --yes", err=True)
        return 1
    return apply(os.environ if environ is None else environ, multipart=args.multipart)


if __name__ == "__main__":
    sys.exit(main())
