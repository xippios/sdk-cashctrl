# Reference data for CashCtrl

Nothing ships here yet, and tenant data never will.

- Accounts, currencies, tax codes, fiscal periods and every other list an organisation
  keeps for itself are per-organisation data. The list tasks serve them live, with `org`;
  they are never packaged.
- The only files this directory may hold are value sets that `docs/upstream/` fixes
  (enumerations such as journal or order types), generated from the snapshot by
  `scripts/refresh_reference.py` (`/refresh-reference-data`), never typed in by hand and
  never fetched from an organisation. The script also regenerates `enums.py`, one
  `StrEnum` per set, with `xippios.core.reference.render_str_enums`. Until the first set
  is needed, the script is a stub that exits non-zero.
- Every file has a row below naming the snapshot file, operation and parameter it comes
  from, and the snapshot's date.

| File | Origin (snapshot file, operation, parameter) | Snapshot |
| --- | --- | --- |
| (none yet) | | |
