Refresh the packaged reference data for CashCtrl: $ARGUMENTS

CashCtrl has two kinds of lists, and only one of them may ship inside the package. A
multi-tenant source (ADR-0014) packages no tenant data, only lists that are the same for
every tenant, if any.

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

`scripts/refresh_reference.py` is a stub until the first such value set is needed: run
without options it says so and exits with status 1. Its `LISTS` is empty, and
`--render-only` regenerates `enums.py` from the packaged `reference/*.json` alone (none
yet, so an empty module), without a request or a key, as an adoption does after a core
release changes the renderers (`/adopt-release`). When a task needs a value set:

1. Work on a branch `chore/reference-<thing>`. Make sure `docs/upstream/` is current
   (`/refresh-upstream` first if it is not).
2. Find the parameter and its "Possible values" in `docs/upstream/`: snapshot file,
   operation, parameter. Values come from there, verbatim, nowhere else.
3. Replace the stub with a generator over the snapshot: a `LISTS` mapping from the set's
   name to (snapshot file, operation, parameter); for each entry it reads the values from
   the snapshot, writes `reference/<name>.json` (`param`, `fetched` = the snapshot date
   in `docs/upstream/FETCHED.md`, `values`) and regenerates `enums.py` with
   `xippios.core.reference.render_str_enums` (`member_names=` for a value with no
   identifier to derive), or, for integer ids, `id_name_pairs` and `render_int_enums`.
   It makes no API call, and keeps `--render-only`. Add the name to `PACKAGED_LISTS` in
   `params.py`, and a test that the generator reproduces the committed files from the
   snapshot.
4. Commit `enums.py` as rendered: core's renderers write it ASCII-only and ruff-clean,
   so no formatting step follows (ADR-0008).
5. Add a row to the provenance table in `reference/README.md`: file, origin (snapshot
   file, operation, parameter), snapshot date.
6. Agents need the values to form valid calls: a parameter typed with the enum lists them
   in the tool's schema. Where a task takes them some other way, add one lookup task per
   list (`list_<thing>`, `/add-endpoint`), which returns the packaged data and does not
   call upstream; a list an agent needs whole that is longer than the default result cap
   (200 rows or 64 KB) gets a cap of its own, `MCP_CAPS` in `tasks.py`, keyed by the
   task's name (ADR-0016).
7. Run the checks and open the PR with the diff summarised: values added or gone (a
   value that disappeared may break callers). Do not merge.
