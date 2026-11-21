"""Every answer a test builds says where it comes from and names its kind (conventions §10).

sdk-core's conventions §10 let a test serve or read a body that was not recorded where and
as the test uses it, of five kinds, and ask the test to say where the body comes from where
it builds it. This module reads every test module with ``ast`` and fails on each place that
builds an answer, or hands a body to the package's code, with no mark covering it.

A place is an ``httpx.Response`` built (or another ``*.Response``), a respx route's
``.respond(...)``, a literal body given to ``classify``, to a model's ``model_validate`` or
``model_validate_json`` or to a scrub (``scrub*``, ``merge_custom``), a recording served at
another URL (``replay_fixture``, ``replay`` or ``mount_fixture`` with ``url``), and a call of
a helper, a class or a fixture of the module that holds an unmarked place, a test that takes
such a fixture included. A recording served at its own operation's path is no place.

A mark names ``§10`` and a kind (``kind 1`` to ``kind 5``, in §10's order), or says that
the value is an input of the test, not an answer from CashCtrl. It covers a place from the
docstring of a function or class that encloses it, from a comment block right above the
statement that holds it (or above a statement that encloses that one inside its function),
from a comment on its own lines, or, for a call of a helper, from the helper's docstring.
A place inside an unmarked helper is covered where every call of the helper is, and the
helpers ``ALLOWED`` names, each with its reason, are covered. A module's docstring covers
nothing, so that a test added to a module states its own kind.

What the check cannot see: whether a mark is true, that is whether the body is of the kind
it names and comes from where it says; which of several bodies in its reach a mark speaks
of, since one mark covers them all, and a helper's mark covers a test that uses the helper
for another kind; a recording served at its own path for another query; a body built in
another module than the one that serves it, or under a name the rules above do not list.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
MODULES = sorted(path for path in TESTS.rglob("*.py") if "fixtures" not in path.parts)

KIND = re.compile(r"\bkinds?\s+[1-5]\b")
SECTION = re.compile(r"§10\b")
INPUT = re.compile(
    r"\binputs?\s+of\s+the\s+test,\s+not\s+(?:an\s+)?answers?\s+from\s+CashCtrl", re.IGNORECASE
)
SCRUB = re.compile(r"^(?:scrub(?:_\w+)?|merge_custom)$")
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
ALLOWED: dict[tuple[str, str], str] = {
    ("tests/test_tasks.py", "serve_by_start"): (
        "each journal page recorded for its start, served at the URL it was recorded for with "
        "its body as recorded: a recording served where and as recorded, which takes no kind; "
        "one route answers by start, since replay_fixture matches no query a request lacks"
    ),
}
"""Top-level helpers whose places are neither a kind of §10 nor an input, with the reason."""


def is_mark(text: str | None) -> bool:
    """A docstring or comment block that names a kind of §10, or says it is an input."""
    if not text:
        return False
    return bool(SECTION.search(text) and KIND.search(text)) or bool(INPUT.search(text))


def literal(node: ast.expr) -> bool:
    """A body written in the test: a dict, list or tuple display, a string or bytes."""
    if isinstance(node, (ast.Dict, ast.List, ast.Tuple, ast.JoinedStr)):
        return True
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))


@dataclass(frozen=True)
class Place:
    """A place that builds an answer and no mark covers: where, in what, and what."""

    module: str
    line: int
    scope: str
    text: str

    def __str__(self) -> str:
        return f"{self.module}:{self.line} in {self.scope}: {self.text}"


class Module:
    """One test module's tree, parents, comments and top-level definitions."""

    def __init__(self, source: str) -> None:
        self.tree = ast.parse(source)
        self.lines = source.splitlines()
        self.parent: dict[ast.AST, ast.AST] = {
            child: node for node in ast.walk(self.tree) for child in ast.iter_child_nodes(node)
        }
        self.comments = {
            token.start[0]: token.string
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.COMMENT
        }
        self.defs: dict[str, ast.AST] = {
            node.name: node
            for node in self.tree.body
            if isinstance(node, (*FUNCTIONS, ast.ClassDef))
        }

    def scopes(self, node: ast.AST) -> list[ast.AST]:
        """The functions, lambdas and classes that enclose ``node``, innermost first."""
        found: list[ast.AST] = []
        current = self.parent.get(node)
        while current is not None:
            if isinstance(current, SCOPES):
                found.append(current)
            current = self.parent.get(current)
        return found

    def outermost(self, node: ast.AST) -> str | None:
        """The top-level definition that holds ``node``, ``None`` at module level."""
        named = [s for s in self.scopes(node) if isinstance(s, (*FUNCTIONS, ast.ClassDef))]
        return named[-1].name if named else None

    def scope_name(self, node: ast.AST) -> str:
        named = [s for s in self.scopes(node) if isinstance(s, (*FUNCTIONS, ast.ClassDef))]
        return ".".join(s.name for s in reversed(named)) or "<module>"

    def block_above(self, line: int) -> str:
        """The comment lines that end right above ``line``."""
        texts = []
        current = line - 1
        while current >= 1 and self.lines[current - 1].lstrip().startswith("#"):
            texts.append(self.comments.get(current, ""))
            current -= 1
        return "\n".join(reversed(texts))

    def marked(self, node: ast.AST) -> bool:
        """A mark of an enclosing docstring, a comment above, or a comment on its lines."""
        for scope in self.scopes(node):
            if isinstance(scope, (*FUNCTIONS, ast.ClassDef)) and is_mark(ast.get_docstring(scope)):
                return True
        line = getattr(node, "lineno", 0)
        end = getattr(node, "end_lineno", line)
        if is_mark(" ".join(self.comments.get(n, "") for n in range(line, end + 1))):
            return True
        if is_mark(self.block_above(line)):
            return True
        current: ast.AST | None = node
        while current is not None and not isinstance(current, (*SCOPES, ast.Module)):
            if isinstance(current, ast.stmt) and is_mark(self.block_above(current.lineno)):
                return True
            current = self.parent.get(current)
        return False


