"""The --org lock: tool calls for another organisation never reach the tool.

The tool is called through ``mcp.Client`` connected in-process, which runs the server's
middleware chain. ``xippios.core.testing.mcp_call`` uses ``MCPServer.call_tool`` and
bypasses the middleware, so it cannot test a lock.
"""

import json
import logging
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
import respx
from mcp import Client
from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import build_server

from xippios.cashctrl import mcp, mcp_write
from xippios.cashctrl._client import DEMO, ORGS_ENV, subdomain_env
from xippios.cashctrl._org_lock import main, org_lock, parse_org

pytestmark = pytest.mark.anyio

TOOL = "cashctrl_echo_org"
REQUEST_LOGGERS = ("httpx", "httpcore")


def locked_server(
    calls: list[str], org: str | None = "demo", instructions: str | None = None
) -> MCPServer:
    async def echo_org(org: str) -> dict[str, str]:
        """Return the organisation the tool was called for.

        Args:
            org: Organisation name, e.g. ``demo``.
        """
        calls.append(org)
        return {"org": org}

    server = build_server("cashctrl", [echo_org], instructions=instructions)
    if org is not None:
        server.middleware.append(org_lock(org))
    return server


async def call(server: MCPServer, arguments: dict[str, Any]) -> tuple[bool, str]:
    async with Client(server) as client:
        result = await client.call_tool(TOOL, arguments)
    text = result.content[0]
    assert text.type == "text"
    return result.is_error, text.text


async def test_the_locked_org_passes() -> None:
    calls: list[str] = []
    is_error, text = await call(locked_server(calls), {"org": "demo"})
    assert not is_error
    assert json.loads(text) == {"org": "demo"}
    assert calls == ["demo"]


@pytest.mark.parametrize("other", ["other", "DEMO", "", None])
async def test_another_org_is_refused_without_calling_the_tool(other: str | None) -> None:
    calls: list[str] = []
    is_error, text = await call(locked_server(calls), {"org": other})
    assert text.startswith("error: InvalidRequestError: ")
    assert "org='demo'" in text
    assert not is_error, "the same shape as every tool error: text, not an MCP error"
    assert calls == []


async def test_a_missing_org_is_left_to_the_tool_validation() -> None:
    calls: list[str] = []
    is_error, text = await call(locked_server(calls), {})
    assert is_error
    assert "org" in text
    assert not text.startswith("error: InvalidRequestError")
    assert calls == []


async def test_listing_tools_is_unaffected() -> None:
    async with Client(locked_server([])) as client:
        tools = await client.list_tools()
    assert [tool.name for tool in tools.tools] == [TOOL]


def test_parse_org_splits_off_org_and_keeps_core_options() -> None:
    assert parse_org("p", ["--org", "demo", "--http", "--port", "9000"]) == (
        "demo",
        ["--http", "--port", "9000"],
    )
    assert parse_org("p", ["--host", "0.0.0.0", "--org=demo"]) == ("demo", ["--host", "0.0.0.0"])
    assert parse_org("p", ["--http"]) == (None, ["--http"])


