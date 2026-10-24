"""Typed client, MCP tools and HTTP routes for CashCtrl.

Distribution ``xippios-cashctrl``. Public API: ``__version__`` and the task
functions re-exported here. Every task takes ``org``, a declared organisation, first,
except ``list_organisations``, which takes no argument and lists the declared
organisations' names.
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

__all__ = [
    "__version__",
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
]
