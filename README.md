# xippios-cashctrl

Typed Python client, MCP server and FastAPI routes for
[CashCtrl](https://cashctrl.com), part of the
[xippios SDK family](https://github.com/xippios). Names and semantics follow the
upstream documentation; every response carries release metadata (source, endpoint,
retrieved_at, published_at, vintage).

## Install

```bash
uv add xippios-cashctrl            # client only
uv add "xippios-cashctrl[mcp]"     # + MCP server
uv add "xippios-cashctrl[http]"    # + FastAPI router
```

## Configuration

CashCtrl serves every organisation from its own subdomain
(`https://<subdomain>.cashctrl.com/api/v1`) and gives every organisation its own API
user. The package therefore works with named organisations, declared in the environment;
nothing is read from files.

| Variable | Meaning |
| --- | --- |
| `CASHCTRL_ORGS` | the organisations, comma-separated, lower-case letters, digits and `_`: `acme,acme_test` |
| `CASHCTRL_<NAME>_SUBDOMAIN` | per organisation, the subdomain: `CASHCTRL_ACME_SUBDOMAIN=acme` |
| `CASHCTRL_<NAME>_API_KEY` | per organisation, the API user's key (Settings → Users & Roles) |
| `CASHCTRL_DEMO_SUBDOMAIN`, `CASHCTRL_DEMO_API_KEY` | the reserved organisation `demo`, used by this repository's tests; never listed in `CASHCTRL_ORGS` |

Every task and tool takes `org`, the name of one declared organisation, as its first
parameter. Each organisation gets its own client, key and rate limit (60 requests per
minute, self-imposed); nothing spans organisations. A deployment reaches exactly the
organisations its environment declares.

## 30-second example

```python
from xippios.cashctrl import tasks
from xippios.cashctrl.models import Filter

# "demo" stands for any declared organisation; the first argument is always org.
periods = tasks.list_fiscal_periods("demo")
current = next(period for period in periods.data if period.is_current)

accounts = tasks.list_accounts("demo", fiscal_period_id=current.id, only_active=True)
for account in accounts.data:
    print(account.number, account.name, account.end_amount)  # a Decimal, or None

cash = tasks.list_accounts("demo", filter=[Filter(comparison="eq", field="number", value="1000")])
record = tasks.get_account("demo", cash.data[0].id)
print(record.meta.endpoint, record.meta.request, record.meta.retrieved_at)
```

Every task returns `Result[T]`: `data` holds models that mirror CashCtrl's payloads
(snake_case attributes, serialised under upstream's camelCase names), `meta` the upstream
operation, the parameters sent and when they were fetched. Async twins are named
`<task>_async`. The tasks are listed in the status table below.

## MCP

```json
{
  "mcpServers": {
    "cashctrl": {
      "command": "uvx",
      "args": ["--from", "xippios-cashctrl[mcp]", "xippios-cashctrl-mcp", "--org", "acme"],
      "env": {
        "CASHCTRL_ORGS": "acme",
        "CASHCTRL_ACME_SUBDOMAIN": "acme",
        "CASHCTRL_ACME_API_KEY": "..."
      }
    }
  }
}
```

`--org acme` locks the server to one organisation: it stops at startup unless `acme` is
declared with a well-formed subdomain, its instructions name the organisation, and a
tool call naming another is refused before it reaches CashCtrl. Without `--org`, a
server serves every declared organisation and the agent picks one per call. Tools are
read-only and named `cashctrl_<verb>_<noun>`. Results are capped at 200 rows or 64 KB
with a note on how to narrow the query. `--http` serves streamable HTTP instead of stdio.

Write tools run in a separate server, `xippios-cashctrl-mcp-write`; every write
tool previews its change unless called with `confirm=true`. It takes `--org` too.

## HTTP

`xippios.cashctrl.http.router` is a FastAPI router the consumer mounts. It has no lock:
every route takes `org` and the consumer passes it explicitly on each request. A
deployment that must reach one organisation only declares only that one. A task whose
parameters are all scalars is a `GET /cashctrl/<task>` with query parameters;
`list_accounts`, whose `filter` is a list, is a `POST` with a JSON body keyed by
parameter name. The MCP entry points quiet httpx's request log; the router does not, so
a consumer that logs at INFO logs httpx's request lines, whose URLs carry the
organisation's host (its subdomain): set the `httpx` logger to WARNING.

## Status

| Upstream operation | Task function | MCP tool | Status |
| --- | --- | --- | --- |
| `GET fiscalperiod/list.json` (List fiscal periods) | `list_fiscal_periods` | `cashctrl_list_fiscal_periods` | available |
| `GET currency/list.json` (List currencies) | `list_currencies` | `cashctrl_list_currencies` | available |
| `GET tax/list.json` (List tax codes) | `list_tax_codes` | `cashctrl_list_tax_codes` | available |
| `GET account/list.json` (List accounts) | `list_accounts` | `cashctrl_list_accounts` | available; HTTP route is `POST` |
| `GET account/read.json` (Read account) | `get_account` | `cashctrl_get_account` | available |

`lang` (`de`, `fr`, `it`, `en`), which upstream takes on every request and which matters
mostly for error messages and exports, is not exposed yet. `list_accounts` checks `dir`
(`ASC`, `DESC`) and each filter's `comparison` (`eq`, `like`, `gt`, `lt`) before
anything is sent, since upstream silently ignores values it does not know; both are
typed as these value sets, so the tool schema lists them. A filter is a `Filter` or,
from Python, a mapping with the same keys.

## Upstream terms and attribution

Data comes from CashCtrl (https://cashctrl.com) under its own terms of use;
this package adds no rights to it. Documentation snapshot: `docs/upstream/`.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
