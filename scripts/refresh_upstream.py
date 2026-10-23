# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4==4.15.0",
#     "markdownify==1.2.3",
# ]
#
# [tool.uv]
# exclude-newer = "2026-10-23T00:00:00Z"
# ///
"""Refresh the upstream documentation snapshot in ``docs/upstream/`` (``/refresh-upstream``).

The CashCtrl API documentation (https://app.cashctrl.com/static/help/en/api/index.html)
is one server-rendered HTML page. Its table of contents has five general entries
(Introduction, Authentication, Error handling, Language, Examples) and one entry per
module (Account, Common, File, ...), and each module groups several controllers, each
with its operations. ``toc.js`` only scrolls and highlights the table of contents and
``main.css`` only styles the page, so neither is captured. This script fetches the page
once and writes:

- ``<entry>.md``: one Markdown file per top-level entry of the table of contents, named
  after the entry (``error-handling.md``, ``common.md``), holding the page's sections for
  that entry under a two-line provenance header (URL with fragment, fetch date);
- ``FETCHED.md``: regenerated entirely, with one row per file.

Every table on the page is a two-column parameter table (a ``<th>`` name, a ``<td>`` with
labels and description). It becomes a pipe table, or an HTML table where it nests another
table. The script stops on any other table shape, on an unknown icon and on any other
change to the page's structure, so that a new construct is looked at before it is
converted. Files a previous snapshot had and this one does not are removed. The same
upstream on the same day gives the same bytes on disk. No key is needed or read. Run from
the repository root::

    uv run scripts/refresh_upstream.py
"""

import argparse
import gzip
import hashlib
import html
import http.client
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Comment, Tag
from bs4.element import NavigableString, PageElement
from markdownify import ATX, BACKSLASH, MarkdownConverter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs/upstream"
COMMAND = "uv run scripts/refresh_upstream.py"

PAGE_URL = "https://app.cashctrl.com/static/help/en/api/index.html"
USER_AGENT = "xippios-cashctrl refresh_upstream (+https://github.com/xippios/sdk-cashctrl)"
TIMEOUT = 60.0
RETRY_PAUSE = 10.0
"""Seconds before the one retry."""

ICONS = {
    "fa-arrow-right": "\N{RIGHTWARDS ARROW}",
    "fa-chevron-right": "\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}",
}
"""Font Awesome icons the page uses as text, by class; the arrows separate menu items."""

# fmt: off
_HTML_ELEMENTS = frozenset((
    "a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo",
    "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code", "col",
    "colgroup", "data", "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt",
    "em", "embed", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4",
    "h5", "h6", "head", "header", "hgroup", "hr", "html", "i", "iframe", "img", "input", "ins",
    "kbd", "label", "legend", "li", "link", "main", "map", "mark", "menu", "meta", "meter",
    "nav", "noscript", "object", "ol", "optgroup", "option", "output", "p", "param", "picture",
    "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "script", "search", "section",
    "select", "slot", "small", "source", "span", "strong", "style", "sub", "summary", "sup",
    "svg", "table", "tbody", "td", "template", "textarea", "tfoot", "th", "thead", "time",
    "title", "tr", "track", "u", "ul", "var", "video", "wbr", "math", "path", "g", "center",
    "font", "big", "strike", "tt", "nobr",
))
"""HTML element names; a tag with any other name is unescaped text in the source."""
# fmt: on
_STRAY_TAG = re.compile(r"</?([A-Za-z][A-Za-z0-9]*)(?=[\s/>])[^<>]*>")
_TAG_OPEN = re.compile(r"<(?=[A-Za-z/!?])")
_PLACEHOLDER = re.compile(r"XIPPIOSBLOCK(\d+)X")


@dataclass(frozen=True)
class Response:
    """The page as served: status, body (decompressed) and the validators sent with it."""

    status: int
    body: bytes
    etag: str | None
    last_modified: str | None


