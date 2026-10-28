"""The write tasks: previews send nothing, confirmed writes replay, updates fail closed.

Every fixture here was recorded from the synthetic demo organisation with
``scripts/record_fixture.py --method POST``, in this order, so that every record created
was deleted again: on 2026-10-24 the journal entry 51 (created, a refused create without
``debitId``, read, updated, deleted, deleted again) and the person 14 (created, read,
updated, deleted); on 2026-10-27 the order 20 (created with the body the order 7 was
created with on 2026-10-24, read, updated, read again, deleted). A preview's ``payload``
is compared with the body the confirmed call sent, as the fixture recorded it: the
preview is what upstream receives.

The negative update cases change a recorded read in memory (a field removed, a stored
list filled in) and serve it with ``respx``; they are not fixtures, and they say so.

``update_order_status`` and ``create_order_payment`` (G5 (8) of 2026-10-28) take their
status ids from the recorded categories (``order_category_list/default`` and
``purchase``), never a guess. Their fixtures of 2026-10-29 record the marked purchase
order 26 (created and deleted through the write tools, not recorded): its status set,
its payment as ``PAIN`` refused and as ``CASH_PDF`` created.
"""

import inspect
import json
import re
import typing
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

import httpx
import pytest
import respx
from fastapi import APIRouter
from mcp.server.mcpserver import MCPServer
from xippios.core import InvalidRequestError, NotFoundError, Result
from xippios.core.http import router_from_tasks
from xippios.core.mcp import build_server, tool_name
from xippios.core.mcp.server import is_write_server, register_tasks
from xippios.core.testing import ReplayFixture, load_fixture, mcp_call, mcp_call_text

from xippios.cashctrl import api, tasks_write
from xippios.cashctrl._client import DEMO, SOURCE
from xippios.cashctrl.api._form import (
    FORM_CONTENT_TYPE,
    custom_xml,
    form_fields,
    form_value,
    json_text,
    merge_custom,
)
from xippios.cashctrl.errors import FieldError, RequestRejected
from xippios.cashctrl.http import router
from xippios.cashctrl.mcp import server as read_server
from xippios.cashctrl.mcp_write import server as write_server
from xippios.cashctrl.models import (
    BankAccountInput,
    JournalEntryDetail,
    JournalEntryDetailProjection,
    JournalItemInput,
    ListResponse,
    OrderCategory,
    OrderDetail,
    OrderItemInput,
    PersonAddressInput,
    PersonDetail,
    PersonDetailProjection,
    WritePreview,
    WriteResult,
)

BASE = "https://demo.cashctrl.com/api/v1"
_FIXTURES = Path(__file__).parent / "fixtures"
DAY = date(2026, 10, 24)
JOURNAL_ENTRY = 51
PERSON = 14
ORDER = 20

WRITE_TASKS: dict[str, Callable[..., Any]] = {
    name: getattr(tasks_write, name) for name in tasks_write.__all__
}


def recorded_body(fixtures_dir: Path, endpoint: str, case: str) -> list[tuple[str, str]]:
    """The form fields the recorded call sent, decoded, in their order."""
    body = load_fixture(fixtures_dir / endpoint / f"{case}.json").request.body
    assert body is not None, f"{endpoint}/{case} recorded no request body"
    return parse_qsl(body, keep_blank_values=True, strict_parsing=True)


def sent_body(route: respx.Route) -> list[tuple[str, str]]:
    """The form fields the last call of ``route`` sent, decoded, in their order."""
    return parse_qsl(route.calls.last.request.content.decode(), keep_blank_values=True)


def recorded_read(fixtures_dir: Path, endpoint: str, case: str) -> dict[str, Any]:
    """The decoded answer of a recorded read, to change in memory for a negative case."""
    body: dict[str, Any] = json.loads(
        load_fixture(fixtures_dir / endpoint / f"{case}.json").response.body
    )
    return body


def preview_of(result: Result[Any]) -> WritePreview[Any]:
    """The preview a write task returned while ``confirm`` was false."""
    assert isinstance(result.data, WritePreview)
    return result.data


def serve_read(respx_mock: respx.MockRouter, path: str, body: dict[str, Any]) -> respx.Route:
    """Answer ``GET <path>`` with ``body``: a recorded read changed in memory."""
    return respx_mock.get(f"{BASE}/{path}").respond(200, json=body)


# Structure ---------------------------------------------------------------------------


@pytest.mark.parametrize("task", WRITE_TASKS.values(), ids=WRITE_TASKS.keys())
def test_every_write_task_is_a_sync_facade_with_confirm_last(task: Callable[..., Any]) -> None:
    assert hasattr(task, "async_fn"), "write the async function and derive the sync one"
    parameters = list(inspect.signature(task).parameters.values())
    confirm = parameters[-1]
    assert confirm.name == "confirm"
    assert typing.get_type_hints(task)["confirm"] is bool
    assert confirm.default is False
    doc = inspect.getdoc(task) or ""
    assert doc.splitlines()[0].endswith(".")
    assert "Args:" in doc
    assert "confirm" in doc
    for parameter in parameters:
        assert re.search(rf"^\s+{parameter.name}:", doc, re.MULTILINE), parameter.name


@pytest.mark.parametrize("task", WRITE_TASKS.values(), ids=WRITE_TASKS.keys())
def test_every_write_task_returns_a_preview_or_a_result(task: Callable[..., Any]) -> None:
    """``Result[WritePreview[<record>] | WriteResult]``: ``performed`` tells them apart."""
    facade: Any = task
    returned = typing.get_type_hints(facade.async_fn)["return"]
    (outcome,) = returned.__pydantic_generic_metadata__["args"]
    preview, result = typing.get_args(outcome)
    assert preview.__pydantic_generic_metadata__["origin"] is WritePreview
    assert preview.__pydantic_generic_metadata__["args"][0] in (
        JournalEntryDetailProjection,
        PersonDetailProjection,
        OrderDetail,
    )
    assert result is WriteResult


# The write server --------------------------------------------------------------------
# assert_write_tools, _tool_names and _serves are copied from xippios-core, which removed
# them in 0.3.0 for this package to carry (ADR-0024; sdk-core cb8ecdf,
# src/xippios/core/testing/adapters.py), with _confirm_problem from its
# src/xippios/core/mcp/server.py, and extended with the check that confirm is the last
# parameter (queue row 26 f). The family check no longer tests a write server; this does.
# Async here: core listed the tools on its private background loop.


def _confirm_problem(fn: Callable[..., Any]) -> str | None:
    """Why ``fn`` does not take ``confirm: bool = False`` last, or ``None`` when it does.

    The annotation is resolved with ``typing.get_type_hints``, so a string annotation
    and ``Annotated[bool, ...]`` count as ``bool``; ``bool | None`` does not.
    """
    parameters = inspect.signature(fn).parameters
    parameter = parameters.get("confirm")
    if parameter is None:
        return "no parameter confirm"
    annotation = typing.get_type_hints(fn).get("confirm", parameter.annotation)
    if annotation is inspect.Parameter.empty:
        return "confirm is not annotated"
    if annotation is not bool:
        return f"confirm is annotated {annotation!r}, not bool"
    if parameter.default is inspect.Parameter.empty:
        return "confirm has no default"
    if parameter.default is not False:
        return f"confirm defaults to {parameter.default!r}, not False"
    if list(parameters)[-1] != "confirm":
        return "confirm is not the last parameter"
    return None


async def _tool_names(server: MCPServer) -> set[str]:
    return {tool.name for tool in await server.list_tools()}


def _serves(route: Any, source: str, fn: Callable[..., Any]) -> bool:
    """True when ``route`` is the one ``router_from_tasks`` builds for ``fn``.

    ``router_from_tasks`` names it ``<source>_<function>`` and puts it at
    ``<prefix>/<function>``; either is enough, so a custom prefix is caught too.
    """
    named = getattr(route, "name", None) == f"{source}_{fn.__name__}"
    return named or str(getattr(route, "path", "")).endswith(f"/{fn.__name__}")


async def assert_write_tools(
    write_server: MCPServer,
    write_tasks: list[Callable[..., Any]],
    *,
    source: str,
    read_server: MCPServer | None = None,
    router: APIRouter | None = None,
) -> None:
    """Check a write server against its write tasks (conventions §8).

    Fails the test, naming the offending tool, unless all of these hold:

    - the write server was registered with ``read_only=False`` (``is_write_server``),
      which ``main``'s loopback rule for ``--http`` depends on;
    - the write server's tools are exactly ``tool_name(source, fn)`` for the write
      tasks, no more and no fewer;
    - every write task takes ``confirm: bool = False`` as its last parameter, so a call
      without it is a dry run;
    - no write tool is on ``read_server``, and no route of ``router`` serves a write
      task (matched by the route name and path ``router_from_tasks`` gives it), when
      given.

    A write server exposes write tools only: reference tools, the organisation list
    among them, stay on the read server.
    """
    assert is_write_server(write_server), (
        "the write server was not registered with read_only=False; the loopback rule depends on it"
    )
    expected = {tool_name(source, fn): fn for fn in write_tasks}
    listed = await _tool_names(write_server)
    unexpected = sorted(listed - expected.keys())
    assert not unexpected, f"write server tools that are not write tasks: {unexpected}"
    missing = sorted(expected.keys() - listed)
    assert not missing, f"write tasks missing from the write server: {missing}"
    for name, fn in expected.items():
        problem = _confirm_problem(fn)
        assert problem is None, f"{name}: {problem}; a write tool takes confirm: bool = False last"
    if read_server is not None:
        on_read = sorted(expected.keys() & await _tool_names(read_server))
        assert not on_read, f"write tools on the read server: {on_read}"
    if router is not None:
        for name, fn in expected.items():
            for route in router.routes:
                path = str(getattr(route, "path", ""))
                methods = " ".join(sorted(getattr(route, "methods", None) or ()))
                served = _serves(route, source, fn)
                assert not served, f"{name}: a write task has an HTTP route, {methods} {path}"


@pytest.mark.anyio
async def test_the_write_server_serves_write_tasks_only() -> None:
    """Conventions §8: a write server, its tools exactly the write tasks, confirm last.

    So the organisation list, a reference tool, stays on the read server. Eleven write
    tasks: create, update and delete for journal entries, persons and orders, an order's
    status and an order's payment (G5 (8) of 2026-10-28).
    """
    assert len(WRITE_TASKS) == 11
    assert {"update_order_status", "create_order_payment"} <= WRITE_TASKS.keys()
    await assert_write_tools(
        write_server,
        list(WRITE_TASKS.values()),
        source=SOURCE,
        read_server=read_server,
        router=router,
    )


def create_thing(name: str, confirm: bool = False) -> dict[str, str]:
    """Create a thing; without confirm, return a preview.

    Args:
        name: The thing's name, e.g. ``"Corn"``.
        confirm: ``True`` writes, ``False`` previews.
    """
    return {"name": name, "written": str(confirm)}


def delete_thing(thing_id: int, confirm: typing.Annotated[bool, "write"] = False) -> dict[str, int]:
    """Delete a thing; without confirm, return a preview.

    Args:
        thing_id: The thing's id, e.g. ``4``.
        confirm: ``True`` deletes, ``False`` previews.
    """
    return {"id": thing_id}


def list_things() -> list[str]:
    """List the things."""
    return ["a"]


WRITE: list[Callable[..., Any]] = [create_thing, delete_thing]
READ: list[Callable[..., Any]] = [list_things]


@pytest.mark.anyio
async def test_assert_write_tools_accepts_a_separate_write_server() -> None:
    await assert_write_tools(
        build_server("example", WRITE, read_only=False),
        WRITE,
        source="example",
        read_server=build_server("example", READ),
        router=router_from_tasks("example", READ),
    )


