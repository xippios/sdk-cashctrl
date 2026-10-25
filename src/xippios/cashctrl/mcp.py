"""MCP server for CashCtrl.

Every task in ``tasks.__all__`` is a read-only tool. No logic lives here (ADR-0001).
Entry point: ``xippios-cashctrl-mcp``; ``--org <name>`` locks it to one organisation
(``_cli``).
"""

from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import TenantLock, build_server

from xippios.cashctrl import tasks
from xippios.cashctrl._cli import serve
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl via xippios. "
    "Tools are read-only. cashctrl_list_organisations lists the configured organisations; "
    "every other tool takes org, the name of one of them, and an unknown name is answered "
    "with the declared ones. "
    "Call the list tools (cashctrl_list_*) first to find valid ids, then query."
)


def build(tenant_lock: TenantLock | None = None) -> MCPServer:
    """The read-only server, locked to one organisation when ``tenant_lock`` is given."""
    return build_server(
        SOURCE,
        [getattr(tasks, name) for name in tasks.__all__],
        version=__version__,
        instructions=INSTRUCTIONS,
        caps=getattr(tasks, "MCP_CAPS", None),
        tenant_lock=tenant_lock,
    )


server = build()


def run() -> None:
    """Run the server: stdio by default, ``--http`` for streamable HTTP, ``--org`` to lock it."""
    serve(server, build)
