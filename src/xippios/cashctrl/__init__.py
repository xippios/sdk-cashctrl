"""Typed client, MCP tools and HTTP routes for CashCtrl.

Distribution ``xippios-cashctrl``. Public API: ``__version__`` and the task
functions re-exported here; every task takes ``org``, a declared organisation, first.
Endpoint wrappers under ``api/`` and the organisation registry in ``_client`` are
internal.
"""

from xippios.cashctrl._version import __version__
from xippios.cashctrl.tasks import (
    get_account,
    list_accounts,
    list_currencies,
    list_fiscal_periods,
    list_tax_codes,
)

__all__ = [
    "__version__",
    "get_account",
    "list_accounts",
    "list_currencies",
    "list_fiscal_periods",
    "list_tax_codes",
]
