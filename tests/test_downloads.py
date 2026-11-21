"""The file tasks: an order's document, the list exports and the reports, on synthetic bytes.

G5 (5), (6) and (7) of 2026-10-28, and the reports' PDF and Excel files of
https://github.com/xippios/sdk-cashctrl/issues/45, each refused by type on the recorded
report tree before its download. A file cannot be recorded: the recorder refuses an
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
from collections.abc import Callable, Iterator, Mapping
from datetime import date
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
from xippios.core.testing import (
    ReplayFixture,
    fixture_path,
    load_fixture,
    sent_query,
    sent_urls,
)

from xippios.cashctrl import api, tasks
from xippios.cashctrl._client import DEMO, SOURCE
from xippios.cashctrl.errors import FieldError, RequestRejected
from xippios.cashctrl.mcp import server
from xippios.cashctrl.mcp_write import server as write_server
from xippios.cashctrl.models import Filter, Person, PersonProjection, ReportFormat

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
REPORT_TASKS = ("download_report", "download_report_collection", "download_annual_report")
"""The report module's file tasks (https://github.com/xippios/sdk-cashctrl/issues/45)."""
FILE_TASKS = frozenset({"download_order_document", *EXPORTS, *REPORT_TASKS})
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
    """Core's adapters skip ``BULK_TASKS``: no tool hands out a path.

    A file task is Python only (sdk-core ADR-0040, decision 4).
    """
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
    if re.fullmatch(
        r"[a-z]+_list_(csv|xlsx|pdf)|order_document_read_pdf|report_[a-z]+_download_[a-z_]+",
        name,
    )
}
REPORT_WRAPPERS = {
    "report_element_download_pdf",
    "report_element_download_xlsx",
    "report_collection_download_pdf",
    "report_collection_download_xlsx",
    "report_collection_download_annualreport",
}
"""The PDF and Excel files of ``docs/upstream/report.md``, the annual report's among them."""

DOCUMENTED_PATHS = frozenset(
    re.findall(
        r"(?:GET|POST) /api/v1/(\S+?)(?=[\s`]|$)",
        "".join(
            page.read_text(encoding="utf-8")
            for page in sorted((Path(__file__).parent.parent / "docs" / "upstream").glob("*.md"))
        ),
    )
)
"""Every path the snapshot documents, each with its file suffix."""


@pytest.mark.parametrize("wrapper", FILE_WRAPPERS.values(), ids=FILE_WRAPPERS.keys())
def test_a_file_wrapper_is_named_after_its_path(wrapper: Callable[..., typing.Any]) -> None:
    """Conventions §2: the suffix last, and only where it tells operations on one path apart.

    ``order/document/read.pdf`` keeps ``_pdf`` beside ``read.json`` and ``read.zip``;
    ``report/collection/download_annualreport.pdf``, the one format of its path, drops it.
    The verbatim path opens the module's docstring.
    """
    module = inspect.getmodule(wrapper)
    assert module is not None
    match = re.match(r"``GET /api/v1/(\S+)``", module.__doc__ or "")
    assert match, "the verbatim path opens the module's docstring"
    path = match.group(1)
    stem = path.rpartition(".")[0]
    formats = {other for other in DOCUMENTED_PATHS if other.rpartition(".")[0] == stem}
    assert path in formats, "the path is one the snapshot documents"
    named = path if len(formats) > 1 else stem
    assert wrapper.__name__ == named.replace("/", "_").replace(".", "_")
    assert module.__name__.rsplit(".", 1)[-1] == wrapper.__name__
    assert f'endpoint="{path}"' in inspect.getsource(wrapper)


