"""Keys resolved as in production: core's placeholder pin is lifted in this module.

Core's plugin pins ``PLACEHOLDER_KEY`` on every auth object in every test not marked
``live`` (ADR-0013), so a test of how a key is resolved overrides ``placeholder_api_key``
at module level with a fixture that pins nothing (conventions §15, item 5). The shell's
demo key, which direnv may have loaded, is removed instead, so no test here can send it.
"""

import base64

import httpx
import pytest
import respx
from xippios.core import ConfigError, InvalidRequestError

from xippios.cashctrl._client import DEMO, TENANTS, client_for

pytestmark = pytest.mark.anyio

HIDDEN_SUBDOMAIN = "xa-hidden-subdomain"
SCAFFOLD_KEY_ENV = "CASHCTRL_API_KEY"  # pragma: allowlist secret
"""The template's key variable, which live.yml passes from its secret beside the demo pair."""
SCAFFOLD_KEY = "scaffold-key-value"  # pragma: allowlist secret
DEMO_KEY = "demo-key-value"  # pragma: allowlist secret


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


def basic(key: str) -> str:
    """The ``Authorization`` header that sends ``key`` as the HTTP basic user name."""
    return "Basic " + base64.b64encode(f"{key}:".encode()).decode("ascii")


@pytest.mark.parametrize("scaffold_key", ["", SCAFFOLD_KEY])
async def test_the_scaffold_key_is_no_organisations_key(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter, scaffold_key: str
) -> None:
    """The live run's ``CASHCTRL_API_KEY``, empty or set, leaves demo's key as it is.

    live.yml passes it from its secret beside the demo pair; the registry declares no
    organisation from it, and the demo client sends its own key. The route answers only
    that key, so a request with any other is no match and fails the test.
    """
    monkeypatch.setenv(SCAFFOLD_KEY_ENV, scaffold_key)
    monkeypatch.setenv(TENANTS.var(DEMO, "SUBDOMAIN"), HIDDEN_SUBDOMAIN)
    monkeypatch.setenv(TENANTS.var(DEMO, "API_KEY"), DEMO_KEY)
    assert TENANTS.names() == (DEMO,)
    route = respx_mock.get(
        url__startswith=f"https://{HIDDEN_SUBDOMAIN}.cashctrl.com/",
        headers={"Authorization": basic(DEMO_KEY)},
    )
    route.mock(return_value=httpx.Response(200, json={}))
    await client_for(DEMO).get("/fiscalperiod/list.json")
    assert route.call_count == 1


def test_the_scaffold_key_declares_no_organisation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the demo pair, ``CASHCTRL_API_KEY`` stands in for no organisation."""
    monkeypatch.setenv(SCAFFOLD_KEY_ENV, SCAFFOLD_KEY)
    monkeypatch.delenv(TENANTS.var(DEMO, "SUBDOMAIN"), raising=False)
    assert TENANTS.names() == ()
    with pytest.raises(InvalidRequestError, match="unknown tenant"):
        client_for(DEMO)
