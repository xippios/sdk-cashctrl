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
