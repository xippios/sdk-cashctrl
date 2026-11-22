"""The capture script's own code and its declaration on core's frame, offline: nothing is fetched.

The fetch, the attribution check, ``FETCHED.md``, the write and ``--check`` are the frame's,
``xippios.core.refresh``, which core's tests hold (sdk-core ADR-0046). What stays here is
the script's own: the declaration of its one page, split into one Markdown file per entry
of the table of contents, and its ``split`` and ``note`` hooks. ``OBSERVED.md`` is the one
file under ``docs/upstream/`` written by hand (conventions §3): an entry whose file would
take its name stops the run, in any letter case.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from bs4 import BeautifulSoup
from xippios.core import refresh
from xippios.core.refresh import Page, Statement

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh_upstream.py"


@pytest.fixture(scope="module")
def script() -> ModuleType:
    """``scripts/refresh_upstream.py`` imported as a module; the frame's ``run`` is not called."""
    spec = importlib.util.spec_from_file_location("refresh_upstream", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def page(*labels: str, notice: str = "\N{COPYRIGHT SIGN} 2026 CashCtrl Ltd.") -> str:
    """A page of the documentation's shape, one general entry and one section per label."""
    entries = "".join(
        f'<li class="manual"><a href="#e{index}">{label}</a></li>'
        for index, label in enumerate(labels)
    )
    sections = "".join(
        f'<section><a id="e{index}"></a><h2>{label}</h2><p>About {label}.</p></section>'
        for index, label in enumerate(labels)
    )
    return (
        f'<html><body><aside><nav class="toc"><ul>{entries}</ul></nav></aside>'
        f'<main class="content">{sections}<footer><img alt="{notice}"></footer></main>'
        "</body></html>"
    )


def answer(script: ModuleType, body: str, content_type: str = "text/html") -> refresh.Response:
    """The page's answer, as the frame hands it to a hook: an input of the test, not an
    answer from CashCtrl.

    Core's own ``Response``, named by its module: the check of a built answer reads a bare
    ``Response(...)`` as httpx's, an answer a route serves.
    """
    return refresh.Response(
        url=script.PAGE_URL,
        status=200,
        body=body.encode(),
        content_type=f"{content_type}; charset=utf-8",
        etag=None,
        last_modified=None,
        redirects=(),
    )


def test_the_snapshot_declares_its_one_page_split_by_the_script(script: ModuleType) -> None:
    snapshot = script.SNAPSHOT
    assert snapshot.pages == (Page(script.PAGE_URL, split=True),)
    assert snapshot.split is script.split
    assert snapshot.note is script.note
    assert (snapshot.name, snapshot.slug) == ("CashCtrl", "cashctrl")
    assert snapshot.out == SCRIPT.parents[1] / "docs" / "upstream"


def test_the_attribution_records_the_notice_and_the_terms(script: ModuleType) -> None:
    """The footer's notice stands in its logo's alt text, which the frame does not read, so
    ``split`` checks it; the link to the terms is in the page's text, which the frame checks."""
    notice, terms = script.SNAPSHOT.attribution
    assert notice == Statement(script.NOTICE, "", where=notice.where)
    assert "split" in notice.where
    assert terms.text == "Terms of Service"
    assert (terms.source, terms.link) == (script.PAGE_URL, "https://cashctrl.com/en/about/terms")


def test_split_writes_one_file_per_entry_under_its_url(script: ModuleType) -> None:
    files = script.split(script.SNAPSHOT.pages[0], answer(script, page("Introduction", "Account")))
    assert list(files) == ["introduction.md", "account.md"]
    assert files["introduction.md"].decode() == (
        f"Source: <{script.PAGE_URL}#e0>\n\n## Introduction\n\nAbout Introduction.\n"
    )


def test_split_stops_on_another_notice_or_another_type(script: ModuleType) -> None:
    first = script.SNAPSHOT.pages[0]
    with pytest.raises(SystemExit, match=r"the footer's copyright notice is "):
        script.split(first, answer(script, page("Introduction", notice="(c) 2027 CashCtrl")))
    with pytest.raises(SystemExit, match=r"expected text/html, got 'application/json'"):
        script.split(first, answer(script, page("Introduction"), "application/json"))


def test_the_note_names_the_files_that_keep_a_table_as_html(script: ModuleType) -> None:
    def row(content: bytes) -> object:
        return type("Row", (), {"content": content, "note": ""})()

    assert script.note(row(b"Source: <x>\n\n<table>\n</table>\n")) == "nested tables kept as HTML"
    assert script.note(row(b"Source: <x>\n\n| a | b |\n")) == ""


def test_an_entry_that_would_be_written_as_observed_is_refused(script: ModuleType) -> None:
    """In lower case too, where the frame refuses ``OBSERVED.md`` and ``FETCHED.md`` by name."""
    with pytest.raises(SystemExit, match=r"clashing file names .*observed\.md"):
        script.split_page(BeautifulSoup(page("Introduction", "Observed"), "html.parser"))
