"""Keys resolved as in production: core's placeholder pin is lifted in this module.

Core's plugin pins ``PLACEHOLDER_KEY`` on every auth object in every test not marked
``live`` (ADR-0013), so a test of how a key is resolved overrides ``placeholder_api_key``
at module level with a fixture that pins nothing (conventions §15, item 5). The shell's
demo key, which direnv may have loaded, is removed instead, so no test here can send it.
"""

import httpx
import pytest
import respx
from xippios.core import ConfigError

from xippios.cashctrl._client import DEMO, TENANTS, client_for

pytestmark = pytest.mark.anyio

HIDDEN_SUBDOMAIN = "xa-hidden-subdomain"


@pytest.fixture
def placeholder_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pins nothing (ADR-0013); the shell's demo key is removed instead."""
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
