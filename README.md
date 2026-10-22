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

Set `CASHCTRL_API_KEY` in the environment. Nothing is read from files.

## 30-second example

```python
from xippios.cashctrl import tasks

# result = tasks.<task>(...)
# result.data, result.meta.retrieved_at, result.meta.request
```

Task functions are listed in the status table below as they are added.

## MCP

```json
{
  "mcpServers": {
    "cashctrl": {
      "command": "uvx",
      "args": ["--from", "xippios-cashctrl[mcp]", "xippios-cashctrl-mcp"],
      "env": { "CASHCTRL_API_KEY": "..." }
    }
  }
}
```

Tools are read-only and named `cashctrl_<verb>_<noun>`. Results are capped at
200 rows or 64 KB with a note on how to narrow the query. `--http` serves streamable
HTTP instead of stdio.

Write tools run in a separate server, `xippios-cashctrl-mcp-write`; every write
tool previews its change unless called with `confirm=true`.

## Status

| Upstream operation | Task function | MCP tool | Status |
| --- | --- | --- | --- |
| (none yet) | | | |

## Upstream terms and attribution

Data comes from CashCtrl (https://cashctrl.com) under its own terms of use;
this package adds no rights to it. Documentation snapshot: `docs/upstream/`.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
