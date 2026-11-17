Refresh the upstream documentation snapshot for CashCtrl: $ARGUMENTS

The snapshot in `docs/upstream/` is the reference for every endpoint wrapper
(ADR-0003). It is refreshed deliberately, by pull request, so changes are visible as
diffs (conventions §3), and captured by `scripts/refresh_upstream.py`, so that a refresh
is reproducible. The change meets sdk-core's definition of done,
https://github.com/xippios/sdk-core/blob/main/docs/definition-of-done.md, and its review
checklist, https://github.com/xippios/sdk-core/blob/main/docs/review-checklist.md.

1. **Compare first.** cashctrl's capture script is of its own shape, not the template's
   skeleton, and has no `--check`: it is run as its docstring says, and the diff in
   step 4 does the comparing. `--out <directory>` writes the snapshot elsewhere, to
   compare without touching `docs/upstream/`; `--from-file <path>` reads a saved copy of
   the page instead of fetching it.
2. **Capture.** `uv run scripts/refresh_upstream.py` fetches the one documentation page,
   https://app.cashctrl.com/static/help/en/api/index.html, before it writes anything,
   then writes one Markdown file per top-level entry of its table of contents and
   regenerates `docs/upstream/FETCHED.md` (conventions §3, ADR-0003): `Fetched`, the UTC
   time of the run in ISO 8601 with an explicit `Z`; under Attribution the copyright line
   as the page's footer states it; the page's size, sha256, HTTP status, ETag and
   Last-Modified where sent; one row per file. It stops on any change to the page's
   structure it does not know (a table shape, a tag, an icon), and unless every section
   shows the same words on the page and in the Markdown. Read the result.
3. **Teach the script** a new construct where it stopped on one. It converts with
   `markdownify` over `beautifulsoup4`: both are pinned in the script's `# /// script`
   block and at the same pins in the dev group of `pyproject.toml`, so that
   `mypy --strict` reads their types; the pins move together.
4. Diff against the previous snapshot: `git diff --stat docs/upstream/` and read the
   changes. Summarise in the pull request what changed upstream: new or removed
   operations, renamed or newly required parameters, changed semantics, and which
   wrappers in `src/xippios/cashctrl/api/` are affected.
5. Change no code with the snapshot, with one exception: `scripts/refresh_upstream.py`,
   the capture script, may change with the snapshot it captures, and so may the
   converter's pins in the dev group (`pyproject.toml`, `uv.lock`). If wrappers must
   follow, list them as follow-up issues or `/add-endpoint` runs.
6. A changelog fragment under `changelog/`, as `changelog/README.md` lays it out, says
   what the refreshed snapshot records that changed upstream.
7. Stage the snapshot (`git add docs/upstream scripts`) before
   `uv run pre-commit run --all-files`, which checks only the files in git's index: an
   unstaged new file would escape the secret scan. Then run the other checks,
   `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`.
