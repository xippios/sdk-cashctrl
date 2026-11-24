- The description of `get_report_data`, `list_journal_entries`, `list_orders`,
  `list_history`, `list_persons`, `get_order_document` and of the write tools
  `create_journal_entry`, `update_journal_entry`, `delete_journal_entry`, `create_person`,
  `update_person`, `create_order`, `update_order`, `update_order_status`,
  `create_order_payment`, `create_order_book_entry` and `update_order_book_entry` is its
  task's docstring before `Args:`, under 1,000 characters, and the text of each of a tool's
  arguments stands in its input schema. Each description states the most requests a call
  sends, retries counted. (https://github.com/xippios/sdk-core/issues/485,
  https://github.com/xippios/sdk-cashctrl/issues/144)
