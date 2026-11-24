"""Write server for CashCtrl.

``tasks_write.__all__`` as confirm-gated tools, behind an entry point of their own,
``xippios-cashctrl-mcp-write``, so a client of the read server never sees a write
tool (conventions §8). Core builds them as a write tool set (``read_only=False``): every task
takes ``confirm: bool = False``, checked before anything is registered, and ``--http``
serves on a loopback ``--host`` only, unless ``--allow-remote`` is passed, since it
carries no authentication. No logic lives here (sdk-core ADR-0001).
``--org <name>`` binds it to one tenant.

The package contract (conventions §8; sdk-core ADR-0063, decisions 7 and 8): ``build()``
returns the write tool set that core builds from ``tasks_write.py``, with what that module
declares for the server, and ``server`` is built from it. No line here is the source's.
"""

from xippios.core import TenantLock
from xippios.core.mcp import ToolSet, build_server, main

from xippios.cashctrl import tasks_write
from xippios.cashctrl._client import ENV_VARS, SOURCE, TENANTS, check_org
from xippios.cashctrl._version import __version__

__all__ = ["ENV_VARS", "SOURCE", "build", "run", "server"]


def build(lock: TenantLock | None = None) -> ToolSet:
    """The write tool set of ``tasks_write.py``, bound to one tenant when ``lock`` is given."""
    return ToolSet.from_tasks(SOURCE, tasks_write, version=__version__, lock=lock, read_only=False)


server = build_server(build(), name="xippios-cashctrl-write")


def run() -> None:
    """Run the write server: stdio by default, ``--http`` on loopback.

    ``--org <name>`` binds it to one tenant.
    """
    main(build, tenants=TENANTS, check=check_org)
