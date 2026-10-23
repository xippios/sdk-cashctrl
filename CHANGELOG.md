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
