"""The package contract: what the package ships and declares, offline and in process.

``mcp.build()`` and ``mcp_write.build()`` are the tool sets a host serves (conventions §8;
sdk-core ADR-0026, amendment 2026-11-18, points c and d), and ``_client.ENV_VARS`` the
variables the package reads, for that host.
"""

import importlib.util
from pathlib import Path

import xippios.cashctrl


def test_the_package_ships_no_reference_scaffold() -> None:
    """The package packages no list (``has_reference_data`` is false), so it has no
    ``params`` or ``enums`` module and no ``reference/`` directory."""
    for module in ("params", "enums"):
        assert importlib.util.find_spec(f"xippios.cashctrl.{module}") is None, module
    (package,) = xippios.cashctrl.__path__
    assert not (Path(package) / "reference").exists()
