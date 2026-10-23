"""The ``--org`` lock and the process setup, shared by both MCP servers.

A server started with ``--org <name>`` serves that one organisation. The name must be
declared and its subdomain present and well-formed, or the server stops at startup with
exit status 2. A ``tools/call`` whose ``org`` argument names another organisation is
answered with the family's error text (``error: InvalidRequestError: ...``) and never
reaches the tool; every other request and notification passes untouched. A call without
``org`` is left to the tool's own argument validation. The server instructions gain one
sentence naming the organisation. Without ``--org`` a server serves every organisation
its environment declares, chosen per call. The HTTP router has no lock: a deployment that
needs one declares only that organisation.

Either way, ``main`` keeps httpx's request lines out of the server's log: they carry the
organisation's host, which is treated like a key.
"""

import argparse
import logging
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerMiddleware, ServerRequestContext
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent
from xippios.core import InvalidRequestError, XippiosError
from xippios.core.mcp import build_parser, error_to_text
from xippios.core.mcp import main as serve

from xippios.cashctrl._client import SOURCE, client_for

__all__ = ["announce_lock", "main", "org_lock", "parse_org", "quiet_request_logging"]

ORG_HELP = "serve only this organisation, e.g. demo; tool calls naming another are refused"
LOCKED = "This server is locked to organisation {org}; every tool call must pass org={org}."
REQUEST_LOGGERS = ("httpx", "httpcore")


def org_lock(org: str) -> ServerMiddleware[Any]:
    """Middleware for ``server.middleware`` that refuses tool calls for any other organisation.

    The middleware API of ``mcp`` is provisional and ``mcp`` has no upper pin: the
    in-process ``mcp.Client(server)`` tests in ``tests/test_org_lock.py`` are the guard.

    Args:
        org: The organisation the server is locked to, e.g. ``"demo"``.
    """

    async def lock(ctx: ServerRequestContext[Any, Any], call_next: CallNext) -> HandlerResult:
        if ctx.method == "tools/call":
            arguments = (ctx.params or {}).get("arguments")
            if isinstance(arguments, Mapping) and "org" in arguments and arguments["org"] != org:
                error = InvalidRequestError(
                    f"this server serves organisation {org!r} only; "
                    f"call the tool with org={org!r}, not {arguments['org']!r}",
                    source=SOURCE,
                )
                return CallToolResult(content=[TextContent(type="text", text=error_to_text(error))])
        return await call_next(ctx)

    return lock


def announce_lock(server: MCPServer, org: str) -> None:
    """Append one sentence naming ``org`` to the instructions ``server`` gives clients."""
    # MCPServer.instructions is read-only; the low-level server's attribute is what the
    # initialize and server/discover answers carry. Guarded by the in-process client
    # tests in tests/test_org_lock.py, like the middleware.
    lowlevel = server._lowlevel_server
    lowlevel.instructions = " ".join(filter(None, [lowlevel.instructions, LOCKED.format(org=org)]))


def quiet_request_logging() -> None:
    """Keep httpx's request lines, and with them the organisation's host, out of the log.

    Building an ``MCPServer`` configures root logging at INFO on stderr, and httpx logs
    every request there with its full URL (``HTTP Request: GET https://<subdomain>...``).
    httpx and httpcore are raised to WARNING; their warnings and errors still show.
    """
    for name in REQUEST_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def parse_org(prog: str, argv: Sequence[str]) -> tuple[str | None, list[str]]:
    """Split ``--org`` off a command line and return it with the arguments for core's ``main``.

    The whole line is first checked by core's parser plus ``--org``, so ``--help`` lists
    every option and a typo fails as usual. ``--org`` is checked as ``client_for`` checks
    it: an undeclared organisation (``InvalidRequestError``) or a missing or malformed
    subdomain (``ConfigError``) exits with status 2 and the message on stderr, before
    anything is served. The key is still read on the first request.
    """
    parser = build_parser(prog)
    parser.add_argument("--org", help=ORG_HELP)
    org = parser.parse_args(argv).org
    only_org = argparse.ArgumentParser(add_help=False)
    only_org.add_argument("--org")
    rest = only_org.parse_known_args(argv)[1]
    if org is not None:
        try:
            client_for(org)
        except XippiosError as exc:
            parser.error(str(exc))
    return org, rest


def main(server: MCPServer, argv: Sequence[str] | None = None) -> None:
    """Core's ``main`` plus ``--org <name>``: lock ``server`` to one organisation, then run it.

    Args:
        server: A server from ``build_server``.
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.
    """
    quiet_request_logging()
    org, rest = parse_org(server.name, sys.argv[1:] if argv is None else argv)
    if org is not None:
        server.middleware.append(org_lock(org))
        announce_lock(server, org)
    serve(server, rest)
