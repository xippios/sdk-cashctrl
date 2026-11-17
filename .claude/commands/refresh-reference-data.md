Note: cashctrl packages no reference data, and `scripts/refresh_reference.py` is the template's skeleton, so this command does not apply here until a documented value set is needed; then the script becomes the generator below.

Refresh the packaged reference data for CashCtrl: $ARGUMENTS

CashCtrl has two kinds of lists, and only one of them may ship inside the package. A
multi-tenant source (ADR-0014) packages no tenant data, only lists that are the same for
every tenant, if any.

The change meets sdk-core's definition of done,
https://github.com/xippios/sdk-core/blob/main/docs/definition-of-done.md, and its review
checklist, https://github.com/xippios/sdk-core/blob/main/docs/review-checklist.md.

- **Tenant data is never packaged.** Accounts, currencies, tax codes, fiscal periods,
  cost centres, units, person categories and every other list an organisation keeps for
  itself are per-organisation data: each organisation has its own, and they change as it
  books. The `list_<thing>` tasks serve them live, with `org`. Never write them into
  `reference/`, `enums.py`, a docstring or a fixture used as data.
- **Value sets the documentation fixes may ship.** Enumerations whose values
  `docs/upstream/` lists as "Possible values" of a parameter (journal types, order
  category types `SALES`/`PURCHASE`, sequence number types) are the only reference data
  this package may carry: `StrEnum`s in `enums.py` (an enumeration of integer ids an
  `IntEnum`, conventions §3) and, where a task looks them up, `reference/<name>.json`,
  generated with provenance from the snapshot, never typed in by hand and never fetched
  from an organisation.

None is packaged yet: `params.py` names no list in `PACKAGED_LISTS`, `enums.py` and
`reference/` hold none, and `scripts/refresh_reference.py` is the template's skeleton,
which fetches its lists through `api/` and so fits no value set the snapshot fixes. When
a task needs one, make the script the generator of step 3, a script of the package's own
shape that its docstring describes; `copier update` never overwrites it. The
`render_enums` port this repository deleted is one to start from:
`git show dfb65ce:scripts/refresh_reference.py` (dfb65ce on main, the merge of #13). Its
`--render-only` regenerates `enums.py` from the packaged `reference/*.json` alone,
without a request or a key, through its one `render_enums` call, as an adoption does
after a core release changes `render_enums` (conventions §15, item 6). Then:

1. Make sure `docs/upstream/` is current (`/refresh-upstream` first if it is not).
2. Find the parameter and its "Possible values" in `docs/upstream/`: snapshot file,
   operation, parameter. Values come from there, verbatim, nowhere else.
3. Make the script a generator over the snapshot: a `LISTS` mapping from the set's
   name to (snapshot file, operation, parameter); for each entry it reads the values from
   the snapshot, writes `reference/<name>.json` with core's `PackagedList(...).write`
   (`param`, `endpoint` = the snapshot file and operation, `fetched` = the snapshot's
   `Fetched` time in `docs/upstream/FETCHED.md`, `records`, a value list as records of
   one field named by the list) and regenerates `enums.py` with
   one `xippios.core.reference.render_enums` call (`member_names=` for a value with no
   identifier to derive; integer ids as `id_name_pairs` builds them), then `ruff format`
   and `ruff check --fix` on it, as `--render-only` does.
   It makes no API call, and keeps `--render-only`. Add the name to `PACKAGED_LISTS` in
   `params.py`, and a test that the generator reproduces the committed files from the
   snapshot.
4. Commit `enums.py` as the script leaves it: core's `render_enums` writes it ASCII-only
   and the script's ruff step lays it out (ADR-0008, amendment 2026-10-27).
5. Add a row to the provenance table in `reference/README.md`: the file, its origin
   (the `docs/upstream/` file it was rebuilt from, the operation and the parameter) and
   the snapshot's `Fetched` time.
6. Agents need the values to form valid calls: a parameter typed with the enum lists them
   in the tool's schema. Where a task takes them some other way, add one lookup task per
   list (`list_<thing>`, `/add-endpoint`), which returns the packaged data and does not
   call upstream; a list an agent needs whole that is longer than the default result cap
   (200 rows or 64 KB) gets a cap of its own, `MCP_CAPS` in `tasks.py`, keyed by the
   task's name (ADR-0016).
7. Update what pins the old lists: counts and dates in docstrings and in tests. A test
   that reads them from the packaged file needs no change.
8. A changelog fragment under `changelog/`, as `changelog/README.md` lays it out, says
   which lists changed.
9. Run the checks,
   `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest && uv run pre-commit run --all-files`,
   and summarise the diff in the pull request: values added or gone (a value that
   disappeared may break callers).