@dataclass(frozen=True)
class Part:
    """One top-level entry of the table of contents and the page sections it covers."""

    label: str
    fragment: str
    sections: tuple[Tag, ...]

    @property
    def file(self) -> str:
        """The snapshot file name: the entry's label, slugified."""
        return re.sub(r"[^a-z0-9]+", "-", self.label.lower()).strip("-") + ".md"

    @property
    def url(self) -> str:
        """The page URL with the entry's own fragment from the table of contents."""
        return PAGE_URL + self.fragment


@dataclass(frozen=True)
class _Row:
    """One row of a parameter table: the name cell, its labels and the description cell."""

    name: Tag
    labels: tuple[str, ...]
    description: Tag


class _RetryableError(Exception):
    """A network error or a 5xx: worth one more attempt."""


def _log(message: str) -> None:
    print(message, flush=True)  # noqa: T201


def _get(url: str) -> Response:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body: bytes = response.read()
            status: int = response.status
            headers = response.headers
    except urllib.error.HTTPError as error:
        if error.code >= 500:
            raise _RetryableError(f"HTTP {error.code} {error.reason}") from None
        raise SystemExit(f"GET {url}: HTTP {error.code} {error.reason}") from None
    except (http.client.HTTPException, OSError) as error:  # URLError is an OSError
        raise _RetryableError(str(error)) from None
    if status != 200:
        raise SystemExit(f"GET {url}: expected HTTP 200, got {status}")
    content_type = headers.get("Content-Type", "").split(";")[0].strip().lower()
    if content_type != "text/html":
        raise SystemExit(f"GET {url}: expected text/html, got {content_type!r}")
    encoding = headers.get("Content-Encoding", "identity").strip().lower()
    if encoding == "gzip":
        body = gzip.decompress(body)
    elif encoding != "identity":
        raise SystemExit(f"GET {url}: unexpected Content-Encoding {encoding!r}")
    return Response(status, body, headers.get("ETag"), headers.get("Last-Modified"))


def fetch(url: str) -> Response:
    """GET ``url``; retry once on a network error or a 5xx."""
    try:
        return _get(url)
    except _RetryableError as error:
        _log(f"  {url}: {error}; retrying once in {RETRY_PAUSE:.0f} s")
    time.sleep(RETRY_PAUSE)
    try:
        return _get(url)
    except _RetryableError as error:
        raise SystemExit(f"GET {url}: {error} (after one retry)") from None


def _page_changed(what: str) -> SystemExit:
    return SystemExit(
        f"The documentation page changed: {what}.\n"
        f"Inspect {PAGE_URL} and update scripts/refresh_upstream.py. Nothing was written."
    )


def escape_stray_tags(source: str) -> tuple[str, list[str]]:
    """Turn ``<Name>`` that is no HTML element back into text, as upstream meant it.

    The page writes ``$customField<ID>`` unescaped; a parser would take ``<ID>`` for an
    element and drop it, and a browser hides it. Escaping it keeps the text.
    """
    stray: list[str] = []

    def keep(match: re.Match[str]) -> str:
        if match[1].lower() in _HTML_ELEMENTS:
            return match[0]
        stray.append(match[0])
        return html.escape(match[0])

    return _STRAY_TAG.sub(keep, source), stray


def _classes(tag: Tag) -> list[str]:
    return [str(name) for name in tag.get_attribute_list("class") if name]


def _text(node: PageElement) -> str:
    return re.sub(r"\s+", " ", node.get_text()).strip()


