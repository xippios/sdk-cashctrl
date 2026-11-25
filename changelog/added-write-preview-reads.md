- A write tool's preview carries `reads`, the operations it read: the record's `read.json`
  for the previews of the eight updates and deletes, such as `["journal/read.json"]`, and
  `[]` for the four creates, `update_order_status` and `create_order_payment`, which send no
  request. Each of the fourteen tools' descriptions says whether its preview reads and what
  that costs, one request or none. (sdk-core ADR-0050,
  https://github.com/xippios/sdk-cashctrl/issues/88)