@pytest.mark.anyio
async def test_assert_write_tools_wants_a_server_registered_as_a_write_server() -> None:
    read_only = build_server("example", [])
    register_tasks(read_only, "example", WRITE)  # the write tasks, registered read-only
    with pytest.raises(
        AssertionError,
        match=(
            r"^the write server was not registered with read_only=False; "
            r"the loopback rule depends on it"
        ),
    ):
        await assert_write_tools(read_only, WRITE, source="example")


@pytest.mark.anyio
async def test_assert_write_tools_wants_exactly_the_write_tasks() -> None:
    # build_server refuses a write task without confirm (conventions §8); a read-only
    # registration on the write server is how a stray tool would get there.
    write = build_server("example", WRITE, read_only=False)
    register_tasks(write, "example", [list_things])
    with pytest.raises(AssertionError, match=r"not write tasks: \['example_list_things'\]"):
        await assert_write_tools(write, WRITE, source="example")
    write = build_server("example", [create_thing], read_only=False)
    with pytest.raises(AssertionError, match=r"missing .*: \['example_delete_thing'\]"):
        await assert_write_tools(write, WRITE, source="example")


def no_confirm(name: str) -> None:
    """No confirm at all."""


def confirm_true(confirm: bool = True) -> None:
    """Writes unless told not to."""


def confirm_required(confirm: bool) -> None:
    """Must be told."""


def confirm_unannotated(confirm=False):  # type: ignore[no-untyped-def]
    """Not annotated."""


def confirm_optional(confirm: bool | None = False) -> None:
    """Optional."""


def confirm_zero(confirm: int = 0) -> None:
    """An int."""


def confirm_first(confirm: bool = False, name: str = "") -> None:
    """Confirm before the other parameters."""


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("task", "problem"),
    [
        (no_confirm, "no parameter confirm"),
        (confirm_true, "confirm defaults to True, not False"),
        (confirm_required, "confirm has no default"),
        (confirm_unannotated, "confirm is not annotated"),
        (confirm_optional, r"confirm is annotated bool \| None, not bool"),
        (confirm_zero, "confirm is annotated <class 'int'>, not bool"),
        (confirm_first, "confirm is not the last parameter"),
    ],
)
async def test_assert_write_tools_wants_confirm_false_last(
    task: Callable[..., Any], problem: str
) -> None:
    write = build_server("example", [create_thing], read_only=False)
    register_tasks(write, "example", [task])  # build_server(read_only=False) refuses most
    with pytest.raises(AssertionError, match=f"^example_{task.__name__}: {problem}; "):
        await assert_write_tools(write, [create_thing, task], source="example")


@pytest.mark.anyio
async def test_assert_write_tools_keeps_write_tools_off_the_read_adapters() -> None:
    write = build_server("example", WRITE, read_only=False)
    read = build_server("example", [list_things, delete_thing])
    with pytest.raises(AssertionError, match=r"on the read server: \['example_delete_thing'\]"):
        await assert_write_tools(write, WRITE, source="example", read_server=read)
    with_write = router_from_tasks("example", [list_things, create_thing])
    with pytest.raises(
        AssertionError,
        match=r"^example_create_thing: a write task has an HTTP route, GET /example/create_thing",
    ):
        await assert_write_tools(write, WRITE, source="example", router=with_write)
    prefixed = router_from_tasks("example", [delete_thing], prefix="/v1")
    with pytest.raises(AssertionError, match=r"^example_delete_thing: .* GET /v1/delete_thing"):
        await assert_write_tools(write, WRITE, source="example", router=prefixed)


@pytest.mark.anyio
async def test_assert_write_tools_names_tools_with_the_underscored_source() -> None:
    write = build_server("usda-nass", WRITE, read_only=False)
    await assert_write_tools(
        write, WRITE, source="usda-nass", router=router_from_tasks("usda-nass", READ)
    )
    with_write = router_from_tasks("usda-nass", WRITE)
    with pytest.raises(AssertionError, match=r"^usda_nass_create_thing: "):
        await assert_write_tools(write, WRITE, source="usda-nass", router=with_write)


@pytest.mark.anyio
async def test_write_tools_are_the_write_tasks_with_their_parameters() -> None:
    """Each write tool takes its task's parameters, confirm among them, and says it writes."""
    tools = {tool.name: tool for tool in await write_server.list_tools()}
    for name, fn in WRITE_TASKS.items():
        tool = tools[tool_name(SOURCE, fn)]
        parameters = set(inspect.signature(fn).parameters)
        assert set(tool.input_schema.get("properties", {})) == parameters, name
        assert "confirm" in tool.input_schema["properties"], name
        assert tool.description, f"{name} has no docstring; agents read it"
        assert tool.annotations is not None
        assert (tool.annotations.read_only_hint, tool.annotations.destructive_hint) == (False, True)


# Journal entries ---------------------------------------------------------------------


def create_the_recorded_journal_entry(confirm: bool = False) -> Any:
    return tasks_write.create_journal_entry(
        DEMO,
        date_added=DAY,
        amount=Decimal("100.00"),
        debit_id=3,
        credit_id=42,
        title="xippios-live fixture",
        tax_id=9,
        confirm=confirm,
    )


def test_create_journal_entry_previews_without_a_request(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    result = create_the_recorded_journal_entry()
    assert not respx_mock.calls, "a create's preview sends nothing"
    preview = result.data
    assert isinstance(preview, WritePreview)
    assert preview.performed is False
    assert preview.endpoint == "journal/create.json"
    assert list(preview.payload.items()) == recorded_body(fixtures_dir, "journal_create", "ok")
    assert (preview.before, preview.changes) == (None, None)
    assert (result.meta.endpoint, result.meta.tenant) == ("journal/create.json", DEMO)
    assert result.meta.request == {"org": DEMO}, "the payload is in data, never twice"


def test_create_journal_entry_with_confirm_replays_the_recorded_create(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    route = replay_fixture("journal_create", "ok")
    result = create_the_recorded_journal_entry(confirm=True)
    sent = route.calls.last.request
    assert sent.method == "POST"
    assert sent.headers["Content-Type"] == FORM_CONTENT_TYPE
    assert sent_body(route) == recorded_body(fixtures_dir, "journal_create", "ok")
    written = result.data
    assert isinstance(written, WriteResult)
    assert (written.performed, written.insert_id, written.message) == (
        True,
        JOURNAL_ENTRY,
        "Book entry saved",
    )
    assert result.meta.tenant == DEMO
    assert result.meta.request == {
        "org": DEMO,
        **dict(recorded_body(fixtures_dir, "journal_create", "ok")),
    }


def test_a_refused_create_names_the_field(replay_fixture: ReplayFixture) -> None:
    """The first recorded field-error list: HTTP 200, ``success`` false, ``errors``."""
    replay_fixture("journal_create", "rejected")
    with pytest.raises(RequestRejected) as raised:
        tasks_write.create_journal_entry(
            DEMO,
            date_added=DAY,
            amount=Decimal("100.00"),
            credit_id=42,
            title="xippios-live fixture rejected",
            tax_id=9,
            confirm=True,
        )
    assert raised.value.errors == [
        FieldError(field="debitId", message="This field cannot be empty.")
    ]
    assert (
        str(raised.value) == "CashCtrl rejected the request: debitId: This field cannot be empty."
    )


def test_a_collective_entry_sends_its_items_as_json(respx_mock: respx.MockRouter) -> None:
    """Items as models or, from Python, as mappings; upstream's keys, numbers as numbers."""
    result = tasks_write.create_journal_entry(
        DEMO,
        title="xippios-live collective",
        items=[
            JournalItemInput(account_id=3, debit=Decimal("500.50")),
            {"accountId": 42, "credit": Decimal("500.50"), "description": "Erlös"},  # type: ignore[list-item]
        ],
    )
    assert not respx_mock.calls
    assert preview_of(result).payload == {
        "items": (
            '[{"accountId":3,"debit":500.5},{"accountId":42,"credit":500.5,"description":"Erlös"}]'
        ),
        "title": "xippios-live collective",
    }


def test_update_journal_entry_previews_the_whole_record_after_one_read(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    read = replay_fixture("journal_read", "for_update")
    result = tasks_write.update_journal_entry(
        DEMO, JOURNAL_ENTRY, title="xippios-live fixture updated"
    )
    assert read.call_count == 1, "one read, never a write"
    preview = result.data
    assert isinstance(preview, WritePreview)
    assert list(preview.payload.items()) == recorded_body(fixtures_dir, "journal_update", "ok")
    assert preview.changes == {"title": "xippios-live fixture updated"}
    assert isinstance(preview.before, JournalEntryDetailProjection)
    assert (preview.before.id, preview.before.title) == (JOURNAL_ENTRY, "xippios-live fixture")
    assert result.meta.endpoint == "journal/update.json"
    assert result.meta.request == {"org": DEMO}


def test_update_journal_entry_with_confirm_reads_then_sends_the_whole_record(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    read = replay_fixture("journal_read", "for_update")
    update = replay_fixture("journal_update", "ok")
    result = tasks_write.update_journal_entry(
        DEMO, JOURNAL_ENTRY, title="xippios-live fixture updated", confirm=True
    )
    assert (read.call_count, update.call_count) == (1, 1)
    assert sent_body(update) == recorded_body(fixtures_dir, "journal_update", "ok")
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (JOURNAL_ENTRY, "Book entry saved")
    assert result.meta.request["id"] == str(JOURNAL_ENTRY)


@pytest.mark.parametrize("confirm", [False, True])
def test_update_journal_entry_refuses_when_a_mandatory_parameter_cannot_be_derived(
    respx_mock: respx.MockRouter, fixtures_dir: Path, confirm: bool
) -> None:
    """The recorded read without ``debitId``, changed in memory: nothing is written."""
    body = recorded_read(fixtures_dir, "journal_read", "for_update")
    del body["data"]["debitId"]
    serve_read(respx_mock, "journal/read.json", body)
    write = respx_mock.post(f"{BASE}/journal/update.json")
    with pytest.raises(InvalidRequestError, match=r"gives no debitId, which update\.json requires"):
        tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, title="x", confirm=confirm)
    assert not write.called
    tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, debit_id=3)  # given: derivable


def test_update_journal_entry_refuses_stored_lists_it_cannot_carry(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """Attachments were never observed filled in; changed in memory to hold one."""
    body = recorded_read(fixtures_dir, "journal_read", "for_update")
    body["data"]["attachments"] = [{"fileId": 3}]
    serve_read(respx_mock, "journal/read.json", body)
    with pytest.raises(InvalidRequestError, match="holds attachments") as raised:
        tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, title="x")
    assert "pass attachments to replace it" in str(raised.value)
    replaced = tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, attachments=[])
    assert "attachments" not in preview_of(replaced).payload
    assert preview_of(replaced).changes == {"attachments": "[]"}, "an empty list is shown"
    cleared = tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, clear=["attachments"])
    assert "attachments" not in preview_of(cleared).payload
    assert preview_of(cleared).changes == {"attachments": "[]"}


