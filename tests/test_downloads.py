"""The file tasks: an order's document and the list exports, tested with synthetic bytes.

G5 (5), (6) and (7) of 2026-10-28. A file cannot be recorded: the recorder refuses an
endpoint without ``.json`` and a body that is not UTF-8 text, so no file wrapper has a
fixture directory. As core's own download tests do, each test mounts a small made-up body
with respx under the content type upstream is assumed to send (``BODIES``) and checks the
request's path and query (``sent_query``), the bytes at ``dest``, the ``Downloaded``
fields and ``meta``. A JSON answer, a refusal sent as HTTP 200, is raised and leaves no
file (queue row 142).
"""

import inspect
import json
import re
import typing
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
import respx
from xippios.core import (
    AuthError,
    Downloaded,
    InvalidRequestError,
    NotFoundError,
    UpstreamError,
    ValidationError,
)
from xippios.core.testing import sent_query, sent_urls

from xippios.cashctrl import api, tasks
from xippios.cashctrl._client import DEMO, SOURCE
from xippios.cashctrl.errors import FieldError, RequestRejected
from xippios.cashctrl.mcp import server
from xippios.cashctrl.mcp_write import server as write_server
from xippios.cashctrl.models import Filter, Person, PersonProjection

BASE = "https://demo.cashctrl.com/api/v1"
"""The placeholder host every offline test replays against (``tests/conftest.py``)."""
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
BODIES: dict[str, tuple[bytes, str]] = {
    "csv": ("﻿Datum;Titel;Betrag\n2025-01-15;Miete;1500.00\n".encode(), "text/csv"),
    "xlsx": (b"PK\x03\x04 synthetic, no workbook", XLSX),
    "pdf": (b"%PDF-1.4\n% synthetic, no document\n%%EOF\n", "application/pdf"),
}
"""A made-up body per format, under the content type upstream is assumed to send."""
JSON_UTF8 = "application/json;charset=utf-8"
"""The content type of every ``.json`` answer recorded since 2026-10-23."""

EXPORTS: dict[str, tuple[Callable[..., typing.Any], Callable[..., typing.Any], str]] = {
    "export_journal_entries": (tasks.export_journal_entries, tasks.list_journal_entries, "journal"),
    "export_accounts": (tasks.export_accounts, tasks.list_accounts, "account"),
    "export_persons": (tasks.export_persons, tasks.list_persons, "person"),
    "export_orders": (tasks.export_orders, tasks.list_orders, "order"),
}
"""Each export, the list task it mirrors and their module."""
FILE_TASKS = frozenset({"download_order_document", *EXPORTS})
NUMBER_1020 = Filter(comparison="eq", field="number", value="1020")


def mount(
    router: respx.MockRouter, endpoint: str, body: bytes, content_type: str | None
) -> respx.Route:
    """Answer ``GET <endpoint>``, any query, with ``body`` under ``content_type``."""
    headers = {} if content_type is None else {"Content-Type": content_type}
    return router.get(f"{BASE}/{endpoint}").respond(200, content=body, headers=headers)


def files(directory: Path) -> list[str]:
    """Every file in ``directory``, a temporary one (``.<name>.*``) included."""
    return sorted(path.name for path in directory.iterdir())


def test_the_file_tasks_are_the_bulk_tasks() -> None:
    assert tasks.BULK_TASKS == FILE_TASKS
    assert set(tasks.__all__) >= tasks.BULK_TASKS


@pytest.mark.anyio
async def test_the_file_tasks_are_no_tools_and_no_routes() -> None:
    """ADR-0019 decision 4: core's adapters skip ``BULK_TASKS``; no tool hands out a path."""
    from fastapi.routing import APIRoute

    from xippios.cashctrl.http import router

    read_tools = {tool.name for tool in await server.list_tools()}
    write_tools = {tool.name for tool in await write_server.list_tools()}
    routes = {route.path for route in router.routes if isinstance(route, APIRoute)}
    for name in FILE_TASKS:
        assert f"{SOURCE}_{name}" not in read_tools | write_tools
        assert f"/{SOURCE}/{name}" not in routes
    assert len(read_tools) == len(tasks.__all__) - len(FILE_TASKS)


