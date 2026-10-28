Note: cashctrl packages no reference data and has no `scripts/refresh_reference.py`, so this command does not apply here until a documented value set is needed; then the script comes back from the `render_enums` port this repository deleted (below).

Refresh the packaged reference data for CashCtrl: $ARGUMENTS

CashCtrl has two kinds of lists, and only one of them may ship inside the package. A
multi-tenant source (ADR-0014) packages no tenant data, only lists that are the same for
every tenant, if any.

The PR meets the definition of done,
https://github.com/xippios/sdk-core/blob/main/docs/definition-of-done.md, and the
reviewer judges it against
https://github.com/xippios/sdk-core/blob/main/docs/review-checklist.md.

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

None is packaged yet, so `scripts/refresh_reference.py`, `params.py`, `enums.py` and
`reference/` are gone (the note above). When a task needs a value set, bring them back
from the `render_enums` port deleted here: `git show dfb65ce:<path>` (dfb65ce on main,
the merge of #13), or `git show <commit>^:<path>` with `<commit>`, the commit that
deleted it, from `git log --diff-filter=D -1 -- scripts/refresh_reference.py`. Not from
template v0.2.2's scaffold: its script imports `render_str_enums` and
`render_int_enums`, which core 0.3.0 removed. Make the script the generator of step 3;
its `--render-only` regenerates `enums.py` from the packaged `reference/*.json` alone,
without a request or a key, through its one `render_enums` call, as an adoption does
after a core release changes `render_enums` (`/adopt-release`). Then:

1. Work on a branch `chore/reference-<thing>`. Make sure `docs/upstream/` is current
   (`/refresh-upstream` first if it is not).
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
8. Run the checks and open the PR, its body as the definition of done says, with the
   diff summarised: values added or gone (a value that disappeared may break callers).
   Do not merge.
