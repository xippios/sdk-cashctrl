"""A pytest plugin that names each test whose replay answers a request other than its recording.

``tests/test_built_answers.py`` runs the modules that replay with it, in a process of their
own (``-p replay_census``), and reads what it writes to the file ``REPLAY_CENSUS`` names:
one JSON line per test in which a route mounted by core's ``mount_fixture`` (behind
``replay_fixture`` and ``replay``) answered a request that differs from the recorded one in
its host, its path, its query or its form body. The plugin wraps ``mount_fixture`` when it is
loaded, before any test module, and changes no answer.
"""

from __future__ import annotations

import json
import os
from collections.abc import Generator, Iterable
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest
import respx
import xippios.core.testing.replay as core_replay
from xippios.core.testing import Fixture

_mounted: list[tuple[Fixture, respx.Route]] = []
_mount_fixture = core_replay.mount_fixture


def _mount_and_keep(
    router: respx.Router,
    fixture: Fixture,
    *,
    match_params: Iterable[str] | None = None,
    url: str | None = None,
) -> respx.Route:
    route = _mount_fixture(router, fixture, match_params=match_params, url=url)
    _mounted.append((fixture, route))
    return route


core_replay.mount_fixture = _mount_and_keep


def differs(fixture: Fixture, request: httpx.Request) -> bool:
    """Whether ``request`` is another request than the one ``fixture`` recorded."""
    recorded = httpx.URL(fixture.request.url)
    if (request.url.host, request.url.path) != (recorded.host, recorded.path):
        return True
    if sorted(request.url.params.multi_items()) != sorted(recorded.params.multi_items()):
        return True
    if request.method != "POST":
        return False
    sent = parse_qsl(request.content.decode("utf-8", "replace"), keep_blank_values=True)
    return sorted(sent) != sorted(parse_qsl(fixture.request.body or "", keep_blank_values=True))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None]:
    _mounted.clear()
    yield
    if any(differs(fixture, call.request) for fixture, route in _mounted for call in route.calls):
        name = getattr(item, "originalname", item.name)
        with Path(os.environ["REPLAY_CENSUS"]).open("a", encoding="utf-8") as census:
            census.write(json.dumps({"module": item.path.name, "test": name}) + "\n")