def split_page(soup: BeautifulSoup) -> list[Part]:
    """Group the page's sections by the top-level entries of its table of contents."""
    toc = soup.select_one("aside nav.toc > ul")
    main = soup.select_one("main.content")
    if toc is None or main is None:
        raise _page_changed("no table of contents (aside nav.toc > ul) or no main.content")

    entries: list[tuple[str, str, set[str]]] = []
    for item in toc.select(":scope > li"):
        link = item.select_one(":scope > a[href]")
        href = link.get("href") if link else None
        if link is None or not isinstance(href, str) or not href.startswith("#"):
            raise _page_changed(f"a table-of-contents entry without a fragment link: {item}")
        if "manual" in _classes(item):
            fragments = {href}
        elif "module" in _classes(item):
            fragments = {
                str(a.get("href")) for a in item.select(":scope > ul > li.controller > a[href]")
            }
        else:
            raise _page_changed(f"a table-of-contents entry of class {_classes(item)}")
        entries.append((_text(link), href, fragments))

    sections: list[list[Tag]] = [[] for _ in entries]
    last = 0
    for child in main.children:
        if isinstance(child, NavigableString) and (isinstance(child, Comment) or not child.strip()):
            continue
        if isinstance(child, Tag) and child.name == "footer":
            continue
        if not (isinstance(child, Tag) and child.name == "section"):
            raise _page_changed(f"unexpected content in main.content: {str(child)[:80]!r}")
        anchor = child.select_one("a[id]")
        fragment = f"#{anchor.get('id')}" if anchor else None
        owners = [i for i, (_, _, fragments) in enumerate(entries) if fragment in fragments]
        if len(owners) != 1:
            raise _page_changed(f"section {fragment} is not under one table-of-contents entry")
        if owners[0] < last:
            raise _page_changed(f"section {fragment} comes after a later table-of-contents entry")
        last = owners[0]
        sections[owners[0]].append(child)

    parts = [
        Part(label, href, tuple(found))
        for (label, href, _), found in zip(entries, sections, strict=True)
    ]
    empty = [part.label for part in parts if not part.sections]
    names = [part.file for part in parts]
    if empty or len(set(names)) != len(names) or "fetched.md" in names:
        raise _page_changed(f"entries without sections {empty} or clashing file names {names}")
    return parts


class _Converter(MarkdownConverter):
    """markdownify with ATX headings, backslash line breaks and one line per paragraph.

    The page's HTML source breaks paragraphs at arbitrary points; one line per paragraph
    keeps every sentence on one line, so a search for a phrase finds it.
    """

    def __init__(self) -> None:
        super().__init__(
            heading_style=ATX,
            bullets="-",
            escape_underscores=False,
            newline_style=BACKSLASH,
            wrap=True,
            wrap_width=None,
        )

    def escape(self, text: str, parent_tags: set[str]) -> str:
        """Escape ``*`` and a ``<`` that would open an HTML tag; leave ``_`` alone.

        Upstream names such as ``update_attachments.json`` are full of underscores.
        """
        return _TAG_OPEN.sub(r"\\<", text.replace("*", r"\*"))


def clean(section: Tag) -> None:
    """Drop navigation and duplicates, turn icons into text, make links absolute."""
    for element in section.select(".breadcrumbs, code.name.mobile, script, style, noscript"):
        element.decompose()
    for comment in section.find_all(string=lambda value: isinstance(value, Comment)):
        comment.extract()
    for icon in section.select('[class*="fa-"]'):
        names = [name for name in _classes(icon) if name.startswith("fa-")]
        known = [ICONS[name] for name in names if name in ICONS]
        if len(known) != 1:
            raise _page_changed(f"an icon with classes {_classes(icon)}; add it to ICONS")
        icon.replace_with(NavigableString(known[0]))
    for image in section.select("img"):
        alt = str(image.get("alt") or "").strip()
        image.replace_with(alt or Path(urlsplit(str(image.get("src") or "")).path).name)
    for link in section.select("a"):
        href = link.get("href")
        if isinstance(href, str):
            link.attrs = {"href": urljoin(PAGE_URL, href.strip())}
        elif _text(link):
            link.unwrap()
        else:
            link.decompose()  # an anchor only: <a id="/account"></a>


def _fence(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}\n{text}\n{fence}"


def _block_text(element: Tag) -> str:
    """Text of a block shown with collapsed whitespace, where only ``<br>`` breaks lines."""
    lines = [""]
    for node in element.descendants:
        if isinstance(node, Tag) and node.name == "br":
            lines.append("")
        elif isinstance(node, NavigableString) and not isinstance(node, Comment):
            lines[-1] += str(node)
    return "\n".join(re.sub(r"\s+", " ", line).strip() for line in lines).strip("\n")


