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

**The demo organisation is synthetic.** It holds invented books only, seeded by
`scripts/seed_demo.py` and described in `docs/demo-org.md` (both on the seed branch,
PR #4, merging separately): placeholder companies, `.example` addresses, invented
amounts. Any module and any amount may therefore be recorded. If the demo pair ever
points at an organisation that is not that synthetic one, stop: never record from it.
These policies stand all the same, and each refusal writes nothing and exits non-zero:

- **GET only.** Any other `--method` is refused before a request is sent. The recorder
  for the write tools will add writes deliberately; never work around this.
- **`.json` only.** An endpoint without the extension (`account/balance`,
  `account/costcenter/balance`, `fiscalperiod/result`, `setting/get`) answers a bare
  number or a document, and an export (`.pdf`, `.xlsx`, `.csv`, `.zip`) a file; both
  are refused before a request is sent.
- **No e-mail addresses.** Every e-mail address in the URL, the headers and the body
  (`createdBy`, `lastUpdatedBy`, HTML fields such as `notes`) becomes
  `user@example.com`, also when `@` is written `%40`, `&#64;`, `&#x40;` or `&commat;`;
  `SYSTEM` stays. `createdBy` may carry the address of the real user who wrote a record.
- **No API user tags.** CashCtrl names an API user in `createdBy` and `lastUpdatedBy` as
  `API:` and the first four characters of its key (observed on the records
  `scripts/seed_demo.py` wrote). Every such tag becomes `API:REDACTED`, and the final
  check refuses any other.

1. The demo pair comes from direnv in `~/github/sdk`. Confirm it without printing it:
   `direnv exec ~/github/sdk sh -c '[ -n "$CASHCTRL_DEMO_SUBDOMAIN" ] && [ -n "$CASHCTRL_DEMO_API_KEY" ] && echo ok'`.
2. Find the request path and parameters in `docs/upstream/` and in the wrapper under
   `src/xippios/cashctrl/api/`. Parameters are named as upstream names them (`fiscalPeriodId`).
   Recordings are read-only `.json` endpoints (`list.json`, `read.json`). Exports (PDF,
   Excel, ZIP) are out of scope, and the recorder also refuses a body that is not UTF-8
   text, because it can be neither scrubbed nor reviewed.
3. Record, from the repository root:

   ```bash
   direnv exec ~/github/sdk uv run scripts/record_fixture.py <endpoint> <case> [key=value ...]
   ```

   It builds the fixture in memory with core's `fixture_from_response` (credentials
   scrubbed), replaces the demo host with `demo.cashctrl.com` everywhere in it (the host
   offline tests replay against), every e-mail address with `user@example.com` and
   every API user tag with `API:REDACTED`, checks it, and only then writes `tests/fixtures/<endpoint>/<case>.json`
   (`account/read.json` becomes `account_read/`). It prints only the status and that
   URL. `--wrong-key` sends an invalid key instead of the real one, to record a 401.
   Error cases (an unknown id, a refusal) are worth recording; the recorder keeps them
   instead of raising.
4. The check runs on the scrubbed fixture before the write: if the real subdomain, the
   real key, an e-mail address other than `user@example.com` or an API user tag other
   than `API:REDACTED` is in it, nothing is written and the script exits non-zero; if a key-like name carries a value other than
   `REDACTED`, it writes the file and exits non-zero for review. Either way, stop and
   report what it named; never print the file to find out.
5. Check again before committing, never echoing a value:

   ```bash
   grep -rniE 'api[_-]?key|token|secret|authorization|password' tests/fixtures
   grep -rhoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' tests/fixtures | sort -u
   direnv exec ~/github/sdk sh -c 'git grep -n --untracked -i -- "$CASHCTRL_DEMO_SUBDOMAIN" >/dev/null && echo LEAK || echo clean'
   ```

   The first prints nothing but `REDACTED` values (and the README's own example line);
   the second prints `user@example.com` and nothing else; the third prints `clean`.
   `grep -rhoE 'API:[A-Za-z0-9]+' tests/fixtures | sort -u` prints `API:REDACTED` at most.
6. Keep the fixture small enough to review, well under 40 KB (`limit=`, a filter, a
   query): prefer the narrowest query that shows the shape. The default chart of
   accounts (139 accounts) is too large for one fixture; narrow `account/list.json`.
   Reference it from a test with the `replay_fixture("<endpoint>", "<case>")` fixture and
   call through `client_for("demo")` or a task with `org="demo"`.