def builds(node: ast.AST) -> bool:
    """Whether ``node`` builds an answer or hands a written body to the package's code."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    if name == "Response" or (isinstance(func, ast.Attribute) and name == "respond"):
        return True
    if name in ("classify", "model_validate", "model_validate_json") or SCRUB.match(name):
        return any(literal(arg) for arg in node.args)
    replays = ("replay_fixture", "replay", "mount_fixture")
    return name in replays and any(k.arg == "url" for k in node.keywords)


def holder(module: Module, node: ast.AST) -> str | None:
    """The top-level definition a place belongs to: a top-level function is its own."""
    if isinstance(node, FUNCTIONS) and node in module.tree.body:
        return node.name
    return module.outermost(node)


def calls_of(module: Module, helpers: set[str]) -> dict[ast.AST, str]:
    """Each call of a helper outside it, and each top-level function taking it as a fixture."""
    sites: dict[ast.AST, str] = {}
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in helpers and holder(module, node) != node.func.id:
                sites[node] = node.func.id
        elif isinstance(node, FUNCTIONS) and node in module.tree.body:
            for arg in (*node.args.args, *node.args.kwonlyargs):
                if arg.arg in helpers and isinstance(module.defs.get(arg.arg), FUNCTIONS):
                    sites[node] = arg.arg
    return sites


def uncovered(source: str, name: str, allowed: set[str] | None = None) -> list[Place]:
    """The places of one module that build an answer and no mark covers.

    ``allowed`` names the module's top-level helpers taken as covered, by default those of
    ``ALLOWED``.
    """
    module = Module(source)
    if allowed is None:
        allowed = {helper for (where, helper) in ALLOWED if where == name}
    unmarked = {
        node
        for node in ast.walk(module.tree)
        if builds(node) and not module.marked(node) and module.outermost(node) not in allowed
    }
    while True:  # a helper that holds an unmarked place passes it to its calls
        helpers = {holder(module, node) for node in unmarked} - {None}
        sites = calls_of(module, {h for h in helpers if h and not h.startswith("test_")})
        new = {
            site
            for site in sites
            if site not in unmarked
            and holder(module, site) not in allowed
            and not module.marked(site)
            and not (isinstance(site, FUNCTIONS) and is_mark(ast.get_docstring(site)))
        }
        if not new:
            break
        unmarked |= new
    called = set(sites.values())
    places = []
    for node in unmarked:
        if not isinstance(node, FUNCTIONS) and module.outermost(node) in called:
            continue  # inside a helper: judged where the helper is called
        if isinstance(node, FUNCTIONS):
            scope, text = node.name, f"takes the fixture {sites[node]}"
        else:
            scope, text = module.scope_name(node), ast.unparse(node).splitlines()[0][:90]
        places.append(Place(name, getattr(node, "lineno", 0), scope, text))
    return sorted(places, key=lambda place: place.line)


@pytest.mark.parametrize("path", MODULES, ids=[path.name for path in MODULES])
def test_every_built_answer_names_where_it_comes_from(path: Path) -> None:
    name = path.relative_to(TESTS.parent).as_posix()
    places = uncovered(path.read_text(encoding="utf-8"), name)
    assert not places, (
        "a body built in a test says where it comes from and names its kind of conventions "
        "§10, or that it is an input of the test, not an answer from CashCtrl:\n"
        + "\n".join(map(str, places))
    )


@pytest.mark.parametrize(("where", "helper"), ALLOWED, ids=[h for _, h in ALLOWED])
def test_each_allowed_helper_still_builds_an_answer(where: str, helper: str) -> None:
    """An entry whose helper is gone, or would leave nothing uncovered, is stale and goes."""
    places = uncovered((TESTS.parent / where).read_text(encoding="utf-8"), where, set())
    assert any(helper in (place.scope.split(".")[0], place.text.split("(")[0]) for place in places)


def lines(source: str) -> list[int]:
    """The lines of the uncovered places of ``source``, a module written here."""
    return [place.line for place in uncovered(source.lstrip("\n"), "tests/test_x.py")]


UNMARKED = """
import httpx

