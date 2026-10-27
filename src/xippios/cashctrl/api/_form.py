"""The form bodies of CashCtrl's writes, encoded once, and the one way they are sent.

Upstream "accepts form-encoded request bodies" (``docs/upstream/introduction.md``), and
every create, update and delete operation is a ``POST`` with form fields named as the
parameter tables name them. This module turns task values into those fields and posts
them through core's form bodies (``AsyncClient.request(..., data=...)``, conventions §6):

- ``True``/``False`` become ``true``/``false`` ("Possible values: true, false");
- a ``Decimal`` or an ``int`` becomes its plain digits (``125.50``, never ``1.255E+2``);
- a ``date`` becomes ``YYYY-MM-DD`` ("Format: YYYY-MM-DD");
- a list or a mapping (``items``, ``addresses``, ``contacts``, ``allocations``) becomes
  compact JSON, "a JSON array ``[{...},{...},...]``", whose objects carry upstream's
  camelCase keys: an input model is dumped by its ``serialization_alias``, ``None``
  fields left out, numbers as JSON numbers, dates as ``YYYY-MM-DD``, as in the
  documented curl examples (``docs/upstream/examples.md``);
- ``custom`` is the XML upstream documents for custom field values,
  ``<values><customField1>My value</customField1></values>`` (``custom_xml``);
- ``None`` and an empty list are left out: upstream reads an omitted parameter as an
  empty value ("omitted parameters are treated as empty values", every ``update.json``).

``post_form`` sends the fields with ``Content-Type: application/x-www-form-urlencoded;
charset=UTF-8``, the charset declared as ``scripts/seed_demo.py`` declared it for the
65 writes that seeded the demo organisation, an umlaut read back byte for byte
(``docs/demo-org.md``, Observed write semantics). A refusal (HTTP 200 with
``"success": false``) is raised by ``_client.classify`` as ``RequestRejected``; core
never retries a ``POST`` after a 5xx or a transport failure (ADR-0011).
"""

import json
import re
import xml.etree.ElementTree as ElementTree
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from decimal import Decimal
from typing import Any
from xml.sax.saxutils import escape

from pydantic import BaseModel
from xippios.core import BODY_LIMIT, InvalidRequestError, ValidationError

from xippios.cashctrl._client import SOURCE, client_for

__all__ = [
    "CUSTOM_FIELD",
    "FORM_CONTENT_TYPE",
    "custom_xml",
    "delete_fields",
    "form_fields",
    "form_value",
    "ids_csv",
    "json_text",
    "merge_custom",
    "post_form",
]

FORM_CONTENT_TYPE = "application/x-www-form-urlencoded; charset=UTF-8"
CUSTOM_FIELD = re.compile(r"customField[1-9][0-9]*")
"""A custom field's name as upstream names it: ``customField`` and its id (``customField1``).

``docs/upstream/common.md``: "the default $customField<ID> variable name"; the parameter
tables show ``<customField1>`` inside ``<values>``.
"""
_XML_TEXT = re.compile(r"[^\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")
"""A character XML 1.0 cannot carry at all, escaped or not (a control character)."""


def _number(value: Decimal) -> int | float:
    """A ``Decimal`` as a JSON number: whole values as integers, others as floats.

    Raises:
        InvalidRequestError: The float would not carry every digit of ``value``.
    """
    if value == value.to_integral_value():
        return int(value)
    number = float(value)
    if Decimal(repr(number)) != value:
        raise InvalidRequestError(
            f"{value} has more digits than a JSON number carries; round it", source=SOURCE
        )
    return number


