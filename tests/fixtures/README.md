# Recorded fixtures

`<endpoint>/<case>.json`, written by `scripts/record_fixture.py` (`/record-fixture`),
never by hand, and only ever from the demo organisation. Credentials are scrubbed, the
demo host is rewritten to `demo.cashctrl.com`, the host offline tests replay against, and
every e-mail address becomes `user@example.com`, in memory before the file is written.
Bodies that are not UTF-8 text, non-zero amounts, methods other than GET, endpoints
other than `.json`, and every module but account, currency, fiscalperiod and tax are
refused; `account/bank/` is refused too.
Still grep before committing:

```bash
grep -rniE 'api[_-]?key|token|secret' tests/fixtures
grep -rhoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' tests/fixtures | sort -u
```
