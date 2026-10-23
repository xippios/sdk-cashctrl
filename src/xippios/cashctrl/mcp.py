"""MCP server for CashCtrl.

Every task in ``tasks.__all__`` is a read-only tool. No logic lives here (ADR-0001).
Entry point: ``xippios-cashctrl-mcp``; ``--org <name>`` locks it to one organisation.
"""

from xippios.core.mcp import build_server

from xippios.cashctrl import tasks
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl._org_lock import main
from xippios.cashctrl._version import __version__

INSTRUCTIONS = (
    "CashCtrl via xippios. "
    "Tools are read-only. Every tool takes org, the name of a configured organisation; "
    "an unknown name is answered with the declared ones. "
    "Call the list tools (cashctrl_list_*) first to find valid ids, then query."
)

server = build_server(
    SOURCE,
    [getattr(tasks, name) for name in tasks.__all__],
    version=__version__,
    instructions=INSTRUCTIONS,
)


def run() -> None:
    """Run the server: stdio by default, ``--http`` for streamable HTTP, ``--org`` to lock it."""
    main(server)
