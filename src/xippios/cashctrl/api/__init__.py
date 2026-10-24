"""Endpoint wrappers for CashCtrl.

Layer 1 of ADR-0001: one module per upstream operation, named after it. A wrapper
takes ``org`` first, then the parameters as upstream names them (snake_cased), calls
``xippios.cashctrl._client.client_for(org)`` and returns models from ``models.py`` that
mirror the payload. No composition and no defaults beyond upstream's own: a paginated
list wrapper fetches one page, and the task collects pages. The reference is the
snapshot in ``docs/upstream/``.

A write wrapper (``*_create``, ``*_update``, ``*_delete``) posts form fields through
``_form.post_form``; ``journal_fields``, ``person_fields`` and ``order_fields`` encode
them from the parameters as upstream names them, so a task can preview exactly what it
would send (``tasks_write``).
"""

from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._form import custom_xml, delete_fields, merge_custom
from xippios.cashctrl.api.account_list import account_list, account_list_params
from xippios.cashctrl.api.account_read import account_read
from xippios.cashctrl.api.currency_list import currency_list
from xippios.cashctrl.api.fiscalperiod_list import fiscalperiod_list
from xippios.cashctrl.api.journal_create import journal_create, journal_fields
from xippios.cashctrl.api.journal_delete import journal_delete
from xippios.cashctrl.api.journal_list import journal_list, journal_list_params
from xippios.cashctrl.api.journal_read import journal_read
from xippios.cashctrl.api.journal_update import journal_update
from xippios.cashctrl.api.order_list import order_list, order_list_params
from xippios.cashctrl.api.order_read import order_read
from xippios.cashctrl.api.person_create import person_create, person_fields
from xippios.cashctrl.api.person_delete import person_delete
from xippios.cashctrl.api.person_list import person_list, person_list_params
from xippios.cashctrl.api.person_read import person_read
from xippios.cashctrl.api.person_update import person_update
from xippios.cashctrl.api.tax_list import tax_list

__all__ = [
    "account_list",
    "account_list_params",
    "account_read",
    "currency_list",
    "custom_xml",
    "delete_fields",
    "encode_filter",
    "fiscalperiod_list",
    "journal_create",
    "journal_delete",
    "journal_fields",
    "journal_list",
    "journal_list_params",
    "journal_read",
    "journal_update",
    "merge_custom",
    "order_list",
    "order_list_params",
    "order_read",
    "person_create",
    "person_delete",
    "person_fields",
    "person_list",
    "person_list_params",
    "person_read",
    "person_update",
    "tax_list",
]
