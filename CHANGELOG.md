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
  synthetic books (Muster Handel AG: 10 fictional companies, 48 manual journal entries in
  2025 and 2026, 4 sales invoices and 2 purchase orders, EUR and USD if missing), so
  fixtures and live tests never touch real data. `--plan` (the default) prints the plan
  without a request; `--apply --yes` first refuses, before any write, an organisation
  whose name lacks `demo`, one that is not empty, and a chart of accounts without the
  account numbers it uses, then writes form-encoded at one request per second and stops
  at the first refusal. It reads only `CASHCTRL_DEMO_SUBDOMAIN` and
  `CASHCTRL_DEMO_API_KEY` and never prints either.
- `docs/demo-org.md`: why the demo organisation is synthetic, how to create and seed it,
  the books in full, the assumed account numbers and VAT codes, and a placeholder for the
  write semantics the first run observes.
