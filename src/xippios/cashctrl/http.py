"""FastAPI router for CashCtrl.

One route per task, ``/cashctrl/<task>`` (ADR-0007): a task whose parameters are all
scalars is a ``GET`` with query parameters, and a task with a non-scalar parameter
(``list_accounts``, whose ``filter`` is a list) is a ``POST`` whose JSON body is keyed
by parameter name. No logic lives here (ADR-0001). The consumer mounts it; it is never
served standalone.
"""

from xippios.core.http import router_from_tasks

from xippios.cashctrl import tasks
from xippios.cashctrl._client import SOURCE

router = router_from_tasks(SOURCE, [getattr(tasks, name) for name in tasks.__all__])

__all__ = ["router"]
