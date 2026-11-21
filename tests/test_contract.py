"""The package contract: what the package ships and declares, offline and in process.

``mcp.build()`` and ``mcp_write.build()`` are the tool sets a host serves (conventions §8;
sdk-core ADR-0026, amendment 2026-11-18, points c and d), and ``_client.ENV_VARS`` the
variables the package reads, for that host.
"""

import importlib.util
from pathlib import Path

from xippios.core import EnvVar

import xippios.cashctrl
from xippios.cashctrl import mcp, mcp_write
from xippios.cashctrl._client import ENV_VARS, TENANTS


def test_the_package_ships_no_reference_scaffold() -> None:
    """The package packages no list (``has_reference_data`` is false), so it has no
    ``params`` or ``enums`` module and no ``reference/`` directory."""
    for module in ("params", "enums"):
        assert importlib.util.find_spec(f"xippios.cashctrl.{module}") is None, module
    (package,) = xippios.cashctrl.__path__
    assert not (Path(package) / "reference").exists()


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
    assert mcp.ENV_VARS is ENV_VARS
    assert mcp_write.ENV_VARS is ENV_VARS, "both servers name the client's list"
