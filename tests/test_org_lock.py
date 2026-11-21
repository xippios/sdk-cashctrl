"""The --org lock's wiring: the package's tasks bound to one organisation, both entry points.

The lock is core's (``TenantLock``, ``bind_tasks``, ``tenant_instructions``) and so is the
serve command (``serve_tenants``); core's ``tests/test_tenant_lock.py`` and
``tests/mcp/test_cli.py`` test them. The lock is no middleware but a wrapper:
``build(TenantLock(TENANTS, org))`` in ``mcp.py`` and in ``mcp_write.py`` returns the tool
set whose tasks ``bind_tasks`` binds, one tool per task with ``org`` bound at build, the
same ``__name__`` (the tool names and the ``MCP_CAPS`` keys stay), the docstring without
its ``org`` line and a signature without ``org``. A bound server's instructions are its
module's ``BOUND_INSTRUCTIONS``, without the clause that a tool takes ``org``, and core ends
them with the sentence that names the organisation (``SENTENCE``); ``list_organisations``
lists the bound organisation alone, with ``meta.tenant`` ``None``.

What stays here is the package's own wiring: its tasks bound, ``--org`` with ``check_org``
on both entry points, the instructions they end with, and the write server held to
loopback. Every tool call goes through ``xippios.core.testing.mcp_call``, an in-process
``mcp.Client``, so core's argument check runs as it does for a real client.
"""

import inspect
import json
import sys
import typing
from typing import Any

import pytest
from mcp.server.mcpserver import MCPServer
from xippios.core import TenantLock, bind_tasks
from xippios.core.mcp import build_server
from xippios.core.testing import ReplayFixture, mcp_call, mcp_call_text

from xippios.cashctrl import mcp, mcp_write, tasks, tasks_write
from xippios.cashctrl._client import DEMO, TENANTS

pytestmark = pytest.mark.anyio

LIST = "cashctrl_list_organisations"
ENTRY_POINT = "xippios-cashctrl-mcp-read"
SENTENCE = (
    "This server is bound to org demo; every tool acts on that organisation and takes no org."
)
LOCK = TenantLock(TENANTS, DEMO, noun="organisation")


@pytest.fixture
def runs(monkeypatch: pytest.MonkeyPatch) -> list[tuple[MCPServer, str, dict[str, Any]]]:
    """Every server core's ``main`` would have run, with its transport and options."""
    served: list[tuple[MCPServer, str, dict[str, Any]]] = []

    def run(self: MCPServer, transport: str, **options: Any) -> None:
        served.append((self, transport, options))

    monkeypatch.setattr(MCPServer, "run", run)
    return served


# The lock and the wrapper ------------------------------------------------------------


@pytest.mark.parametrize("name", [*tasks.__all__, *tasks_write.__all__])
def test_a_bound_task_keeps_its_name_and_drops_org(name: str) -> None:
    """Same ``__name__`` (tool names, ``MCP_CAPS`` keys), no ``org`` in signature or docstring."""
    task = getattr(tasks, name, None) or getattr(tasks_write, name)
    bound = bind_tasks([task], LOCK)[0]
    assert bound.__name__ == task.__name__
    parameters = inspect.signature(bound).parameters
    assert "org" not in parameters
    assert list(parameters) == [p for p in inspect.signature(task).parameters if p != "org"]
    assert "org" not in typing.get_type_hints(bound)
    doc = inspect.getdoc(bound) or ""
    assert doc.splitlines()[0] == (inspect.getdoc(task) or "").splitlines()[0]
    assert "    org:" not in doc
    assert ("Args:" in doc) == bool(parameters), "an Args: block the org line emptied goes"


async def test_a_bound_sync_facade_awaits_its_async_twin(replay_fixture: ReplayFixture) -> None:
    """The recorded currency list, replayed: the test asserts what was sent and the meta."""
    route = replay_fixture("currency_list", "default")
    result = await bind_tasks([tasks.list_currencies], LOCK)[0]()
    assert (result.meta.tenant, result.meta.request) == (DEMO, {"org": DEMO})
    assert route.call_count == 1


# Calls on a bound server -------------------------------------------------------------


async def test_the_organisation_list_shows_the_bound_organisation_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa,xb")
    unlocked = json.loads(await mcp_call_text(build_server(mcp.build()), LIST, {}))
    assert unlocked["data"] == ["xa", "xb", DEMO]
    only = json.loads(await mcp_call_text(build_server(mcp.build(LOCK)), LIST, {}))
    assert only["data"] == [DEMO]
    assert only["meta"]["tenant"] is None
    assert only["meta"]["endpoint"] == "list_organisations"
    assert tasks.list_organisations().data == ["xa", "xb", DEMO], "the task itself is unchanged"


async def test_the_bound_read_server_reaches_the_bound_organisation_only(
    monkeypatch: pytest.MonkeyPatch, replay_fixture: ReplayFixture
) -> None:
    """A call that still names an organisation is refused before the tool runs.

    Core's argument check refuses an argument no tool of a bound server declares, ``org``
    among them, and names the ones the tool takes; the call without it reaches the bound
    organisation alone. The recorded currency list is replayed: the test asserts what was
    sent and the meta.
    """
    monkeypatch.setenv(TENANTS.list_var, "xa")
    monkeypatch.setenv(TENANTS.var("xa", "SUBDOMAIN"), "xa-tenant")
    route = replay_fixture("currency_list", "default")
    server = build_server(mcp.build(LOCK))
    refused = await mcp_call_text(server, "cashctrl_list_currencies", {"org": "xa"})
    assert refused == (
        "error: InvalidRequestError: org: Not an argument of this tool; it takes no arguments"
    )
    assert route.call_count == 0, "the refused call sends nothing"
    payload = await mcp_call(server, "cashctrl_list_currencies", {})
    assert (payload["meta"]["tenant"], payload["meta"]["request"]) == (DEMO, {"org": DEMO})
    assert route.call_count == 1, "the demo host, never xa's"


# Startup and the command line --------------------------------------------------------


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
    # The bound server's own text leaves out the clause that a tool takes org, which the
    # unbound server's keeps, and core's sentence names the organisation.
    assert module.server.instructions == module.INSTRUCTIONS
    assert "takes org" in module.INSTRUCTIONS
    assert server.instructions == f"{module.BOUND_INSTRUCTIONS} {SENTENCE}"
    assert "takes org" not in server.instructions
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
    # main's errors name the entry point that runs, sys.argv[0] as installed; an installed
    # script runs as __main__ without a module spec, which argparse reads (core's
    # tests/mcp/test_cli.py, entry_point).
    monkeypatch.setattr("sys.argv", [f"/opt/venv/bin/{ENTRY_POINT}", "--org", "xa"])
    monkeypatch.setattr(sys.modules["__main__"], "__spec__", None)
    with pytest.raises(SystemExit) as info:
        mcp.run()
    assert info.value.code == 2
    err = capsys.readouterr().err
    assert f"{ENTRY_POINT}: error: {message}" in err
    assert "evil.com" not in err
    assert runs == []


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
