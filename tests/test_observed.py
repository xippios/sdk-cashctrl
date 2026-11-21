"""``docs/upstream/OBSERVED.md`` as committed: what CashCtrl does that the snapshot never states.

sdk-core's conventions §3 keep these notes in one file written by hand, which the capture
script neither writes nor checks and ``FETCHED.md`` lists in a row of its own, and give
each note its evidence: the probe that showed it, its date, its operation and its sample, a
recording under ``tests/fixtures/``, or its request where the probe kept no answer. A note
here is a ``###`` section, and its last paragraph, ``Probe:``, names them. The package's
own text, ``CLAUDE.md``, ``README.md``, ``docs/demo-org.md`` and every module under
``src/xippios/cashctrl/``, keeps what its reader needs and no probe: the probes stand in
``OBSERVED.md`` alone.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "docs" / "upstream"
OBSERVED = UPSTREAM / "OBSERVED.md"
ROW = (
    "| OBSERVED.md | - | - | written by hand: what upstream does but never documents; "
    "not fetched or checked |"
)
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
CITED = re.compile(r"`((?:tests|docs|src|scripts)/[^`\s]+\.[a-z]+)`")
OPERATION = re.compile(r"`(GET|POST) ([a-z][a-z0-9_/]*(?:\.[a-z]+)?)(?:\?[^`\s]*)?`")
NOT_KEPT = "kept no answer"
ENDPOINT_BLOCK = re.compile(
    r"^#### Endpoint\n\n(?P<fence>`{3,})\n(?P<method>[A-Z]+) /api/v1/(?P<path>\S+)\n(?P=fence)$",
    re.MULTILINE,
)
PROBE = re.compile(
    r"\b(?:observed|verified|verification|seen|probed)\b(?:(?!\.\s).){0,60}?\b20\d\d-\d\d-\d\d\b"
    r"|\b20\d\d-\d\d-\d\d\b(?:(?!\.\s).){0,25}?\b(?:observed|seen)\b"
    r"|\bobserved in [A-Z][a-z]+ 20\d\d\b"
    r"|\((?:observed|verified)\b",
    re.IGNORECASE,
)
"""A probe in prose: observed, verified or seen with its date, or a citation ``(observed``."""
RULES = [ROOT / "CLAUDE.md", ROOT / "README.md", ROOT / "docs" / "demo-org.md"]
"""The package's documents, which point to ``OBSERVED.md`` and keep no probe."""
SCRIPTS = [ROOT / "scripts" / "record_fixture.py"]
"""The scripts whose text states what upstream does, which keep no probe either."""
WRAPPED = re.compile(r'\A"""``(GET|POST) /api/v1/([^`\s]+)``')
"""A wrapper module's first line: the operation it wraps."""


def text() -> str:
    return OBSERVED.read_text(encoding="utf-8")


def notes() -> dict[str, list[str]]:
    """Each note's heading and its paragraphs, each paragraph's lines joined by a space.

    A ``##`` heading groups notes and is none itself.
    """
    parts = re.split(r"^(##|###) (.+)$", text(), flags=re.MULTILINE)
    return {
        heading: [" ".join(block.split()) for block in body.split("\n\n") if block.strip()]
        for level, heading, body in zip(parts[1::3], parts[2::3], parts[3::3], strict=True)
        if level == "###"
    }


def documented() -> set[tuple[str, str]]:
    """Each method and path the snapshot's Endpoint blocks document."""
    found: set[tuple[str, str]] = set()
    for page in sorted(UPSTREAM.glob("*.md")):
        for block in ENDPOINT_BLOCK.finditer(page.read_text(encoding="utf-8")):
            found.add((block["method"], block["path"]))
    return found


def test_fetched_md_lists_observed_md_in_a_row_of_its_own() -> None:
    fetched = (UPSTREAM / "FETCHED.md").read_text(encoding="utf-8")
    assert fetched.splitlines()[-1] == ROW
    assert "never edited by hand but `OBSERVED.md`" in " ".join(fetched.split())


def test_every_note_ends_with_its_probe() -> None:
    """The date, an operation of the snapshot, and a recording or a request."""
    found = notes()
    assert len(found) >= 20
    for heading, paragraphs in found.items():
        probe = paragraphs[-1]
        assert probe.startswith("Probe: "), heading
        assert DATE.search(probe), heading
        assert OPERATION.search(probe), heading
        assert "`tests/fixtures/" in probe or NOT_KEPT in probe, heading


def test_every_probe_a_note_names_has_its_own_date() -> None:
    """A recording's day, from its ``recorded_at``, is a date of its ``Probe:`` paragraph,
    and a probe that kept no answer has a date in its own sentence."""
    for heading, paragraphs in notes().items():
        probe = paragraphs[-1]
        for path in CITED.findall(probe):
            if path.startswith("tests/fixtures/"):
                recorded = json.loads((ROOT / path).read_text("utf-8"))["recorded_at"]
                assert recorded[:10] in DATE.findall(probe), f"{heading}: {path}"
        for sentence in re.split(r"(?<=\.) (?=[A-Z])", probe):
            if NOT_KEPT in sentence:
                assert DATE.search(sentence), f"{heading}: {sentence}"
                assert OPERATION.search(sentence), f"{heading}: {sentence}"


def test_every_operation_is_one_the_snapshot_documents() -> None:
    named = {(method, path) for method, path in OPERATION.findall(text())}
    assert named
    assert sorted(named - documented()) == []


def test_every_file_the_notes_cite_exists() -> None:
    cited = CITED.findall(text())
    assert cited
    assert [path for path in cited if not (ROOT / path).is_file()] == []


def test_the_documents_point_to_the_notes() -> None:
    for path in RULES:
        assert "docs/upstream/OBSERVED.md" in path.read_text(encoding="utf-8"), path.name


def test_the_package_keeps_no_probe() -> None:
    """A probe, kept or not, stands in ``OBSERVED.md`` alone; the rule it backs stays."""
    sources = sorted((ROOT / "src" / "xippios" / "cashctrl").rglob("*.py"))
    found = {
        str(path.relative_to(ROOT)): [match[0] for match in PROBE.finditer(" ".join(text.split()))]
        for path in [*RULES, *SCRIPTS, *sources]
        if (text := path.read_text(encoding="utf-8"))
    }
    assert {path: probes for path, probes in found.items() if probes} == {}


def test_every_wrapper_that_points_to_the_notes_has_its_note() -> None:
    """A wrapper whose docstring points to ``OBSERVED.md`` wraps an operation a probe names.

    So a pointer to a note that does not exist fails, and so does a wrapper that states
    its answer's shape without the pointer.
    """
    probed = {
        (method, path)
        for paragraphs in notes().values()
        for method, path in OPERATION.findall(paragraphs[-1])
    }
    missing, unpointed = [], []
    for module in sorted((ROOT / "src" / "xippios" / "cashctrl" / "api").glob("*.py")):
        source = module.read_text(encoding="utf-8")
        wrapped = WRAPPED.match(source)
        if wrapped is None:
            continue
        points = "docs/upstream/OBSERVED.md" in source
        if points and (wrapped[1], wrapped[2]) not in probed:
            missing.append(module.name)
        if not points and re.search(r"\bIts answer\b|\{\"total\": \d", source):
            unpointed.append(module.name)
    assert (missing, unpointed) == ([], [])
