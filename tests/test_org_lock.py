"""The --org lock: core's TenantLock, wired into core's main by ``_cli`` (ADR-0014).

Every tool call goes through ``xippios.core.testing.mcp_call_text``, an in-process
``mcp.Client``, so the lock's middleware runs as it does for a real client.
"""

import json
import logging
from typing import Any

import httpx
import pytest
import respx
from mcp import Client
from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import TenantLock, build_server
from xippios.core.testing import mcp_call_text

from xippios.cashctrl import mcp, mcp_write, tasks
from xippios.cashctrl._cli import serve
from xippios.cashctrl._client import DEMO, TENANTS

pytestmark = pytest.mark.anyio

TOOL = "cashctrl_echo_org"
LIST = "cashctrl_list_organisations"
REQUEST_LOGGERS = ("httpx", "httpcore")
REFUSED = "error: InvalidRequestError: this server is locked to org=demo; "


class EchoServers:
    """Builds servers with one tool that records the organisation it was called for."""

    def __init__(self, instructions: str | None = None) -> None:
        self.calls: list[str] = []
        self.locks: list[TenantLock | None] = []
        self.instructions = instructions

    def build(self, tenant_lock: TenantLock | None = None) -> MCPServer:
        calls = self.calls

        async def echo_org(org: str) -> dict[str, str]:
            """Return the organisation the tool was called for.

            Args:
                org: Organisation name, e.g. ``demo``.
            """
            calls.append(org)
            return {"org": org}

        self.locks.append(tenant_lock)
        return build_server(
            "cashctrl",
            [echo_org, tasks.list_organisations],
            instructions=self.instructions,
            tenant_lock=tenant_lock,
        )


@pytest.fixture
def runs(monkeypatch: pytest.MonkeyPatch) -> list[tuple[MCPServer, str, dict[str, Any]]]:
    """Every server core's ``main`` would have run, with its transport and options."""
    served: list[tuple[MCPServer, str, dict[str, Any]]] = []

    def run(self: MCPServer, transport: str, **options: Any) -> None:
        served.append((self, transport, options))

    monkeypatch.setattr(MCPServer, "run", run)
    return served


def locked(echo: EchoServers) -> MCPServer:
    return echo.build(TenantLock("org", DEMO))


async def test_the_locked_org_passes() -> None:
    echo = EchoServers()
    text = await mcp_call_text(locked(echo), TOOL, {"org": DEMO})
    assert json.loads(text) == {"org": DEMO}
    assert echo.calls == [DEMO]


@pytest.mark.parametrize("other", ["other", "DEMO", "", None])
async def test_another_org_is_refused_without_calling_the_tool(other: str | None) -> None:
    echo = EchoServers()
    text = await mcp_call_text(locked(echo), TOOL, {"org": other})
    assert text == REFUSED + "the call named another tenant"
    assert echo.calls == []


async def test_a_call_without_org_is_refused_without_calling_the_tool() -> None:
    """Core's lock: a tool whose schema declares org must receive it on a locked server."""
    echo = EchoServers()
    text = await mcp_call_text(locked(echo), TOOL, {})
    assert text == REFUSED + "the call did not name the tenant"
    assert echo.calls == []


async def test_the_organisation_list_shows_the_locked_organisation_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa,xb")
    echo = EchoServers()
    unlocked = json.loads(await mcp_call_text(echo.build(), LIST, {}))
    assert unlocked["data"] == ["xa", "xb", DEMO]
    only = json.loads(await mcp_call_text(locked(echo), LIST, {}))
    assert only["data"] == [DEMO]
    assert only["meta"]["tenant"] is None
    refused = await mcp_call_text(locked(echo), LIST, {"org": "xa"})
    assert refused == REFUSED + "the call named another tenant"


async def test_listing_tools_is_unaffected() -> None:
    async with Client(locked(EchoServers())) as client:
        tools = await client.list_tools()
    assert [tool.name for tool in tools.tools] == [TOOL, LIST]


