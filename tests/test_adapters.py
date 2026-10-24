"""The adapters expose exactly the tasks, in the shapes the conventions prescribe.

Per-task end-to-end calls belong next to the task's replay test, with
``xippios.core.testing.mcp_call`` and FastAPI's ``TestClient``.
"""

import inspect
import typing
from collections.abc import Callable

import pytest
from fastapi.routing import APIRoute
from xippios.core.http import is_scalar
from xippios.core.mcp import tool_name
from xippios.core.testing import assert_write_tools

from xippios.cashctrl import mcp_write, tasks, tasks_write
from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.http import router
from xippios.cashctrl.mcp import server

pytestmark = pytest.mark.anyio

TASKS: dict[str, Callable[..., object]] = {name: getattr(tasks, name) for name in tasks.__all__}


def _parameters(fn: Callable[..., object]) -> dict[str, object]:
    hints = typing.get_type_hints(fn)
    parameters = inspect.signature(fn).parameters.values()
    return {p.name: hints.get(p.name, p.annotation) for p in parameters}


async def test_mcp_tools_are_the_tasks_with_their_parameters() -> None:
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert set(tools) == {tool_name(SOURCE, fn) for fn in TASKS.values()}
    for name, fn in TASKS.items():
        tool = tools[tool_name(SOURCE, fn)]
        assert set(tool.input_schema.get("properties", {})) == set(_parameters(fn)), name
        assert tool.description, f"{name} has no docstring; agents read it"


async def test_http_routes_are_the_tasks_with_the_right_methods() -> None:
    routes = {route.path: route for route in router.routes if isinstance(route, APIRoute)}
    assert set(routes) == {f"/{SOURCE}/{name}" for name in TASKS}
    for name, fn in TASKS.items():
        scalar_only = all(is_scalar(annotation) for annotation in _parameters(fn).values())
        assert routes[f"/{SOURCE}/{name}"].methods == ({"GET"} if scalar_only else {"POST"}), name


async def test_the_organisation_list_is_on_the_read_server() -> None:
    assert "cashctrl_list_organisations" in {tool.name for tool in await server.list_tools()}


def test_the_write_server_serves_write_tasks_only() -> None:
    """Core's check (conventions §8): a write server, its tools exactly the write tasks.

    So the organisation list, a reference tool, stays on the read server (ADR-0014).
    """
    write_tasks = [getattr(tasks_write, name) for name in tasks_write.__all__]
    assert_write_tools(
        mcp_write.server, write_tasks, source=SOURCE, read_server=server, router=router
    )


async def test_write_tools_are_the_write_tasks_with_their_parameters() -> None:
    """Each write tool takes its task's parameters, confirm among them, and says it writes."""
    tools = {tool.name: tool for tool in await mcp_write.server.list_tools()}
    for name in tasks_write.__all__:
        fn = getattr(tasks_write, name)
        tool = tools[tool_name(SOURCE, fn)]
        assert set(tool.input_schema.get("properties", {})) == set(_parameters(fn)), name
        assert "confirm" in tool.input_schema["properties"], name
        assert tool.description, f"{name} has no docstring; agents read it"
        assert tool.annotations is not None
        assert (tool.annotations.read_only_hint, tool.annotations.destructive_hint) == (False, True)


async def test_the_order_categories_are_on_the_read_server_and_the_router() -> None:
    """``list_order_categories`` is a read task: agents need its ids to form ``create_order``."""
    assert "cashctrl_list_order_categories" in {tool.name for tool in await server.list_tools()}
    routes = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert f"/{SOURCE}/list_order_categories" in routes
    write_tools = {tool.name for tool in await mcp_write.server.list_tools()}
    assert "cashctrl_list_order_categories" not in write_tools
