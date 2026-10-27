"""The --org lock: tools bound to one organisation (``_org_lock``), wired up by ``_cli``.

The lock is the package's own since core 0.3.0 (ADR-0024): no middleware, but a wrapper
that binds ``org`` on every tool when the server is built, so no tool takes it. Every
tool call goes through ``xippios.core.testing.mcp_call_text``, an in-process
``mcp.Client``, so core's argument check runs as it does for a real client. The parts of
core's ``tests/mcp/test_lock.py`` (sdk-core ``cb8ecdf``) that still apply are here: the
lock's validation, the bound tenant passing, the list narrowed to it, the instructions.
"""

import dataclasses
import inspect
import json
import logging
import typing
from typing import Any

import httpx
import pytest
import respx
from mcp import Client
from mcp.server.mcpserver import MCPServer
from xippios.core.mcp import build_server
from xippios.core.testing import mcp_call, mcp_call_text

from xippios.cashctrl import mcp, mcp_write, tasks, tasks_write
from xippios.cashctrl._cli import serve
from xippios.cashctrl._client import DEMO, SOURCE, TENANTS
from xippios.cashctrl._org_lock import OrgLock, bind, bind_tasks, instructions, lock_sentence

pytestmark = pytest.mark.anyio

TOOL = "cashctrl_echo_org"
LIST = "cashctrl_list_organisations"
REQUEST_LOGGERS = ("httpx", "httpcore")
SENTENCE = (
    "This server is bound to org demo; every tool acts on that organisation and takes no org."
)
LOCK = OrgLock("org", DEMO)


