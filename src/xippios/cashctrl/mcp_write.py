"""Write server for CashCtrl.

``tasks_write.__all__`` as confirm-gated tools, behind a separate entry point,
``xippios-cashctrl-mcp-write``, so read-only clients never see write tools
(conventions §8). ``--org <name>`` binds it to one organisation (``_cli``); ``--http``
serves it on a loopback ``--host`` only, unless ``--allow-remote`` is passed, since it
carries no authentication. No logic lives here (ADR-0001).
"""

from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import build_server

from xippios.cashctrl import tasks_write
from xippios.cashctrl._cli import serve
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl._org_lock import OrgLock, bind_tasks, instructions
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl write tools via xippios. "
    "Every tool takes org, the name of a configured organisation. "
    "Every tool returns a preview unless confirm=true is passed. "
    "Call it once without confirm, show the preview, then confirm."
)


def build(lock: OrgLock | None = None) -> MCPServer:
    """The write server, bound to one organisation when ``lock`` is given."""
    return build_server(
        SOURCE,
        bind_tasks([getattr(tasks_write, name) for name in tasks_write.__all__], lock),
        name="xippios-cashctrl-write",
        version=__version__,
        instructions=instructions(INSTRUCTIONS, lock),
        caps=getattr(tasks_write, "MCP_CAPS", None),
        read_only=False,
    )


server = build()


def run() -> None:
    """Run the write server: stdio by default, ``--http`` for HTTP, ``--org`` to bind it."""
    serve(server, build)
