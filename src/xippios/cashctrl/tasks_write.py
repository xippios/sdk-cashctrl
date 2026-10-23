"""Write tasks for CashCtrl.

Served only by ``xippios-cashctrl-mcp-write``, never by the read-only server.
Every function takes ``confirm: bool = False`` and, while ``confirm`` is false, returns
a dry-run preview of what would change instead of changing it (conventions §8). Nothing
here is mounted on the HTTP router. List the sync names in ``__all__``.

``org: str`` is the first, required parameter of every write task: the name of a
declared organisation (``demo``, ``acme``), handed to the endpoint wrappers, which reach
CashCtrl through ``client_for(org)``. ``tests/test_tasks.py`` checks every name in
``__all__``.
"""

__all__: list[str] = []
