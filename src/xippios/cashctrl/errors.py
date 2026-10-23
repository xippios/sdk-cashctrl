"""CashCtrl failure modes with a distinct, documented meaning (conventions §5)."""

from collections.abc import Sequence

from xippios.core import InvalidRequestError, UpstreamModel

__all__ = ["FieldError", "RequestRejected"]


class FieldError(UpstreamModel):
    """One item of the ``errors`` list of a rejection (``docs/upstream/error-handling.md``).

    Attributes:
        field: The request parameter the message is about, as upstream names it
            (``debitId``); ``None`` when upstream names none.
        message: Upstream's message, in the language of the request's ``lang``.
    """

    field: str | None = None
    message: str


class RequestRejected(InvalidRequestError):
    """CashCtrl answered HTTP 200 with ``"success": false``: it refused the request.

    Upstream reports validation errors this way, not through status codes
    (``docs/upstream/error-handling.md``). Unlike core's other ``InvalidRequestError``
    cases, this one is raised after the upstream call, by the client's ``classify`` hook;
    adapters answer it like any ``InvalidRequestError``: text over MCP, HTTP 422.

    Attributes:
        errors: The field errors upstream listed, in its order; empty when it gave none.
        upstream_message: Upstream's single message (``errorMessage``), when it sent one.
    """

    def __init__(
        self,
        errors: Sequence[FieldError] = (),
        *,
        upstream_message: str | None = None,
        source: str | None = None,
    ) -> None:
        self.errors = list(errors)
        self.upstream_message = upstream_message
        super().__init__(_describe(self.errors, upstream_message), source=source)


def _describe(errors: Sequence[FieldError], upstream_message: str | None) -> str:
    if errors:
        reasons = "; ".join(
            f"{error.field}: {error.message}" if error.field else error.message for error in errors
        )
    else:
        reasons = upstream_message or "no reason given"
    return f"CashCtrl rejected the request: {reasons}"
