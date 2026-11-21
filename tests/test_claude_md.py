"""``CLAUDE.md`` stays under 37,000 characters, below the 40,000 at which Claude Code cuts it.

A rule past the cut is never read, so the file keeps each rule in a sentence and a pointer,
and its reference text stands in the files it points to: ``docs/write-tools.md``,
``docs/demo-org.md``, ``docs/upstream/OBSERVED.md``, the README and the docstrings of the code.
The bound leaves room below the cut for the next change. It counts UTF-8 bytes, never fewer
than the characters, so ``wc -c`` and ``wc -m`` in any locale stay under it too.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUND = 37_000


def test_claude_md_stays_under_its_bound() -> None:
    size = len((ROOT / "CLAUDE.md").read_bytes())
    assert size < BOUND, (
        f"CLAUDE.md holds {size:,} bytes, {BOUND:,} at most: move its reference text into "
        "the documents and docstrings it points to, and keep each rule"
    )
