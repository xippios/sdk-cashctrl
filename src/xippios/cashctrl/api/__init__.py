"""Endpoint wrappers for CashCtrl.

Layer 1 of ADR-0001: one module per upstream operation, named after it. A wrapper
takes ``org`` first, then the parameters as upstream names them (snake_cased), calls
``xippios.cashctrl._client.client_for(org)`` and returns models from ``models.py`` that
mirror the payload. No composition and no defaults beyond upstream's own. The reference
is the snapshot in ``docs/upstream/``.
"""

from xippios.cashctrl.api._filter import encode_filter
from xippios.cashctrl.api.account_list import account_list, account_list_params
from xippios.cashctrl.api.account_read import account_read
from xippios.cashctrl.api.currency_list import currency_list
from xippios.cashctrl.api.fiscalperiod_list import fiscalperiod_list
from xippios.cashctrl.api.tax_list import tax_list

__all__ = [
    "account_list",
    "account_list_params",
    "account_read",
    "currency_list",
    "encode_filter",
    "fiscalperiod_list",
    "tax_list",
]
