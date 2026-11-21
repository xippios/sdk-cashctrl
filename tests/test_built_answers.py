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

A mark names ``§10`` and a kind (``kind 1`` to ``kind 5``, in §10's order). For a value
handed to the code that no route serves as an answer and ``classify`` does not read, a
literal given to a model or a scrub, or a response given to ``fixture_from_response`` alone,
a mark may instead say that the value is an input of the test, not an answer from CashCtrl;
a served answer takes a kind. It covers a place from the
docstring of a function or class that encloses it, from a comment block right above the
statement that holds it (or above a statement that encloses that one inside its function),
from a comment on its own lines, or, for a call of a helper, from the helper's docstring.
A place inside an unmarked helper is covered where every call of the helper is, and the
helpers ``ALLOWED`` names, each with its reason, are covered. A module's docstring covers
nothing, so that a test added to a module states its own kind.

A replay that answers another request than the recorded one, in its host, path, query or
form body, is the third kind: the modules that replay run once more in a process of their
own with ``tests/replay_census.py``, and each test it names says ``kind 3`` beside ``§10`` in
its docstring, a comment inside it, or the docstring of a helper or fixture it uses.

What the check cannot see: whether a mark is true, that is whether the body is of the kind
it names and comes from where it says, and whether a third kind's reason holds; which of
several bodies in its reach a mark speaks of, since one mark covers them all, so an unmarked
body added to a test that already carries a mark passes, and a helper's mark covers a test
that uses the helper for another kind; which replay of a test the third kind speaks of; a
body built in another module than the one that serves it, or under a name the rules above
do not list.
"""

from __future__ import annotations

import ast
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
MODULES = sorted(path for path in TESTS.rglob("*.py") if "fixtures" not in path.parts)

KIND = re.compile(r"\bkinds?\s+[1-5]\b")
THIRD = re.compile(r"\bkind\s+3\b|\bkinds\s+(?:[1-5],?\s+(?:and\s+)?)*3\b")
SECTION = re.compile(r"§10\b")
INPUT = re.compile(
    r"\binputs?\s+of\s+the\s+test,\s+not\s+(?:an\s+)?answers?\s+from\s+CashCtrl", re.IGNORECASE
)
SCRUB = re.compile(r"^(?:scrub(?:_\w+)?|merge_custom)$")
REPLAYS = ("replay_fixture", "replay", "mount_fixture")
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
UNFIT = (
    "a made-up exchange whose written form the test compares: no kind of §10 fits it as "
    "built, a reshaped body would change an assertion, and no scrubbed recording keeps "
    "what it carries"
)
ALLOWED: dict[tuple[str, str], str] = {
    ("tests/test_tasks.py", "serve_by_start"): (
        "each journal page recorded for its start, served at the URL it was recorded for with "
        "its body as recorded: a recording served where and as recorded, which takes no kind; "
        "one route answers by start, since replay_fixture matches no query a request lacks"
    ),
    ("tests/test_record_fixture.py", "test_a_percent_encoded_key_is_redacted_and_goes_to_review"): (
        UNFIT
    ),
    ("tests/test_record_fixture.py", "test_a_recorded_fixture_replays_on_the_placeholder_host"): (
        UNFIT
    ),
    (
        "tests/test_record_fixture.py",
        "test_the_placeholder_host_leaves_no_trace_of_the_organisation",
    ): (UNFIT),
    ("tests/test_record_fixture.py", "test_other_token_like_fields_are_redacted"): UNFIT,
}
"""Top-level helpers and tests whose places are neither a kind of §10 nor an input, each with
its reason. The four tests of the recorder are no kind as built and stay listed until a
recording or a change of their assertions brings them to one."""


def is_mark(text: str | None, served: bool = False) -> bool:
    """A docstring or comment block that names a kind of §10, or, for a value handed to the
    code that no route serves as an answer, says it is an input."""
    if not text:
        return False
    if SECTION.search(text) and KIND.search(text):
        return True
    return not served and bool(INPUT.search(text))


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

    def marked(self, node: ast.AST, served: bool) -> bool:
        """A mark of an enclosing docstring, a comment above, or a comment on its lines."""
        for scope in self.scopes(node):
            documented = isinstance(scope, (*FUNCTIONS, ast.ClassDef))
            if documented and is_mark(ast.get_docstring(scope), served):  # type: ignore[arg-type]
                return True
        line = getattr(node, "lineno", 0)
        end = getattr(node, "end_lineno", line)
        if is_mark(" ".join(self.comments.get(n, "") for n in range(line, end + 1)), served):
            return True
        if is_mark(self.block_above(line), served):
            return True
        current: ast.AST | None = node
        while current is not None and not isinstance(current, (*SCOPES, ast.Module)):
            if isinstance(current, ast.stmt) and is_mark(self.block_above(current.lineno), served):
                return True
            current = self.parent.get(current)
        return False

    def handed(self, node: ast.Call) -> bool:
        """An ``httpx.Response`` given to ``fixture_from_response`` alone, directly or by a
        local name: an exchange handed to the recorder's code, which no route serves."""
        parent = self.parent.get(node)
        if isinstance(parent, ast.Call) and ast.unparse(parent.func) == "fixture_from_response":
            return True
        if not (isinstance(parent, ast.Assign) and len(parent.targets) == 1):
            return False
        target = parent.targets[0]
        if not isinstance(target, ast.Name):
            return False
        scope = next((s for s in self.scopes(node) if isinstance(s, FUNCTIONS)), self.tree)
        uses = [
            n
            for n in ast.walk(scope)
            if isinstance(n, ast.Name) and n.id == target.id and isinstance(n.ctx, ast.Load)
        ]
        return bool(uses) and all(
            isinstance(call := self.parent.get(n), ast.Call)
            and ast.unparse(call.func) == "fixture_from_response"
            for n in uses
        )

    def serves(self, node: ast.Call) -> bool:
        """Whether the place serves an answer: a route's, or one ``classify`` reads, where
        only a kind of §10 marks it; a value handed to the code may be marked an input."""
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name == "respond" or name in REPLAYS or name == "classify":
            return True
        if name == "Response":
            from_httpx = isinstance(func, ast.Name) or ast.unparse(func) == "httpx.Response"
            return from_httpx and not self.handed(node)
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
    return name in REPLAYS and any(k.arg == "url" for k in node.keywords)


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
    served: set[ast.AST] = {
        node
        for node in ast.walk(module.tree)
        if builds(node) and isinstance(node, ast.Call) and module.serves(node)
    }
    unmarked = {
        node
        for node in ast.walk(module.tree)
        if builds(node)
        and not module.marked(node, node in served)
        and module.outermost(node) not in allowed
    }
    while True:  # a helper that holds an unmarked place passes it to its calls
        helpers = {holder(module, node) for node in unmarked} - {None}
        serving = {holder(module, node) for node in unmarked & served}
        sites = calls_of(module, {h for h in helpers if h and not h.startswith("test_")})
        new = set()
        for site, helper in sites.items():
            serves = helper in serving
            if site in unmarked or holder(module, site) in allowed:
                continue
            if module.marked(site, serves):
                continue
            if isinstance(site, FUNCTIONS) and is_mark(ast.get_docstring(site), serves):
                continue
            new.add(site)
            if serves:
                served.add(site)
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


def replaying() -> list[Path]:
    """The test modules that replay a recording, this one left out."""
    return [
        path
        for path in MODULES
        if path.name != Path(__file__).name
        and any(
            isinstance(node, ast.Call)
            and getattr(node.func, "id", getattr(node.func, "attr", "")) in REPLAYS
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        )
    ]


def names_the_third_kind(path: Path, test: str) -> bool:
    """Whether ``test`` says its replay is the third kind of §10: in its docstring, in a
    comment inside it, or in the docstring of a helper or fixture of the module it uses."""
    source = path.read_text(encoding="utf-8")
    module = Module(source)
    function = module.defs.get(test)
    if not isinstance(function, FUNCTIONS):
        return False
    texts = [ast.get_docstring(function) or ""]
    texts += [
        text
        for line, text in module.comments.items()
        if function.lineno <= line <= (function.end_lineno or line)
    ]
    used = {
        n.func.id
        for n in ast.walk(function)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    used |= {arg.arg for arg in function.args.args}
    helpers = [module.defs[name] for name in used if name in module.defs]
    texts += [
        ast.get_docstring(helper) or "" for helper in helpers if isinstance(helper, FUNCTIONS)
    ]
    return any(SECTION.search(text) and THIRD.search(text) for text in texts)


def test_every_replay_for_another_request_names_the_third_kind(tmp_path: Path) -> None:
    """A replay that answers a request other than its recording's, in its host, path, query
    or form body, is §10's third kind, and the test says so and why.

    The modules that replay run in a process of their own with ``tests/replay_census.py``,
    which names each test whose replay answered another request than the recorded one.
    """
    census = tmp_path / "census.jsonl"
    env = {**os.environ, "REPLAY_CENSUS": str(census)}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(TESTS), env.get("PYTHONPATH")]))
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "replay_census", "-p", "no:cacheprovider"]
        + ["-m", "not live"]
        + [str(path) for path in replaying()],
        cwd=TESTS.parent,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout[-3000:] + run.stderr[-3000:]
    rows = census.read_text(encoding="utf-8").splitlines() if census.exists() else []
    tests = sorted({(row["module"], row["test"]) for row in map(json.loads, rows)})
    assert tests, "the census saw no replay for another request"
    unmarked = [
        f"tests/{module}::{test}"
        for module, test in tests
        if not names_the_third_kind(TESTS / module, test)
    ]
    assert not unmarked, (
        "a replay for another request says it is the third kind of conventions §10, and why: "
        "the test asserts only what was sent, or the operation answers alike there:\n"
        + "\n".join(unmarked)
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


def test_an_input_marks_a_value_handed_to_the_code_and_no_served_answer() -> None:
    served = UNMARKED.replace(
        "def test_one():\n",
        'def test_one():\n    """The body is an input of the test, not an answer from CashCtrl'
        '."""\n',
    )
    assert lines(served) == [5], "a served answer takes a kind"
    handed = served.replace("    answer = ", "    fixture = fixture_from_response(").replace(
        "})\n", "}))\n"
    )
    assert lines(handed) == [], "an exchange handed to the code may be an input"
    by_name = served.replace("\n\n\ndef", "\n\ndef") + "    step(fixture_from_response(answer))\n"
    assert lines(by_name) == []
    validated = (
        'def test_two():\n    """The record is an input of the test, not an answer from'
        ' CashCtrl."""\n'
        '    Model.model_validate({"id": 1})\n'
    )
    assert lines(validated) == []


def test_a_module_docstring_covers_nothing() -> None:
    assert lines('"""Bodies composed (conventions §10, kind 2)."""\n' + UNMARKED) == [6]


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
