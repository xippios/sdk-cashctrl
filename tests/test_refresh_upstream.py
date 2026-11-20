"""The capture script and ``docs/upstream/OBSERVED.md``, offline: nothing is fetched.

``OBSERVED.md`` is the one file under ``docs/upstream/`` written by hand, the notes on what
upstream does but never documents (conventions §3): the script lists it in ``FETCHED.md``
where it exists, never writes or removes it, and refuses a page entry that would take its
name.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from bs4 import BeautifulSoup

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh_upstream.py"
ROW = (
    "| OBSERVED.md | - | - | written by hand: what upstream does but never documents; "
    "not fetched or checked |"
)


@pytest.fixture(scope="module")
def script() -> ModuleType:
    """``scripts/refresh_upstream.py`` imported as a module; ``main`` is not run."""
    spec = importlib.util.spec_from_file_location("refresh_upstream", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def page(*labels: str) -> BeautifulSoup:
    """A page of the documentation's shape, one general entry and one section per label."""
    entries = "".join(
        f'<li class="manual"><a href="#e{index}">{label}</a></li>'
        for index, label in enumerate(labels)
    )
    sections = "".join(
        f'<section><a id="e{index}"></a><h2>{label}</h2></section>'
        for index, label in enumerate(labels)
    )
    return BeautifulSoup(
        f'<aside><nav class="toc"><ul>{entries}</ul></nav></aside>'
        f'<main class="content">{sections}</main>',
        "html.parser",
    )


def fetched(script: ModuleType, *, observed: bool) -> str:
    parts = script.split_page(page("Introduction"))
    files = {part.file: "Source: <x>\n" for part in parts}
    response = script.Response(status=200, body=b"<html></html>", etag=None, last_modified=None)
    return str(
        script.render_fetched(
            parts, files, response, "2026-11-20T00:00:00Z", "2026", observed=observed
        )
    )


def test_fetched_lists_observed_in_a_row_of_its_own_where_it_exists(script: ModuleType) -> None:
    with_file = fetched(script, observed=True)
    assert with_file.splitlines()[-1] == ROW
    assert "never edited by hand but `OBSERVED.md`, where it exists" in with_file.replace("\n", " ")
    without = fetched(script, observed=False)
    assert "| OBSERVED.md |" not in without
    assert without.splitlines()[-1].startswith("| introduction.md |")


def test_a_snapshot_keeps_observed_and_removes_a_stale_file(
    script: ModuleType, tmp_path: Path
) -> None:
    (tmp_path / "FETCHED.md").write_text("old\n", encoding="utf-8")
    (tmp_path / "OBSERVED.md").write_text("a note\n", encoding="utf-8")
    (tmp_path / "gone.md").write_text("stale\n", encoding="utf-8")
    script.write_snapshot(tmp_path, {"introduction.md": "Source: <x>\n"}, "new\n")
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "FETCHED.md",
        "OBSERVED.md",
        "introduction.md",
    ]
    assert (tmp_path / "OBSERVED.md").read_text(encoding="utf-8") == "a note\n"


def test_an_entry_that_would_be_written_as_observed_is_refused(script: ModuleType) -> None:
    with pytest.raises(SystemExit, match=r"clashing file names .*observed\.md"):
        script.split_page(page("Introduction", "Observed"))