def test_update_journal_entry_refuses_lines_with_allocations(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """The recorded collective entry's lines, one given an allocation in memory."""
    body = recorded_read(fixtures_dir, "journal_read", "collective")
    body["data"]["items"][0]["allocations"] = [{"share": 1, "toCostCenterId": 2}]
    serve_read(respx_mock, "journal/read.json", body)
    entry_id = body["data"]["id"]
    with pytest.raises(InvalidRequestError, match="holds items, a line with allocations") as raised:
        tasks_write.update_journal_entry(DEMO, entry_id, title="x")
    assert "pass items to replace it" in str(raised.value)


def test_update_journal_entry_carries_a_collective_entrys_lines(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """A collective entry needs no amount, debitId or creditId: upstream ignores them."""
    replay_fixture("journal_read", "collective")
    entry_id = recorded_read(fixtures_dir, "journal_read", "collective")["data"]["id"]
    payload = preview_of(tasks_write.update_journal_entry(DEMO, entry_id, title="x")).payload
    lines = json.loads(payload["items"])
    assert len(lines) == 3
    assert all(
        set(line) <= {"accountId", "associateId", "credit", "debit", "description", "taxId"}
        for line in lines
    )
    assert payload["title"] == "x"


def test_update_journal_entry_keeps_the_stored_custom_values(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    body = recorded_read(fixtures_dir, "journal_read", "for_update")
    stored = "<values><customField1>A</customField1><customField2>B &amp; C</customField2></values>"
    body["data"]["custom"] = stored
    serve_read(respx_mock, "journal/read.json", body)
    untouched = tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, title="x")
    assert preview_of(untouched).payload["custom"] == stored, "sent back as stored, unparsed"
    changed = tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, custom={"customField2": "<D>"})
    assert preview_of(changed).payload["custom"] == (
        "<values><customField1>A</customField1><customField2>&lt;D&gt;</customField2></values>"
    )
    assert preview_of(changed).changes == {
        "custom": "<values><customField2>&lt;D&gt;</customField2></values>"
    }


def test_update_journal_entry_clears_the_parameters_named_in_clear(
    replay_fixture: ReplayFixture,
) -> None:
    replay_fixture("journal_read", "for_update")
    result = tasks_write.update_journal_entry(
        DEMO, JOURNAL_ENTRY, title="x", clear=["tax_id", "notes", "items"]
    )
    preview = preview_of(result)
    assert "taxId" not in preview.payload, "left out: upstream empties what is left out"
    assert preview.payload["title"] == "x"
    assert preview.changes == {"title": "x", "taxId": "", "notes": "", "items": "[]"}


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"clear": ["tax"]}, "clear: 'tax' is not an update.json parameter here"),
        ({"clear": ["id"]}, "clear: 'id' is not an update.json parameter here"),
        ({"clear": ["taxId"]}, "clear: 'taxId' is not an update.json parameter here"),
        ({"clear": "notes"}, "clear takes a list of parameter names, not str"),
        (
            {"clear": ["sequence_number_id"]},
            "clear: 'sequence_number_id' is not stored, and an update sends it only when "
            "it is given",
        ),
        ({"title": "x", "clear": ["title"]}, "clear: 'title' is both changed and cleared"),
        (
            {"custom": {"customField1": "x"}, "clear": ["custom"]},
            "clear: 'custom' is both changed and cleared",
        ),
        ({"associate_id": "Muster AG"}, "associate_id must be a person's id, a whole number"),
        ({"associate_id": True}, "associate_id must be a person's id"),
        ({"items": [{"account_id": 3, "associate_id": "Neu AG"}]}, "items[0].associate_id"),
    ],
)
def test_an_update_refuses_its_arguments_before_any_request(
    respx_mock: respx.MockRouter, arguments: dict[str, Any], message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, **arguments)
    assert not respx_mock.calls


@pytest.mark.parametrize("field", ["orderId", "orderBookEntryId", "salaryBookEntryId"], ids=str)
def test_update_journal_entry_refuses_an_entry_another_module_booked(
    respx_mock: respx.MockRouter, fixtures_dir: Path, field: str
) -> None:
    """The recorded read with one of the three set, changed in memory: nothing is written."""
    body = recorded_read(fixtures_dir, "journal_read", "for_update")
    body["data"][field] = 3
    serve_read(respx_mock, "journal/read.json", body)
    write = respx_mock.post(f"{BASE}/journal/update.json")
    with pytest.raises(
        InvalidRequestError,
        match=f"booked by an order or a salary run \\({field} set\\); upstream documents "
        "that such entries cannot be updated here",
    ):
        tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, title="x", confirm=True)
    assert not write.called


def test_a_create_takes_a_persons_id_only(respx_mock: respx.MockRouter) -> None:
    with pytest.raises(InvalidRequestError, match="create a new person with create_person"):
        tasks_write.create_journal_entry(DEMO, associate_id="Neu AG")  # type: ignore[arg-type]
    with pytest.raises(InvalidRequestError, match=r"items\[0\]\.associate_id"):
        tasks_write.create_journal_entry(
            DEMO,
            items=[{"account_id": 3, "debit": 1, "associate_id": "Neu AG"}],  # type: ignore[list-item]
        )
    assert not respx_mock.calls
    sent = tasks_write.create_journal_entry(DEMO, associate_id=7, title="t")
    assert preview_of(sent).payload == {"associateId": "7", "title": "t"}


def test_an_update_refuses_a_wrong_custom_name_before_the_read(
    respx_mock: respx.MockRouter,
) -> None:
    with pytest.raises(InvalidRequestError, match="'colour' is not a custom field name"):
        tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, custom={"colour": "blue"})
    assert not respx_mock.calls


def test_delete_journal_entry_previews_the_entry_it_would_delete(
    replay_fixture: ReplayFixture,
) -> None:
    read = replay_fixture("journal_read", "for_update")
    result = tasks_write.delete_journal_entry(DEMO, JOURNAL_ENTRY)
    assert read.call_count == 1
    preview = result.data
    assert isinstance(preview, WritePreview)
    assert preview.payload == {"ids": str(JOURNAL_ENTRY)}
    assert isinstance(preview.before, JournalEntryDetailProjection)
    assert preview.before.id == JOURNAL_ENTRY
    assert preview.changes is None