def test_an_undeclared_org_fails_fast(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        parse_org("xippios-cashctrl", ["--org", "nope", "--http"])
    assert info.value.code == 2
    err = capsys.readouterr().err
    expected = "unknown organisation 'nope'; declared organisations: demo"
    assert f"xippios-cashctrl: error: {expected}" in err
    assert "placeholder" not in err


def test_help_lists_org_and_core_options(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        parse_org("xippios-cashctrl", ["--help"])
    assert info.value.code == 0
    out = capsys.readouterr().out
    for option in ("--org", "--http", "--host", "--port"):
        assert option in out


def test_unknown_options_still_fail() -> None:
    with pytest.raises(SystemExit) as info:
        parse_org("p", ["--org", "demo", "--nope"])
    assert info.value.code == 2


async def test_main_locks_the_server_then_hands_over_to_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    server = locked_server(calls, org=None)
    runs: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(server, "run", lambda transport, **kw: runs.append((transport, kw)))
    before = len(server.middleware)
    main(server, ["--org", "demo", "--http", "--port", "9001"])
    assert runs == [("streamable-http", {"host": "127.0.0.1", "port": 9001})]
    assert len(server.middleware) == before + 1
    _, text = await call(server, {"org": "other"})
    assert text.startswith("error: InvalidRequestError: ")
    assert calls == []


def test_main_without_org_serves_unlocked(monkeypatch: pytest.MonkeyPatch) -> None:
    server = locked_server([], org=None)
    runs: list[str] = []
    monkeypatch.setattr(server, "run", lambda transport, **kw: runs.append(transport))
    before = len(server.middleware)
    main(server, [])
    assert runs == ["stdio"]
    assert len(server.middleware) == before


@pytest.mark.parametrize("module", [mcp, mcp_write], ids=["mcp", "mcp_write"])
def test_both_entry_points_fail_fast_on_an_undeclared_org(
    module: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["entry-point", "--org", "nope"])
    monkeypatch.setattr(module.server, "run", lambda *a, **kw: pytest.fail("served"))
    before = len(module.server.middleware)
    with pytest.raises(SystemExit) as info:
        module.run()
    assert info.value.code == 2
    assert "unknown organisation 'nope'" in capsys.readouterr().err
    assert len(module.server.middleware) == before


@pytest.mark.parametrize(
    ("value", "message"),
    [("", "CASHCTRL_XA_SUBDOMAIN is not set"), ("evil.com/x?", "CASHCTRL_XA_SUBDOMAIN is not a")],
)
def test_a_missing_or_malformed_subdomain_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], value: str, message: str
) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa")
    monkeypatch.setenv(subdomain_env("xa"), value)
    with pytest.raises(SystemExit) as info:
        parse_org("xippios-cashctrl", ["--org", "xa"])
    assert info.value.code == 2
    err = capsys.readouterr().err
    assert f"xippios-cashctrl: error: {message}" in err
    assert "evil.com" not in err


async def test_a_locked_server_names_the_organisation_in_its_instructions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = locked_server([], org=None, instructions="CashCtrl via xippios.")
    monkeypatch.setattr(server, "run", lambda *a, **kw: None)
    main(server, ["--org", DEMO])
    expected = (
        "CashCtrl via xippios. "
        "This server is locked to organisation demo; every tool call must pass org=demo."
    )
    assert server.instructions == expected
    async with Client(server) as client:
        assert client.instructions == expected


async def test_an_unlocked_server_keeps_its_instructions(monkeypatch: pytest.MonkeyPatch) -> None:
    server = locked_server([], org=None, instructions="CashCtrl via xippios.")
    monkeypatch.setattr(server, "run", lambda *a, **kw: None)
    main(server, [])
    async with Client(server) as client:
        assert client.instructions == "CashCtrl via xippios."


@pytest.fixture
def request_loggers() -> Iterator[None]:
    """Restore the httpx and httpcore log levels that ``main`` changes for the process."""
    loggers = [logging.getLogger(name) for name in REQUEST_LOGGERS]
    levels = [logger.level for logger in loggers]
    yield
    for logger, level in zip(loggers, levels, strict=True):
        logger.setLevel(level)


@pytest.mark.usefixtures("request_loggers")
@pytest.mark.parametrize("argv", [[], ["--org", DEMO]], ids=["unlocked", "locked"])
def test_main_keeps_request_urls_out_of_the_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    respx_mock: respx.MockRouter,
    argv: list[str],
) -> None:
    """Core's ``main``, which this ``main`` hands over to, quiets httpx and httpcore.

    ``build_server`` quiets them too, so the levels are reset after building the server:
    only the call inside ``main`` can raise them again before the request.
    """
    server = locked_server([], org=None)
    for name in REQUEST_LOGGERS:
        logging.getLogger(name).setLevel(logging.NOTSET)
    monkeypatch.setattr(server, "run", lambda *a, **kw: None)
    main(server, argv)
    assert [logging.getLogger(name).level for name in REQUEST_LOGGERS] == [logging.WARNING] * 2
    respx_mock.get("https://xq-tenant.cashctrl.com/api/v1/x.json").respond(200)
    with caplog.at_level(logging.INFO):
        httpx.get("https://xq-tenant.cashctrl.com/api/v1/x.json")
    assert "xq-tenant" not in caplog.text
    assert not [record for record in caplog.records if record.name in REQUEST_LOGGERS]
