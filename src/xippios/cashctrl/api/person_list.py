"""``GET /api/v1/person/list.json``: persons (people and companies), one page at a time.

Reference: ``docs/upstream/person.md``, "List people" ("Returns a list of people."). Its
documented parameters, all optional: ``categoryId``, ``dir`` (default ``ASC``),
``filter``, ``limit`` ("The number of entries to retrieve. Defaults to 100."),
``onlyActive``, ``onlyCustomers``, ``onlyEmployees``, ``onlyFamilies``,
``onlyInsurances``, ``onlyNotes``, ``onlyVendors``, ``onlyWithImages``,
``onlyWithoutCategory``, ``onlyWithoutRole``, ``query``, ``sort`` (default ``name``)
and ``start`` ("The starting entry. Defaults to 0."). Pages are the task's business.
"""

from collections.abc import Sequence

from xippios.core import parse

from xippios.cashctrl._client import SOURCE, client_for
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._params import flag, present
from xippios.cashctrl.models import Direction, Filter, ListResponse, Person

__all__ = ["person_list", "person_list_params"]


def person_list_params(
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    limit: int | None = None,
    only_active: bool | None = None,
    only_customers: bool | None = None,
    only_employees: bool | None = None,
    only_families: bool | None = None,
    only_insurances: bool | None = None,
    only_notes: bool | None = None,
    only_vendors: bool | None = None,
    only_with_images: bool | None = None,
    only_without_category: bool | None = None,
    only_without_role: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
    start: int | None = None,
) -> dict[str, str | int]:
    """The query parameters of ``person/list.json``, under upstream's names.

    A parameter left at ``None`` is not sent, so upstream applies its own default; an
    empty ``filter`` is not sent either. Booleans are sent as ``true``/``false`` and
    ``filter`` as its JSON array.
    """
    return present(
        {
            "categoryId": category_id,
            "dir": dir,
            "filter": encode_filter(filter) if filter else None,
            "onlyActive": flag(only_active),
            "onlyCustomers": flag(only_customers),
            "onlyEmployees": flag(only_employees),
            "onlyFamilies": flag(only_families),
            "onlyInsurances": flag(only_insurances),
            "onlyNotes": flag(only_notes),
            "onlyVendors": flag(only_vendors),
            "onlyWithImages": flag(only_with_images),
            "onlyWithoutCategory": flag(only_without_category),
            "onlyWithoutRole": flag(only_without_role),
            "query": query,
            "sort": sort,
            "start": start,
            "limit": limit,
        }
    )


async def person_list(
    org: str,
    *,
    category_id: int | None = None,
    dir: Direction | None = None,
    filter: Sequence[Filter] | None = None,
    limit: int | None = None,
    only_active: bool | None = None,
    only_customers: bool | None = None,
    only_employees: bool | None = None,
    only_families: bool | None = None,
    only_insurances: bool | None = None,
    only_notes: bool | None = None,
    only_vendors: bool | None = None,
    only_with_images: bool | None = None,
    only_without_category: bool | None = None,
    only_without_role: bool | None = None,
    query: str | None = None,
    sort: str | None = None,
    start: int | None = None,
) -> ListResponse[Person]:
    """Call ``person/list.json`` for organisation ``org``: one page and upstream's total.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        category_id: ``categoryId``, a person category.
        dir: ``dir``, ``ASC`` or ``DESC``; upstream's default is ``ASC``.
        filter: ``filter``, sent as a JSON array; all filters must match.
        limit: ``limit``, the number of entries; upstream's default is 100.
        only_active: ``onlyActive``; upstream's default is false.
        only_customers: ``onlyCustomers``; upstream's default is false.
        only_employees: ``onlyEmployees``; upstream's default is false.
        only_families: ``onlyFamilies``; upstream's default is false.
        only_insurances: ``onlyInsurances``; upstream's default is false.
        only_notes: ``onlyNotes``; upstream's default is false.
        only_vendors: ``onlyVendors``; upstream's default is false.
        only_with_images: ``onlyWithImages``; upstream's default is false.
        only_without_category: ``onlyWithoutCategory``; upstream's default is false.
        only_without_role: ``onlyWithoutRole``; upstream's default is false.
        query: ``query``, a full-text search.
        sort: ``sort``, the column to sort by; upstream's default is ``name``.
        start: ``start``, the offset of the first entry; upstream's default is 0.
    """
    params = person_list_params(
        category_id=category_id,
        dir=dir,
        filter=filter,
        limit=limit,
        only_active=only_active,
        only_customers=only_customers,
        only_employees=only_employees,
        only_families=only_families,
        only_insurances=only_insurances,
        only_notes=only_notes,
        only_vendors=only_vendors,
        only_with_images=only_with_images,
        only_without_category=only_without_category,
        only_without_role=only_without_role,
        query=query,
        sort=sort,
        start=start,
    )
    raw = await client_for(org).get_json("/person/list.json", params=params)
    return parse(ListResponse[Person], raw, source=SOURCE, endpoint="person/list.json")
