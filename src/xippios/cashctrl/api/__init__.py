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

A file wrapper (``*_list_csv``, ``*_list_xlsx``, ``*_list_pdf``, ``order_document_read_pdf``)
streams the file to a path through ``_download.download`` and returns core's
``Downloaded``; an export takes its list's query, from ``*_list_params``, with
``columns`` added by ``export_params``.
"""

from xippios.cashctrl.api._download import export_params
from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api._form import custom_xml, delete_fields, merge_custom
from xippios.cashctrl.api.account_category_list import account_category_list
from xippios.cashctrl.api.account_costcenter_list import (
    account_costcenter_list,
    account_costcenter_list_params,
)
from xippios.cashctrl.api.account_list import account_list, account_list_params
from xippios.cashctrl.api.account_list_csv import account_list_csv
from xippios.cashctrl.api.account_list_pdf import account_list_pdf
from xippios.cashctrl.api.account_list_xlsx import account_list_xlsx
from xippios.cashctrl.api.account_read import account_read
from xippios.cashctrl.api.currency_list import currency_list
from xippios.cashctrl.api.customfield_list import customfield_list, customfield_list_params
from xippios.cashctrl.api.fiscalperiod_list import fiscalperiod_list
from xippios.cashctrl.api.history_list import history_list, history_list_params
from xippios.cashctrl.api.journal_create import journal_create, journal_fields
from xippios.cashctrl.api.journal_delete import journal_delete
from xippios.cashctrl.api.journal_list import journal_list, journal_list_params
from xippios.cashctrl.api.journal_list_csv import journal_list_csv
from xippios.cashctrl.api.journal_list_pdf import journal_list_pdf
from xippios.cashctrl.api.journal_list_xlsx import journal_list_xlsx
from xippios.cashctrl.api.journal_read import journal_read
from xippios.cashctrl.api.journal_update import journal_update
from xippios.cashctrl.api.location_list import location_list
from xippios.cashctrl.api.order_bookentry_list import order_bookentry_list
from xippios.cashctrl.api.order_category_list import (
    order_category_list,
    order_category_list_params,
)
from xippios.cashctrl.api.order_create import order_create, order_fields
from xippios.cashctrl.api.order_delete import order_delete
from xippios.cashctrl.api.order_document_read import order_document_read
from xippios.cashctrl.api.order_document_read_pdf import (
    order_document_read_pdf,
    order_document_read_pdf_params,
)
from xippios.cashctrl.api.order_list import order_list, order_list_params
from xippios.cashctrl.api.order_list_csv import order_list_csv
from xippios.cashctrl.api.order_list_pdf import order_list_pdf
from xippios.cashctrl.api.order_list_xlsx import order_list_xlsx
from xippios.cashctrl.api.order_read import order_read
from xippios.cashctrl.api.order_update import order_update
from xippios.cashctrl.api.person_category_list import person_category_list
from xippios.cashctrl.api.person_create import person_create, person_fields
from xippios.cashctrl.api.person_delete import person_delete
from xippios.cashctrl.api.person_list import person_list, person_list_params
from xippios.cashctrl.api.person_list_csv import person_list_csv
from xippios.cashctrl.api.person_list_pdf import person_list_pdf
from xippios.cashctrl.api.person_list_xlsx import person_list_xlsx
from xippios.cashctrl.api.person_read import person_read
from xippios.cashctrl.api.person_title_list import person_title_list
from xippios.cashctrl.api.person_update import person_update
from xippios.cashctrl.api.report_element_data import (
    report_element_data,
    report_element_data_params,
)
from xippios.cashctrl.api.report_tree import report_tree
from xippios.cashctrl.api.tax_list import tax_list

__all__ = [
    "account_category_list",
    "account_costcenter_list",
    "account_costcenter_list_params",
    "account_list",
    "account_list_csv",
    "account_list_params",
    "account_list_pdf",
    "account_list_xlsx",
    "account_read",
    "currency_list",
    "custom_xml",
    "customfield_list",
    "customfield_list_params",
    "delete_fields",
    "encode_filter",
    "export_params",
    "fiscalperiod_list",
    "history_list",
    "history_list_params",
    "journal_create",
    "journal_delete",
    "journal_fields",
    "journal_list",
    "journal_list_csv",
    "journal_list_params",
    "journal_list_pdf",
    "journal_list_xlsx",
    "journal_read",
    "journal_update",
    "location_list",
    "merge_custom",
    "order_bookentry_list",
    "order_category_list",
    "order_category_list_params",
    "order_create",
    "order_delete",
    "order_document_read",
    "order_document_read_pdf",
    "order_document_read_pdf_params",
    "order_fields",
    "order_list",
    "order_list_csv",
    "order_list_params",
    "order_list_pdf",
    "order_list_xlsx",
    "order_read",
    "order_update",
    "person_category_list",
    "person_create",
    "person_delete",
    "person_fields",
    "person_list",
    "person_list_csv",
    "person_list_params",
    "person_list_pdf",
    "person_list_xlsx",
    "person_read",
    "person_title_list",
    "person_update",
    "report_element_data",
    "report_element_data_params",
    "report_tree",
    "tax_list",
]