def _pre_text(element: Tag) -> str:
    """Text of a ``<pre>`` as shown: verbatim, without blank first and last lines."""
    text = element.get_text().replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _rows(table: Tag) -> list[_Row]:
    """The rows of a parameter table; each is a ``<th>`` name and a ``<td>`` description."""
    rows: list[_Row] = []
    for tr in table.select(":scope > tr, :scope > thead > tr, :scope > tbody > tr"):
        cells = [cell for cell in tr.children if isinstance(cell, Tag)]
        loose = [n for n in tr.children if isinstance(n, NavigableString) and n.strip()]
        if [cell.name for cell in cells] != ["th", "td"] or loose:
            raise _page_changed(f"a table row that is not <th> + <td>: {str(tr)[:160]!r}")
        if any(cell.has_attr("rowspan") or cell.has_attr("colspan") for cell in cells):
            raise _page_changed(f"a parameter table with merged cells: {str(tr)[:160]!r}")
        name, description = cells
        labels: tuple[str, ...] = ()
        box = description.select_one(":scope > div.labels")
        if box is not None:
            labels = tuple(_text(label) for label in box.select(":scope > div"))
            box.decompose()
        rows.append(_Row(name, labels, description))
    if not rows:
        raise _page_changed(f"a table without rows: {str(table)[:160]!r}")
    return rows