async def test_serve_locks_the_server_then_hands_over_to_core(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers()
    unlocked = echo.build()
    serve(unlocked, echo.build, ["--host", "127.0.0.1", "--org=demo", "--http", "--port", "9001"])
    assert echo.locks == [None, TenantLock("org", DEMO)]
    ((server, transport, options),) = runs
    assert server is not unlocked, "the locked server is built anew"
    assert (transport, options) == ("streamable-http", {"host": "127.0.0.1", "port": 9001})
    assert await mcp_call_text(server, TOOL, {"org": "other"}) == (
        REFUSED + "the call named another tenant"
    )
    assert echo.calls == []


def test_serve_without_org_serves_unlocked(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers()
    unlocked = echo.build()
    serve(unlocked, echo.build, [])
    assert runs == [(unlocked, "stdio", {})]
    assert echo.locks == [None]


def test_an_undeclared_org_fails_fast(
    runs: list[tuple[MCPServer, str, dict[str, Any]]], capsys: pytest.CaptureFixture[str]
) -> None:
    echo = EchoServers()
    with pytest.raises(SystemExit) as info:
        serve(echo.build(), echo.build, ["--org", "nope", "--http"])
    assert info.value.code == 2
    err = capsys.readouterr().err
    assert "xippios-cashctrl: error: unknown tenant 'nope'; declared tenants: demo" in err
    assert "placeholder" not in err
    assert echo.locks == [None], "nothing is built for an undeclared organisation"
    assert runs == []


def test_help_lists_org_and_core_options(capsys: pytest.CaptureFixture[str]) -> None:
    echo = EchoServers()
    with pytest.raises(SystemExit) as info:
        serve(echo.build(), echo.build, ["--help"])
    assert info.value.code == 0
    out = capsys.readouterr().out
    for option in ("--org", "--http", "--host", "--port", "--allow-remote"):
        assert option in out


def test_unknown_options_still_fail() -> None:
    echo = EchoServers()
    with pytest.raises(SystemExit) as info:
        serve(echo.build(), echo.build, ["--org", "demo", "--nope"])
    assert info.value.code == 2


@pytest.mark.parametrize("module", [mcp, mcp_write], ids=["mcp", "mcp_write"])
def test_both_entry_points_fail_fast_on_an_undeclared_org(
    module: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    monkeypatch.setattr("sys.argv", ["entry-point", "--org", "nope"])
    with pytest.raises(SystemExit) as info:
        module.run()
    assert info.value.code == 2
    assert "unknown tenant 'nope'" in capsys.readouterr().err
    assert runs == []


@pytest.mark.parametrize("module", [mcp, mcp_write], ids=["mcp", "mcp_write"])
async def test_both_entry_points_lock_to_the_org(
    module: Any,
    monkeypatch: pytest.MonkeyPatch,
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    monkeypatch.setattr("sys.argv", ["entry-point", "--org", DEMO])
    module.run()
    ((server, transport, _),) = runs
    assert transport == "stdio"
    assert server is not module.server
    assert server.name == module.server.name
    assert server.instructions == (
        f"{module.INSTRUCTIONS} This server is locked to org demo; "
        "every tool call that takes org must pass org=demo."
    )


async def test_the_read_server_locked_refuses_another_org_before_any_request(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa")
    server = mcp.build(TenantLock("org", DEMO))
    text = await mcp_call_text(server, "cashctrl_list_currencies", {"org": "xa"})
    assert text == REFUSED + "the call named another tenant"
    assert not respx_mock.calls


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "CASHCTRL_XA_SUBDOMAIN is not set"),
        ("evil.com/x?", "CASHCTRL_XA_SUBDOMAIN does not hold a valid SUBDOMAIN"),
    ],
)
def test_a_missing_or_malformed_subdomain_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
    value: str,
    message: str,
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa")
    monkeypatch.setenv(TENANTS.var("xa", "SUBDOMAIN"), value)
    echo = EchoServers()
    with pytest.raises(SystemExit) as info:
        serve(echo.build(), echo.build, ["--org", "xa"])
    assert info.value.code == 2
    err = capsys.readouterr().err
    assert f"xippios-cashctrl: error: {message}" in err
    assert "evil.com" not in err
    assert runs == []


async def test_a_locked_server_names_the_organisation_in_its_instructions(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers(instructions="CashCtrl via xippios.")
    serve(echo.build(), echo.build, ["--org", DEMO])
    ((server, _, _),) = runs
    expected = (
        "CashCtrl via xippios. "
        "This server is locked to org demo; every tool call that takes org must pass org=demo."
    )
    async with Client(server) as client:
        assert client.instructions == expected


async def test_an_unlocked_server_keeps_its_instructions(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers(instructions="CashCtrl via xippios.")
    serve(echo.build(), echo.build, [])
    ((server, _, _),) = runs
    async with Client(server) as client:
        assert client.instructions == "CashCtrl via xippios."


@pytest.mark.parametrize(
    "argv",
    [["--http", "--host", "0.0.0.0"], ["--org", DEMO, "--http", "--host", "0.0.0.0"]],
    ids=["unlocked", "locked"],
)
def test_the_write_server_stays_on_loopback_over_http(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
    argv: list[str],
) -> None:
    """Core's rule: a write server carries no authentication, so --allow-remote is explicit."""
    monkeypatch.setattr("sys.argv", ["entry-point", *argv])
    with pytest.raises(SystemExit) as info:
        mcp_write.run()
    assert info.value.code == 2
    assert "--allow-remote" in capsys.readouterr().err
    assert runs == []
    monkeypatch.setattr("sys.argv", ["entry-point", *argv, "--allow-remote"])
    mcp_write.run()
    monkeypatch.setattr("sys.argv", ["entry-point", "--http", "--host", "localhost"])
    mcp_write.run()
    monkeypatch.setattr("sys.argv", ["entry-point", *argv])
    mcp.run()  # the read server is not held to loopback
    assert [(transport, options["host"]) for _, transport, options in runs] == [
        ("streamable-http", "0.0.0.0"),
        ("streamable-http", "localhost"),
        ("streamable-http", "0.0.0.0"),
    ]


@pytest.mark.parametrize("argv", [[], ["--org", DEMO]], ids=["unlocked", "locked"])
def test_serve_keeps_request_urls_out_of_the_log(
    caplog: pytest.LogCaptureFixture,
    respx_mock: respx.MockRouter,
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
    argv: list[str],
) -> None:
    """Core's ``main`` quiets httpx and httpcore before it serves; the plugin restores them.

    ``build_server`` quiets them too, so the levels are reset after building the server:
    only the call inside ``main`` can raise them again before the request.
    """
    echo = EchoServers()
    server = echo.build()
    for name in REQUEST_LOGGERS:
        logging.getLogger(name).setLevel(logging.NOTSET)
    serve(server, echo.build, argv)
    assert [logging.getLogger(name).level for name in REQUEST_LOGGERS] == [logging.WARNING] * 2
    respx_mock.get("https://xq-tenant.cashctrl.com/api/v1/x.json").respond(200)
    with caplog.at_level(logging.INFO):
        httpx.get("https://xq-tenant.cashctrl.com/api/v1/x.json")
    assert "xq-tenant" not in caplog.text
    assert not [record for record in caplog.records if record.name in REQUEST_LOGGERS]
