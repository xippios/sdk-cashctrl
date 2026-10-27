"""The ``--org`` lock: tools bound to one organisation, so no tool takes ``org`` (ADR-0024).

Core held the lock as ``xippios.core.mcp.TenantLock``, a middleware that refused a tool
call naming another tenant, until 0.3.0 left it to this package (ADR-0024; the family
review's C8). The lock here is no middleware but a wrapper: given ``--org <name>``,
``bind_tasks`` hands ``build_server`` tools on which ``org`` is bound when the server is
built. Each wrapper keeps its task's ``__name__``, so tool names and ``MCP_CAPS`` keys stay
as they are, and its docstring without the ``org`` line under ``Args:``; its signature
and annotations leave ``org`` out, so no tool's input schema declares it, and it calls the
task with ``org=<name>``. The organisation list of a bound server lists that
organisation only (``_only_the_locked_tenant``), still with ``meta.tenant`` ``None``. The
server's instructions gain one sentence naming the organisation (``lock_sentence``).

Kept from the copy at sdk-core's ``cb8ecdf379c04522e5f1dcd91ea5e8bdfa1fb3ff``
(``src/xippios/core/mcp/server.py``): ``TenantLock``'s validation of the parameter and
the tenant, as ``OrgLock``; ``_only_the_locked_tenant``; and ``_lock_sentence``,
reworded for a bound ``org``. The middleware's functions (``_lock_middleware``,
``_declares``, ``_refusal``, ``_check_lock``, ``_defaulted``) have no part in it: a
bound tool has no ``org`` to check. Private to this package: ``_cli`` validates the
organisation at startup and ``mcp.py`` and ``mcp_write.py`` call ``bind_tasks`` and
``instructions``. The HTTP router has no lock: a deployment that needs one declares
only that organisation.
"""

import asyncio
import functools
import inspect
import re
import typing
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from xippios.core import Result

from xippios.cashctrl._tenants import _LISTS_TENANTS

__all__ = ["OrgLock", "bind", "bind_tasks", "instructions", "lock_sentence"]


@dataclass(frozen=True, slots=True)
class OrgLock:
    """Bind a server to one organisation: every tool acts on it and none takes ``param``.

    Attributes:
        param: The task parameter that names the organisation, ``"org"``.
        value: The organisation the server serves, e.g. ``"demo"``; checked at startup
            by ``_cli``, declared and with a well-formed subdomain.

    Raises:
        ValueError: ``param`` is not a parameter name or ``value`` is empty.
    """

    param: str
    value: str

    def __post_init__(self) -> None:
        if not self.param.isidentifier():
            raise ValueError("param must be a parameter name such as 'org'")
        if not self.value:
            raise ValueError("value must name the tenant the server serves")


def lock_sentence(lock: OrgLock) -> str:
    """The sentence a bound server's instructions end with."""
    return (
        f"This server is bound to {lock.param} {lock.value}; every tool acts on that "
        f"organisation and takes no {lock.param}."
    )


def instructions(base: str | None, lock: OrgLock | None) -> str | None:
    """``base``, followed by ``lock_sentence`` when the server is bound; ``base`` when not."""
    if lock is None:
        return base
    return " ".join(filter(None, [base, lock_sentence(lock)]))


def _only_the_locked_tenant(lock: OrgLock, result: Any) -> Any:
    """A tenant list narrowed to the tenant ``lock`` binds; anything else unchanged."""
    if not isinstance(result, Result) or not isinstance(result.data, list):
        return result
    return result.model_copy(update={"data": [name for name in result.data if name == lock.value]})


def _without_arg(doc: str, param: str) -> str:
    """``doc`` without ``param``'s entry under ``Args:``, and without an ``Args:`` left empty.

    ``doc`` is cleaned as ``inspect.getdoc`` cleans it. The entry is its first line,
    ``    <param>: ...``, and every line after it indented deeper, its continuation.
    """
    entry = re.compile(rf"\s+{re.escape(param)}:")
    kept: list[str] = []
    in_args = False
    skipping: int | None = None
    for line in doc.splitlines():
        indent = len(line) - len(line.lstrip())
        if skipping is not None and line.strip() and indent > skipping:
            continue
        skipping = None
        if line.strip() == "Args:":
            in_args = True
        elif line.strip() and indent == 0:
            in_args = False
        if in_args and entry.match(line):
            skipping = indent
            continue
        kept.append(line)
    lines: list[str] = []
    for index, line in enumerate(kept):
        following = kept[index + 1] if index + 1 < len(kept) else ""
        if line == "Args:" and not following.startswith(" "):
            continue  # the parameter was its only entry
        lines.append(line)
    return "\n".join(lines).rstrip()


def bind(fn: Callable[..., Any], lock: OrgLock) -> Callable[..., Any]:
    """``fn`` as the tool of a server bound to ``lock.value``.

    A task that takes ``lock.param`` becomes an async function of its other parameters
    that awaits the task with ``param=value``: the same ``__name__``, the docstring
    without the parameter's line under ``Args:``, and a signature and annotations
    without it. The organisation list (``list_task``) lists the bound organisation
    only. Any other task is returned as it is.

    Args:
        fn: A task, a ``sync`` facade or a plain function, e.g. ``tasks.list_accounts``.
        lock: The organisation the server is bound to, e.g. ``OrgLock("org", "demo")``.
    """
    if getattr(fn, _LISTS_TENANTS, False) is True:

        @functools.wraps(fn)
        def only_the_locked_tenant() -> Any:
            return _only_the_locked_tenant(lock, fn())

        return only_the_locked_tenant
    signature = inspect.signature(fn)
    if lock.param not in signature.parameters:
        return fn
    hints = typing.get_type_hints(fn)
    parameters = [
        p.replace(annotation=hints.get(p.name, p.annotation))
        for p in signature.parameters.values()
        if p.name != lock.param
    ]
    returns = hints.get("return", signature.return_annotation)
    twin = getattr(fn, "async_fn", None)
    target = twin if inspect.iscoroutinefunction(twin) else fn
    bound_to = {lock.param: lock.value}

    async def bound(**kwargs: Any) -> Any:
        if inspect.iscoroutinefunction(target):
            return await target(**bound_to, **kwargs)
        return await asyncio.to_thread(target, **bound_to, **kwargs)  # as core's as_async

    bound.__name__ = fn.__name__
    bound.__qualname__ = fn.__qualname__
    bound.__module__ = fn.__module__
    bound.__doc__ = _without_arg(inspect.getdoc(fn) or "", lock.param)
    bound.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=parameters, return_annotation=returns
    )
    bound.__annotations__ = {p.name: p.annotation for p in parameters} | {"return": returns}
    return bound


def bind_tasks(
    tasks: Iterable[Callable[..., Any]], lock: OrgLock | None
) -> list[Callable[..., Any]]:
    """``tasks`` as a server's tools: bound to ``lock`` (``bind``), or as they are without one."""
    if lock is None:
        return list(tasks)
    return [bind(fn, lock) for fn in tasks]
