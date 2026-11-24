- `list_journal_entries`, `list_persons`, `list_orders` and `list_history` without `limit`
  collect at most 24 pages of 100, for Python and MCP alike, and send no request at or past
  upstream's count. Where they need more pages they refuse with `InvalidRequestError` after
  the first request and return nothing, naming the count, the bound, the paging arguments,
  the requests sent, the page reached and the total of pages.
  (https://github.com/xippios/sdk-core/issues/480,
  https://github.com/xippios/sdk-cashctrl/issues/135)