def test_there_is_a_wrapper_for_every_format_of_every_export() -> None:
    expected = {f"{module}_list_{ext}" for *_, module in EXPORTS.values() for ext in BODIES}
    assert set(FILE_WRAPPERS) == expected | {"order_document_read_pdf"} | REPORT_WRAPPERS


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
    """sdk-core ADR-0017: a task that fetches them deliberately may, and its docstring says so."""
    route = mount(respx_mock, "person/list.csv", *BODIES["csv"])
    tasks.export_persons(DEMO, "csv", tmp_path / "bank.csv", columns=["nr", "ssn", "iban"])
    assert sent_query(route)["columns"] == "nr,ssn,iban"
    doc = " ".join((inspect.getdoc(tasks.export_persons) or "").split())
    assert "fetches them deliberately and gets them in the file (sdk-core ADR-0017)" in doc


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
    replay_fixture: ReplayFixture, tmp_path: Path
) -> None:
    """The recorded 404 of an id no order has (docs/upstream/OBSERVED.md), replayed."""
    route = replay_fixture("order_document_read", "unknown_id_pdf", match_params=["ids"])
    dest = tmp_path / "invoice.pdf"
    dest.write_bytes(b"the caller's earlier file")
    with pytest.raises(NotFoundError) as info:
        tasks.download_order_document(DEMO, [999999999], dest)
    assert route.call_count == 1
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


# The report files (https://github.com/xippios/sdk-cashctrl/issues/45): an element's or a
# collection's PDF or Excel file and the annual report's PDF, each refused by the type rule
# of get_report_data on the tree upstream lists right before the download.

FP2025 = 2
"""The demo organisation's fiscal period 2025."""
REPORT_MEDIA = {"pdf": "application/pdf;charset=UTF-8", "xlsx": f"{XLSX};charset=UTF-8"}
"""The content types upstream sent for a report's PDF and Excel file (observed 2026-11-17)."""
TREE = f"{BASE}/report/tree.json"
RULE = (
    "payroll and people reports, every type that starts with SALARY_ or contains PERSON, "
    "and SETTLEMENT, WITHHOLDING_TAX_SETTLEMENT, PEOPLE and ORG_CHART "
    "(personal data, sdk-core ADR-0017)"
)
PAYROLL_TYPES = (
    "SALARY_BOOK_ENTRIES, SALARY_LIST, SALARY_TYPES, SALARY_TYPE_RECAP, SETTLEMENT, "
    "WITHHOLDING_TAX_SETTLEMENT"
)
"""The refused types of the recorded tree's collection 8, ``Lohnbericht``, sorted."""


def tree_nodes(nodes: list[dict[str, typing.Any]]) -> Iterator[dict[str, typing.Any]]:
    """Every node of a tree body, depth first."""
    for node in nodes:
        yield node
        yield from tree_nodes(node.get("data") or [])


def tree_body(
    fixtures_dir: Path, changes: Mapping[str, Mapping[str, typing.Any]] | None = None
) -> dict[str, typing.Any]:
    """``report_tree/default``'s body, the nodes ``changes`` names by tree key changed.

    Recorded on 2026-10-27: collection 1, ``Jahresbericht``, the one marked system, holds
    the balance sheet (element 1) and the profit and loss (2); collection 3 the revenue
    and expense by person; collection 8, ``Lohnbericht``, the payroll reports.
    """
    fixture = load_fixture(fixture_path(fixtures_dir, "report_tree", "default"))
    body: dict[str, typing.Any] = json.loads(fixture.response.body)
    for node in tree_nodes(body["data"]):
        node.update((changes or {}).get(node["id"], {}))
    return body


def mount_tree(
    router: respx.MockRouter,
    fixtures_dir: Path,
    changes: Mapping[str, Mapping[str, typing.Any]] | None = None,
) -> respx.Route:
    """Answer ``report/tree.json`` with the recorded tree, as ``tree_body`` changes it."""
    return router.get(TREE).respond(200, json=tree_body(fixtures_dir, changes))


def mount_report(
    router: respx.MockRouter, endpoint: str, format: str, filename: str | None = None
) -> respx.Route:
    """Answer ``GET <endpoint>`` with ``format``'s synthetic body under upstream's type."""
    headers = {"Content-Type": REPORT_MEDIA[format]}
    if filename is not None:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return router.get(f"{BASE}/{endpoint}").respond(200, content=BODIES[format][0], headers=headers)


def test_the_report_files_are_pdf_and_excel() -> None:
    assert tasks.REPORT_FORMATS == ("pdf", "xlsx")


