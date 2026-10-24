"""``POST /api/v1/person/create.json``: a new person.

Reference: ``docs/upstream/person.md``, "Create person" ("Creates a new person. Returns
either a success or multiple error messages (for each issue)."). Its documented
parameters: ``company``, ``firstName`` and ``lastName`` (each marked mandatory: "Either
``firstName``, ``lastName`` or ``company`` must be set"), and optionally ``addresses``,
``altName``, ``attachments``, ``bankAccounts``, ``bankData``, ``categoryId``,
``certificateTemplateId``, ``certificateValues``, ``children``, ``color``, ``contacts``,
``custom``, ``dateBirth``, ``department``, ``discountPercentage``, ``industry``,
``insuranceContracts``, ``insuranceMemberNr``, ``insuranceNr``,
``isAutoFillResponsiblePerson``, ``isCustomer``, ``isEmployee``, ``isFamily``,
``isInactive``, ``isInsurance``, ``isVendor``, ``language``, ``locationId``, ``notes``,
``nr``, ``position``, ``sequenceNumberId``, ``servicePeriods``, ``ssn``, ``superiorId``,
``titleId``, ``userId`` and ``vatUid``. ``person/update.json`` documents the same ones
and ``id``, so ``person_fields`` encodes both.

Observed on 2026-10-23 (``docs/demo-org.md``): the answer is ``{"success": true,
"insertId": <int>, "message": ...}``; an umlaut sent form-encoded with
``charset=UTF-8`` was read back byte for byte.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from pydantic import JsonValue
from xippios.core import parse

from xippios.cashctrl._client import SOURCE
from xippios.cashctrl.api._form import form_fields, post_form
from xippios.cashctrl.models import (
    AttachmentInput,
    BankAccountInput,
    ChildInput,
    Color,
    InsuranceContractInput,
    Language,
    PersonAddressInput,
    PersonContactInput,
    ServicePeriodInput,
    WriteAnswer,
)

__all__ = ["person_create", "person_fields"]


def person_fields(
    *,
    id: int | None = None,
    company: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    addresses: Sequence[PersonAddressInput] | None = None,
    alt_name: str | None = None,
    attachments: Sequence[AttachmentInput] | None = None,
    bank_accounts: Sequence[BankAccountInput] | None = None,
    bank_data: str | None = None,
    category_id: int | None = None,
    certificate_template_id: int | None = None,
    certificate_values: Mapping[str, JsonValue] | None = None,
    children: Sequence[ChildInput] | None = None,
    color: Color | None = None,
    contacts: Sequence[PersonContactInput] | None = None,
    custom: str | None = None,
    date_birth: date | None = None,
    department: str | None = None,
    discount_percentage: Decimal | None = None,
    industry: str | None = None,
    insurance_contracts: Sequence[InsuranceContractInput] | None = None,
    insurance_member_nr: str | None = None,
    insurance_nr: str | None = None,
    is_auto_fill_responsible_person: bool | None = None,
    is_customer: bool | None = None,
    is_employee: bool | None = None,
    is_family: bool | None = None,
    is_inactive: bool | None = None,
    is_insurance: bool | None = None,
    is_vendor: bool | None = None,
    language: Language | None = None,
    location_id: int | None = None,
    notes: str | None = None,
    nr: str | None = None,
    position: str | None = None,
    sequence_number_id: int | None = None,
    service_periods: Sequence[ServicePeriodInput] | None = None,
    ssn: str | None = None,
    superior_id: int | None = None,
    title_id: int | None = None,
    user_id: int | None = None,
    vat_uid: str | None = None,
) -> dict[str, str]:
    """The form fields of ``person/create.json`` (``id`` unset) or ``update.json`` (set).

    Upstream's names, in the order of its table, ``id`` first; a value left at ``None``
    or an empty list is not sent (``api/_form.py``). ``certificate_values`` is sent as a
    JSON object (``{"F": true, "2.3a": "Bonus"}``) and ``custom`` as the XML text upstream
    stores; an empty ``certificate_values`` is not sent.
    """
    return form_fields(
        {
            "id": id,
            "company": company,
            "firstName": first_name,
            "lastName": last_name,
            "addresses": addresses,
            "altName": alt_name,
            "attachments": attachments,
            "bankAccounts": bank_accounts,
            "bankData": bank_data,
            "categoryId": category_id,
            "certificateTemplateId": certificate_template_id,
            "certificateValues": certificate_values or None,
            "children": children,
            "color": color,
            "contacts": contacts,
            "custom": custom,
            "dateBirth": date_birth,
            "department": department,
            "discountPercentage": discount_percentage,
            "industry": industry,
            "insuranceContracts": insurance_contracts,
            "insuranceMemberNr": insurance_member_nr,
            "insuranceNr": insurance_nr,
            "isAutoFillResponsiblePerson": is_auto_fill_responsible_person,
            "isCustomer": is_customer,
            "isEmployee": is_employee,
            "isFamily": is_family,
            "isInactive": is_inactive,
            "isInsurance": is_insurance,
            "isVendor": is_vendor,
            "language": language,
            "locationId": location_id,
            "notes": notes,
            "nr": nr,
            "position": position,
            "sequenceNumberId": sequence_number_id,
            "servicePeriods": service_periods,
            "ssn": ssn,
            "superiorId": superior_id,
            "titleId": title_id,
            "userId": user_id,
            "vatUid": vat_uid,
        }
    )


async def person_create(org: str, fields: Mapping[str, str]) -> WriteAnswer:
    """Call ``person/create.json`` for organisation ``org`` with ``fields``.

    Args:
        org: A declared organisation, e.g. ``"demo"``.
        fields: The form fields, from ``person_fields`` without ``id``.

    Raises:
        RequestRejected: Upstream refused the person, naming the fields.
    """
    raw = await post_form(org, "/person/create.json", fields)
    return parse(WriteAnswer, raw, source=SOURCE, endpoint="person/create.json")
