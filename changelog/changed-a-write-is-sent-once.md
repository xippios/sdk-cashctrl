- The fourteen write tools send their write once, after a 429 too: an error after a 5xx or a
  failure in transit says that the request was sent once and that its outcome is unknown,
  and each tool's description names the read that shows whether the write was applied,
  `list_journal_entries`, `get_journal_entry`, `list_persons`, `get_person`, `list_orders`,
  `get_order` or `list_order_book_entries`, and for `create_order_payment` the orders' status
  where the payment sets one. (https://github.com/xippios/sdk-core/issues/480)
