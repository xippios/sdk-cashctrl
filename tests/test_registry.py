"""The organisation registry: declaration, lookup and one isolated client per organisation.

The registry is core's ``Tenants`` (ADR-0014); these tests pin the semantics this package
relies on. Where core's wording differs from the local registry's, a test asserts the
behaviour and the variable names, not the text.
"""

import os

import pytest
from xippios.core import ConfigError, InvalidRequestError

from xippios.cashctrl._client import DEMO, RATE_LIMIT, TENANTS, check_subdomain, client_for

pytestmark = pytest.mark.anyio

# Values that must never appear in a message.
HIDDEN_SUBDOMAIN = "xa-hidden-subdomain"
HIDDEN_KEY = "xa-hidden-key-value"  # pragma: allowlist secret
# Shorthands over TENANTS, for these tests only.
ORGS_ENV = TENANTS.list_var


def subdomain_env(org: str) -> str:
    return TENANTS.var(org, "SUBDOMAIN")


def api_key_env(org: str) -> str:
    return TENANTS.var(org, "API_KEY")


def orgs() -> tuple[str, ...]:
    return TENANTS.names()


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


def test_the_registry_is_cashctrls_scheme() -> None:
    assert TENANTS.source == "cashctrl"
    assert TENANTS.list_var == "CASHCTRL_ORGS"
    assert TENANTS.fields == ("SUBDOMAIN", "API_KEY")
    assert TENANTS.reserved == (DEMO,)


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
    with pytest.raises(ConfigError, match="lower-case") as info:
        orgs()
    assert ORGS_ENV in str(info.value)
    assert name not in str(info.value), "named by position: it may be a value pasted by mistake"


def test_duplicate_names_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,xb,xa")
    with pytest.raises(ConfigError, match="twice"):
        orgs()


def test_require_lists_the_declared_names_and_no_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ORGS_ENV, "xa,xb")
    declare(monkeypatch, "xa")
    declare(monkeypatch, "xb")
    assert TENANTS.require("xa") == "xa"
    with pytest.raises(InvalidRequestError) as info:
        TENANTS.require("nope")
    message = str(info.value)
    assert "'nope'" in message
    assert "xa, xb, demo" in message
    assert HIDDEN_SUBDOMAIN not in message
    assert HIDDEN_KEY not in message
    assert "placeholder" not in message


@pytest.mark.usefixtures("no_demo")
def test_require_without_any_declaration_names_the_variables() -> None:
    with pytest.raises(InvalidRequestError) as info:
        TENANTS.require("demo")
    message = str(info.value)
    for variable in (ORGS_ENV, subdomain_env(DEMO), api_key_env(DEMO)):
        assert variable in message


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


def test_a_changed_key_builds_a_new_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Core keys the cache by every variable of the organisation, the key included."""
    first = client_for(DEMO)
    monkeypatch.setenv(api_key_env(DEMO), "another-placeholder")  # pragma: allowlist secret
    assert client_for(DEMO) is not first


def test_reset_drops_every_cached_client() -> None:
    first = client_for(DEMO)
    TENANTS.reset()
    assert client_for(DEMO) is not first


def test_the_subdomain_is_lower_cased(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(subdomain_env(DEMO), "  Muster-AG ")
    assert client_for(DEMO).config.base_url == "https://muster-ag.cashctrl.com/api/v1"


@pytest.mark.parametrize("value", ["a", "a-b", "a1", "x" * 63])
def test_one_dns_label_is_a_subdomain(value: str) -> None:
    assert check_subdomain(value.upper()) == value


@pytest.mark.parametrize("value", ["", "a_b", "-a", "a-", "a.b", "x" * 64, "evil.com/x?"])
def test_anything_else_is_refused_without_the_value(value: str) -> None:
    with pytest.raises(ValueError, match=r"^not one DNS label$"):
        check_subdomain(value)


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


def test_a_malformed_subdomain_says_what_the_variable_should_hold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``Tenants(hints=...)``: the operator learns the expected form, never the value."""
    monkeypatch.setenv(ORGS_ENV, "xa")
    monkeypatch.setenv(subdomain_env("xa"), f"{HIDDEN_SUBDOMAIN}.cashctrl.com")
    with pytest.raises(ConfigError) as info:
        client_for("xa")
    assert "CASHCTRL_XA_SUBDOMAIN" in str(info.value)
    assert "one DNS label: acme for acme.cashctrl.com" in str(info.value)
    assert HIDDEN_SUBDOMAIN not in str(info.value)