def test_delete_journal_entry_with_confirm_reads_then_deletes(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """The read the preview makes, made again: the booked-entry check needs the record."""
    read = replay_fixture("journal_read", "for_update")
    route = replay_fixture("journal_delete", "ok")
    result = tasks_write.delete_journal_entry(DEMO, JOURNAL_ENTRY, confirm=True)
    assert (read.call_count, route.call_count) == (1, 1)
    assert sent_body(route) == recorded_body(fixtures_dir, "journal_delete", "ok")
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (None, "1 book entry deleted")
    assert result.meta.request == {"org": DEMO, "ids": str(JOURNAL_ENTRY)}


def test_deleting_a_gone_entry_is_refused(replay_fixture: ReplayFixture) -> None:
    """Observed: ``success`` false with a top-level ``message``; a refusal, not a 404.

    The read recorded before the entry was deleted, the delete recorded after it: an
    entry that goes between the confirmed call's read and its delete.
    """
    replay_fixture("journal_read", "for_update")
    replay_fixture("journal_delete", "already_deleted")
    with pytest.raises(RequestRejected) as raised:
        tasks_write.delete_journal_entry(DEMO, JOURNAL_ENTRY, confirm=True)
    assert raised.value.errors == []
    assert raised.value.upstream_message == "This book entry does not exist."


@pytest.mark.parametrize("confirm", [False, True])
def test_a_delete_of_an_unknown_id_is_not_found(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, confirm: bool
) -> None:
    """The read refuses it, previewed or confirmed: the delete is never sent."""
    replay_fixture("journal_read", "unknown_id")
    write = respx_mock.post(f"{BASE}/journal/delete.json")
    with pytest.raises(NotFoundError):
        tasks_write.delete_journal_entry(DEMO, 999999999, confirm=confirm)
    assert not write.called


@pytest.mark.parametrize("confirm", [False, True])
@pytest.mark.parametrize("field", ["orderId", "orderBookEntryId", "salaryBookEntryId"], ids=str)
def test_delete_journal_entry_refuses_an_entry_another_module_booked(
    respx_mock: respx.MockRouter, fixtures_dir: Path, field: str, confirm: bool
) -> None:
    """The recorded read with one of the three set, changed in memory: nothing is deleted."""
    body = recorded_read(fixtures_dir, "journal_read", "for_update")
    body["data"][field] = 3
    read = serve_read(respx_mock, "journal/read.json", body)
    write = respx_mock.post(f"{BASE}/journal/delete.json")
    with pytest.raises(
        InvalidRequestError,
        match=f"booked by an order or a salary run \\({field} set\\); upstream documents "
        "that such entries cannot be deleted here",
    ):
        tasks_write.delete_journal_entry(DEMO, JOURNAL_ENTRY, confirm=confirm)
    assert (read.call_count, write.called) == (1, False)


ORDER_BOOKED = 50
"""The entry a seeded purchase order booked, recorded as ``journal_read/order_booked``."""


@pytest.mark.parametrize(
    ("write", "path", "call"),
    [
        (
            "deleted",
            "journal/delete.json",
            lambda: tasks_write.delete_journal_entry(DEMO, ORDER_BOOKED),
        ),
        (
            "updated",
            "journal/update.json",
            lambda: tasks_write.update_journal_entry(DEMO, ORDER_BOOKED, title="x"),
        ),
    ],
    ids=["delete", "update"],
)
def test_a_preview_refuses_an_entry_an_order_booked(
    replay_fixture: ReplayFixture,
    respx_mock: respx.MockRouter,
    write: str,
    path: str,
    call: Callable[[], Any],
) -> None:
    """The recorded read of an entry an order booked (2026-10-26), unchanged: refused.

    ``orderId`` is set, ``attachmentCount`` is ``null``; without ``confirm`` the delete's
    and the update's read refuses it, and nothing is written.
    """
    read = replay_fixture("journal_read", "order_booked")
    sent = respx_mock.post(f"{BASE}/{path}")
    with pytest.raises(
        InvalidRequestError,
        match=rf"journal entry {ORDER_BOOKED} was booked by an order or a salary run "
        rf"\(orderId set\); upstream documents that such entries cannot be {write} here",
    ):
        call()
    assert (read.call_count, sent.called) == (1, False)


# Persons -----------------------------------------------------------------------------


def create_the_recorded_person(confirm: bool = False) -> Any:
    return tasks_write.create_person(
        DEMO,
        company="xippios-live Fixture GmbH",
        addresses=[
            PersonAddressInput(
                type="MAIN",
                address="Musterstrasse 1",
                zip="8001",
                city="Zürich",
                canton="ZH",
                country="CHE",
            )
        ],
        contacts=[{"type": "EMAIL_WORK", "address": "user@example.com"}],  # type: ignore[list-item]
        is_customer=True,
        nr="xippios-live",
        language="DE",
        confirm=confirm,
    )


def test_create_person_previews_without_a_request(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    result = create_the_recorded_person()
    assert not respx_mock.calls
    assert list(preview_of(result).payload.items()) == recorded_body(
        fixtures_dir, "person_create", "ok"
    )
    assert result.meta.request == {"org": DEMO}


def test_create_person_with_confirm_replays_the_recorded_create(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    route = replay_fixture("person_create", "ok")
    result = create_the_recorded_person(confirm=True)
    assert sent_body(route) == recorded_body(fixtures_dir, "person_create", "ok")
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (PERSON, "Person saved")
    assert result.meta.tenant == DEMO


def test_update_person_previews_the_whole_record_after_one_read(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    read = replay_fixture("person_read", "for_update")
    result = tasks_write.update_person(DEMO, PERSON, company="xippios-live Fixture AG")
    assert read.call_count == 1
    preview = result.data
    assert isinstance(preview, WritePreview)
    assert list(preview.payload.items()) == recorded_body(fixtures_dir, "person_update", "ok")
    assert preview.changes == {"company": "xippios-live Fixture AG"}
    assert isinstance(preview.before, PersonDetailProjection)
    assert preview.before.company == "xippios-live Fixture GmbH"
    assert preview.before.addresses[0].city == "Zürich", "the umlaut came back as sent"


def test_update_person_with_confirm_reads_then_sends_the_whole_record(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    replay_fixture("person_read", "for_update")
    update = replay_fixture("person_update", "ok")
    result = tasks_write.update_person(
        DEMO, PERSON, company="xippios-live Fixture AG", confirm=True
    )
    assert sent_body(update) == recorded_body(fixtures_dir, "person_update", "ok")
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (PERSON, "Person saved")


def test_update_person_refuses_a_person_without_company_or_name(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """The recorded read without ``company``, changed in memory: nothing is written."""
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    del body["data"]["company"]
    serve_read(respx_mock, "person/read.json", body)
    write = respx_mock.post(f"{BASE}/person/update.json")
    with pytest.raises(InvalidRequestError, match="gives no company, firstName, lastName"):
        tasks_write.update_person(DEMO, PERSON, department="x", confirm=True)
    assert not write.called
    tasks_write.update_person(DEMO, PERSON, last_name="Muster")


@pytest.mark.parametrize(
    ("field", "stored", "parameter"),
    [
        ("bankAccounts", [{"iban": "CH00", "type": "DEFAULT"}], "bank_accounts"),
        ("children", [{"name": "Anna"}], "children"),
        ("servicePeriods", [{"dateEntry": "2020-01-01"}], "service_periods"),
        ("insuranceContracts", [{"typeId": 1}], "insurance_contracts"),
        ("attachments", [{"fileId": 3}], "attachments"),
        ("certificateValuesMap", {"F": True}, "certificate_values"),
    ],
)
def test_update_person_refuses_stored_lists_it_cannot_carry(
    respx_mock: respx.MockRouter, fixtures_dir: Path, field: str, stored: Any, parameter: str
) -> None:
    """Changed in memory: these were only ever seen empty, so their shape is unknown."""
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    body["data"][field] = stored
    serve_read(respx_mock, "person/read.json", body)
    with pytest.raises(InvalidRequestError, match=f"holds {parameter},"):
        tasks_write.update_person(DEMO, PERSON, department="x")


@pytest.mark.parametrize(
    ("where", "change", "message"),
    [
        ("addresses", {"titleId": 1}, "addresses, one with a titleId"),
        ("contacts", {"purpose": "INVOICE"}, "contacts, one with a purpose"),
    ],
)
def test_update_person_refuses_undocumented_stored_keys(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    where: str,
    change: dict[str, Any],
    message: str,
) -> None:
    """Observed 2026-10-24: an address's ``titleId`` is stored and read back, a contact's
    ``purpose`` was not stored; neither is in its table, so neither can be sent back."""
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    body["data"][where][0].update(change)
    serve_read(respx_mock, "person/read.json", body)
    with pytest.raises(InvalidRequestError, match=message):
        tasks_write.update_person(DEMO, PERSON, department="x")
    replaced = tasks_write.update_person(DEMO, PERSON, clear=[where])
    assert where not in preview_of(replaced).payload


@pytest.mark.parametrize(
    ("role", "unknown"),
    [("isEmployee", ["user_id"]), ("isInsurance", ["insurance_nr", "insurance_member_nr"])],
)
def test_update_person_refuses_fields_whose_absence_is_unknown(
    respx_mock: respx.MockRouter, fixtures_dir: Path, role: str, unknown: list[str]
) -> None:
    """An employee's ``userId`` and an insurance's numbers were never seen come back."""
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    body["data"][role] = True
    serve_read(respx_mock, "person/read.json", body)
    write = respx_mock.post(f"{BASE}/person/update.json")
    with pytest.raises(InvalidRequestError, match=f"read shows no {', '.join(unknown)}"):
        tasks_write.update_person(DEMO, PERSON, department="x", confirm=True)
    assert not write.called
    cleared = preview_of(tasks_write.update_person(DEMO, PERSON, department="x", clear=unknown))
    assert cleared.changes == {"department": "x", **{PERSON_NAMES[n]: "" for n in unknown}}
    values: dict[str, Any] = dict.fromkeys(unknown, "1")
    given = tasks_write.update_person(DEMO, PERSON, **values)
    assert preview_of(given).payload[PERSON_NAMES[unknown[0]]] == "1"


PERSON_NAMES = {
    "user_id": "userId",
    "insurance_nr": "insuranceNr",
    "insurance_member_nr": "insuranceMemberNr",
}


def test_update_person_clears_and_validates_clear(
    respx_mock: respx.MockRouter, replay_fixture: ReplayFixture
) -> None:
    with pytest.raises(InvalidRequestError, match=r"clear: 'id' is not an update\.json parameter"):
        tasks_write.update_person(DEMO, PERSON, clear=["id"])
    with pytest.raises(InvalidRequestError, match="'nr' is both changed and cleared"):
        tasks_write.update_person(DEMO, PERSON, nr="x", clear=["nr"])
    assert not respx_mock.calls
    replay_fixture("person_read", "for_update")
    preview = preview_of(tasks_write.update_person(DEMO, PERSON, clear=["nr", "contacts"]))
    assert "nr" not in preview.payload
    assert "contacts" not in preview.payload
    assert preview.changes == {"nr": "", "contacts": "[]"}


def test_clearing_a_flag_sends_false(
    respx_mock: respx.MockRouter, replay_fixture: ReplayFixture
) -> None:
    """Clearing a yes/no value means ``false``: the payload sends it, ``changes`` shows it.

    The recorded person is a customer (``isCustomer`` true) and not inactive; the
    confirmed call is answered by a mocked success, not a fixture, to show the form sent.
    """
    replay_fixture("person_read", "for_update")
    preview = preview_of(
        tasks_write.update_person(DEMO, PERSON, clear=["is_customer", "is_inactive"])
    )
    assert (preview.payload["isCustomer"], preview.payload["isInactive"]) == ("false", "false")
    assert preview.changes == {"isCustomer": "false", "isInactive": "false"}
    assert preview.payload["isVendor"] == "false", "a flag not cleared is carried over"
    write = respx_mock.post(f"{BASE}/person/update.json").respond(
        200, json={"success": True, "insertId": PERSON, "message": "Person saved"}
    )
    tasks_write.update_person(DEMO, PERSON, clear=["is_customer"], confirm=True)
    assert ("isCustomer", "false") in sent_body(write)
    assert sent_body(write) == list(
        preview_of(tasks_write.update_person(DEMO, PERSON, clear=["is_customer"])).payload.items()
    )


UPDATE_TABLES: dict[str, dict[str, str]] = {
    "update_journal_entry": tasks_write.JOURNAL_UPDATE,
    "update_person": tasks_write.PERSON_UPDATE,
    "update_order": tasks_write.ORDER_UPDATE,
}
"""Each update task's table of the parameters its ``update.json`` documents."""
UPDATES = [getattr(tasks_write, name) for name in UPDATE_TABLES]


@pytest.mark.parametrize("task", UPDATES, ids=lambda t: t.__name__)
def test_clearing_a_parameter_that_is_never_sent_is_refused(
    respx_mock: respx.MockRouter, task: Callable[..., Any]
) -> None:
    """``sequence_number_id`` is sent only when given; a clear of it would be a no-op."""
    with pytest.raises(InvalidRequestError) as raised:
        task(DEMO, 1, clear=["sequence_number_id"])
    assert str(raised.value).endswith("clearing it would change nothing: drop it from clear"), (
        "the refusal says what to do"
    )
    assert not respx_mock.calls


@pytest.mark.parametrize("task", UPDATES, ids=lambda t: t.__name__)
def test_every_boolean_update_parameter_is_a_flag(task: Callable[..., Any]) -> None:
    """``_FLAGS`` holds every ``bool | None`` parameter of an update task, ``confirm`` aside."""
    facade: Any = task
    hints = typing.get_type_hints(facade.async_fn)
    booleans = {name for name, hint in hints.items() if hint == bool | None}
    assert booleans <= tasks_write._FLAGS
    table = UPDATE_TABLES[task.__name__]
    assert tasks_write._FLAGS & set(table) == booleans
    assert tasks_write._FLAGS.issubset(set().union(*UPDATE_TABLES.values()))


def test_every_update_task_has_a_table() -> None:
    """The write tasks named ``update_*`` are exactly those with a table here, but one.

    ``update_order_status`` calls ``order/update_status.json``, no ``update.json``: it
    sends the ids and the status it is given, no record to read and merge.
    """
    updates = {name for name in tasks_write.__all__ if name.startswith("update_")}
    assert updates - {"update_order_status"} == set(UPDATE_TABLES)


def test_the_update_takes_every_documented_parameter_but_the_unsent_from_the_record(
    fixtures_dir: Path,
) -> None:
    """``_UNSENT`` is exactly what an update neither derives nor blocks on, per resource."""
    entry = JournalEntryDetail.model_validate(
        recorded_read(fixtures_dir, "journal_read", "for_update")["data"]
    )
    values, stored = tasks_write._journal_values(entry)
    assert set(tasks_write.JOURNAL_UPDATE) - set(values) - set(stored) == set(tasks_write._UNSENT)
    person = PersonDetail.model_validate(
        recorded_read(fixtures_dir, "person_read", "for_update")["data"]
    )
    person_values, person_stored, _ = tasks_write._person_values(person)
    assert set(tasks_write.PERSON_UPDATE) - set(person_values) - set(person_stored) == set(
        tasks_write._UNSENT
    )
    order = OrderDetail.model_validate(
        recorded_read(fixtures_dir, "order_read", "for_update")["data"]
    )
    order_values, order_stored = tasks_write._order_values(order)
    assert set(tasks_write.ORDER_UPDATE) - set(order_values) - set(order_stored) == set(
        tasks_write._UNSENT
    )


def test_update_person_refuses_an_address_it_cannot_carry(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """An address type outside the documented value set, changed in memory."""
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    body["data"]["addresses"][0]["type"] = "SUMMER_HOUSE"
    serve_read(respx_mock, "person/read.json", body)
    with pytest.raises(InvalidRequestError, match="holds addresses,"):
        tasks_write.update_person(DEMO, PERSON, department="x")
    given = tasks_write.update_person(DEMO, PERSON, addresses=[{"type": "MAIN", "city": "Bern"}])  # type: ignore[list-item]
    assert preview_of(given).payload["addresses"] == '[{"type":"MAIN","city":"Bern"}]'


def test_delete_person_previews_then_deletes(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    replay_fixture("person_read", "for_update")
    preview = tasks_write.delete_person(DEMO, PERSON).data
    assert isinstance(preview, WritePreview)
    assert isinstance(preview.before, PersonDetailProjection)
    assert (preview.before.id, preview.payload) == (PERSON, {"ids": str(PERSON)})
    route = replay_fixture("person_delete", "ok")
    result = tasks_write.delete_person(DEMO, PERSON, confirm=True)
    assert sent_body(route) == recorded_body(fixtures_dir, "person_delete", "ok")
    assert isinstance(result.data, WriteResult)
    assert result.data.message == "1 person deleted"


SSN = "756.0000.0000.00"
"""A made-up social security number: tests only, never sent anywhere."""
IBAN = "CH00 TEST 0000 0000 0000 0"
"""A made-up IBAN: tests only, never sent anywhere."""


def test_create_person_never_echoes_ssn_or_iban(respx_mock: respx.MockRouter) -> None:
    """ADR-0017: the values go upstream, but neither the preview nor ``meta.request`` shows them.

    The confirmed call is answered by a mocked success, not a fixture, to show what was
    sent: a fixture never carries the values.
    """
    arguments: dict[str, Any] = {
        "company": "xippios-live Fixture GmbH",
        "ssn": SSN,
        "bank_accounts": [BankAccountInput(iban=IBAN, type="SALARY", bic="TESTCHZZ")],
    }
    preview = preview_of(tasks_write.create_person(DEMO, **arguments))
    assert preview.payload["ssn"] == "REDACTED"
    assert json.loads(preview.payload["bankAccounts"]) == [
        {"iban": "REDACTED", "type": "SALARY", "bic": "TESTCHZZ"}
    ]
    write = respx_mock.post(f"{BASE}/person/create.json").respond(
        200, json={"success": True, "insertId": PERSON, "message": "Person saved"}
    )
    result = tasks_write.create_person(DEMO, **arguments, confirm=True)
    sent = dict(sent_body(write))
    assert sent["ssn"] == SSN, "upstream receives the value"
    assert json.loads(sent["bankAccounts"])[0]["iban"] == IBAN
    assert result.meta.request["ssn"] == "REDACTED"
    assert json.loads(result.meta.request["bankAccounts"])[0]["iban"] == "REDACTED"
    shown = result.model_dump_json() + preview.model_dump_json()
    assert SSN not in shown
    assert IBAN not in shown


def test_update_person_shows_no_stored_or_given_ssn(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """The recorded read with an ``ssn``, changed in memory: the update sends it back.

    The preview's ``payload`` and ``changes`` show ``REDACTED`` and its ``before`` has no
    ``ssn``; a cleared ``ssn`` shows as empty, which reveals nothing.
    """
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    body["data"]["ssn"] = SSN
    serve_read(respx_mock, "person/read.json", body)
    kept = preview_of(tasks_write.update_person(DEMO, PERSON, department="x"))
    assert kept.payload["ssn"] == "REDACTED"
    assert isinstance(kept.before, PersonDetailProjection)
    assert not hasattr(kept.before, "ssn")
    given = preview_of(tasks_write.update_person(DEMO, PERSON, ssn="756.1111.1111.11"))
    assert given.changes == {"ssn": "REDACTED"}
    assert given.payload["ssn"] == "REDACTED"
    cleared = preview_of(tasks_write.update_person(DEMO, PERSON, clear=["ssn"]))
    assert cleared.changes == {"ssn": ""}
    assert "ssn" not in cleared.payload
    write = respx_mock.post(f"{BASE}/person/update.json").respond(
        200, json={"success": True, "insertId": PERSON, "message": "Person saved"}
    )
    result = tasks_write.update_person(DEMO, PERSON, department="x", confirm=True)
    assert dict(sent_body(write))["ssn"] == SSN, "the stored value is carried over"
    assert result.meta.request["ssn"] == "REDACTED"


def test_a_previewed_record_leaves_out_ssn_and_iban(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """Changed in memory: a stored ``ssn`` and bank account stay out of ``before``."""
    body = recorded_read(fixtures_dir, "person_read", "for_update")
    body["data"]["ssn"] = SSN
    body["data"]["bankAccounts"] = [{"iban": IBAN, "type": "DEFAULT"}]
    serve_read(respx_mock, "person/read.json", body)
    preview = preview_of(tasks_write.delete_person(DEMO, PERSON))
    assert isinstance(preview.before, PersonDetailProjection)
    assert preview.before.bank_accounts == [{"type": "DEFAULT"}]
    assert SSN not in preview.model_dump_json()
    assert IBAN not in preview.model_dump_json()


def test_update_person_never_echoes_a_given_iban(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """ADR-0017: an ``iban`` given to ``update_person`` goes upstream, never into a result.

    The recorded read the update starts from, and for the confirmed call the recorded
    update's answer: a replay never matches the request body, so the form asserted here
    is the one the task sent, with the made-up value no fixture carries.
    """
    accounts = [BankAccountInput(iban=IBAN, type="DEFAULT", bic="TESTCHZZ")]
    shown = [{"iban": "REDACTED", "type": "DEFAULT", "bic": "TESTCHZZ"}]
    read = replay_fixture("person_read", "for_update")
    preview = preview_of(tasks_write.update_person(DEMO, PERSON, bank_accounts=accounts))
    assert preview.changes is not None
    assert set(preview.changes) == {"bankAccounts"}
    assert json.loads(preview.changes["bankAccounts"]) == shown
    assert json.loads(preview.payload["bankAccounts"]) == shown
    update = replay_fixture("person_update", "ok")
    result = tasks_write.update_person(DEMO, PERSON, bank_accounts=accounts, confirm=True)
    assert read.call_count == 2, "the confirmed call reads again"
    sent = dict(sent_body(update))
    assert json.loads(sent["bankAccounts"]) == [
        {"iban": IBAN, "type": "DEFAULT", "bic": "TESTCHZZ"}
    ], "upstream receives the value"
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (PERSON, "Person saved")
    assert json.loads(result.meta.request["bankAccounts"]) == shown
    assert IBAN not in result.model_dump_json() + preview.model_dump_json()


def test_a_shown_iban_is_redacted_whatever_the_case_of_its_key() -> None:
    """The key of an item of ``bankAccounts`` is matched in any case, as the projection's.

    ``BankAccountInput`` sends ``iban`` only, so this goes to ``_shown`` directly.
    """
    sent = json_text(
        [
            {"IBAN": IBAN, "type": "DEFAULT"},
            {"Iban": IBAN, "type": "SALARY"},
            {"iban": "", "type": "OTHER"},
        ]
    )
    shown = tasks_write._shown({"bankAccounts": sent, "company": "x"})
    assert json.loads(shown["bankAccounts"]) == [
        {"IBAN": "REDACTED", "type": "DEFAULT"},
        {"Iban": "REDACTED", "type": "SALARY"},
        {"iban": "", "type": "OTHER"},
    ]
    assert shown["company"] == "x"
    assert IBAN not in json.dumps(shown)


# Orders ------------------------------------------------------------------------------


def create_the_recorded_order(confirm: bool = False) -> Any:
    return tasks_write.create_order(
        DEMO,
        associate_id=7,
        category_id=4,
        date=DAY,
        nr="xippios-live",
        description="xippios-live fixture",
        language="DE",
        items=[
            OrderItemInput(
                account_id=42,
                name="xippios-live item",
                unit_price=Decimal("100.00"),
                quantity=Decimal(1),
                tax_id=9,
            )
        ],
        confirm=confirm,
    )


def test_create_order_previews_without_a_request(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    result = create_the_recorded_order()
    assert not respx_mock.calls
    assert list(preview_of(result).payload.items()) == recorded_body(
        fixtures_dir, "order_create", "ok"
    )


def test_create_order_with_confirm_replays_the_recorded_create(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    route = replay_fixture("order_create", "ok")
    result = create_the_recorded_order(confirm=True)
    assert sent_body(route) == recorded_body(fixtures_dir, "order_create", "ok")
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (ORDER, "Rechnung saved")
    assert result.meta.endpoint == "order/create.json"


def test_create_order_sends_several_partners_comma_separated(respx_mock: respx.MockRouter) -> None:
    result = tasks_write.create_order(DEMO, associate_id=[7, 8], category_id=4, date=DAY)
    assert preview_of(result).payload == {
        "associateId": "7,8",
        "categoryId": "4",
        "date": "2026-10-24",
    }
    with pytest.raises(InvalidRequestError, match="associate_id takes a person's id"):
        tasks_write.create_order(DEMO, associate_id=[], category_id=4, date=DAY)
    assert not respx_mock.calls


def update_the_recorded_order(confirm: bool = False) -> Any:
    """The update recorded on 2026-10-27: two header fields changed, no ``items`` given."""
    return tasks_write.update_order(
        DEMO,
        ORDER,
        description="xippios-live fixture updated",
        due_days=30,
        confirm=confirm,
    )


def test_update_order_previews_the_whole_order_after_one_read(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    read = replay_fixture("order_read", "for_update")
    result = update_the_recorded_order()
    assert read.call_count == 1, "one read, never a write"
    preview = preview_of(result)
    assert preview.endpoint == "order/update.json"
    assert list(preview.payload.items()) == recorded_body(fixtures_dir, "order_update", "ok")
    assert preview.changes == {"description": "xippios-live fixture updated", "dueDays": "30"}
    assert isinstance(preview.before, OrderDetail)
    assert (preview.before.id, preview.before.description, preview.before.due_days) == (
        ORDER,
        "xippios-live fixture",
        None,
    )
    assert result.meta.endpoint == "order/update.json"
    assert (result.meta.tenant, result.meta.request) == (DEMO, {"org": DEMO})


def test_update_order_with_confirm_reads_then_sends_the_whole_order(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    read = replay_fixture("order_read", "for_update")
    update = replay_fixture("order_update", "ok")
    result = update_the_recorded_order(confirm=True)
    assert (read.call_count, update.call_count) == (1, 1)
    sent = update.calls.last.request
    assert sent.headers["Content-Type"] == FORM_CONTENT_TYPE
    assert sent_body(update) == recorded_body(fixtures_dir, "order_update", "ok")
    written = result.data
    assert isinstance(written, WriteResult)
    assert (written.performed, written.insert_id, written.message) == (
        True,
        ORDER,
        "Rechnung saved",
    ), "an update answers the order's own id"
    assert result.meta.request == {
        "org": DEMO,
        **dict(recorded_body(fixtures_dir, "order_update", "ok")),
    }


ITEM_KEYS = frozenset(OrderItemInput.model_fields)
"""The keys the items table documents, by task name: what an update carries back."""


def test_update_order_carries_the_items_back_unchanged(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """The items the update sent are the stored ones, and the read after it shows them so.

    ``order_read/after_update`` was recorded right after the update: every field of the
    item is as before, the computed totals included, but its ``id``: upstream stores the
    items an update sends anew (26 became 27).
    """
    replay_fixture("order_read", "for_update")
    payload = preview_of(update_the_recorded_order()).payload
    before = OrderDetail.model_validate(
        recorded_read(fixtures_dir, "order_read", "for_update")["data"]
    )
    after = OrderDetail.model_validate(
        recorded_read(fixtures_dir, "order_read", "after_update")["data"]
    )
    assert json.loads(payload["items"]) == [
        {
            "accountId": 42,
            "name": "xippios-live item",
            "unitPrice": 100,
            "quantity": 1,
            "taxId": 9,
            "type": "ARTICLE",
        }
    ], "the stored item under the table's keys, none of the computed ones"
    assert [item.model_dump(exclude={"id"}) for item in after.items] == [
        item.model_dump(exclude={"id"}) for item in before.items
    ]
    assert ([i.id for i in before.items], [i.id for i in after.items]) == ([26], [27])
    assert (after.description, after.due_days) == ("xippios-live fixture updated", 30)
    assert (after.sub_total, after.tax, after.total) == (
        before.sub_total,
        before.tax,
        before.total,
    )
    assert after.status_id == before.status_id, "statusId sent back as stored"


def test_update_order_replaces_the_items_when_given(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    replay_fixture("order_read", "for_update")
    items: list[Any] = [
        OrderItemInput(account_id=42, name="xippios-live chair", unit_price=Decimal("172.32")),
        {"account_id": 42, "name": "xippios-live desk", "unit_price": 680, "quantity": 2},
    ]
    preview = preview_of(tasks_write.update_order(DEMO, ORDER, items=items))
    sent = (
        '[{"accountId":42,"name":"xippios-live chair","unitPrice":172.32},'
        '{"accountId":42,"name":"xippios-live desk","unitPrice":680,"quantity":2}]'
    )
    assert preview.payload["items"] == sent
    assert preview.changes == {"items": sent}
    recorded = dict(recorded_body(fixtures_dir, "order_update", "ok"))
    stored = {name: value for name, value in recorded.items() if name not in ("items", "dueDays")}
    assert {name: value for name, value in preview.payload.items() if name != "items"} == {
        **stored,
        "description": "xippios-live fixture",
    }, "every other field as stored: the recorded update without its two changes"


def test_update_order_clears_items_flags_and_text(replay_fixture: ReplayFixture) -> None:
    replay_fixture("order_read", "for_update")
    preview = preview_of(
        tasks_write.update_order(
            DEMO, ORDER, clear=["items", "is_display_item_gross", "notes", "description"]
        )
    )
    assert "items" not in preview.payload, "left out: upstream empties what is left out"
    assert "description" not in preview.payload
    assert preview.payload["isDisplayItemGross"] == "false"
    assert preview.changes == {
        "items": "[]",
        "isDisplayItemGross": "false",
        "notes": "",
        "description": "",
    }
    emptied = preview_of(tasks_write.update_order(DEMO, ORDER, items=[]))
    assert "items" not in emptied.payload
    assert emptied.changes == {"items": "[]"}, "an empty list given is shown"


def test_update_order_keeps_the_stored_custom_values(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """The recorded read with custom values, changed in memory."""
    body = recorded_read(fixtures_dir, "order_read", "for_update")
    stored = (
        "<values><customField3>A-17</customField3><customField4>B &amp; C</customField4></values>"
    )
    body["data"]["custom"] = stored
    serve_read(respx_mock, "order/read.json", body)
    untouched = tasks_write.update_order(DEMO, ORDER, description="x")
    assert preview_of(untouched).payload["custom"] == stored, "sent back as stored, unparsed"
    changed = tasks_write.update_order(DEMO, ORDER, custom={"customField3": "A-18"})
    assert preview_of(changed).payload["custom"] == (
        "<values><customField3>A-18</customField3><customField4>B &amp; C</customField4></values>"
    )
    assert preview_of(changed).changes == {
        "custom": "<values><customField3>A-18</customField3></values>"
    }
    cleared = tasks_write.update_order(DEMO, ORDER, clear=["custom"])
    assert "custom" not in preview_of(cleared).payload
    assert preview_of(cleared).changes == {"custom": ""}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda data: data.update(attachments=[{"fileId": 3}]),
            "holds attachments, never observed filled",
        ),
        (
            lambda data: data["items"][0].update(allocations=[{"share": 1, "toCostCenterId": 2}]),
            "holds items, one with allocations, never observed filled",
        ),
        (
            lambda data: data["items"][0].update(attachments=[{"fileId": 3}]),
            "holds items, one with attachments, a key the items table does not document",
        ),
        (
            lambda data: data["items"][0].update(isOptional=True, optional=True),
            "holds items, one marked optional, a key the items table does not document",
        ),
        (
            lambda data: data["items"][0].update(accountId=None),
            "holds items, one outside the documented value sets or without its account",
        ),
        (
            lambda data: data["items"][0].update(type="BUNDLE"),
            "holds items, one outside the documented value sets",
        ),
    ],
    ids=[
        "attachments",
        "item-allocations",
        "item-attachments",
        "item-optional",
        "item-without-account",
        "item-type",
    ],
)
def test_update_order_refuses_what_it_cannot_carry(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    change: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    """The recorded read changed in memory: nothing is written, unless replaced or cleared."""
    body = recorded_read(fixtures_dir, "order_read", "for_update")
    change(body["data"])
    serve_read(respx_mock, "order/read.json", body)
    write = respx_mock.post(f"{BASE}/order/update.json")
    with pytest.raises(InvalidRequestError, match=re.escape(message)) as raised:
        tasks_write.update_order(DEMO, ORDER, description="x", confirm=True)
    assert str(raised.value).endswith("Nothing was sent")
    assert not write.called
    parameter = "attachments" if "holds attachments" in message else "items"
    assert f"pass {parameter} to replace it" in str(raised.value)
    cleared = preview_of(tasks_write.update_order(DEMO, ORDER, clear=[parameter]))
    assert parameter not in cleared.payload
    emptied: dict[str, Any] = {parameter: []}
    replaced = preview_of(tasks_write.update_order(DEMO, ORDER, **emptied))
    assert replaced.changes == {parameter: "[]"}


@pytest.mark.parametrize(
    ("change", "arguments", "missing"),
    [
        (lambda data: data.pop("associateId"), {"description": "x"}, "associateId"),
        (lambda data: None, {"clear": ["associate_id"]}, "associateId"),
        (lambda data: None, {"clear": ["category_id", "date"]}, "categoryId, date"),
    ],
    ids=["read-without-partner", "partner-cleared", "category-and-date-cleared"],
)
def test_update_order_refuses_an_order_without_a_mandatory_parameter(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    change: Callable[[dict[str, Any]], object],
    arguments: dict[str, Any],
    missing: str,
) -> None:
    """``associateId``, ``categoryId`` and ``date`` are mandatory: given, stored or refused."""
    body = recorded_read(fixtures_dir, "order_read", "for_update")
    change(body["data"])
    serve_read(respx_mock, "order/read.json", body)
    write = respx_mock.post(f"{BASE}/order/update.json")
    with pytest.raises(
        InvalidRequestError, match=f"gives no {missing}, which update.json requires"
    ):
        tasks_write.update_order(DEMO, ORDER, **arguments, confirm=True)
    assert not write.called


def test_update_order_takes_a_partner_the_read_lacks(
    respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    body = recorded_read(fixtures_dir, "order_read", "for_update")
    del body["data"]["associateId"]
    serve_read(respx_mock, "order/read.json", body)
    preview = preview_of(tasks_write.update_order(DEMO, ORDER, associate_id=8))
    assert preview.payload["associateId"] == "8"
    assert preview.changes == {"associateId": "8"}


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"associate_id": "Muster AG"}, "associate_id must be a person's id, a whole number"),
        ({"associate_id": True}, "associate_id must be a person's id"),
        ({"items": [{"name": "x", "unit_price": 1}]}, "items[0].account_id: Field required"),
        ({"items": {"account_id": 42}}, "items takes a list, not dict"),
        ({"language": "de"}, "language must be one of DE, EN, FR, IT"),
        ({"recurrence": "HOURLY"}, "recurrence must be one of MONTHLY"),
        ({"notify_type": "SOMETIMES"}, "notify_type must be one of NONE"),
        ({"description": "x", "clear": ["description"]}, "'description' is both changed"),
        ({"clear": ["dueDays"]}, "clear: 'dueDays' is not an update.json parameter here"),
        ({"clear": ["id"]}, "clear: 'id' is not an update.json parameter here"),
        ({"custom": {"colour": "blue"}}, "'colour' is not a custom field name"),
    ],
)
def test_update_order_refuses_its_arguments_before_any_request(
    respx_mock: respx.MockRouter, arguments: dict[str, Any], message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks_write.update_order(DEMO, ORDER, **arguments)
    assert not respx_mock.calls


def test_delete_order_previews_the_order_then_deletes(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """The preview reads a seeded order (``order_read/by_id``): a preview never writes."""
    replay_fixture("order_read", "by_id")
    preview = tasks_write.delete_order(DEMO, 3).data
    assert isinstance(preview, WritePreview)
    assert isinstance(preview.before, OrderDetail)
    assert (preview.before.nr, preview.payload) == ("RE-2026-103", {"ids": "3"})
    route = replay_fixture("order_delete", "ok")
    result = tasks_write.delete_order(DEMO, ORDER, confirm=True)
    assert sent_body(route) == recorded_body(fixtures_dir, "order_delete", "ok")
    assert isinstance(result.data, WriteResult)
    assert result.data.message == "1 document deleted"


# Order statuses and payments ----------------------------------------------------------


def recorded_invoice_statuses() -> list[int]:
    """The status ids of the default invoice category, in their order, as recorded.

    From ``order_category_list/default`` (recorded on 2026-10-24): never a guessed id.
    """
    raw = load_fixture(_FIXTURES / "order_category_list" / "default.json").response.body
    categories = ListResponse[OrderCategory].model_validate_json(raw or "")
    (invoice,) = [
        category
        for category in categories.data
        if "<en>Invoice</en>" in (category.name_singular or "") and not category.is_inactive
    ]
    return [status.id for status in invoice.status]


DRAFT, OPEN = recorded_invoice_statuses()[:2]
"""The first two statuses of the invoice category (Draft, then Open in the recording)."""
PAY_DAY = DAY
"""The payment's execution date: the date of every record the live tests write."""
PAID = 26
"""The marked purchase order the status and payment fixtures of 2026-10-29 record."""


def recorded_purchase_invoice_status() -> int:
    """The status the recorded update set, chosen as the live test chooses it.

    From ``order_category_list/purchase`` (recorded on 2026-10-29): the purchase invoice
    category's next status after the first that names no follow-up action, an open one
    first (gap, row 242).
    """
    raw = load_fixture(_FIXTURES / "order_category_list" / "purchase.json").response.body
    categories = ListResponse[OrderCategory].model_validate_json(raw or "")
    (invoice,) = [
        category
        for category in categories.data
        if "<en>Invoice</en>" in (category.name_singular or "") and not category.is_inactive
    ]
    _, *others = invoice.status
    actionless = [status for status in others if not status.action_id]
    return min(actionless, key=lambda status: (status.is_closed, status.pos or 0)).id


REMINDED = recorded_purchase_invoice_status()
"""The status ``order_update_status/ok`` set on the order 26 (Reminded 1)."""


def test_update_order_status_previews_the_payload_without_a_request(
    respx_mock: respx.MockRouter,
) -> None:
    result = tasks_write.update_order_status(DEMO, [ORDER, 21], OPEN)
    assert not respx_mock.calls, "nothing is read and nothing is sent"
    preview = preview_of(result)
    assert preview.endpoint == "order/update_status.json"
    assert list(preview.payload.items()) == [("ids", f"{ORDER},21"), ("statusId", str(OPEN))]
    assert (preview.before, preview.changes) == (None, None)
    assert (result.meta.endpoint, result.meta.tenant) == ("order/update_status.json", DEMO)
    assert result.meta.request == {"org": DEMO}, "the payload is in data, never twice"


def test_update_order_status_with_confirm_replays_the_recorded_update(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    preview = preview_of(tasks_write.update_order_status(DEMO, [PAID], REMINDED))
    recorded = recorded_body(fixtures_dir, "order_update_status", "ok")
    assert list(preview.payload.items()) == recorded, "the preview is what upstream received"
    route = replay_fixture("order_update_status", "ok")
    result = tasks_write.update_order_status(DEMO, [PAID], REMINDED, confirm=True)
    assert route.call_count == 1
    assert len(respx_mock.calls) == 1, "no read before the write"
    assert route.calls.last.request.headers["Content-Type"] == FORM_CONTENT_TYPE
    assert sent_body(route) == recorded
    assert isinstance(result.data, WriteResult)
    assert (result.data.performed, result.data.insert_id, result.data.message) == (
        True,
        None,
        "Status changed",
    )
    assert result.meta.request == {"org": DEMO, **dict(recorded)}


def test_create_order_payment_previews_the_payload_without_a_request(
    respx_mock: respx.MockRouter,
) -> None:
    result = tasks_write.create_order_payment(
        DEMO,
        PAY_DAY,
        [ORDER, 21],
        amount=Decimal("50.00"),
        is_combine=False,
        status_id=OPEN,
        type="CASH_PDF",
    )
    assert not respx_mock.calls
    preview = preview_of(result)
    assert preview.endpoint == "order/payment/create.json"
    assert list(preview.payload.items()) == [
        ("date", "2026-10-24"),
        ("orderIds", f"{ORDER},21"),
        ("amount", "50.00"),
        ("isCombine", "false"),
        ("statusId", str(OPEN)),
        ("type", "CASH_PDF"),
    ], "the order of the parameter table"
    assert (preview.before, preview.changes) == (None, None)
    assert result.meta.request == {"org": DEMO}


def test_create_order_payment_leaves_upstreams_defaults_to_upstream(
    respx_mock: respx.MockRouter,
) -> None:
    """Without ``amount`` and ``type`` upstream pays every open amount as ``PAIN``."""
    preview = preview_of(tasks_write.create_order_payment(DEMO, PAY_DAY, [ORDER]))
    assert preview.payload == {"date": "2026-10-24", "orderIds": str(ORDER)}
    assert not respx_mock.calls


def test_create_order_payment_with_confirm_replays_the_recorded_payment(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """``CASH_PDF`` for the order 26: created, no ``insertId`` in the answer."""
    preview = preview_of(tasks_write.create_order_payment(DEMO, PAY_DAY, [PAID], type="CASH_PDF"))
    recorded = recorded_body(fixtures_dir, "order_payment_create", "cash_pdf")
    assert list(preview.payload.items()) == recorded, "the preview is what upstream received"
    route = replay_fixture("order_payment_create", "cash_pdf")
    result = tasks_write.create_order_payment(DEMO, PAY_DAY, [PAID], type="CASH_PDF", confirm=True)
    assert len(respx_mock.calls) == 1, "no read before the write"
    assert route.calls.last.request.headers["Content-Type"] == FORM_CONTENT_TYPE
    assert sent_body(route) == recorded
    assert isinstance(result.data, WriteResult)
    assert (result.data.insert_id, result.data.message) == (None, "Payment order created")
    assert result.meta.endpoint == "order/payment/create.json"
    assert result.meta.request == {"org": DEMO, **dict(recorded)}


def test_a_refused_payment_names_the_date_and_the_bank_accounts(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """``PAIN`` for the order 26 on 2026-10-29: refused, the fields and messages named."""
    preview = preview_of(tasks_write.create_order_payment(DEMO, PAY_DAY, [PAID], type="PAIN"))
    recorded = recorded_body(fixtures_dir, "order_payment_create", "pain")
    assert list(preview.payload.items()) == recorded
    route = replay_fixture("order_payment_create", "pain")
    with pytest.raises(RequestRejected) as refused:
        tasks_write.create_order_payment(DEMO, PAY_DAY, [PAID], type="PAIN", confirm=True)
    assert sent_body(route) == recorded
    assert [(error.field, error.message) for error in refused.value.errors] == [
        ("date", "The date cannot be in the past."),
        (None, "Rechnung xippios-live: Sender: Bank account must be set."),
        (None, "Rechnung xippios-live: Recipient: Bank account must be set."),
        (None, "Rechnung xippios-live: Sender: BIC must be set."),
    ]
    assert str(refused.value).startswith(
        "CashCtrl rejected the request: date: The date cannot be in the past.; "
    )


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: tasks_write.update_order_status(DEMO, [], OPEN), "ids takes a list of at least"),
        (
            lambda: tasks_write.update_order_status(DEMO, ORDER, OPEN),  # type: ignore[arg-type]
            "ids takes a list of at least one order id, e.g. [20], not 20",
        ),
        (
            lambda: tasks_write.update_order_status(DEMO, "20,21", OPEN),  # type: ignore[arg-type]
            "ids takes a list",
        ),
        (
            lambda: tasks_write.update_order_status(DEMO, [ORDER, 0, True], OPEN),
            "ids: an id is a whole number of at least 1, not 0, True",
        ),
        (
            lambda: tasks_write.update_order_status(DEMO, [ORDER], 0),
            "status_id must be a status id from list_order_categories",
        ),
        (
            lambda: tasks_write.update_order_status(DEMO, [ORDER], None),  # type: ignore[arg-type]
            "status_id must be a status id",
        ),
        (
            lambda: tasks_write.create_order_payment(DEMO, PAY_DAY, []),
            "order_ids takes a list of at least one order id",
        ),
        (
            lambda: tasks_write.create_order_payment(DEMO, PAY_DAY, [ORDER], status_id=-1),
            "status_id must be a status id",
        ),
        (
            lambda: tasks_write.create_order_payment(DEMO, PAY_DAY, [ORDER], type="SWIFT"),  # type: ignore[arg-type]
            "type must be one of PAIN, SEPA_PAIN, WIRE_PDF, CASH_PDF, not 'SWIFT'",
        ),
    ],
)
def test_status_and_payment_arguments_are_refused_before_any_request(
    respx_mock: respx.MockRouter, call: Callable[[], Any], message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        call()
    assert not respx_mock.calls


@pytest.mark.anyio
async def test_status_and_payment_through_the_write_server(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, fixtures_dir: Path
) -> None:
    """The tools preview without a request and write with ``confirm``: the recordings."""
    status = replay_fixture("order_update_status", "ok")
    payment = replay_fixture("order_payment_create", "cash_pdf")
    arguments = {"org": DEMO, "ids": [PAID], "status_id": REMINDED}
    preview = await mcp_call(write_server, "cashctrl_update_order_status", arguments)
    assert preview["data"] == preview["data"] | {
        "performed": False,
        "payload": dict(recorded_body(fixtures_dir, "order_update_status", "ok")),
    }
    paying = {"org": DEMO, "date": "2026-10-24", "order_ids": [PAID], "type": "CASH_PDF"}
    planned = await mcp_call(write_server, "cashctrl_create_order_payment", paying)
    assert planned["data"]["payload"] == dict(
        recorded_body(fixtures_dir, "order_payment_create", "cash_pdf")
    )
    assert not respx_mock.calls
    done = await mcp_call(
        write_server, "cashctrl_update_order_status", {**arguments, "confirm": True}
    )
    paid = await mcp_call(
        write_server, "cashctrl_create_order_payment", {**paying, "confirm": True}
    )
    assert (done["data"]["performed"], paid["data"]["performed"]) == (True, True)
    assert (status.call_count, payment.call_count) == (1, 1)
    refused = await mcp_call_text(
        write_server, "cashctrl_create_order_payment", {**paying, "type": "SWIFT"}
    )
    assert refused.startswith("error: InvalidRequestError: type: ")
    assert payment.call_count == 1


@pytest.mark.anyio
async def test_the_payment_tool_lists_the_payment_types() -> None:
    tools = {tool.name: tool for tool in await write_server.list_tools()}
    schema = tools["cashctrl_create_order_payment"].input_schema
    assert schema["required"] == ["org", "date", "order_ids"]
    kinds = schema["properties"]["type"]["anyOf"][0]
    assert kinds == {"enum": ["PAIN", "SEPA_PAIN", "WIRE_PDF", "CASH_PDF"], "type": "string"}
    assert tools["cashctrl_update_order_status"].input_schema["required"] == [
        "org",
        "ids",
        "status_id",
    ]


def test_the_status_and_payment_wrappers_build_upstreams_fields() -> None:
    assert api.order_update_status_fields(ids=[3, 5], status_id=OPEN) == {
        "ids": "3,5",
        "statusId": str(OPEN),
    }
    assert api.order_payment_create_fields(date=PAY_DAY, order_ids=[3]) == {
        "date": "2026-10-24",
        "orderIds": "3",
    }
    assert api.order_payment_create_fields(
        date=PAY_DAY, order_ids=[3, 5], is_combine=True, amount=Decimal("12.5")
    ) == {"date": "2026-10-24", "orderIds": "3,5", "amount": "12.5", "isCombine": "true"}


# The confirm gate --------------------------------------------------------------------

NOT_TRUE: list[Any] = ["false", "no", 1, [0], "true", 1.0]
"""Values a Python caller might pass for ``confirm`` that are not ``True``: each previews."""


@pytest.mark.parametrize("confirm", NOT_TRUE, ids=[repr(value) for value in NOT_TRUE])
def test_a_create_writes_only_when_confirm_is_true(
    respx_mock: respx.MockRouter, confirm: Any
) -> None:
    result = create_the_recorded_journal_entry(confirm=confirm)
    assert isinstance(result.data, WritePreview)
    assert not respx_mock.calls, "no request at all"


@pytest.mark.parametrize("confirm", NOT_TRUE, ids=[repr(value) for value in NOT_TRUE])
def test_an_update_writes_only_when_confirm_is_true(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, confirm: Any
) -> None:
    read = replay_fixture("journal_read", "for_update")
    write = respx_mock.post(f"{BASE}/journal/update.json")
    result = tasks_write.update_journal_entry(DEMO, JOURNAL_ENTRY, title="x", confirm=confirm)
    assert isinstance(result.data, WritePreview)
    assert (read.call_count, write.called) == (1, False), "the read only, never the write"


@pytest.mark.parametrize("confirm", NOT_TRUE, ids=[repr(value) for value in NOT_TRUE])
def test_an_order_update_writes_only_when_confirm_is_true(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, confirm: Any
) -> None:
    read = replay_fixture("order_read", "for_update")
    write = respx_mock.post(f"{BASE}/order/update.json")
    result = tasks_write.update_order(DEMO, ORDER, description="x", confirm=confirm)
    assert isinstance(result.data, WritePreview)
    assert (read.call_count, write.called) == (1, False), "the read only, never the write"


@pytest.mark.parametrize("confirm", NOT_TRUE, ids=[repr(value) for value in NOT_TRUE])
def test_a_status_or_a_payment_writes_only_when_confirm_is_true(
    respx_mock: respx.MockRouter, confirm: Any
) -> None:
    status = tasks_write.update_order_status(DEMO, [ORDER], OPEN, confirm=confirm)
    payment = tasks_write.create_order_payment(DEMO, PAY_DAY, [ORDER], confirm=confirm)
    assert isinstance(status.data, WritePreview)
    assert isinstance(payment.data, WritePreview)
    assert not respx_mock.calls, "no request at all"


@pytest.mark.parametrize("confirm", NOT_TRUE, ids=[repr(value) for value in NOT_TRUE])
def test_a_delete_writes_only_when_confirm_is_true(
    replay_fixture: ReplayFixture, respx_mock: respx.MockRouter, confirm: Any
) -> None:
    replay_fixture("person_read", "for_update")
    write = respx_mock.post(f"{BASE}/person/delete.json")
    result = tasks_write.delete_person(DEMO, PERSON, confirm=confirm)
    assert isinstance(result.data, WritePreview)
    assert not write.called


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("sent", "performed"),
    [
        ("false", False),
        ("no", False),
        ("0", False),
        (0, False),
        ("true", True),
        ("yes", True),
        (1, True),
    ],
)
async def test_the_tool_schema_reads_confirm_as_a_boolean(
    respx_mock: respx.MockRouter, sent: Any, performed: bool
) -> None:
    """Over MCP the schema converts confirm (pydantic's lax bool) before the task runs.

    ``"true"``, ``"yes"``, ``"1"`` and ``1`` become ``True``; ``"false"``, ``"no"``,
    ``"0"`` and ``0`` become ``False``; anything else is refused by the schema.
    """
    read = json.loads(load_fixture(_FIXTURES / "person_read" / "for_update.json").response.body)
    respx_mock.get(f"{BASE}/person/read.json").respond(200, json=read)
    write = respx_mock.post(f"{BASE}/person/delete.json").respond(
        200, json={"success": True, "message": "1 person deleted"}
    )
    arguments = {"org": DEMO, "id": PERSON, "confirm": sent}
    payload = await mcp_call(write_server, "cashctrl_delete_person", arguments)
    assert payload["data"]["performed"] is performed
    assert write.called is performed
    with pytest.raises(AssertionError, match="bool"):
        await mcp_call(write_server, "cashctrl_delete_person", {**arguments, "confirm": [0]})


# Python callers' arguments -----------------------------------------------------------


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: tasks_write.create_journal_entry(DEMO, notify_type="SOMETIMES"),  # type: ignore[arg-type]
            "notify_type must be one of NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL",
        ),
        (
            lambda: tasks_write.create_journal_entry(DEMO, items=[{"debit": 1}]),  # type: ignore[list-item]
            "items[0].account_id: Field required",
        ),
        (
            lambda: tasks_write.create_journal_entry(DEMO, items={"accountId": 1}),  # type: ignore[arg-type]
            "items takes a list, not dict",
        ),
        (
            lambda: tasks_write.create_person(
                DEMO,
                contacts=[{"type": "PIGEON", "address": "x"}],  # type: ignore[list-item]
            ),
            "contacts[0].type: Input should be",
        ),
        (
            lambda: tasks_write.create_person(DEMO, language="de"),  # type: ignore[arg-type]
            "language must be one of",
        ),
        (lambda: tasks_write.update_person(DEMO, 0), "id must be a whole number of at least 1"),
        (lambda: tasks_write.delete_order(DEMO, True), "id must be a whole number of at least 1"),
        (
            lambda: tasks_write.create_order(
                DEMO,
                associate_id=7,
                category_id=4,
                date=DAY,
                items=[{"name": "x"}],  # type: ignore[list-item]
            ),
            "items[0].account_id: Field required",
        ),
        (
            lambda: tasks_write.create_journal_entry(DEMO, custom={"customField0": "x"}),
            "'customField0' is not a custom field name",
        ),
    ],
)
def test_arguments_are_refused_before_any_request(
    respx_mock: respx.MockRouter, call: Callable[[], Any], message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        call()
    assert not respx_mock.calls


def test_an_input_model_refuses_an_unknown_key() -> None:
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        JournalItemInput.model_validate({"account_id": 3, "debitt": 1})


# The form encoding -------------------------------------------------------------------


def test_form_values_are_encoded_as_upstream_reads_them() -> None:
    assert form_value(True) == "true"
    assert form_value(False) == "false"
    assert form_value(Decimal("125.50")) == "125.50"
    assert form_value(Decimal("1E+2")) == "100", "plain digits, never an exponent"
    assert form_value(42) == "42"
    assert form_value(0.1) == "0.1"
    assert form_value(date(2020, 1, 15)) == "2020-01-15"
    assert form_value("Zürich & Co") == "Zürich & Co"
    assert form_value("") == "", "an empty text is sent: it empties a field"
    assert form_value(None) is None
    assert form_value([]) is None, "an empty list is not sent"


def test_lists_are_compact_json_under_upstreams_keys() -> None:
    item = OrderItemInput(account_id=42, name="Stuhl", unit_price=Decimal("172.32"), quantity=6)
    assert json_text([item]) == (
        '[{"accountId":42,"name":"Stuhl","unitPrice":172.32,"quantity":6}]'
    ), "None fields left out, whole numbers as integers, others as floats"
    assert json_text([{"dateEntry": date(2020, 1, 15), "notes": None}]) == (
        '[{"dateEntry":"2020-01-15"}]'
    )
    assert json_text({"F": True, "2.3a": "Bonus"}) == '{"F":true,"2.3a":"Bonus"}'


def test_a_number_a_json_float_cannot_carry_is_refused() -> None:
    with pytest.raises(InvalidRequestError, match="more digits than a JSON number carries"):
        json_text([{"debit": Decimal("0.1000000000000000000001")}])


def test_form_fields_leave_out_what_is_not_set() -> None:
    assert form_fields({"a": None, "b": True, "c": [], "d": "x", "e": 0}) == {
        "b": "true",
        "d": "x",
        "e": "0",
    }


def test_custom_fields_are_upstreams_xml_with_values_escaped() -> None:
    assert custom_xml({"customField1": "Blau & <Grün>", "customField12": '["a","b"]'}) == (
        "<values><customField1>Blau &amp; &lt;Grün&gt;</customField1>"
        '<customField12>["a","b"]</customField12></values>'
    )


@pytest.mark.parametrize(
    ("custom", "message"),
    [
        ({"customfield1": "x"}, "'customfield1' is not a custom field name"),
        ({"customField": "x"}, "'customField' is not a custom field name"),
        ({"customField01": "x"}, "'customField01' is not a custom field name"),
        ({"$myField": "x"}, "'$myField' is not a custom field name"),
        ({"customField1><x": "x"}, "is not a custom field name"),
        ({"customField1": 3}, "the value of 'customField1' must be text, not int"),
        ({"customField1": "a\x00b"}, "holds a control character XML cannot carry"),
    ],
)
def test_custom_field_names_and_values_are_checked(custom: Any, message: str) -> None:
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        custom_xml(custom)


def test_merging_custom_fields_keeps_what_is_not_changed() -> None:
    stored = "<values><customField1>A</customField1><customField2>B</customField2></values>"
    assert merge_custom(stored, {}) == stored
    assert merge_custom(None, {}) is None
    assert merge_custom(stored, {"customField2": "", "customField3": "C"}) == (
        "<values><customField1>A</customField1><customField2></customField2>"
        "<customField3>C</customField3></values>"
    )
    assert (
        merge_custom(None, {"customField1": "A"})
        == "<values><customField1>A</customField1></values>"
    )


@pytest.mark.parametrize(
    "stored",
    [
        "<values><customField1><b>x</b></customField1></values>",
        "<other><customField1>x</customField1></other>",
        '<!DOCTYPE v [<!ENTITY a "aaaa">]><values><customField1>&a;</customField1></values>',
        "<values><customField1>x</customField1>",
        "plain text",
    ],
    ids=["nested", "other-root", "dtd", "unclosed", "text"],
)
def test_stored_custom_values_that_cannot_be_carried_are_refused(stored: str) -> None:
    with pytest.raises(InvalidRequestError, match="cannot be carried over"):
        merge_custom(stored, {"customField1": "y"})


def test_the_write_wrappers_build_upstreams_fields() -> None:
    assert api.journal_fields(id=5, title="t", items=[]) == {"id": "5", "title": "t"}
    assert api.delete_fields([3, 5]) == {"ids": "3,5"}
    assert api.order_fields(associate_id=7, category_id=4, date=DAY) == {
        "associateId": "7",
        "categoryId": "4",
        "date": "2026-10-24",
    }
    assert api.person_fields(certificate_values={}) == {}, "an empty map is not sent"


# Through the write server ------------------------------------------------------------


@pytest.mark.anyio
async def test_a_preview_through_the_write_server(fixtures_dir: Path) -> None:
    arguments = {
        "org": DEMO,
        "date_added": "2026-10-24",
        "amount": "100.00",
        "debit_id": 3,
        "credit_id": 42,
        "title": "xippios-live fixture",
        "tax_id": 9,
    }
    payload = await mcp_call(write_server, "cashctrl_create_journal_entry", arguments)
    assert payload["data"]["performed"] is False
    assert list(payload["data"]["payload"].items()) == recorded_body(
        fixtures_dir, "journal_create", "ok"
    )
    assert payload["meta"] == payload["meta"] | {"tenant": DEMO, "request": {"org": DEMO}}


@pytest.mark.anyio
async def test_an_order_update_through_the_write_server(
    replay_fixture: ReplayFixture, fixtures_dir: Path
) -> None:
    """The tool previews, then writes with ``confirm``: the recorded update, end to end."""
    replay_fixture("order_read", "for_update")
    update = replay_fixture("order_update", "ok")
    arguments = {
        "org": DEMO,
        "id": ORDER,
        "description": "xippios-live fixture updated",
        "due_days": 30,
    }
    preview = await mcp_call(write_server, "cashctrl_update_order", arguments)
    assert preview["data"]["performed"] is False
    assert list(preview["data"]["payload"].items()) == recorded_body(
        fixtures_dir, "order_update", "ok"
    )
    assert preview["data"]["before"]["items"][0]["name"] == "xippios-live item"
    assert not update.called
    done = await mcp_call(write_server, "cashctrl_update_order", {**arguments, "confirm": True})
    assert (done["data"]["performed"], done["data"]["insert_id"]) == (True, ORDER)
    assert sent_body(update) == recorded_body(fixtures_dir, "order_update", "ok")
    assert done["meta"]["tenant"] == DEMO


@pytest.mark.anyio
async def test_a_refusal_through_the_write_server(
    respx_mock: respx.MockRouter, fixtures_dir: Path, replay_fixture: ReplayFixture
) -> None:
    body = recorded_read(fixtures_dir, "journal_read", "for_update")
    del body["data"]["creditId"]
    serve_read(respx_mock, "journal/read.json", body)
    write = respx_mock.post(f"{BASE}/journal/update.json")
    text = await mcp_call_text(
        write_server,
        "cashctrl_update_journal_entry",
        {"org": DEMO, "id": JOURNAL_ENTRY, "title": "x", "confirm": True},
    )
    assert text.startswith("error: InvalidRequestError: the journal entry gives no creditId")
    assert not write.called
    replay_fixture("journal_create", "rejected")
    rejected = await mcp_call_text(
        write_server,
        "cashctrl_create_journal_entry",
        {"org": DEMO, "credit_id": 42, "amount": "100.00", "confirm": True},
    )
    assert rejected == (
        "error: RequestRejected: CashCtrl rejected the request: "
        "debitId: This field cannot be empty."
    )


@pytest.mark.anyio
async def test_the_write_tool_schemas_show_snake_case_inside_lists() -> None:
    tools = {tool.name: tool for tool in await write_server.list_tools()}
    for name in ("cashctrl_create_order", "cashctrl_update_order"):
        schema = tools[name].input_schema
        item = schema["$defs"]["OrderItemInput"]["properties"]
        assert {"account_id", "unit_price", "tax_id"} <= set(item), name
        assert "accountId" not in item, name
    schema = tools["cashctrl_create_order"].input_schema
    assert schema["properties"]["confirm"] == {
        "default": False,
        "title": "Confirm",
        "type": "boolean",
    }
    custom = tools["cashctrl_create_person"].input_schema["properties"]["custom"]
    assert {"additionalProperties": {"type": "string"}, "type": "object"} in custom["anyOf"]


SNAKE_CASE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")
UPSTREAM_FIELDS = frozenset({"payload", "changes"})
"""Form fields under upstream's names, as ``meta.request``; their keys are not checked."""


def result_keys(node: object) -> set[str]:
    """Every key of a decoded result but those inside ``payload`` and ``changes``."""
    found: set[str] = set()
    if isinstance(node, dict):
        for name, value in node.items():
            found.add(str(name))
            if name not in UPSTREAM_FIELDS:
                found |= result_keys(value)
    elif isinstance(node, list):
        for item in node:
            found |= result_keys(item)
    return found


WRITE_TOOL_CASES: dict[str, tuple[list[tuple[str, str]], dict[str, Any]]] = {
    "preview of an update": (
        [("journal_read", "for_update")],
        {"tool": "cashctrl_update_journal_entry", "id": JOURNAL_ENTRY, "title": "x"},
    ),
    "preview of a person delete": (
        [("person_read", "for_update")],
        {"tool": "cashctrl_delete_person", "id": PERSON},
    ),
    "preview of an order delete": (
        [("order_read", "by_id")],
        {"tool": "cashctrl_delete_order", "id": 3},
    ),
    "preview of an order update": (
        [("order_read", "for_update")],
        {"tool": "cashctrl_update_order", "id": ORDER, "due_days": 30},
    ),
    "a performed status update": (
        [("order_update_status", "ok")],
        {
            "tool": "cashctrl_update_order_status",
            "ids": [PAID],
            "status_id": REMINDED,
            "confirm": True,
        },
    ),
    "a performed payment": (
        [("order_payment_create", "cash_pdf")],
        {
            "tool": "cashctrl_create_order_payment",
            "date": "2026-10-24",
            "order_ids": [PAID],
            "type": "CASH_PDF",
            "confirm": True,
        },
    ),
    "a performed create": (
        [("order_create", "ok")],
        {
            "tool": "cashctrl_create_order",
            "associate_id": 7,
            "category_id": 4,
            "date": "2026-10-24",
            "confirm": True,
        },
    ),
}


@pytest.mark.anyio
@pytest.mark.parametrize(("fixtures", "arguments"), WRITE_TOOL_CASES.values(), ids=WRITE_TOOL_CASES)
async def test_write_tool_results_carry_snake_case_keys(
    replay_fixture: ReplayFixture,
    fixtures: list[tuple[str, str]],
    arguments: dict[str, Any],
) -> None:
    """``before`` is a read record, snake_case like every read result; the form fields in
    ``payload`` and ``changes`` keep upstream's names, as ``meta.request`` does."""
    for endpoint, case in fixtures:
        replay_fixture(endpoint, case)
    call = dict(arguments)
    tool = call.pop("tool")
    payload = await mcp_call(write_server, tool, {"org": DEMO, **call})
    keys = result_keys(payload["data"])
    assert keys, "a result without keys proves nothing"
    assert sorted(key for key in keys if not SNAKE_CASE.fullmatch(key)) == []
    assert payload["meta"]["tenant"] == DEMO


def test_no_write_task_is_a_route() -> None:
    from fastapi.routing import APIRoute

    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert not {f"/cashctrl/{name}" for name in WRITE_TASKS} & paths


def test_a_preview_carries_the_form_fields_only_once(respx_mock: respx.MockRouter) -> None:
    """A preview's ``meta.request`` is ``org``; a performed write's holds the fields."""
    preview = create_the_recorded_journal_entry()
    dumped = preview.model_dump_json()
    assert dumped.count('"title":"xippios-live fixture"') == 1
    respx_mock.post(f"{BASE}/journal/create.json").mock(
        return_value=httpx.Response(200, json={"success": True, "insertId": 1, "message": "ok"})
    )
    performed = create_the_recorded_journal_entry(confirm=True)
    assert performed.model_dump_json().count('"title":"xippios-live fixture"') == 1
