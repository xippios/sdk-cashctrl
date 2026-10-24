import os
from collections.abc import Iterator

import pytest

from xippios.cashctrl._client import DEMO, TENANTS

# Core's plugin keeps the run offline (ADR-0013): no network outside a test marked live or
# network, no rate-limit waits, and every auth object of every organisation sends
# PLACEHOLDER_KEY, pinned on EnvKeyAuth, with CASHCTRL_DEMO_API_KEY set to it
# (xippios_placeholder_key_envs in pyproject.toml). What stays here is which
# organisations exist in a test: demo only.
pytest_plugins = ["xippios.core.testing.plugin"]

DEMO_PAIR = frozenset({TENANTS.var(DEMO, "SUBDOMAIN"), TENANTS.var(DEMO, "API_KEY")})
PLACEHOLDER_SUBDOMAIN = "demo"
"""Fixtures are recorded as https://demo.cashctrl.com/api/v1/... (scripts/record_fixture.py)."""


def _strip_productive_organisations() -> None:
    """Remove every ``CASHCTRL_*`` variable but the demo pair from this process.

    Runs once, when pytest imports this file, before any fixture of any scope: no
    session- or module-scoped fixture, and no test, can see ``CASHCTRL_ORGS`` or another
    organisation's subdomain or key. The demo pair stays for the live tests.
    """
    for name in [name for name in os.environ if name.startswith("CASHCTRL_")]:
        if name not in DEMO_PAIR:
            del os.environ[name]


_strip_productive_organisations()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def demo_only(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Only the demo organisation can exist in a test, offline on the replay host.

    The process holds no ``CASHCTRL_*`` variable but the demo pair (stripped at import),
    and ``CASHCTRL_ORGS`` is removed again for every test. An offline test gets the
    placeholder subdomain, so fixture replay matches the recorded host even when direnv
    has loaded the real one; core's plugin gives it the placeholder key. A live test
    keeps the demo pair from the environment.

    Every cached client is dropped before and after each test, after the placeholder is
    set, so no test is handed a client another test built.
    """
    monkeypatch.delenv(TENANTS.list_var, raising=False)
    if request.node.get_closest_marker("live") is None:
        monkeypatch.setenv(TENANTS.var(DEMO, "SUBDOMAIN"), PLACEHOLDER_SUBDOMAIN)
    TENANTS.reset()
    yield
    TENANTS.reset()


@pytest.fixture
def demo_org() -> str:
    """The one organisation a live test may reach: ``demo``, and only when it is all there is."""
    names = TENANTS.names()
    assert names == (DEMO,), "live tests run against the demo organisation and nothing else"
    return DEMO
