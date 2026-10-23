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

# pytester runs this conftest in a subprocess: tests/test_tasks.py proves with it that a
# key a live test cached never reaches a later offline test.
pytest_plugins = ["xippios.core.testing.plugin", "pytester"]

DEMO_PAIR = frozenset({subdomain_env(DEMO), api_key_env(DEMO)})
PLACEHOLDER_KEY = "placeholder-for-fixture-replay"  # pragma: allowlist secret
PLACEHOLDERS = {
    # Fixtures are recorded as https://demo.cashctrl.com/api/v1/... (scripts/record_fixture.py).
    subdomain_env(DEMO): "demo",
    api_key_env(DEMO): PLACEHOLDER_KEY,
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
def demo_only(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[str | None]:
    """Only the demo organisation can exist in a test, and offline it sends the placeholder.

    The process holds no ``CASHCTRL_*`` variable but the demo pair (stripped at import),
    and ``CASHCTRL_ORGS`` is removed again for every test. Offline tests always get the
    placeholder demo pair, so fixture replay matches the recorded host even when direnv
    has loaded the real one. A live test keeps the demo pair from the environment and
    never gets a placeholder.

    A client's auth reads the key once and caches it, so a client a live test built would
    carry the real key. Every cached client is therefore dropped before and after each
    test, after the placeholders are set: the next ``client_for`` builds a client whose
    auth reads the placeholder. ``test_a_key_a_live_test_cached_never_reaches_the_next``
    in ``tests/test_tasks.py`` runs this file in a subprocess to prove it.

    Yields the placeholder key, or ``None`` in a live test.
    """
    monkeypatch.delenv(ORGS_ENV, raising=False)
    live = request.node.get_closest_marker("live") is not None
    if not live:
        for name, placeholder in PLACEHOLDERS.items():
            monkeypatch.setenv(name, placeholder)
    reset_clients()
    yield None if live else PLACEHOLDER_KEY
    reset_clients()


@pytest.fixture
def demo_org() -> str:
    """The one organisation a live test may reach: ``demo``, and only when it is all there is."""
    assert orgs() == (DEMO,), "live tests run against the demo organisation and nothing else"
    return DEMO
