"""MCP server for CashCtrl.

Every task in ``tasks.__all__`` is a read-only tool, but those ``tasks.BULK_TASKS``
names, which core skips: the server is passed ``tasks.__all__`` whole (ADR-0019). No
logic lives here (ADR-0001). Entry point: ``xippios-cashctrl-mcp``; ``--org <name>``
binds it to one organisation (``_cli``, ``_org_lock``).
"""

from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import build_server

from xippios.cashctrl import tasks
from xippios.cashctrl._cli import serve
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl._org_lock import OrgLock, bind_tasks, instructions
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl via xippios. "
    "Tools are read-only. cashctrl_list_organisations lists the configured organisations; "
    "every other tool takes org, the name of one of them, and an unknown name is answered "
    "with the declared ones. "
    "Call the list tools (cashctrl_list_*) first to find valid ids, then query."
)


def build(lock: OrgLock | None = None) -> MCPServer:
    """The read-only server, bound to one organisation when ``lock`` is given."""
    return build_server(
        SOURCE,
        bind_tasks([getattr(tasks, name) for name in tasks.__all__], lock),
        version=__version__,
        instructions=instructions(INSTRUCTIONS, lock),
        caps=getattr(tasks, "MCP_CAPS", None),
    )


server = build()


def run() -> None:
    """Run the server: stdio by default, ``--http`` for streamable HTTP, ``--org`` to bind it."""
    # Command-line options of the source's own reach core's parser through its hooks
    # (ADR-0014): _cli.serve calls main(server, add_options=add_org, apply_options=<returns
    # the server, bound to the organisation --org names>).
    serve(server, build)
