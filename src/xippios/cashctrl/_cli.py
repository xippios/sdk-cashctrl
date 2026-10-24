"""The ``--org`` option both MCP servers take, through core's option hooks (ADR-0014).

Core's ``main`` parses the command line once, with ``--org`` added by ``add_org``. Given
``--org <name>``, ``locked`` checks the organisation as ``client_for`` would, declared
(``TENANTS.require``) and with a well-formed subdomain (``TENANTS.field``), and returns
the server built anew with ``tenant_lock=TenantLock("org", name)``: core refuses every
tool call that names another organisation or leaves ``org`` out, and adds a sentence
naming the organisation to the instructions. An undeclared name or a missing or
malformed subdomain stops the process at startup, exit status 2, the message on stderr,
nothing served; the key is still read on the first request. Without ``--org`` the
server is served as built, for every organisation its environment declares.

Core's ``build_server`` and ``main`` keep httpx's request lines, which carry the
organisation's host, out of the log (``xippios.core.mcp.quiet_request_logging``), and
``main`` serves a write server over ``--http`` on a loopback ``--host`` only, unless
``--allow-remote`` is passed. The HTTP router has no lock: a deployment that needs one
declares only that organisation.
"""

import argparse
from collections.abc import Callable, Sequence

from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import TenantLock, main

from xippios.cashctrl._client import TENANTS

__all__ = ["ORG_HELP", "add_org", "serve"]

ORG_HELP = "serve only this organisation, e.g. demo; tool calls naming another are refused"

Build = Callable[[TenantLock | None], MCPServer]
"""Builds an adapter's server, locked to one organisation or, given ``None``, not."""


def add_org(parser: argparse.ArgumentParser) -> None:
    """Put ``--org`` on core's parser, so ``--help`` lists it and a typo fails as usual."""
    parser.add_argument("--org", help=ORG_HELP)


def serve(server: MCPServer, build: Build, argv: Sequence[str] | None = None) -> None:
    """Run ``server``, or the one ``build`` locks to ``--org``, through core's ``main``.

    Args:
        server: The adapter's unlocked server, built by ``build(None)``.
        build: Builds the adapter's server; called with the lock when ``--org`` is given.
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.
    """

    def locked(namespace: argparse.Namespace, unlocked: MCPServer) -> MCPServer:
        if namespace.org is None:
            return unlocked
        org = TENANTS.require(namespace.org)
        TENANTS.field(org, "SUBDOMAIN")
        return build(TenantLock("org", org))

    main(server, argv, add_options=add_org, apply_options=locked)
