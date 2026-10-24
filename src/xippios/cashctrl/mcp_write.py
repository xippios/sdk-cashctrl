"""Write server for CashCtrl.

``tasks_write.__all__`` as confirm-gated tools, behind a separate entry point,
``xippios-cashctrl-mcp-write``, so read-only clients never see write tools
(conventions §8). ``--org <name>`` locks it to one organisation (``_cli``); ``--http``
serves it on a loopback ``--host`` only, unless ``--allow-remote`` is passed, since it
carries no authentication. No logic lives here (ADR-0001).
"""

from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import TenantLock, build_server

from xippios.cashctrl import tasks_write
from xippios.cashctrl._cli import serve
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl write tools via xippios. "
    "Every tool takes org, the name of a configured organisation. "
    "Every tool returns a preview unless confirm=true is passed. "
    "Call it once without confirm, show the preview, then confirm."
)


def build(tenant_lock: TenantLock | None = None) -> MCPServer:
    """The write server, locked to one organisation when ``tenant_lock`` is given."""
    return build_server(
        SOURCE,
        [getattr(tasks_write, name) for name in tasks_write.__all__],
        name="xippios-cashctrl-write",
        version=__version__,
        instructions=INSTRUCTIONS,
        read_only=False,
        tenant_lock=tenant_lock,
    )


server = build()


def run() -> None:
    """Run the write server: stdio by default, ``--http`` for HTTP, ``--org`` to lock it."""
    serve(server, build)
