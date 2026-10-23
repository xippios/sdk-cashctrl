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