@pytest.mark.parametrize("format", ["pdf", "xlsx"])
def test_download_report_writes_the_file_where_the_caller_says(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path, format: ReportFormat
) -> None:
    tree = mount_tree(respx_mock, fixtures_dir)
    endpoint = f"report/element/download.{format}"
    route = mount_report(respx_mock, endpoint, format, f"Balance 2025.{format}")
    dest = tmp_path / f"balance.{format}"
    result = tasks.download_report(DEMO, 1, format, dest, fiscal_period=FP2025)
    assert (tree.call_count, route.call_count) == (1, 1), "the tree first, then the file"
    assert sent_query(route) == {"elementId": "1", "fiscalPeriod": str(FP2025)}
    assert dest.read_bytes() == BODIES[format][0]
    assert result.data.path == dest
    assert result.data.bytes == len(BODIES[format][0])
    assert result.data.filename == f"Balance 2025.{format}", "upstream's name, not dest's"
    assert result.data.content_type == REPORT_MEDIA[format]
    assert result.meta.endpoint == endpoint
    assert result.meta.request == {"org": DEMO, "elementId": 1, "fiscalPeriod": FP2025}
    assert (result.meta.tenant, result.meta.total) == (DEMO, None)
    assert result.meta.retrieved_at == result.data.retrieved_at
    assert files(tmp_path) == [dest.name], "no temporary file left"


def test_a_report_file_takes_and_sends_the_parameters_of_get_report_data(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    """``download.pdf`` and ``download.xlsx`` document the parameters of ``data.json``."""
    arguments: dict[str, typing.Any] = {
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 6, 30),
        "language": "de",
        "sort": "text",
    }
    mount_tree(respx_mock, fixtures_dir)
    data = respx_mock.get(f"{BASE}/report/element/data.json").respond(
        200, json={"total": 0, "data": []}
    )
    tasks.get_report_data(DEMO, 1, **arguments)
    route = mount_report(respx_mock, "report/element/download.xlsx", "xlsx")
    result = tasks.download_report(DEMO, 1, "xlsx", tmp_path / "half.xlsx", **arguments)
    assert sent_query(route) == sent_query(data)
    assert result.meta.request["startDate"] == "2025-01-01"
    downloaded = set(inspect.signature(tasks.download_report).parameters) - {"format", "dest"}
    assert downloaded == set(inspect.signature(tasks.get_report_data).parameters)
    collection = set(inspect.signature(tasks.download_report_collection).parameters)
    assert collection == downloaded - {"element_id"} | {"collection_id", "format", "dest"}


@pytest.mark.parametrize("format", ["pdf", "xlsx"])
def test_download_report_collection_writes_the_file_where_the_caller_says(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path, format: ReportFormat
) -> None:
    """Collection 1 holds the balance sheet and the profit and loss: both pass."""
    tree = mount_tree(respx_mock, fixtures_dir)
    endpoint = f"report/collection/download.{format}"
    route = mount_report(respx_mock, endpoint, format, f"Annual report 2025.{format}")
    dest = tmp_path / f"annual.{format}"
    result = tasks.download_report_collection(DEMO, 1, format, dest, fiscal_period=FP2025)
    assert (tree.call_count, route.call_count) == (1, 1)
    assert sent_query(route) == {"collectionId": "1", "fiscalPeriod": str(FP2025)}
    assert dest.read_bytes() == BODIES[format][0]
    assert result.data.filename == f"Annual report 2025.{format}"
    assert result.meta.endpoint == endpoint
    assert result.meta.request == {"org": DEMO, "collectionId": 1, "fiscalPeriod": FP2025}
    assert result.meta.retrieved_at == result.data.retrieved_at
    assert files(tmp_path) == [dest.name]


@pytest.mark.parametrize("fiscal_period_id", [FP2025, None])
def test_download_annual_report_writes_the_pdf_where_the_caller_says(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path, fiscal_period_id: int | None
) -> None:
    tree = mount_tree(respx_mock, fixtures_dir)
    endpoint = "report/collection/download_annualreport.pdf"
    route = mount_report(respx_mock, endpoint, "pdf", "Annual report 2025.pdf")
    dest = tmp_path / "annual.pdf"
    result = tasks.download_annual_report(DEMO, dest, fiscal_period_id=fiscal_period_id)
    assert (tree.call_count, route.call_count) == (1, 1)
    sent = {} if fiscal_period_id is None else {"fiscalPeriodId": fiscal_period_id}
    assert sent_query(route) == {name: str(value) for name, value in sent.items()}
    assert dest.read_bytes() == BODIES["pdf"][0]
    assert result.meta.endpoint == endpoint
    assert result.meta.request == {"org": DEMO, **sent}
    assert files(tmp_path) == [dest.name]


