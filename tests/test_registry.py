"""The organisation registry: declaration, lookup and one isolated client per organisation."""

import os

import httpx
import pytest
import respx
from xippios.core import ConfigError, InvalidRequestError

from xippios.cashctrl._client import (
    DEMO,
    ORGS_ENV,
    RATE_LIMIT,
    api_key_env,
    client_for,
    orgs,
    require_org,
    subdomain_env,
)

pytestmark = pytest.mark.anyio

# Values that must never appear in a message.
HIDDEN_SUBDOMAIN = "xa-hidden-subdomain"
HIDDEN_KEY = "xa-hidden-key-value"  # pragma: allowlist secret


@pytest.fixture
def no_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(subdomain_env(DEMO), raising=False)
    monkeypatch.delenv(api_key_env(DEMO), raising=False)


@pytest.fixture(scope="module")
def cashctrl_variables_at_module_scope() -> set[str]:
    return {name for name in os.environ if name.startswith("CASHCTRL_")}


def test_no_fixture_scope_sees_a_productive_organisation(
    cashctrl_variables_at_module_scope: set[str],
) -> None:
    """conftest strips every CASHCTRL_* variable but the demo pair when pytest imports it."""
    assert cashctrl_variables_at_module_scope <= {subdomain_env(DEMO), api_key_env(DEMO)}


def declare(monkeypatch: pytest.MonkeyPatch, org: str, *, key: bool = True) -> None:
    monkeypatch.setenv(subdomain_env(org), f"{org}-{HIDDEN_SUBDOMAIN}")
    if key:
        monkeypatch.setenv(api_key_env(org), f"{org}-{HIDDEN_KEY}")


def test_variable_names_follow_the_scheme() -> None:
    assert subdomain_env("acme_test") == "CASHCTRL_ACME_TEST_SUBDOMAIN"
    assert api_key_env("acme_test") == "CASHCTRL_ACME_TEST_API_KEY"  # pragma: allowlist secret
    assert subdomain_env(DEMO) == "CASHCTRL_DEMO_SUBDOMAIN"
    assert api_key_env(DEMO) == "CASHCTRL_DEMO_API_KEY"  # pragma: allowlist secret


@pytest.mark.usefixtures("no_demo")
def test_nothing_declared_means_no_organisation() -> None:
    assert orgs() == ()


@pytest.mark.usefixtures("no_demo")
def test_listed_organisations_in_declared_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ORGS_ENV, " xb, xa ,,")
    assert orgs() == ("xb", "xa")


def test_demo_is_appended_when_its_pair_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,xb")
    assert orgs() == ("xa", "xb", DEMO)


@pytest.mark.parametrize("missing", ["subdomain", "key"])
def test_demo_needs_both_variables(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    variable = subdomain_env(DEMO) if missing == "subdomain" else api_key_env(DEMO)
    monkeypatch.setenv(variable, "")
    assert orgs() == ()


def test_environment_is_read_on_every_call(monkeypatch: pytest.MonkeyPatch) -> None:
    assert orgs() == (DEMO,)
    monkeypatch.setenv(ORGS_ENV, "xa")
    assert orgs() == ("xa", DEMO)


def test_demo_cannot_be_listed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,demo")
    with pytest.raises(ConfigError, match="reserved") as info:
        orgs()
    assert "CASHCTRL_DEMO_SUBDOMAIN" in str(info.value)


@pytest.mark.parametrize("name", ["Xa", "a-b", "a b", "ä"])
def test_malformed_names_are_refused(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    monkeypatch.setenv(ORGS_ENV, f"xa,{name}")
    with pytest.raises(ConfigError, match="lower-case"):
        orgs()


def test_duplicate_names_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,xb,xa")
    with pytest.raises(ConfigError, match="twice"):
        orgs()


def test_require_org_lists_the_declared_names_and_no_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,xb")
    declare(monkeypatch, "xa")
    declare(monkeypatch, "xb")
    assert require_org("xa") == "xa"
    with pytest.raises(InvalidRequestError) as info:
        require_org("nope")
    message = str(info.value)
    assert "'nope'" in message
    assert "xa, xb, demo" in message
    assert HIDDEN_SUBDOMAIN not in message
    assert HIDDEN_KEY not in message
    assert "placeholder" not in message


@pytest.mark.usefixtures("no_demo")
def test_require_org_without_any_declaration_names_the_variables() -> None:
    with pytest.raises(InvalidRequestError) as info:
        require_org("demo")
    assert "no organisation is declared" in str(info.value)
    assert ORGS_ENV in str(info.value)


def test_client_for_refuses_an_undeclared_org() -> None:
    with pytest.raises(InvalidRequestError):
        client_for("xa")


def test_each_org_has_its_own_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,xb")
    declare(monkeypatch, "xa")
    declare(monkeypatch, "xb")
    a, b = client_for("xa"), client_for("xb")
    assert a is not b
    assert a is client_for("xa")
    assert a.config.base_url == f"https://xa-{HIDDEN_SUBDOMAIN}.cashctrl.com/api/v1"
    assert b.config.base_url == f"https://xb-{HIDDEN_SUBDOMAIN}.cashctrl.com/api/v1"
    assert a._bucket is not None
    assert b._bucket is not None
    assert a._bucket is not b._bucket
    assert a.config.rate_limit == b.config.rate_limit == RATE_LIMIT
    assert a.config.cache is None
    assert b.config.cache is None


def test_a_changed_subdomain_builds_a_new_client(monkeypatch: pytest.MonkeyPatch) -> None:
    first = client_for(DEMO)
    monkeypatch.setenv(subdomain_env(DEMO), "other")
    second = client_for(DEMO)
    assert second is not first
    assert second.config.base_url == "https://other.cashctrl.com/api/v1"


@pytest.mark.parametrize("value", ["", "   ", "evil.com/x?", "a_b", "-a"])
def test_a_missing_or_malformed_subdomain_is_a_config_error(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa")
    monkeypatch.setenv(subdomain_env("xa"), value)
    with pytest.raises(ConfigError) as info:
        client_for("xa")
    assert "CASHCTRL_XA_SUBDOMAIN" in str(info.value)
    if value.strip():
        assert value not in str(info.value)


async def test_a_declared_org_without_its_key_fails_on_the_first_request(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter
) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa")
    declare(monkeypatch, "xa", key=False)
    route = respx_mock.get(url__startswith=f"https://xa-{HIDDEN_SUBDOMAIN}.cashctrl.com/")
    route.mock(return_value=httpx.Response(200, json={}))
    client = client_for("xa")
    with pytest.raises(ConfigError, match="CASHCTRL_XA_API_KEY"):
        await client.get("/fiscalperiod/list.json")
    assert not route.called