FILE_WRAPPERS = {
    name: getattr(api, name)
    for name in api.__all__
    if re.fullmatch(r"[a-z]+_list_(csv|xlsx|pdf)|order_document_read_pdf", name)
}


@pytest.mark.parametrize("wrapper", FILE_WRAPPERS.values(), ids=FILE_WRAPPERS.keys())
def test_a_file_wrapper_is_named_after_its_path(wrapper: Callable[..., typing.Any]) -> None:
    """Conventions §2 (D95): the suffix last; the verbatim path first in the docstring."""
    module = inspect.getmodule(wrapper)
    assert module is not None
    match = re.match(r"``GET /api/v1/(\S+)``", module.__doc__ or "")
    assert match, "the verbatim path opens the module's docstring"
    path = match.group(1)
    assert wrapper.__name__ == path.replace("/", "_").replace(".", "_")
    assert module.__name__.rsplit(".", 1)[-1] == wrapper.__name__
    assert f'endpoint="{path}"' in inspect.getsource(wrapper)


def test_there_is_a_wrapper_for_every_format_of_every_export() -> None:
    expected = {f"{module}_list_{ext}" for *_, module in EXPORTS.values() for ext in BODIES}
    assert set(FILE_WRAPPERS) == expected | {"order_document_read_pdf"}


# The order document (G5 (5) of 2026-10-28; Johannes, 2026-10-28: ids, one PDF a call).


