"""Typed client, MCP tools and HTTP routes for CashCtrl.

Distribution ``xippios-cashctrl``. Public API: ``__version__`` and the task
functions re-exported here. Every task takes ``org``, a declared organisation, first,
except ``list_organisations``, which takes no argument and lists the declared
organisations' names. The write tasks (``create_*``, ``update_*``, ``delete_*``, from
``tasks_write``) preview unless called with ``confirm=True``.
Endpoint wrappers under ``api/`` and the organisation registry in ``_client`` are
internal.
"""

from xippios.cashctrl._version import __version__
from xippios.cashctrl.tasks import (
    get_account,
    get_journal_entry,
    get_order,
    get_person,
    list_accounts,
    list_currencies,
    list_fiscal_periods,
    list_journal_entries,
    list_orders,
    list_organisations,
    list_persons,
    list_tax_codes,
)
from xippios.cashctrl.tasks_write import (
    create_journal_entry,
    create_person,
    delete_journal_entry,
    delete_person,
    update_journal_entry,
    update_person,
)

__all__ = [
    "__version__",
    "create_journal_entry",
    "create_person",
    "delete_journal_entry",
    "delete_person",
    "get_account",
    "get_journal_entry",
    "get_order",
    "get_person",
    "list_accounts",
    "list_currencies",
    "list_fiscal_periods",
    "list_journal_entries",
    "list_orders",
    "list_organisations",
    "list_persons",
    "list_tax_codes",
    "update_journal_entry",
    "update_person",
]
