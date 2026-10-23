"""The configured ``xippios.core`` client for CashCtrl.

One ``AsyncClient`` for the whole package: task functions share its rate limiter and
cache, and the same instance serves the sync facades and the MCP server.
"""

from xippios.core import AsyncClient, BasicKeyAuth, ClientConfig, RateLimit

from xippios.cashctrl._version import __version__

SOURCE = "cashctrl"
BASE_URL = "https://example.cashctrl.com/api/v1"
API_KEY_ENV = "CASHCTRL_API_KEY"  # pragma: allowlist secret (a variable name, not a key)
RATE_LIMIT = RateLimit(per_minute=60)

config = ClientConfig(
    source=SOURCE,
    version=__version__,
    base_url=BASE_URL,
    rate_limit=RATE_LIMIT,
)
# The key is read from the environment on the first request, never at import.
auth = BasicKeyAuth(API_KEY_ENV, source=SOURCE)
client = AsyncClient(config, auth=auth)

__all__ = ["API_KEY_ENV", "BASE_URL", "RATE_LIMIT", "SOURCE", "auth", "client", "config"]
