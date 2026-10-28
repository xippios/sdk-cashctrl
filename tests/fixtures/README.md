# Recorded fixtures

`<endpoint>/<case>.json`, written by `scripts/record_fixture.py` (`/record-fixture`),
never by hand, and only ever from the demo organisation, whose books are synthetic
(`scripts/seed_demo.py`, `docs/demo-org.md`). Credentials are scrubbed, the demo host is
rewritten to `demo.cashctrl.com`, the host offline tests replay against, every e-mail
address becomes `user@example.com` and every API user tag (`API:` and the first four
characters of a key, in `createdBy` and `lastUpdatedBy`) becomes `API:REDACTED`, and
the text value of every token-like body field (`hash`, `token`, `secret`, `apiKey`, by
name in any case; `order/read.json` sends `hash`) and of every personal identifier the
package keeps out of its projections (`ssn`, `iban`, `qrIban`, ADR-0017;
`person/list.json` sends `ssn` and `iban`, `location/list.json` `iban` and `qrIban`, only
ever `null`) becomes `REDACTED`, in memory before the file is written. The
final check refuses any other tag in any case and position, the key's first four
characters on their own as a possible key prefix, and any value but `null` or `REDACTED`
under a token-like or identifier name, in a write's form body and its JSON values too; a
compound name such as `publicHash` is written for review.
Bodies that are not UTF-8 text, methods other than GET and POST, a POST to anything but
the nine write paths the write tools call, a create without `xippios-live`, and
endpoints other than `.json` are refused. A write's fixture holds the request body too
(core records it), scrubbed and checked like the rest; the write fixtures of 2026-10-24
record a journal entry and a person marked `xippios-live`, created, read, updated and
deleted again in that order, and those of 2026-10-27 the order 20, created, read,
updated, read again and deleted. Still grep before committing:

```bash
grep -rniE 'api[_-]?key|token|secret' tests/fixtures
grep -rhoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' tests/fixtures | sort -u
grep -rhoiE 'API:[A-Za-z0-9]+' tests/fixtures | sort -u
grep -rhoiE '(hash|token|secret|api[_-]?key)\\?": *\\?"[^"\\]*' tests/fixtures | sort -u
grep -rhoiE --include='*.json' '\\?"(ssn|iban|qr[_-]?iban)\\?" *: *[^,}]*' tests/fixtures | grep -cvE ': *(null|\\?"REDACTED\\?")$'
grep -rhoiE --include='*.json' '(ssn=|iban%22%3A)[^&"]*' tests/fixtures | grep -cvE '(=|%3A)(REDACTED|null|%22REDACTED%22[^&"]*)$'
```

The last two count, without printing them, the values of `ssn`, `iban` and `qrIban`
that are neither `null` nor `REDACTED`, in the JSON bodies and in a write's form body;
both print `0`.
