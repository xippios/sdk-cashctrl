# Recorded fixtures

`<endpoint>/<case>.json`, written by `scripts/record_fixture.py` (`/record-fixture`),
never by hand, and only ever from the demo organisation, whose books are synthetic
(`scripts/seed_demo.py`, `docs/demo-org.md`). Credentials are scrubbed, the demo host is
rewritten to `demo.cashctrl.com`, the host offline tests replay against, every e-mail
address becomes `user@example.com` and every API user tag (`API:` and the first four
characters of a key, in `createdBy` and `lastUpdatedBy`) becomes `API:REDACTED`, in
memory before the file is written. The final check refuses any other tag in any case and
position, and the key's first four characters on their own as a possible key prefix.
Bodies that are not UTF-8 text, methods other than GET and endpoints other than `.json`
are refused. Still grep before committing:

```bash
grep -rniE 'api[_-]?key|token|secret' tests/fixtures
grep -rhoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' tests/fixtures | sort -u
grep -rhoiE 'API:[A-Za-z0-9]+' tests/fixtures | sort -u
```
