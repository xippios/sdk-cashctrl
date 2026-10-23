Refresh the packaged reference data for CashCtrl: $ARGUMENTS

CashCtrl has two kinds of lists, and only one of them may ship inside the package.

- **Tenant data is never packaged.** Accounts, currencies, tax codes, fiscal periods,
  cost centres, units, person categories and every other list an organisation keeps for
  itself are per-organisation data: each organisation has its own, and they change as it
  books. The `list_<thing>` tasks serve them live, with `org`. Never write them into
  `reference/`, `enums.py`, a docstring or a fixture used as data.
- **Value sets the documentation fixes may ship.** Enumerations whose values
  `docs/upstream/` lists as "Possible values" of a parameter (journal types, order
  category types `SALES`/`PURCHASE`, sequence number types) are the only reference data
  this package may carry: `StrEnum`s in `enums.py` and, where a task looks them up,
  `reference/<name>.json`, generated with provenance from the snapshot, never typed in
  by hand and never fetched from an organisation.

`scripts/refresh_reference.py` is a stub until the first such value set is needed: it
says so and exits with status 1. When a task needs one:

1. Work on a branch `chore/reference-<thing>`. Make sure `docs/upstream/` is current
   (`/refresh-upstream` first if it is not).
2. Find the parameter and its "Possible values" in `docs/upstream/`: snapshot file,
   operation, parameter. Values come from there, verbatim, nowhere else.
3. Replace the stub with a generator over the snapshot: a `LISTS` mapping from the set's
   name to (snapshot file, operation, parameter); for each entry it reads the values from
   the snapshot, writes `reference/<name>.json` (`param`, `fetched` = the snapshot date
   in `docs/upstream/FETCHED.md`, `values`) and regenerates `enums.py` with
   `xippios.core.reference.render_str_enums`. It makes no API call. Add the name to
   `PACKAGED_LISTS` in `params.py`, and a test that the generator reproduces the
   committed files from the snapshot.
4. Format the regenerated `enums.py`, in this order:
   `uv run ruff format src/xippios/cashctrl/enums.py && uv run ruff check --fix src/xippios/cashctrl/enums.py`.
   `render_str_enums` in xippios-core currently writes `__all__` unsorted on one line
   (ruff RUF022 and, past 100 characters, E501); formatting first leaves only the sort
   for `--fix`. The fix in core is tracked as row 12 of the family's `COORDINATION.md`
   queue (`render_str_enums`); drop this step once a core release carries it.
5. Add a row to the provenance table in `reference/README.md`: file, origin (snapshot
   file, operation, parameter), snapshot date.
6. Run the checks and open the PR with the diff summarised: values added or gone (a
   value that disappeared may break callers). Do not merge.
