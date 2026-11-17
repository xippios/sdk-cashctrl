- The write server books, changes and deletes the book entries of orders, such as a
  payment received for an invoice: `create_order_book_entry`, `update_order_book_entry`
  and `delete_order_book_entry`, confirm-gated as every write tool is. The update reads
  the entry and sends it whole, and the update and the delete write only an entry booked
  by hand, refusing one that the order's items booked. `docs/demo-org.md` names them among
  the demo role's write needs.
  (https://github.com/xippios/sdk-cashctrl/issues/43,
  https://github.com/xippios/sdk-cashctrl/issues/68)
