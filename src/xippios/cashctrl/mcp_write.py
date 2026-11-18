"""Write server for CashCtrl.

``tasks_write.__all__`` as confirm-gated tools, behind a separate entry point,
``xippios-cashctrl-mcp-write``, so read-only clients never see write tools
(conventions §8). ``--org <name>`` binds it to one organisation (core's
``serve_tenants``); ``--http`` serves it on a loopback ``--host`` only, unless
``--allow-remote`` is passed, since it carries no authentication. No logic lives here
(ADR-0001).
"""

from xippios.core import TenantLock, bind_tasks, tenant_instructions
from xippios.core.mcp import ToolSet, build_server, serve_tenants, tool_functions

from xippios.cashctrl import tasks_write
from xippios.cashctrl._client import SOURCE, TENANTS, check_org
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl write tools via xippios. "
    "Every tool takes org, the name of a configured organisation. "
    "Every tool returns a preview unless confirm=true is passed. "
    "Call it once without confirm, show the preview, then confirm."
)


def build(lock: TenantLock | None = None) -> ToolSet:
    """The write tool set, bound to one organisation when ``lock`` is given."""
    return ToolSet(
        SOURCE,
        bind_tasks(tool_functions(tasks_write), lock),
        caps=getattr(tasks_write, "MCP_CAPS", None),
        instructions=tenant_instructions(INSTRUCTIONS, lock),
        version=__version__,
        read_only=False,
    )


server = build_server(build(), name="xippios-cashctrl-write")


def run() -> None:
    """Run the write server: stdio by default, ``--http`` for HTTP, ``--org`` to bind it."""
    serve_tenants(server, build, TENANTS, noun="organisation", check=check_org)
