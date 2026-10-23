"""The ``filter`` parameter of CashCtrl's ``list.json`` operations, encoded once.

Upstream takes ``filter`` as "a JSON array ``[{...},{...},...]``" of
``{comparison, field, value}`` (``docs/upstream/account.md``, "List accounts"; the same
table recurs on the other lists that document ``filter``).
"""

import json
from collections.abc import Sequence

from xippios.cashctrl.models import Filter

__all__ = ["encode_filter"]


def encode_filter(filters: Sequence[Filter]) -> str:
    """``filters`` as the compact JSON array upstream reads, keys in the documented order.

    Example: ``[{"comparison":"eq","field":"number","value":"1000"}]``.
    """
    return json.dumps(
        [item.model_dump(mode="json") for item in filters],
        separators=(",", ":"),
        ensure_ascii=False,
    )
