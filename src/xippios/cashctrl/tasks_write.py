"""Write tasks for CashCtrl.

Served only by ``xippios-cashctrl-mcp-write``, never by the read-only server.
Every function takes ``confirm: bool = False`` and, while ``confirm`` is false, returns
a dry-run preview of what would change instead of changing it (conventions §8). Nothing
here is mounted on the HTTP router. List the sync names in ``__all__``.
"""

__all__: list[str] = []