def _md_cell(cell: Tag) -> str:
    """A cell as one line of Markdown for a pipe table; paragraphs joined by ``<br>``."""
    markdown = _Converter().convert_soup(BeautifulSoup(cell.decode_contents(), "html.parser"))
    markdown = markdown.replace("\\\n", "<br>")
    paragraphs = (re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", markdown))
    return "<br>".join(p for p in paragraphs if p).replace("|", r"\|")


def _pipe_table(rows: list[_Row]) -> str:
    """A pipe table with an empty header row: name, labels (if any), description."""
    with_labels = any(row.labels for row in rows)
    width = 3 if with_labels else 2
    lines = ["|" + " |" * width, "|" + " --- |" * width]
    for row in rows:
        cells = [_md_cell(row.name)]
        if with_labels:
            cells.append(", ".join(row.labels))
        cells.append(_md_cell(row.description))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _html_inline(node: PageElement) -> str:
    """Inline HTML reduced to code, links, line breaks and emphasis; other tags unwrapped."""
    if isinstance(node, NavigableString):
        if isinstance(node, Comment):
            return ""
        return html.escape(re.sub(r"\s+", " ", str(node)), quote=False)
    if not isinstance(node, Tag):
        return ""
    inner = "".join(_html_inline(child) for child in node.children)
    href = node.get("href")
    match node.name:
        case "code":
            return f"<code>{html.escape(_text(node), quote=False)}</code>"
        case "a" if isinstance(href, str):
            return f'<a href="{html.escape(href)}">{inner.strip()}</a>'
        case "br":
            return "<br>"
        case "strong" | "b":
            return f"<strong>{inner.strip()}</strong>"
        case "em" | "i":
            return f"<em>{inner.strip()}</em>"
        case _:
            return inner


def _html_cell(tag: str, cell: Tag) -> str:
    """A cell for an HTML table: paragraphs joined by ``<br>``, nested tables on own lines."""
    pieces: list[tuple[str, str]] = []
    run = ""
    for child in [*cell.children, None]:
        if child is None or (isinstance(child, Tag) and child.name in ("p", "div", "table")):
            if run.strip():
                pieces.append(("text", run.strip()))
            run = ""
            if isinstance(child, Tag) and child.name == "table":
                pieces.append(("table", _html_table(_rows(child))))
            elif isinstance(child, Tag) and _html_inline(child).strip():
                pieces.append(("text", _html_inline(child).strip()))
        else:
            run += _html_inline(child)
    content = ""
    previous = ""
    for kind, text in pieces:
        if kind == "table":
            content += f"\n{text}\n"
        else:
            content += ("<br>" if previous == "text" else "") + text
        previous = kind
    return f"<{tag}>{content}</{tag}>"


def _html_table(rows: list[_Row]) -> str:
    """An HTML table with the pipe table's columns, one row per line, nested tables inline."""
    with_labels = any(row.labels for row in rows)
    lines = ["<table>"]
    for row in rows:
        cells = [_html_cell("th", row.name)]
        if with_labels:
            cells.append(f"<td>{html.escape(', '.join(row.labels), quote=False)}</td>")
        cells.append(_html_cell("td", row.description))
        lines.append("<tr>" + "".join(cells) + "</tr>")
    lines.append("</table>")
    return "\n".join(lines)


def render_table(table: Tag) -> str:
    """A parameter table as a pipe table, or as HTML where it nests another table."""
    rows = _rows(table)
    if table.select_one("table") is not None:
        return _html_table(rows)
    return _pipe_table(rows)


def render_block(element: Tag) -> str:
    """A table, or an endpoint or example as a fenced code block."""
    if element.name == "table":
        return render_table(element)
    if element.name == "pre":
        return _fence(_pre_text(element))
    return _fence(_block_text(element))


def convert_section(soup: BeautifulSoup, section: Tag) -> str:
    """One ``section.controller`` of the page as Markdown.

    Tables, endpoints and examples are rendered on their own and put back in place of a
    placeholder after markdownify has converted the rest.
    """
    clean(section)
    blocks: list[str] = []
    held: set[int] = set()
    for element in section.select("table, pre, .example, .endpoint"):  # document order
        if any(id(parent) in held for parent in element.parents):
            continue  # inside a block already rendered, such as a nested table
        placeholder = soup.new_tag("p")
        placeholder.string = f"XIPPIOSBLOCK{len(blocks)}X"
        blocks.append(render_block(element))
        held.add(id(element))
        element.replace_with(placeholder)

    markdown = _Converter().convert_soup(section).replace("\xa0", " ")
    lines = [line.rstrip() for line in markdown.strip().split("\n")]
    markdown = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    found = [int(index) for index in _PLACEHOLDER.findall(markdown)]
    if found != list(range(len(blocks))):
        raise SystemExit(f"Conversion lost or reordered blocks: {found}; nothing was written.")
    return _PLACEHOLDER.sub(lambda match: blocks[int(match[1])], markdown)


def render_part(soup: BeautifulSoup, part: Part, day: str) -> str:
    """One snapshot file: the provenance header, then the entry's sections."""
    body = "\n\n".join(convert_section(soup, section) for section in part.sections)
    return f"Source: <{part.url}>\\\nFetched: {day} (UTC)\n\n{body}\n"


def _headings(markdown: str) -> int:
    count, fenced = 0, False
    for line in markdown.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{2,3} ", line):
            count += 1
    return count


def render_fetched(parts: list[Part], response: Response, day: str) -> str:
    """The whole of ``FETCHED.md``."""
    digest = hashlib.sha256(response.body).hexdigest()
    lines = [
        "# Upstream documentation snapshot \N{EM DASH} CashCtrl",
        "",
        "Source of truth for every endpoint wrapper (ADR-0003). Files in this directory are",
        f"fetched from {PAGE_URL} by",
        "`scripts/refresh_upstream.py` (`/refresh-upstream`), never edited by hand, and",
        "refreshed deliberately by PR so that changes show up as diffs. This file is",
        "generated by the same script.",
        "",
        "## How the page is captured",
        "",
        "The documentation is one server-rendered HTML page whose table of contents links to",
        "its sections by fragment (`#intro`, `#/account`). The script fetches the page once",
        "and writes one Markdown file per top-level entry of the table of contents, named",
        "after the entry: the five general sections, then one file per module holding all of",
        "the module's controllers. Each file starts with the URL of its entry and the fetch",
        "date. Headings keep the page's levels: `##` controller, `###` operation, `####`",
        "Parameters, Endpoint or Example; each paragraph is one line.",
        "",
        "Navigation (table of contents, breadcrumbs, anchors), scripts, styles, the footer",
        "and the parameter names the page repeats for small screens are dropped; the arrow",
        "icons between menu items become \N{RIGHTWARDS ARROW}. `toc.js` (scrolling and",
        "table-of-contents highlighting) and `main.css` are not captured. Endpoints, curl",
        "examples and JSON responses become fenced code blocks, verbatim. Every table on the",
        "page is a two-column parameter table; it becomes a pipe table with an empty header",
        "row and the columns name, labels (mandatory or optional, data type, limits) and",
        "description. A table that nests another (the fields of a JSON parameter) cannot be a",
        "pipe table and stays an HTML table with the same columns, reduced to code, links and",
        "line breaks. Links into the page are absolute.",
        "",
        f"Regenerate: `{COMMAND}`",
        "",
        "## Files",
        "",
        "The page as fetched:",
        "",
        f"- HTTP {response.status}, {len(response.body)} bytes, sha256 `{digest}`",
        f"- ETag `{response.etag or 'not sent'}`",
        f"- Last-Modified {response.last_modified or 'not sent'}",
        "",
        "Fetched is the UTC date of the run.",
        "",
        "| File | URL | Fetched |",
        "| --- | --- | --- |",
    ]
    lines += [f"| {part.file} | {part.url} | {day} |" for part in parts]
    return "\n".join(lines) + "\n"


def write_snapshot(out: Path, files: dict[str, str], fetched_md: str) -> None:
    """Write every file, drop files the new snapshot no longer has, write ``FETCHED.md``."""
    if out.exists() and any(out.iterdir()) and not (out / "FETCHED.md").is_file():
        raise SystemExit(f"{out} is neither empty nor a snapshot (no FETCHED.md); not writing")
    out.mkdir(parents=True, exist_ok=True)
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name != "FETCHED.md" and path.name not in files:
            path.unlink()
            _log(f"  removed {path.name}: no longer upstream")
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8", newline="\n")
    (out / "FETCHED.md").write_text(fetched_md, encoding="utf-8", newline="\n")


def main() -> None:
    """Fetch the page, split and convert it, then write the snapshot."""
    parser = argparse.ArgumentParser(description="Refresh docs/upstream/ from CashCtrl.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="snapshot directory")
    out: Path = parser.parse_args().out
    day = datetime.now(UTC).date().isoformat()

    _log(f"Page: {PAGE_URL}")
    response = fetch(PAGE_URL)
    digest = hashlib.sha256(response.body).hexdigest()
    _log(
        f"  HTTP {response.status}, {len(response.body)} bytes, sha256 {digest}, "
        f"ETag {response.etag or '-'}, Last-Modified {response.last_modified or '-'}"
    )
    try:
        source = response.body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SystemExit(f"GET {PAGE_URL}: not UTF-8 ({error})") from None
    if _PLACEHOLDER.search(source):
        raise _page_changed("the page contains the converter's placeholder text")
    source, stray = escape_stray_tags(source)
    if stray:
        _log(f"  kept as text, not HTML elements: {', '.join(sorted(set(stray)))}")

    soup = BeautifulSoup(source, "html.parser")
    parts = split_page(soup)
    expected = sum(len(s.select("h2, h3")) for part in parts for s in part.sections)
    files = {part.file: render_part(soup, part, day) for part in parts}
    converted = sum(_headings(text) for text in files.values())
    if converted != expected:
        raise SystemExit(f"{expected} h2/h3 headings on the page, {converted} converted")
    for part in parts:
        _log(f"  {part.file}: {part.label}, {len(part.sections)} sections, {part.url}")
    write_snapshot(out, files, render_fetched(parts, response, day))
    _log(f"Wrote {len(files)} files and FETCHED.md under {out}")


if __name__ == "__main__":
    main()
