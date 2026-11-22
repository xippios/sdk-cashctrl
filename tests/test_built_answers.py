"""Every answer a test builds says where it comes from and names its kind (conventions §10).

The check is core's, collected by the star import below (sdk-core ADR-0049): it fails on each
place of the tests that builds or serves a body without its mark, naming its file and line,
and its census, after every other test of the run, fails a test whose replay answered
another request than the recorded one without naming the third kind. ``READERS`` adds the
package's own function that takes a body written in a test, and ``ALLOWED`` the one helper
whose places are neither a kind of §10 nor an input, with its reason.
"""

from xippios.core.testing.built_answers import *  # noqa: F403

READERS = frozenset({"merge_custom"})
"""The package's own function that takes a body written in a test, judged as a scrub is."""

ALLOWED: dict[tuple[str, str], str] = {
    ("tests/test_tasks.py", "serve_by_start"): (
        "each journal page recorded for its start, served at the URL it was recorded for with "
        "its body as recorded: a recording served where and as recorded, which takes no kind; "
        "one route answers by start, since replay_fixture matches no query a request lacks"
    ),
}
"""Top-level helpers whose places are neither a kind of §10 nor an input, with the reason."""
