Record a fixture for CashCtrl: $ARGUMENTS

Expected arguments: `<endpoint> <case> [key=value ...] [--wrong-key]`, for example
`account/read.json unknown_id id=999999999`.

Fixtures are recorded through the real client by `scripts/record_fixture.py`, never typed
in by hand. **Every fixture comes from the demo organisation and from nothing else**: the
script has no organisation parameter, drops `CASHCTRL_ORGS` from its own environment and
always records through `client_for("demo")`. Never record from a productive organisation,
never adapt the script or a one-off snippet to do so, and never set `CASHCTRL_ORGS` with
real names to record. The repository is public.

The demo subdomain is treated exactly like a key: never in a file, a commit, a log line or
a report. Never print `CASHCTRL_DEMO_SUBDOMAIN` or any variable ending in `_API_KEY`.

**Policies until the demo organisation is confirmed synthetic.** Whether its content
suits a public repository is its owner's decision; until then the recorder holds to
these, and each refusal writes nothing and exits non-zero:

- **GET only.** Any other `--method` is refused before a request is sent. The recorder
  for the write tools will add writes deliberately; never work around this.
- **`.json` only.** An endpoint without the extension (`account/balance`,
  `account/costcenter/balance`, `fiscalperiod/result`, `setting/get`) answers a bare
  number or a document, and an export (`.pdf`, `.xlsx`, `.csv`, `.zip`) a file; both
  are refused before a request is sent.
- **Allowed modules only.** Every module but account, currency, fiscalperiod and tax
  is refused before a request is sent (`ALLOWED_MODULES` in the script), and
  `account/bank/` is refused even so (IBAN, BIC, QR-IBAN; `REFUSED_PATHS`). The others
  are not yet cleared for recording from the demo organisation: locations carry the
  company's address and VAT number, history the audit trail, person, order and journal
  third parties and amounts.
- **No amounts.** A body with a non-zero number under a key matching `amount`,
  `balance`, `targetMin` or `targetMax` (any case, any depth) is refused, naming the
  key; `total`, `rate`, `percentage*` and ids are not amounts. The key list is tuned
  for the allowed modules and must be revisited (`debit`, `credit`, `sum`, `value`,
  `price`, `net`, `gross`, `total` outside the list envelope) before journal or order
  is allowed. Narrow the case to records whose amounts are zero. `--allow-amounts`
  lifts this policy, and only this one: it exists for a future synthetic demo
  organisation and is **only** for that. Never pass it while the demo organisation is
  not confirmed synthetic.
- **No e-mail addresses.** Every e-mail address in the URL, the headers and the body
  (`createdBy`, `lastUpdatedBy`, HTML fields such as `notes`) becomes
  `user@example.com`, also when `@` is written `%40`, `&#64;`, `&#x40;` or `&commat;`;
  `SYSTEM` stays.

1. The demo pair comes from direnv in `~/github/sdk`. Confirm it without printing it:
   `direnv exec ~/github/sdk sh -c '[ -n "$CASHCTRL_DEMO_SUBDOMAIN" ] && [ -n "$CASHCTRL_DEMO_API_KEY" ] && echo ok'`.
2. Find the request path and parameters in `docs/upstream/` and in the wrapper under
   `src/xippios/cashctrl/api/`. Parameters are named as upstream names them (`fiscalPeriodId`).
   Recordings are read-only `.json` endpoints (`list.json`, `read.json`) of the allowed
   modules. Exports (PDF, Excel, ZIP) are out of scope, and the recorder also refuses a
   body that is not UTF-8 text, because it can be neither scrubbed nor reviewed.
3. Record, from the repository root:

   ```bash
   direnv exec ~/github/sdk uv run scripts/record_fixture.py <endpoint> <case> [key=value ...]
   ```

   It builds the fixture in memory with core's `fixture_from_response` (credentials
   scrubbed), replaces the demo host with `demo.cashctrl.com` everywhere in it (the host
   offline tests replay against) and every e-mail address with `user@example.com`,
   checks it, and only then writes `tests/fixtures/<endpoint>/<case>.json`
   (`account/read.json` becomes `account_read/`). It prints only the status and that
   URL. `--wrong-key` sends an invalid key instead of the real one, to record a 401.
   Error cases (an unknown id, a refusal) are worth recording; the recorder keeps them
   instead of raising.
4. The check runs on the scrubbed fixture before the write: if the real subdomain, the
   real key or an e-mail address other than `user@example.com` is in it, nothing is
   written and the script exits non-zero; if a key-like name carries a value other than
   `REDACTED`, it writes the file and exits non-zero for review. A refused amount names
   its key. Either way, stop and report what it named; never print the file to find
   out.
5. Check again before committing, never echoing a value:

   ```bash
   grep -rniE 'api[_-]?key|token|secret|authorization|password' tests/fixtures
   grep -rhoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' tests/fixtures | sort -u
   direnv exec ~/github/sdk sh -c 'git grep -n --untracked -i -- "$CASHCTRL_DEMO_SUBDOMAIN" >/dev/null && echo LEAK || echo clean'
   ```

   The first prints nothing but `REDACTED` values (and the README's own example line);
   the second prints `user@example.com` and nothing else; the third prints `clean`.
6. Keep the fixture small enough to review (`limit=`, a filter); a response that lists the
   organisation's records is data, so prefer the narrowest query that shows the shape.
   Reference it from a test with the `replay_fixture("<endpoint>", "<case>")` fixture and
   call through `client_for("demo")` or a task with `org="demo"`.
