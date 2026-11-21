"""Keys resolved as in production: core's placeholder pin is lifted in this module.

Core's plugin pins ``PLACEHOLDER_KEY`` on every auth object in every test not marked
``live`` (sdk-core ADR-0035, decision 3), so a test of how a key is resolved overrides
``placeholder_api_key`` at module level with a fixture that pins nothing (conventions §15,
item 5). The shell's demo key, which direnv may have loaded, is removed instead, so no
test here can send it.
"""

import base64
from pathlib import Path

import httpx
import pytest
import respx
from xippios.core import ConfigError
from xippios.core.testing import load_fixture

from xippios.cashctrl._client import DEMO, TENANTS, client_for

pytestmark = pytest.mark.anyio

HIDDEN_SUBDOMAIN = "xa-hidden-subdomain"
DEMO_KEY = "demo-key-value"  # pragma: allowlist secret
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def placeholder_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pins nothing (sdk-core ADR-0035, decision 3); the shell's demo key is removed instead."""
    monkeypatch.delenv(TENANTS.var(DEMO, "API_KEY"), raising=False)


async def test_a_declared_org_without_its_key_fails_on_the_first_request(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter
) -> None:
    monkeypatch.setenv(TENANTS.list_var, "xa")
    monkeypatch.setenv(TENANTS.var("xa", "SUBDOMAIN"), HIDDEN_SUBDOMAIN)
    route = respx_mock.get(url__startswith=f"https://{HIDDEN_SUBDOMAIN}.cashctrl.com/")
    route.mock(return_value=httpx.Response(200, json={}))
    client = client_for("xa")
    with pytest.raises(ConfigError, match="CASHCTRL_XA_API_KEY"):
        await client.get("/fiscalperiod/list.json")
    assert not route.called


def basic(key: str) -> str:
    """The ``Authorization`` header that sends ``key`` as the HTTP basic user name."""
    return "Basic " + base64.b64encode(f"{key}:".encode()).decode("ascii")


async def test_the_demo_client_sends_its_key_as_the_basic_user_name(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter
) -> None:
    """Demo's own key, sent as the HTTP basic user name with no password.

    The route answers only that header, so a request with any other is no match and fails
    the test. It serves ``fiscalperiod_list/default``'s recorded answer at this test's host:
    the test asserts only what was sent (conventions §10, kind 3).
    """
    monkeypatch.setenv(TENANTS.var(DEMO, "SUBDOMAIN"), HIDDEN_SUBDOMAIN)
    monkeypatch.setenv(TENANTS.var(DEMO, "API_KEY"), DEMO_KEY)
    assert TENANTS.names() == (DEMO,)
    route = respx_mock.get(
        url__startswith=f"https://{HIDDEN_SUBDOMAIN}.cashctrl.com/",
        headers={"Authorization": basic(DEMO_KEY)},
    )
    answer = load_fixture(FIXTURES / "fiscalperiod_list" / "default.json").response
    headers = [(name, value) for name, value in answer.headers if name.lower() != "content-length"]
    route.mock(return_value=httpx.Response(answer.status, headers=headers, text=answer.body))
    await client_for(DEMO).get("/fiscalperiod/list.json")
    assert route.call_count == 1