def test_download_order_document_writes_the_pdf_where_the_caller_says(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    body, content_type = BODIES["pdf"]
    route = respx_mock.get(f"{BASE}/order/document/read.pdf").respond(
        200,
        content=body,
        headers={
            "Content-Type": content_type,
            "Content-Disposition": 'attachment; filename="RE-2026-103.pdf"',
        },
    )
    dest = tmp_path / "invoice.pdf"
    result = tasks.download_order_document(DEMO, [3], dest)
    assert sent_query(route) == {"ids": "3"}
    assert httpx.URL(sent_urls(route)[-1]).path == "/api/v1/order/document/read.pdf"
    assert dest.read_bytes() == body
    assert result.data == Downloaded(
        path=dest,
        bytes=len(body),
        content_type="application/pdf",
        filename="RE-2026-103.pdf",
        etag=None,
        last_modified=None,
        retrieved_at=result.data.retrieved_at,
    )
    assert result.meta.endpoint == "order/document/read.pdf"
    assert result.meta.request == {"org": DEMO, "ids": "3"}
    assert (result.meta.tenant, result.meta.total) == (DEMO, None)
    assert result.meta.retrieved_at == result.data.retrieved_at, "when the file was complete"
    assert files(tmp_path) == ["invoice.pdf"], "no temporary file left"


def test_several_ids_are_one_pdf_sent_comma_separated(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    route = mount(respx_mock, "order/document/read.pdf", *BODIES["pdf"])
    result = tasks.download_order_document(DEMO, [3, 5, 4], str(tmp_path / "three.pdf"))
    assert sent_query(route) == {"ids": "3,5,4"}, "upstream's CSV, in the order given"
    assert result.meta.request == {"org": DEMO, "ids": "3,5,4"}
    assert result.data.path == tmp_path / "three.pdf"


@pytest.mark.parametrize(
    ("ids", "message"),
    [
        ([], "ids takes a list of at least one order id such as [3], not []"),
        ("3", "ids takes a list of at least one order id such as [3], not '3'"),
        (3, "ids takes a list of at least one order id such as [3], not 3"),
        ([3, "5"], "ids must be whole numbers, the orders' ids, not '5'"),
        ([True], "ids must be whole numbers, the orders' ids, not True"),
    ],
)
def test_download_order_document_refuses_ids_before_anything_is_sent(
    respx_mock: respx.MockRouter, tmp_path: Path, ids: object, message: str
) -> None:
    arguments: dict[str, typing.Any] = {"ids": ids}
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks.download_order_document(DEMO, dest=tmp_path / "x.pdf", **arguments)
    assert not respx_mock.calls
    assert files(tmp_path) == []


# The list exports (G5 (6) of 2026-10-28).


@pytest.mark.parametrize("format", BODIES)
@pytest.mark.parametrize(("name", "case"), EXPORTS.items(), ids=EXPORTS.keys())
def test_an_export_streams_upstreams_file_to_dest(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    name: str,
    case: tuple[Callable[..., typing.Any], Callable[..., typing.Any], str],
    format: str,
) -> None:
    export, _, module = case
    body, content_type = BODIES[format]
    route = mount(respx_mock, f"{module}/list.{format}", body, content_type)
    dest = tmp_path / f"{module}.{format}"
    result = export(DEMO, format, dest)
    assert httpx.URL(sent_urls(route)[-1]).path == f"/api/v1/{module}/list.{format}"
    person_columns = {"columns": ",".join(tasks.PERSON_COLUMNS)}
    assert sent_query(route) == (person_columns if name == "export_persons" else {})
    assert dest.read_bytes() == body
    assert isinstance(result.data, Downloaded)
    assert (result.data.path, result.data.bytes) == (dest, len(body))
    assert result.data.content_type == content_type
    assert result.meta.endpoint == f"{module}/list.{format}"
    assert result.meta.request == {"org": DEMO, **sent_query(route)}
    assert (result.meta.tenant, result.meta.total) == (DEMO, None)
    assert result.meta.retrieved_at == result.data.retrieved_at
    assert files(tmp_path) == [dest.name], "no temporary file left"


EVERY_FILTER: dict[str, dict[str, typing.Any]] = {
    "export_journal_entries": {
        "fiscal_period_id": 2,
        "account_id": 3,
        "associate_id": 8,
        "query": "Miete",
        "filter": [Filter(comparison="eq", field="reference", value="RE-2025-003")],
        **{
            f"only_{flag}": True
            for flag in [
                "collective",
                "cost_centers",
                "imported",
                "manual",
                "notes",
                "purchase",
                "salary",
                "sales",
                "untaxed",
            ]
        },
        "sort": "title",
        "dir": "ASC",
        "start": 20,
        "limit": 500,
    },
    "export_accounts": {
        "query": "Finanz",
        "filter": [NUMBER_1020],
        "category_id": 1,
        "fiscal_period_id": 2,
        "only_active": True,
        "only_cost_centers": True,
        "only_notes": True,
        "sort": "name",
        "dir": "DESC",
    },
    "export_persons": {
        "query": "Muster",
        "filter": [Filter(comparison="eq", field="city", value="Basel")],
        "category_id": 1,
        **{
            f"only_{flag}": True
            for flag in [
                "active",
                "customers",
                "vendors",
                "employees",
                "insurances",
                "families",
                "notes",
                "with_images",
                "without_category",
                "without_role",
            ]
        },
        "sort": "nr",
        "dir": "DESC",
        "start": 20,
        "limit": 500,
    },
    "export_orders": {
        "type": "SALES",
        "fiscal_period_id": 1,
        "query": "Büromöbel",
        "filter": [Filter(comparison="eq", field="nr", value="RE-2026-101")],
        "category_id": 4,
        "status_id": 12,
        "person_id": 10,
        "group_id": 3,
        "only_open": True,
        "only_overdue": True,
        "only_cost_centers": True,
        "only_notes": True,
        "sort": "nr",
        "dir": "ASC",
        "start": 20,
        "limit": 500,
    },
}
"""Every filter each export takes, given: the parameters its list takes, ``columns`` aside."""


@pytest.mark.parametrize(("name", "case"), EXPORTS.items(), ids=EXPORTS.keys())
def test_an_export_takes_its_lists_parameters_and_columns(
    name: str, case: tuple[Callable[..., typing.Any], Callable[..., typing.Any], str]
) -> None:
    """The snapshot documents each export as its ``list.json`` plus ``columns``."""
    export, listing, _ = case
    exported = set(inspect.signature(export).parameters) - {"format", "dest", "columns"}
    assert exported == set(inspect.signature(listing).parameters)
    assert set(EVERY_FILTER[name]) == exported - {"org"}


@pytest.mark.parametrize(("name", "case"), EXPORTS.items(), ids=EXPORTS.keys())
def test_an_export_sends_every_filter_as_its_list_does(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    name: str,
    case: tuple[Callable[..., typing.Any], Callable[..., typing.Any], str],
) -> None:
    export, listing, module = case
    arguments = EVERY_FILTER[name]
    listed = respx_mock.get(f"{BASE}/{module}/list.json").respond(
        200, json={"total": 0, "data": []}
    )
    listing(DEMO, **arguments)
    exported = mount(respx_mock, f"{module}/list.xlsx", *BODIES["xlsx"])
    result = export(DEMO, "xlsx", tmp_path / "all.xlsx", columns=["nr", "name"], **arguments)
    assert sent_query(exported) == {**sent_query(listed), "columns": "nr,name"}
    assert len(sent_query(exported)) == len(arguments) + 1, "every filter sent"
    assert result.meta.request["columns"] == "nr,name"


@pytest.mark.parametrize("name", ["export_journal_entries", "export_persons", "export_orders"])
def test_limit_is_passed_through_and_upstreams_default_otherwise(
    respx_mock: respx.MockRouter, tmp_path: Path, name: str
) -> None:
    """No export is cut at 100 by the task: ``limit`` goes as given, or not at all."""
    export, _, module = EXPORTS[name]
    route = mount(respx_mock, f"{module}/list.csv", *BODIES["csv"])
    export(DEMO, "csv", tmp_path / "default.csv")
    assert "limit" not in sent_query(route)
    assert "start" not in sent_query(route)
    result = export(DEMO, "csv", tmp_path / "all.csv", limit=1000)
    assert sent_query(route)["limit"] == "1000"
    assert result.meta.request["limit"] == 1000
    doc = inspect.getdoc(export) or ""
    assert "100 when ``limit`` is left out" in doc
    assert "``meta.total``" in doc


def test_the_account_export_takes_no_limit_as_upstream_documents_none() -> None:
    assert {"start", "limit"}.isdisjoint(inspect.signature(tasks.export_accounts).parameters)


def test_the_person_export_names_the_projections_columns_without_identifiers(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    """Johannes, 2026-10-28: ``PersonProjection``'s fields under upstream's names, sent."""
    route = mount(respx_mock, "person/list.pdf", *BODIES["pdf"])
    tasks.export_persons(DEMO, "pdf", tmp_path / "persons.pdf")
    columns = sent_query(route)["columns"].split(",")
    assert columns == list(tasks.PERSON_COLUMNS)
    assert len(columns) == len(PersonProjection.model_fields) == len(set(columns))
    assert {"firstName", "lastName", "emailWork", "isCustomer"} <= set(columns)
    assert not {name.lower() for name in columns} & {"ssn", "iban", "qriban"}
    assert set(Person.model_fields) - set(PersonProjection.model_fields) == {"ssn", "iban"}


def test_a_caller_who_names_the_identifiers_gets_them(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    """ADR-0017: a task that fetches them deliberately may, and its docstring says so."""
    route = mount(respx_mock, "person/list.csv", *BODIES["csv"])
    tasks.export_persons(DEMO, "csv", tmp_path / "bank.csv", columns=["nr", "ssn", "iban"])
    assert sent_query(route)["columns"] == "nr,ssn,iban"
    doc = " ".join((inspect.getdoc(tasks.export_persons) or "").split())
    assert "fetches them deliberately and gets them in the file (ADR-0017)" in doc


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"format": "xls"}, "format must be csv or xlsx or pdf, not 'xls'"),
        ({"format": "CSV"}, "format must be csv or xlsx or pdf, not 'CSV'"),
        ({"dir": "up"}, "dir must be ASC or DESC, not 'up'"),
        ({"filter": [{"comparison": "equals", "field": "nr", "value": "1"}]}, "not 'equals'"),
        ({"columns": "nr,name"}, 'columns takes a list of column names such as ["nr", "name"]'),
        ({"columns": []}, "columns names at least one column"),
        ({"columns": ["nr", "name,city"]}, "columns[1] must be a column name without a comma"),
        ({"columns": [" "]}, "columns[0] must be a column name without a comma, not ' '"),
        ({"columns": [7]}, "columns[0] must be a column name without a comma, not 7"),
        ({"start": -1}, "start must be a whole number of at least 0, not -1"),
        ({"limit": 0}, "limit must be a whole number of at least 1, not 0"),
        ({"type": "sales"}, "type must be SALES or PURCHASE, not 'sales'"),
    ],
)
def test_an_export_refuses_what_upstream_would_ignore(
    respx_mock: respx.MockRouter, tmp_path: Path, arguments: dict[str, typing.Any], message: str
) -> None:
    call: dict[str, typing.Any] = {"format": "csv", **arguments}
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        tasks.export_orders(DEMO, dest=tmp_path / "x.csv", **call)
    assert not respx_mock.calls
    assert files(tmp_path) == []