def _plain(value: Any) -> Any:
    """``value`` with every model, ``Decimal`` and ``date`` made plain JSON, recursively."""
    if isinstance(value, BaseModel):
        dumped = value.model_dump(by_alias=True, exclude_none=True, round_trip=False)
        return {name: _plain(item) for name, item in dumped.items()}
    if isinstance(value, Mapping):
        return {str(name): _plain(item) for name, item in value.items() if item is not None}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return _number(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def json_text(value: Any) -> str:
    """``value`` as the compact JSON upstream reads, objects under upstream's keys.

    Example: ``[{"accountId":42,"name":"Beratung","unitPrice":150}]``.
    """
    return json.dumps(_plain(value), ensure_ascii=False, separators=(",", ":"))


def form_value(value: Any) -> str | None:
    """One task value as the text of a form field; ``None`` or an empty list is not sent."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(Decimal(repr(value)), "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    if isinstance(value, list | tuple) and not value:
        return None
    return json_text(value)


def form_fields(named: Mapping[str, Any]) -> dict[str, str]:
    """The form fields of ``named``, upstream name to text, in its order; unset ones left out."""
    fields: dict[str, str] = {}
    for name, value in named.items():
        text = form_value(value)
        if text is not None:
            fields[name] = text
    return fields


def _custom_problems(custom: Mapping[Any, Any]) -> list[str]:
    problems: list[str] = []
    for name, value in custom.items():
        if not isinstance(name, str) or not CUSTOM_FIELD.fullmatch(name):
            problems.append(
                f"custom: {name!r} is not a custom field name; upstream names them "
                "customField<ID>, e.g. customField1"
            )
        if not isinstance(value, str):
            problems.append(
                f"custom: the value of {name!r} must be text, not {type(value).__name__}"
            )
        elif _XML_TEXT.search(value):
            problems.append(
                f"custom: the value of {name!r} holds a control character XML cannot carry"
            )
    return problems


def _render(pairs: Iterable[tuple[str, str]]) -> str:
    inner = "".join(f"<{name}>{escape(value)}</{name}>" for name, value in pairs)
    return f"<values>{inner}</values>"


def custom_xml(custom: Mapping[str, str]) -> str:
    """Custom field values as upstream's XML, each value escaped (``&``, ``<``, ``>``).

    Example: ``{"customField1": "Blau & Grün"}`` gives
    ``<values><customField1>Blau &amp; Grün</customField1></values>``.

    Raises:
        InvalidRequestError: A name is not ``customField<ID>``, or a value is not text or
            holds a character XML cannot carry; every problem is named.
    """
    problems = _custom_problems(custom)
    if problems:
        raise InvalidRequestError("; ".join(problems), source=SOURCE)
    return _render(custom.items())


def _stored_values(stored: str) -> list[tuple[str, str]]:
    """The ``(name, text)`` pairs of a record's ``custom`` XML, in their order.

    Raises:
        InvalidRequestError: The text is not ``<values>`` holding plain text elements, so
            it cannot be carried over value for value.
    """
    unreadable = InvalidRequestError(
        "custom: the record's stored custom field values are not <values> with one text "
        "element per field, so they cannot be carried over; the update was not sent",
        source=SOURCE,
    )
    if "<!" in stored:  # a DTD or a comment: never handed to the parser
        raise unreadable
    try:
        root = ElementTree.fromstring(stored)
    except ElementTree.ParseError:
        raise unreadable from None
    if root.tag != "values" or root.attrib or (root.text or "").strip():
        raise unreadable
    pairs: list[tuple[str, str]] = []
    for child in root:
        if child.attrib or len(child) or (child.tail or "").strip():
            raise unreadable
        pairs.append((child.tag, child.text or ""))
    return pairs


def merge_custom(stored: str | None, changes: Mapping[str, str]) -> str | None:
    """A record's ``custom`` XML with ``changes`` applied, every other value kept.

    A field named in ``changes`` takes its new value (an empty text empties it); one not
    named keeps the value the record holds; a new name is added at the end. Without
    changes the stored text is returned as it is, unparsed.

    Raises:
        InvalidRequestError: A name in ``changes`` is not ``customField<ID>`` or a value
            is not text, or the stored XML cannot be carried over value for value.
    """
    if not changes:
        return stored
    problems = _custom_problems(changes)
    if problems:
        raise InvalidRequestError("; ".join(problems), source=SOURCE)
    pairs = _stored_values(stored) if stored and stored.strip() else []
    merged = dict(pairs)
    merged.update(changes)
    return _render(merged.items())


async def post_form(org: str, path: str, fields: Mapping[str, str]) -> Any:
    """``POST`` ``fields`` form-encoded to ``path`` for organisation ``org``; the JSON answer.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        path: The operation's path after ``/api/v1``, e.g. ``"/journal/create.json"``.
        fields: The form fields, upstream name to text, e.g. from ``form_fields``.

    Raises:
        RequestRejected: Upstream answered HTTP 200 with ``"success": false``.
        ValidationError: The answer is not JSON.
    """
    response = await client_for(org).request(
        "POST", path, data=fields, headers={"Content-Type": FORM_CONTENT_TYPE}
    )
    try:
        return response.json()
    except ValueError as exc:
        raise ValidationError(
            f"{SOURCE}: response from {path} is not JSON",
            raw=response.text[:BODY_LIMIT],
            source=SOURCE,
        ) from exc


def ids_csv(ids: Sequence[int]) -> str:
    """``[3, 5]`` → ``"3,5"``: the CSV upstream's ``ids`` and ``associateId`` take."""
    return ",".join(str(item) for item in ids)


def delete_fields(ids: Sequence[int]) -> dict[str, str]:
    """The form fields of a ``delete.json`` operation: ``{"ids": "3,5"}``."""
    return {"ids": ids_csv(ids)}
