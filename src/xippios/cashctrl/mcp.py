"""MCP server for CashCtrl.

Every task in ``tasks.__all__`` is a read-only tool, but those ``tasks.BULK_TASKS``
names (``tool_functions``, ADR-0019). No logic lives here (ADR-0001). Entry point:
``xippios-cashctrl-mcp-read``; ``--org <name>`` binds it to one organisation (core's
``serve_tenants``).
"""

from xippios.core import TenantLock, bind_tasks, tenant_instructions
from xippios.core.mcp import ToolSet, build_server, serve_tenants, tool_functions

from xippios.cashctrl import tasks
from xippios.cashctrl._client import SOURCE, TENANTS, check_org
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl via xippios. "
    "Tools are read-only. cashctrl_list_organisations lists the configured organisations; "
    "every other tool takes org, the name of one of them, and an unknown name is answered "
    "with the declared ones. "
    "Call the list tools (cashctrl_list_*) first to find valid ids, then query."
)


def build(lock: TenantLock | None = None) -> ToolSet:
    """The read-only tool set, bound to one organisation when ``lock`` is given."""
    return ToolSet(
        SOURCE,
        bind_tasks(tool_functions(tasks), lock),
        caps=getattr(tasks, "MCP_CAPS", None),
        instructions=tenant_instructions(INSTRUCTIONS, lock),
        version=__version__,
    )


server = build_server(build())


def run() -> None:
    """Run the server: stdio by default, ``--http`` for streamable HTTP, ``--org`` to bind it."""
    serve_tenants(server, build, TENANTS, noun="organisation", check=check_org)
