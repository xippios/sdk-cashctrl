"""The two MCP servers' entry points: ``-read`` and ``-write``, with no alias (conventions §8).

A source with a write server names its servers ``xippios-<source>-mcp-read`` and
``xippios-<source>-mcp-write``, and its old ``xippios-<source>-mcp`` goes without an
alias (sdk-core ADR-0026), which core's family check holds; both servers are named
``xippios-<source>`` (sdk-core ADR-0063, decision 7). The text that tells a user or an
agent how to start a server names only the two entry points.
"""

import re
from pathlib import Path

import pytest

from xippios.cashctrl import mcp, mcp_write

ROOT = Path(__file__).resolve().parents[1]

ENTRY_POINTS = {
    "xippios-cashctrl-mcp-read": "xippios.cashctrl.mcp:run",
    "xippios-cashctrl-mcp-write": "xippios.cashctrl.mcp_write:run",
}

# The files that name an entry point; CHANGELOG.md keeps the old name where it was released.
TEXTS = [
    "README.md",
    "CLAUDE.md",
    "src/xippios/cashctrl/mcp.py",
    "src/xippios/cashctrl/mcp_write.py",
    "src/xippios/cashctrl/tasks_write.py",
]


def test_the_server_names_stay() -> None:
    assert mcp.server.name == "xippios-cashctrl"
    assert mcp_write.server.name == "xippios-cashctrl", "both servers take the source's name"


@pytest.mark.parametrize("path", TEXTS)
def test_the_text_names_only_the_entry_points(path: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    named = set(re.findall(r"xippios-cashctrl-mcp[-a-z]*", text))
    assert named, f"{path} names no entry point"
    assert named <= ENTRY_POINTS.keys(), f"{path} names {sorted(named - ENTRY_POINTS.keys())}"


def test_the_readme_starts_both_servers() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in ENTRY_POINTS:
        assert f'"{name}", "--org"' in readme, name
