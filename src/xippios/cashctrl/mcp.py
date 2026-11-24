"""MCP server for CashCtrl.

Every task in ``tasks.__all__`` is a read-only tool, but those ``tasks.BULK_TASKS``
names (``tool_functions``, sdk-core ADR-0040). No logic lives here (sdk-core ADR-0001). Entry point:
``xippios-cashctrl-mcp-read``.
``--org <name>`` binds it to one tenant.

The package contract (conventions §8; sdk-core ADR-0063, decisions 7 and 8): ``build()``
returns the tool set that core builds from ``tasks.py``, with what that module declares for
the server, ``server`` is built from it, and ``ENV_VARS`` beside ``SOURCE`` names the
variables the package reads. No line here is the source's: its server's text, caps and
options stand in ``tasks.py``.
"""

from xippios.core import TenantLock
from xippios.core.mcp import ToolSet, build_server, main

from xippios.cashctrl import tasks
from xippios.cashctrl._client import ENV_VARS, SOURCE, TENANTS, check_org
from xippios.cashctrl._version import __version__

__all__ = ["ENV_VARS", "SOURCE", "build", "run", "server"]


def build(lock: TenantLock | None = None) -> ToolSet:
    """The read-only tool set of ``tasks.py``, bound to one tenant when ``lock`` is given."""
    return ToolSet.from_tasks(SOURCE, tasks, version=__version__, lock=lock)


server = build_server(build())


def run() -> None:
    """Run the server: stdio by default, ``--http`` for streamable HTTP.

    ``--org <name>`` binds it to one tenant.
    """
    main(build, tenants=TENANTS, check=check_org)
