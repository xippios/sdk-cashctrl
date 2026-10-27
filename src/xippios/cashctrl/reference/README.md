# Reference data for CashCtrl

Nothing ships here yet, and tenant data never will.

- Accounts, currencies, tax codes, fiscal periods and every other list an organisation
  keeps for itself are per-organisation data. The list tasks serve them live, with `org`;
  they are never packaged: a multi-tenant source packages no tenant data (ADR-0014), only
  lists that are the same for every organisation, if any.
- The only files this directory may hold are value sets that `docs/upstream/` fixes
  (enumerations such as journal or order types), generated from the snapshot by
  `scripts/refresh_reference.py` (`/refresh-reference-data`), never typed in by hand and
  never fetched from an organisation. The script also regenerates `enums.py` with one
  `xippios.core.reference.render_enums` call, a `StrEnum` per value set or an `IntEnum`
  per list of integer ids, then `ruff format` and `ruff check --fix`. Until the first set
  is needed, the script is a stub that exits non-zero; `--render-only` regenerates
  `enums.py` from the files here alone.
- Files keep upstream's names: a value set its parameter's name, a table its column
  names, a list of integer ids its records under upstream's field names.
- Agents get the values of every packaged set so they can form valid calls: a parameter
  typed with the set's enum lists them in the tool's schema; otherwise one lookup task
  per set, `list_<thing>`, served as the MCP tool `cashctrl_list_<thing>`, or the
  upstream's own lookup operation when it serves every set through one;
  `/refresh-reference-data` adds the task where it is missing.
- Every file has a row below naming the snapshot file, operation and parameter it comes
  from, and the snapshot's date.

| File | Origin (snapshot file, operation, parameter) | Snapshot |
| --- | --- | --- |
| (none yet) | | |