class EchoServers:
    """Builds servers with one tool that records the organisation it was called for."""

    def __init__(self, instructions: str | None = None) -> None:
        self.calls: list[str] = []
        self.locks: list[OrgLock | None] = []
        self.instructions = instructions

    def build(self, lock: OrgLock | None = None) -> MCPServer:
        calls = self.calls

        async def echo_org(org: str, note: str = "") -> dict[str, str]:
            """Return the organisation the tool was called for.

            Args:
                org: Organisation name, e.g. ``demo``.
                note: Any text, e.g. ``"hi"``.
            """
            calls.append(org)
            return {"org": org, "note": note}

        self.locks.append(lock)
        return build_server(
            SOURCE,
            bind_tasks([echo_org, tasks.list_organisations], lock),
            instructions=instructions(self.instructions, lock),
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
    return echo.build(LOCK)


# The lock and the wrapper ------------------------------------------------------------


def test_a_lock_is_a_frozen_pair() -> None:
    assert (LOCK.param, LOCK.value) == ("org", DEMO)
    assert OrgLock(param="org", value=DEMO) == LOCK
    with pytest.raises(dataclasses.FrozenInstanceError):
        LOCK.value = "other"  # type: ignore[misc]


@pytest.mark.parametrize(("param", "value"), [("", "acme"), ("an org", "acme"), ("org", "")])
def test_a_lock_needs_a_parameter_name_and_a_tenant(param: str, value: str) -> None:
    with pytest.raises(ValueError, match=r"param must be|value must name"):
        OrgLock(param, value)


@pytest.mark.parametrize("name", [*tasks.__all__, *tasks_write.__all__])
def test_a_bound_task_keeps_its_name_and_drops_org(name: str) -> None:
    """Same ``__name__`` (tool names, ``MCP_CAPS`` keys), no ``org`` in signature or docstring."""
    task = getattr(tasks, name, None) or getattr(tasks_write, name)
    bound = bind(task, LOCK)
    assert bound.__name__ == task.__name__
    parameters = inspect.signature(bound).parameters
    assert "org" not in parameters
    assert list(parameters) == [p for p in inspect.signature(task).parameters if p != "org"]
    assert "org" not in typing.get_type_hints(bound)
    doc = inspect.getdoc(bound) or ""
    assert doc.splitlines()[0] == (inspect.getdoc(task) or "").splitlines()[0]
    assert "    org:" not in doc
    assert ("Args:" in doc) == bool(parameters), "an Args: block the org line emptied goes"


def test_the_docstring_loses_the_org_entry_and_its_continuation() -> None:
    def task(org: str, query: str | None = None) -> None:
        """Find things.

        Args:
            org: A declared organisation name,
                e.g. ``demo``.
            query: Full-text search, e.g. ``"Muster"``.

        Returns:
            Nothing.
        """

    assert inspect.getdoc(bind(task, LOCK)) == (
        'Find things.\n\nArgs:\n    query: Full-text search, e.g. ``"Muster"``.\n\n'
        "Returns:\n    Nothing."
    )


def test_a_task_without_org_is_left_as_it_is() -> None:
    def ping() -> dict[str, bool]:
        """Answer without an organisation."""
        return {"pong": True}

    assert bind(ping, LOCK) is ping
    assert bind_tasks([ping], None) == [ping]


async def test_a_bound_sync_facade_awaits_its_async_twin(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://demo.cashctrl.com/api/v1/currency/list.json")
    route.respond(200, json={"total": 0, "data": []})
    result = await bind(tasks.list_currencies, LOCK)()
    assert (result.meta.tenant, result.meta.request) == (DEMO, {"org": DEMO})
    assert route.call_count == 1


# Calls on a bound server -------------------------------------------------------------


async def test_the_bound_org_is_passed() -> None:
    echo = EchoServers()
    text = await mcp_call_text(locked(echo), TOOL, {"note": "hi"})
    assert json.loads(text) == {"org": DEMO, "note": "hi"}
    assert echo.calls == [DEMO]


async def test_no_tool_of_a_bound_server_takes_org() -> None:
    async with Client(locked(EchoServers())) as client:
        tools = (await client.list_tools()).tools
    assert [tool.name for tool in tools] == [TOOL, LIST]
    for tool in tools:
        assert "org" not in tool.input_schema.get("properties", {}), tool.name
        assert "org:" not in (tool.description or ""), tool.name


@pytest.mark.parametrize("other", [DEMO, "other", "DEMO", "", None])
async def test_a_call_that_still_passes_org_is_answered_for_the_bound_org(
    other: str | None,
) -> None:
    """Observed under core 0.3.0: its argument check ignores an argument no tool declares.

    The ``mcp`` SDK's argument model drops an unknown argument, and core's argument
    middleware validates with that model, so ``org`` is neither refused nor passed on:
    the tool runs for the bound organisation, whatever the call named.
    """
    echo = EchoServers()
    text = await mcp_call_text(locked(echo), TOOL, {"org": other, "note": "x"})
    assert json.loads(text) == {"org": DEMO, "note": "x"}
    assert echo.calls == [DEMO]


async def test_a_refused_argument_is_answered_by_core_before_the_tool_runs() -> None:
    echo = EchoServers()
    text = await mcp_call_text(locked(echo), TOOL, {"note": 7})
    assert text == "error: InvalidRequestError: note: Input should be a valid string"
    assert echo.calls == []


async def test_the_organisation_list_shows_the_bound_organisation_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa,xb")
    echo = EchoServers()
    unlocked = json.loads(await mcp_call_text(echo.build(), LIST, {}))
    assert unlocked["data"] == ["xa", "xb", DEMO]
    only = json.loads(await mcp_call_text(locked(echo), LIST, {}))
    assert only["data"] == [DEMO]
    assert only["meta"]["tenant"] is None
    assert only["meta"]["endpoint"] == "list_organisations"
    assert tasks.list_organisations().data == ["xa", "xb", DEMO], "the task itself is unchanged"


async def test_a_lock_on_an_undeclared_organisation_lists_nothing() -> None:
    server = EchoServers().build(OrgLock("org", "gone"))
    assert (await mcp_call(server, LIST, {}))["data"] == []


async def test_the_bound_read_server_reaches_the_bound_organisation_only(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa")
    monkeypatch.setenv(TENANTS.var("xa", "SUBDOMAIN"), "xa-tenant")
    route = respx_mock.get("https://demo.cashctrl.com/api/v1/currency/list.json")
    route.respond(200, json={"total": 0, "data": []})
    server = mcp.build(LOCK)
    payload = await mcp_call(server, "cashctrl_list_currencies", {"org": "xa"})
    assert (payload["meta"]["tenant"], payload["meta"]["request"]) == (DEMO, {"org": DEMO})
    assert route.call_count == 1, "the demo host, never xa's"


# Startup and the command line --------------------------------------------------------


async def test_serve_binds_the_server_then_hands_over_to_core(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers()
    unlocked = echo.build()
    serve(unlocked, echo.build, ["--host", "127.0.0.1", "--org=demo", "--http", "--port", "9001"])
    assert echo.locks == [None, LOCK]
    ((server, transport, options),) = runs
    assert server is not unlocked, "the bound server is built anew"
    assert (transport, options) == ("streamable-http", {"host": "127.0.0.1", "port": 9001})
    assert json.loads(await mcp_call_text(server, TOOL, {}))["org"] == DEMO
    assert echo.calls == [DEMO]


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
async def test_both_entry_points_bind_to_the_org(
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
    assert server.instructions == f"{module.INSTRUCTIONS} {SENTENCE}"
    bound = {tool.name: tool for tool in await server.list_tools()}
    unbound = {tool.name: tool for tool in await module.server.list_tools()}
    assert bound.keys() == unbound.keys(), "the same tools, by name"
    for name, tool in bound.items():
        expected = set(unbound[name].input_schema.get("properties", {})) - {"org"}
        assert set(tool.input_schema.get("properties", {})) == expected, name


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


async def test_a_bound_server_names_the_organisation_in_its_instructions(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers(instructions="CashCtrl via xippios.")
    serve(echo.build(), echo.build, ["--org", DEMO])
    ((server, _, _),) = runs
    async with Client(server) as client:
        assert client.instructions == f"CashCtrl via xippios. {SENTENCE}"
    assert lock_sentence(LOCK) == SENTENCE
    assert instructions(None, LOCK) == SENTENCE


async def test_an_unlocked_server_keeps_its_instructions(
    runs: list[tuple[MCPServer, str, dict[str, Any]]],
) -> None:
    echo = EchoServers(instructions="CashCtrl via xippios.")
    serve(echo.build(), echo.build, [])
    ((server, _, _),) = runs
    async with Client(server) as client:
        assert client.instructions == "CashCtrl via xippios."
    assert json.loads(await mcp_call_text(server, TOOL, {"org": "other"}))["org"] == "other"


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
