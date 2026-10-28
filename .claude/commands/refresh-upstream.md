Refresh the upstream documentation snapshot for CashCtrl: $ARGUMENTS

The snapshot in `docs/upstream/` is the reference for every endpoint wrapper
(ADR-0003). It is refreshed deliberately, by PR, so changes are visible as diffs, and
captured by `scripts/refresh_upstream.py`, so that a refresh is reproducible. The PR
meets the definition of done,
https://github.com/xippios/sdk-core/blob/main/docs/definition-of-done.md, and the
reviewer judges it against
https://github.com/xippios/sdk-core/blob/main/docs/review-checklist.md.

1. Work on a branch `docs/upstream-<yyyy-mm-dd>`.
2. **Compare first.** cashctrl's capture script is of its own shape, not the template's
   skeleton, and has no `--check`: it is run as its docstring says, and the diff in
   step 4 does the comparing. `--out <directory>` writes the snapshot elsewhere, to
   compare without touching `docs/upstream/`; `--from-file <path>` reads a saved copy of
   the page instead of fetching it.
3. **Capture.** `uv run scripts/refresh_upstream.py` fetches the one documentation page,
   https://app.cashctrl.com/static/help/en/api/index.html, before it writes anything,
   then writes one Markdown file per top-level entry of its table of contents and
   regenerates `docs/upstream/FETCHED.md` (conventions §3, ADR-0003): `Fetched`, the UTC
   time of the run in ISO 8601 with an explicit `Z`; under Attribution the copyright line
   as the page's footer states it; the page's size, sha256, HTTP status, ETag and
   Last-Modified where sent; one row per file. It stops on any change to the page's
   structure it does not know (a table shape, a tag, an icon), and unless every section
   shows the same words on the page and in the Markdown. Read the result. A new
   construct is taught to the script, which converts with `markdownify` over
   `beautifulsoup4`: both are pinned in the script's `# /// script` block and at the
   same pins in the dev group of `pyproject.toml`, so that `mypy --strict` reads their
   types; the pins move together.
4. Diff against the previous snapshot: `git diff --stat docs/upstream/` and read the
   changes. Summarise in the PR description what changed upstream: new or removed
   operations, renamed or newly required parameters, changed semantics, and which
   wrappers in `src/xippios/cashctrl/api/` are affected.
5. Do not change any code in this PR, with one exception: `scripts/refresh_upstream.py`,
   the capture script, may change with the snapshot it captures, and so may the
   converter's pins in the dev group (`pyproject.toml`, `uv.lock`). If wrappers must
   follow, list them as follow-up issues or `/add-endpoint` runs.
6. Stage the snapshot (`git add docs/upstream scripts`) before
   `uv run pre-commit run --all-files`, which checks only the files in git's index: an
   unstaged new file would escape the secret scan.
7. Open the PR, its body as the definition of done says. Do not merge.