def test_one():
    answer = httpx.Response(200, json={"total": 0, "data": []})
"""


def test_an_unmarked_response_fails_and_a_mark_covers_it() -> None:
    assert lines(UNMARKED) == [4]
    marked = UNMARKED.replace(
        "def test_one():\n",
        'def test_one():\n    """An empty list, composed (conventions §10, kind 2)."""\n',
    )
    assert lines(marked) == []
    commented = UNMARKED.replace(
        "    answer", "    # Composed (conventions §10, kind 2).\n    answer"
    )
    assert lines(commented) == []
    words = marked.replace("kind 2", "composed")
    assert lines(words) == [5], "a mark names a kind by its number"


def test_a_module_docstring_covers_nothing() -> None:
    assert lines('"""Bodies composed (conventions §10, kind 2)."""\n' + UNMARKED) == [6]


def test_an_input_is_a_mark() -> None:
    source = """
import httpx

def test_one(route):
    \"\"\"The key is an input of the test, not an answer from CashCtrl.\"\"\"
    route.respond(200, json={"key": "k"})
"""
    assert lines(source) == []


def test_a_helper_passes_an_unmarked_place_to_each_call() -> None:
    source = """
import httpx

def answer(body):
    return httpx.Response(200, json=body)

def test_marked():
    \"\"\"A read changed in memory (conventions §10, kind 4).\"\"\"
    answer({})

def test_unmarked():
    answer({})
"""
    assert lines(source) == [11]
    marked = source.replace(
        "def answer(body):\n",
        'def answer(body):\n    """A read changed in memory (conventions §10, kind 4)."""\n',
    )
    assert lines(marked) == []
    assert lines(source.split("def test_marked")[0]) == [4], "a helper nothing calls"


def test_a_fixture_that_builds_passes_it_to_the_tests_that_take_it() -> None:
    source = """
import pytest

@pytest.fixture
def served(respx_mock):
    respx_mock.get("https://x/a.json").respond(200, json={})

def test_one(served):
    pass
"""
    assert lines(source) == [7]


def test_a_replay_at_its_own_path_is_no_place_and_one_at_another_url_is() -> None:
    source = """
def test_one(replay_fixture):
    replay_fixture("account_list", "default")
    replay_fixture("account_list", "default", url="https://x/other.json")
"""
    assert lines(source) == [3]
