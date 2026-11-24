# Layout

The files that every source of the family holds are laid out once, in the tree of
sdk-template's README,
[What gets generated](https://github.com/xippios/sdk-template/blob/main/README.md#what-gets-generated).
This file holds what `xippios-cashctrl` adds to that tree, a module, a task file, a
script or a test of its own, each with what it holds, and the change that adds one updates it.

The import path is `xippios.cashctrl` (sdk-core ADR-0006); `src/xippios/` is a
namespace package.
Where the API's operation ids repeat across its services, `api/` keeps one module per service
instead, named after the service, and this file says so (conventions §2).

```
src/xippios/cashctrl/api/
  <operation>.py   one module per operation, named after its path with each / as _ and its
                   file suffix dropped, but for a suffix that tells operations on one path
                   apart, kept as the last word, .json never (conventions §2):
                   journal_list.py for journal/list.json, journal_list_csv.py for
                   journal/list.csv, report_collection_download_annualreport.py for
                   report/collection/download_annualreport.pdf, the one format of its path
  _download.py     the file operations' one download: core's download into a file beside
                   dest, and the refusal sent as JSON under HTTP 200, which core cannot see
  _filter.py       the filter parameter of the list operations, encoded once
  _form.py         the form bodies of the writes, encoded once, and post_form, which sends them
  _params.py       the query parameters of the list operations, encoded once
scripts/
  record_fixture.py  records one exchange with the demo organisation, sent once by core's
                     send_once; core's Scrub, then its own TenantScrub (host, encoded and
                     JSON checks) and scrub_text
  seed_demo.py       seeds a fresh, empty demo organisation with synthetic books
                     (docs/demo-org.md); --discovery adds one custom field and one cost centre
tests/
  fixtures/        recorded responses, <wrapper>/<case>.json, never hand-written
  test_tasks_write.py  the write tasks: previews send nothing, writes replay, updates fail
                   closed; the write server's own test (core's assert_write_tools)
  test_downloads.py  the file tasks on synthetic bytes mounted by respx; a refusal leaves no file
  test_contract.py the package contract's own part: ENV_VARS names the organisations and
                   their pair, secret
  test_entry_points.py  the servers' entry points, -read and -write, their one name and the
                   text that names them
  test_org_lock.py the --org lock's wiring: bound tasks, both entry points, through core's mcp_call
  test_registry.py organisation declaration, lookup and one client per organisation
  test_key_resolution.py  keys resolved as in production: placeholder_api_key pins nothing
  test_errors.py   classify, RequestRejected and the recorded refusals
  test_record_fixture.py  the recorder never writes the demo host, subdomain or key
  test_seed_demo.py       the seeder refuses unsafe states before any write, offline
  test_refresh_upstream.py  the capture script's declaration and hooks on core's frame, offline
  test_observed.py  OBSERVED.md's notes and probes
  test_claude_md.py  CLAUDE.md stays under 37,000 characters
docs/
  upstream/OBSERVED.md  what CashCtrl was seen doing beside its documentation, each note
                   with its probe
  demo-org.md      the synthetic demo organisation: why, how to create and seed it, its books
  write-tools.md   how a write tool is built and tested
```