@pytest.mark.parametrize("name", EXPORTS)
def test_every_export_checks_format_and_columns(
    respx_mock: respx.MockRouter, tmp_path: Path, name: str
) -> None:
    export = EXPORTS[name][0]
    arguments: dict[str, typing.Any] = {"format": "docx", "columns": []}
    with pytest.raises(InvalidRequestError) as info:
        export(DEMO, dest=tmp_path / "x", **arguments)
    assert "format must be csv or xlsx or pdf, not 'docx'" in str(info.value)
    assert "columns names at least one column" in str(info.value)
    assert not respx_mock.calls


# A refusal sent as HTTP 200 (queue row 142): core writes a 2xx body unread, so the file
# task reads the answer's content type before the file becomes dest.


def test_an_unknown_order_is_not_found_and_nothing_is_written(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    """The ``read.json`` refusal's shape, assumed for ``read.pdf`` (not observed)."""
    refusal = {"success": False, "errorMessage": "This order does not exist.", "data": None}
    body = json.dumps(refusal).encode()
    mount(respx_mock, "order/document/read.pdf", body, JSON_UTF8)
    dest = tmp_path / "invoice.pdf"
    dest.write_bytes(b"the caller's earlier file")
    with pytest.raises(NotFoundError) as info:
        tasks.download_order_document(DEMO, [999999], dest)
    assert str(info.value) == "CashCtrl: This order does not exist. (/order/document/read.pdf)"
    assert dest.read_bytes() == b"the caller's earlier file", "dest is left as it was"
    assert files(tmp_path) == ["invoice.pdf"], "the refusal is removed"


def test_an_unknown_orders_404_is_not_found_and_dest_stays(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    """Observed on 2026-10-29: upstream answers an id no order has with HTTP 404."""
    respx_mock.get(f"{BASE}/order/document/read.pdf").respond(
        404, text="<title>CashCtrl - 404 Not Found</title>"
    )
    dest = tmp_path / "invoice.pdf"
    dest.write_bytes(b"the caller's earlier file")
    with pytest.raises(NotFoundError) as info:
        tasks.download_order_document(DEMO, [999999], dest)
    assert str(info.value).endswith("(/order/document/read.pdf)")
    assert dest.read_bytes() == b"the caller's earlier file"
    assert files(tmp_path) == ["invoice.pdf"]


@pytest.mark.parametrize(
    "content_type", [JSON_UTF8, "application/json", "Application/JSON ; charset=UTF-8"]
)
def test_an_exports_refusal_is_raised_and_removed(
    respx_mock: respx.MockRouter, tmp_path: Path, content_type: str
) -> None:
    refusal = {"success": False, "errors": [{"field": "columns", "message": "Invalid."}]}
    mount(respx_mock, "journal/list.csv", json.dumps(refusal).encode(), content_type)
    with pytest.raises(RequestRejected) as info:
        tasks.export_journal_entries(DEMO, "csv", tmp_path / "journal.csv", columns=["x"])
    assert info.value.errors == [FieldError(field="columns", message="Invalid.")]
    assert files(tmp_path) == []


def test_a_refusal_with_a_message_on_an_export_is_no_absence(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    """An export reads no record by id: a refusal with a message is ``RequestRejected``."""
    body = b'{"success":false,"errorMessage":"Not allowed.","data":null}'
    mount(respx_mock, "person/list.xlsx", body, JSON_UTF8)
    with pytest.raises(RequestRejected) as info:
        tasks.export_persons(DEMO, "xlsx", tmp_path / "persons.xlsx")
    assert info.value.upstream_message == "Not allowed."
    assert files(tmp_path) == []


@pytest.mark.parametrize(
    "body", [b'{"success":true,"data":[]}', b'{"success":false', b"[" + b"1," * 9000 + b"1]"]
)
def test_json_that_is_no_refusal_is_raised_too(
    respx_mock: respx.MockRouter, tmp_path: Path, body: bytes
) -> None:
    """Whatever JSON stands in for a file, it is never kept as one."""
    mount(respx_mock, "account/list.pdf", body, JSON_UTF8)
    with pytest.raises(ValidationError, match="neither a file nor a refusal"):
        tasks.export_accounts(DEMO, "pdf", tmp_path / "accounts.pdf")
    assert files(tmp_path) == []


@pytest.mark.parametrize(
    "content_type", ["text/csv", "text/plain", "application/octet-stream", "text/html", None]
)
def test_any_other_content_type_is_kept_as_the_file(
    respx_mock: respx.MockRouter, tmp_path: Path, content_type: str | None
) -> None:
    """The content type decides (row 142's rule): even a refusal's text under another type."""
    body = b'{"success":false}'
    mount(respx_mock, "order/list.csv", body, content_type)
    result = tasks.export_orders(DEMO, "csv", tmp_path / "orders.csv")
    assert (tmp_path / "orders.csv").read_bytes() == body
    assert result.data.content_type == content_type


@pytest.mark.parametrize(("status", "error"), [(401, AuthError), (404, UpstreamError)])
def test_a_status_error_writes_nothing(
    respx_mock: respx.MockRouter, tmp_path: Path, status: int, error: type[Exception]
) -> None:
    """``classify`` maps the status as for a read: a 404 is an unknown endpoint."""
    route = respx_mock.get(f"{BASE}/journal/list.pdf").respond(status, text="no")
    with pytest.raises(error):
        tasks.export_journal_entries(DEMO, "pdf", tmp_path / "journal.pdf")
    assert route.call_count == 1
    assert files(tmp_path) == []


def test_dest_names_a_file_in_a_directory_that_exists(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    with pytest.raises(InvalidRequestError, match="dest is a directory"):
        tasks.export_accounts(DEMO, "csv", tmp_path)
    with pytest.raises(InvalidRequestError, match="dest's directory does not exist"):
        tasks.download_order_document(DEMO, [3], tmp_path / "missing" / "x.pdf")
    assert not respx_mock.calls
    assert files(tmp_path) == []


@pytest.mark.anyio
async def test_the_async_twins_are_the_tasks(respx_mock: respx.MockRouter, tmp_path: Path) -> None:
    route = mount(respx_mock, "order/list.pdf", *BODIES["pdf"])
    result = await tasks.export_orders_async(DEMO, "pdf", tmp_path / "o.pdf", type="PURCHASE")
    assert sent_query(route) == {"type": "PURCHASE"}
    assert result.data.bytes == len(BODIES["pdf"][0])
