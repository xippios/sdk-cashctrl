"""The package contract: what the package ships and declares, offline and in process.

``mcp.build()`` and ``mcp_write.build()`` are the tool sets a host serves (conventions §8;
sdk-core ADR-0026, amendment 2026-11-18, points c and d), and ``_client.ENV_VARS`` the
variables the package reads, for that host. Core's family check holds the read server's
part and the entry points; what stays here is the package's own.
"""

from xippios.core import EnvVar

from xippios.cashctrl import mcp_write
from xippios.cashctrl._client import ENV_VARS, TENANTS


def test_env_vars_name_the_organisations_and_their_pair_secret() -> None:
    """The tenant list first, then each organisation's key and subdomain, both secret: the
    subdomain is kept like a key, never in a file, a log line or a report."""
    assert (
        EnvVar("CASHCTRL_ORGS", secret=False, required=False),
        EnvVar("CASHCTRL_<NAME>_API_KEY", secret=True, required=True),
        EnvVar("CASHCTRL_<NAME>_SUBDOMAIN", secret=True, required=True),
    ) == ENV_VARS
    assert TENANTS.list_var == ENV_VARS[0].name_or_pattern
    assert {f"CASHCTRL_<NAME>_{field}" for field in TENANTS.fields} == {
        var.name_or_pattern for var in ENV_VARS[1:]
    }
    assert mcp_write.ENV_VARS is ENV_VARS, "the write server names the client's list"