@pytest.mark.parametrize(
    ("element_id", "report_type"),
    [
        (24, "SALARY_LIST"),
        (28, "SETTLEMENT"),
        (35, "WITHHOLDING_TAX_SETTLEMENT"),
        (5, "REVENUE_BY_PERSON"),
        (6, "EXPENSE_BY_PERSON_CHART"),
    ],
)
@pytest.mark.parametrize("format", ["pdf", "xlsx"])
def test_a_payroll_or_people_report_is_refused_before_its_download(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    tmp_path: Path,
    element_id: int,
    report_type: str,
    format: ReportFormat,
) -> None:
    tree = mount_tree(respx_mock, fixtures_dir)
    route = mount_report(respx_mock, f"report/element/download.{format}", format)
    with pytest.raises(InvalidRequestError) as refused:
        tasks.download_report(DEMO, element_id, format, tmp_path / "x", fiscal_period=FP2025)
    assert refused.value.message == (
        f"report element {element_id} is of type {report_type}: download_report refuses {RULE}"
    )
    assert (tree.call_count, route.call_count) == (1, 0)
    assert files(tmp_path) == []


def test_the_debtor_report_passes_as_get_report_data_reads_it(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    """``OPEN_DEBTORS`` names business partners as ``list_persons`` does (0.3.0, row 225)."""
    mount_tree(respx_mock, fixtures_dir)
    route = mount_report(respx_mock, "report/element/download.pdf", "pdf")
    tasks.download_report(DEMO, 12, "pdf", tmp_path / "debtors.pdf", fiscal_period=FP2025)
    assert route.call_count == 1


@pytest.mark.parametrize(
    ("collection_id", "types"),
    [
        (8, PAYROLL_TYPES),
        (
            3,
            "EXPENSE_BY_PERSON, EXPENSE_BY_PERSON_CHART, REVENUE_BY_PERSON, "
            "REVENUE_BY_PERSON_CHART",
        ),
    ],
)
def test_a_collection_that_holds_a_refused_report_is_refused_before_its_download(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    tmp_path: Path,
    collection_id: int,
    types: str,
) -> None:
    """Its file holds every report in it, so one refused report refuses the collection."""
    tree = mount_tree(respx_mock, fixtures_dir)
    route = mount_report(respx_mock, "report/collection/download.pdf", "pdf")
    with pytest.raises(InvalidRequestError) as refused:
        tasks.download_report_collection(DEMO, collection_id, "pdf", tmp_path / "x.pdf")
    assert refused.value.message == (
        f"report collection {collection_id} holds reports of the types {types}: "
        f"download_report_collection refuses {RULE}"
    )
    assert (tree.call_count, route.call_count) == (1, 0)
    assert files(tmp_path) == []


def test_every_download_reads_the_tree_as_upstream_lists_it_then(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    """A collection gains a payroll report between two downloads: the second is refused.

    The tree each download reads is the one ``get_report_data`` keeps, so its refusal of
    the changed element needs no request of its own.
    """
    tree = respx_mock.get(TREE).mock(
        side_effect=[
            httpx.Response(200, json=tree_body(fixtures_dir)),
            httpx.Response(
                200, json=tree_body(fixtures_dir, {"element-2": {"type": "SALARY_LIST"}})
            ),
        ]
    )
    route = mount_report(respx_mock, "report/collection/download.pdf", "pdf")
    tasks.download_report_collection(DEMO, 1, "pdf", tmp_path / "first.pdf", fiscal_period=FP2025)
    with pytest.raises(
        InvalidRequestError, match="report collection 1 holds reports of the types SALARY_LIST: "
    ):
        tasks.download_report_collection(
            DEMO, 1, "pdf", tmp_path / "second.pdf", fiscal_period=FP2025
        )
    assert (tree.call_count, route.call_count) == (2, 1)
    with pytest.raises(
        InvalidRequestError, match="report element 2 is of type SALARY_LIST: get_report_data"
    ):
        tasks.get_report_data(DEMO, 2, fiscal_period=FP2025)
    assert tree.call_count == 2
    assert files(tmp_path) == ["first.pdf"]


def test_the_annual_report_is_refused_when_its_collection_holds_a_refused_report(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    """The annual report is the system collection's PDF: the same file (observed 2026-11-17)."""
    tree = mount_tree(respx_mock, fixtures_dir, {"element-2": {"type": "SALARY_LIST"}})
    route = mount_report(respx_mock, "report/collection/download_annualreport.pdf", "pdf")
    with pytest.raises(InvalidRequestError) as refused:
        tasks.download_annual_report(DEMO, tmp_path / "annual.pdf", fiscal_period_id=FP2025)
    assert refused.value.message == (
        "the annual report, report collection 1, holds reports of the types SALARY_LIST: "
        f"download_annual_report refuses {RULE}"
    )
    assert (tree.call_count, route.call_count) == (1, 0)
    assert files(tmp_path) == []


def test_the_annual_report_is_refused_when_no_collection_is_marked_system(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    """Fail closed: without its collection, what the annual report holds cannot be checked."""
    unmarked = {"collection-1": {"system": False, "isSystem": False}}
    tree = mount_tree(respx_mock, fixtures_dir, unmarked)
    route = mount_report(respx_mock, "report/collection/download_annualreport.pdf", "pdf")
    with pytest.raises(InvalidRequestError) as refused:
        tasks.download_annual_report(DEMO, tmp_path / "annual.pdf")
    assert refused.value.message == (
        "the report tree marks no collection as the system collection the annual report "
        f"prints, so its reports cannot be checked: download_annual_report refuses {RULE}"
    )
    assert (tree.call_count, route.call_count) == (1, 0)


@pytest.mark.parametrize(
    ("task", "endpoint", "fmt"),
    [
        ("download_report", "report/element/download.pdf", "pdf"),
        ("download_report", "report/element/download.xlsx", "xlsx"),
        ("download_report_collection", "report/collection/download.pdf", "pdf"),
        ("download_report_collection", "report/collection/download.xlsx", "xlsx"),
    ],
)
def test_a_report_the_tree_does_not_list_is_not_found_and_dest_stays(
    respx_mock: respx.MockRouter,
    fixtures_dir: Path,
    replay_fixture: ReplayFixture,
    tmp_path: Path,
    task: str,
    endpoint: str,
    fmt: ReportFormat,
) -> None:
    """Asked of upstream as given, as by ``get_report_data``: the recorded 404, replayed.

    Recorded for the id alone and served here for the id with a fiscal period, a request
    of the same operation that upstream answers alike (conventions §10).
    """
    tree = mount_tree(respx_mock, fixtures_dir)
    directory = endpoint.rsplit(".", 1)[0].replace("/", "_")
    route = replay_fixture(directory, f"unknown_id_{fmt}")
    dest = tmp_path / f"missing.{fmt}"
    dest.write_bytes(b"the caller's earlier file")
    with pytest.raises(NotFoundError) as info:
        getattr(tasks, task)(DEMO, 999999999, fmt, dest, fiscal_period=FP2025)
    assert str(info.value) == f"CashCtrl: no record has an id asked, HTTP 404 (/{endpoint})"
    assert (tree.call_count, route.call_count) == (1, 1)
    assert dest.read_bytes() == b"the caller's earlier file"
    assert files(tmp_path) == [f"missing.{fmt}"]


def test_a_report_files_refusal_sent_as_http_200_is_raised_and_removed(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    mount_tree(respx_mock, fixtures_dir)
    body = b'{"success":false,"errorMessage":"Not allowed.","data":null}'
    mount(respx_mock, "report/collection/download.xlsx", body, JSON_UTF8)
    with pytest.raises(RequestRejected) as info:
        tasks.download_report_collection(DEMO, 1, "xlsx", tmp_path / "annual.xlsx")
    assert info.value.upstream_message == "Not allowed."
    assert files(tmp_path) == []


@pytest.mark.parametrize(
    ("task", "arguments", "message"),
    [
        ("download_report", {"format": "csv"}, "format must be pdf or xlsx, not 'csv'"),
        ("download_report", {"format": "PDF"}, "format must be pdf or xlsx, not 'PDF'"),
        ("download_report", {"element_id": "1"}, "element_id must be a whole number, not '1'"),
        (
            "download_report",
            {"fiscal_period": FP2025, "start_date": date(2025, 1, 1)},
            "give fiscal_period or start_date and end_date, not both",
        ),
        (
            "download_report",
            {"start_date": "2025-01-01"},
            "start_date must be a date (YYYY-MM-DD), not str",
        ),
        ("download_report", {"sort": 3}, "sort must be a string, not int"),
        (
            "download_report_collection",
            {"collection_id": True},
            "collection_id must be a whole number, not True",
        ),
        ("download_report_collection", {"format": "xls"}, "format must be pdf or xlsx, not 'xls'"),
        (
            "download_annual_report",
            {"fiscal_period_id": "2"},
            "fiscal_period_id must be a whole number, not '2'",
        ),
    ],
)
def test_a_report_file_refuses_its_arguments_before_anything_is_sent(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    task: str,
    arguments: dict[str, typing.Any],
    message: str,
) -> None:
    ids = {
        "download_report": {"element_id": 1, "format": "pdf"},
        "download_report_collection": {"collection_id": 1, "format": "pdf"},
        "download_annual_report": {},
    }[task]
    with pytest.raises(InvalidRequestError, match=re.escape(message)):
        getattr(tasks, task)(DEMO, dest=tmp_path / "x", **{**ids, **arguments})
    assert not respx_mock.calls, "not even the tree"
    assert files(tmp_path) == []


def test_a_report_file_names_every_problem_at_once(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    arguments: dict[str, typing.Any] = {"element_id": 1.5, "format": "docx", "language": 2}
    with pytest.raises(InvalidRequestError) as info:
        tasks.download_report(DEMO, dest=tmp_path / "x", **arguments)
    assert str(info.value).count(";") == 2
    assert "format must be pdf or xlsx, not 'docx'" in str(info.value)
    assert not respx_mock.calls


@pytest.mark.parametrize("task", REPORT_TASKS)
def test_a_report_files_dest_is_checked_before_the_tree_is_read(
    respx_mock: respx.MockRouter, tmp_path: Path, task: str
) -> None:
    ids = {} if task == "download_annual_report" else {"format": "pdf"}
    first = [] if task == "download_annual_report" else [1]
    with pytest.raises(InvalidRequestError, match="dest is a directory"):
        getattr(tasks, task)(DEMO, *first, dest=tmp_path, **ids)
    with pytest.raises(InvalidRequestError, match="dest's directory does not exist"):
        getattr(tasks, task)(DEMO, *first, dest=tmp_path / "missing" / "x.pdf", **ids)
    assert not respx_mock.calls
    assert files(tmp_path) == []


@pytest.mark.parametrize("task", REPORT_TASKS)
def test_a_report_files_docstring_states_the_refusal_and_what_the_file_holds(task: str) -> None:
    doc = " ".join((inspect.getdoc(getattr(tasks, task)) or "").split())
    assert "payroll and people reports" in doc
    assert "no key is dropped from a file" in doc
    assert "(``BULK_TASKS``)" in doc


@pytest.mark.anyio
async def test_the_report_files_async_twins_are_the_tasks(
    respx_mock: respx.MockRouter, fixtures_dir: Path, tmp_path: Path
) -> None:
    mount_tree(respx_mock, fixtures_dir)
    element = mount_report(respx_mock, "report/element/download.pdf", "pdf")
    collection = mount_report(respx_mock, "report/collection/download.xlsx", "xlsx")
    annual = mount_report(respx_mock, "report/collection/download_annualreport.pdf", "pdf")
    await tasks.download_report_async(DEMO, 1, "pdf", tmp_path / "e.pdf")
    await tasks.download_report_collection_async(DEMO, 1, "xlsx", tmp_path / "c.xlsx")
    await tasks.download_annual_report_async(DEMO, tmp_path / "a.pdf", fiscal_period_id=FP2025)
    assert (element.call_count, collection.call_count, annual.call_count) == (1, 1, 1)
    assert sent_query(annual) == {"fiscalPeriodId": str(FP2025)}
