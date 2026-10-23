import os
from collections.abc import Iterator

import pytest

from xippios.cashctrl._client import (
    DEMO,
    ORGS_ENV,
    api_key_env,
    orgs,
    reset_clients,
    subdomain_env,
)

pytest_plugins = ["xippios.core.testing.plugin"]

DEMO_PAIR = frozenset({subdomain_env(DEMO), api_key_env(DEMO)})
PLACEHOLDERS = {
    # Fixtures are recorded as https://demo.cashctrl.com/api/v1/... (scripts/record_fixture.py).
    subdomain_env(DEMO): "demo",
    api_key_env(DEMO): "placeholder-for-fixture-replay",  # pragma: allowlist secret
}


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
    """Only the demo organisation can exist in a test.

    The process holds no ``CASHCTRL_*`` variable but the demo pair (stripped at import),
    and ``CASHCTRL_ORGS`` is removed again for every test. Offline tests always get the
    placeholder demo pair, so fixture replay matches the recorded host even when direnv
    has loaded the real one. A live test keeps the demo pair from the environment and
    never gets a placeholder. Clients are rebuilt per test.
    """
    monkeypatch.delenv(ORGS_ENV, raising=False)
    if request.node.get_closest_marker("live") is None:
        for name, placeholder in PLACEHOLDERS.items():
            monkeypatch.setenv(name, placeholder)
    reset_clients()
    yield
    reset_clients()


@pytest.fixture
def demo_org() -> str:
    """The one organisation a live test may reach: ``demo``, and only when it is all there is."""
    assert orgs() == (DEMO,), "live tests run against the demo organisation and nothing else"
    return DEMO
