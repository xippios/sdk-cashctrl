"""MCP server for CashCtrl.

Every task in ``tasks.__all__`` is a read-only tool, but those ``tasks.BULK_TASKS``
names (``tool_functions``, sdk-core ADR-0040). No logic lives here (sdk-core ADR-0001).
Entry point: ``xippios-cashctrl-mcp-read``.

``--org <name>`` binds it to one tenant (core's ``serve_tenants``), and ``mcp_write.py``'s
server the same way. The lock is no middleware but a wrapper:
``build(TenantLock(TENANTS, org))`` returns the tool set whose tasks core's ``bind_tasks``
binds, one tool per task with ``org`` bound at build, the same ``__name__`` (the tool
names and the ``MCP_CAPS`` keys stay), the docstring without its ``org`` line and a
signature without ``org``. Its instructions are ``BOUND_INSTRUCTIONS``, without the clause
that a tool takes ``org``, and core ends them with the sentence that names the
organisation; ``list_organisations`` lists the bound organisation alone, with
``meta.tenant`` ``None``.

The package contract (conventions §8; sdk-core ADR-0026, amendment 2026-11-18, points c and d):
``build()`` returns the tool set a host serves as this entry point does, with the caps
and the option hooks ``tasks.py`` defines, ``MCP_CAPS``, ``mcp_add_options`` and
``mcp_apply_options``; ``server`` is built from it, and ``ENV_VARS`` beside ``SOURCE``
names the variables the package reads.
"""

from xippios.core import TenantLock, bind_tasks, tenant_instructions
from xippios.core.mcp import ToolSet, build_server, serve_tenants, tool_functions

from xippios.cashctrl import tasks
from xippios.cashctrl._client import ENV_VARS, SOURCE, TENANTS, check_org
from xippios.cashctrl._version import __version__

__all__ = ["ENV_VARS", "SOURCE", "build", "run", "server"]

INSTRUCTIONS = (
    "CashCtrl via xippios. "
    "Tools are read-only. cashctrl_list_organisations lists the configured organisations; "
    "every other tool takes org, the name of one of them, and an unknown name is answered "
    "with the declared ones. "
    "Call the list tools (cashctrl_list_*) first to find valid ids, then query."
)
BOUND_INSTRUCTIONS = (
    "CashCtrl via xippios. "
    "Tools are read-only. "
    "Call the list tools (cashctrl_list_*) first to find valid ids, then query."
)
"""The text of a server ``lock`` binds, whose tools take no tenant: core's sentence names it."""


def build(lock: TenantLock | None = None) -> ToolSet:
    """The read-only tool set, bound to one tenant when ``lock`` is given."""
    return ToolSet(
        SOURCE,
        bind_tasks(tool_functions(tasks), lock),
        caps=getattr(tasks, "MCP_CAPS", None),
        instructions=tenant_instructions(INSTRUCTIONS, lock, bound=BOUND_INSTRUCTIONS),
        version=__version__,
        add_options=getattr(tasks, "mcp_add_options", None),
        apply_options=getattr(tasks, "mcp_apply_options", None),
    )


server = build_server(build())


def run() -> None:
    """Run the server: stdio by default, ``--http`` for streamable HTTP.

    ``--org <name>`` binds it to one tenant.
    """
    serve_tenants(server, build, TENANTS, noun="organisation", check=check_org)
