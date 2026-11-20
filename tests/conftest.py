from collections.abc import Iterator

import pytest
from xippios.core.testing import keep_reserved_tenants

from xippios.cashctrl._client import DEMO, TENANTS

# Core's plugin keeps the default run offline and free of real keys (sdk-core ADR-0035),
# runs anyio tests on asyncio and serves the family check in tests/test_family.py; a key's
# variable is named under xippios_placeholder_key_envs in pyproject.toml, not here.
pytest_plugins = ["xippios.core.testing.plugin"]

# Once, when pytest imports this file, before any fixture of any scope: core removes the
# tenant list and every tenant's variables but the reserved demo's, which the live tests
# read, so no test sees another tenant (conventions §7; sdk-core ADR-0042, decision 1).
keep_reserved_tenants(TENANTS)

PLACEHOLDER_SUBDOMAIN = "demo"
"""Fixtures are recorded as https://demo.cashctrl.com/api/v1/... (scripts/record_fixture.py)."""


@pytest.fixture(autouse=True)
def demo_only(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Only the demo organisation can exist in a test, offline on the replay host.

    The process holds no organisation's variables but the demo pair (stripped at import),
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
